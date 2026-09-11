"""Shared induction prompt and label-generation machinery.

Noise padding is token-matched under the tested model because character matching over-pads controls.
Seeds deterministically select label sets.
"""

import string
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Collection,
    Iterable,
    Mapping,
)

import numpy as np
from ordered_set import OrderedSet

from smolbench.evals import Answer, QnA, Quiz


# Missing range-free templates raise rather than leaking position ranges.
@dataclass(frozen=True, slots=True)
class Prompter:
    """Bundle a generated-context prompt.

    Templates require ``$positive_info`` and query keys; range-free templates must omit range placeholders.
    ``safe_substitute`` permits literal ``$`` but leaves misspelled placeholders verbatim.
    """

    #: Prompt template.
    template: string.Template
    #: Query generator yielding substitutions and answers.
    query_gen: Callable[..., Iterable[tuple[dict[str, str], Any]]]
    #: Position-range-free template; required by range-omitting conditions.
    range_free_template: string.Template | None = None


@dataclass(frozen=True, slots=True)
class RenderedQuery:
    """Rendered prompts and token counts for one query.

    Counts are generation-time values, avoiding inconsistent re-tokenization.
    """

    #: Condition name to rendered prompt.
    prompts: Mapping[str, str]
    #: Condition name to generation-time token count.
    token_counts: Mapping[str, int]
    #: Ground-truth answer, shared across conditions.
    answer: Answer


def build_substitution(query: dict[str, str], positive_info: str) -> dict[str, str]:
    """Merge query substitutions with arm ``positive_info``.

    ``positive_info`` wins collisions so arms cannot collapse into one.

    Parameters
    ----------
    query : dict[str, str]
        Query substitutions to merge.
    positive_info : str
        Arm-specific positive-information context.

    Returns
    -------
    dict[str, str]
        A fresh dict, so callers may mutate it further.
    """
    return query | {"positive_info": positive_info}


def context_renderer(
    prompter: Prompter,
    query: dict[str, str],
    template: string.Template | None = None,
) -> Callable[[str], str]:
    """Build a deterministic ``context -> prompt`` renderer.

    Parameters
    ----------
    prompter : Prompter
        Prompter supplying the default template.
    query : dict[str, str]
        Query substitutions for each rendering.
    template : string.Template | None, optional
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
    """Generate ``n`` unique ``length``-character strings over ``charset``.

    Sampling without replacement guarantees uniqueness.

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
        # ``rng.choice`` requires an int64 population.
        raise ValueError(
            f"{base}**{length} exceeds the int64 sample space rng.choice "
            f"supports; reduce length (or count, which drives it)."
        )
    indices: np.ndarray = rng.choice(base**length, size=n, replace=False)
    digits: np.ndarray = np.empty((n, length), dtype=np.int64)
    for idx in range(length - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    # OrderedSet preserves unique draw order.
    return OrderedSet("".join(row) for row in charset_array[digits])


# Headroom above the unique-label minimum prevents a full sample space.
# Changing this changes label length, and so prompt length, for every config.
LABEL_LENGTH_SAFETY_FACTOR: int = 2


def random_labels(
    count: int,
    seed: int,
    charset: Collection[str],
    min_length: int = 0,
) -> tuple[str, ...]:
    """Generate deterministic unique labels for a benchmark configuration.

    Label length includes safety headroom above the unique-label minimum.

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
    tuple[str, ...]
        Generated labels.
    """
    # A one-label configuration must not generate an empty label.
    length: int = max(
        min_length,
        1,
        int(np.ceil(np.emath.logn(len(charset), count))) * LABEL_LENGTH_SAFETY_FACTOR,
    )
    return tuple(
        random_unique_strings(
            count, length, np.random.default_rng(seed), charset=charset
        )
    )


def quizzes_from_prompts(
    prompts: Iterable[RenderedQuery],
    qna_cls: type[QnA],
    conditions: Iterable[str],
) -> dict[str, Quiz]:
    """Wrap rendered queries into one ``Quiz`` per condition.

    Raise early for missing conditions.

    Parameters
    ----------
    prompts : Iterable[RenderedQuery]
        Rendered prompts to group by condition.
    qna_cls : type[QnA]
        Question-and-answer class for each rendered prompt.
    conditions : Iterable[str]
        Condition names expected in every rendered query.

    Returns
    -------
    dict[str, Quiz]
        Quizzes keyed by condition name.
    """
    condition_names = tuple(conditions)
    quizzes: dict[str, list] = {name: [] for name in condition_names}
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
