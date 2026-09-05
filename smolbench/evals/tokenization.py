"""Tokenize prompts for the model under test, to size token-matched prompts.

The induction ``noise_intens`` arm pads the intensional (rule) prompt to the
extensional (listing) prompt's length, so an intens-vs-extens gap cannot be
blamed on prompt length. Length means TOKENS under the tested model's OWN
tokenizer, not characters: at the periodic production config (``n=9``, seed
1776, ``cl100k_base``) a character-matched pad ran 1.62x the extensional
prompt's 26,279 tokens. `for_model` maps an eval model alias (also vLLM's
``--served-model-name``) to that checkpoint's `Tokenizer`.

Pad CONTENT is whitespace only, which is a separate choice from the unit and
needs its own justification. Whitespace carries no token-level information a
model can condition on, so the padded arm differs from the unpadded intensional
arm in LENGTH and nothing else -- exactly the one variable this control exists
to vary. Random alphanumerics (an earlier, since-deleted generator padded with
letters + digits + whitespace) inject spurious tokens the model may try to
interpret as part of the task, confounding the length control with an
unmeasured distractor-content effect. The KNOWN COST, stated honestly rather
than sold as free: whitespace padding is harder on the OUTPUT CONTRACT.
``notebooks/induction/analysis/extens_vs_noise.py`` measures per-lane
non-compliance on both arms and buckets a substantial minority of models into
"padding-robustness collapse" (noise arm largely non-compliant), where
``extens > noise`` is mechanically forced and the row is a padding finding, not
evidence about information. That is a measured trade-off accepted with the
mechanism made visible, not a win.

NO SILENT FALLBACKS: every constructor raises when it cannot load its
tokenizer. A count fixes PROMPT BYTES, so a fallback would pad differently
under the same seed and break byte-for-byte regeneration of a replicate from
its ``rep_{seed}.yaml`` filename.
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

    #: Human-readable identity (repo id, encoding name, served model...).
    #: Free-form: it appears only in logs and errors, so a token-match failure
    #: names WHICH tokenizer could not reach the target.
    name: str

    def count(self, text: str) -> int:
        """Return the number of tokens `text` encodes to.

        Implementations MUST exclude special/BOS tokens: the chat template wraps
        both compared prompts identically downstream, so an inconsistent offset
        becomes an off-by-N in the match.
        """
        ...


class HFTokenizer:
    """A model's own tokenizer, loaded from its HuggingFace ``tokenizer.json``.

    Built on ``huggingface_hub`` + ``tokenizers``, not ``transformers``:
    counting needs one file and the Rust BPE that reads it, not torch.
    """

    def __init__(self, name: str, tokenizer: Any) -> None:
        """Wrap an already-constructed ``tokenizers.Tokenizer``.

        Prefer `from_repo`; this stays public so a local-checkout or
        test-fixture tokenizer can be adapted without network.

        Parameters
        ----------
        tokenizer : Any
            Duck-typed on ``encode(text, add_special_tokens=False).ids``.
        """
        self.name = name
        self._tokenizer = tokenizer

    @classmethod
    def from_repo(cls, repo_id: str) -> "HFTokenizer":
        """Download (once, then cached) and load `repo_id`'s tokenizer.

        Fetches only ``tokenizer.json`` (a few MB, not the weights) into
        ``~/.cache/huggingface``, so only the first call needs network.
        Disabling truncation and padding on load is load-bearing: an embedded
        ``truncation`` stanza is honored on every ``encode``
        (``nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8`` ships
        ``{"max_length": 512}``, reporting a ~26,000-token prompt as 512), and
        a padded batch counts tokens the model never sees.

        Raises
        ------
        ImportError
            ``huggingface_hub`` or ``tokenizers`` is not installed.
        RuntimeError
            The repo ships no ``tokenizer.json`` (common for quantized
            redistributions), or the fetch failed; the message names the
            ``tokenizer_hf_id`` deploy-spec key that overrides the source repo.
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
        """Load a ``tiktoken`` encoding by any name ``get_encoding`` accepts.

        Raises
        ------
        ImportError
            ``tiktoken`` (the ``lean`` extra, not a core dependency) is missing.
        """
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

        Raises
        ------
        requests.HTTPError
            The endpoint rejected the request; vLLM exposes ``/tokenize`` by
            default, so a 404 means the server predates it or disabled it.
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

    `model` is a key of ``ec2.EC2_DEPLOY_SPECS``; the tokenizer comes from that
    spec's ``hf_model_id``, or its ``tokenizer_hf_id`` override for weights-only
    quantized repos. Memoized per alias for the life of the process.

    ``ec2`` is imported INSIDE this function: its ``EC2_*`` constants are read
    from ``os.environ`` at IMPORT time, so an eager import would freeze them for
    a notebook importing the induction stack before ``load_dotenv(keys.env)``
    (see ``smolbench.evals.experiment``).

    Raises
    ------
    KeyError
        No deploy spec names `model`; such a caller must build and pass a
        `Tokenizer` itself.
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


# ---------------------------------------------------------------------------
# Token-matched whitespace padding: public API. Originally lived in
# smolbench.induction._common, which imports these names back (never copies
# them -- see that module's own comment) so existing callers keep resolving.
# ---------------------------------------------------------------------------

# Whitespace units tried, in order, as the repeating pad atom; a unit must cost
# ~1 token per repetition under the tokenizer in play. BPE vocabularies carry
# dedicated tokens for RUNS of a single whitespace character (`" " * 128` is ONE
# token in cl100k_base), so a pure-space pad cannot reach a large target.
# Alternating two whitespace characters defeats those run-merges: `" \t"`
# measures ~1 token/rep in both cl100k_base and o200k_base. The rest are
# fallbacks for tokenizers that merge `" \t"`. `choose_whitespace_unit` verifies
# each candidate empirically; it does not trust this order.
WHITESPACE_UNITS: Tuple[str, ...] = (
    " \t", " \n\t", "\t ", " \n", "\t\n ",
    # "\r" and "\x0b" go LAST so every tokenizer that already selected a unit
    # above keeps selecting it (noise prompts stay byte-identical across
    # studies). Gemma-4 and EXAONE-4.0 merge EVERY mixed space/tab/newline run
    # (Gemma ships dedicated multi-whitespace tokens), so none of the units
    # above cost 1 token/rep there; a bare carriage return does, as neither
    # vocab has a multi-\r merge.
    "\r",
    "\x0b",
)

# Repetition counts `choose_whitespace_unit` probes. Small and large mixed, so
# it rejects a unit that merges only once a run gets long (the failure mode that
# silently saturates a pad below its target). The top probe deliberately goes
# past 1024: a `tokenizer.json` can embed a `truncation` stanza capping every
# count (Nemotron-Ultra ships max_length 512), which would make a saturating
# tokenizer look linear at 256 and then silently refuse to grow. `HFTokenizer`
# disables truncation on load; this probe backstops tokenizers built elsewhere.
_UNIT_PROBES: Tuple[int, ...] = (1, 64, 256, 2048)

# A unit qualifies when its total cost stays within this factor of n tokens
# at every probe. The bound is multiplicative: at the n=1 probe integer
# counts force EXACTLY one token (a 2-token first repetition is rejected),
# while larger probes tolerate up to 2:1 merging -- harmless, since the
# verified search below supplies exactness and a half-density unit just pads
# with twice the characters. The gate exists to reject runaway merging
# (cost -> 0), which no character length could compensate.
_UNIT_COST_TOLERANCE: float = 0.5

# Bounds the `token_matched_noise_prompt` search; each pass costs one full
# re-encode of the prompt. Estimate-and-correct normally converges in 2-3
# passes, and the bisection fallback needs about log2(pad length), roughly 15,
# more in the worst case. Reaching this bound means the tokenizer behaves
# pathologically, and raising is the right outcome.
_MAX_MATCH_ITERATIONS: int = 32


def choose_whitespace_unit(tokenizer: Tokenizer) -> str:
    """Pick a whitespace pad atom that costs ~1 token per repetition.

    Whether a unit repeats linearly depends on the tokenizer's merge table, and
    the model under test supplies the tokenizer, so the choice is probed
    empirically rather than hard-coded.

    Returns
    -------
    str
        First unit in :data:`WHITESPACE_UNITS` whose measured cost stays within
        :data:`_UNIT_COST_TOLERANCE` of 1 token/repetition at every probe in
        :data:`_UNIT_PROBES`.

    Raises
    ------
    ValueError
        If no candidate qualifies -- a loud failure beats a pad that silently
        saturates, leaving the "length control" arm shorter than the arm it
        controls for.
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

    The noise-padded ("length control") arm. The pad is APPENDED, keeping the
    rules where the unpadded intensional arm puts them, and the match is on the
    whole RENDERED prompt, per query: query text length varies from query to
    query, so equal-token CONTEXTS would still give unequal-token PROMPTS.
    Consumes no RNG and takes no seed, so a replicate stays regenerable from its
    seed alone.

    PRECONDITION: ``tokenizer.count(render(context)) < target_tokens``,
    STRICTLY. An appended pad can only grow a prompt, so a base that already
    meets or exceeds the target is unreachable and raises (see `Raises`).

    Parameters
    ----------
    render : Callable[[str], str]
        ``context -> prompt``; called repeatedly, so it must be cheap and
        DETERMINISTIC (a varying render would measure some other prompt).
    target_tokens : int
        In practice ``tokenizer.count(extens)`` for the matching extensional
        prompt.
    tokenizer : Tokenizer
        MUST be the model under test's (``tokenization.for_model(model)``), or
        the control de-calibrates by however much the two disagree.
    unit : str, optional
        Pad atom; defaults to :func:`choose_whitespace_unit`'s pick. Pass it to
        skip the probe when padding many prompts with one tokenizer.

    Returns
    -------
    str
        ``render(context + pad)``, verified (never assumed) EXACTLY
        `target_tokens` tokens. There is no other return: every unreachable
        target raises, so a caller never has to check the result to learn
        whether the length control was actually built.

    Raises
    ------
    ValueError
        If the precondition above fails -- the unpadded prompt already costs
        ``>= target_tokens`` -- since an appended pad cannot SHRINK a prompt.
    ValueError
        If the search cannot land on `target_tokens`; a close-but-inexact prompt
        would reintroduce the length confound invisibly.
    """
    base: str = render(context)
    base_tokens: int = tokenizer.count(base)
    if base_tokens >= target_tokens:
        # Raise, never warn-and-return the unpadded render: no caller checked
        # the returned length, so the "length control" arm silently shipped
        # BYTE-IDENTICAL to the intensional arm it controls for whenever this
        # branch fired (measured at the periodic config for n <= 2, where the
        # extensional listing is not strictly longer than the intensional
        # rules). A confounded arm that looks collected is worse than a run
        # that stops.
        raise ValueError(
            f"unpadded prompt is already {base_tokens} tokens, which is not "
            f"below the target of {target_tokens}; an appended pad can only "
            "GROW a prompt, never SHRINK one, so no whitespace pad reaches "
            "this target. The caller's precondition -- rendered context "
            "strictly shorter than target_tokens -- does not hold here."
        )

    pad_unit: str = unit if unit is not None else choose_whitespace_unit(tokenizer)

    # Estimate, then correct, then (only if needed) bisect. The unit costs ~1
    # token, so the token deficit is a near-exact estimate of the missing
    # repetitions. Every pass re-measures the WHOLE rendered prompt, absorbing
    # the merges no estimate can predict: pad against context, and pad against
    # whatever the template renders after it.
    #
    # Correction alone can oscillate (n -> n+3 -> n -> ...) when those merges
    # make the local token cost jump around, so the probes also maintain a
    # bracket (`lo` below the target, `hi` above) and replace any estimate that
    # escapes it with the midpoint -- turning oscillation into a terminating
    # bisection. A bracket that closes to adjacent values without an exact hit
    # means the token count JUMPS over the target: no repetition count satisfies
    # the request, a genuine failure.
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

