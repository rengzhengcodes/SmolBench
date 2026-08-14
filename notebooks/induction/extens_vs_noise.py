"""Focused test: extensional vs noise-padded intensional, per model (21 contrasts).

Both arms are LONG. `extens` is the fully enumerated position -> label listing;
`noise_intens` is the compact rule form padded with whitespace to exactly the
same token count under the model's own tokenizer. So this contrast holds prompt
LENGTH fixed and varies only whether the tokens carry information -- it is the
cleanest available test of "is the extensional arm hard because it is long, or
because enumerated evidence is harder to induce from than a stated rule?"

A significant extens < noise result means length is not the explanation.

Correction discipline
---------------------
These 21 contrasts are a SUBSET of the 210 pre-registered PRIMARY family, and
the primary inference stays at m = 210. Re-correcting at m = 21 after choosing
this subset because it looked interesting is data-dependent family sizing --
the same hazard flagged against `alpha_eq = ALPHA / len(near_ties)` in
MULTIPLICITY_PLAN.md section 3. The m = 21 column is reported as a SENSITIVITY
check only, to show how little the conclusion depends on the choice.

Run:
    uv run --no-project --with numpy --with scipy python notebooks/induction/extens_vs_noise.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from power_analysis import INFOS, MODELS, RESULTS_DIR  # noqa: E402
from paired_analysis import (  # noqa: E402
    aligned, build_primary_contrasts, cmh_unpaired_p, holm, load_marks, mcnemar_exact_p,
)
from significance_report import QUARANTINED, hochberg  # noqa: E402

ALPHA = 0.05


def noncompliance() -> dict:
    """(model, info) -> share of marks with a non-null ``compliance`` value."""
    rx = re.compile(r"^\s*compliance:\s*(\S+)", re.M)
    out = {}
    for model in MODELS:
        for info in INFOS:
            vals = []
            for path in (RESULTS_DIR / f"{model}_{info}").glob("rep_*.yaml"):
                vals += rx.findall(path.read_text())
            out[(model, info)] = (1.0 - vals.count("null") / len(vals)) if vals else float("nan")
    return out


def main() -> None:
    correct, valid = load_marks()
    nc = noncompliance()

    # p-values for the FULL pre-registered family, so the m=210 Holm decision
    # for these 21 is the real one rather than a recomputation on a subset.
    full = []
    for label, key_a, key_b in build_primary_contrasts():
        a, b, sidx = aligned(correct, valid, key_a, key_b, drop_invalid=False)
        full.append((label, key_a, key_b,
                     mcnemar_exact_p(int((a & ~b).sum()), int((~a & b).sum()))))
    p_full = np.array([r[3] for r in full])
    holm_full = holm(p_full, ALPHA)
    full_idx = {(r[1], r[2]): i for i, r in enumerate(full)}

    rows = []
    for model in MODELS:
        ka, kb = (model, "extens"), (model, "noise_intens")
        a, b, sidx = aligned(correct, valid, ka, kb, drop_invalid=False)
        nb, ncd = int((a & ~b).sum()), int((~a & b).sum())
        rows.append(dict(
            model=model, acc_e=a.mean(), acc_n=b.mean(), n=a.size, b=nb, c=ncd,
            disc=(nb + ncd) / max(a.size, 1),
            p=mcnemar_exact_p(nb, ncd),
            p_unp=cmh_unpaired_p(a, b, sidx),
            holm210=bool(holm_full[full_idx[(ka, kb)]]),
            quar=(ka in QUARANTINED or kb in QUARANTINED),
            nc_e=nc[ka], nc_n=nc[kb],
        ))

    p21 = np.array([r["p"] for r in rows])
    h21, hb21 = holm(p21, ALPHA), hochberg(p21, ALPHA)

    print("EXTENSIONAL vs NOISE-PADDED INTENSIONAL, per model")
    print("Both arms token-matched; the contrast isolates INFORMATION from LENGTH.")
    print(f"Paired exact McNemar. n = {min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} "
          f"matched items.\n")
    hdr = (f"{'model':13s} {'extens':>7s} {'noise':>7s} {'disc':>6s} {'b/c':>9s} "
           f"{'p':>10s} {'H210':>5s} {'H21':>4s} {'Hoch21':>7s}  flags")
    print(hdr); print("-" * len(hdr))
    for i, r in enumerate(rows):
        flags = []
        if r["quar"]:
            flags.append("QUARANTINED")
        else:
            for lbl, v in (("extens", r["nc_e"]), ("noise", r["nc_n"])):
                if v >= 0.25:
                    flags.append(f"{lbl} {v:.0%} non-compliant")
        star = lambda ok: " yes " if ok else "  .  "
        print(f"{r['model']:13s} {r['acc_e']:7.3f} {r['acc_n']:7.3f} {r['disc']:6.3f} "
              f"{r['b']:4d}/{r['c']:<4d} {r['p']:10.2e} {star(r['holm210']):>5s} "
              f"{star(h21[i]):>4s} {star(hb21[i]):>7s}  {'; '.join(flags)}")

    usable = [i for i, r in enumerate(rows) if not r["quar"]
              and max(r["nc_e"], r["nc_n"]) < 0.25]
    sig_full = [rows[i] for i in range(len(rows)) if rows[i]["holm210"]]
    sig_clean = [rows[i] for i in usable if rows[i]["holm210"]]

    print(f"\nH210 = Holm over the pre-registered 210-contrast family (PRIMARY inference).")
    print(f"H21 / Hoch21 = Holm / Hochberg over these 21 only -- SENSITIVITY ONLY; "
          f"re-sizing the\n  family to a subset chosen after seeing the data is not a "
          f"valid primary analysis.")
    print(f"  agreement: H210 {sum(r['holm210'] for r in rows)}, H21 {h21.sum()}, "
          f"Hoch21 {hb21.sum()} of 21")

    print(f"\nSIGNIFICANT under the primary (m=210) correction: {len(sig_full)} of 21")
    for r in sig_full:
        d = "noise HIGHER" if r["acc_n"] > r["acc_e"] else "extens HIGHER"
        tag = " [QUARANTINED]" if r["quar"] else (
            " [contaminated]" if max(r["nc_e"], r["nc_n"]) >= 0.25 else "")
        print(f"  {r['model']:13s} {r['acc_e']:.3f} vs {r['acc_n']:.3f}   {d}{tag}")

    print(f"\nOf those, on CLEAN arms (<25% non-compliance, not quarantined): "
          f"{len(sig_clean)}")
    for r in sig_clean:
        d = "noise HIGHER" if r["acc_n"] > r["acc_e"] else "extens HIGHER"
        print(f"  {r['model']:13s} {r['acc_e']:.3f} vs {r['acc_n']:.3f}   {d}   "
              f"p={r['p']:.2e}")
    n_up = sum(1 for r in sig_clean if r["acc_n"] > r["acc_e"])
    print(f"\nDirection among clean significant results: {n_up} noise-higher, "
          f"{len(sig_clean) - n_up} extens-higher.")


if __name__ == "__main__":
    main()
