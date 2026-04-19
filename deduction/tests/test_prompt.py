"""Prints a sample prompt + runs extract_proof across a handful of cases."""

from deduction.prompt import extract_proof, tactics_only_prompt


def main() -> None:
    p = tactics_only_prompt(
        target_sig="theorem le_inv_iff_mul_le {r p : ℝ≥0} (h : p ≠ 0) : r ≤ p⁻¹ ↔ r * p ≤ 1",
        context_text=(
            "@[simp] theorem mul_inv_cancel (h : a ≠ 0) : a * a⁻¹ = 1\n"
            "\n"
            "theorem mul_comm : ∀ a b : G, a * b = b * a"
        ),
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


if __name__ == "__main__":
    main()
