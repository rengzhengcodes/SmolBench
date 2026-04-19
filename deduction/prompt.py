"""
Prompt template for deduction trials and a lightweight extractor for the
model's output. One template for now; iterate if a specific model misbehaves.

The instruction asks the model for just the tactic sequence (no `theorem`,
no `:= by`, no prose) so the output is directly feedable to
`deduction.verifier.verify`. `extract_proof` tolerates a few common deviations
(markdown code fences, a leading `by`) without trying to be a full parser.
"""

import re

_FENCE_RE = re.compile(r"```(?:lean4?)?\s*\n(.*?)\n```", re.DOTALL)


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


if __name__ == "__main__":
    p = tactics_only_prompt(
        target_sig="theorem le_inv_iff_mul_le {r p : ℝ≥0} (h : p ≠ 0) : r ≤ p⁻¹ ↔ r * p ≤ 1",
        context_text="@[simp] theorem mul_inv_cancel (h : a ≠ 0) : a * a⁻¹ = 1\n\ntheorem mul_comm : ∀ a b : G, a * b = b * a",
    )
    print("=== PROMPT ===")
    print(p)

    cases = [
        "  intro h\n  exact h",
        "by\n  intro h\n  exact h",
        "```lean\nintro h\nexact h\n```",
        "```lean4\nby\n  intro h\n  exact h\n```",
        "  Sure! Here's the proof:\n```\nintro h\nexact h\n```",
    ]
    print("\n=== EXTRACT CASES ===")
    for c in cases:
        print(f"raw:       {c!r}")
        print(f"extracted: {extract_proof(c)!r}")
        print()
