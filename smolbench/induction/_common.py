"""Share generation machinery between the induction benchmarks (periodic, chromatic).

The two benchmarks must stay CALIBRATED with each other: the noise-padding
ablation is only comparable across evals when the noise profile is identical,
and a given seed must map to the same label set in both. This module holds that
machinery once.

The noise pad is WHITESPACE, sized in TOKENS (:func:`token_matched_noise_prompt`)
against the tokenizer of the model under test and verified to hit the target
exactly. Characters are the wrong unit: models consume tokens, and a
character-matched pad over-pads the control arm (~1.6x at the periodic
production config).
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

    Contract: ``template`` MUST reference ``$positive_info`` (filled with the
    intensional, extensional, or noise-padded context) plus every key
    ``query_gen`` and ``substitution`` produce. Rendering uses
    ``string.Template.safe_substitute``, which SILENTLY leaves an unmatched or
    misspelled placeholder verbatim in the prompt instead of raising, so
    validate templates against a sample query before an expensive run.
    """

    #: Prompt template. See the placeholder contract in the class docstring.
    template: string.Template
    #: Static placeholder values merged into every query's substitutions.
    substitution: Dict[str, str]
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs. The exact mapping arguments are
    #: benchmark-specific; see each benchmark's built-in query generators.
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]
    #: Optional template for extensional prompts. Use this so the query
    #: representation can match the extensional context (e.g. chromatic's
    #: $query_years). Falls back to ``template`` when None.
    extens_template: Optional[string.Template] = None

    @property
    def resolved_extens_template(self) -> string.Template:
        """Return ``extens_template`` if the caller set one, else ``template``."""
        return self.extens_template or self.template


def build_substitution(
    query: Dict[str, str], prompter: Prompter, positive_info: str
) -> Dict[str, str]:
    """Merge a query's substitutions with the prompter's, plus positive_info.

    The one place that merge happens, so all three renderings in both
    benchmarks share one precedence: dict-union left-to-right over ``query``,
    ``prompter.substitution``, ``positive_info``, so ``positive_info`` wins a
    collision. Returns a fresh dict, so callers may mutate it further
    (chromatic's extensional renderer adds ``query_years``). Consumes no RNG.
    """
    return query | prompter.substitution | {"positive_info": positive_info}


def context_renderer(
    prompter: "Prompter",
    query: Dict[str, str],
    template: Optional[string.Template] = None,
) -> Callable[[str], str]:
    """Build one query's ``context -> rendered prompt`` function.

    :func:`token_matched_noise_prompt` needs one query's rendering as a reusable
    callable; binding ``query`` in a function scope also avoids closing over a
    loop variable at the call site. ``template`` defaults to
    ``prompter.template`` (what the intensional and noise-padded arms render
    with). The returned callable is deterministic and side-effect free.
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
        If ``length < ceil(log_{len(charset)}(n))``: too small a space to hold
        ``n`` unique strings.
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len = np.ceil(np.emath.logn(base, n))
    if length < min_len:
        raise ValueError(
            f"length={length} < {min_len} = ceil(log_{base}({n})): "
            f"insufficient length to generate {n} unique strings."
        )
    indices: np.ndarray = rng.choice(base ** length, size=n, replace=False)
    digits: np.ndarray = np.empty((n, length), dtype=np.int64)
    for idx in range(length - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    return OrderedSet("".join(row) for row in charset_array[digits])


# This factor multiplies the information-theoretic minimum label length
# (ceil(log_base(count))) when the code auto-generates random labels. A
# label space sized to the theoretic minimum is exactly full once `count`
# labels are drawn, so `random_unique_strings` would have zero slack to
# reject collisions during sampling. This factor doubles the length to give
# headroom: base**l grows exponentially in l, so even +1 already multiplies
# the space by `base`. This keeps unique sampling fast and lets it avoid
# exhausting the space in practice. This factor is a calibration invariant
# shared by both benchmarks' auto-generated labels and colors -- changing
# it changes label length, and therefore prompt length, for every
# benchmark at once.
LABEL_LENGTH_SAFETY_FACTOR: int = 2


def random_labels(
    count: int,
    seed: int,
    charset: Collection[str],
    min_length: int = 0,
) -> Tuple[str, ...]:
    """Auto-generate ``count`` unique random labels for a benchmark config.

    Both ``PeriodicConfig`` and ``ChromaticIntervalsConfig`` derive labels here,
    which is what keeps their label-length formulas calibrated. Length is
    ``max(min_length, ceil(log_{len(charset)}(count)) * LABEL_LENGTH_SAFETY_FACTOR)``;
    ``min_length=0`` (the default) adds no floor beyond that formula
    (chromatic), while periodic passes 2 so single-character labels are never
    auto-generated. RNG call order is fixed -- one fresh
    ``np.random.default_rng(seed)``, then one :func:`random_unique_strings`
    call -- so a seed always yields the same label set.
    """
    length: int = max(
        min_length,
        int(np.ceil(np.emath.logn(len(charset), count))) * LABEL_LENGTH_SAFETY_FACTOR,
    )
    return tuple(
        random_unique_strings(count, length, np.random.default_rng(seed), charset=charset)
    )


# This tuple lists whitespace units to try, in order, as the repeating pad
# atom. The unit must cost ~1 token per repetition under the tokenizer in
# play. This rules out the obvious candidates: BPE vocabularies carry
# dedicated tokens for RUNS of a single whitespace character, so `" " * 128`
# is ONE token in cl100k_base, and a pure-space pad cannot reach a large
# target. A unit that alternates two different whitespace characters
# defeats those run-merges -- `" \t"` measures at ~1 token per repetition
# in both cl100k_base and o200k_base. The rest are fallbacks for
# tokenizers that merge `" \t"`. `choose_whitespace_unit` verifies each
# candidate empirically; it does not trust this order.
WHITESPACE_UNITS: Tuple[str, ...] = (
    " \t", " \n\t", "\t ", " \n", "\t\n ",
    # This tuple appends "\r" and "\x0b" LAST, so every tokenizer that
    # already selected one of the units above keeps selecting it (this keeps
    # noise prompts byte-identical across studies). Gemma-4 and EXAONE-4.0
    # tokenizers merge EVERY mixed space/tab/newline run (Gemma ships
    # dedicated multi-whitespace tokens), so none of the units above cost
    # 1 token/rep there. A bare carriage return does: neither vocab has a
    # multi-\r merge.
    "\r",
    "\x0b",
)

# This tuple lists the repetition counts that `choose_whitespace_unit`
# probes. It mixes small and large counts, so it rejects a unit that merges
# only once a run gets long (the failure mode that makes a pad silently
# saturate below its target). The top probe deliberately goes past 1024: a
# `tokenizer.json` can embed a `truncation` stanza that caps every count
# (Nemotron-Ultra ships max_length 512). That cap would make a saturating
# tokenizer look linear at 256, then silently refuse to grow. A probe above
# any plausible cap turns that into a loud failure here, instead of a length
# control that is quietly wrong. `HFTokenizer` also disables truncation on
# load; this probe is the backstop for tokenizers built elsewhere.
_UNIT_PROBES: Tuple[int, ...] = (1, 64, 256, 2048)

# A unit qualifies when its marginal cost stays within this factor of 1
# token per repetition at every probe. The slack allows a boundary token, or
# a unit that costs 2 tokens for the first repetition and 1 token
# thereafter. It rejects any unit that compresses (cost -> 0) and so would
# never reach the target.
_UNIT_COST_TOLERANCE: float = 0.5

# This bounds the `token_matched_noise_prompt` search. Each pass costs one
# full re-encode of the prompt. The estimate-and-correct phase normally
# converges in 2-3 passes, and the bisection fallback needs about
# log2(pad length), roughly 15, more passes in the worst case. This bound is
# generous compared to both. If the search reaches it, the tokenizer
# behaves pathologically, and raising an exception is the right outcome.
_MAX_MATCH_ITERATIONS: int = 32


def choose_whitespace_unit(tokenizer) -> str:
    """Pick a whitespace pad atom that costs ~1 token per repetition.

    Whether a unit repeats linearly depends on the tokenizer's merge table, and
    these benchmarks run against whatever tokenizer the model under test uses,
    so the choice is probed empirically rather than hard-coded. ``tokenizer``
    is any :class:`~smolbench.evals.tokenization.Tokenizer`.

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

    The noise-padded ("length control") arm of both induction benchmarks. The
    pad is APPENDED, keeping the rules at the top of the prompt where the
    unpadded intensional arm puts them, and the match is on the whole RENDERED
    prompt, per query: query text differs in length per prompt and chromatic's
    extensional arm renders from a different template, so equal-token CONTEXTS
    would still give unequal-token PROMPTS. Consumes no RNG and takes no seed,
    so a replicate stays regenerable from its seed alone.

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
        `target_tokens` tokens. An unreachable target -- unpadded prompt
        already that long -- returns the unpadded render and logs a warning.

    Raises
    ------
    ValueError
        If the search cannot land on `target_tokens`; a close-but-inexact
        prompt would reintroduce the length confound invisibly.
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

    # This search estimates, then corrects, then (only if needed) bisects.
    #
    # The unit costs ~1 token, so the token deficit is itself a near-exact
    # estimate of how many repetitions are missing. The first probe usually
    # lands within a token or two, and the correction step finishes the job.
    # Every pass re-measures the WHOLE rendered prompt. This is what absorbs
    # the second-order effects no estimate can predict: merges where the pad
    # abuts the context, and merges between the pad and whatever the
    # template renders after it.
    #
    # Correction alone can oscillate (n -> n+3 -> n -> ...) when those merges
    # make the local token cost jump around. So the probes also maintain a
    # bracket: `lo` repetitions land below the target, `hi` above it. Once
    # the bracket is established, this search replaces any estimate that
    # escapes it with the midpoint. This turns a potential oscillation into
    # a bisection that must terminate. A bracket that closes to adjacent
    # values without an exact hit means the token count JUMPS over the
    # target: no repetition count satisfies the request. That is a genuine
    # failure, not something to paper over.
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
    that order. ``qna_cls`` is the question type (``ToF`` for True/False,
    ``Numeric`` for integers); its ``__post_init__`` validates the answers.
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in prompts:
        intens_quiz.append(qna_cls(prompt=intens, answer=answer))
        extens_quiz.append(qna_cls(prompt=extens, answer=answer))
        noise_intens_quiz.append(qna_cls(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)
