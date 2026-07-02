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
    build_substitution,
    noise_pad,
    quizzes_from_prompts,
    random_labels,
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
            # min_length=0 (the default): unlike periodic's labels, chromatic
            # colors have no multi-character floor -- see random_labels'
            # docstring for why that is a no-op here (the length formula is
            # already >= 0 for any valid count >= 1).
            object.__setattr__(
                self,
                "colors",
                random_labels(
                    self.colors, self.seed, charset=string.ascii_letters
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


def _join_english_list(items: Iterable[str]) -> Iterator[str]:
    """Joins pre-rendered item strings into a comma-and-"and" English list.

    Shared join structure behind ``_prompt_intervals`` and
    ``_prompt_extensional``: both render a sequence of strings this same
    way (only the per-item rendering differs -- interval ranges like
    "5 to 10" vs. individual years like "7"), so the join logic lives here
    exactly once. Merging was verified to leave both callers'
    byte-for-byte output unchanged (each caller now just pre-renders its
    items to strings, then delegates the joining).

    Formatting rules -- deliberately NOT the Oxford-comma convention for
    exactly two items, to match natural "A and B" phrasing rather than
    "A, and B":

    - 1 item: yielded alone, unadorned.
    - 2 items: ``"item1 "`` then ``"and item2"``, concatenating to
      ``"item1 and item2"`` (space-separated, no comma).
    - 3+ items: ``"item, "`` for every item but the last, then
      ``"and itemN"`` for the last, concatenating to
      ``"item1, item2, ..., and itemN"``.

    Parameters
    ----------
    items:
        Pre-rendered item strings, in display order.

    Yields
    ------
    str
        Fragments that concatenate (e.g. via ``"".join``) into the full
        English list.

    Raises
    ------
    ValueError
        If ``items`` is empty: unpacking requires at least one item. Both
        callers here always pass at least one interval/year, so this is
        unreachable through them, not newly introduced by the merge.
    """
    # Picks off the last item for "and" handling.
    *left, terminus = items
    if len(left) == 1:
        # Exactly two items: no comma, just "A " + "and B".
        yield f"{left[0]} "
    else:
        # Three or more items: comma-separate everything but the last.
        for item in left:
            yield f"{item}, "
    # Terminating sentence handling: "and " prefix only when there was a
    # preceding item to conjoin with (i.e. not the lone-item case).
    yield f"and {terminus}" if left else f"{terminus}"


def _prompt_intervals(intervals: Iterable[Interval]) -> Iterator[str]:
    """Given an iterable of intervals, turn it into a prompt of intervals.

    Uses exclusive-end notation (e.g. "5 to 10") to match the query convention.
    """
    yield from _join_english_list(f"{start} to {end}" for start, end in intervals)


def _prompt_extensional(intervals: Iterable[Interval]) -> Iterator[str]:
    """Given an iterable of intervals, turn it into an extensional prompt of intervals."""
    times: Iterable = itertools.chain(*[range(start, end) for start, end in intervals])
    yield from _join_english_list(str(time) for time in times)


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
    # Hoisted out of the loop: constant across colors, and pulling it out of
    # the f-string avoids nesting a "..." lookup inside an f-string that is
    # itself delimited with "...", which forced the original onto an
    # awkward line-broken replacement field just to keep the quoting legal.
    role: str = prompter.substitution["role"]
    for color, inters in label_to_intervals.items():
        if not inters.any():
            continue
        anneal: Intervals = tuple(anneal_intervals(inters))
        intervals_str: str = "".join(_prompt_intervals(iter(anneal)))
        intension += f"{color} was {role} on {intervals_str}.\n"

    # Creates the extensional representation (year-indexed, direct lookup format).
    extension: str = "".join(_prompt_extensional_indexed(intervals_to_labels))

    # Creates the noise-padded intensional context: intension + noise to match
    # the extensional length, so context-length is not a confound between the two.
    noise_intension: str = noise_pad(intension, extension, config.seed)

    # Creates different types of queries.
    for query, answer in prompter.query_gen(
        label_to_intervals, intervals_to_labels, config.seed
    ):
        # Creates the intensional prompt (interval query matches interval context).
        intens_sub = build_substitution(query, prompter, intension)
        intens = prompter.template.safe_substitute(intens_sub)

        # Creates the extensional prompt. If an extens_template is provided it uses
        # $query_years (an enumerated list of the queried years) so the query
        # representation matches the extensional context, removing the need to
        # mentally expand an interval query against an already-enumerated context.
        extens_sub = build_substitution(query, prompter, extension)
        if "start" in query and "end" in query:
            start, end = int(query["start"]), int(query["end"])
            extens_sub["query_years"] = "".join(_prompt_extensional([(start, end)]))
        extens = prompter.resolved_extens_template.safe_substitute(extens_sub)

        # Creates the noise-padded intensional prompt (same template/query as intens,
        # but positive_info is padded with random noise to match extensional length).
        noise_intens_sub = build_substitution(query, prompter, noise_intension)
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
    computed as sum(end - start) over its annealed intervals. A color that
    was assigned zero intervals is skipped entirely (there is nothing to
    anneal or sum); a color assigned only degenerate zero-length intervals
    (start == end) is NOT skipped -- it still yields a query, correctly
    answered with total=0, since it did hold the role for an (empty) span.

    Notes
    -----
    ``intervals`` here is the 2D ndarray built by
    ``get_random_exclusive_chromatic_intervals`` (``intervals_arr[labels ==
    color_idx]``), shape ``(num_intervals, 2)``. The "no intervals for this
    color" check must therefore be a *count* check (``len(intervals) == 0``,
    i.e. zero rows) rather than a truthiness/value check: ``bool(ndarray)``
    is only well-defined when the array holds exactly one element, so
    ``if not intervals:`` raises ``ValueError`` for any color holding one or
    more intervals (each row already has 2 elements). The superficially
    similar ``if not intervals.any():`` idiom used elsewhere in this module
    does evaluate without raising, but it checks element *values*, not
    interval *count* -- it would wrongly treat a color holding a single
    ``(0, 0)`` interval as having none (both elements are falsy), silently
    dropping a duration query that should legitimately answer 0. A row-count
    check has neither failure mode.
    """
    for color, intervals in label_to_intervals.items():
        if len(intervals) == 0:
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
