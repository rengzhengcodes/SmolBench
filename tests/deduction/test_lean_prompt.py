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
        # --- 13-02: a NON-lean fence must not steal the match ---------------
        # Pins the post-fix contract: fences are paired by scanning lines, so a
        # ```text / ```python block is consumed whole (never returned) and the
        # following ```lean block is what comes back. Before the fix these two
        # returned text that STARTED WITH a literal "```lean" line, which was
        # then sent to Lean as a tactic.
        ("```text\nintro h\nsimp\n```\n\n```lean\nintro h\nsimp\n```",
         "intro h\nsimp"),
        ("```python\nprint(1)\n```\n\n```lean\nexact h\n```", "exact h"),
        # A lean block FOLLOWED by a non-lean one: last LEAN-ish block wins,
        # not merely the last block.
        ("```lean\nexact h\n```\n```text\nblah\n```", "exact h"),
        # A trailing UNCLOSED non-lean fence must not destroy the closed lean
        # block before it: only closed blocks are candidates, and the dangling
        # opener simply yields no block of its own.
        ("```lean\nexact h\n```\n```python\nnever closed", "exact h"),
        # An empty lean block still counts as an answer (unchanged behaviour):
        # the model answered, it answered with nothing.
        ("```lean\n\n```", ""),
    ],
)
def test_extract_tactic_block(text, expected):
    """Fence extraction, including 13-02's non-lean-fence cases.

    The last five cases pin the LINE-SCANNING pairing introduced for 13-02:
    a closing ``` line is only ever a closing delimiter for the fence that is
    currently open, so a non-lean block can no longer make the extractor
    return a chunk beginning with a literal "```lean" header line.
    """
    assert prompt.extract_tactic_block(text) == expected


def test_build_user_prompt_appends_instruction():
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION
