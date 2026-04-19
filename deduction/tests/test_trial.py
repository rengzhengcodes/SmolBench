"""Round-trip sanity check on the TrialResult schema."""

from deduction.trial import TrialResult, now_iso


def main() -> None:
    r = TrialResult(
        target_id="ENNReal.le_rpow_one_div_iff",
        file_path="Mathlib/Analysis/SpecialFunctions/Pow/NNReal.lean",
        condition="ext-nodoc-d2",
        context_chars=3789,
        model="stub",
        temperature=0.0,
        k_index=0,
        proof_text="sorry",
        ok=False,
        error="contains sorry",
        tactics_applied=0,
        tokens_in=None,
        tokens_out=None,
        wall_ms=12,
        timestamp=now_iso(),
    )
    d = r.to_json_dict()
    r2 = TrialResult.from_json_dict(d)
    assert r == r2, "round-trip failed"
    print("round-trip ok")
    print(d)


if __name__ == "__main__":
    main()
