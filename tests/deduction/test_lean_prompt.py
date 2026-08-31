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
    ],
)
def test_extract_tactic_block(text, expected):
    assert prompt.extract_tactic_block(text) == expected


def test_build_user_prompt_appends_instruction():
    rc = RenderedContext(chain="stepk", level=0, text="CONTEXT BLOCK")
    assert prompt.build_user_prompt(rc) == "CONTEXT BLOCK" + "\n\n" + prompt.INSTRUCTION
