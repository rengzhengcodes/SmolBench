"""
Generates chromatic intervals.
"""

import string
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias, Collection, Iterable, Tuple, Dict, Callable, Optional
from ordered_set import OrderedSet

import numpy as np

from smolbench.evals import Quiz, ToF, Numeric

# A color in the mathematical sense of some label.
Color: TypeAlias = str
# Interval of the form [start, end) as indices of some Sequence.
Interval: TypeAlias = Tuple[int, int]
# A collection of intervals.
Intervals: TypeAlias = Collection[Interval]


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
        if self.n < 1:
            raise ValueError("n must be positive.")
        if self.intervals < 1:
            raise ValueError("intervals must be positive.")
        if self.intervals > self.n:
            raise ValueError(
                "intervals cannot exceed n for exclusive interval generation."
            )

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


@dataclass(frozen=True, slots=True)
class Prompter:
    """Everything needed to prompt an LLM given the context."""

    template: string.Template
    substitution: Dict[str, str]
    query_gen: Callable[
        [Dict[Color, Intervals], Dict[Interval, Color], int], Iterable[Dict[str, str]]
    ]
    #: Optional template for extensional prompts. Uses $query_years instead of
    #: $start/$end so the query representation matches the extensional context.
    #: Falls back to template if not provided.
    extens_template: Optional[string.Template] = None


def _get_random_colors(
    n: int,
    l: int,
    rng: np.random.Generator,
    charset: Collection[str] = string.ascii_letters,
) -> OrderedSet[Color]:
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
    OrderedSet of unique colors.

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
    return OrderedSet("".join(color) for color in charset_array[digits])


def _assign_colors(
    intervals: Collection[Interval],
    colors: Collection[Color],
    labeler: Callable[[Color, Intervals], Intervals],
    cleanser: Callable[[Intervals, Intervals], Intervals],
) -> Tuple[Dict[Color, Intervals], Dict[Interval, OrderedSet[Color]]]:
    """
    Given an ordered collection of intervals, assign colors to each interval.

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
    intervals_to_label: Dict[Interval, Color] = defaultdict(OrderedSet)
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
    intervals: OrderedSet[Interval] = np.array(
        tuple(_get_random_exclusive_intervals(n, intervaler))
    )
    return _assign_colors(intervals, colors, labeler, cleanser)


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
        np.arange(config.n), config.intervals - 1, replace=False
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
    if len(intervals_to_labels) != config.intervals:
        raise AssertionError(
            "Generated interval count does not match the requested interval count."
        )
    # Flattens intervals to labels due to exclusive property.
    flat_intervals_to_labels: Dict[Interval, Color] = {}
    for interval, labels in intervals_to_labels.items():
        assert len(labels) == 1, f"{interval}:{labels}"
        flat_intervals_to_labels[interval] = labels.pop()

    return label_to_intervals, flat_intervals_to_labels


def anneal_intervals(intervals: Intervals) -> Intervals:
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
    """Given an iterable of intervals, turn it into a prompt of intervals.

    Uses exclusive-end notation (e.g. "5 to 10") to match the query convention.
    """
    # Picks off end for "and" handling.
    *left, terminus = intervals
    # Two interval handling.
    if len(left) == 1:
        start, end = left[0]
        yield f"{start} to {end} "
    # 3 or more interval handling.
    else:
        for start, end in left:
            yield f"{start} to {end}, "
    # Terminating sentence handling.
    start, end = terminus
    yield f"and {start} to {end}" if left else f"{start} to {end}"


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


def _prompt_extensional_indexed(intervals_to_labels: Dict[Interval, Color]) -> str:
    """Yields one 'Year X: Color.\n' line per year in chronological order.

    Produces a year-keyed context so the model can resolve each queried year with
    a direct key lookup instead of scanning a comma-separated list. Each year
    appears exactly once due to the exclusive interval property.
    """
    for (start, end), color in sorted(intervals_to_labels.items()):
        for year in range(start, end):
            yield f"Year {year}: {color}.\n"


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

    # Creates the intensional representation (person-indexed, interval format).
    intension: str = ""
    for color, inters in label_to_intervals.items():
        if not inters.any():
            continue
        anneal: Intervals = tuple(anneal_intervals(inters))
        intension += f"{color} was {prompter.substitution["role"]} on {
            "".join(_prompt_intervals(iter(anneal)))}.\n"

    # Creates the extensional representation (year-indexed, direct lookup format).
    extension: str = "".join(_prompt_extensional_indexed(intervals_to_labels))

    extens_template = prompter.extens_template or prompter.template

    # Creates different types of queries.
    for query, answer in prompter.query_gen(
        label_to_intervals, intervals_to_labels, config.seed
    ):
        # Creates the intensional prompt (interval query matches interval context).
        intens_sub = query | prompter.substitution | {"positive_info": intension}
        intens = prompter.template.safe_substitute(intens_sub)

        # Creates the extensional prompt. If an extens_template is provided it uses
        # $query_years (an enumerated list of the queried years) so the query
        # representation matches the extensional context, removing the need to
        # mentally expand an interval query against an already-enumerated context.
        extens_sub = query | prompter.substitution | {"positive_info": extension}
        if "start" in query and "end" in query:
            start, end = int(query["start"]), int(query["end"])
            extens_sub["query_years"] = "".join(_prompt_extensional([(start, end)]))
        extens = extens_template.safe_substitute(extens_sub)

        yield intens, extens, answer


def get_random_exclusive_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz]:
    """
    Wraps get_random_exclusive_prompts to produce a QnA format.

    Returns
    -------
    intensional Quiz, extensional Quiz
    """
    intens_quiz: Quiz = []
    extens_quiz: Quiz = []
    for intens, extens, answer in get_random_exclusive_prompts(config, prompter):
        intens_quiz.append(ToF(prompt=intens, answer=answer))
        extens_quiz.append(ToF(prompt=extens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz)


def duration_query_gen(
    label_to_intervals: Dict[Color, Intervals],
    intervals_to_labels: Dict[Interval, Color],
    seed: int,
) -> Iterable[Tuple[Dict[str, str], int]]:
    """Yields (query_dict, total_years) per color for duration queries.

    The answer is the total number of years that color held the role,
    computed as sum(end - start) over its annealed intervals.
    """
    for color, intervals in label_to_intervals.items():
        if not intervals:
            continue
        annealed = tuple(anneal_intervals(intervals))
        total = sum(end - start for start, end in annealed)
        yield {"color": color}, total


def get_random_exclusive_numeric_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz]:
    """Like get_random_exclusive_quiz but yields Numeric items for integer answers."""
    intens_quiz: Quiz = []
    extens_quiz: Quiz = []
    for intens, extens, answer in get_random_exclusive_prompts(config, prompter):
        intens_quiz.append(Numeric(prompt=intens, answer=answer))
        extens_quiz.append(Numeric(prompt=extens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz)


if __name__ == "__main__":
    template = string.Template(
        "Context:\n"
        "---\n"
        "There is a ceremonial role called the $role, whose job it is to"
        " head the $parade parade. No one else besides the $role is able to head"
        " the $parade parade. At the end of one's term as $role, they have a ceremony"
        " where they hand off the $role ceremonial sceptre to their successor."
        " The following lists the people who were $role and the years they were $role:\n"
        "$positive_info\n"
        "\n"
        "Query:\n"
        "Has $color1 handed the sceptre to $color2? Answer with only one word:"
        " 'True' or 'False'."
    )

    def query_gen(
        labels_to_intervals: Dict[Color, Intervals],
        interval_to_label: Dict[Interval, Color],
        seed: int,
    ) -> Iterable[Tuple[Dict[str, str], bool]]:
        """Generates direct-succession queries."""
        rng: np.random.Generator = np.random.default_rng(seed)
        sorted_intervals = sorted(interval_to_label.items(), key=lambda item: item[0][0])
        # True cases: pairs where color2 immediately followed color1.
        true_pairs: OrderedSet = OrderedSet(
            (c1, c2)
            for ((_s1, e1), c1), ((s2, _e2), c2) in zip(sorted_intervals, sorted_intervals[1:])
        )
        for color1, color2 in true_pairs:
            yield {"color1": color1, "color2": color2}, True
        # False cases: same count, randomly sampled non-successor pairs.
        all_colors: list = list(labels_to_intervals.keys())
        false_pairs: OrderedSet = OrderedSet()
        while len(false_pairs) < len(true_pairs):
            c1, c2 = (str(c) for c in rng.choice(all_colors, size=2, replace=False))
            if (c1, c2) not in true_pairs:
                false_pairs.add((c1, c2))
        for color1, color2 in false_pairs:
            yield {"color1": color1, "color2": color2}, False

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
