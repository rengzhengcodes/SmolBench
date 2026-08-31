"""Generation machinery behind the induction benchmark (periodic).

Kept separate from ``periodic.py`` so the calibration invariants live in one
place: the noise-padding ablation is comparable across evals only when the
noise profile is identical, and a seed must always map to the same label set.
(``smolbench.deduction.lean.context`` reuses the pad search below for the same
reason.)

The noise pad is WHITESPACE sized in TOKENS (:func:`token_matched_noise_prompt`)
under the tokenizer of the model under test, verified to hit the target exactly.
Characters are the wrong unit -- a character-matched pad over-pads the control
arm ~1.6x at the periodic production config (an ad-hoc design-time
measurement; the load-bearing invariant is the verified per-prompt token
exactness, not that ratio).
"""

import logging
import string
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, Iterable, Optional, Tuple

import numpy as np
from ordered_set import OrderedSet

from smolbench.evals import Answer, QnA, Quiz


@dataclass(frozen=True, slots=True)
class Prompter:
    """Bundle everything needed to prompt an LLM with a generated context.

    Placeholder contract: ``template`` MUST reference ``$positive_info`` (the
    intensional, extensional or noise-padded context) plus every key
    ``query_gen`` and ``substitution`` produce. Rendering uses
    ``safe_substitute``, which SILENTLY leaves a misspelled placeholder verbatim
    instead of raising, so validate templates on a sample query first.
    ``safe_substitute`` (not ``substitute``) is deliberate: a literal ``$`` in
    quiz text must not raise mid-study, and the golden-quiz hash pins
    (``tests/induction/test_golden_quizzes.py``) already fail on any drift in
    the rendered prompts.
    """

    #: Prompt template. See the placeholder contract in the class docstring.
    template: string.Template
    #: Static placeholder values merged into every query's substitutions.
    substitution: Dict[str, str]
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs; the mapping arguments are
    #: benchmark-specific (see each benchmark's built-in query generators).
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]
    #: Optional extensional-prompt template, so the query representation can
    #: match the extensional context. Falls back to ``template`` when None.
    extens_template: Optional[string.Template] = None

    @property
    def resolved_extens_template(self) -> string.Template:
        """Return ``extens_template`` if the caller set one, else ``template``."""
        return self.extens_template or self.template


def build_substitution(
    query: Dict[str, str], prompter: Prompter, positive_info: str
) -> Dict[str, str]:
    """Merge a query's substitutions with the prompter's, plus positive_info.

    The single merge point for all three renderings, so precedence is uniform:
    dict-union in the order ``query``, ``prompter.substitution``,
    ``positive_info``, the last winning a collision: the static
    ``prompter.substitution`` outranks the query so a ``query_gen`` cannot
    silently override a study-pinned field, and the arm's context comes last
    because every arm must control it. Returns a fresh dict, so callers may
    mutate it further.
    """
    return query | prompter.substitution | {"positive_info": positive_info}


def context_renderer(
    prompter: "Prompter",
    query: Dict[str, str],
    template: Optional[string.Template] = None,
) -> Callable[[str], str]:
    """Build one query's deterministic ``context -> rendered prompt`` function.

    :func:`token_matched_noise_prompt` needs the rendering as a reusable
    callable; binding ``query`` in a function scope also avoids closing over a
    loop variable at the call site. ``template`` defaults to
    ``prompter.template``, the intensional and noise-padded arms' template.
    """
    resolved: string.Template = template if template is not None else prompter.template

    def render(context: str) -> str:
        return resolved.safe_substitute(build_substitution(query, prompter, context))

    return render


def random_unique_strings(
    n: int,
    length: int,
    rng: np.random.Generator,
    charset: Collection[str],
) -> OrderedSet[str]:
    """Generate ``n`` unique random strings of length ``length`` over ``charset``.

    Samples integers in ``[0, base**length)`` without replacement and
    base-expands each, so uniqueness is exact at ``O(n * length)`` however
    densely the space is sampled. ``charset`` must exclude any separator in use
    downstream.

    Raises
    ------
    ValueError
        If ``length < ceil(log_{len(charset)}(n))``: too small a space for ``n``
        unique strings.
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len = np.ceil(np.emath.logn(base, n))
    if length < min_len:
        raise ValueError(
            f"length={length} < {min_len} = ceil(log_{base}({n})): "
            f"insufficient length to generate {n} unique strings."
        )
    if base**length > np.iinfo(np.int64).max:
        # rng.choice needs the population to fit in int64; past that it dies
        # with an opaque numpy OverflowError, so raise this module's own
        # message first. Unreachable at any in-repo config (max space is 26^4).
        raise ValueError(
            f"{base}**{length} exceeds the int64 sample space rng.choice "
            f"supports; reduce length (or count, which drives it)."
        )
    indices: np.ndarray = rng.choice(base ** length, size=n, replace=False)
    digits: np.ndarray = np.empty((n, length), dtype=np.int64)
    for idx in range(length - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    # OrderedSet, not tuple: the type documents the uniqueness contract and
    # keeps draw order (a plain set would de-determinize iteration); its dedup
    # is provably inert, since the draws are without replacement.
    return OrderedSet("".join(row) for row in charset_array[digits])


# Multiplies the information-theoretic minimum label length
# (ceil(log_base(count))) for auto-generated labels. At exactly that minimum the
# space is full once `count` labels are drawn, leaving `random_unique_strings`
# zero slack; doubling the length gives headroom, since base**l grows
# exponentially in l. A calibration invariant for every auto-generated label
# set -- changing it changes label length, and so prompt length, for every
# config at once.
LABEL_LENGTH_SAFETY_FACTOR: int = 2


def random_labels(
    count: int,
    seed: int,
    charset: Collection[str],
    min_length: int = 0,
) -> Tuple[str, ...]:
    """Auto-generate ``count`` unique random labels for a benchmark config.

    Length is
    ``max(min_length, ceil(log_{len(charset)}(count)) * LABEL_LENGTH_SAFETY_FACTOR)``;
    ``min_length=0`` adds no floor, periodic passes 2 so
    single-character labels are never auto-generated. RNG call order is fixed --
    one fresh ``np.random.default_rng(seed)``, then one
    :func:`random_unique_strings` call -- so a seed always yields the same set.
    """
    # Floor of 1: at count=1, min_length=0 the information-theoretic minimum
    # is 0 and the "label" would be the empty string.
    length: int = max(
        min_length,
        1,
        int(np.ceil(np.emath.logn(len(charset), count))) * LABEL_LENGTH_SAFETY_FACTOR,
    )
    return tuple(
        random_unique_strings(count, length, np.random.default_rng(seed), charset=charset)
    )


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


def choose_whitespace_unit(tokenizer) -> str:
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
    tokenizer,
    unit: Optional[str] = None,
) -> str:
    """Render `context` padded with whitespace to hit an exact token count.

    The noise-padded ("length control") arm. The pad is APPENDED, keeping the
    rules where the unpadded intensional arm puts them, and the match is on the
    whole RENDERED prompt, per query: query text length varies (and an
    ``extens_template`` can render from a different template), so equal-token
    CONTEXTS would still give unequal-token PROMPTS. Consumes no RNG and takes
    no seed, so a replicate stays regenerable from its seed alone.

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
        `target_tokens` tokens. An unreachable target -- unpadded prompt already
        that long -- returns the unpadded render and logs a warning rather
        than raising: an appended pad cannot SHRINK a prompt, and reuse sites
        pad contexts that legitimately exceed the target. Callers for which an
        over-long base is a fatal confound must check the result (the study
        notebook asserts exact matches; production has ~200x headroom).

    Raises
    ------
    ValueError
        If the search cannot land on `target_tokens`; a close-but-inexact prompt
        would reintroduce the length confound invisibly.
    """
    base: str = render(context)
    base_tokens: int = tokenizer.count(base)
    if base_tokens >= target_tokens:
        logging.warning(
            f"token_matched_noise_prompt: unpadded prompt is already "
            f"{base_tokens} tokens >= target {target_tokens}; returning it "
            "unpadded (the length control cannot be built by appending)"
        )
        return base

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
    lo: int = 0  # f(0) = base_tokens < target_tokens, per the early return
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


def quizzes_from_prompts(
    prompts: Iterable[Tuple[str, str, str, Answer]],
    qna_cls: type[QnA],
) -> Tuple[Quiz, Quiz, Quiz]:
    """Wrap (intens, extens, noise_intens, answer) tuples into three quizzes.

    Returns the intensional, extensional and noise-padded intensional Quiz, in
    that order. ``qna_cls`` is the question type (``ToF`` / ``Numeric``); its
    ``__post_init__`` validates the answers.
    """
    intens_quiz: list[QnA] = []
    extens_quiz: list[QnA] = []
    noise_intens_quiz: list[QnA] = []
    for intens, extens, noise_intens, answer in prompts:
        intens_quiz.append(qna_cls(prompt=intens, answer=answer))
        extens_quiz.append(qna_cls(prompt=extens, answer=answer))
        noise_intens_quiz.append(qna_cls(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)
