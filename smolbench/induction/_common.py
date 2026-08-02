"""
Generation machinery shared by the induction benchmarks (periodic, chromatic).

The two benchmarks must stay CALIBRATED against each other: the noise-padding
ablation is only comparable across evals if the noise profile is identical,
and the random-label sampler fixes how fresh seeds map to fresh label sets.
Keeping these here, once, is what enforces that.

The noise pad is WHITESPACE sized in TOKENS (`token_matched_noise_prompt`),
not random characters sized in characters. Characters were the wrong unit:
models consume tokens, and random alphanumerics tokenize far worse than
structured text, so a character-matched pad silently over-padded the control
arm -- 42,639 tokens against a 26,279-token extensional target at the
periodic production config, 1.62x the length it was supposed to match. The
pad is now built against the tokenizer of the model under test and verified
to hit its target exactly; see `smolbench.evals.tokenization`.
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
    """Everything needed to prompt an LLM given a generated context.

    Contract: ``template`` MUST reference ``$positive_info`` (filled with the
    intensional / extensional / noise-padded context) plus every key produced
    by ``query_gen`` and ``substitution``. Rendering uses
    ``string.Template.safe_substitute``, so an unmatched or misspelled
    placeholder is SILENTLY left verbatim in the prompt rather than raising --
    validate templates against a sample query before an expensive run.
    """

    #: Prompt template; see the placeholder contract in the class docstring.
    template: string.Template
    #: Static placeholder values merged into every query's substitutions.
    substitution: Dict[str, str]
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs; the exact mapping arguments are
    #: benchmark-specific (see each benchmark's built-in query generators).
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]
    #: Optional template for extensional prompts, so the query representation
    #: can match the extensional context (e.g. chromatic's $query_years).
    #: Falls back to ``template`` when None.
    extens_template: Optional[string.Template] = None

    @property
    def resolved_extens_template(self) -> string.Template:
        """The template to use for rendering the extensional prompt.

        Returns ``extens_template`` when the caller set one, otherwise falls
        back to ``template`` -- the same fallback both benchmarks need, so
        it lives on the shared ``Prompter`` rather than being reimplemented
        (identically) at each call site.

        Returns
        -------
        string.Template
            ``self.extens_template`` if not None, else ``self.template``.
        """
        return self.extens_template or self.template


def build_substitution(
    query: Dict[str, str], prompter: Prompter, positive_info: str
) -> Dict[str, str]:
    """Merges a query's substitutions with the prompter's, plus positive_info.

    Every rendered prompt (intensional, extensional, noise-padded
    intensional) is built from the same three substitution sources, with
    only ``positive_info`` differing between the three renderings; this is
    the one place that merge happens, so all three renderings -- and both
    benchmarks -- apply the same precedence.

    Parameters
    ----------
    query:
        The per-query substitution dict yielded by a ``query_gen`` (e.g.
        ``{"color": ..., "year": ...}``).
    prompter:
        Supplies the static ``substitution`` dict merged into every query.
    positive_info:
        The generated context (intensional / extensional / noise-padded
        intensional) for this particular rendering.

    Returns
    -------
    Dict[str, str]
        A new dict combining all three sources. None of ``query``,
        ``prompter.substitution``, or ``positive_info`` are mutated, and
        the inputs share no memory with the result (safe for callers to
        mutate the returned dict further, as chromatic's extensional
        renderer does when adding ``query_years``). Precedence on key
        collisions follows dict-union's left-to-right rule applied in
        merge order (``query``, then ``prompter.substitution``, then
        ``positive_info``): ``positive_info`` always wins, and
        ``prompter.substitution`` wins over same-named keys in ``query``.

    Notes
    -----
    Pure dict composition -- no RNG is consumed, so callers may invoke this
    any number of times per query without affecting reproducibility or RNG
    call order.
    """
    return query | prompter.substitution | {"positive_info": positive_info}


def context_renderer(
    prompter: "Prompter",
    query: Dict[str, str],
    template: Optional[string.Template] = None,
) -> Callable[[str], str]:
    """Builds one query's ``context -> rendered prompt`` function.

    :func:`token_matched_noise_prompt` searches for a pad length by
    repeatedly rendering candidate contexts into the full prompt, so it
    needs the rendering for ONE query as a reusable callable. Binding
    ``query`` here, in a function scope, rather than closing over a loop
    variable at the call site also keeps the closure's capture unambiguous.

    Parameters
    ----------
    prompter:
        Supplies the template and the static substitutions.
    query:
        The single query's substitution dict.
    template:
        Template override (e.g. ``prompter.resolved_extens_template``).
        Defaults to ``prompter.template``, which is what the intensional
        and noise-padded arms both render with.

    Returns
    -------
    Callable[[str], str]
        ``context -> prompt``, deterministic and free of side effects, so
        the caller may invoke it as many times as its search needs.
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
    """
    Generates n unique random strings of length ``length`` over ``charset``.

    Strings are sampled as integers in [0, base**length) without
    replacement and base-expanded, so uniqueness is exact and the cost is
    O(n*length) regardless of how densely the space is sampled.

    Parameters
    ----------
    n:
        Number of strings to generate.
    length:
        Length of each string.
    rng:
        The RNG being used.
    charset:
        Character set to draw from (callers must exclude any separator in
        use downstream).

    Returns
    -------
    OrderedSet of n unique strings.

    Raises
    ------
    ValueError if length < ceil(log_{len(charset)}(n)): the space is too
    small to hold n unique strings.
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


# Multiplier applied to the information-theoretic minimum label length
# (ceil(log_base(count))) when auto-generating random labels. A label space
# sized to the theoretic minimum is exactly full once `count` labels are
# drawn, so `random_unique_strings` would have zero slack to reject
# collisions during sampling; doubling the length gives headroom (base**l
# grows exponentially in l, so even +1 already multiplies the space by
# `base`) so unique sampling remains fast and never exhausts the space in
# practice. This factor is a calibration invariant shared by both
# benchmarks' auto-generated labels/colors -- changing it changes label
# length (and therefore prompt length) for every benchmark at once.
LABEL_LENGTH_SAFETY_FACTOR: int = 2


def random_labels(
    count: int,
    seed: int,
    charset: Collection[str],
    min_length: int = 0,
) -> Tuple[str, ...]:
    """Auto-generates ``count`` unique random labels for a benchmark config.

    Thin, documented wrapper around :func:`random_unique_strings` that
    derives the label length from ``count`` and ``charset`` the same way
    for every benchmark, plus an optional caller-supplied floor. This is
    the single place both ``PeriodicConfig`` and ``ChromaticIntervalsConfig``
    go through to auto-generate labels/colors from an integer count, which
    is what keeps their label-length formulas calibrated against each other.

    Parameters
    ----------
    count:
        Number of unique labels to generate.
    seed:
        RNG seed; a fresh ``np.random.default_rng(seed)`` is constructed
        internally, so the same seed always yields the same label set.
    charset:
        Character set to draw labels from.
    min_length:
        Lower bound on the generated label length, applied after the
        ``LABEL_LENGTH_SAFETY_FACTOR`` scaling below. Defaults to 0, i.e.
        no floor beyond what the length formula itself produces (chromatic's
        behavior); pass e.g. 2 for a benchmark that additionally requires
        multi-character labels regardless of how small ``count`` is
        (periodic's behavior, so single-character labels are never
        auto-generated even when 1-2 labels would technically fit).

    Returns
    -------
    Tuple[str, ...]
        ``count`` unique labels, in the order produced by
        :func:`random_unique_strings`.

    Notes
    -----
    Label length is
    ``max(min_length, ceil(log_{len(charset)}(count)) * LABEL_LENGTH_SAFETY_FACTOR)``.
    RNG call order: exactly one ``np.random.default_rng`` construction
    followed by one ``random_unique_strings`` call, matching the pre-hoist
    call sites byte-for-byte.
    """
    length: int = max(
        min_length,
        int(np.ceil(np.emath.logn(len(charset), count))) * LABEL_LENGTH_SAFETY_FACTOR,
    )
    return tuple(
        random_unique_strings(count, length, np.random.default_rng(seed), charset=charset)
    )


# Whitespace units tried, in order, as the repeating pad atom. The unit must
# cost ~1 token per repetition under the tokenizer in play, which rules out
# the obvious candidates: BPE vocabularies carry dedicated tokens for RUNS of
# a single whitespace character, so `" " * 128` is ONE token in cl100k_base
# and a pure-space pad simply cannot reach a large target. Alternating two
# different whitespace characters defeats those run-merges -- `" \t"` measures
# at ~1 token per repetition in both cl100k_base and o200k_base. The rest are
# fallbacks for tokenizers that merge `" \t"`; `choose_whitespace_unit`
# verifies empirically rather than trusting this order.
WHITESPACE_UNITS: Tuple[str, ...] = (" \t", " \n\t", "\t ", " \n", "\t\n ")

# Repetition counts probed by `choose_whitespace_unit`. Small and large, so a
# unit that merges only once a run gets long (the failure mode that makes a
# pad silently saturate below its target) is rejected. The top probe is
# deliberately past 1024: a `tokenizer.json` can embed a `truncation` stanza
# capping every count (Nemotron-Ultra ships max_length 512), which would make
# a saturating tokenizer look linear at 256 and then silently refuse to grow.
# Probing above any plausible cap turns that into a loud failure here rather
# than a length control that is quietly wrong. `HFTokenizer` also disables
# truncation on load -- this is the backstop for tokenizers built elsewhere.
_UNIT_PROBES: Tuple[int, ...] = (1, 64, 256, 2048)

# A unit qualifies if its marginal cost is within this factor of 1 token per
# repetition at every probe. Slack allows a boundary token or a unit that
# costs 2 tokens for the first repetition and 1 thereafter, while rejecting
# anything that compresses (cost -> 0) and would never reach the target.
_UNIT_COST_TOLERANCE: float = 0.5

# Bound on the `token_matched_noise_prompt` search. Each pass costs one full
# re-encode of the prompt; the estimate-and-correct phase normally converges
# in 2-3 passes, and the bisection fallback needs ~log2(pad length) ~= 15 more
# in the worst case, so this bound is generous. Reaching it means the
# tokenizer is behaving pathologically and an exception is the right outcome.
_MAX_MATCH_ITERATIONS: int = 32


def choose_whitespace_unit(tokenizer) -> str:
    """Picks a whitespace pad atom that costs ~1 token per repetition.

    The token-matched noise pad is built by repeating one whitespace unit,
    which only works if repeating it actually grows the token count roughly
    linearly. Whether a given unit does depends entirely on the tokenizer's
    merge table, and the induction benchmarks now run against whatever
    tokenizer the model under test uses -- so this probes empirically
    instead of hard-coding a unit that happened to work on the encodings
    tested by hand.

    Parameters
    ----------
    tokenizer:
        Any :class:`~smolbench.evals.tokenization.Tokenizer` (anything with
        ``count(str) -> int``).

    Returns
    -------
    str
        The first unit in :data:`WHITESPACE_UNITS` whose measured cost is
        within :data:`_UNIT_COST_TOLERANCE` of 1 token per repetition at
        every probe in :data:`_UNIT_PROBES`.

    Raises
    ------
    ValueError
        If no candidate qualifies. Better a loud failure than a pad that
        silently saturates: a unit that compresses to nothing would leave
        the "length control" arm shorter than the arm it controls for,
        which is the exact confound this machinery exists to remove.
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
    """Renders `context` padded with whitespace to hit an exact token count.

    This is the noise-padded ("length control") arm of both induction
    benchmarks. ``render`` turns a context into the FULLY substituted
    prompt, so the search measures the real thing -- template, query, and
    context together -- rather than the context block alone. That matters
    because the arms being length-matched do not share a template: chromatic
    renders its extensional prompt from ``extens_template`` with an extra
    ``$query_years`` block, so contexts of equal token count would still
    produce prompts of unequal token count.

    Matching happens per query rather than once per config for the same
    reason: the query text substituted into each prompt differs in length,
    so only a per-prompt search can make every noise prompt exactly as long
    as its extensional counterpart.

    Parameters
    ----------
    render:
        ``context -> rendered prompt``. Called repeatedly (a handful of
        times), so it should be a cheap string substitution and must be
        deterministic -- a render that varied between calls would make the
        measured count describe a prompt other than the one returned.
    context:
        The intensional context to pad (the pad is appended to it, so the
        rules the model needs stay at the top of the prompt, exactly where
        the unpadded intensional arm puts them).
    target_tokens:
        The token count to hit -- in practice ``tokenizer.count(extens)``
        for the matching extensional prompt.
    tokenizer:
        The :class:`~smolbench.evals.tokenization.Tokenizer` defining
        "token". Use the tokenizer of the model under test
        (``tokenization.for_model(model)``); a different one silently
        de-calibrates the control by however much the two disagree.
    unit:
        Whitespace atom to repeat. Defaults to `choose_whitespace_unit`'s
        pick for this tokenizer; pass one explicitly to skip the probe when
        padding many prompts with the same tokenizer.

    Returns
    -------
    str
        ``render(context + pad)``, whose token count under `tokenizer`
        equals `target_tokens` EXACTLY -- verified before returning, never
        assumed. The one exception is an unreachable target (see below),
        where the unpadded render is returned.

    Raises
    ------
    ValueError
        If the search cannot land on `target_tokens`. Returning a close-but-
        inexact prompt is not an option: the whole point of the arm is that
        its length is not a confound, and an unverified pad would
        reintroduce the confound invisibly.

    Notes
    -----
    Unreachable target: when the unpadded prompt is ALREADY at least
    `target_tokens` long, no amount of appending can shrink it, so the
    unpadded render is returned and a warning is logged. This mirrors the
    ``max(0, ...)`` floor of the character-matched implementation this
    replaces, and in practice never fires -- the extensional context is
    orders of magnitude longer than the intensional rules.

    Determinism: whitespace padding needs no randomness, so unlike the
    random-character pad it replaces, this function consumes no RNG and
    takes no seed. A given (context, target, tokenizer) always yields the
    same prompt, which keeps a replicate regenerable from its seed alone.
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

    # Estimate, then correct, then (only if needed) bisect.
    #
    # The unit costs ~1 token, so the token deficit is itself a near-exact
    # estimate of how many repetitions are missing -- the first probe usually
    # lands within a token or two and the correction step finishes the job.
    # Every pass re-measures the WHOLE rendered prompt, which is what absorbs
    # the second-order effects no estimate can predict: merges where the pad
    # abuts the context, and merges between the pad and whatever the template
    # renders after it.
    #
    # Correction alone can oscillate (n -> n+3 -> n -> ...) when those merges
    # make the local token cost jump around, so the probes also maintain a
    # bracket: `lo` repetitions land below the target, `hi` above it. Once the
    # bracket is established, any estimate that escapes it is replaced by the
    # midpoint, which turns a potential oscillation into a bisection that must
    # terminate. A bracket that closes to adjacent values without an exact hit
    # means the token count JUMPS over the target -- no repetition count
    # satisfies the request -- and that is a genuine failure, not something to
    # paper over.
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
            break  # bracket exhausted: the count steps over the target
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
    """Wraps (intens, extens, noise_intens, answer) tuples into three quizzes.

    Parameters
    ----------
    prompts:
        The benchmark's prompt generator output, one tuple per query.
    qna_cls:
        The question type to wrap each prompt in (``ToF`` for True/False
        answers, ``Numeric`` for integers) -- the class's ``__post_init__``
        validates that the answers actually match.

    Returns
    -------
    (intensional Quiz, extensional Quiz, noise-padded intensional Quiz)
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in prompts:
        intens_quiz.append(qna_cls(prompt=intens, answer=answer))
        extens_quiz.append(qna_cls(prompt=extens, answer=answer))
        noise_intens_quiz.append(qna_cls(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)
