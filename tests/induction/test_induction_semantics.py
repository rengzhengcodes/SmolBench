"""Semantic (non-byte) regression checks for the induction generators.

Answers are recomputed from the underlying rule, so a wrong-but-self-consistent
generation fails here even when tests/induction/test_golden_quizzes.py agrees.
"""

import re
import string
from math import lcm, prod
from typing import Any

import pytest

from conftest import StubTokenizer

from smolbench.induction.periodic import (
    CONDITIONS,
    PeriodicConfig,
    Prompter,
    generate_sequence,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)

#: Conditions whose question text states the position range. Zero is excluded:
#: it needs a range-free template (`Prompter.range_free_template`) these
#: minimal test templates don't supply; passing this subset also pins that
#: `conditions` is a real parameter.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}

NUM_TMPL = string.Template("$positive_info\nHow many of positions 1..$seq_len include '$label'?")
TOF_TMPL = string.Template("$positive_info\nDoes position $pos include '$label'? True/False.")


def _check_counts(cfg: PeriodicConfig) -> tuple[dict[int, str], dict[int, str]]:
    """Assert every Numeric answer equals a brute-force divisible-position tally."""
    period_to_label, pos_to_compound = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}
    quizzes = get_periodic_numeric_quiz(
        cfg, Prompter(NUM_TMPL, numeric_count_query_gen), tokenizer=StubTokenizer(),
        conditions=POSITIVE_ARMS,
    )
    intens_quiz = quizzes["intens"]
    assert len(intens_quiz) == cfg.n
    for qna in intens_quiz:
        match = re.search(r"positions 1\.\.(\d+) include '(\w+)'", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        seq_len, label = int(match.group(1)), match.group(2)
        period = label_to_period[label]
        assert qna.answer == sum(1 for pos in range(1, seq_len + 1) if pos % period == 0)
    return period_to_label, pos_to_compound


def test_periodic_tof_answers_match_divisibility_rule() -> None:
    """ToF answers must equal ``pos % period == 0``, identically across all three arms."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=7)
    period_to_label, _ = generate_sequence(cfg)
    label_to_period = {label: period for period, label in period_to_label.items()}

    quizzes = get_periodic_quiz(
        cfg, Prompter(TOF_TMPL, tof_membership_query_gen), tokenizer=StubTokenizer(),
        conditions=POSITIVE_ARMS,
    )
    intens, extens, noise_intens = (
        quizzes["intens"], quizzes["extens"], quizzes["noise_intens"])
    assert len(intens) > 0
    for qna in intens:
        match = re.search(r"Does position (\d+) include '(\w+)'\?", qna.prompt)
        assert match is not None, f"unexpected prompt shape: {qna.prompt!r}"
        pos, label = int(match.group(1)), match.group(2)
        assert qna.answer == (pos % label_to_period[label] == 0)

    assert [q.answer for q in extens] == [q.answer for q in intens]
    assert [q.answer for q in noise_intens] == [q.answer for q in intens]


def test_periodic_numeric_answers_and_default_pathway() -> None:
    """Default (no ``periods``) config yields periods 1..n, seq_len lcm(1..n), exact counts."""
    cfg = PeriodicConfig(n=4, labels=["a", "bb", "ccc", "dddd"], seed=11)
    assert cfg.periods is None
    period_to_label, pos_to_compound = _check_counts(cfg)
    assert sorted(period_to_label) == [1, 2, 3, 4]
    assert max(pos_to_compound) == lcm(1, 2, 3, 4) == 12


def test_coprime_periods_make_sequence_length_the_product() -> None:
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


def test_divisor_periods_add_harmonics_without_moving_sequence_length() -> None:
    """A divisor set adds harmonics while seq_len stays at the declared length."""
    base = tuple(range(1, 10))
    # 2520 = lcm(1..9) = the base sequence length; the rest are its divisors
    # (2520/2, /3, /4, /5), so each added harmonic fits the length exactly.
    added = (2520, 1260, 840, 630, 504)
    periods = base + added
    cfg = PeriodicConfig(n=len(periods), labels=len(periods), seed=17,
                         periods=periods, expect_seq_len=2520)
    period_to_label, pos_to_compound = _check_counts(cfg)

    assert len(period_to_label) == 14 > len(base)  # 9 base + 5 added labels
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
        # lcm(1..9) = 2520, and the extra 11 multiplies it to 27720 != 2520.
        (dict(n=10, labels=10, periods=tuple(range(1, 10)) + (11,), expect_seq_len=2520),
         r"lcm\(periods\) is 27720"),
        (dict(n=3, labels=3, periods=(1, 2, 4), expect_seq_len=2520),
         "not the declared expect_seq_len"),
        (dict(n=4, labels=4, expect_seq_len=60), "only means something alongside"),
    ],
)
def test_period_validation(kwargs: dict[str, Any], match: str) -> None:
    """Malformed period sets must raise at construction, not silently resize the sequence."""
    with pytest.raises(ValueError, match=match):
        PeriodicConfig(seed=3, **kwargs)


def test_labels_must_be_distinct() -> None:
    """A duplicate explicit label is rejected at construction: two rules for one
    string would give a single prompt two contradictory ground truths."""
    with pytest.raises(ValueError, match="distinct"):
        PeriodicConfig(n=3, labels=("dup", "dup", "zzz"), seed=1)


# ---------------------------------------------------------------------------
# The condition mapping, and the zero arm's range-free rendering
# ---------------------------------------------------------------------------

#: A minimal range-free counterpart of `NUM_TMPL`: the same question with the
#: "1..$seq_len" range clause removed, which is what the zero condition needs.
NUM_TMPL_RANGE_FREE = string.Template("$positive_info\nHow many positions include '$label'?")


def numeric_prompter(**kwargs: Any) -> Prompter:
    return Prompter(NUM_TMPL, numeric_count_query_gen, **kwargs)


def test_the_quiz_is_keyed_by_condition_in_mapping_order() -> None:
    """`get_periodic_numeric_quiz` returns a dict keyed by condition name in the
    mapping's order, not a positional 3-tuple with a fourth arm bolted on."""
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=4, labels=4, seed=3),
        numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
        tokenizer=StubTokenizer(),
    )
    assert list(quizzes) == list(CONDITIONS) == [
        "intens", "extens", "noise_intens", "zero"]
    assert {len(q) for q in quizzes.values()} == {4}


def test_a_single_condition_mapping_renders_exactly_that_arm() -> None:
    """`conditions` is a real parameter: a one-entry mapping is a shape the
    render loop can't produce by ignoring it."""
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=4, labels=4, seed=3), numeric_prompter(),
        tokenizer=StubTokenizer(), conditions={"intens": CONDITIONS["intens"]},
    )
    assert list(quizzes) == ["intens"]


def test_the_zero_arm_states_no_range_and_leaks_no_answer() -> None:
    """The zero arm must not print any answer in its prompt: the period-1
    harmonic's answer is seq_len, so a range-stating question would leak it and
    inflate the information-gap floor by the resulting free hit (11.1 pp)."""
    cfg = PeriodicConfig(n=6, labels=6, seed=5)
    _p2l, p2c = generate_sequence(cfg)
    seq_len = max(p2c)
    quizzes = get_periodic_numeric_quiz(
        cfg, numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
        tokenizer=StubTokenizer(),
    )
    zero = quizzes["zero"]
    assert len(zero) == len(quizzes["intens"]) == 6
    for question in zero:
        integers = [int(tok) for tok in re.findall(r"\d+", question.prompt)]
        assert seq_len not in integers, question.prompt
        assert question.answer not in integers, question.prompt
    # Same questions and answers as the informative arms: only the context
    # (and the range clause) differ.
    assert [q.answer for q in zero] == [q.answer for q in quizzes["intens"]]
    # Confirms seq_len is a real possible answer, so the checks above aren't vacuous.
    assert seq_len in [q.answer for q in zero]


def test_a_range_free_template_that_still_states_the_range_is_refused() -> None:
    """The leak gate checks the rendered prompt, not the promised template: any
    range substitution surviving into the text raises, naming the key."""
    leaky = string.Template("$positive_info\nHow many of positions 1..$seq_len include '$label'?")
    with pytest.raises(ValueError) as exc:
        get_periodic_numeric_quiz(
            PeriodicConfig(n=4, labels=4, seed=3),
            numeric_prompter(range_free_template=leaky),
            tokenizer=StubTokenizer(),
        )
    assert "seq_len" in str(exc.value)


def test_an_omit_range_condition_without_its_template_is_refused() -> None:
    """No silent fallback to the range-stating template: a zero arm rendered
    from it would be the leak this condition exists to remove."""
    with pytest.raises(ValueError) as exc:
        get_periodic_numeric_quiz(
            PeriodicConfig(n=4, labels=4, seed=3), numeric_prompter(),
            tokenizer=StubTokenizer(),
        )
    assert "range_free_template" in str(exc.value)


@pytest.mark.parametrize("target, match", [
    ("nope", "nope"),            # names a condition that is not in the mapping
    ("noise_intens", "noise_intens"),  # names a condition that is itself padded
])
def test_a_bad_token_target_is_refused(target: str, match: str) -> None:
    """`match_tokens_to` must name a condition that exists and isn't itself
    padded, or the render loop has no valid count to pad against."""
    from smolbench.induction.periodic import Condition

    conditions = dict(CONDITIONS)
    conditions["noise_intens"] = Condition(
        context=CONDITIONS["noise_intens"].context, match_tokens_to=target)
    with pytest.raises(ValueError) as exc:
        get_periodic_numeric_quiz(
            PeriodicConfig(n=4, labels=4, seed=3),
            numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
            tokenizer=StubTokenizer(), conditions=conditions,
        )
    assert match in str(exc.value)


def test_rendered_queries_carry_the_token_count_of_every_arm() -> None:
    """Generation already tokenizes each prompt; reporting those counts lets a
    caller size a completion budget without re-tokenizing the whole quiz."""
    from smolbench.induction.periodic import get_periodic_prompts

    tokenizer = StubTokenizer()
    rendered = list(get_periodic_prompts(
        PeriodicConfig(n=4, labels=4, seed=3),
        numeric_prompter(range_free_template=NUM_TMPL_RANGE_FREE),
        tokenizer=tokenizer,
    ))
    assert len(rendered) == 4
    for query in rendered:
        assert set(query.prompts) == set(query.token_counts) == set(CONDITIONS)
        for arm, prompt in query.prompts.items():
            assert query.token_counts[arm] == tokenizer.count(prompt), arm
        # The noise arm is a length control: its count equals the extens count.
        assert query.token_counts["noise_intens"] == query.token_counts["extens"]
