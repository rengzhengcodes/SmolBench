"""Semantic (non-byte) regression checks for the induction generators.

Answers are recomputed from the underlying rule, so a wrong-but-self-consistent
generation fails here even when tests/induction/test_golden_quizzes.py agrees.
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

NUM_TMPL = string.Template("$positive_info\nHow many of positions 1..$seq_len include '$label'?")
TOF_TMPL = string.Template("$positive_info\nDoes position $pos include '$label'? True/False.")


def _check_counts(cfg):
    """Assert every Numeric answer equals a brute-force divisible-position tally."""
    period_to_label, pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}
    intens_quiz, _extens, _noise = get_periodic_numeric_quiz(
        cfg, Prompter(NUM_TMPL, {}, numeric_count_query_gen), tokenizer=StubTokenizer()
    )
    assert len(intens_quiz) == cfg.n
    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        assert qna.answer == sum(1 for pos in range(1, seq_len + 1) if pos % period == 0)
    return period_to_label, pos_to_compound


def test_periodic_tof_answers_match_divisibility_rule():
    """ToF answers must equal ``pos % period == 0``, identically across all three arms."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=7)
    period_to_label, _ = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    intens, extens, noise_intens = get_periodic_quiz(
        cfg, Prompter(TOF_TMPL, {}, tof_membership_query_gen), tokenizer=StubTokenizer()
    )
    assert len(intens) > 0
    for qna in intens:
        match = re.search(r"Does position (\d+) include '(\w+)'\?", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        pos, label = int(match.group(1)), match.group(2)
        assert qna.answer == (pos % label_to_period[label] == 0)

    assert [q.answer for q in extens] == [q.answer for q in intens]
    assert [q.answer for q in noise_intens] == [q.answer for q in intens]


def test_periodic_numeric_answers_and_default_pathway():
    """Default (no ``periods``) config yields periods 1..n, seq_len lcm(1..n), exact counts."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=11)
    assert cfg.periods is None
    period_to_label, pos_to_compound = _check_counts(cfg)
    assert sorted(period_to_label) == [1, 2, 3, 4]
    assert max(pos_to_compound) == lcm(1, 2, 3, 4) == 12


def test_coprime_periods_make_sequence_length_the_product():
    """A pairwise-coprime period set gives seq_len == prod(periods), order-independently."""
    periods = (1, 2, 3, 7, 11, 13)
    labels = ["a", "bb", "ccc", "dddd", "eeeee", "ffffff"]
    cfg = PeriodicConfig(n=6, labels=labels, seed=13, periods=periods)

    period_to_label, pos_to_compound = _check_counts(cfg)
    assert set(period_to_label) == set(periods)
    assert lcm(*periods) == prod(periods)
    assert max(pos_to_compound) == prod(periods)

    shuffled = PeriodicConfig(n=6, labels=labels, seed=13, periods=(13, 1, 7, 2, 11, 3))
    assert generate_sequence(shuffled)[0] == period_to_label


def test_divisor_periods_add_harmonics_without_moving_sequence_length():
    """A divisor set adds harmonics while seq_len stays at the declared length."""
    base = tuple(range(1, 10))
    added = (2520, 1260, 840, 630, 504)
    periods = base + added
    cfg = PeriodicConfig(n=len(periods), labels=len(periods), seed=17,
                         periods=periods, expect_seq_len=2520)
    period_to_label, pos_to_compound = _check_counts(cfg)

    assert len(period_to_label) == 14 > len(base)
    assert max(pos_to_compound) == 2520 == lcm(*base)
    for d in added:
        occurrences = sum(1 for comp in pos_to_compound.values()
                          if period_to_label[d] in comp.split("|"))
        assert occurrences == 2520 // d
    assert sum(1 for c in pos_to_compound.values()
               if period_to_label[2520] in c.split("|")) == 1


@pytest.mark.parametrize(
    "kwargs, match",
    [
        (dict(n=4, labels=4, periods=(1, 2, 4, 5)), "pairwise coprime"),
        (dict(n=4, labels=4, periods=(1, 2, 3)), "must equal n"),
        (dict(n=4, labels=4, periods=(1, 3, 3, 5)), "distinct"),
        (dict(n=10, labels=10, periods=tuple(range(1, 10)) + (11,), expect_seq_len=2520),
         r"lcm\(periods\) is 27720"),
        (dict(n=3, labels=3, periods=(1, 2, 4), expect_seq_len=2520),
         "not the declared expect_seq_len"),
        (dict(n=4, labels=4, expect_seq_len=60), "only means something alongside"),
    ],
)
def test_period_validation(kwargs, match):
    """Malformed period sets must raise at construction, not silently resize the sequence."""
    with pytest.raises(ValueError, match=match):
        PeriodicConfig(seed=3, **kwargs)


def test_chromatic_succession_answers_match_interval_map():
    """succession answers must equal "pair is consecutive in the interval tiling"."""
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
        assert answer == (pair in true_pairs)
        seen_true += bool(answer)
        seen_false += not answer
    assert seen_true > 0
    assert seen_false > 0


def test_chromatic_duration_query_gen_totals_and_zero_interval_color():
    """Durations equal annealed-span sums; zero-interval colors yield no query at all."""
    cfg = ChromaticIntervalsConfig(n=40, intervals=8, colors=4, seed=1776)
    label_to_intervals, intervals_to_labels = get_random_exclusive_chromatic_intervals(cfg)

    interval_counts = [len(intervals) for intervals in label_to_intervals.values()]
    assert any(count == 0 for count in interval_counts)
    assert any(count > 1 for count in interval_counts)

    queried_totals = {
        query["color"]: total
        for query, total in duration_query_gen(label_to_intervals, intervals_to_labels, cfg.seed)
    }

    for color, intervals in label_to_intervals.items():
        if len(intervals) == 0:
            assert color not in queried_totals
            continue
        annealed = tuple(anneal_intervals(intervals))
        assert queried_totals[color] == sum(end - start for start, end in annealed)
