"""Extract the scored proof from a model's answer text.

Two scoring modes differ only in how the final proof block is found:

``iclr``
    The block is the last contiguous run of step lines. Any other line ends it, so
    prose between two steps (a model echoing the prompt's instructions, a rule it
    quotes, a comment) drops every step above that line. This is the rule the
    ICLR 2027 submission's Horn table was scored with.
``default``
    The same block, but prose lines between step lines are skipped instead of
    ending it. The checker already ignores such lines (see ``checker``), so this
    scores the proof the model wrote. A separator still ends the block, so a draft
    above it is not scored. The separators are a code fence, a reasoning close tag
    (``</think>``, ``[/THINK]``), a horizontal rule (``--`` or longer, ``***``,
    ``___``) and a markdown heading.

In both modes, trailing prose after the last step is skipped. In ``iclr`` mode a closed
code block followed by an opened one ends the block, so a fenced draft above a fenced
final proof is not scored.
"""

from __future__ import annotations

import re

from .checker import _STEP_RE, Verdict, verify
from .render import Rendered
from .theory import Theory

#: Scoring modes, see the module docstring.
SCORING_MODES = ("iclr", "default")
DEFAULT_SCORING = "default"

_THINK_BLOCK_RE = re.compile(
    r"<think>.*?</think>|\[THINK\].*?\[/THINK\]", re.DOTALL | re.IGNORECASE
)
_FENCE_RE = re.compile(r"^\s*```")
_LINE_DECOR_RE = re.compile(r"^[\s>*`_-]+|[\s*`_]+$")
#: Lines that end a ``default`` block: reasoning close tags, horizontal rules, headings.
_SEPARATOR_RE = re.compile(
    r"^(?:.*(?:</think>|\[/THINK\]).*|(?:-\s*){2,}|(?:\*\s*){3,}|(?:_\s*){3,}|#{1,6}\s.*)$",
    re.IGNORECASE,
)


def strip_reasoning(text: str) -> str:
    """Remove inline reasoning blocks (``<think>`` and Ministral's ``[THINK]``)."""
    return _THINK_BLOCK_RE.sub("", text)


def step_text(line: str) -> str | None:
    """The step in ``line`` with list markers, quotes and backticks removed, or None."""
    s = _LINE_DECOR_RE.sub("", line.strip())
    return s if _STEP_RE.match(s) else None


def final_proof_block(text: str, scoring: str = DEFAULT_SCORING) -> str:
    """The final block of proof-step lines in ``text`` under ``scoring``.

    Returns ``""`` (verdict ``no_answer``) when there is no step line.
    """
    if scoring not in SCORING_MODES:
        raise ValueError(f"unknown scoring mode {scoring!r}; expected one of {SCORING_MODES}")
    lines = text.rstrip().splitlines()
    block: list[str] = []
    fences = 0
    for line in reversed(lines):
        s = line.strip()
        if not s:
            continue
        if _FENCE_RE.match(s):
            fences += 1
            if block and (fences >= 2 or scoring == "default"):
                break
            continue
        step = step_text(s)
        if step is None:
            if block and (scoring == "iclr" or _SEPARATOR_RE.match(s)):
                break
            continue
        fences = 0
        block.append(step)
    if not block:
        return ""
    return "\n".join(reversed(block)) + "\n"


def extract_answer(content: str, scoring: str = DEFAULT_SCORING) -> str:
    """The proof block of a response's text, after inline reasoning is removed."""
    return final_proof_block(strip_reasoning(content or ""), scoring)


def score_answer(
    theory: Theory,
    rendered: Rendered,
    content: str,
    finish_reason: str,
    scoring: str = DEFAULT_SCORING,
) -> tuple[str, Verdict]:
    """The extracted answer and its verdict for a response that finished (stop or length)."""
    answer = extract_answer(content, scoring)
    return answer, verify(theory, rendered, answer, finish_reason or "stop")


def verdict_fields(
    theory: Theory,
    rendered: Rendered,
    content: str,
    finish_reason: str,
    scoring: str = DEFAULT_SCORING,
) -> dict:
    """The verdict fields a result row stores for a finished response."""
    answer, v = score_answer(theory, rendered, content, finish_reason, scoring)
    return {
        "answer": answer,
        "verdict": v.verdict,
        "steps": v.steps,
        "route": v.route,
        "reason": v.reason,
        "ignored_lines": v.ignored_lines,
        "scoring": scoring,
    }
