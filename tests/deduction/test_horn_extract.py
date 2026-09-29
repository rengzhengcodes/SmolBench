"""Proof extraction under the two scoring modes (``smolbench.deduction.horn.extract``)."""

from __future__ import annotations

import pytest

from smolbench.deduction.horn.extract import (
    SCORING_MODES,
    extract_answer,
    final_proof_block,
)

ECHO = "A step applies one library rule with x set to one constant."
INTERLEAVED = f"derive a(c) from f(c)\n{ECHO}\nderive g(c) from a(c)\n{ECHO}\nderive h(c) from g(c)\n"
FULL = "derive a(c) from f(c)\nderive g(c) from a(c)\nderive h(c) from g(c)\n"


def test_modes():
    assert SCORING_MODES == ("iclr", "default")


def test_iclr_stops_at_prose_between_steps():
    assert final_proof_block(INTERLEAVED, "iclr") == "derive h(c) from g(c)\n"


def test_default_skips_prose_between_steps():
    assert final_proof_block(INTERLEAVED, "default") == FULL
    assert final_proof_block(INTERLEAVED) == FULL


@pytest.mark.parametrize("sep", ["</think>", "[/THINK]", "---", "--", "***", "___", "## Final proof", "```"])
def test_default_stops_at_separators(sep):
    text = f"derive z(c) from f(c)\n{sep}\nderive a(c) from f(c)\n"
    assert final_proof_block(text, "default") == "derive a(c) from f(c)\n"


def test_default_keeps_a_fenced_final_proof_only():
    text = "Draft:\nderive a(c) from f(c)\nFinal:\n```\nderive a(c) from f(c)\nderive g(c) from a(c)\n```\n"
    assert final_proof_block(text, "default") == "derive a(c) from f(c)\nderive g(c) from a(c)\n"


def test_both_modes_skip_trailing_prose_and_strip_markers():
    for mode in SCORING_MODES:
        assert final_proof_block("- `derive a(c) from f(c)`\n\nThis completes the proof.", mode) == (
            "derive a(c) from f(c)\n"
        )
        assert final_proof_block("no steps here", mode) == ""


def test_extract_answer_removes_reasoning_blocks():
    text = "<think>derive z(c) from f(c)</think>\nderive a(c) from f(c)\n"
    for mode in SCORING_MODES:
        assert extract_answer(text, mode) == "derive a(c) from f(c)\n"


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        final_proof_block("derive a(c) from f(c)", "strict")
