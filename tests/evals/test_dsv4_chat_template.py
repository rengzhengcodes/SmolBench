"""Pin byte equality for the DeepSeek-V4 inline chat template.

Ground truth is ``tests/fixtures/dsv4/encoding_dsv4_vendored.py``, vendored
verbatim from ``deepseek-ai/DeepSeek-V4-Pro`` on 2026-08-11: re-vendor it from
upstream when the encoding changes, never patch it to match the template.
"""

from __future__ import annotations

import importlib.util

import jinja2
import pytest

from smolbench.evals.providers.ec2 import DSV4_CHAT_TEMPLATE
from tests._paths import FIXTURES

_VENDORED = FIXTURES / "dsv4" / "encoding_dsv4_vendored.py"


def _load_vendored():
    spec = importlib.util.spec_from_file_location("encoding_dsv4_vendored", _VENDORED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENC = _load_vendored()

LEAN_SYSTEM = (
    "You are an expert in the Lean 4 theorem prover and the Mathlib4 library.\n"
    "Respond with only the Lean 4 tactic block."
)
USER_PROMPT = (
    "You are a precise integer counter.\n\n"
    "Task: answer the question below with a single integer and nothing else.\n\n"
    "Context:\nEvery 2 positions write 'foo'.\n\n"
    "Question:\nHow many of the positions 1 through 2520 include 'foo'?"
)


def _render(messages, **kwargs):
    return jinja2.Template(DSV4_CHAT_TEMPLATE).render(
        messages=messages, add_generation_prompt=True, **kwargs
    )


@pytest.mark.parametrize(
    "kwargs,mode",
    # The unset row is load-bearing: vLLM's deepseek_v4 parser defaults thinking=True.
    [({"thinking": True}, "thinking"), ({}, "thinking"), ({"thinking": False}, "chat")],
    ids=["thinking", "unset-defaults-thinking", "chat"],
)
@pytest.mark.parametrize(
    "messages",
    [
        [{"role": "user", "content": USER_PROMPT}],
        [{"role": "system", "content": LEAN_SYSTEM}, {"role": "user", "content": USER_PROMPT}],
    ],
    ids=["user-only", "system+user"],
)
def test_matches_shipped_encoding(messages, kwargs, mode):
    assert _render(messages, **kwargs) == ENC.encode_messages(messages, thinking_mode=mode)
