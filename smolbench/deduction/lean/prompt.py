"""Build LLM prompts from rendered context.

The static system prompt (`SYSTEM`) and the (theorem, k, rung)-fixed context
block are no longer assembled into a hand-rolled `Message` list: `SYSTEM`
travels as the calling `ChatClient`'s per-call `system=` argument, and
`build_user_prompt` returns the plain user-turn string. The old Anthropic
Messages client's `cache_breakpoint=True` hints (which marked the end of the
system message and the end of the context block as cache boundaries) are
gone along with that client — OpenRouter auto-caches long, stable Anthropic
prompt prefixes without needing an explicit breakpoint, so nothing is lost.
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


def build_user_prompt(rendered: RenderedContext) -> str:
    """Assemble the user-turn prompt text for one LLM call.

    Parameters
    ----------
    rendered : RenderedContext
        The rendered context block for one (theorem, k, rung) triple, as
        produced by `smolbench.deduction.lean.context.render`.

    Returns
    -------
    str
        `rendered.text` followed by a blank line and `INSTRUCTION`.
        Byte-identical to the `content` of the user-role message the
        pre-refactor `build_messages` used to build — only the packaging
        changed, not the text sent to the model.

    Notes
    -----
    The system half of the old two-message list now travels separately, as
    the calling `ChatClient`'s per-call `system=` argument (see `SYSTEM`
    above) — it is not part of this function's return value. The old
    Anthropic `cache_breakpoint=True` hints are gone along with the
    hand-rolled `Message` type they were attached to; OpenRouter's
    Anthropic-backed models auto-cache stable prompt prefixes without an
    explicit breakpoint.
    """
    return rendered.text + "\n\n" + INSTRUCTION
