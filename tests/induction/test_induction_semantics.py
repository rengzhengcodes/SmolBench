"""Run semantic (non-byte) regression checks for the induction generators.

tests/induction/test_golden_quizzes.py pins exact SHA-256 hashes of generated
quizzes. It is extremely sensitive (any prompt-wording or ordering change
trips it), but by construction it cannot tell a correct generation from a
wrong-but-self-consistent one. If a bug changed which answer a query
generator computes, a maintainer "fixing" the failing golden test by
re-recording the hash would silently bake the bug into the golden file
forever.

These tests instead recompute the ground-truth answer for each question
from the underlying rule (harmonic divisibility for periodic; the raw
interval-to-color map for chromatic) and check it against what the
generator actually produced. So a drift in the answer-computation logic
fails here regardless of what the golden hashes say. Configs are kept
small (sequence lengths and interval counts well under a few dozen), so
the whole module runs in well under a second.
"""

import re
import string
from math import lcm, prod

import pytest

from conftest import StubTokenizer

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
    """An intensional periodic quiz's ToF answers must equal ``pos % period == 0``.

    This is recomputed here directly from the harmonic definition
    (generate_sequence's period-to-label mapping), independent of
    tof_membership_query_gen's own internal computation of the same fact.
    Position and label are recovered by parsing them back out of the
    rendered prompt, instead of re-calling the query generator, so this
    check exercises the full get_periodic_quiz pipeline, not just the
    generator function in isolation.
    """
    # Explicit, distinct, easily-regex-matched labels (no auto-random
    # labels), so period-to-label is known upfront and unambiguous to
    # parse back out.
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=7)
    period_to_label, _pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    template = string.Template(
        "$positive_info\nDoes position $pos include '$label'? True/False."
    )
    intens_quiz, extens_quiz, noise_intens_quiz = get_periodic_quiz(
        cfg, Prompter(template, {}, tof_membership_query_gen), tokenizer=StubTokenizer()
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

    # The extensional and noise-padded-intensional quizzes render the same
    # context under different framings, but must carry identical answers
    # in identical order (get_periodic_prompts yields one shared `answer`
    # per query, reused for all three renderings). This is a cheap
    # structural check that the three-way parity documented in
    # get_periodic_prompts holds.
    assert [q.answer for q in extens_quiz] == [q.answer for q in intens_quiz]
    assert [q.answer for q in noise_intens_quiz] == [q.answer for q in intens_quiz]


# ---------------------------------------------------------------------------
# Periodic: count answers must match an independently-counted occurrence tally
# ---------------------------------------------------------------------------


def test_periodic_numeric_answers_match_independent_count():
    """Every Numeric answer must equal a brute-force count of divisible positions.

    The intensional periodic quiz's Numeric answer for each label must equal a
    brute-force count of positions 1..seq_len divisible by that label's period.
    This is computed here with a plain range/sum, not with the ``seq_len
    // period`` floor-division formula numeric_count_query_gen itself
    uses. The two are mathematically equal only because every period
    divides seq_len exactly (seq_len = lcm(1..n)). Because this counts instead of
    dividing, an off-by-one or wrong-formula regression in the source would be caught,
    even though the formula currently agrees with the brute-force tally.
    """
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=11)
    period_to_label, _pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    template = string.Template(
        "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
    )
    intens_quiz, _extens_quiz, _noise_quiz = get_periodic_numeric_quiz(
        cfg, Prompter(template, {}, numeric_count_query_gen), tokenizer=StubTokenizer()
    )
    # numeric_count_query_gen yields exactly one query per harmonic. Unlike
    # tof_membership_query_gen, it does not sample or exclude; n=4 -> 4 queries.
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
# Periodic: the explicit coprime-period pathway
# ---------------------------------------------------------------------------


def test_coprime_periods_make_sequence_length_the_product():
    """A pairwise-coprime period set must give seq_len == prod(periods).

    The count answers must still be exact, too. This is the entire premise of the
    coprime pathway. The default 1..n pathway's length is lcm(1..n), a step function
    nobody can dial: n=10 leaves it at 2520, n=11 multiplies it by a fresh prime.
    Coprimality collapses lcm to the product, so a caller picks the length. If that
    identity ever silently broke, for example a period set slipping through validation
    with a shared factor, lengths would come out shorter than requested, and every
    answer would still look self-consistent. So this checks lcm == prod explicitly,
    instead of trusting the constructor.

    Counts are recomputed by brute-force tally over the generated
    sequence, not by ``seq_len // period``, for the reason given in
    test_periodic_numeric_answers_match_independent_count: the two agree
    only because each period divides seq_len exactly, precisely the
    property under test here.
    """
    periods = (1, 2, 3, 7, 11, 13)
    labels = ["a", "bb", "ccc", "dddd", "eeeee", "ffffff"]
    cfg = PeriodicConfig(n=6, labels=labels, seed=13, periods=periods)

    period_to_label, pos_to_compound = generate_sequence(cfg)
    assert set(period_to_label) == set(periods)
    # The identity that makes the length dial-able, asserted both ways.
    assert lcm(*periods) == prod(periods)
    assert max(pos_to_compound) == prod(periods)

    # Labels attach to periods in ascending period order, so labels[i]
    # belongs to the i-th smallest period. Even if the set is passed unsorted, the
    # mapping must not change.
    shuffled = PeriodicConfig(n=6, labels=labels, seed=13, periods=(13, 1, 7, 2, 11, 3))
    assert generate_sequence(shuffled)[0] == period_to_label

    label_to_period = {label: period for period, label in period_to_label.items()}
    template = string.Template(
        "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
    )
    intens_quiz, _extens_quiz, _noise_quiz = get_periodic_numeric_quiz(
        cfg, Prompter(template, {}, numeric_count_query_gen), tokenizer=StubTokenizer()
    )
    assert len(intens_quiz) == cfg.n

    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        assert match is not None, f"prompt didn't match the expected shape: {qna.prompt!r}"
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        assert qna.answer == sum(1 for pos in range(1, seq_len + 1) if pos % period == 0)


def test_non_coprime_periods_are_rejected():
    """Period sets sharing a factor must raise, not silently shorten.

    ``(1, 2, 4, ...)`` has lcm 4 where the product is 8, so accepting it
    would hand back a sequence half the requested length, while every
    downstream answer stayed internally consistent. That is a
    config-level bug that no answer-checking test could detect. The only cheap place
    to catch it is at construction, by rejecting there.
    """
    for bad, shared in (((1, 2, 4, 5), 2), ((1, 3, 5, 9), 3), ((2, 3, 5, 10), 2)):
        with pytest.raises(ValueError, match="pairwise coprime"):
            PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=3, periods=bad)

    # Shape errors stay distinct from the coprimality error.
    with pytest.raises(ValueError, match="must equal n"):
        PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=3, periods=(1, 2, 3))
    with pytest.raises(ValueError, match="distinct"):
        PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=3, periods=(1, 3, 3, 5))


def test_divisor_periods_add_harmonics_without_moving_sequence_length():
    """A non-coprime divisor set must leave seq_len exactly where it was.

    It does this while adding harmonics: that is the dual of coprime mode, and the whole
    point of it. Coprime mode lengthens the extensional listing; this lengthens the
    intensional rule list instead. It works because a period d contributes only
    seq_len/d occurrences to the listing, so large divisors add rules and questions
    almost for free. If lcm ever drifted off the declared length, the listing would
    silently resize, and the manipulation would no longer be "intensional length holding
    extensional fixed." That is why expect_seq_len is checked, not inferred.
    """
    base = tuple(range(1, 10))              # lcm(1..9) == 2520
    added = (2520, 1260, 840, 630, 504)     # the largest proper divisors
    periods = base + added
    cfg = PeriodicConfig(
        n=len(periods), labels=len(periods), seed=17,
        periods=periods, expect_seq_len=2520,
    )
    period_to_label, pos_to_compound = generate_sequence(cfg)

    # The invariant under test: more harmonics, identical sequence length.
    assert len(period_to_label) == 14 > len(base)
    assert max(pos_to_compound) == 2520 == lcm(*base)

    # Every added period divides the length, so counts stay exact, and the
    # large ones are deliberately rare in the listing (2520 fires once).
    for d in added:
        occurrences = sum(1 for comp in pos_to_compound.values()
                          if period_to_label[d] in comp.split("|"))
        assert occurrences == 2520 // d
    assert sum(1 for c in pos_to_compound.values()
               if period_to_label[2520] in c.split("|")) == 1

    # A quiz over this config asks one question per harmonic, so the rule
    # list and the question count both grow while the listing does not.
    template = string.Template(
        "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
    )
    intens_quiz, _extens, _noise = get_periodic_numeric_quiz(
        cfg, Prompter(template, {}, numeric_count_query_gen), tokenizer=StubTokenizer()
    )
    assert len(intens_quiz) == len(periods)
    label_to_period = {lab: p for p, lab in period_to_label.items()}
    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        assert qna.answer == sum(1 for pos in range(1, seq_len + 1) if pos % period == 0)


def test_divisor_mode_rejects_periods_that_move_the_length():
    """A period that does not divide the declared length must raise.

    If 11 slips in alongside 1..9, lcm multiplies to 27,720, an eleven-fold longer
    extensional listing. The quiz would still be internally consistent, so the only
    symptom would be a study silently comparing against the wrong baseline.
    expect_seq_len turns that into a crash.
    """
    periods = tuple(range(1, 10)) + (11,)
    with pytest.raises(ValueError, match="lcm\\(periods\\) is 27720"):
        PeriodicConfig(n=len(periods), labels=len(periods), seed=17,
                       periods=periods, expect_seq_len=2520)

    # Under-reaching the declared length is caught by the same assertion.
    with pytest.raises(ValueError, match="not the declared expect_seq_len"):
        PeriodicConfig(n=3, labels=3, seed=17, periods=(1, 2, 4), expect_seq_len=2520)

    # And the field is meaningless without an explicit period set.
    with pytest.raises(ValueError, match="only means something alongside"):
        PeriodicConfig(n=4, labels=4, seed=17, expect_seq_len=60)


def test_coprime_mode_still_requires_coprimality_when_length_undeclared():
    """If expect_seq_len is omitted, the strict coprime contract still applies.

    The two modes share one field, so this pins the discriminator: no
    declared length means coprime mode, and a shared factor is still an
    error there, not waved through by the divisor branch.
    """
    with pytest.raises(ValueError, match="pairwise coprime"):
        PeriodicConfig(n=4, labels=4, seed=17, periods=(1, 2, 4, 5))
    # The error names the escape hatch, so the divisor pathway is findable.
    with pytest.raises(ValueError, match="expect_seq_len"):
        PeriodicConfig(n=4, labels=4, seed=17, periods=(1, 2, 4, 5))


def test_default_pathway_is_untouched_by_the_periods_field():
    """If ``periods`` is omitted, the consecutive-integer behavior stays unchanged.

    It stays exactly as it was: the coprime pathway is additive, not a replacement.

    tests/induction/test_golden_quizzes.py pins the generated bytes at the
    notebooks' production config, so this test only needs to check the
    structural fact that the field defaults to None and still yields
    periods 1..n. Together they cover the guarantee that already-collected
    replicates remain comparable with anything generated after this
    change.
    """
    cfg = PeriodicConfig(n=5, labels=["a", "bb", "ccc", "dddd", "eeeee"], seed=5)
    assert cfg.periods is None
    period_to_label, pos_to_compound = generate_sequence(cfg)
    assert sorted(period_to_label) == [1, 2, 3, 4, 5]
    assert max(pos_to_compound) == lcm(1, 2, 3, 4, 5) == 60


# ---------------------------------------------------------------------------
# Chromatic: succession True/False answers must match the interval tiling
# ---------------------------------------------------------------------------


def test_chromatic_succession_answers_match_interval_map():
    """succession_query_gen's True answers must correspond to consecutive color pairs.

    Specifically, these are pairs that are actually consecutive in the interval tiling.
    "Consecutive" means one color's interval immediately followed by
    another's, chronologically. Its False answers must never be one of
    those pairs.

    Ground truth (``true_pairs``) is rebuilt directly from
    ``intervals_to_labels``, the raw interval->color map returned by
    ``get_random_exclusive_chromatic_intervals``, independent of
    succession_query_gen's own internal ``true_pairs`` bookkeeping. So a
    self-consistent bug in that bookkeeping (for example an off-by-one in
    the ``zip(sorted_intervals, sorted_intervals[1:])`` pairing) would
    still be caught here.
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
        # every False answer must not be one (catches false negatives,
        # that is, "a known-False pair isn't [a successor pair]").
        assert answer == (pair in true_pairs)
        seen_true += bool(answer)
        seen_false += not answer
    # Both polarities must actually be exercised, or the equality check
    # above would trivially pass over an empty or one-sided generator.
    assert seen_true > 0
    assert seen_false > 0


# ---------------------------------------------------------------------------
# Chromatic: duration totals, including the n=40 config that regresses the
# pre-fix ndarray-truthiness crash in duration_query_gen.
# ---------------------------------------------------------------------------


def test_chromatic_duration_query_gen_totals_and_zero_interval_color():
    """Regression test for the fixed ``if not intervals:`` ndarray-truthiness bug.

    (Documented in duration_query_gen's docstring, chromatic.py.) Calling
    ``bool()`` on a multi-row ndarray raises, so the old code crashed for
    any color holding more than one interval. n=40/intervals=8/colors=4/
    seed=1776 is a known configuration (chosen by the architect for this
    test) that simultaneously produces:

    - a color with zero intervals (must be skipped, no query at all, not
      a query answered 0), exercising the ``len(intervals) == 0`` branch;
    - colors with multiple intervals, some of which anneal together
      (consecutive or overlapping intervals merged into one span) and
      some of which stay separate, exercising the annealing branch that
      the old ``if not intervals:`` code could never even reach without
      crashing.

    Each yielded total is checked against an independently-computed sum of annealed
    interval lengths (calling anneal_intervals directly here, instead of trusting
    duration_query_gen's own internal total). The zero-interval color is confirmed to
    be silently absent from the results, not present with total=0.
    """
    cfg = ChromaticIntervalsConfig(n=40, intervals=8, colors=4, seed=1776)
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(cfg)

    interval_counts = [len(intervals) for intervals in label_to_intervals.values()]
    # These checks document (and pin) the fixture's shape. If a future
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

    # This is the crash regression itself. The old `if not intervals:` code
    # raised ValueError ("truth value of an array with more than one
    # element is ambiguous") the moment it reached a multi-interval color.
    # So simply exhausting the generator without an exception is already
    # a meaningful check.
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
