"""Generation machinery behind the induction benchmark (periodic).

Kept separate from ``periodic.py`` so the calibration invariants live in one
place: the noise-padding ablation is comparable across evals only when the
noise profile is identical, and a seed must always map to the same label set.
(``smolbench.deduction.lean.context`` -- lands in slice 3 -- reuses
:mod:`smolbench.evals.tokenization`'s pad search for the same reason.)

The noise pad is WHITESPACE sized in TOKENS (:func:`token_matched_noise_prompt`)
under the tokenizer of the model under test, verified to hit the target exactly.
Characters are the wrong unit -- a character-matched pad over-pads the control
arm ~1.6x at the periodic production config (an ad-hoc design-time
measurement; the load-bearing invariant is the verified per-prompt token
exactness, not that ratio). The pad search itself, its unit table and the
pad-content rationale now live in :mod:`smolbench.evals.tokenization` -- this
module re-exports them (see the comment below) so an existing caller of
``smolbench.induction._common`` keeps resolving. What stays here is everything
else the calibration invariant needs: ``Prompter``, the substitution merge, and
the random label/string generators.
"""

import string
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, Iterable, Optional, Tuple

import numpy as np
from ordered_set import OrderedSet

from smolbench.evals import Answer, QnA, Quiz
# Re-exported, not re-implemented: these are the SAME objects as
# smolbench.evals.tokenization's, never copies. A second, independently-edited
# pad search would silently de-calibrate the noise arm between the two studies
# that use it (this one and, eventually, smolbench.deduction.lean.context).
# The import stays here so `from smolbench.induction._common import
# token_matched_noise_prompt` keeps resolving for any existing caller; a
# sibling study reaches for the public smolbench.evals.tokenization import
# instead (see smolbench.induction.periodic's own import for the pattern).
from smolbench.evals.tokenization import (  # noqa: F401 -- re-exported
    WHITESPACE_UNITS,
    _MAX_MATCH_ITERATIONS,
    _UNIT_COST_TOLERANCE,
    _UNIT_PROBES,
    choose_whitespace_unit,
    token_matched_noise_prompt,
)


# Design: exactly TWO fields. `Prompter` previously also carried
# `substitution: Dict[str, str]` and `extens_template: Optional[Template]`
# (plus a `resolved_extens_template` property). Both were hooks for the
# `query_years` mechanism of the chromatic benchmark, which has been deleted:
# `substitution` was `{}` at every construction site in the repo, and no
# production caller ever set `extens_template`. They were dead weight that made
# TWO render paths (template vs extens_template) and a three-term substitution
# precedence look live when only one path and two terms ever executed -- a
# reader had to check every call site to learn that. Removing them makes the
# single live path the only path.
@dataclass(frozen=True, slots=True)
class Prompter:
    """Bundle everything needed to prompt an LLM with a generated context.

    Placeholder contract: ``template`` MUST reference ``$positive_info`` (the
    intensional, extensional or noise-padded context) plus every key
    ``query_gen`` produces -- and nothing else, since those two sources are now
    the whole substitution (see :func:`build_substitution`). For the built-in
    periodic generators that means ``$positive_info`` plus ``$label`` and
    ``$seq_len`` (``numeric_count_query_gen``) or ``$label`` and ``$pos``
    (``tof_membership_query_gen``). Rendering uses ``safe_substitute``, which
    SILENTLY leaves a misspelled placeholder verbatim instead of raising, so
    validate templates on a sample query first. ``safe_substitute`` (not
    ``substitute``) is deliberate: a literal ``$`` in quiz text must not raise
    mid-study, and the golden-quiz hash pins
    (``tests/induction/test_golden_quizzes.py``) already fail on any drift in
    the rendered prompts.
    """

    #: Prompt template. See the placeholder contract in the class docstring.
    template: string.Template
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs; the mapping arguments are
    #: benchmark-specific (see each benchmark's built-in query generators).
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]


def build_substitution(
    query: Dict[str, str], prompter: Prompter, positive_info: str
) -> Dict[str, str]:
    """Merge a query's substitutions with the arm's ``positive_info`` context.

    The single merge point for all three renderings, so precedence is uniform:
    a two-term dict-union in the order ``query``, ``positive_info``, the last
    winning a collision. The arm's context comes last because every arm --
    intensional, extensional, noise-padded, zero-information -- must control
    it; a ``query_gen`` that emitted its own ``positive_info`` key would
    otherwise silently collapse the three arms into one. Nothing can outrank a
    ``query_gen`` any more: the static ``prompter.substitution`` table that used
    to sit between the two terms is gone with the chromatic hooks (see the
    :class:`Prompter` comment). Returns a fresh dict, so callers may mutate it
    further.

    `prompter` is currently UNUSED -- deliberately, not by oversight. It was
    the source of that removed static term, and it is kept in the signature so
    this stays the one merge point every render site calls the same way
    (:func:`context_renderer` plus the three arms in ``periodic.py``), with a
    stable seam for any future prompter-sourced substitution. Every caller
    already holds a `Prompter`, so the parameter costs nothing; dropping it is
    a safe follow-up if nothing reclaims it.
    """
    return query | {"positive_info": positive_info}


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
