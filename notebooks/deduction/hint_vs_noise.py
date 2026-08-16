"""Deduction analogue of the induction `extens` vs `noise_intens` contrast.

The question, on both legs, is the same one: **does the model do better because
the context carries INFORMATION, or merely because it is longer?**

  induction:  `extens`  (fully enumerated position -> label listing)
              vs `noise_intens` (the compact rule, whitespace-padded to exactly
              the same TOKEN count under the model's own tokenizer)

  deduction:  `hint:3`  (three real ground-truth proof tactics handed over)
              vs `noise:3` (three JUNK tactics in the same slots)

Both hold the context's size fixed and vary only whether it is informative, so
a significant `hint:3` > `noise:3` says the model is using the content of the
hint rather than responding to its bulk.

Pairing: cells are matched on ``(theorem_id, k)`` WITHIN one model, so each
model is its own control and the two rungs are compared on identical theorems
at identical prefix depth. That makes exact McNemar the right test, as on the
induction leg.

Multiplicity: Holm-Bonferroni over the 21 models at FWER 0.05, matching the
directive for the induction leg. Holm is valid under arbitrary dependence,
which this family needs -- the 21 tests share a theorem set.

Run:
    uv run --no-project --with numpy --with scipy python \
        notebooks/deduction/hint_vs_noise.py --rows-dir <dir>
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from error_bars import holm  # noqa: E402
from power_analysis import (  # noqa: E402
    ALPHA,
    FAMILIES,
    MODELS,
    UNMEASURABLE_VERDICTS,
    mcnemar_exact_p,
)

#: The informative rung and its length-matched uninformative twin.
RUNG_INFO, RUNG_NOISE = "hint:3", "noise:3"


def load_rungs(path: Path, model: str) -> dict:
    """(theorem_id, k) -> {rung: 0/1}, earliest surviving row per cell.

    Applies the same two rules as ``load_joint_cells``: the FIRST row whose
    verdict is measurable wins (a later retry is an independent draw, and
    last-wins would report pass@N as pass@1), and unmeasurable verdicts are
    left ABSENT rather than scored 0.
    """
    out: dict = defaultdict(dict)
    for line in path.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row.get("kind") != "cell" or row.get("replicate_idx", 0) != 0:
            continue
        if row.get("rung") not in (RUNG_INFO, RUNG_NOISE):
            continue
        if row.get("verdict") in UNMEASURABLE_VERDICTS:
            continue
        cell = (row["theorem_id"], row["k"])
        if row["rung"] in out[cell]:
            continue  # earliest surviving attempt already recorded
        out[cell][row["rung"]] = 1 if row.get("verdict") == "success" else 0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows-dir", type=Path, required=True)
    args = ap.parse_args(argv)

    rows = []
    for model in MODELS:
        pairs = load_rungs(args.rows_dir / model / "verified_rows.jsonl", model)
        both = [v for v in pairs.values() if RUNG_INFO in v and RUNG_NOISE in v]
        info = np.array([v[RUNG_INFO] for v in both], dtype=bool)
        noise = np.array([v[RUNG_NOISE] for v in both], dtype=bool)
        b = int((info & ~noise).sum())   # hint solved, noise not
        c = int((~info & noise).sum())   # noise solved, hint not
        rows.append(dict(model=model, n=info.size, acc_i=info.mean(),
                         acc_n=noise.mean(), b=b, c=c,
                         p=mcnemar_exact_p(b, c)))

    rej = holm(np.array([r["p"] for r in rows]), ALPHA)

    print("DEDUCTION: hint:3 (informative) vs noise:3 (length-matched junk), per model")
    print("Paired exact McNemar on cells matched by (theorem, k) within each model.")
    print(f"Holm-Bonferroni over m = {len(rows)} models at FWER {ALPHA}.\n")
    hdr = (f"{'model':30s} {'n':>5s} {'hint:3':>7s} {'noise:3':>8s} {'diff':>7s} "
           f"{'b/c':>9s} {'p':>10s} {'Holm':>5s}")
    print(hdr)
    print("-" * len(hdr))
    order = [m for fam in FAMILIES.values() for m in fam]
    idx = {r["model"]: i for i, r in enumerate(rows)}
    for m in order:
        r = rows[idx[m]]
        print(f"{r['model']:30s} {r['n']:5d} {r['acc_i']:7.3f} {r['acc_n']:8.3f} "
              f"{r['acc_i'] - r['acc_n']:+7.3f} {r['b']:4d}/{r['c']:<4d} "
              f"{r['p']:10.2e} {' yes ' if rej[idx[m]] else '  .  '}")

    sig = [rows[i] for i in range(len(rows)) if rej[i]]
    up = [r for r in sig if r["acc_i"] > r["acc_n"]]
    print(f"\nSignificant under Holm: {len(sig)} of {len(rows)}")
    print(f"  hint:3 HIGHER (information helps): {len(up)}")
    print(f"  noise:3 HIGHER:                    {len(sig) - len(up)}")

    # A null is uninterpretable without the effect it could have caught, so
    # report the MINIMUM DETECTABLE EFFECT rather than leaving the reader to
    # assume the test was well powered. For each model, find the most balanced
    # discordant split that would still clear Holm's FIRST (strictest)
    # threshold at its observed discordant total.
    print(f"\n{'-' * 78}\nMINIMUM DETECTABLE EFFECT -- what this null actually rules out")
    print(f"{'-' * 78}")
    print(f"At each model's OBSERVED discordant total, the most balanced split "
          f"that would\nstill clear Holm's strictest step (alpha/{len(rows)} = "
          f"{ALPHA / len(rows):.2e}), in accuracy points.\n")
    print(f"{'model':30s} {'disc':>5s} {'needed split':>13s} {'= MDE':>7s} "
          f"{'observed':>9s}")
    print("-" * 70)
    mdes = []
    thresh = ALPHA / len(rows)
    for m in order:
        r = rows[idx[m]]
        nd = r["b"] + r["c"]
        need = None
        for k in range(nd // 2, -1, -1):
            if mcnemar_exact_p(nd - k, k) <= thresh:
                need = k
                break
        if need is None:
            print(f"{m:30s} {nd:5d} {'IMPOSSIBLE':>13s} {'--':>7s} "
                  f"{r['acc_i'] - r['acc_n']:+9.3f}")
            continue
        mde = (nd - 2 * need) / r["n"]
        mdes.append(mde)
        print(f"{m:30s} {nd:5d} {f'{nd - need}/{need}':>13s} {mde:7.3f} "
              f"{r['acc_i'] - r['acc_n']:+9.3f}")
    if mdes:
        print(f"\nMedian MDE: {np.median(mdes):.3f} accuracy points. Largest "
              f"observed |difference|: "
              f"{max(abs(r['acc_i'] - r['acc_n']) for r in rows):.3f}.")
        print("So this null rules out LARGE information effects, not small ones "
              "-- see the\ncaveat in FAMILY_LADDER_ANALYSIS_2026-08-16.md.")
    n_neg = sum(1 for r in rows if r["acc_i"] < r["acc_n"])
    n_pos = sum(1 for r in rows if r["acc_i"] > r["acc_n"])
    print(f"\nDirection of the point estimates, ignoring significance: "
          f"{n_pos} favour hint:3,\n  {n_neg} favour noise:3, "
          f"{len(rows) - n_pos - n_neg} exactly tied -- consistent with no "
          f"effect rather than\n  a real effect this design cannot resolve.")
    print(f"\nNot significant: {len(rows) - len(sig)} -- listed so a null is not "
          f"mistaken for an untested contrast:")
    for i, r in enumerate(rows):
        if not rej[i]:
            print(f"  {r['model']:30s} {r['acc_i']:.3f} vs {r['acc_n']:.3f}  "
                  f"p={r['p']:.2e}  (discordant {r['b'] + r['c']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
