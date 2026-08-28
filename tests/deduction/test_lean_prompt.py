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


def test_extract_leading_closed_think_bare_tactics():
    text = "<think>\nfirst I'll try induction\n</think>\nexact h\nsimp"
    assert prompt.extract_tactic_block(text) == "exact h\nsimp"


def test_extract_leading_closed_think_then_fenced_block():
    text = "<think>reasoning about the goal state</think>\n```lean\nexact h\nsimp\n```"
    assert prompt.extract_tactic_block(text) == "exact h\nsimp"


def test_extract_unclosed_think_returns_empty():
    text = "<think>\nstill reasoning and reasoning with no end in sight..."
    assert prompt.extract_tactic_block(text) == ""


def test_extract_think_not_at_start_untouched():
    text = "some preamble <think>not a leading tag</think> exact h"
    assert prompt.extract_tactic_block(text) == text.strip()


def test_extract_empty_rationale_think_block():
    assert prompt.extract_tactic_block("<think></think>tac") == "tac"


def test_build_user_prompt_appends_instruction():
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION


def test_system_prompt_non_empty():
    assert prompt.SYSTEM.strip()
    assert "Lean 4" in prompt.SYSTEM
