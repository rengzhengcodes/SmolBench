"""Holm and Hochberg significance report over the PRIMARY contrast family.

Applies both step-down Holm (1979) and step-up Hochberg (1988) at FWER = 0.05 to
the 210 pre-registered PRIMARY contrasts, and reports which results are
significant, in which direction, and where the two procedures disagree.

Test choice
-----------
The headline uses the PAIRED test (exact McNemar on item-matched marks), which
is the correct statistic for this design -- every model answers the same seeds
with byte-identical prompts, and all four info arms at a given seed reuse the
same queries and answers. See PAIRED_ANALYSIS_RESULTS.md. The unpaired
harmonic-stratified CMH that ``power_analysis.py`` plans is reported alongside
for comparison.

Procedure choice
----------------
Holm controls FWER under ARBITRARY dependence and is uniformly more powerful
than single-step Bonferroni. Hochberg is uniformly more powerful than Holm but
requires Simes-type positive dependence (MTP2, Sarkar 1998), which is NOT
verified for this contrast structure -- 210 CMH/McNemar statistics sharing
models, seeds and harmonics. Hochberg is therefore reported as a sensitivity
check, not as the headline: where it rejects strictly more than Holm, those
extra rejections rest on an unverified assumption.

Reporting discipline
--------------------
Two classes of significant result are NOT scientific findings and are labelled
as such rather than silently included:

  * ZERO-ARM contrasts. The `zero` arm is a chance-floor baseline (~0.00-0.03)
    against arms at 0.60-1.00, so these are significant by construction. They
    are a positive control -- their FAILURE would indicate a broken pipeline.
  * QUARANTINED noise lanes. Six `noise_intens` lanes are 30-100% non-compliant
    with the output contract (exaone_32b/33b at acc 0.000 with total generative
    collapse, glm_flash 48.9% empty, min3_8b/14b 100% non-compliant, glm_air
    17.8% empty). Contrasts involving them measure whitespace-padding-induced
    degeneration, not induction.

Run:
    uv run --no-project --with numpy --with scipy python notebooks/induction/significance_report.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from power_analysis import INFOS, MODELS, RESULTS_DIR  # noqa: E402
from paired_analysis import (  # noqa: E402
    aligned,
    build_primary_contrasts,
    cmh_unpaired_p,
    holm,
    load_marks,
    mcnemar_exact_p,
)

ALPHA = 0.05

#: noise_intens lanes quarantined for output-contract collapse -- see the module
#: docstring and PAIRED_ANALYSIS_RESULTS.md's compliance table.
QUARANTINED = {
    ("exaone_32b", "noise_intens"), ("exaone_33b", "noise_intens"),
    ("glm_flash", "noise_intens"), ("glm_air", "noise_intens"),
    ("min3_8b", "noise_intens"), ("min3_14b", "noise_intens"),
}


def hochberg(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Hochberg (1988) step-up rejections at familywise level `alpha`.

    Same critical values as Holm, but stepping UP from the largest p-value:
    let k = max{i : p_(i) <= alpha / (m - i + 1)}; reject the k smallest.
    Uniformly at least as powerful as Holm, but valid only under Simes-type
    positive dependence, not arbitrary dependence.
    """
    m = pvals.size
    order = np.argsort(pvals)
    sorted_p = pvals[order]
    reject = np.zeros(m, dtype=bool)
    for i in range(m - 1, -1, -1):          # i = 0-based rank
        if sorted_p[i] <= alpha / (m - i):
            reject[order[: i + 1]] = True
            break
    return reject


def contaminated_cells(threshold: float = 0.25) -> dict:
    """(model, info) -> non-compliance rate, for cells above `threshold`.

    A contrast touching one of these is statistically significant but
    scientifically ambiguous: the arm may be losing accuracy because the model
    stopped obeying the output contract, not because the task got harder. This
    is the same confound that makes the quarantined noise lanes unusable, at
    lower severity, and it must be visible next to the findings rather than
    discovered later.
    """
    import re
    rx = re.compile(r"^\s*compliance:\s*(\S+)", re.M)
    out = {}
    for model in MODELS:
        for info in INFOS:
            vals = []
            for path in (RESULTS_DIR / f"{model}_{info}").glob("rep_*.yaml"):
                vals += rx.findall(path.read_text())
            if not vals:
                continue
            rate = 1.0 - vals.count("null") / len(vals)
            if rate >= threshold:
                out[(model, info)] = rate
    return out


def classify(label: str, key_a, key_b) -> str:
    """Bucket a contrast for reporting: zero-arm control, quarantined, or real."""
    if key_a in QUARANTINED or key_b in QUARANTINED:
        return "quarantined"
    if key_a[1] == "zero" or key_b[1] == "zero":
        return "zero-control"
    return "finding"


def main() -> None:
    correct, valid = load_marks()
    contrasts = build_primary_contrasts()

    rows = []
    for label, key_a, key_b in contrasts:
        a, b, sidx = aligned(correct, valid, key_a, key_b, drop_invalid=False)
        nb, nc = int((a & ~b).sum()), int((~a & b).sum())
        rows.append(dict(
            label=label, key_a=key_a, key_b=key_b,
            acc_a=a.mean(), acc_b=b.mean(), n=a.size,
            p_paired=mcnemar_exact_p(nb, nc),
            p_unpaired=cmh_unpaired_p(a, b, sidx),
            kind=classify(label, key_a, key_b),
            kind_is_ladder="ladder" in label,
        ))

    p_pair = np.array([r["p_paired"] for r in rows])
    p_unp = np.array([r["p_unpaired"] for r in rows])
    m = len(rows)

    res = {
        ("paired", "Holm"): holm(p_pair, ALPHA),
        ("paired", "Hochberg"): hochberg(p_pair, ALPHA),
        ("unpaired", "Holm"): holm(p_unp, ALPHA),
        ("unpaired", "Hochberg"): hochberg(p_unp, ALPHA),
    }

    print(f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}")
    print(f"Replicate depth: n = {min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} "
          f"matched items per contrast\n")
    print(f"{'test':10s} {'procedure':10s} {'rejected':>9s}  {'uncorrected p<0.05':>19s}")
    print("-" * 54)
    for (test, proc), rej in res.items():
        raw = (p_pair if test == "paired" else p_unp) < ALPHA
        print(f"{test:10s} {proc:10s} {rej.sum():9d}  {raw.sum():19d}")

    hp, hb = res[("paired", "Holm")], res[("paired", "Hochberg")]
    extra = [rows[i] for i in range(m) if hb[i] and not hp[i]]
    print(f"\nHolm vs Hochberg (paired): Hochberg rejects "
          f"{'the same set' if not extra else f'{len(extra)} MORE'}")
    for r in extra:
        print(f"   +{r['label']:52s} p={r['p_paired']:.3e}")

    # ---- the findings, excluding controls and quarantined lanes -------------
    for bucket, title in (
        ("finding", "SIGNIFICANT FINDINGS (Holm, paired)"),
        ("zero-control", "zero-arm positive controls (significant by construction)"),
        ("quarantined", "QUARANTINED lanes (output-contract collapse, NOT findings)"),
    ):
        sel = [r for i, r in enumerate(rows) if hp[i] and r["kind"] == bucket]
        tot = sum(1 for r in rows if r["kind"] == bucket)
        print(f"\n{'=' * 78}\n{title}: {len(sel)} of {tot}\n{'=' * 78}")
        if bucket != "finding":
            if bucket == "zero-control":
                print("  (all arms vs the chance floor; failure here would mean a broken "
                      "pipeline)")
            else:
                print("  (listed so they are not mistaken for scaling results)")
            for r in sorted(sel, key=lambda r: r["p_paired"])[:6]:
                print(f"  {r['label']:54s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}")
            if len(sel) > 6:
                print(f"  ... and {len(sel) - 6} more")
            continue

        contam = contaminated_cells()
        def tag(r):
            hits = [f"{k[0]}/{k[1]} {contam[k]:.0%}" for k in (r["key_a"], r["key_b"])
                    if k in contam]
            return ("   [!] non-compliant: " + "; ".join(hits)) if hits else ""
        ladders = [r for r in sel if r["kind_is_ladder"]]
        infos = [r for r in sel if not r["kind_is_ladder"]]
        print(f"\n-- LADDER contrasts (scaling within a family): {len(ladders)} "
              f"of {sum(1 for r in rows if r['kind'] == 'finding' and r['kind_is_ladder'])}")
        for r in sorted(ladders, key=lambda r: r["p_paired"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            print(f"  {direction} {r['label']:52s} {r['acc_a']:.3f} -> {r['acc_b']:.3f}"
                  f"   p={r['p_paired']:.2e}{tag(r)}")
        print(f"\n-- INFO-ARM contrasts (within one model): {len(infos)} "
              f"of {sum(1 for r in rows if r['kind'] == 'finding' and not r['kind_is_ladder'])}")
        for r in sorted(infos, key=lambda r: r["p_paired"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            print(f"  {direction} {r['label']:52s} {r['acc_a']:.3f} -> {r['acc_b']:.3f}"
                  f"   p={r['p_paired']:.2e}{tag(r)}")
        n_contam = sum(1 for r in sel if tag(r))
        print(f"\n  [!] {n_contam} of {len(sel)} findings touch a cell that is >=25% "
              f"NON-COMPLIANT with the\n      output contract -- significant, but the "
              f"mechanism may be format collapse\n      rather than task difficulty.")

    # ---- what is NOT significant, which is half the story -------------------
    ns = [r for i, r in enumerate(rows) if not hp[i] and r["kind"] == "finding"]
    ceiling = [r for r in ns if min(r["acc_a"], r["acc_b"]) >= 0.95]
    print(f"\n{'=' * 78}\nNOT significant: {len(ns)} of "
          f"{sum(1 for r in rows if r['kind'] == 'finding')} non-control contrasts")
    print(f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)} -- these are "
          f"ties by\n  construction, not underpowered; many have ZERO discordant items, "
          f"where no\n  replicate count can separate them (see the +/-0.20 equivalence "
          f"decision).")


if __name__ == "__main__":
    main()
