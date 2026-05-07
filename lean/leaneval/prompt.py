"""Build LLM messages from rendered context.

The static system prompt and the (theorem, k, rung)-fixed context block are
emitted as separate messages with `cache_breakpoint=True`, so Anthropic prompt
caching can re-use them across the N rollouts at one cell.
"""

from __future__ import annotations

from .context import RenderedContext
from .llm.base import Message

SYSTEM = """You are an expert in the Lean 4 theorem prover and the Mathlib4 library.

You will be shown the state of an in-progress proof and asked to complete the
remainder. Respond with **only** the Lean 4 tactic block that completes the
proof, with no surrounding markdown or commentary. Use newline-separated tactics
exactly as they would appear in a Lean source file.

Do not include the theorem statement, the `by` keyword, or any tactics that
have already been applied — output only the tactics that remain.""".strip()

INSTRUCTION = """Produce the remaining Lean 4 tactics that close all goals from the current
state. Output only the tactic lines, nothing else.""".strip()


_FENCE_RE = __import__("re").compile(
    r"```(?:lean|lean4)?\s*\n(.*?)\n```",
    __import__("re").DOTALL,
)


def extract_tactic_block(text: str) -> str:
    """Pull the Lean tactics out of an LLM response.

    Strategy:
      1. If the response contains one or more ```` ```lean ... ``` ```` (or
         unlabelled) fenced blocks, return the LAST one — models that prefix
         tactics with reasoning typically put the answer last.
      2. Otherwise fall back to stripping a single surrounding fence (legacy).
      3. Otherwise return the stripped text as-is.
    """
    s = text.strip()
    matches = _FENCE_RE.findall(s)
    if matches:
        return matches[-1].strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1 :]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def build_messages(rendered: RenderedContext) -> list[Message]:
    """Assemble the message list for one LLM call.

    Cache breakpoints:
      - end of system message (stable across all calls)
      - end of context block (stable per (theorem, k, rung), reused across rollouts)
    """
    return [
        Message(role="system", content=SYSTEM, cache_breakpoint=True),
        Message(role="user", content=rendered.text + "\n\n" + INSTRUCTION, cache_breakpoint=True),
    ]
