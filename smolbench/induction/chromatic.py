"""
Generates chromatic intervals.
"""

import string
import itertools
from dataclasses import dataclass
from typing import TypeAlias, Collection, Iterable, Iterator, Tuple, Dict

from ordered_set import OrderedSet
import numpy as np

from smolbench.evals import Quiz, ToF, Numeric
from smolbench.induction._common import (
    Prompter,
    make_noise,
    quizzes_from_prompts,
    random_unique_strings,
)

# Prompter is re-exported: the class is shared with periodic so the prompting
# contract stays identical across benchmarks.
__all__ = [
    "ChromaticIntervalsConfig",
    "Prompter",
    "Color",
    "Interval",
    "Intervals",
    "anneal_intervals",
    "get_random_exclusive_chromatic_intervals",
    "get_random_exclusive_prompts",
    "get_random_exclusive_quiz",
    "get_random_exclusive_numeric_quiz",
    "succession_query_gen",
    "one_hop_year_query_gen",
    "duration_query_gen",
]

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
                    random_unique_strings(
                        self.colors, length, np.random.default_rng(self.seed),
                        charset=string.ascii_letters,
                    )
                ),
            )
        else:
            object.__setattr__(self, "colors", tuple(self.colors))


def _get_random_exclusive_intervals(n: int, intervaler: Iterator[int]) -> Iterator[Interval]:
    """
    Generates consecutive non-overlapping [start, end) intervals tiling [0, n).

    Parameters
    ----------
    n:
        Exclusive upper bound of the covered range [0, n).
    intervaler:
        Iterator of candidate interval endpoints (e.g. sorted random
        markers); each yielded end is clamped to n and the final interval
        always closes at n.

    Yields
    ------
    Consecutive non-overlapping (start, end) tuples whose ends tile [0, n).
    """
    start: int = 0
    end: int = 0

    while end < n:
        end = min(n, next(intervaler, n))
        yield (start, end)
        start = end


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
    colors. Both preserve color-major insertion order (all of the first
    color's intervals, then the second's, ...), which downstream query
    generators rely on for reproducible RNG consumption.
    """

    # Seeds and generates the interval demarcations.
    rng: np.random.Generator = np.random.default_rng(config.seed)
    markers: np.ndarray = rng.choice(
        np.arange(config.n), config.intervals - 1, replace=False
    )
    markers.sort()

    # Uniform color assignment: one independent draw per interval.
    num_colors: int = len(config.colors)
    labels = rng.integers(num_colors, size=config.intervals)

    intervals_arr: np.ndarray = np.array(
        tuple(_get_random_exclusive_intervals(config.n, iter(markers)))
    )

    # Bookkeeping in color-major order (see the Returns note). The exclusive
    # property holds by construction: each interval got exactly one draw.
    label_to_intervals: Dict[Color, Intervals] = {}
    intervals_to_labels: Dict[Interval, Color] = {}
    for color_idx, color in enumerate(config.colors):
        assignment: np.ndarray = intervals_arr[labels == color_idx]
        label_to_intervals[color] = assignment
        for interval in assignment:
            intervals_to_labels[tuple(interval.tolist())] = color

    if len(intervals_to_labels) != config.intervals:
        raise AssertionError(
            "Generated interval count does not match the requested interval count."
        )
    return label_to_intervals, intervals_to_labels


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


def _prompt_intervals(intervals: Iterable[Interval]) -> Iterator[str]:
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


def _prompt_extensional(intervals: Iterable[Interval]) -> Iterator[str]:
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


def _prompt_extensional_indexed(intervals_to_labels: Dict[Interval, Color]) -> Iterator[str]:
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
) -> Iterable[Tuple[str, str, str, bool]]:
    """
    Generates an intensional, extensional, and noise-padded intensional prompt for the LLM.

    The noise-padded intensional uses the same interval-format context as the
    intensional prompt but appends random noise so its positive_info length matches
    the extensional's, ablating context-length as a confound.
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

    # Creates the noise-padded intensional context: intension + noise to match
    # the extensional length, so context-length is not a confound between the two.
    noise_rng: np.random.Generator = np.random.default_rng(config.seed + 1)
    noise_intension: str = intension + make_noise(
        max(0, len(extension) - len(intension)), noise_rng
    )

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

        # Creates the noise-padded intensional prompt (same template/query as intens,
        # but positive_info is padded with random noise to match extensional length).
        noise_intens_sub = query | prompter.substitution | {"positive_info": noise_intension}
        noise_intens = prompter.template.safe_substitute(noise_intens_sub)

        yield intens, extens, noise_intens, answer


def get_random_exclusive_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz, Quiz]:
    """
    Wraps get_random_exclusive_prompts to produce a True/False QnA format.

    Returns
    -------
    (intensional Quiz, extensional Quiz, noise-padded intensional Quiz)
    """
    return quizzes_from_prompts(get_random_exclusive_prompts(config, prompter), ToF)


def get_random_exclusive_numeric_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz, Quiz]:
    """Like get_random_exclusive_quiz but yields Numeric items for integer answers."""
    return quizzes_from_prompts(get_random_exclusive_prompts(config, prompter), Numeric)


# ---------------------------------------------------------------------------
# Built-in query generators
# ---------------------------------------------------------------------------
# These are the importable task definitions (mirroring periodic.py's built-in
# generators): the notebooks and the __main__ demo consume the SAME functions,
# so the statistically load-bearing query sampling exists in exactly one place.

def succession_query_gen(
    labels_to_intervals: Dict[Color, Intervals],
    interval_to_label: Dict[Interval, Color],
    seed: int,
) -> Iterable[Tuple[Dict[str, str], bool]]:
    """Generates direct-succession queries.

    Yields True for each unique (predecessor, successor) pair and an equal
    number of False for randomly-sampled non-successor pairs. Substitution
    keys: ``$color1``, ``$color2``.
    """
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


def one_hop_year_query_gen(
    labels_to_intervals: Dict[Color, Intervals],
    interval_to_label: Dict[Interval, Color],
    seed: int,
) -> Iterable[Tuple[Dict[str, str], bool]]:
    """Generates single-year queries (one-hop for both representations).

    True: one random year sampled from each interval the colour holds.
    False: one random year sampled from another colour's interval, per
    interval held. Substitution keys: ``$color``, ``$year``.
    """
    rng: np.random.Generator = np.random.default_rng(seed)
    all_intervals: list = list(interval_to_label.items())  # [((s, e), color), ...]
    for color, intervals in labels_to_intervals.items():
        if not intervals.any():
            continue
        # True: one year drawn uniformly from each interval this colour holds.
        for start, end in intervals:
            year = int(rng.integers(start, end))
            yield {"color": color, "year": year}, True
        # False: one year drawn from a different colour's interval, per interval held.
        other_intervals: list = [(s, e) for (s, e), c in all_intervals if c != color]
        for _ in intervals:
            s, e = other_intervals[int(rng.integers(len(other_intervals)))]
            year = int(rng.integers(s, e))
            yield {"color": color, "year": year}, False


def duration_query_gen(
    label_to_intervals: Dict[Color, Intervals],
    intervals_to_labels: Dict[Interval, Color],
    seed: int,
) -> Iterable[Tuple[Dict[str, str], int]]:
    """Yields (query_dict, total_years) per color for duration queries.

    The answer is the total number of years that color held the role,
    computed as sum(end - start) over its annealed intervals.

    WARNING: currently broken against the ndarray interval collections the
    pipeline produces ("if not intervals:" raises on a multi-element array);
    unused by any notebook. Left as-is pending a correctness review.
    """
    for color, intervals in label_to_intervals.items():
        if not intervals:
            continue
        annealed = tuple(anneal_intervals(intervals))
        total = sum(end - start for start, end in annealed)
        yield {"color": color}, total


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

    for inte, exte, noise_inte, ans in get_random_exclusive_prompts(
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
            succession_query_gen,
        ),
    ):
        print(inte)
        print(exte)
        print(ans)
