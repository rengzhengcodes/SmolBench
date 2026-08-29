"""Test chromatic-interval induction (sceptre-handoff sequences).

Overview
--------
This benchmark measures whether a model can answer questions about a
timeline of ``n`` discrete units (e.g. years) tiled by ``intervals``
consecutive, non-overlapping, exclusive-end ``[start, end)`` spans, each
independently assigned one of ``colors`` labels (see
:func:`get_random_exclusive_chromatic_intervals`). The name and the demo's
prompt template frame this as a "ceremonial sceptre handoff": a sequence of
office-holders (colors), each holding a role for a contiguous span of years
(an interval), hands the role's sceptre to its immediate successor at the
interval boundary. See ``smolbench/induction/README.md``'s presidency
example, which is the same shape of problem: who held office over what
span, and who followed whom.

Three query shapes are built in, each producing a True/False or
integer-answer quiz over the same generated intervals:

- :func:`succession_query_gen` -- True/False: did color2 immediately
  follow color1 (quiz via :func:`get_random_exclusive_quiz`)?
- :func:`one_hop_year_query_gen` -- True/False: did a color hold a given
  single year?
- :func:`duration_query_gen` -- integer: how many years total did a color
  hold the role (quiz via :func:`get_random_exclusive_numeric_quiz`), after
  this function merges adjacent/overlapping intervals of that color
  (:func:`anneal_intervals`)?

Information conditions
-----------------------
A single query set can be compared across three parallel conditions, each
built from the same underlying intervals (see
:func:`get_random_exclusive_prompts`):

- **intensional**: the compact rule form, one line per color naming the
  (annealed) interval span(s) it held, e.g. "<color> was <role> on 0 to
  8." (:func:`_prompt_intervals`). This is the pattern-fitted
  representation.
- **extensional**: the fully enumerated year -> color lookup table, one
  "Year Y: Color." line per year in the timeline
  (:func:`_prompt_extensional_indexed`). This is the exhaustive
  empirical-evidence representation. It is always at least as long as the
  intensional one.
- **noise_intens**: the same intensional text, padded with whitespace to
  match the extensional prompt's token count under the model's own
  tokenizer. See ``smolbench/induction/periodic.py``'s module docstring for
  the general mechanism and rationale. A match on the rendered prompt, not
  the context block, matters here in particular: the extensional arm
  renders from ``extens_template`` with an extra ``$query_years`` block, so
  equal-length CONTEXTS would still give unequal-length PROMPTS.

Configuration
-------------
:class:`ChromaticIntervalsConfig` (n, intervals, colors, seed), plus a
``smolbench.induction._common.Prompter`` (prompt template, static
substitutions, and one of the query generators above), together determine a
run. :func:`get_random_exclusive_prompts` is the core generator that both
quiz wrappers and the ``__main__`` demo build on. This module only supplies
the generation machinery and its built-in query generators; it does not
hold canonical configs for a live eval driver. This module is exercised by
``tests/induction/test_golden_quizzes.py``,
``tests/induction/test_noise_token_match.py``, and
``tests/induction/test_induction_semantics.py``.

Seed discipline
----------------
Every generator here takes an explicit ``seed`` and builds its own RNG
internally, so a run is fully reproducible from its config; the noise pad
consumes no RNG at all. See ``smolbench/induction/periodic.py``'s module
docstring for the general rationale. The ``__main__`` demo below uses
seed 1776.

Tokenizer discipline
--------------------
The noise arm's tokenizer argument is REQUIRED, not defaulted, so
quizzes stay per-(seed, model): the intensional and extensional prompts
stay identical across models, and only ``noise_intens`` varies. See
``smolbench/induction/periodic.py``'s module docstring for why a
plausible-but-wrong default would be worse than no default.

Golden-hash contract
---------------------
Generation is byte-pinned by ``tests/induction/test_golden_quizzes.py``. A change
to RNG call order or call count here (color/label sampling,
marker/interval sampling, query sampling), or to the noise-padding
scheme, breaks that pin. The fix belongs in the change, never in a
re-baselined fixture. See ``smolbench/induction/periodic.py``'s module
docstring for the general discipline.
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
            If ``n`` is not positive, if ``intervals`` is not positive, or
            if ``intervals`` exceeds ``n`` (exclusive interval generation
            needs at least one discrete unit per interval).
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

    Parameters
    ----------
    n : int
        Exclusive upper bound of the covered range [0, n).
    intervaler : Iterator[int]
        Iterator of candidate interval endpoints (e.g. sorted random
        markers). This function clamps each yielded end to n, and the final
        interval always closes at n.

    Yields
    ------
    Interval
        Consecutive non-overlapping (start, end) tuples whose ends tile
        [0, n).
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

    Parameters
    ----------
    config : ChromaticIntervalsConfig
        Generator config.

    Returns
    -------
    Tuple[Dict[Color, Collection[Interval]], Dict[Interval, Color]]
        A dict that maps colors to intervals, and a dict that maps
        intervals to colors. Both preserve color-major insertion order (all
        of the first color's intervals, then the second's, and so on).
        Downstream query generators rely on this order for reproducible RNG
        consumption.
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

    Parameters
    ----------
    intervals : Intervals
        The intervals to combine. Must hold at least one interval; this
        function reads ``intervals[0]`` unconditionally to seed the merge.

    Yields
    ------
    Interval
        Merged (start, end) tuples, in ascending start order. Two input
        intervals merge into one output interval when the second one starts
        at or before the first one's end (touching or overlapping).
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

    This is the shared join structure behind ``_prompt_intervals`` and
    ``_prompt_extensional``: both render a sequence of strings the same way.
    Only the per-item rendering differs (interval ranges like "5 to 10" vs.
    individual years like "7"), so the join logic lives here exactly once.
    Each caller pre-renders its items to strings, then delegates the
    joining here.

    The rules below deliberately do NOT use the Oxford-comma convention for
    exactly two items; they match natural "A and B" phrasing rather than
    "A, and B":

    - 1 item: yielded alone, unadorned.
    - 2 items: ``"item1 "`` then ``"and item2"``, which concatenate to
      ``"item1 and item2"`` (space-separated, no comma).
    - 3+ items: ``"item, "`` for every item but the last, then
      ``"and itemN"`` for the last, which concatenate to
      ``"item1, item2, ..., and itemN"``.

    Parameters
    ----------
    items : Iterable[str]
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
        callers here always pass at least one interval or year, so this
        case is unreachable through them.
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
    """Yield one 'Year X: Color.\n' line per year, in chronological order.

    This produces a year-keyed context, so the model can resolve each
    queried year with a direct key lookup instead of scanning a
    comma-separated list. Each year appears exactly once, because of the
    exclusive interval property.
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

    The noise-padded intensional prompt uses the same interval-format
    context as the intensional prompt, but appends whitespace until the
    rendered prompt has exactly as many tokens as the extensional prompt
    for the same query. This ablates context length as a confound.

    Parameters
    ----------
    config : ChromaticIntervalsConfig
        The benchmark config (timeline length, interval count, colors, seed).
    prompter : Prompter
        Template, static substitutions, query generator, and the optional
        ``extens_template``.
    tokenizer : Tokenizer
        The :class:`~smolbench.evals.tokenization.Tokenizer` that defines
        the noise arm's token target. Use the tokenizer of the model this
        quiz goes to (``tokenization.for_model(model)``). This parameter is
        required by design; see the module docstring's tokenizer
        discipline.

    Yields
    ------
    Tuple[str, str, str, bool]
        ``(intens, extens, noise_intens, answer)`` for each query.
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

    Parameters
    ----------
    config, prompter, tokenizer
        Forwarded verbatim to :func:`get_random_exclusive_prompts`. See
        that function for why ``tokenizer`` is required.

    Returns
    -------
    Tuple[Quiz, Quiz, Quiz]
        The intensional Quiz, extensional Quiz, and noise-padded
        intensional Quiz, in that order.
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

    Like :func:`get_random_exclusive_quiz`, but wraps each prompt in a
    ``Numeric`` item for an integer answer, instead of a ``ToF`` item for a
    True/False answer.

    Parameters
    ----------
    config, prompter, tokenizer
        Forwarded verbatim to :func:`get_random_exclusive_prompts`. See
        that function for why ``tokenizer`` is required.

    Returns
    -------
    Tuple[Quiz, Quiz, Quiz]
        The intensional Quiz, extensional Quiz, and noise-padded
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

    Yields True for each unique (predecessor, successor) pair, and an
    equal number of False queries for randomly-sampled non-successor
    pairs. Substitution keys: ``$color1``, ``$color2``.

    Parameters
    ----------
    labels_to_intervals : Dict[Color, Intervals]
        Color-to-intervals mapping from
        :func:`get_random_exclusive_chromatic_intervals`.
    interval_to_label : Dict[Interval, Color]
        Interval-to-color mapping from
        :func:`get_random_exclusive_chromatic_intervals`.
    seed : int
        RNG seed for the False-pair sampling.

    Yields
    ------
    Tuple[Dict[str, str], bool]
        A ``({"color1": ..., "color2": ...}, answer)`` pair per query.
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

    True: one random year sampled from each interval the color holds.
    False: one random year sampled from another color's interval, per
    interval held. Substitution keys: ``$color``, ``$year``.

    Parameters
    ----------
    labels_to_intervals : Dict[Color, Intervals]
        Color-to-intervals mapping from
        :func:`get_random_exclusive_chromatic_intervals`.
    interval_to_label : Dict[Interval, Color]
        Interval-to-color mapping from
        :func:`get_random_exclusive_chromatic_intervals`.
    seed : int
        RNG seed for the year sampling.

    Yields
    ------
    Tuple[Dict[str, str], bool]
        A ``({"color": ..., "year": ...}, answer)`` pair per query.
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
    """Yield a (query_dict, total_years) pair per color for duration queries.

    The answer is the total number of years that color held the role,
    computed as sum(end - start) over its annealed intervals. A color that
    was assigned zero intervals is skipped entirely; there is nothing to
    anneal or sum for it. A color assigned only degenerate zero-length
    intervals (start == end) is NOT skipped: it still yields a query,
    correctly answered with total=0, because it did hold the role, for an
    empty span.

    Parameters
    ----------
    label_to_intervals : Dict[Color, Intervals]
        Color-to-intervals mapping from
        :func:`get_random_exclusive_chromatic_intervals`.
    intervals_to_labels : Dict[Interval, Color]
        Unused by this generator (duration queries need only the
        color-to-intervals direction), but every ``query_gen`` in this
        module shares the same signature.
    seed : int
        Unused by this generator (duration answers need no sampling), but
        every ``query_gen`` in this module shares the same signature.

    Yields
    ------
    Tuple[Dict[str, str], int]
        A ``({"color": ...}, total_years)`` pair per color.

    Notes
    -----
    ``intervals`` here is the 2D ndarray that
    ``get_random_exclusive_chromatic_intervals`` builds
    (``intervals_arr[labels == color_idx]``), shape
    ``(num_intervals, 2)``. The "no intervals for this color" check must
    therefore be a *count* check (``len(intervals) == 0``, i.e. zero rows),
    not a truthiness/value check. ``bool(ndarray)`` is only well-defined
    when the array holds exactly one element, so ``if not intervals:``
    raises ``ValueError`` for any color holding one or more intervals (each
    row already has 2 elements). The superficially similar
    ``if not intervals.any():`` idiom, used elsewhere in this module, does
    evaluate without raising, but it checks element *values*, not interval
    *count*. It would wrongly treat a color holding a single ``(0, 0)``
    interval as having none (both elements are falsy), and would silently
    drop a duration query that should legitimately answer 0. A row-count
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
