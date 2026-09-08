"""Tokenize prompts for model-specific length controls.

Whitespace padding isolates length without adding content; failed tokenizer loads raise because
fallback counts would break byte-for-byte regeneration.
"""

import functools
import logging
from typing import Any, Callable, Optional, Protocol, Tuple, runtime_checkable

import requests

from smolbench.evals.openai_compat import METADATA_TIMEOUT_S


@runtime_checkable
class Tokenizer(Protocol):
    """Structural interface for model token counting."""

    #: Human-readable identity for logs and errors.
    name: str

    def count(self, text: str) -> int:
        """Count tokens in `text`.

        Must exclude special/BOS tokens: both compared prompts get the same chat-template wrap
        downstream, so an inconsistent offset becomes an off-by-N in the match.

        Parameters
        ----------
        text : str
            Text to tokenize.

        Returns
        -------
        int
            Token count.
        """
        ...


class HFTokenizer:
    """A model tokenizer loaded from HuggingFace ``tokenizer.json``."""

    def __init__(self, name: str, tokenizer: Any) -> None:
        """Wrap a constructed ``tokenizers.Tokenizer``.

        Parameters
        ----------
        name : str
            Tokenizer name.
        tokenizer : Any
            Object supporting ``encode(...).ids``.
        """
        self.name = name
        self._tokenizer = tokenizer

    @classmethod
    def from_repo(cls, repo_id: str) -> "HFTokenizer":
        """Load and cache `repo_id`'s tokenizer.

        Disable embedded truncation and padding because they would miscount prompts.

        Parameters
        ----------
        repo_id : str
            Repository containing ``tokenizer.json``.

        Returns
        -------
        HFTokenizer
            Loaded tokenizer.

        Raises
        ------
        RuntimeError
            If loading fails or no ``tokenizer.json`` exists.
        """
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer as HFTokenizerImpl
        except ImportError as exc:  # pragma: no cover -- both are core deps
            raise ImportError(
                "HFTokenizer needs `huggingface_hub` and `tokenizers` "
                f"(pip install smolbench): {exc}"
            ) from exc
        try:
            path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
        except Exception as exc:  # noqa: BLE001 -- hub raises a wide family here
            raise RuntimeError(
                f"could not fetch tokenizer.json from {repo_id!r}: "
                f"{type(exc).__name__}: {exc}. If this repo ships weights "
                "only (common for quantized redistributions), point the "
                "deploy spec's `tokenizer_hf_id` key at a repo that has the "
                "tokenizer -- normally the unquantized base model."
            ) from exc
        tokenizer = HFTokenizerImpl.from_file(path)
        tokenizer.no_truncation()
        tokenizer.no_padding()
        return cls(repo_id, tokenizer)

    def count(self, text: str) -> int:
        """Return `text`'s token count under this checkpoint's tokenizer."""
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)


class TiktokenTokenizer:
    """A fixed ``tiktoken`` encoding for tests and offline work.

    It is selected explicitly, never a model-tokenizer fallback.
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """Load a ``tiktoken`` encoding by any name ``get_encoding`` accepts."""
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover -- optional extra
            raise ImportError(
                "TiktokenTokenizer needs `tiktoken` "
                f"(pip install 'smolbench[lean]'): {exc}"
            ) from exc
        self.name = f"tiktoken:{encoding_name}"
        self._encoding = tiktoken.get_encoding(encoding_name)

    def count(self, text: str) -> int:
        """Return `text`'s token count under this encoding."""
        return len(self._encoding.encode(text))


class VLLMTokenizer:
    """Count tokens through a vLLM server's ``/tokenize`` endpoint."""

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        """Bind to one served model.

        Strip ``/v1`` because vLLM serves ``/tokenize`` at the server root.

        Parameters
        ----------
        base_url : str
            OpenAI-compatible URL.
        model : str
            Model name.
        api_key : str
            Server bearer token.
        """
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            root = root[: -len("/v1")]
        self.name = f"vllm:{model}@{root}"
        self._url = f"{root}/tokenize"
        self._model = model
        self._api_key = api_key

    def count(self, text: str) -> int:
        """Count `text` through the live server.

        Parameters
        ----------
        text : str
            Prompt text.

        Returns
        -------
        int
            Server-reported token count.

        Raises
        ------
        requests.HTTPError
            On rejection.
        """
        response = requests.post(
            self._url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "prompt": text, "add_special_tokens": False},
            timeout=METADATA_TIMEOUT_S,
        )
        response.raise_for_status()
        return int(response.json()["count"])


@functools.lru_cache(maxsize=None)
def for_model(model: str) -> Tokenizer:
    """Return the tokenizer for served alias `model`.

    Import ``ec2`` lazily so environment-derived settings are not frozen early.

    Parameters
    ----------
    model : str
        ``ec2.EC2_DEPLOY_SPECS`` key.

    Returns
    -------
    Tokenizer
        Served checkpoint tokenizer.
    """
    from smolbench.evals.providers import ec2

    spec = ec2.EC2_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(
            f"no EC2_DEPLOY_SPECS entry for model {model!r}; pass a "
            "Tokenizer explicitly for models outside the spec table"
        )
    repo_id: str = spec.get("tokenizer_hf_id") or spec["hf_model_id"]
    logging.info(f"tokenization.for_model: {model!r} -> {repo_id}")
    return HFTokenizer.from_repo(repo_id)


# Mixed whitespace avoids BPE run merges; candidates are verified empirically.
WHITESPACE_UNITS: Tuple[str, ...] = (
    " \t", " \n\t", "\t ", " \n", "\t\n ",
    # Last to preserve earlier selections and byte-identical noise prompts.
    "\r",
    "\x0b",
)

# Mixed probes reject units that merge only on long runs or truncate counts.
_UNIT_PROBES: Tuple[int, ...] = (1, 64, 256, 2048)

# Reject runaway merging; exact search tolerates modest merging.
_UNIT_COST_TOLERANCE: float = 0.5

# Bound repeated full-prompt encodes; failure signals pathological tokenization.
_MAX_MATCH_ITERATIONS: int = 32


def choose_whitespace_unit(tokenizer: Tokenizer) -> str:
    """Pick a near-one-token whitespace pad atom.

    Parameters
    ----------
    tokenizer : Tokenizer
        Tokenizer to probe.

    Returns
    -------
    str
        Qualifying pad atom.

    Raises
    ------
    ValueError
        If no candidate qualifies.
    """
    for unit in WHITESPACE_UNITS:
        if all(
            abs(tokenizer.count(unit * n) - n) <= _UNIT_COST_TOLERANCE * n
            for n in _UNIT_PROBES
        ):
            return unit
    raise ValueError(
        f"no candidate in {WHITESPACE_UNITS!r} costs ~1 token per repetition "
        f"under tokenizer {getattr(tokenizer, 'name', tokenizer)!r}; a "
        "whitespace pad cannot be sized against it. Add a unit this "
        "tokenizer does not merge to WHITESPACE_UNITS."
    )




def token_matched_noise_prompt(
    render: Callable[[str], str],
    context: str,
    target_tokens: int,
    tokenizer: Tokenizer,
    unit: Optional[str] = None,
) -> str:
    """Render `context` with whitespace to an exact token count.

    Padding only grows prompts; unreachable targets raise to preserve the length control.

    Parameters
    ----------
    render : Callable[[str], str]
        Deterministic context renderer.
    context : str
        Context to pad.
    target_tokens : int
        Exact rendered token count.
    tokenizer : Tokenizer
        Model tokenizer.
    unit : str | None
        Pad atom; probes when omitted.

    Returns
    -------
    str
        Exact-length rendered prompt.
    """
    base: str = render(context)
    base_tokens: int = tokenizer.count(base)
    if base_tokens >= target_tokens:
        # Padding cannot shrink; returning unpadded would erase the control.
        raise ValueError(
            f"unpadded prompt is already {base_tokens} tokens, which is not "
            f"below the target of {target_tokens}; an appended pad can only "
            "GROW a prompt, never SHRINK one, so no whitespace pad reaches "
            "this target. The caller's precondition -- rendered context "
            "strictly shorter than target_tokens -- does not hold here."
        )

    pad_unit: str = unit if unit is not None else choose_whitespace_unit(tokenizer)

    # Re-measure each estimate and bracket it to prevent merge-driven oscillation.
    n: int = target_tokens - base_tokens
    lo: int = 0  # f(0) = base_tokens < target_tokens, per the guard above
    hi: Optional[int] = None
    for _ in range(_MAX_MATCH_ITERATIONS):
        prompt: str = render(context + pad_unit * n)
        got: int = tokenizer.count(prompt)
        if got == target_tokens:
            return prompt
        if got < target_tokens:
            lo = max(lo, n)
        else:
            hi = n if hi is None else min(hi, n)
        if hi is not None and hi - lo <= 1:
            break  # the bracket is exhausted: the count steps over the target
        estimate: int = n + (target_tokens - got)
        if estimate <= lo or (hi is not None and estimate >= hi):
            estimate = (lo + hi) // 2 if hi is not None else lo + 1
        n = estimate
    raise ValueError(
        f"could not pad to exactly {target_tokens} tokens with unit "
        f"{pad_unit!r} under tokenizer "
        f"{getattr(tokenizer, 'name', tokenizer)!r} "
        f"(unpadded prompt: {base_tokens} tokens; search bracketed to "
        f"{lo}..{hi} repetitions). The unit's token cost is not fine-grained "
        "enough to hit an exact target; add a better one to WHITESPACE_UNITS."
    )
