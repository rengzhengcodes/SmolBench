"""Offline tests for smolbench.deduction.lean.prompt (fence extraction + prompt assembly)."""

import smolbench.deduction.lean.prompt as prompt
from smolbench.deduction.lean.context import RenderedContext


def test_extract_last_lean_fence_wins():
    text = "reasoning\n```lean\nwrong\n```\nmore\n```lean\nexact h\nsimp\n```\ntrailing"
    assert prompt.extract_tactic_block(text) == "exact h\nsimp"


def test_extract_unlabeled_fence():
    assert prompt.extract_tactic_block("```\nrfl\n```") == "rfl"


def test_extract_lean4_labelled_fence():
    assert prompt.extract_tactic_block("```lean4\nomega\n```") == "omega"


def test_extract_bare_text_passthrough():
    assert prompt.extract_tactic_block("  exact h\nsimp  ") == "exact h\nsimp"


def test_build_user_prompt_appends_instruction():
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION


def test_system_prompt_non_empty():
    assert prompt.SYSTEM.strip()
    assert "Lean 4" in prompt.SYSTEM
