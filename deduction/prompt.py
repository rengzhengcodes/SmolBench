"""
Prompt templates + matching extractors for deduction trials.

Two model families supported so far:
- `tactics_only_prompt` + `extract_proof` — generic instruct models. Asks for
  just the tactic sequence; extracts from markdown fences and strips a leading
  `by` keyword.
- `dsprover_prompt` + `extract_proof_dsprover` — matches the DeepSeek-Prover-V2
  training format. The model is asked to complete a Lean 4 theorem given its
  header with `:= by\\n  sorry`; it emits the full theorem inside a ```lean4
  fence, and we pull out the tactic body.

Selecting the pair per model is the caller's job (see run_pilot's
`SB_PROMPT_TYPE` env var).
"""

import re

_FENCE_RE = re.compile(r"```(?:lean4?)?\s*\n(.*?)\n```", re.DOTALL)
_LEAN4_FENCE_RE = re.compile(r"```(?:lean4?)\s*\n(.*?)\n```", re.DOTALL)
_BY_RE = re.compile(r":=\s*by\b", re.IGNORECASE)


def tactics_only_prompt(target_sig: str, context_text: str) -> str:
    """Build a prompt asking the model to emit tactics only."""
    return (
        "You are completing a Lean 4 proof.\n"
        "\n"
        "Available declarations (you may use any of these in the proof):\n"
        f"{context_text}\n"
        "\n"
        "Target theorem:\n"
        f"{target_sig}\n"
        "\n"
        "Write the proof using Lean 4 tactics. Output one tactic per line. "
        "Do not include `theorem`, `:= by`, or any explanation — output only "
        "the tactic sequence.\n"
        "\n"
        "Proof:\n"
    )


def extract_proof(raw: str) -> str:
    """Pull a proof out of a raw LLM response.

    - If the output is wrapped in a ```lean ... ``` fence, take the fence body.
    - Strip a leading `by` token if the model emitted one despite the instruction.
    - Strip leading/trailing whitespace.
    """
    match = _FENCE_RE.search(raw)
    if match:
        raw = match.group(1)
    raw = raw.strip()
    if raw.startswith("by\n"):
        raw = raw[3:].lstrip("\n")
    elif raw.startswith("by "):
        raw = raw[3:]
    return raw.strip()


def dsprover_prompt(target_sig: str, context_text: str) -> str:
    """Prompt DeepSeek-Prover-V2 to complete a theorem. Matches the format the
    model was trained on: a partial Lean 4 declaration ending in `:= by\\n  sorry`
    inside a ```lean4 fence."""
    return (
        "Complete the following Lean 4 proof. Replace the `sorry` with tactics "
        "that close the goal.\n"
        "\n"
        "You may use any of these lemmas in the proof (they are already in scope):\n"
        f"{context_text}\n"
        "\n"
        "```lean4\n"
        f"{target_sig} := by\n"
        "  sorry\n"
        "```\n"
        "\n"
        "First, outline the main proof steps briefly. Then write the complete "
        "Lean 4 proof inside a ```lean4 code block.\n"
    )


def extract_proof_dsprover(raw: str) -> str:
    """Pull the tactic body from a DS-Prover output.

    The model typically emits a plan followed by a ```lean4 ... ``` block
    containing the full theorem declaration `... := by <tactics>`. We take
    the LAST such block (the model's final answer after any intermediate
    sketches), find `:= by`, and return everything after it.

    Falls back to the generic `extract_proof` if no `:= by` pattern is found
    — that handles term-mode completions (`:= <expression>`) by yielding the
    whole block for the verifier to reject rather than silently dropping.
    """
    fences = _LEAN4_FENCE_RE.findall(raw)
    if not fences:
        # No lean4-tagged fence — fall back to generic extraction
        return extract_proof(raw)
    block = fences[-1]  # prefer the final answer over intermediate sketches
    m = _BY_RE.search(block)
    if m is None:
        # Term-mode proof — return empty so verifier reports parse error on
        # an empty tactic list rather than trying to run `:= <term>` as a tactic
        return ""
    return block[m.end():].strip("\n").strip()
