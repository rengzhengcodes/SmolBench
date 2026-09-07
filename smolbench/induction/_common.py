"""Generation machinery behind the induction benchmark (periodic).

Kept separate from ``periodic.py`` so the calibration invariants live in one
place: the noise-padding ablation is comparable across evals only when the
noise profile is identical, and a seed must always map to the same label set.

The noise pad is whitespace sized in TOKENS
(:func:`~smolbench.evals.tokenization.token_matched_noise_prompt`) under the
tokenizer of the model under test, verified to hit the target exactly --
characters are the wrong unit, as a character-matched pad over-pads the
control arm. The pad search itself and its unit table live in
:mod:`smolbench.evals.tokenization`; this module holds ``Prompter``, the
substitution merge, and the random label/string generators.
"""

import string
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Tuple,
)

import numpy as np
from ordered_set import OrderedSet

from smolbench.evals import Answer, QnA, Quiz


# range_free_template is exercised in production, unlike two now-deleted
# fields it might resemble: run_study.py supplies it (`zero_template`), and
# `periodic.get_periodic_prompts` raises when a condition needs it
# (`omit_range=True`) and it is `None` -- no silent fallback to the
# range-stating `template`, since that fallback is exactly the answer-leaking
# prompt this field exists to avoid.
@dataclass(frozen=True, slots=True)
class Prompter:
    """Bundle everything needed to prompt an LLM with a generated context.

    Placeholder contract: ``template`` MUST reference ``$positive_info`` (the
    intensional, extensional or noise-padded context) plus every key
    ``query_gen`` produces, and nothing else (see :func:`build_substitution`).
    ``range_free_template``, when supplied, must hold to the same contract
    minus any placeholder that states a position range (e.g. ``$seq_len``):
    it is the question a range-omitting condition renders from instead of
    ``template``. Rendering uses ``safe_substitute``, not ``substitute``, so a
    literal ``$`` in quiz text does not raise mid-study -- but a misspelled
    placeholder is silently left verbatim, so validate templates on a sample
    query first.
    """

    #: Prompt template. See the placeholder contract in the class docstring.
    template: string.Template
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs; the mapping arguments are
    #: benchmark-specific (see each benchmark's built-in query generators).
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]
    #: Template for a condition that must not reveal the position range (see
    #: ``periodic.py``'s ``RANGE_KEYS``). ``None`` is fine unless a condition
    #: needs it, in which case generation raises rather than falling back to
    #: ``template`` and shipping the leak silently.
    range_free_template: Optional[string.Template] = None


@dataclass(frozen=True, slots=True)
class RenderedQuery:
    """One query's rendered prompt and token count, per information condition.

    Emitted by ``smolbench.induction.periodic.get_periodic_prompts``: one
    ``RenderedQuery`` per underlying query. The counts are not a convenience
    re-tokenization -- they are the same counts generation already computed
    to build the prompts (every condition is tokenized during rendering, to
    give a padded condition's target) -- so a caller sizing a completion
    budget can read them off here instead of re-tokenizing every prompt.
    """

    #: condition name -> that condition's rendered prompt for this query.
    prompts: Mapping[str, str]
    #: condition name -> ``tokenizer.count(prompts[name])`` under the
    #: tokenizer generation ran with. Same keys as `prompts`.
    token_counts: Mapping[str, int]
    #: This query's ground-truth answer -- identical across every condition,
    #: since only the amount of positive information shown varies.
    answer: Answer


def build_substitution(query: Dict[str, str], positive_info: str) -> Dict[str, str]:
    """Merge a query's substitutions with the arm's ``positive_info`` context.

    The single merge point for all three renderings, so precedence is
    uniform: `positive_info` wins any collision with `query`, since every arm
    must control it -- a ``query_gen`` that emitted its own ``positive_info``
    key would otherwise silently collapse the three arms into one.

    Parameters
    ----------
    query : Dict[str, str]
        Query substitutions to merge.
    positive_info : str
        Arm-specific positive-information context.

    Returns
    -------
    Dict[str, str]
        A fresh dict, so callers may mutate it further.
    """
    return query | {"positive_info": positive_info}


def context_renderer(
    prompter: "Prompter",
    query: Dict[str, str],
    template: Optional[string.Template] = None,
) -> Callable[[str], str]:
    """Build one query's deterministic ``context -> rendered prompt`` function.

    :func:`~smolbench.evals.tokenization.token_matched_noise_prompt` needs
    the rendering as a reusable callable. ``template`` defaults to
    ``prompter.template``.

    Parameters
    ----------
    prompter : Prompter
        Prompter supplying the default template.
    query : Dict[str, str]
        Query substitutions for each rendering.
    template : Optional[string.Template], optional
        Template to render.

    Returns
    -------
    Callable[[str], str]
        Function mapping context to a rendered prompt.
    """
    resolved: string.Template = template if template is not None else prompter.template

    def render(context: str) -> str:
        return resolved.safe_substitute(build_substitution(query, context))

    return render


def random_unique_strings(
    n: int,
    length: int,
    rng: np.random.Generator,
    charset: Collection[str],
) -> OrderedSet[str]:
    """Generate ``n`` unique random strings of length ``length`` over ``charset``.

    Samples integers in ``[0, base**length)`` without replacement and
    base-expands each, so uniqueness is exact regardless of how densely the
    space is sampled. ``charset`` must exclude any separator in use
    downstream.

    Parameters
    ----------
    n : int
        Number of unique strings to generate.
    length : int
        Length of each generated string.
    rng : np.random.Generator
        Random generator supplying samples.
    charset : Collection[str]
        Characters from which to build strings.

    Returns
    -------
    OrderedSet[str]
        Generated unique strings in draw order.

    Raises
    ------
    ValueError
        If ``length`` is too small a space for ``n`` unique strings.
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
        # rng.choice needs the population to fit in int64; raise our own
        # message rather than an opaque numpy OverflowError.
        raise ValueError(
            f"{base}**{length} exceeds the int64 sample space rng.choice "
            f"supports; reduce length (or count, which drives it)."
        )
    indices: np.ndarray = rng.choice(base ** length, size=n, replace=False)
    digits: np.ndarray = np.empty((n, length), dtype=np.int64)
    for idx in range(length - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    # OrderedSet, not tuple: documents the uniqueness contract and keeps draw
    # order (a plain set would de-determinize iteration).
    return OrderedSet("".join(row) for row in charset_array[digits])


# Multiplies the information-theoretic minimum label length
# (ceil(log_base(count))) for auto-generated labels, giving headroom since
# `random_unique_strings` has zero slack at exactly that minimum. Changing
# this changes label length, and so prompt length, for every config at once.
LABEL_LENGTH_SAFETY_FACTOR: int = 2


def random_labels(
    count: int,
    seed: int,
    charset: Collection[str],
    min_length: int = 0,
) -> Tuple[str, ...]:
    """Auto-generate ``count`` unique random labels for a benchmark config.

    Length is
    ``max(min_length, ceil(log_{len(charset)}(count)) * LABEL_LENGTH_SAFETY_FACTOR)``.
    A fresh ``np.random.default_rng(seed)`` feeds one
    :func:`random_unique_strings` call, so a seed always yields the same set.

    Parameters
    ----------
    count : int
        Number of labels to generate.
    seed : int
        Seed for the random generator.
    charset : Collection[str]
        Characters from which to build labels.
    min_length : int, optional
        Minimum label length.

    Returns
    -------
    Tuple[str, ...]
        Generated labels.
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
    prompts: Iterable[RenderedQuery],
    qna_cls: type[QnA],
    conditions: Iterable[str],
) -> Dict[str, Quiz]:
    """Wrap ``RenderedQuery`` instances into one ``Quiz`` per condition.
    Raises ``ValueError``, naming it, if some ``RenderedQuery`` lacks one of
    `conditions`'s names -- otherwise a missing arm would surface much later
    as a confusing ``KeyError``.

    Parameters
    ----------
    prompts : Iterable[RenderedQuery]
        Rendered prompts to group by condition.
    qna_cls : type[QnA]
        Question-and-answer class for each rendered prompt.
    conditions : Iterable[str]
        Typed structurally (any string iterable) rather than as
        ``periodic.CONDITIONS``'s key type, because importing ``periodic`` here
        would be a cycle; passing the mapping directly still works since
        iterating it yields its keys in the wanted order.

    Returns
    -------
    Dict[str, Quiz]
        Quizzes keyed by condition name.
    """
    condition_names = tuple(conditions)
    quizzes: Dict[str, list] = {name: [] for name in condition_names}
    for rendered in prompts:
        for name in condition_names:
            if name not in rendered.prompts:
                raise ValueError(
                    f"RenderedQuery is missing condition {name!r}: it only "
                    f"carries {sorted(rendered.prompts)}."
                )
            quizzes[name].append(
                qna_cls(prompt=rendered.prompts[name], answer=rendered.answer)
            )
    return {name: tuple(qnas) for name, qnas in quizzes.items()}
