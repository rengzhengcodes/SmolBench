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


# Info-strings that mark a fenced block as "the answer" rather than scratch
# work: an unlabelled fence (```` ``` ````) or one explicitly tagged `lean`/`lean4`.
_LEANISH_FENCE_TAGS = frozenset({"", "lean", "lean4"})


def _find_closed_fenced_blocks(s: str) -> list[tuple[str, str]]:
    """Scan ``s`` line-by-line and collect every *closed* fenced code block.

    Design rationale
    -----------------
    This is a hand-written line scanner, not a regex, because a closing
    fence line (bare ```` ``` ````) is lexically indistinguishable from an
    opening fence with an empty info-string. A regex that anchors an
    opening match on ``(?m)^```(?:lean4?)?[ \\t]*\\n`` will happily open a
    *new* match on the closing ``` ``` ``` of a preceding non-lean block
    (e.g. ```` ```text ````), and then pair it with whatever fence comes
    after that -- silently returning the wrong span, or (worse, on the
    reviewer's own repro case) `''`. Tracking fence state explicitly as we
    walk the lines sidesteps that ambiguity entirely: a line can only ever
    be interpreted as "open" or "close" relative to the state we are
    already in.

    Parameters
    ----------
    s : str
        Text to scan, already ``<think>``-stripped by the caller.

    Returns
    -------
    list of (str, str)
        One ``(tag, body)`` pair per closed fenced block, in the order the
        blocks appear in ``s``. ``tag`` is the fence's info-string with
        surrounding whitespace stripped (e.g. ``""``, ``"lean"``,
        ``"text"``); ``body`` is the raw (unstripped) text between the
        opening and closing fence lines, newline-joined. An opening fence
        with no matching close by the end of ``s`` contributes nothing --
        it is simply dropped, matching the "unclosed fence" fallback
        behaviour documented on `extract_tactic_block`.
    """
    # Design: `tag is None` is the sole open/closed state flag. `buf` is
    # initialised to `[]` up front (rather than `None`) and simply goes
    # unused while `tag is None`, so its type stays a plain `list[str]` --
    # no `Optional` to narrow (via `assert` or otherwise) at the point
    # where we consume it on close.
    tag: str | None = None
    buf: list[str] = []
    blocks: list[tuple[str, str]] = []
    for line in s.split("\n"):
        stripped = line.rstrip()
        if tag is None:
            # Outside any fence: a "```" line (with an optional info-string)
            # opens one and starts capturing its body.
            if stripped.startswith("```"):
                tag, buf = stripped[3:].strip(), []
        else:
            # Inside a fence: only a bare "```" line closes it. Anything
            # else -- including another "```xyz" -- is just body content
            # (nested fences aren't a thing Lean responses use).
            if stripped == "```":
                blocks.append((tag, "\n".join(buf)))
                tag, buf = None, []
            else:
                buf.append(line)
    return blocks


def extract_tactic_block(text: str) -> str:
    """Pull the Lean tactics out of an LLM response, stripped.

    In order: strip a leading ``<think>`` block through its first ``</think>``
    (belt-and-suspenders -- `smolbench/evals/openai_compat.py` is the primary
    split point); return the LAST *closed* fenced block whose info-string is
    ``lean``, ``lean4``, or empty, since a model that reasons first puts the
    answer last -- non-``lean``-ish fences (e.g. ```` ```text ````,
    ```` ```python ````) are tracked so their closing fence is correctly
    consumed instead of being mistaken for the start of the next block, but
    such blocks are themselves never returned; else strip a single
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
    blocks = _find_closed_fenced_blocks(s)
    candidates = [body for fence_tag, body in blocks if fence_tag in _LEANISH_FENCE_TAGS]
    if candidates:
        # Last one wins (see docstring); no emptiness filter -- a genuinely
        # empty ```` ```lean\n\n``` ```` block is a legitimate (if useless)
        # answer, not a parse failure to fall through on.
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
