"""Offline tests for smolbench.deduction.lean.prompt (fence extraction + prompt assembly)."""

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
        # A non-lean fence must not steal the match: fences pair by scanning
        # lines, so a ```text/```python block is consumed whole and the
        # following ```lean block is what comes back. Before this, text
        # starting with a literal ```lean line could be sent to Lean as a
        # tactic.
        ("```text\nintro h\nsimp\n```\n\n```lean\nintro h\nsimp\n```",
         "intro h\nsimp"),
        ("```python\nprint(1)\n```\n\n```lean\nexact h\n```", "exact h"),
        # A lean block followed by a non-lean one: the last lean-ish block
        # wins, not merely the last block.
        ("```lean\nexact h\n```\n```text\nblah\n```", "exact h"),
        # A trailing unclosed non-lean fence must not destroy the closed lean
        # block before it: only closed blocks are candidates, and the
        # dangling opener simply yields no block of its own.
        ("```lean\nexact h\n```\n```python\nnever closed", "exact h"),
        # An empty lean block still counts as an answer (unchanged behaviour):
        # the model answered, it answered with nothing.
        ("```lean\n\n```", ""),
    ],
)
def test_extract_tactic_block(text: str, expected: str) -> None:
    """Fence extraction, including the non-lean-fence cases.

    A closing ``` line only ever closes the fence currently open, so a
    non-lean block cannot make the extractor return a chunk beginning with a
    literal "```lean" header line.
    """
    assert prompt.extract_tactic_block(text) == expected


def test_build_user_prompt_appends_instruction() -> None:
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION
