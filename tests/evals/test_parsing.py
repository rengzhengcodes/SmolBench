"""Test answer extraction and output-contract compliance.

The eval prompts demand a bare answer and nothing else. The original
graders enforced that by parsing strictly. That made "the model was
wrong" and "the model was right but ignored the format" the same
event, a distinction the induction ``noise_intens`` arm badly needs.
Its whitespace padding degrades instruction following without touching
the reasoning being measured.

These tests pin both halves of the split: the answer that gets
extracted, and the violation label that records how the response broke
the contract.
"""

import pytest

from smolbench.evals import Mark, Marks, Numeric, ToF
from smolbench.evals.openai_compat import grade
from smolbench.evals.parsing import (
    DEGENERATE,
    EMPTY,
    MARKUP,
    MULTIPLE_VALUES,
    PREFIXED,
    TRUNCATED,
    UNPARSEABLE,
    VERBOSE,
    WRONG_LEXICON,
    parse_for,
    parse_numeric,
    parse_tof,
)


# ---------------------------------------------------------------------------
# Compliant responses: unchanged behaviour, no violation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [("True", True), ("False", False), ("true", True), ("  False  ", False)],
)
def test_tof_compliant(text, expected):
    """A bare verdict parses and is flagged compliant."""
    result = parse_tof(text)
    assert result.value is expected
    assert result.violation is None
    assert result.compliant


@pytest.mark.parametrize("text,expected", [("2520", 2520), ("-7", -7), (" 42 ", 42)])
def test_numeric_compliant(text, expected):
    """A bare integer parses and is flagged compliant."""
    result = parse_numeric(text)
    assert result.value == expected
    assert result.violation is None


# ---------------------------------------------------------------------------
# Violations that still yield an answer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,value,violation",
    [
        ("Answer: False", False, PREFIXED),
        ("Answer:\nFalse", False, PREFIXED),
        ("**False**", False, MARKUP),
        ('"True".', True, MARKUP),
        ("Yes", True, WRONG_LEXICON),
        ("No", False, WRONG_LEXICON),
    ],
)
def test_tof_recoverable_violations(text, value, violation):
    """Right verdict, wrong shape: recovered AND flagged.

    These are exactly the responses the whitespace-padded noise arm
    produces. The old behavior scored them as failures, charging the
    model for formatting when the question was answered correctly.
    """
    result = parse_tof(text)
    assert result.value is value
    assert result.violation == violation
    assert result.recovered


def test_tof_long_response_ending_in_verdict_is_recovered():
    """A model that reasons and then concludes did conclude."""
    text = "x" * 400 + "\n\nno entry says Wk handed to PD.\n\nAnswer: False"
    result = parse_tof(text)
    assert result.value is False
    assert result.violation == VERBOSE


@pytest.mark.parametrize(
    "text,value,violation",
    [
        ("Answer: 315", 315, PREFIXED),
        ("**42**", 42, MARKUP),
        ("\\boxed{280}", 280, MARKUP),
        ("2520 // 8 = 315\n\n315", 315, MULTIPLE_VALUES),
    ],
)
def test_numeric_recoverable_violations(text, value, violation):
    """Integers behind prose or markup are recovered and flagged.

    ``"2520 // 8 = 315\\n\\n315"`` is the case that matters most. The
    original rule took the FIRST integer and graded this as 2520, the
    operand, not the result. So the mark looked validly graded and was
    simply wrong.
    """
    result = parse_numeric(text)
    assert result.value == value
    assert result.violation == violation


@pytest.mark.parametrize(
    "text,value",
    [("2520/2", 1260), ("2520//2", 1260), ("2520//1", 2520), ("2520/5", 504),
     ("1260 + 0", 1260), ("-7", -7)],
)
def test_numeric_evaluates_unevaluated_expressions(text, value):
    """A calculation is graded on what it computes, not on an operand.

    Real responses from the periodic study: the model answered "2520/2"
    when 1260 was wanted. The first-integer rule scores the numerator
    (2520), and the last-integer rule scores the divisor (2). Both are
    wrong, while the model was right. Only expression evaluation grades
    what it actually said.
    """
    result = parse_numeric(text)
    assert result.value == value


@pytest.mark.parametrize("text", ["9**9**9", "2520/0", "2520/7.5abc"])
def test_numeric_refuses_unsafe_or_ill_formed_expressions(text):
    """Exponentiation, division by zero, and junk never evaluate.

    ``9**9**9`` is a denial-of-service rather than an answer, so Pow is
    not in the allowlist, and the expression is never computed. The
    response falls back to integer extraction instead of hanging the
    grader.
    """
    result = parse_numeric(text)
    assert result.violation != "unevaluated-expression"


@pytest.mark.parametrize(
    "text", ["The count is " + "0" * 20379 + " items", "9" * 5000, "-" + "7" * 9000]
)
def test_absurdly_long_integers_do_not_raise(text):
    """A giant digit run yields no answer instead of crashing.

    Python refuses int/str conversion past 4,300 digits, so an
    unguarded ``int()`` in the grading path is a crash, not a bad
    grade. A degenerating model really does emit these. One response
    carried a 20,379-digit run, which propagated out of grade() and
    killed a live study mid-arm after hours of GPU time.
    """
    result = parse_numeric(text)
    assert result.value is None
    assert result.violation is not None


def test_grade_survives_a_parser_exception():
    """A parser bug degrades one mark to invalid; it must not kill the run.

    The grading step runs after the expensive part. So an exception here
    throws away work that retrying cannot recover. On a spot instance,
    the box keeps billing while nothing progresses.
    """
    import smolbench.evals.openai_compat as oc
    import smolbench.evals.parsing as parsing_mod

    def exploding_parse(question, text):
        raise RuntimeError("simulated parser bug")

    # grade() imports parse_for from the module at call time, so patching the
    # module attribute is what the running code will see.
    saved = parsing_mod.parse_for
    parsing_mod.parse_for = exploding_parse
    try:
        marks = oc.grade(
            (ToF(prompt="q", answer=True),), [("True", None)], "stub-model"
        )
    finally:
        parsing_mod.parse_for = saved

    assert marks.marks[0].score is None
    assert marks.marks[0].compliance == "parser-error"
    assert marks.marks[0].response == "True"  # raw text kept for re-grading


def test_arithmetic_evaluation_cannot_execute_code():
    """The evaluator walks a validated AST; it never calls ``eval``."""
    from smolbench.evals.parsing import _eval_arithmetic

    assert _eval_arithmetic("__import__('os').system('echo hi')") is None
    assert _eval_arithmetic("open('/etc/passwd')") is None


# ---------------------------------------------------------------------------
# Failures that must NOT be recovered
# ---------------------------------------------------------------------------


def test_degenerate_repetition_is_never_recovered():
    """Repetition collapse is not a parsing problem.

    Observed live: Nemotron-Ultra-253B, under the whitespace-padded
    noise arm, emitted 24,576 characters of "0", the whole completion
    budget, on every question. There is no answer in there to find.
    """
    collapse = "0" * 24576
    for result in (parse_numeric(collapse), parse_tof(collapse)):
        assert result.value is None
        assert result.violation == DEGENERATE


def test_collapse_after_a_real_beginning_is_degenerate_not_truncated():
    """A response that starts fine and then devolves is a breakdown, not a cap.

    Observed live: Olmo-3.1-32B-Think, under the whitespace-padded
    noise arm, began reasoning, then emitted ~16,400 repeated U+2010
    hyphens until the 16k completion budget ran out. If you judge the
    whole string, you'd see a wide alphabet, the real prose at the
    front, and call it TRUNCATED. That blames the budget for the model
    breaking down, which is a materially different finding.
    """
    response = "Okay, let me work through the intervals carefully. " * 5 + "‐" * 16000
    result = parse_tof(response)
    assert result.value is None
    assert result.violation == DEGENERATE


def test_phrase_level_collapse_is_degenerate():
    """A looped PHRASE is collapse even though the alphabet is wide.

    Llama-4-Maverick, under the whitespace-padded noise arm, looped
    ``"## Step 1"`` for thousands of words. Every character-level test
    sees a normal alphabet: letters, digits, punctuation. So without a
    word-level check, this got labelled ``multiple-values``, blaming
    the parser for what is the model breaking down.
    """
    result = parse_numeric("## Step 1\n\n" * 300)
    assert result.value is None
    assert result.violation == DEGENERATE


def test_vocabulary_collapse_over_a_whole_response_is_degenerate():
    """Loop-then-wander still counts, even when the tail looks varied.

    Maverick's real responses looped a header for thousands of words,
    then drifted into unrelated hallucinated text ending in a boxed
    number. So neither the tail nor the alphabet looked wrong, but the
    response used 67 distinct words across 4,746. A whole-response
    diversity ratio is what catches that shape.
    """
    looped = "## Step 1\n\n" * 400
    wandered = " ".join(f"unrelated token {i}" for i in range(20))
    result = parse_numeric(looped + wandered + "\n\nThe final answer is: 1")
    assert result.violation == DEGENERATE


def test_long_genuine_reasoning_is_not_flagged_degenerate():
    """Real reasoning of the same length must survive the ratio rule."""
    from smolbench.evals.parsing import is_degenerate

    prose = " ".join(
        f"consider interval {i} where colour {i % 7} held the role until year {i * 3}"
        for i in range(300)
    )
    assert not is_degenerate(prose)


def test_ordinary_repetition_is_not_flagged_degenerate():
    """Formatting artefacts must not trip the detector.

    A horizontal rule, a run of trailing newlines, or varied prose that
    happens to be long are all normal output. Only genuine looping
    counts. A model that repeats one phrase for forty sentences has
    broken down, so that case belongs in the degenerate tests above,
    not here.
    """
    varied = " ".join(
        f"in year {i} the role passed to colour {i % 5}" for i in range(40)
    )
    assert parse_tof(varied + "\n\nFalse").value is False
    assert parse_tof("-" * 60 + "\nTrue").violation != DEGENERATE
    assert parse_tof("True" + "\n" * 40).violation != DEGENERATE


def test_truncated_reasoning_is_not_mined_for_a_verdict():
    """A chain cut off mid-thought stays invalid.

    A permissive parser "recovered" 96% of invalids by matching a
    stray "no" or the word "answer" inside reasoning that never
    concluded. Invented verdicts from unfinished chains are worse than
    leaving them invalid. So long responses are only trusted when
    they END in a verdict.
    """
    chain = (
        "Okay, let's tackle this. Is 191 less than 1019? No, wait -- "
        "hmm, let me recount the intervals. " * 6
    )
    result = parse_tof(chain)
    assert result.value is None
    assert result.violation == TRUNCATED


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_response(text):
    """Nothing back is its own label, not a parse failure."""
    assert parse_tof(text).violation == EMPTY
    assert parse_numeric(text).violation == EMPTY


def test_unparseable_short_response():
    """Short, non-empty, no answer in it."""
    assert parse_tof("maybe?").violation == UNPARSEABLE
    assert parse_numeric("no number here").violation == UNPARSEABLE


def test_conflicting_verdicts_take_the_last():
    """Disagreeing tokens resolve to the final one, and say so."""
    result = parse_tof("True, no wait, False")
    assert result.value is False
    assert result.violation == MULTIPLE_VALUES


# ---------------------------------------------------------------------------
# No-regression: anything the strict parser accepted must be unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["True", "False", "true", "FALSE"])
def test_tof_agrees_with_strict_parser_where_strict_succeeds(text):
    """Where ``ToF.condition`` succeeded, the new parser must agree.

    This guards the one thing that would silently rewrite
    already-collected results: a recovery rule that changes a grade
    which previously parsed.
    """
    assert parse_tof(text).value == ToF.condition(text)


@pytest.mark.parametrize("text", ["2520", "-7", "0"])
def test_numeric_agrees_with_strict_parser_on_bare_integers(text):
    """Bare integers are unchanged; only multi-integer answers move."""
    assert parse_numeric(text).value == Numeric.condition(text)


# ---------------------------------------------------------------------------
# parse_for dispatch and the grading integration
# ---------------------------------------------------------------------------


def test_parse_for_dispatches_on_question_type():
    """ToF and Numeric questions route to their own extractors."""
    assert parse_for(ToF(prompt="p", answer=True), "Answer: True").value is True
    assert parse_for(Numeric(prompt="p", answer=1), "Answer: 315").value == 315


def test_grade_records_compliance_and_scores_recovered_answers():
    """A right answer in the wrong shape scores correct AND is flagged.

    This is the whole point of the change. The noise arm's format
    breaks stop being counted as reasoning failures, while remaining
    visible as format failures.
    """
    quiz = (
        ToF(prompt="q1", answer=False),
        ToF(prompt="q2", answer=True),
        ToF(prompt="q3", answer=True),
    )
    responses = [("False", None), ("Answer: True", None), ("0" * 600, None)]
    marks = grade(quiz, responses, "stub-model")

    assert [m.score for m in marks.marks] == [1, 1, None]
    assert [m.compliance for m in marks.marks] == [None, PREFIXED, DEGENERATE]
    assert marks.correct == 2
    assert marks.invalid == 1
    # Compliance is counted independently of correctness.
    assert marks.noncompliant == 2


def test_grade_still_marks_genuinely_wrong_answers_wrong():
    """Format leniency must not turn wrong answers into right ones."""
    quiz = (ToF(prompt="q", answer=True),)
    marks = grade(quiz, [("Answer: False", None)], "stub-model")
    assert marks.marks[0].score == 0
    assert marks.marks[0].compliance == PREFIXED


# ---------------------------------------------------------------------------
# Backward compatibility of the serialized form
# ---------------------------------------------------------------------------


def test_marks_without_compliance_field_still_load(tmp_path):
    """Replicate YAMLs written before this field existed must still load.

    ``Marks.load`` builds each mark with ``Mark(**m)``, so the field
    has to carry a default. None there means "not assessed", NOT
    "compliant": the thousands of already-collected replicates predate
    the check.
    """
    path = tmp_path / "rep_1776.yaml"
    Marks(
        model="m",
        marks=(Mark(query="q", answer=True, response="True", score=1),),
    ).dump(path)
    text = path.read_text()
    assert "compliance" in text  # newly written files carry it

    # Simulate an older file by stripping the field back out.
    path.write_text("\n".join(
        line for line in text.splitlines() if "compliance" not in line
    ))
    loaded = Marks.load(path)
    assert loaded.marks[0].compliance is None
    assert loaded.marks[0].score == 1
