"""Build LLM prompts from rendered context.

`SYSTEM` travels as the calling `ChatClient`'s per-call `system=` argument;
`build_user_prompt` returns the plain user-turn string.
"""

from __future__ import annotations

import re

from .context import RenderedContext

SYSTEM = """You are an expert in the Lean 4 theorem prover and the Mathlib4 library.

You will be shown the state of an in-progress proof and asked to complete the
remainder. Respond with **only** the Lean 4 tactic block that completes the
proof, with no surrounding markdown or commentary. Use newline-separated tactics
exactly as they would appear in a Lean source file.

Do not include the theorem statement, the `by` keyword, or any tactics that
have already been applied — output only the tactics that remain.""".strip()

INSTRUCTION = """Produce the remaining Lean 4 tactics that close all goals from the current
state. Output only the tactic lines, nothing else.""".strip()


_FENCE_RE = re.compile(r"```(?:lean|lean4)?\s*\n(.*?)\n```", re.DOTALL)


def extract_tactic_block(text: str) -> str:
    """Pull the Lean tactics out of an LLM response, stripped.

    In order: strip a leading ``<think>`` block through its first ``</think>``
    (belt-and-suspenders -- `smolbench/evals/openai_compat.py` is the primary
    split point); return the LAST fenced ```` ```lean ```` or unlabelled block,
    since a model that reasons first puts the answer last; else strip a single
    surrounding fence; else return the stripped text as-is.

    Returns
    -------
    str
        The tactic text, or ``""`` for a response opening with an UNCLOSED
        ``<think>`` block: no recoverable tactics, and scoring it would pollute
        ``lean_error`` stats instead of giving a clean "no answer".
    """
    s = text.strip()
    if s.startswith("<think>"):
        close_idx = s.find("</think>")
        if close_idx == -1:
            # Truncated CoT: "" is a clean miss, not a wrong proof (see Returns).
            return ""
        s = s[close_idx + len("</think>") :].lstrip()
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


def build_user_prompt(rendered: RenderedContext) -> str:
    """The user turn: `rendered.text` (one (theorem, k, rung) triple) plus `INSTRUCTION`."""
    return rendered.text + "\n\n" + INSTRUCTION
