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


_FENCE_RE = __import__("re").compile(
    r"```(?:lean|lean4)?\s*\n(.*?)\n```",
    __import__("re").DOTALL,
)


def extract_tactic_block(text: str) -> str:
    """Pull the Lean tactics out of an LLM response.

    Applies four steps in order: strip a leading ``<think>`` block, then
    prefer the last fenced code block, then fall back to a single
    surrounding fence, then fall back to the stripped text as-is.

    Parameters
    ----------
    text : str
        Raw text of the model's response.

    Returns
    -------
    str
        The extracted tactic text, stripped of surrounding whitespace.
        Returns ``""`` for a response that opens with an unclosed
        ``<think>`` block (see Notes).

    Notes
    -----
    Step 0 handles a leading ``<think>`` reasoning block. If the (stripped)
    response opens with ``<think>``, this strips through the FIRST
    ``</think>`` tag, plus any whitespace right after it, and continues
    extracting from the remainder using steps 1-3 below.

    An UNCLOSED think block (starts with ``<think>`` but has no matching
    ``</think>`` at all) means the completion was cut off mid-reasoning —
    for example, it hit the max-tokens budget before the model reached an
    answer. Such a block has no recoverable tactic text. This function
    returns ``""`` for it, rather than scoring the raw reasoning ramble as
    a proof attempt. The LeanDojo replay would fail on it regardless, and
    letting it through would pollute ``lean_error`` stats with parse noise
    instead of giving a clean "no answer" signal.

    `smolbench/evals/openai_compat.py` (~line 551) already splits
    ``content`` on the first ``</think>`` client-side, when the server
    returns reasoning and answer concatenated in one string. In practice,
    step 0 here is belt-and-suspenders for text that reaches the extractor
    with the think blob still attached — for example, a provider that
    does not route through that client, or a future regression there. See
    that module's docstring for the primary split point.

    Step 1: if the response contains one or more ```` ```lean ... ``` ````
    (or unlabelled) fenced blocks, this returns the LAST one. Models that
    prefix tactics with reasoning typically put the answer last.

    Step 2: otherwise, this falls back to stripping a single surrounding
    fence (legacy behavior).

    Step 3: otherwise, this returns the stripped text as-is.
    """
    s = text.strip()
    if s.startswith("<think>"):
        close_idx = s.find("</think>")
        if close_idx == -1:
            # Truncated CoT: no closing tag means no tactic text survived
            # to be extracted. Returning "" (rather than, say, the raw
            # blob) keeps this a clean miss instead of a guaranteed-wrong
            # proof attempt polluting lean_error stats. See docstring above.
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

    Notes
    -----
    The system half of the old two-message list now travels separately,
    as the calling `ChatClient`'s per-call `system=` argument (see
    `SYSTEM` above). It is not part of this function's return value.

    The old Anthropic `cache_breakpoint=True` hints are gone along with
    the hand-rolled `Message` type they were attached to. OpenRouter's
    Anthropic-backed models auto-cache stable prompt prefixes without an
    explicit breakpoint.
    """
    return rendered.text + "\n\n" + INSTRUCTION
