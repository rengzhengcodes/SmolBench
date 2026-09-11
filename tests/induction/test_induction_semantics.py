"""Semantic regression checks for induction generators.

Recomputed answers catch wrong but self-consistent generation.
"""

import re
import string
from math import lcm, prod
from typing import Any

import pytest
from conftest import StubTokenizer
from tests.induction._periodic import POSITIVE_ARMS

from smolbench.induction._common import Prompter
from smolbench.induction.periodic import (
    CONDITIONS,
    PeriodicConfig,
    generate_sequence,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)

NUM_TMPL = string.Template(
    "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
)
TOF_TMPL = string.Template(
    "$positive_info\nDoes position $pos include '$label'? True/False."
)


def _check_counts(cfg: PeriodicConfig) -> tuple[dict[int, str], dict[int, str]]:
    """Check numeric answers against divisible-position tallies."""
    period_to_label, pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}
    quizzes = get_periodic_numeric_quiz(
        cfg,
        Prompter(NUM_TMPL, numeric_count_query_gen),
        tokenizer=StubTokenizer(),
        conditions=POSITIVE_ARMS,
    )
    intens_quiz = quizzes["intens"]
    assert len(intens_quiz) == cfg.n
    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        assert qna.answer == sum(
            1 for pos in range(1, seq_len + 1) if pos % period == 0
        )
    return period_to_label, pos_to_compound


def test_periodic_tof_answers_match_divisibility_rule() -> None:
    """ToF answers must equal ``pos % period == 0``, identically across all three arms."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=7)
    period_to_label, _ = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    quizzes = get_periodic_quiz(
        cfg,
        Prompter(TOF_TMPL, tof_membership_query_gen),
        tokenizer=StubTokenizer(),
        conditions=POSITIVE_ARMS,
    )
    intens, extens, noise_intens = (
        quizzes["intens"],
        quizzes["extens"],
        quizzes["noise_intens"],
    )
    assert len(intens) > 0
    for qna in intens:
        match = re.search(r"Does position (\d+) include '(\w+)'\?", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        pos, label = int(match.group(1)), match.group(2)
        assert qna.answer == (pos % label_to_period[label] == 0)

    assert [q.answer for q in extens] == [q.answer for q in intens]
    assert [q.answer for q in noise_intens] == [q.answer for q in intens]


def test_periodic_numeric_answers_and_default_pathway() -> None:
    """Default periods yield exact counts and their LCM sequence length."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=11)
    assert cfg.periods is None
    period_to_label, pos_to_compound = _check_counts(cfg)
    assert sorted(period_to_label) == [1, 2, 3, 4]
    assert max(pos_to_compound) == lcm(1, 2, 3, 4) == 12


def test_coprime_periods_make_sequence_length_the_product() -> None:
    """Coprime periods yield their product, independent of order."""
    periods = (1, 2, 3, 7, 11, 13)
    labels = ["a", "bb", "ccc", "dddd", "eeeee", "ffffff"]
    cfg = PeriodicConfig(n=6, labels=labels, seed=13, periods=periods)

    period_to_label, pos_to_compound = _check_counts(cfg)
    assert set(period_to_label) == set(periods)
    assert lcm(*periods) == prod(periods)
    assert max(pos_to_compound) == prod(periods)

    shuffled = PeriodicConfig(n=6, labels=labels, seed=13, periods=(13, 1, 7, 2, 11, 3))
    assert generate_sequence(shuffled)[0] == period_to_label


def test_divisor_periods_add_harmonics_without_moving_sequence_length() -> None:
    """Divisor harmonics preserve the declared sequence length."""
    base = tuple(range(1, 10))
    # Divisors preserve the base sequence length.
    added = (2520, 1260, 840, 630, 504)
    periods = base + added
    cfg = PeriodicConfig(
        n=len(periods),
        labels=len(periods),
        seed=17,
        periods=periods,
        expect_seq_len=2520,
    )
    period_to_label, pos_to_compound = _check_counts(cfg)

    assert len(period_to_label) == 14 > len(base)  # 9 base + 5 added labels
    assert max(pos_to_compound) == 2520 == lcm(*base)
    for d in added:
        occurrences = sum(
            1
            for comp in pos_to_compound.values()
            if period_to_label[d] in comp.split("|")
        )
        assert occurrences == 2520 // d
    assert (
        sum(
            1 for c in pos_to_compound.values() if period_to_label[2520] in c.split("|")
        )
        == 1
    )


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"n": 4, "labels": 4, "periods": (1, 2, 4, 5)}, "pairwise coprime"),
        ({"n": 4, "labels": 4, "periods": (1, 2, 3)}, "must equal n"),
        ({"n": 4, "labels": 4, "periods": (1, 3, 3, 5)}, "distinct"),
        # Extra 11 changes the LCM.
        (
            {
                "n": 10,
                "labels": 10,
                "periods": tuple(range(1, 10)) + (11,),
                "expect_seq_len": 2520,
            },
            r"lcm\(periods\) is 27720",
        ),
        (
            {"n": 3, "labels": 3, "periods": (1, 2, 4), "expect_seq_len": 2520},
            "not the declared expect_seq_len",
        ),
        ({"n": 4, "labels": 4, "expect_seq_len": 60}, "only means something alongside"),
    ],
)
def test_period_validation(kwargs: dict[str, Any], match: str) -> None:
    """Malformed period sets fail before they can resize a sequence."""
    with pytest.raises(ValueError, match=match):
        PeriodicConfig(seed=3, **kwargs)


def test_labels_must_be_distinct() -> None:
    """Reject duplicate labels with contradictory ground truths."""
    with pytest.raises(ValueError, match="distinct"):
        PeriodicConfig(n=3, labels=("dup", "dup", "zzz"), seed=1)


#: Range-free counterpart required by the zero condition.
NUM_TMPL_RANGE_FREE = string.Template(
    "$positive_info\nHow many positions include '$label'?"
)


def numeric_prompter(**kwargs: Any) -> Prompter:
    """Build a numeric prompter with the supplied template options."""
    return Prompter(NUM_TMPL, numeric_count_query_gen, **kwargs)


CFG4 = PeriodicConfig(n=4, labels=4, seed=3)


def _quizzes(
    cfg: PeriodicConfig = CFG4, prompter: Prompter | None = None, **kwargs: Any
) -> dict:
    """Render with the range-free numeric prompter unless one is passed."""
    return get_periodic_numeric_quiz(
        cfg,
        prompter or numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
        tokenizer=StubTokenizer(),
        **kwargs,
    )


def test_the_quiz_is_keyed_by_condition_in_mapping_order() -> None:
    """Quiz mappings retain condition names and order."""
    quizzes = _quizzes()
    assert (
        list(quizzes)
        == list(CONDITIONS)
        == ["intens", "extens", "noise_intens", "zero"]
    )
    assert {len(q) for q in quizzes.values()} == {4}


def test_a_single_condition_mapping_renders_exactly_that_arm() -> None:
    """A one-entry mapping verifies that ``conditions`` controls rendering."""
    quizzes = _quizzes(
        prompter=numeric_prompter(), conditions={"intens": CONDITIONS["intens"]}
    )
    assert list(quizzes) == ["intens"]


def test_the_zero_arm_states_no_range_and_leaks_no_answer() -> None:
    """The zero arm must not leak answers through its range."""
    cfg = PeriodicConfig(n=6, labels=6, seed=5)
    _p2l, p2c = generate_sequence(cfg)
    seq_len = max(p2c)
    quizzes = _quizzes(cfg)
    zero = quizzes["zero"]
    assert len(zero) == len(quizzes["intens"]) == 6
    for question in zero:
        integers = [int(tok) for tok in re.findall(r"\d+", question.prompt)]
        assert seq_len not in integers, question.prompt
        assert question.answer not in integers, question.prompt
    # Only context and range clause differ from informative arms.
    assert [q.answer for q in zero] == [q.answer for q in quizzes["intens"]]
    # Ensures the leak check is meaningful.
    assert seq_len in [q.answer for q in zero]


def test_a_single_digit_range_does_not_refuse_a_range_free_template() -> None:
    """Ordinary numbering prose sharing digits with a tiny range is not a leak."""
    counting = string.Template(
        "$positive_info\nPositions are counted starting from 1. "
        "How many positions include '$label'?"
    )
    quizzes = _quizzes(
        PeriodicConfig(n=1, labels=1, seed=3),
        numeric_prompter(range_free_template=counting),
        # n=1 leaves the extensional arm too short to pad against.
        conditions={"zero": CONDITIONS["zero"]},
    )
    assert all("counted starting from 1" in q.prompt for q in quizzes["zero"])


def test_a_range_free_template_that_still_states_the_range_is_refused() -> None:
    """Reject range text surviving in a supposedly range-free prompt."""
    leaky = string.Template(
        "$positive_info\nHow many of positions 1..$seq_len include '$label'?"
    )
    with pytest.raises(ValueError) as exc:
        _quizzes(prompter=numeric_prompter(range_free_template=leaky))
    assert "seq_len" in str(exc.value)


def test_an_omit_range_condition_without_its_template_is_refused() -> None:
    """Reject a missing range-free template to prevent answer leaks."""
    with pytest.raises(ValueError) as exc:
        _quizzes(prompter=numeric_prompter())
    assert "range_free_template" in str(exc.value)


@pytest.mark.parametrize(
    "target, match",
    [
        ("nope", "nope"),  # names a condition that is not in the mapping
        ("noise_intens", "noise_intens"),  # names a condition that is itself padded
    ],
)
def test_a_bad_token_target_is_refused(target: str, match: str) -> None:
    """Token targets must exist and cannot be padded themselves."""
    from smolbench.induction.periodic import Condition

    conditions = dict(CONDITIONS)
    conditions["noise_intens"] = Condition(
        context=CONDITIONS["noise_intens"].context, match_tokens_to=target
    )
    with pytest.raises(ValueError) as exc:
        _quizzes(conditions=conditions)
    assert match in str(exc.value)


def test_rendered_queries_carry_the_token_count_of_every_arm() -> None:
    """Rendered prompts retain token counts for completion budgeting."""
    from smolbench.induction.periodic import get_periodic_prompts

    tokenizer = StubTokenizer()
    rendered = list(
        get_periodic_prompts(
            PeriodicConfig(n=4, labels=4, seed=3),
            numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
            tokenizer=tokenizer,
        )
    )
    assert len(rendered) == 4
    for query in rendered:
        assert set(query.prompts) == set(query.token_counts) == set(CONDITIONS)
        for arm, prompt in query.prompts.items():
            assert query.token_counts[arm] == tokenizer.count(prompt), arm
        # Noise is a length control.
        assert query.token_counts["noise_intens"] == query.token_counts["extens"]
