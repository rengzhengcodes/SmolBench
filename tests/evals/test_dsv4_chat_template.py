"""Pin byte equality for the DeepSeek-V4 inline chat template.

The V4 repos ship no chat template (``chat_template.jinja`` 404s and
``tokenizer_config.json`` has no ``chat_template`` key, verified
2026-08-11). The shipped encoding lives in the repo's
``encoding/encoding_dsv4.py``. The family-ladder study serves V4 through
vLLM's literal ``--chat-template`` string
(``smolbench.evals.providers.ec2.DSV4_CHAT_TEMPLATE``), so that hand-written Jinja
must reproduce the shipped Python encoding byte-for-byte for every message
shape this repo actually sends:

* induction: ``[user]`` (plus the provider system-prompt slot, unused for
  DeepSeek), and
* the Lean deduction eval: ``[system, user]``,

both with a generation prompt, in both ``thinking`` and ``chat`` modes.
``tests/fixtures/dsv4/encoding_dsv4_vendored.py`` is the shipped module,
vendored verbatim from ``deepseek-ai/DeepSeek-V4-Pro`` (2026-08-11). This
test renders both and checks equality. If DeepSeek revises the encoding,
re-vendor and re-derive; never patch the template without re-running this
pin.
"""

from __future__ import annotations

import importlib.util

import pytest

jinja2 = pytest.importorskip("jinja2")

from smolbench.evals.providers.ec2 import DSV4_CHAT_TEMPLATE
from tests._paths import FIXTURES

_VENDORED = FIXTURES / "dsv4" / "encoding_dsv4_vendored.py"


def _load_vendored():
    spec = importlib.util.spec_from_file_location("encoding_dsv4_vendored", _VENDORED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENC = _load_vendored()

# The Lean eval's real system prompt shape (multiline, markdown-ish) and the
# induction eval's real user shape (long, newline-heavy). This is
# representative content, not placeholders, so whitespace handling is
# actually exercised.
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
    "messages",
    [
        [{"role": "user", "content": USER_PROMPT}],
        [{"role": "system", "content": LEAN_SYSTEM}, {"role": "user", "content": USER_PROMPT}],
    ],
    ids=["user-only", "system+user"],
)
def test_thinking_mode_matches_shipped_encoding(messages):
    expected = ENC.encode_messages(messages, thinking_mode="thinking")
    assert _render(messages, thinking=True) == expected


@pytest.mark.parametrize(
    "messages",
    [
        [{"role": "user", "content": USER_PROMPT}],
        [{"role": "system", "content": LEAN_SYSTEM}, {"role": "user", "content": USER_PROMPT}],
    ],
    ids=["user-only", "system+user"],
)
def test_thinking_undefined_defaults_to_thinking(messages):
    """vLLM's deepseek_v4 parser defaults thinking to True when the kwarg is absent.

    The template must agree, so an unset chat_template_kwargs cannot
    de-synchronize the template and the parser.
    """
    expected = ENC.encode_messages(messages, thinking_mode="thinking")
    assert _render(messages) == expected


@pytest.mark.parametrize(
    "messages",
    [
        [{"role": "user", "content": USER_PROMPT}],
        [{"role": "system", "content": LEAN_SYSTEM}, {"role": "user", "content": USER_PROMPT}],
    ],
    ids=["user-only", "system+user"],
)
def test_chat_mode_matches_shipped_encoding(messages):
    expected = ENC.encode_messages(messages, thinking_mode="chat")
    assert _render(messages, thinking=False) == expected


def test_prompt_ends_inside_think_block_in_thinking_mode():
    """The shipped encoding ends the thinking-mode prompt with an open ``<think>``.

    The completion carries no opening tag. This is pinned separately,
    so a template regression here fails with a readable message
    instead of a wall-of-diff byte mismatch.
    """
    out = _render([{"role": "user", "content": "hi"}], thinking=True)
    assert out.endswith("<think>")
    assert _render([{"role": "user", "content": "hi"}], thinking=False).endswith("</think>")
