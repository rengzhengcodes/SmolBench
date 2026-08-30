"""Test chromatic-interval induction (sceptre-handoff sequences).

Measures whether a model can answer questions about a timeline of ``n``
discrete units (e.g. years) tiled by ``intervals`` consecutive,
non-overlapping, exclusive-end ``[start, end)`` spans, each independently
assigned one of ``colors`` labels
(:func:`get_random_exclusive_chromatic_intervals`); the demo frames those as
office-holders handing a ceremonial sceptre to their successor at each
interval boundary. Three query shapes are built in:
:func:`succession_query_gen` (True/False: did color2 immediately follow
color1?), :func:`one_hop_year_query_gen` (True/False: did a color hold a
given year?), and :func:`duration_query_gen` (integer: how many years total,
after merging that color's adjacent intervals via
:func:`anneal_intervals`). :class:`ChromaticIntervalsConfig` plus a
``_common.Prompter`` determine a run, via
:func:`get_random_exclusive_prompts`; this module holds generation machinery
and query generators, not canonical eval configs.

Information conditions, all built from one set of intervals:
**intensional** = one line per color naming the (annealed) span(s) it held,
"<color> was <role> on 0 to 8." (:func:`_prompt_intervals`);
**extensional** = the enumerated year -> color table, one "Year Y: Color."
line per year (:func:`_prompt_extensional_indexed`), always at least as
long; **noise_intens** = the intensional text padded with whitespace to the
extensional prompt's token count under the model's own tokenizer. Matching
the RENDERED PROMPT rather than the context block matters here in
particular: the extensional arm renders from ``extens_template`` with an
extra ``$query_years`` block, so equal-length CONTEXTS would still give
unequal-length PROMPTS.

Every generator takes an explicit ``seed`` and builds its own RNG, so a run
is reproducible from its config; the noise pad consumes no RNG. The noise
arm's tokenizer is REQUIRED, not defaulted, so quizzes stay per-(seed,
model) with only ``noise_intens`` varying across models (see
``smolbench/induction/periodic.py``'s module docstring for why). Generation
is byte-pinned by ``tests/induction/test_golden_quizzes.py``, and further
exercised by ``tests/induction/test_noise_token_match.py`` and
``tests/induction/test_induction_semantics.py``: any change to RNG call
order or count (color/label, marker/interval, query sampling), or to the
noise-padding scheme, breaks that pin -- fix the change, never the fixture.
The ``__main__`` demo uses seed 1776.
"""

import string
import itertools
from dataclasses import dataclass
from typing import TypeAlias, Collection, Iterable, Iterator, Tuple, Dict

from ordered_set import OrderedSet
import numpy as np

from smolbench.evals import Quiz, ToF, Numeric
from smolbench.evals.tokenization import TiktokenTokenizer, Tokenizer
from smolbench.induction._common import (
    Prompter,
    build_substitution,
    choose_whitespace_unit,
    context_renderer,
    quizzes_from_prompts,
    random_labels,
    token_matched_noise_prompt,
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
    """Configure the generation of one set of chromatic intervals."""

    #: Number of discrete units in the timeline.
    n: int
    #: Number of intervals.
    intervals: int
    #: Number of colors to auto-generate, or a Collection of colors to assign.
    colors: Collection[Color] | int
    #: RNG seed for reproducibility.
    seed: int

    def __post_init__(self):
        """Validate n, intervals, and colors, and turn colors into a Collection.

        Raises
        ------
        ValueError
            If ``n`` or ``intervals`` is not positive, or if ``intervals``
            exceeds ``n`` (exclusive interval generation needs at least one
            discrete unit per interval).
        """
        if self.n < 1:
            raise ValueError("n must be positive.")
        if self.intervals < 1:
            raise ValueError("intervals must be positive.")
        if self.intervals > self.n:
            raise ValueError(
                "intervals cannot exceed n for exclusive interval generation."
            )

        # This generates the colors when the caller passed a count.
        if isinstance(self.colors, int):
            # min_length=0 (the default): unlike periodic's labels, chromatic
            # colors have no multi-character floor. See random_labels'
            # docstring for why that is a no-op here: the length formula is
            # already >= 0 for any valid count >= 1.
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
    """Generate consecutive non-overlapping [start, end) intervals tiling [0, n).

    ``intervaler`` supplies candidate endpoints (e.g. sorted random markers);
    each end is clamped to ``n`` and the final interval always closes at ``n``.
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
    """Generate a set of intervals from [0, n), each an equally likely color.

    Returns
    -------
    Tuple[Dict[Color, Collection[Interval]], Dict[Interval, Color]]
        Color-to-intervals and intervals-to-color. Both preserve color-major
        insertion order (all of the first color's intervals, then the
        second's, ...), which downstream query generators rely on for
        reproducible RNG consumption.
    """

    # This seeds the RNG and generates the interval demarcations.
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

    # This bookkeeping runs in color-major order (see the Returns note). The
    # exclusive property holds by construction: each interval got exactly
    # one draw.
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
    """Combine intervals that touch or overlap into merged spans.

    Yields merged (start, end) tuples in ascending start order; two intervals
    merge when the second starts at or before the first one's end.
    ``intervals`` must be non-empty -- ``intervals[0]`` seeds the merge.
    """
    # This sorts the intervals by start.
    intervals = sorted(intervals, key=lambda interval: interval[0])

    # This anneals consecutive and overlapping intervals together.
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
    """Join pre-rendered item strings into a comma-and-"and" English list.

    Shared by ``_prompt_intervals`` and ``_prompt_extensional``, which differ
    only in per-item rendering. Yields fragments that concatenate (e.g. via
    ``"".join``) into the list. No Oxford comma at exactly two items:

    - 1 item: yielded alone, unadorned.
    - 2 items: ``"item1 "`` + ``"and item2"`` -> ``"item1 and item2"``.
    - 3+ items: ``"item, "`` per item but the last, then ``"and itemN"``.

    Raises
    ------
    ValueError
        If ``items`` is empty (unpacking needs at least one item);
        unreachable through either caller.
    """
    # This picks off the last item for "and" handling.
    *left, terminus = items
    if len(left) == 1:
        # Exactly two items: no comma, just "A " + "and B".
        yield f"{left[0]} "
    else:
        # Three or more items: comma-separate everything but the last.
        for item in left:
            yield f"{item}, "
    # This handles the terminating sentence: an "and " prefix appears only
    # when there was a preceding item to conjoin with (not the lone-item
    # case).
    yield f"and {terminus}" if left else f"{terminus}"


def _prompt_intervals(intervals: Iterable[Interval]) -> Iterator[str]:
    """Turn an iterable of intervals into a prompt fragment listing them.

    Uses exclusive-end notation (e.g. "5 to 10") to match the query
    convention.
    """
    yield from _join_english_list(f"{start} to {end}" for start, end in intervals)


def _prompt_extensional(intervals: Iterable[Interval]) -> Iterator[str]:
    """Turn an iterable of intervals into an extensional prompt fragment."""
    times: Iterable = itertools.chain(*[range(start, end) for start, end in intervals])
    yield from _join_english_list(str(time) for time in times)


def _prompt_extensional_indexed(intervals_to_labels: Dict[Interval, Color]) -> Iterator[str]:
    """Yield one newline-terminated 'Year X: Color.' line per year, chronologically.

    A year-keyed context, so the model resolves a queried year by direct
    lookup rather than scanning a comma-separated list. Each year appears
    exactly once, by the exclusive-interval property.
    """
    for (start, end), color in sorted(intervals_to_labels.items()):
        for year in range(start, end):
            yield f"Year {year}: {color}.\n"


def get_random_exclusive_prompts(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
) -> Iterable[Tuple[str, str, str, bool]]:
    """Generate an intensional, extensional, and noise-padded intensional prompt.

    Yields ``(intens, extens, noise_intens, answer)`` per query. The
    noise-padded prompt keeps the intensional interval-format context but
    appends whitespace until the RENDERED prompt has exactly as many tokens
    as the extensional prompt for the SAME query, ablating context length as
    a confound. ``tokenizer`` defines that token target and must be the
    model's own (``tokenization.for_model(model)``) -- see the module
    docstring's tokenizer discipline.
    """
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(
        config
    )

    # This builds the intensional representation (person-indexed, interval
    # format).
    intension: str = ""
    # This hoists `role` out of the loop: it is constant across colors, and
    # pulling it out of the f-string avoids nesting a "..." lookup inside an
    # f-string that is itself delimited with "...".
    role: str = prompter.substitution["role"]
    for color, inters in label_to_intervals.items():
        if not inters.any():
            continue
        anneal: Intervals = tuple(anneal_intervals(inters))
        intervals_str: str = "".join(_prompt_intervals(iter(anneal)))
        intension += f"{color} was {role} on {intervals_str}.\n"

    # This builds the extensional representation (year-indexed, direct
    # lookup format).
    extension: str = "".join(_prompt_extensional_indexed(intervals_to_labels))

    # This probes the whitespace pad atom once here, not per query: the
    # atom depends only on the tokenizer, and probing it inside the loop
    # would repeat the same measurements for every question.
    unit: str = choose_whitespace_unit(tokenizer)

    # This builds each query's prompts.
    for query, answer in prompter.query_gen(
        label_to_intervals, intervals_to_labels, config.seed
    ):
        # This builds the intensional prompt (interval query matches
        # interval context).
        intens_sub = build_substitution(query, prompter, intension)
        intens = prompter.template.safe_substitute(intens_sub)

        # This builds the extensional prompt. When the caller supplies an
        # extens_template, it uses $query_years (an enumerated list of the
        # queried years), so the query representation matches the
        # extensional context. This removes the need to mentally expand an
        # interval query against an already-enumerated context.
        extens_sub = build_substitution(query, prompter, extension)
        if "start" in query and "end" in query:
            start, end = int(query["start"]), int(query["end"])
            extens_sub["query_years"] = "".join(_prompt_extensional([(start, end)]))
        extens = prompter.resolved_extens_template.safe_substitute(extens_sub)

        # This builds the noise-padded intensional prompt: same
        # template/query as intens, but positive_info is padded with
        # whitespace until the whole rendered prompt matches THIS query's
        # extensional prompt, token for token. That includes the
        # $query_years block extens_template adds; a context-level match
        # could never account for that block.
        noise_intens = token_matched_noise_prompt(
            context_renderer(prompter, query),
            intension,
            tokenizer.count(extens),
            tokenizer,
            unit=unit,
        )

        yield intens, extens, noise_intens, answer


def get_random_exclusive_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
) -> Tuple[Quiz, Quiz, Quiz]:
    """Wrap :func:`get_random_exclusive_prompts` to produce True/False QnA format.

    Arguments are forwarded verbatim. Returns the intensional, extensional,
    and noise-padded intensional Quiz, in that order.
    """
    return quizzes_from_prompts(
        get_random_exclusive_prompts(config, prompter, tokenizer=tokenizer), ToF
    )


def get_random_exclusive_numeric_quiz(
    config: ChromaticIntervalsConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
) -> Tuple[Quiz, Quiz, Quiz]:
    """Wrap :func:`get_random_exclusive_prompts` to produce integer-answer QnA format.

    As :func:`get_random_exclusive_quiz`, but wraps each prompt in a
    ``Numeric`` item instead of a ``ToF`` one. Arguments are forwarded
    verbatim. Returns the intensional, extensional, and noise-padded
    intensional Quiz, in that order.
    """
    return quizzes_from_prompts(
        get_random_exclusive_prompts(config, prompter, tokenizer=tokenizer), Numeric
    )


# ---------------------------------------------------------------------------
# Built-in query generators
# ---------------------------------------------------------------------------
# These are the importable task definitions (mirroring periodic.py's built-in
# generators). The offline test suite (tests/induction/test_golden_quizzes.py,
# tests/induction/test_noise_token_match.py, tests/induction/test_induction_semantics.py) and
# the __main__ demo consume these SAME functions, so the statistically
# load-bearing query sampling exists in exactly one place.

def succession_query_gen(
    labels_to_intervals: Dict[Color, Intervals],
    interval_to_label: Dict[Interval, Color],
    seed: int,
) -> Iterable[Tuple[Dict[str, str], bool]]:
    """Generate direct-succession queries.

    Yields ``({"color1": ..., "color2": ...}, answer)`` pairs: True for each
    unique (predecessor, successor) pair, then an equal number of False
    queries from randomly-sampled non-successor pairs (``seed`` drives only
    that sampling). Both mappings come from
    :func:`get_random_exclusive_chromatic_intervals`.
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
    """Generate single-year queries (one-hop for both representations).

    Yields ``({"color": ..., "year": ...}, answer)`` pairs: True for one
    random year from each interval the color holds, False for one random year
    from another color's interval, per interval held. Both mappings come from
    :func:`get_random_exclusive_chromatic_intervals`; ``seed`` drives the year
    sampling.
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
    """Yield a ``({"color": ...}, total_years)`` pair per color.

    ``total_years`` is sum(end - start) over the color's annealed intervals.
    A color assigned zero intervals is skipped; one assigned only degenerate
    zero-length intervals (start == end) is NOT, and correctly answers 0.
    ``intervals_to_labels`` and ``seed`` are unused here (duration queries
    need neither direction nor sampling) but every ``query_gen`` in this
    module shares one signature.

    Notes
    -----
    ``intervals`` is the ``(num_intervals, 2)`` ndarray that
    ``get_random_exclusive_chromatic_intervals`` builds, so the "no intervals"
    check must be a row-COUNT check (``len(intervals) == 0``). ``if not
    intervals:`` raises ``ValueError`` for any multi-element array, and the
    ``if not intervals.any():`` idiom used elsewhere in this module checks
    element VALUES, so it would drop a color holding a single ``(0, 0)``
    interval whose duration query legitimately answers 0.
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

    # No served model here; use the same fixed tiktoken encoding as
    # periodic.py's demo. See the module docstring's tokenizer discipline.
    demo_tokenizer = TiktokenTokenizer("cl100k_base")

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
        tokenizer=demo_tokenizer,
    ):
        print(inte)
        print(exte)
        print(ans)
        print(
            "token counts -- intens:", demo_tokenizer.count(inte),
            "extens:", demo_tokenizer.count(exte),
            "noise_intens:", demo_tokenizer.count(noise_inte),
        )
