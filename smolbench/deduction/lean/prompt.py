"""Build LLM prompts from rendered context; `SYSTEM` is passed per call."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import RenderedContext

SYSTEM = """You are an expert in the Lean 4 theorem prover and the Mathlib4 library.

You will be shown the state of an in-progress proof and asked to complete the
remainder. Respond with **only** the Lean 4 tactic block that completes the
proof, with no surrounding markdown or commentary. Use newline-separated tactics
exactly as they would appear in a Lean source file.

Do not include the theorem statement, the `by` keyword, or any tactics that
have already been applied — output only the tactics that remain.

Hypotheses shown with `✝` (e.g. `x✝`, `this✝`) are inaccessible and cannot be
referenced by name. Name them with `rename_i` or use them through `‹_›`,
`assumption`, or `_`.""".strip()

INSTRUCTION = (
    """Produce the remaining Lean 4 tactics that close all goals from the current
state. Output only the tactic lines, nothing else.""".strip()
)


# Answer-fence tags; other fences must not supply tactics.
_LEANISH_FENCE_TAGS = frozenset({"", "lean", "lean4"})


def _find_closed_fenced_blocks(s: str) -> list[tuple[str, str]]:
    """Collect closed fenced blocks without pairing a closer as a new opener.

    Parameters
    ----------
    s : str

    Returns
    -------
    list[tuple[str, str]]
        Closed tag/body pairs in order.
    """
    # `tag is None` alone tracks open state, avoiding Optional narrowing for `buf`.
    tag: str | None = None
    buf: list[str] = []
    blocks: list[tuple[str, str]] = []
    for line in s.split("\n"):
        stripped = line.rstrip()
        if tag is None:
            if stripped.startswith("```"):
                tag, buf = stripped[3:].strip(), []
        else:
            # Lean responses do not use nested fences.
            if stripped == "```":
                blocks.append((tag, "\n".join(buf)))
                tag, buf = None, []
            else:
                buf.append(line)
    return blocks


def extract_tactic_block(text: str) -> str:
    """Extract tactics, preferring the last closed Lean fence after reasoning.

    An unclosed `<think>` block returns empty so truncated reasoning does not inflate `lean_error`.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
        Extracted tactics; empty for unclosed `<think>`.
    """
    s = text.strip()
    if s.startswith("<think>"):
        close_idx = s.find("</think>")
        if close_idx == -1:
            # Truncated reasoning is a clean miss, not a wrong proof.
            return ""
        s = s[close_idx + len("</think>") :].lstrip()
    blocks = _find_closed_fenced_blocks(s)
    candidates = [
        body for fence_tag, body in blocks if fence_tag in _LEANISH_FENCE_TAGS
    ]
    if candidates:
        # An empty Lean fence is still an answer, not a parse failure.
        return candidates[-1].strip()
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
