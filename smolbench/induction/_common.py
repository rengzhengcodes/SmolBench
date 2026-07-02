"""
Generation machinery shared by the induction benchmarks (periodic, chromatic).

The two benchmarks must stay CALIBRATED against each other: the noise-padding
ablation is only comparable across evals if the noise profile is identical,
and the random-label sampler fixes how fresh seeds map to fresh label sets.
Keeping these here, once, is what enforces that.
"""

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


def make_noise(length: int, rng: np.random.Generator) -> str:
    """Generates a random noise string of the given character length.

    Draws uniformly from ASCII letters, digits, spaces, and newlines. This
    profile is the length-matching pad for the noise-intensional ablation;
    changing it de-calibrates every benchmark at once, which is exactly why
    it lives here and nowhere else.
    """
    charset = list(string.ascii_letters + string.digits + "   \n")
    return "".join(charset[i] for i in rng.integers(len(charset), size=length))


def noise_pad(intension: str, extension: str, seed: int) -> str:
    """Pads an intensional context with noise to match an extensional length.

    Appends random noise (see :func:`make_noise`) to ``intension`` so the
    resulting string's length equals ``len(extension)`` (or ``intension``
    unchanged if it is already at least as long). This produces the
    "noise-padded intensional" context used to ablate context length as a
    confound: the model sees the same rules as the plain intensional prompt,
    padded to the same length as the extensional prompt, so any accuracy gap
    between intensional and extensional cannot be attributed to length alone.

    Parameters
    ----------
    intension:
        The intensional (rule-based) context to pad.
    extension:
        The extensional (enumerated) context whose length sets the pad
        target.
    seed:
        The benchmark config's base seed. The noise RNG is seeded with
        ``seed + 1``, NOT ``seed`` -- a deliberate, calibration-critical
        offset. Every other generator in a benchmark run (label sampling,
        interval/marker sampling, query sampling) is seeded from ``seed``
        directly; using ``seed + 1`` here gives the noise stream its own
        independent draw sequence so that consuming noise never perturbs --
        and is never perturbed by -- the RNG call order of the rest of the
        pipeline, while remaining fully reproducible from the single
        ``seed`` field on the config. Both benchmarks (periodic, chromatic)
        must derive the noise seed identically, or their noise profiles
        stop being calibrated against each other -- which is the entire
        reason this helper lives here instead of being duplicated per
        benchmark.

    Returns
    -------
    str
        ``intension`` with noise appended so its length matches
        ``len(extension)`` (unchanged if ``intension`` is already at least
        that long).

    Notes
    -----
    RNG call order: exactly one ``np.random.default_rng`` construction
    followed by one ``make_noise`` call, matching the pre-hoist call sites
    byte-for-byte -- this function performs no other RNG draws.
    """
    noise_rng: np.random.Generator = np.random.default_rng(seed + 1)
    return intension + make_noise(max(0, len(extension) - len(intension)), noise_rng)


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
