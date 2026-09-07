"""Tokenize prompts for the model under test, to size token-matched prompts.

The induction ``noise_intens`` arm pads the intensional prompt to the extensional prompt's
length, so an intens-vs-extens gap can't be blamed on prompt length. Length means tokens under
the tested model's own tokenizer, not characters: a character-matched pad measured 1.62x the
target token count at the periodic production config. `for_model` maps an eval model alias to
that checkpoint's `Tokenizer`.

Pad content is whitespace only, not random alphanumerics: whitespace carries no token-level
information a model can condition on, so the padded arm differs from the intensional arm in
length alone, where random content would add an unmeasured distractor-content confound. Known
cost: whitespace padding is harder on the output contract in some models --
``notebooks/induction/analysis/extens_vs_noise.py`` measures this per lane rather than hiding it.

Every constructor raises rather than falling back when it cannot load its tokenizer: a count
fixes prompt bytes, so a silent fallback would pad differently under the same seed and break
byte-for-byte regeneration of a replicate from its ``rep_{seed}.yaml`` filename.
"""

import functools
import logging
from typing import Any, Callable, Optional, Protocol, Tuple, runtime_checkable

import requests

from smolbench.evals.openai_compat import METADATA_TIMEOUT_S


@runtime_checkable
class Tokenizer(Protocol):
    """Anything that can count a string's tokens for the model under test.

    Structural, not nominal, so the offline test suite can drive token matching
    with a deterministic stub.
    """

    #: Human-readable identity (repo id, encoding name, served model...). Free-form; used only
    #: in logs and errors, so a token-match failure can name which tokenizer was in play.
    name: str

    def count(self, text: str) -> int:
        """Return the number of tokens `text` encodes to.

        Must exclude special/BOS tokens: both compared prompts get the same chat-template wrap
        downstream, so an inconsistent offset becomes an off-by-N in the match.

        Parameters
        ----------
        text : str
            Text to tokenize.

        Returns
        -------
        int
            Token count of `text`.
        """
        ...


class HFTokenizer:
    """A model's own tokenizer, loaded from its HuggingFace ``tokenizer.json``.

    Built on ``huggingface_hub`` + ``tokenizers``, not ``transformers``:
    counting needs one file and the Rust BPE that reads it, not torch.
    """

    def __init__(self, name: str, tokenizer: Any) -> None:
        """Wrap an already-constructed ``tokenizers.Tokenizer``.

        Prefer `from_repo`; this stays public so a local-checkout or test-fixture tokenizer
        can be adapted without network.

        Parameters
        ----------
        name : str
            Name of the wrapped tokenizer.
        tokenizer : Any
            duck-typed on ``encode(text, add_special_tokens=False).ids``.
        """
        self.name = name
        self._tokenizer = tokenizer

    @classmethod
    def from_repo(cls, repo_id: str) -> "HFTokenizer":
        """Download (once, then cached) and load `repo_id`'s tokenizer.

        Fetches only ``tokenizer.json`` into ``~/.cache/huggingface``, not the weights, so only
        the first call needs network. Disables truncation and padding on load: an embedded
        ``truncation`` stanza is otherwise honored on every ``encode`` (one Nemotron
        redistribution ships ``max_length: 512`` and silently reports a ~26,000-token prompt as
        512), and a padded batch would count tokens the model never sees.

        Parameters
        ----------
        repo_id : str
            HuggingFace repository containing ``tokenizer.json``.

        Returns
        -------
        HFTokenizer
            the loaded tokenizer.

        Raises
        ------
        RuntimeError
            naming the ``tokenizer_hf_id`` deploy-spec override, when the repo ships no
            ``tokenizer.json`` (common for quantized redistributions) or the fetch fails.
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
    """A fixed ``tiktoken`` encoding, for tests and offline/tokenizer-free work.

    NOT a stand-in for the model under test: ``cl100k_base`` is nobody's
    tokenizer among the served checkpoints, and nothing falls back to it -- a
    caller selects it explicitly.
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
    """Count tokens by asking a LIVE vLLM server's ``/tokenize`` endpoint.

    Ground truth for what the served model sees, hence the cross-check that
    `HFTokenizer` loaded the right tokenizer. NOT for the prompt-building hot
    path: sizing one pad takes several ``count`` calls per question, and an HTTP
    round trip per call on a ~55 KB prompt would dwarf the eval.
    """

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        """Bind to one served model on one vLLM server.

        `base_url` is the OpenAI-compatible base URL (``ec2._base_url()``); vLLM
        serves ``/tokenize`` at the SERVER root, not under ``/v1``, so a trailing
        ``/v1`` is stripped here.

        Parameters
        ----------
        base_url : str
            OpenAI-compatible base URL.
        model : str
            Served model name.
        api_key : str
            Bearer token for the server.
        """
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            root = root[: -len("/v1")]
        self.name = f"vllm:{model}@{root}"
        self._url = f"{root}/tokenize"
        self._model = model
        self._api_key = api_key

    def count(self, text: str) -> int:
        """Return `text`'s token count as reported by the live server.

        vLLM exposes ``/tokenize`` by default, so a 404 means the server predates it or disabled
        it.

        Parameters
        ----------
        text : str
            Prompt text to tokenize.

        Returns
        -------
        int
            the server-reported token count.

        Raises
        ------
        requests.HTTPError
            on rejection.
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
    """Return the tokenizer of the checkpoint served under alias `model`.

    Memoized per alias for the life of the process.

    ``ec2`` is imported inside this function, not at module scope: its ``EC2_*`` constants are
    read from ``os.environ`` at import time, so an eager import would freeze them for a notebook
    that imports the induction stack before ``load_dotenv(keys.env)`` (see
    ``smolbench.evals.experiment``).

    Parameters
    ----------
    model : str
        A key of ``ec2.EC2_DEPLOY_SPECS``; the tokenizer comes from that spec's
        ``hf_model_id``, or its ``tokenizer_hf_id`` override for weights-only quantized repos.

    Returns
    -------
    Tokenizer
        The tokenizer for the served checkpoint.
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


# Whitespace pad atoms tried in order; a unit must cost ~1 token/repetition under the tokenizer
# in play. BPE vocabularies carry dedicated tokens for runs of a single whitespace character
# (`" " * 128` is one token in cl100k_base), so a pure-space pad can't reach a large target.
# Alternating two characters defeats those run-merges (`" \t"` measures ~1 token/rep in
# cl100k_base and o200k_base); the rest are fallbacks for tokenizers that merge `" \t"`.
# `choose_whitespace_unit` verifies each candidate empirically rather than trusting this order.
WHITESPACE_UNITS: Tuple[str, ...] = (
    " \t", " \n\t", "\t ", " \n", "\t\n ",
    # "\r" and "\x0b" go last so a tokenizer that already selected an earlier unit keeps
    # selecting it (noise prompts stay byte-identical across studies). Gemma-4 and EXAONE-4.0
    # merge every mixed space/tab/newline run, so none of the units above cost 1 token/rep
    # there; a bare carriage return does.
    "\r",
    "\x0b",
)

# Repetition counts `choose_whitespace_unit` probes, small and large mixed so a unit that only
# merges once a run gets long is rejected (that failure mode silently saturates a pad below its
# target). The top probe goes past 1024 because a `tokenizer.json` can embed a `truncation`
# stanza capping every count (one Nemotron redistribution ships max_length 512), which would
# make a saturating tokenizer look linear at 256; `HFTokenizer` disables truncation on load,
# so this probe backstops tokenizers built elsewhere.
_UNIT_PROBES: Tuple[int, ...] = (1, 64, 256, 2048)

# Multiplicative cost bound: at the n=1 probe it forces exactly one token, while larger probes
# tolerate up to 2:1 merging (harmless, since the verified search below supplies exactness and
# a half-density unit just pads with twice the characters). Exists to reject runaway merging
# (cost -> 0), which no character length could compensate.
_UNIT_COST_TOLERANCE: float = 0.5

# Bounds the `token_matched_noise_prompt` search; each pass re-encodes the whole prompt.
# Estimate-and-correct normally converges in 2-3 passes; the bisection fallback needs about
# log2(pad length), roughly 15 more in the worst case. Reaching this bound means the tokenizer
# behaves pathologically, and raising is the right outcome.
_MAX_MATCH_ITERATIONS: int = 32


def choose_whitespace_unit(tokenizer: Tokenizer) -> str:
    """Pick a whitespace pad atom that costs ~1 token per repetition.

    Probed empirically against the given tokenizer's merge table rather than hard-coded, since
    the model under test supplies the tokenizer.

    Parameters
    ----------
    tokenizer : Tokenizer
        Tokenizer whose merge table is probed.

    Returns
    -------
    str
        The qualifying whitespace pad atom.

    Raises
    ------
    ValueError
        If no candidate in :data:`WHITESPACE_UNITS` qualifies: a loud failure beats a pad that
        silently saturates, leaving the length-control arm shorter than the arm it controls for.
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
    """Render `context` padded with whitespace to hit an exact token count.

    The noise-padded ("length control") arm. The pad is appended, keeping the rules where the
    unpadded intensional arm puts them; matching is on the whole rendered prompt, since per-query
    text length varies (equal-token contexts would still give unequal-token prompts). Consumes
    no RNG, so a replicate stays regenerable from its seed alone. Result is verified, never
    assumed, to be exactly `target_tokens`; every unreachable target raises instead.

    Precondition: ``tokenizer.count(render(context)) < target_tokens``, strictly -- an appended
    pad can only grow a prompt. Raises ValueError if that fails, or if the search can't land on
    an exact count (a close-but-inexact prompt would reintroduce the length confound invisibly).

    Parameters
    ----------
    render : Callable[[str], str]
        Called repeatedly, so it must be cheap and deterministic.
    context : str
        Context to pad with whitespace.
    target_tokens : int
        Exact token count for the rendered prompt.
    tokenizer : Tokenizer
        Must be the model under test's, or the control de-calibrates by however much the
        two tokenizers disagree.
    unit : str | None
        Defaults to :func:`choose_whitespace_unit`'s pick; pass it to skip the probe when
        padding many prompts with one tokenizer.

    Returns
    -------
    str
        Rendered prompt with exact target token count.
    """
    base: str = render(context)
    base_tokens: int = tokenizer.count(base)
    if base_tokens >= target_tokens:
        # Raise, don't warn-and-return the unpadded render: an unchecked short-circuit here
        # would ship the "length control" arm byte-identical to the arm it controls for (this
        # fired at the periodic config for n <= 2, where the extensional listing isn't strictly
        # longer than the intensional rules).
        raise ValueError(
            f"unpadded prompt is already {base_tokens} tokens, which is not "
            f"below the target of {target_tokens}; an appended pad can only "
            "GROW a prompt, never SHRINK one, so no whitespace pad reaches "
            "this target. The caller's precondition -- rendered context "
            "strictly shorter than target_tokens -- does not hold here."
        )

    pad_unit: str = unit if unit is not None else choose_whitespace_unit(tokenizer)

    # Estimate from the token deficit (the unit costs ~1 token, so the deficit approximates the
    # missing repetitions), then correct by re-measuring the whole rendered prompt each pass,
    # since merges aren't predictable from an estimate alone. Correction alone can oscillate
    # when merges shift the local cost, so a bracket (`lo` below target, `hi` above) is kept and
    # any estimate that escapes it is replaced by the midpoint, turning oscillation into a
    # terminating bisection. A bracket that closes to adjacent values without an exact hit means
    # the token count jumps over the target: no repetition count satisfies the request.
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

