"""Build LLM prompts from rendered context.

`SYSTEM` travels as the calling `ChatClient`'s per-call `system=` argument;
`build_user_prompt` returns the plain user-turn string.
"""

from __future__ import annotations

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


# Fence info-strings that mark a block as "the answer" rather than scratch work.
_LEANISH_FENCE_TAGS = frozenset({"", "lean", "lean4"})


def _find_closed_fenced_blocks(s: str) -> list[tuple[str, str]]:
    """Scan ``s`` line-by-line and collect every *closed* fenced code block.

    A hand-written scanner, not a regex: a bare closing fence is lexically
    identical to an opening fence with an empty info-string, so a regex can
    open a new match on a preceding block's closer and pair it with the
    wrong fence. Tracking open/closed state explicitly avoids that.

    An opening fence with no matching close by end of ``s`` is dropped,
    matching the unclosed-fence fallback in `extract_tactic_block`.

    Parameters
    ----------
    s : str
        Text to scan for fenced code blocks.

    Returns
    -------
    list[tuple[str, str]]
        One ``(tag, body)`` pair per closed block, in appearance order.
    """
    # `tag is None` is the sole open/closed flag; `buf` starts as `[]` rather
    # than `None` so it needs no `Optional` narrowing when consumed on close.
    tag: str | None = None
    buf: list[str] = []
    blocks: list[tuple[str, str]] = []
    for line in s.split("\n"):
        stripped = line.rstrip()
        if tag is None:
            if stripped.startswith("```"):
                tag, buf = stripped[3:].strip(), []
        else:
            # Nested fences aren't a thing Lean responses use, so any
            # non-bare line here is just body content.
            if stripped == "```":
                blocks.append((tag, "\n".join(buf)))
                tag, buf = None, []
            else:
                buf.append(line)
    return blocks


def extract_tactic_block(text: str) -> str:
    """Pull the Lean tactics out of an LLM response, stripped.

    Strips a leading ``<think>...</think>`` block (belt-and-suspenders --
    `smolbench/evals/openai_compat.py` is the primary split point), then
    returns the LAST closed lean/lean4/untagged fenced block, since a model
    that reasons first puts the answer last; else strips one surrounding
    fence; else returns the text as-is. Non-lean fences are tracked (so
    their closer isn't mistaken for the next block's start) but never
    returned.

    An UNCLOSED ``<think>`` block has no recoverable tactics, and scoring it
    would pollute ``lean_error`` stats.

    Parameters
    ----------
    text : str
        LLM response containing tactics.

    Returns
    -------
    str
        ``""`` for an UNCLOSED ``<think>`` block.
    """
    s = text.strip()
    if s.startswith("<think>"):
        close_idx = s.find("</think>")
        if close_idx == -1:
            # Truncated CoT: "" is a clean miss, not a wrong proof.
            return ""
        s = s[close_idx + len("</think>") :].lstrip()
    blocks = _find_closed_fenced_blocks(s)
    candidates = [body for fence_tag, body in blocks if fence_tag in _LEANISH_FENCE_TAGS]
    if candidates:
        # No emptiness filter: an empty ```lean``` block is a legitimate,
        # if useless, answer -- not a parse failure to fall through on.
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
