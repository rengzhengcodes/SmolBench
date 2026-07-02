"""Semantic (non-byte) regression checks for the induction generators.

tests/test_golden_quizzes.py pins exact SHA-256 hashes of generated quizzes:
it is extremely sensitive (any prompt-wording or ordering change trips it)
but, by construction, cannot tell a CORRECT generation from a
wrong-but-self-consistent one -- if a bug changed which answer a query
generator computes, a maintainer "fixing" the failing golden test by
re-recording the hash would silently bake the bug into the golden file
forever.

These tests instead recompute the ground-truth answer for each question
from the underlying rule (harmonic divisibility for periodic; the raw
interval-to-color map for chromatic) and assert it against what the
generator actually produced, so a drift in the ANSWER-COMPUTATION logic
fails here regardless of what the golden hashes say. Configs are kept small
(sequence lengths and interval counts well under a few dozen) so the whole
module runs in well under a second.
"""

import re
import string

from smolbench.induction.chromatic import (
    ChromaticIntervalsConfig,
    anneal_intervals,
    duration_query_gen,
    get_random_exclusive_chromatic_intervals,
    succession_query_gen,
)
from smolbench.induction.periodic import (
    PeriodicConfig,
    Prompter,
    generate_sequence,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)

# ---------------------------------------------------------------------------
# Periodic: True/False membership answers must match "period divides pos"
# ---------------------------------------------------------------------------


def test_periodic_tof_answers_match_divisibility_rule():
    """Every ToF answer in an intensional periodic quiz must equal
    ``pos % period == 0``, recomputed here directly from the harmonic
    definition (generate_sequence's period-to-label mapping) -- independent
    of tof_membership_query_gen's own internal computation of the same
    fact. Position and label are recovered by parsing them back out of the
    rendered prompt (rather than re-calling the query generator), so this
    check exercises the full get_periodic_quiz pipeline, not just the
    generator function in isolation.
    """
    # Explicit, distinct, easily-regex-matched labels (no auto-random labels)
    # so period<->label is known upfront and unambiguous to parse back out.
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=7)
    period_to_label, _pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    template = string.Template(
        "$positive_info\nDoes position $pos include '$label'? True/False."
    )
    intens_quiz, extens_quiz, noise_intens_quiz = get_periodic_quiz(
        cfg, Prompter(template, {}, tof_membership_query_gen)
    )
    assert len(intens_quiz) > 0  # sanity: the generator actually yielded queries

    checked = 0
    for qna in intens_quiz:
        match = re.search(r"Does position (\d+) include '(\w+)'\?", qna.prompt)
        assert match is not None, f"prompt didn't match the expected shape: {qna.prompt!r}"
        pos, label = int(match.group(1)), match.group(2)
        expected = pos % label_to_period[label] == 0
        assert qna.answer == expected
        checked += 1
    assert checked == len(intens_quiz)

    # The extensional and noise-padded-intensional quizzes render the SAME
    # context under different framings but must carry identical answers in
    # identical order (get_periodic_prompts yields one shared `answer` per
    # query, reused for all three renderings) -- a cheap structural check
    # that the three-way parity documented in get_periodic_prompts holds.
    assert [q.answer for q in extens_quiz] == [q.answer for q in intens_quiz]
    assert [q.answer for q in noise_intens_quiz] == [q.answer for q in intens_quiz]


# ---------------------------------------------------------------------------
# Periodic: count answers must match an independently-counted occurrence tally
# ---------------------------------------------------------------------------


def test_periodic_numeric_answers_match_independent_count():
    """Every Numeric answer in an intensional periodic quiz must equal a
    brute-force COUNT of positions 1..seq_len divisible by that label's
    period -- computed here with a plain range/sum, not with the
    ``seq_len // period`` floor-division formula numeric_count_query_gen
    itself uses. The two are mathematically equal only because every period
    divides seq_len exactly (seq_len = lcm(1..n)); recomputing by counting
    instead of dividing means an off-by-one or wrong-formula regression in
    the source would be caught even though it currently agrees with the
    brute-force tally.
    """
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=11)
    period_to_label, _pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    template = string.Template(
        "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
    )
    intens_quiz, _extens_quiz, _noise_quiz = get_periodic_numeric_quiz(
        cfg, Prompter(template, {}, numeric_count_query_gen)
    )
    # numeric_count_query_gen yields exactly one query per harmonic (unlike
    # tof_membership_query_gen, it does not sample/exclude); n=4 -> 4 queries.
    assert len(intens_quiz) == cfg.n

    checked = 0
    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        assert match is not None, f"prompt didn't match the expected shape: {qna.prompt!r}"
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        expected = sum(1 for pos in range(1, seq_len + 1) if pos % period == 0)
        assert qna.answer == expected
        checked += 1
    assert checked == cfg.n


# ---------------------------------------------------------------------------
# Chromatic: succession True/False answers must match the interval tiling
# ---------------------------------------------------------------------------


def test_chromatic_succession_answers_match_interval_map():
    """succession_query_gen's True answers must correspond exactly to
    color pairs that are actually consecutive in the interval tiling (one
    color's interval immediately followed by another's, chronologically);
    its False answers must never be one of those pairs.

    Ground truth (``true_pairs``) is rebuilt directly from
    ``intervals_to_labels`` -- the raw interval->color map returned by
    ``get_random_exclusive_chromatic_intervals`` -- independent of
    succession_query_gen's own internal ``true_pairs`` bookkeeping, so a
    self-consistent bug in that bookkeeping (e.g. an off-by-one in the
    ``zip(sorted_intervals, sorted_intervals[1:])`` pairing) would still be
    caught here.
    """
    cfg = ChromaticIntervalsConfig(n=20, intervals=6, colors=4, seed=99)
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(cfg)

    sorted_intervals = sorted(intervals_to_labels.items(), key=lambda item: item[0][0])
    true_pairs = {
        (color1, color2)
        for (_interval1, color1), (_interval2, color2)
        in zip(sorted_intervals, sorted_intervals[1:])
    }

    seen_true = seen_false = 0
    for query, answer in succession_query_gen(label_to_intervals, intervals_to_labels, cfg.seed):
        pair = (query["color1"], query["color2"])
        # A single equality check covers both directions: every True answer
        # must be an actual successor pair (catches false positives), and
        # every False answer must NOT be one (catches false negatives --
        # i.e. "a known-False pair isn't [a successor pair]").
        assert answer == (pair in true_pairs)
        seen_true += bool(answer)
        seen_false += not answer
    # Both polarities must actually be exercised, or the equality check
    # above would trivially pass over an empty/one-sided generator.
    assert seen_true > 0
    assert seen_false > 0


# ---------------------------------------------------------------------------
# Chromatic: duration totals, including the n=40 config that regresses the
# pre-fix ndarray-truthiness crash in duration_query_gen.
# ---------------------------------------------------------------------------


def test_chromatic_duration_query_gen_totals_and_zero_interval_color():
    """Regression test for the fixed ``if not intervals:`` ndarray-truthiness
    bug documented in duration_query_gen's docstring (chromatic.py): calling
    ``bool()`` on a multi-row ndarray raises, so the OLD code crashed for
    any color holding more than one interval. n=40/intervals=8/colors=4/
    seed=1776 is a known configuration (chosen by the architect for this
    test) that simultaneously produces:

    - a color with ZERO intervals (must be skipped -- no query at all,
      not a query answered 0), exercising the ``len(intervals) == 0``
      branch;
    - colors with MULTIPLE intervals, some of which anneal together
      (consecutive/overlapping intervals merged into one span) and some of
      which stay separate, exercising the annealing branch that the old
      ``if not intervals:`` code could never even reach without crashing.

    Each yielded total is checked against an independently-computed sum of
    annealed interval lengths (calling anneal_intervals directly here,
    rather than trusting duration_query_gen's own internal total), and the
    zero-interval color is confirmed to be silently absent from the
    results rather than present with total=0.
    """
    cfg = ChromaticIntervalsConfig(n=40, intervals=8, colors=4, seed=1776)
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(cfg)

    interval_counts = [len(intervals) for intervals in label_to_intervals.values()]
    # These assertions document (and pin) the fixture's shape: if a future
    # numpy/RNG change made this config stop covering the zero-interval or
    # multi-interval-with-annealing cases, the test would otherwise keep
    # passing while silently testing much less than intended.
    assert any(count == 0 for count in interval_counts), (
        "expected config n=40/intervals=8/colors=4/seed=1776 to include a "
        "zero-interval color; RNG behavior may have changed"
    )
    assert any(count > 1 for count in interval_counts), (
        "expected config n=40/intervals=8/colors=4/seed=1776 to include a "
        "multi-interval color; RNG behavior may have changed"
    )

    # This is the crash regression itself: the old `if not intervals:` code
    # raised ValueError ("truth value of an array with more than one
    # element is ambiguous") the moment it reached a multi-interval color,
    # so simply exhausting the generator without an exception is already a
    # meaningful assertion.
    queried_totals = {
        query["color"]: total
        for query, total in duration_query_gen(label_to_intervals, intervals_to_labels, cfg.seed)
    }

    for color, intervals in label_to_intervals.items():
        if len(intervals) == 0:
            assert color not in queried_totals  # zero-interval colors yield no query
            continue
        annealed = tuple(anneal_intervals(intervals))
        expected_total = sum(end - start for start, end in annealed)
        assert queried_totals[color] == expected_total
