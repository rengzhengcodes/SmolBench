"""Share generation machinery between the induction benchmarks (periodic, chromatic).

The two benchmarks must stay CALIBRATED with each other. The noise-padding
ablation is only comparable across evals when the noise profile is
identical. The random-label sampler must map a fresh seed to the same fresh
label set in both benchmarks. This module holds that machinery once, so it
enforces the calibration for both benchmarks.

The noise pad is WHITESPACE, sized in TOKENS (see
:func:`token_matched_noise_prompt`). It is not random characters sized in
characters. Characters were the wrong unit: models consume tokens, and
random alphanumerics tokenize far worse than structured text. A
character-matched pad silently over-padded the control arm: 42,639 tokens
against a 26,279-token extensional target at the periodic production config,
1.62x the length it was supposed to match. The pad now measures against the
tokenizer of the model under test and verifies that it hits the target
exactly. See `smolbench.evals.tokenization`.
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
    intensional, extensional, or noise-padded context) plus every key that
    ``query_gen`` and ``substitution`` produce. The render step uses
    ``string.Template.safe_substitute``, which does not raise an error for
    an unmatched or misspelled placeholder. It SILENTLY leaves that
    placeholder verbatim in the prompt instead. Validate templates against
    a sample query before an expensive run.
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
        """Return the template to use for the extensional prompt.

        Return ``extens_template`` when the caller sets one. Otherwise fall
        back to ``template``. Both benchmarks need this same fallback, so it
        lives once on the shared ``Prompter`` instead of being reimplemented
        at each call site.

        Returns
        -------
        string.Template
            ``self.extens_template`` if not None, else ``self.template``.
        """
        return self.extens_template or self.template


def build_substitution(
    query: Dict[str, str], prompter: Prompter, positive_info: str
) -> Dict[str, str]:
    """Merge a query's substitutions with the prompter's, plus positive_info.

    Every rendered prompt (intensional, extensional, or noise-padded
    intensional) builds from the same three substitution sources. Only
    ``positive_info`` differs between the three renderings. This function is
    the one place that merge happens, so all three renderings, in both
    benchmarks, apply the same precedence.

    Parameters
    ----------
    query : Dict[str, str]
        The per-query substitution dict that a ``query_gen`` yields (e.g.
        ``{"color": ..., "year": ...}``).
    prompter : Prompter
        Supplies the static ``substitution`` dict merged into every query.
    positive_info : str
        The generated context (intensional, extensional, or noise-padded
        intensional) for this particular rendering.

    Returns
    -------
    Dict[str, str]
        A new dict that combines all three sources. This function does not
        mutate ``query``, ``prompter.substitution``, or ``positive_info``,
        and the result shares no memory with the inputs. Callers may mutate
        the returned dict further, as chromatic's extensional renderer does
        when it adds ``query_years``. On a key collision, precedence follows
        dict-union's left-to-right rule in merge order (``query``, then
        ``prompter.substitution``, then ``positive_info``): ``positive_info``
        always wins, and ``prompter.substitution`` wins over a same-named key
        in ``query``.

    Notes
    -----
    This is pure dict composition. It consumes no RNG, so callers may call
    it any number of times per query without affecting reproducibility or
    RNG call order.
    """
    return query | prompter.substitution | {"positive_info": positive_info}


def context_renderer(
    prompter: "Prompter",
    query: Dict[str, str],
    template: Optional[string.Template] = None,
) -> Callable[[str], str]:
    """Build one query's ``context -> rendered prompt`` function.

    :func:`token_matched_noise_prompt` searches for a pad length by
    repeatedly rendering candidate contexts into the full prompt. It needs
    the rendering for ONE query as a reusable callable. This function binds
    ``query`` here, in a function scope, which also keeps the closure's
    capture unambiguous; it avoids closing over a loop variable at the call
    site.

    Parameters
    ----------
    prompter : Prompter
        Supplies the template and the static substitutions.
    query : Dict[str, str]
        The single query's substitution dict.
    template : string.Template, optional
        Template override (e.g. ``prompter.resolved_extens_template``).
        Defaults to ``prompter.template``, which is what the intensional
        and noise-padded arms both render with.

    Returns
    -------
    Callable[[str], str]
        A ``context -> prompt`` function. It is deterministic and free of
        side effects, so the caller may call it as many times as its search
        needs.
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

    This function samples strings as integers in ``[0, base**length)``
    without replacement, then base-expands each integer into a string. This
    keeps uniqueness exact, at a cost of ``O(n * length)`` regardless of how
    densely the space is sampled.

    Parameters
    ----------
    n : int
        Number of strings to generate.
    length : int
        Length of each string.
    rng : numpy.random.Generator
        The RNG to use.
    charset : Collection[str]
        Character set to draw from. Callers must exclude any separator in
        use downstream.

    Returns
    -------
    OrderedSet[str]
        ``n`` unique strings.

    Raises
    ------
    ValueError
        If ``length < ceil(log_{len(charset)}(n))``: the space is too small
        to hold ``n`` unique strings.
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

    This is a thin, documented wrapper around :func:`random_unique_strings`.
    It derives the label length from ``count`` and ``charset`` the same way
    for every benchmark, plus an optional caller-supplied floor. Both
    ``PeriodicConfig`` and ``ChromaticIntervalsConfig`` go through this
    single function to auto-generate labels or colors from an integer count.
    This is what keeps their label-length formulas calibrated with each
    other.

    Parameters
    ----------
    count : int
        Number of unique labels to generate.
    seed : int
        RNG seed. This function constructs a fresh
        ``np.random.default_rng(seed)`` internally, so the same seed always
        yields the same label set.
    charset : Collection[str]
        Character set to draw labels from.
    min_length : int, default 0
        Lower bound on the generated label length, applied after the
        ``LABEL_LENGTH_SAFETY_FACTOR`` scaling below. The default of 0 sets
        no floor beyond what the length formula itself produces (chromatic's
        behavior). Pass, for example, 2 for a benchmark that also requires
        multi-character labels regardless of how small ``count`` is
        (periodic's behavior): this keeps single-character labels from ever
        being auto-generated, even when 1-2 labels would technically fit.

    Returns
    -------
    Tuple[str, ...]
        ``count`` unique labels, in the order that
        :func:`random_unique_strings` produces.

    Notes
    -----
    Label length is
    ``max(min_length, ceil(log_{len(charset)}(count)) * LABEL_LENGTH_SAFETY_FACTOR)``.
    RNG call order: exactly one ``np.random.default_rng`` construction,
    followed by one ``random_unique_strings`` call.
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

    The token-matched noise pad repeats one whitespace unit. This only works
    when repeating the unit grows the token count roughly linearly. Whether
    a given unit does depends entirely on the tokenizer's merge table, and
    the induction benchmarks now run against whatever tokenizer the model
    under test uses. So this function probes empirically. It does not
    hard-code a unit that happened to work on the encodings tested by hand.

    Parameters
    ----------
    tokenizer : Tokenizer
        Any :class:`~smolbench.evals.tokenization.Tokenizer` (anything with
        ``count(str) -> int``).

    Returns
    -------
    str
        The first unit in :data:`WHITESPACE_UNITS` whose measured cost falls
        within :data:`_UNIT_COST_TOLERANCE` of 1 token per repetition at
        every probe in :data:`_UNIT_PROBES`.

    Raises
    ------
    ValueError
        If no candidate qualifies. A loud failure here is better than a pad
        that silently saturates: a unit that compresses to nothing would
        leave the "length control" arm shorter than the arm it controls for.
        That is the exact confound this machinery exists to remove.
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

    This is the noise-padded ("length control") arm of both induction
    benchmarks. ``render`` turns a context into the FULLY substituted
    prompt, so the search measures the real thing: template, query, and
    context together, not the context block alone. That matters because the
    arms being length-matched do not share a template: chromatic renders its
    extensional prompt from ``extens_template`` with an extra
    ``$query_years`` block. Contexts of equal token count would then still
    produce prompts of unequal token count.

    This match happens per query, not once per config, for the same reason:
    the query text substituted into each prompt differs in length. Only a
    per-prompt search can make every noise prompt exactly as long as its
    extensional counterpart.

    Parameters
    ----------
    render : Callable[[str], str]
        ``context -> rendered prompt``. This function calls ``render``
        repeatedly (a handful of times), so it should be a cheap string
        substitution, and it must be deterministic. A render that varies
        between calls would make the measured count describe a prompt other
        than the one returned.
    context : str
        The intensional context to pad. The pad is appended to it, so the
        rules the model needs stay at the top of the prompt, exactly where
        the unpadded intensional arm puts them.
    target_tokens : int
        The token count to hit. In practice this is
        ``tokenizer.count(extens)`` for the matching extensional prompt.
    tokenizer : Tokenizer
        The :class:`~smolbench.evals.tokenization.Tokenizer` that defines
        "token". Use the tokenizer of the model under test
        (``tokenization.for_model(model)``). A different one silently
        de-calibrates the control by however much the two disagree.
    unit : str, optional
        Whitespace atom to repeat. Defaults to `choose_whitespace_unit`'s
        pick for this tokenizer. Pass one explicitly to skip the probe when
        padding many prompts with the same tokenizer.

    Returns
    -------
    str
        ``render(context + pad)``. Its token count under `tokenizer` equals
        `target_tokens` EXACTLY; this function verifies that before
        returning, it never just assumes it. The one exception is an
        unreachable target (see the Notes section), where this function
        returns the unpadded render.

    Raises
    ------
    ValueError
        If the search cannot land on `target_tokens`. A close-but-inexact
        prompt is not an option to return: the whole point of the arm is
        that its length is not a confound, and an unverified pad would
        reintroduce the confound invisibly.

    Notes
    -----
    Unreachable target: when the unpadded prompt is ALREADY at least
    `target_tokens` long, no amount of appending can shrink it. This
    function then returns the unpadded render and logs a warning. This
    mirrors the ``max(0, ...)`` floor of the character-matched
    implementation this function replaces. In practice it never fires: the
    extensional context is orders of magnitude longer than the intensional
    rules.

    Determinism: whitespace padding needs no randomness. Unlike the
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

    Parameters
    ----------
    prompts : Iterable[Tuple[str, str, str, Answer]]
        The benchmark's prompt generator output, one tuple per query.
    qna_cls : type[QnA]
        The question type to wrap each prompt in (``ToF`` for True/False
        answers, ``Numeric`` for integers). The class's ``__post_init__``
        validates that the answers actually match.

    Returns
    -------
    Tuple[Quiz, Quiz, Quiz]
        The intensional Quiz, extensional Quiz, and noise-padded
        intensional Quiz, in that order.
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in prompts:
        intens_quiz.append(qna_cls(prompt=intens, answer=answer))
        extens_quiz.append(qna_cls(prompt=extens, answer=answer))
        noise_intens_quiz.append(qna_cls(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)
