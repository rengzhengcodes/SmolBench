"""Proof extraction (``smolbench.deduction.horn.extract``)."""

from __future__ import annotations

from smolbench.deduction.horn.extract import extract_answer, final_proof_block

ECHO = "A step applies one library rule with x set to one constant."


def test_prose_between_steps_ends_the_proof():
    text = f"derive a(c) from f(c)\n{ECHO}\nderive g(c) from a(c)\n"
    assert final_proof_block(text) == "derive g(c) from a(c)\n"


def test_fenced_final_proof_after_a_draft():
    text = "Draft:\nderive a(c) from f(c)\nFinal:\n```\nderive a(c) from f(c)\nderive g(c) from a(c)\n```\n"
    assert final_proof_block(text) == "derive a(c) from f(c)\nderive g(c) from a(c)\n"


def test_trailing_prose_is_skipped_and_markers_stripped():
    assert final_proof_block("- `derive a(c) from f(c)`\n\nThis completes the proof.") == "derive a(c) from f(c)\n"
    assert final_proof_block("no steps here") == ""


def test_extract_answer_removes_reasoning_blocks():
    text = "<think>derive z(c) from f(c)</think>\nderive a(c) from f(c)\n"
    assert extract_answer(text) == "derive a(c) from f(c)\n"
