"""Tests for Lean fence extraction and prompt assembly."""

import pytest

import smolbench.deduction.lean.prompt as prompt
from smolbench.deduction.lean.context import RenderedContext

_THINK_NOT_AT_START = "some preamble <think>not a leading tag</think> exact h"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("reasoning\n```lean\nwrong\n```\nmore\n```lean\nexact h\nsimp\n```\ntrailing",
         "exact h\nsimp"),
        ("```\nrfl\n```", "rfl"),
        ("```lean4\nomega\n```", "omega"),
        ("  exact h\nsimp  ", "exact h\nsimp"),
        ("<think>\nfirst I'll try induction\n</think>\nexact h\nsimp", "exact h\nsimp"),
        ("<think>reasoning about the goal state</think>\n```lean\nexact h\nsimp\n```",
         "exact h\nsimp"),
        ("<think>\nstill reasoning and reasoning with no end in sight...", ""),
        (_THINK_NOT_AT_START, _THINK_NOT_AT_START.strip()),
        ("<think></think>tac", "tac"),
        ("```lean\nrfl", "rfl"),  # unclosed fence: header line stripped, body kept
        # Non-Lean fences must not steal the following Lean block.
        ("```text\nintro h\nsimp\n```\n\n```lean\nintro h\nsimp\n```",
         "intro h\nsimp"),
        ("```python\nprint(1)\n```\n\n```lean\nexact h\n```", "exact h"),
        # The last Lean block wins, not merely the last block.
        ("```lean\nexact h\n```\n```text\nblah\n```", "exact h"),
        # An unclosed non-Lean fence must not discard the preceding closed block.
        ("```lean\nexact h\n```\n```python\nnever closed", "exact h"),
        # An empty Lean block is still an answer.
        ("```lean\n\n```", ""),
    ],
)
def test_extract_tactic_block(text: str, expected: str) -> None:
    """A non-Lean fence cannot yield a literal ` ```lean` tactic header."""
    assert prompt.extract_tactic_block(text) == expected


def test_build_user_prompt_appends_instruction() -> None:
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION
