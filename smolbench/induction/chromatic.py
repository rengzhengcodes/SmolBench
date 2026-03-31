"""
Generates chromatic intervals.
"""

import string
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias, Collection, Iterable, Tuple, Dict, Set, Callable

import numpy as np

# A color in the mathematical sense of some label.
Color: TypeAlias = str
# Interval of the form [start, end) as indices of some Sequence.
Interval: TypeAlias = Tuple[int, int]
# A collection of intervals.
Intervals: TypeAlias = Collection[Interval]


def _get_random_colors(
    n: int,
    l: int,
    rng: np.random.Generator,
    charset: Collection[str] = string.ascii_letters,
) -> Set[Color]:
    """
    Generates n unique random colors of l length.

    Parameters
    ----------
    n:
        Number of colors to generate.
    l:
        Length of each color.
    rng:
        The rng being used.
    charset:
        The characters to include in each color.

    Return
    ------
    Set of unique colors.

    Exceptions
    ----------
    ValueError if l < ceil(log_{len(charset)}(n)) as cannot generate n unique colors.
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len: int = np.ceil(np.emath.logn(base, n))
    if l < min_len:
        raise ValueError(
            f"l < {min_len} = "
            f"ceil(log_{{{base}}}({n}))\n"
            f"Insufficient expressivity for labels in charset for the given length."
        )

    # Colors represented as an integer so it could be quickly exhaustively generated.
    colors: np.ndarray[int] = rng.choice(base**l, size=n, replace=False)
    digits: np.ndarray[int] = np.empty((n, l), dtype=np.int64)
    for idx in range(l - 1, -1, -1):
        colors, digits[:, idx] = np.divmod(colors, base)

    charset_array: np.ndarray[str] = np.asarray(charset)
    return {"".join(color) for color in charset_array[digits]}


def _assign_colors(
    intervals: Collection[Interval],
    colors: Collection[Color],
    labeler: Callable[[Color, Intervals], Intervals],
    cleanser: Callable[[Intervals, Intervals], Intervals],
) -> Tuple[Dict[Color, Intervals], Dict[Interval, Set[Color]]]:
    """
    Given a set of intervals, assign colors to each interval.

    Parameters
    ----------
    intervals:
        A collection of intervals that need to be assigned a color.
    colors:
        The assignable interval colors.
    labeler:
        The arbitrator of which intervals get assigned for a color.
    cleanser:
        Cleans up what the labeler has access to on the next iteration of assignment.

    Returns
    -------
    A dictionary of every color to its intervals and every interval to its color.
    """
    label_to_intervals: Dict[Color, Intervals] = {}
    intervals_to_label: Dict[Interval, Color] = defaultdict(set)
    for color in colors:
        # Assigns to remaining intervals.
        assignment: Intervals = labeler(color, intervals)

        # Return bookkeeping.
        label_to_intervals[color] = assignment
        for interval in assignment:
            intervals_to_label[tuple(interval.tolist())].add(color)

        # Cleanses assignable intervals.
        intervals = cleanser(intervals, assignment)

    return label_to_intervals, intervals_to_label


def _get_random_exclusive_intervals(n: int, intervaler: Iterable[int]) -> Interval:
    """
    Generates intervals from [0, n) where each interval does not overlap the
    previous.

    Parameters
    ----------
    n:
        The total length of intervals to generate.
    intervaler:
        The structure used to generate the next element of an interval.

    Yields
    ------
    A series of intervals from [0, n) generated off rng.
    """
    start: int = 0
    end: int = 0

    while end < n:
        end = min(n, next(intervaler, n))
        yield (start, end)
        start = end


def _get_exclusive_chromatic_intervals(
    n: int,
    colors: Collection[Color],
    intervaler: Iterable[int],
    labeler: Callable[[Color, Intervals], Intervals],
    cleanser: Callable[[Color]],
) -> Tuple[Dict[Color, Intervals], Dict[Interval, Color]]:
    """
    Generates chromatic intervals from [0, n), where each i in [0, n) has exactly
    one color (i.e., no intervals overlap).

    Parameters
    ----------
    n:
        The length the intervals can span.
    colors:
        The colors to assign to the intervals.
    intervaler:
        The generator of intervals.
    labeler:
        Assigns colors to each interval.
    cleanser:
        Cleans up what the labeler has access to between colors.

    Returns
    -------
    A dictionary of every color to its intervals and every interval to its color.
    """
    intervals: Set[Interval] = np.array(
        tuple(_get_random_exclusive_intervals(n, intervaler))
    )
    return _assign_colors(intervals, colors, labeler, cleanser)


@dataclass(frozen=True)
class ChromaticIntervalsConfig:
    """Config for generating some chromatic intervals."""

    #: Number of discrete units in the interval.
    n: int
    #: Number of intervals.
    intervals: int
    #: Number of colors or Collection of colors to assign.
    colors: Collection[Color] | int
    #: rng seed for reproducibility.
    seed: int

    def __post_init__(self):
        """Turns colors into a Collection."""
        # Generates the colors if needed.
        if isinstance(self.colors, int):
            length: int = (
                int(np.ceil(np.emath.logn(len(string.ascii_letters), self.colors))) * 2
            )
            object.__setattr__(
                self,
                "colors",
                tuple(
                    _get_random_colors(
                        self.colors, length, np.random.default_rng(self.seed)
                    )
                ),
            )
        else:
            object.__setattr__(self, "colors", tuple(self.colors))


def get_random_exclusive_chromatic_intervals(
    config: ChromaticIntervalsConfig,
) -> Tuple[Dict[Color, Collection[Interval]], Dict[Interval, Color]]:
    """
    Generates a number of intervals from [0, n) and each interval has equal
    probability of being any color.

    Parameters
    ----------
    config:
        Generator config.

    Returns
    -------
    A dictionary mapping colors to intervals and a dictionary mapping intervals to
    colors.
    """

    # Seeds and generates the interval demarcations.
    rng: np.random.Generator = np.random.default_rng(config.seed)
    markers: np.ndarray[int] = rng.choice(
        range(config.n + 1), config.intervals - 1, replace=False
    )
    markers.sort()

    # Defines a uniform labeler.
    num_colors: int = len(config.colors)
    labels = rng.integers(num_colors, size=config.intervals)

    def labeler(color: Color, intervals: np.ndarray[Interval]) -> np.ndarray(Interval):
        """Returns the intervals associated with a given color."""
        color_idx: int = config.colors.index(color)
        return intervals[labels == color_idx]

    # Defines a null cleanser.
    def cleanser(original: Intervals, _: Intervals) -> Intervals:
        """Does not prune anything due to how the labeler works."""
        return original

    # Generates the chromatic intervals.
    label_to_intervals, intervals_to_labels = _get_exclusive_chromatic_intervals(
        config.n, config.colors, iter(markers), labeler, cleanser
    )
    # Flattens intervals to labels due to exclusive property.
    flat_intervals_to_labels: Dict[Interval, Color] = {}
    for interval, labels in intervals_to_labels.items():
        assert len(labels) == 1, f"{interval}:{labels}"
        flat_intervals_to_labels[interval] = labels.pop()

    return label_to_intervals, flat_intervals_to_labels


def _anneal_intervals(intervals: Intervals) -> Intervals:
    "Combines intervals that are next to each other."
    # Sorts intervals by start.
    intervals = sorted(intervals, key=lambda interval: interval[0])

    # Anneals consecutive and overlapping intervals together.
    proposed_start, proposed_end = intervals[0]
    for cur_start, cur_end in intervals:
        if cur_start <= proposed_end:
            proposed_end = cur_end
        else:
            yield proposed_start, proposed_end
            proposed_start = cur_start
            proposed_end = cur_end

    yield proposed_start, proposed_end


def _prompt_intervals(intervals: Iterable[Interval]) -> str:
    """Given an iterable of intervals, turn it into a prompt of intervals."""
    # Picks off end for "and" handling.
    *left, terminus = intervals
    # Two interval handling.
    if len(left) == 1:
        start, end = left[0]
        yield f"{start} to {end-1} "
    # 3 or more interval handling.
    else:
        for start, end in left:
            yield f"{start} to {end-1}, "
    # Terminating sentence handling.
    start, end = terminus
    yield f"and {start} to {end-1}" if left else f"{start} to {end-1}"


def _prompt_extensional(intervals: Iterable[Interval]) -> str:
    """Given an iterable of intervals, turn it into an extensional prompt of intervals."""
    # Picks off end for "and" handling.
    times: Iterable = itertools.chain(*[range(start, end) for start, end in intervals])
    *left, terminus = times
    # Two times handling.
    if len(left) == 1:
        yield f"{left[0]} "
    # 3 or more interval handling.
    else:
        for time in left:
            yield f"{time}, "
    # Terminating sentence handling.
    yield f"and {terminus}" if left else f"{terminus}"


@dataclass(frozen=True, slots=True)
class Prompter:
    """Everything needed to prompt an LLM given the context."""

    template: string.Template
    substitution: Dict[str, str]
    query_gen: Callable[
        [Dict[Color, Intervals], Dict[Interval, Color], int], Iterable[Dict[str, str]]
    ]


def get_random_exclusive_prompts(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
) -> Tuple[str, str]:
    """
    Generates an intensional and extensional prompt for the LLM.
    """
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(
        config
    )

    # Creates the intensional and extensional representation.
    intension: str = ""
    extension: str = ""
    for color, inters in label_to_intervals.items():
        if not inters.any():
            continue
        anneal: Intervals = tuple(_anneal_intervals(inters))
        intension += f"{color} was {prompter.substitution["role"]} on {
            "".join(_prompt_intervals(iter(anneal)))}.\n"
        extension += f"{color} was {prompter.substitution["role"]} on {
            "".join(_prompt_extensional(anneal))}.\n"

    # Creates different types of queries.
    for query, answer in prompter.query_gen(
        label_to_intervals, intervals_to_labels, config.seed
    ):
        substitution = query | prompter.substitution
        # Creates the intensional prompt.
        substitution["positive_info"] = intension
        intens = prompter.template.safe_substitute(substitution)
        # Creates the extensional prompt.
        substitution["positive_info"] = extension
        extens = prompter.template.safe_substitute(substitution)

        yield intens, extens, answer


if __name__ == "__main__":
    template = string.Template(
        "Context:\n"
        "---\n"
        "There is a ceremonial role called the $role, whose job it is to"
        " head the $parade parade. No one else besides the $role is able to head"
        " the $parade parade. The following lists the people who were $role and"
        " the years they were $role:\n"
        "$positive_info\n"
        "\n"
        "Query:\n"
        "Between the years $start and $end, exclusive of the end, could $color"
        " have headed the $parade parade every year?"
    )

    def query_gen(
        labels_to_intervals: Dict[Color, Intervals],
        interval_to_label: Dict[Intervals, Color],
        seed: int,
    ) -> Dict[str, str]:
        """Generates a series of queries"""
        rng: np.random.Generator = np.random.default_rng(seed)
        # Finds max interval.
        n: int = max(interval[1] for interval in interval_to_label)
        for color, intervals in labels_to_intervals.items():
            # Generates a series of true items.
            for start, end in intervals:
                start, end = np.sort(
                    rng.choice(range(start, end + 1), size=2, replace=False)
                )
                yield {"color": color, "start": start, "end": end}, True
            # Generates a false proposition.
            invalid_range: Intervals = _anneal_intervals(
                itertools.chain(
                    (set(interval_to_label.keys()) - set(itertools.chain(*intervals)))
                )
            )
            for start, end in invalid_range:
                start = rng.choice(range(start, end))
                # Binom with p = intervals / n capped at end for a similar-ish
                # distr. to positive accounts.
                end = min(
                    end,
                    start
                    + rng.binomial(
                        end - start + 1,
                        np.mean([len(interval) for interval in interval_to_label]) / n,
                    )
                    + 1,
                )
                yield {"color": color, "start": start, "end": end}, False

    for inte, exte, ans in get_random_exclusive_prompts(
        ChromaticIntervalsConfig(
            n=250,
            intervals=250 // 4,
            colors=45,
            seed=1776,
        ),
        Prompter(
            template,
            {
                "role": "Twislax",
                "parade": "Gildane",
            },
            query_gen,
        ),
    ):
        print(inte)
        print(exte)
        print(ans)
