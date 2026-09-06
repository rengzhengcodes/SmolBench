"""Test answer extraction and the violation label recording contract breaks."""

import pytest

from smolbench.evals import Numeric, ToF
from smolbench.evals.openai_compat import grade
from smolbench.evals.quiz import COMPLIANT
from smolbench.evals.parsing import (
    DEGENERATE, EMPTY, EXPRESSION, MARKUP, MULTIPLE_VALUES, PREFIXED, TRUNCATED,
    UNPARSEABLE, VERBOSE, WRONG_LEXICON, is_degenerate, parse_for, parse_numeric, parse_tof,
)

_TRUNCATED_CHAIN = (
    "Okay, let's tackle this. Is 191 less than 1019? No, wait -- "
    "hmm, let me recount the intervals. " * 6
)


@pytest.mark.parametrize(
    "text,value,violation",
    [("True", True, None), ("False", False, None), ("true", True, None),
     ("  False  ", False, None), ("Answer: False", False, PREFIXED),
     ("Answer:\nFalse", False, PREFIXED), ("**False**", False, MARKUP),
     ('"True".', True, MARKUP), ("Yes", True, WRONG_LEXICON), ("No", False, WRONG_LEXICON),
     ("x" * 400 + "\n\nno entry says Wk handed to PD.\n\nAnswer: False", False, VERBOSE),
     ("True, no wait, False", False, MULTIPLE_VALUES), ("   ", None, EMPTY),
     ("maybe?", None, UNPARSEABLE), (_TRUNCATED_CHAIN, None, TRUNCATED)],
)
def test_tof_extraction(text, value, violation):
    """A verdict is recovered from any shape that ends in one; unfinished chains are not."""
    result = parse_tof(text)
    assert result.value is value
    assert result.violation == violation
    assert result.compliant is (violation is None)
    assert result.recovered is (value is not None and violation is not None)


@pytest.mark.parametrize(
    "text,value,violation",
    [("2520", 2520, None), ("-7", -7, None), (" 42 ", 42, None),
     ("Answer: 315", 315, PREFIXED), ("**42**", 42, MARKUP), ("\\boxed{280}", 280, MARKUP),
     ("2520 // 8 = 315\n\n315", 315, MULTIPLE_VALUES), ("2520/2", 1260, EXPRESSION),
     # A worked calculation after an "answer" lead-in: the terminal integer is
     # the result; the first-after-lead would score the operand 2520.
     ("The answer is computed as 2520 / 8 = 315", 315, MULTIPLE_VALUES),
     # Over-long but varied bare integer: out of range, NOT a repetition
     # collapse -- must not inflate the DEGENERATE census.
     ("1234567890" * 5, None, UNPARSEABLE),
     ("2520//2", 1260, EXPRESSION), ("1260 + 0", 1260, EXPRESSION),
     ("2520 - 5 * 2", 2510, EXPRESSION), ("", None, EMPTY), ("no number here", None, UNPARSEABLE)],
)
def test_numeric_extraction(text, value, violation):
    """An integer is graded on what the response computes, not on an operand."""
    result = parse_numeric(text)
    assert result.value == value
    assert result.violation == violation


@pytest.mark.parametrize("text", ["9**9**9", "2520/0", "2520/7.5abc"])
def test_numeric_refuses_unsafe_or_ill_formed_expressions(text):
    """Exponentiation, division by zero, and junk never evaluate -- but a
    violation is still recorded (integer-picking labels them MULTIPLE_VALUES)."""
    result = parse_numeric(text)
    assert result.violation != EXPRESSION
    assert result.violation is not None


def test_arithmetic_evaluation_cannot_execute_code():
    """The evaluator walks a validated AST; it never calls ``eval``."""
    from smolbench.evals.parsing import _eval_arithmetic

    assert _eval_arithmetic("__import__('os').system('echo hi')") is None
    assert _eval_arithmetic("open('/etc/passwd')") is None


def test_absurdly_long_integer_yields_no_answer():
    """Python refuses int/str conversion past 4,300 digits; that must not crash grading."""
    result = parse_numeric("The count is " + "0" * 20379 + " items")
    assert result.value is None
    assert result.violation is not None


@pytest.mark.parametrize("text", ["True", "False", "FALSE", "  true "])
def test_tof_agrees_with_strict_parser(text):
    """Where the legacy strict parser succeeds, the lenient one must not regrade it."""
    assert parse_tof(text).value == ToF.condition(text)


@pytest.mark.parametrize("text", ["2520", "-7", "0"])
def test_numeric_agrees_with_strict_parser(text):
    assert parse_numeric(text).value == Numeric.condition(text)


@pytest.mark.parametrize(
    "text",
    ["0" * 24576,
     "Okay, let me work through the intervals carefully. " * 5 + "‐" * 16000,
     "## Step 1\n\n" * 300,
     "## Step 1\n\n" * 400 + " ".join(f"unrelated token {i}" for i in range(20))
     + "\n\nThe final answer is: 1"],
)
def test_degenerate(text):
    """Repetition collapse is a breakdown, not a parsing problem: no answer is mined out."""
    for result in (parse_numeric(text), parse_tof(text)):
        assert result.value is None
        assert result.violation == DEGENERATE


@pytest.mark.parametrize(
    "text",
    [" ".join(f"consider interval {i} where colour {i % 7} held the role until year {i * 3}"
              for i in range(300)),
     " ".join(f"in year {i} the role passed to colour {i % 5}" for i in range(40)) + "\n\nFalse",
     "-" * 60 + "\nTrue", "True" + "\n" * 40],
)
def test_not_degenerate(text):
    """Long genuine reasoning and formatting artefacts must not trip the detector."""
    assert not is_degenerate(text)
    assert parse_tof(text).violation != DEGENERATE


def test_parse_for_dispatches_on_question_type():
    """ToF and Numeric questions route to their own extractors."""
    assert parse_for(ToF(prompt="p", answer=True), "Answer: True").value is True
    assert parse_for(Numeric(prompt="p", answer=1), "Answer: 315").value == 315


def test_grade_records_scores_and_compliance():
    """Recovered right answers score correct but stay flagged; wrong ones stay wrong."""
    quiz = (
        ToF(prompt="q1", answer=False),
        ToF(prompt="q2", answer=True),
        ToF(prompt="q3", answer=True),
        ToF(prompt="q4", answer=True),
    )
    responses = [("False", None), ("Answer: True", None), ("0" * 600, None),
                 ("Answer: False", None)]
    marks = grade(quiz, responses, "stub-model")

    assert [m.score for m in marks.marks] == [1, 1, None, 0]
    # COMPLIANT is the explicit string "compliant", never None: `parse_for`
    # still reports "no violation" as `violation=None`, and `grade` is the
    # boundary that translates that into the stored label.
    assert [m.compliance for m in marks.marks] == [COMPLIANT, PREFIXED, DEGENERATE, PREFIXED]
    assert (marks.correct, marks.invalid, marks.noncompliant) == (2, 1, 3)


def test_grade_survives_a_parser_exception():
    """A parser bug degrades one mark to invalid; it must not kill the run."""
    import smolbench.evals.openai_compat as oc
    import smolbench.evals.parsing as parsing_mod

    def exploding_parse(question, text):
        raise RuntimeError("simulated parser bug")

    saved = parsing_mod.parse_for
    parsing_mod.parse_for = exploding_parse
    try:
        marks = oc.grade((ToF(prompt="q", answer=True),), [("True", None)], "stub-model")
    finally:
        parsing_mod.parse_for = saved

    assert marks.marks[0].score is None
    assert marks.marks[0].compliance == "parser-error"
    assert marks.marks[0].response == "True"
