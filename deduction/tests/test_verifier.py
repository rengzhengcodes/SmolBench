"""Smoke-test verify() against Dojo: ground truth passes, wrong proofs fail."""

from deduction.verifier import verify


def main() -> None:
    FILE = "Mathlib/Data/NNReal/Basic.lean"
    NAME = "NNReal.le_inv_iff_mul_le"
    GT = "rw [← mul_le_mul_left (pos_iff_ne_zero.2 h), mul_inv_cancel h, mul_comm]"

    cases = [
        ("ground-truth (str)", GT, True),
        ("ground-truth (list)", [GT], True),
        ("wrong proof rfl", "rfl", False),
        ("syntax error", "this is not valid lean", False),
        ("empty proof", "", False),
    ]
    for name, proof, expected in cases:
        r = verify(FILE, NAME, proof)
        print(f"{name:25s}: ok={r.ok}  tactics_applied={r.tactics_applied}  "
              f"{'PASS' if r.ok == expected else 'FAIL'}")
        assert r.ok == expected, f"{name}: expected ok={expected}, got {r.ok}: {r.error}"

    print("\nAll cases behaved as expected.")


if __name__ == "__main__":
    main()
