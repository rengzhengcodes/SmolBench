"""Extract the scored proof from a model's answer text.

The proof is the last contiguous run of step lines in the answer, after inline
reasoning blocks are removed. Trailing prose after the last step is skipped. Any other
non-step line ends the run, and so does a closed code block followed by an opened one,
so a draft written above the final proof is not scored. This is the rule the ICLR 2027
submission's Horn results were scored with.
"""

from __future__ import annotations

import re

from .checker import _STEP_RE, verify
from .render import Rendered
from .theory import Theory

_THINK_BLOCK_RE = re.compile(
    r"<think>.*?</think>|\[THINK\].*?\[/THINK\]", re.DOTALL | re.IGNORECASE
)
_FENCE_RE = re.compile(r"^\s*```")
_LINE_DECOR_RE = re.compile(r"^[\s>*`_-]+|[\s*`_]+$")


def strip_reasoning(text: str) -> str:
    """Remove inline reasoning blocks (``<think>`` and Ministral's ``[THINK]``)."""
    return _THINK_BLOCK_RE.sub("", text)


def step_text(line: str) -> str | None:
    """The step in ``line`` with list markers, quotes and backticks removed, or None."""
    s = _LINE_DECOR_RE.sub("", line.strip())
    return s if _STEP_RE.match(s) else None


def final_proof_block(text: str) -> str:
    """The last contiguous run of step lines in ``text``, or ``""`` (verdict ``no_answer``)."""
    lines = text.rstrip().splitlines()
    block: list[str] = []
    fences = 0
    for line in reversed(lines):
        s = line.strip()
        if not s:
            continue
        if _FENCE_RE.match(s):
            fences += 1
            if block and fences >= 2:
                break
            continue
        step = step_text(s)
        if step is None:
            if block:
                break
            continue
        fences = 0
        block.append(step)
    if not block:
        return ""
    return "\n".join(reversed(block)) + "\n"


def extract_answer(content: str) -> str:
    """The proof block of a response's text, after inline reasoning is removed."""
    return final_proof_block(strip_reasoning(content or ""))


def verdict_fields(theory: Theory, rendered: Rendered, content: str, finish_reason: str) -> dict:
    """The verdict fields a result row stores for a finished response (stop or length)."""
    answer = extract_answer(content)
    v = verify(theory, rendered, answer, finish_reason or "stop")
    return {
        "answer": answer,
        "verdict": v.verdict,
        "steps": v.steps,
        "route": v.route,
        "reason": v.reason,
        "ignored_lines": v.ignored_lines,
    }
