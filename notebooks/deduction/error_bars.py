"""Block-bootstrap error bars for the deduction leg of the family-ladder study.

Deliverable
-----------
Accurate uncertainty on (i) each of the 21 checkpoints' pass@1 rate and (ii)
every pre-registered contrast's paired difference, with the number of bootstrap
resamples CHOSEN BY MEASUREMENT rather than asserted (``--mode sweep``).

Why the resampling unit is a THEOREM, not a cell
------------------------------------------------
A cell is one ``(theorem_id, k, prompt_rung)`` triple, and each theorem
contributes several cells that share a ground truth and a proof prefix. Those
cells are not independent: a theorem the model simply cannot do fails at every
rung, and one it finds easy succeeds at every rung. Resampling CELLS would treat
each as fresh information and understate the interval; resampling whole THEOREM
BLOCKS with replacement preserves the within-theorem correlation, which is the
standard cluster/block bootstrap (Davison & Hinkley 1997, ch. 3; Field & Welsh
2007 for the clustered case).

The effective sample size is therefore the number of THEOREM BLOCKS (216 in the
21-way paired set), NOT the 707 cells. That distinction is the whole reason the
intervals below are wider than a naive binomial on 707 would give, and it is
reported next to every figure so nobody re-derives a tighter number.

Interval method
---------------
BCa (bias-corrected and accelerated; Efron 1987), with the acceleration from a
jackknife over theorem blocks. Percentile intervals are reported alongside
because BCa is the one that changes materially for the near-floor lanes -- at
``nemotron-3-nano-30b-a3b``'s 0.041 the bootstrap distribution is right-skewed
and a percentile interval is visibly mis-centred. Where BCa's bias-correction is
undefined (every resample identical, which happens only at a degenerate 0.000)
the code falls back to percentile and says so rather than emitting a silent NaN.

Pairing
-------
Contrasts run on the 21-way paired cell set so that every contrast rests on the
SAME cells and the differences are commensurable. This costs almost nothing
here: the 21-way intersection is 707 of a lane's 712 measurable cells (99.3%),
because deepseek-v3.1's 415 exception cells were repaired before the snapshot.
Per-lane marginal rates over each lane's own 712 are printed alongside, and the
two differ by at most 0.002.

Row rules are NOT re-derived here -- ``load_joint_cells`` already implements
earliest-surviving-row-per-cell and the unmeasurable-verdict exclusion, with
tests. See its docstring and ``notebooks/CONTAMINATION_INVENTORY_2026-08-15.md``.

Run:
    uv run --no-project --with numpy --with scipy python \
        notebooks/deduction/error_bars.py --rows-dir <dir> --mode sweep
    uv run --no-project --with numpy --with scipy python \
        notebooks/deduction/error_bars.py --rows-dir <dir> --mode report -B 20000
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_analysis import (  # noqa: E402
    ALPHA,
    FAMILIES,
    MODELS,
    build_cross_family_contrasts,
    build_within_family_contrasts,
    load_joint_cells,
    mcnemar_exact_p,
)

#: Resample counts swept by ``--mode sweep``. Each runs on an INDEPENDENT RNG
#: stream so the drift between them measures Monte-Carlo error, not a shared
#: seed's luck.
B_GRID = (1_000, 2_000, 5_000, 10_000, 20_000)

#: Drift below this (in accuracy points) is smaller than anything the write-up
#: interprets -- rates are reported to 3 decimals, so half a thousandth on an
#: interval endpoint is invisible.
DRIFT_TOL = 0.0005


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Holm (1979) step-down rejections at familywise level `alpha`.

    Valid under ARBITRARY dependence between the test statistics, which is what
    this family needs: the 21 ladder contrasts share cells and models, and no
    positive-dependence structure has been established for them.
    """
    m = pvals.size
    order = np.argsort(pvals)
    reject = np.zeros(m, dtype=bool)
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


def block_matrix(models: list[str], blocks: dict) -> tuple[np.ndarray, np.ndarray]:
    """Flatten `blocks` into per-theorem success/count arrays.

    Returns
    -------
    (succ, size)
        ``succ`` is ``(n_theorems, n_models)`` -- successes by theorem block;
        ``size`` is ``(n_theorems,)`` -- cells in that block. Resampling rows of
        these two together IS the block bootstrap: a theorem is drawn whole,
        carrying every rung's cell and its own cell count.
    """
    thms = sorted(blocks)
    succ = np.zeros((len(thms), len(models)), dtype=np.int32)
    size = np.zeros(len(thms), dtype=np.int32)
    for i, thm in enumerate(thms):
        cells = blocks[thm]
        size[i] = len(cells)
        for j, model in enumerate(models):
            succ[i, j] = sum(cellmap[model] for cellmap in cells.values())
    return succ, size


def _bca_bounds(theta_star: np.ndarray, theta_hat: float, jack: np.ndarray,
                alpha: float) -> tuple[float, float, bool]:
    """BCa interval endpoints; returns (lo, hi, used_percentile_fallback)."""
    lo_pct, hi_pct = np.percentile(theta_star, [100 * alpha / 2,
                                                100 * (1 - alpha / 2)])
    prop = float(np.mean(theta_star < theta_hat))
    if prop <= 0.0 or prop >= 1.0:
        return float(lo_pct), float(hi_pct), True  # z0 undefined -> percentile
    z0 = norm.ppf(prop)
    jbar = jack.mean()
    num = float(np.sum((jbar - jack) ** 3))
    den = 6.0 * float(np.sum((jbar - jack) ** 2)) ** 1.5
    a = num / den if den > 0 else 0.0
    out = []
    for z in (norm.ppf(alpha / 2), norm.ppf(1 - alpha / 2)):
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        out.append(float(np.percentile(theta_star, 100 * norm.cdf(adj))))
    return out[0], out[1], False


def bootstrap_stats(succ: np.ndarray, size: np.ndarray, B: int, seed: int,
                    alpha: float = 0.05) -> dict:
    """Block-bootstrap marginal rates and all pairwise paired differences.

    One resample draws ``n_theorems`` theorem indices WITH REPLACEMENT and
    recomputes every model's rate as ``sum(successes) / sum(cells)`` over the
    drawn blocks -- a ratio estimator, because a resample's total cell count
    varies with which theorems were drawn.
    """
    n_thm, n_mod = succ.shape
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_thm, size=(B, n_thm))

    # (B, n_models) resampled successes and (B,) resampled cell totals.
    star_succ = succ[idx].sum(axis=1)
    star_size = size[idx].sum(axis=1)[:, None]
    star_rate = star_succ / star_size

    # Jackknife over theorem blocks for the BCa acceleration.
    tot_succ, tot_size = succ.sum(axis=0), size.sum()
    jack = (tot_succ - succ) / (tot_size - size)[:, None]  # (n_thm, n_models)

    theta_hat = tot_succ / tot_size
    marg = {}
    for j in range(n_mod):
        lo, hi, fb = _bca_bounds(star_rate[:, j], float(theta_hat[j]),
                                 jack[:, j], alpha)
        p_lo, p_hi = np.percentile(star_rate[:, j],
                                   [100 * alpha / 2, 100 * (1 - alpha / 2)])
        marg[j] = dict(rate=float(theta_hat[j]), lo=lo, hi=hi,
                       pct_lo=float(p_lo), pct_hi=float(p_hi),
                       se=float(star_rate[:, j].std(ddof=1)), fallback=fb)
    return dict(star_rate=star_rate, jack=jack, theta_hat=theta_hat,
                marginal=marg, alpha=alpha)


def diff_ci(bs: dict, ja: int, jb: int) -> dict:
    """BCa interval for the PAIRED difference rate(b) - rate(a).

    Differenced INSIDE each resample, so the two models' shared theorem draw
    cancels. That is the point of pairing: the difference's interval is much
    tighter than the two marginals' intervals would suggest, because a resample
    that draws hard theorems lowers both models together.
    """
    star = bs["star_rate"][:, jb] - bs["star_rate"][:, ja]
    hat = float(bs["theta_hat"][jb] - bs["theta_hat"][ja])
    jack = bs["jack"][:, jb] - bs["jack"][:, ja]
    lo, hi, fb = _bca_bounds(star, hat, jack, bs["alpha"])
    return dict(diff=hat, lo=lo, hi=hi, se=float(star.std(ddof=1)), fallback=fb)


def paired_mcnemar(models: list[str], blocks: dict, a: str, b: str) -> tuple:
    """Discordant counts and exact McNemar p over all paired cells."""
    ia, ib = models.index(a), models.index(b)
    nb = nc = 0
    for cells in blocks.values():
        for cellmap in cells.values():
            va, vb = cellmap[models[ia]], cellmap[models[ib]]
            if va and not vb:
                nb += 1
            elif vb and not va:
                nc += 1
    return nb, nc, mcnemar_exact_p(nb, nc)


def load(rows_dir: Path) -> tuple:
    files = [rows_dir / m / "verified_rows.jsonl" for m in MODELS]
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"missing row files: {[str(f) for f in missing]}")
    return load_joint_cells(files, models=tuple(MODELS))


def mode_sweep(succ: np.ndarray, size: np.ndarray, models: list[str]) -> None:
    """Measure Monte-Carlo drift across B, so B is chosen rather than asserted."""
    print(f"Resample-count sweep -- {succ.shape[0]} theorem blocks, "
          f"{int(size.sum())} cells, {len(models)} models")
    print("Each B runs on an INDEPENDENT RNG stream; drift = max |endpoint "
          "change| vs the\nnext larger B, over all 21 marginal BCa intervals.\n")
    print(f"{'B':>8s} {'max drift (pts)':>16s} {'median drift':>14s} "
          f"{'worst lane':>28s}")
    print("-" * 72)
    prev = None
    for k, B in enumerate(B_GRID):
        bs = bootstrap_stats(succ, size, B, seed=1000 + k)
        cur = np.array([[bs["marginal"][j]["lo"], bs["marginal"][j]["hi"]]
                        for j in range(len(models))])
        if prev is not None:
            d = np.abs(cur - prev)
            worst = models[int(np.argmax(d.max(axis=1)))]
            print(f"{B:8d} {d.max():16.5f} {np.median(d):14.5f} {worst:>28s}")
        else:
            print(f"{B:8d} {'(baseline)':>16s} {'':>14s} {'':>28s}")
        prev = cur
    print(f"\nTolerance: {DRIFT_TOL} pts (rates are reported to 3 decimals, so "
          f"drift below\nhalf a thousandth cannot change a printed figure).")


def mode_report(succ, size, models, blocks, per_lane, B, out_json) -> None:
    bs = bootstrap_stats(succ, size, B, seed=20260816)
    n_thm = succ.shape[0]
    n_cells = int(size.sum())

    print("=" * 92)
    print("DEDUCTION LEG -- pass@1 with block-bootstrap 95% CIs")
    print("=" * 92)
    print(f"Resampling unit: THEOREM BLOCK. n = {n_thm} blocks "
          f"({n_cells} cells, {n_cells / n_thm:.1f} cells per block).")
    print(f"B = {B:,} resamples, BCa intervals (percentile shown for contrast).")
    print("The effective sample size is 216 THEOREMS, not 707 cells -- see the "
          "module docstring.\n")

    print(f"{'model':30s} {'pass@1':>7s} {'95% BCa':>17s} {'width':>7s} "
          f"{'percentile':>17s} {'own-712':>8s}")
    print("-" * 92)
    order = [m for fam in FAMILIES.values() for m in fam]
    for m in order:
        j = models.index(m)
        r = bs["marginal"][j]
        flag = " *pct" if r["fallback"] else ""
        print(f"{m:30s} {r['rate']:7.3f} [{r['lo']:.3f}, {r['hi']:.3f}] "
              f"{r['hi'] - r['lo']:7.3f} [{r['pct_lo']:.3f}, {r['pct_hi']:.3f}] "
              f"{per_lane.get(m, float('nan')):8.3f}{flag}")

    naive = np.sqrt(bs["theta_hat"] * (1 - bs["theta_hat"]) / n_cells) * 1.96 * 2
    boot_w = np.array([bs["marginal"][j]["hi"] - bs["marginal"][j]["lo"]
                       for j in range(len(models))])
    print(f"\nDesign effect: block-bootstrap intervals are "
          f"{np.median(boot_w / naive):.2f}x (median) the width a naive binomial "
          f"on {n_cells}\n  independent cells would give -- range "
          f"{np.min(boot_w / naive):.2f}x to {np.max(boot_w / naive):.2f}x. "
          f"Treating cells as independent\n  would overstate precision by that "
          f"factor.")

    results = {"n_theorem_blocks": n_thm, "n_cells": n_cells, "B": B,
               "marginals": {m: bs["marginal"][models.index(m)] for m in models},
               "contrasts": {}}

    for tier, contrasts, corrected in (
        ("PRIMARY -- within-family ladder", build_within_family_contrasts(), True),
        ("SECONDARY -- cross-family, size-matched", build_cross_family_contrasts(), False),
    ):
        rows = []
        for label, a, b in contrasts:
            ci = diff_ci(bs, models.index(a), models.index(b))
            nb, nc, p = paired_mcnemar(models, blocks, a, b)
            rows.append((label, a, b, ci, nb, nc, p))
        pv = np.array([r[6] for r in rows])
        rej = holm(pv) if corrected else np.zeros(len(rows), dtype=bool)

        print(f"\n{'=' * 92}\n{tier}: {len(rows)} contrasts\n{'=' * 92}")
        if corrected:
            print("Holm-Bonferroni at FWER 0.05 over these 21 (arbitrary "
                  "dependence).\n")
        print(f"{'contrast':52s} {'diff':>7s} {'95% BCa':>17s} {'b/c':>10s} "
              f"{'Holm':>5s}")
        print("-" * 92)
        for (label, a, b, ci, nb, nc, p), ok in zip(rows, rej):
            mark = " yes " if ok else ("  .  " if corrected else "  -  ")
            crosses = "" if (ci["lo"] > 0 or ci["hi"] < 0) else "  (CI spans 0)"
            short = label if len(label) <= 52 else label[:49] + "..."
            print(f"{short:52s} {ci['diff']:+7.3f} [{ci['lo']:+.3f}, "
                  f"{ci['hi']:+.3f}] {nb:4d}/{nc:<5d} {mark}{crosses}")
            results["contrasts"][label] = dict(
                model_a=a, model_b=b, **ci, b=nb, c=nc, p=p, holm=bool(ok))

        agree = sum(1 for (_, _, _, ci, _, _, _), ok in zip(rows, rej)
                    if ok == (ci["lo"] > 0 or ci["hi"] < 0))
        if corrected:
            print(f"\nHolm and the uncorrected CI agree on {agree}/{len(rows)}. "
                  f"They are DIFFERENT questions:\n  the CI is uncorrected and "
                  f"two-sided per contrast; Holm controls the familywise error "
                  f"over all 21.")

    if out_json:
        Path(out_json).write_text(json.dumps(results, indent=2, default=float))
        print(f"\nwrote {out_json}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows-dir", type=Path, required=True,
                    help="directory of <model>/verified_rows.jsonl")
    ap.add_argument("--mode", choices=("sweep", "report"), default="report")
    ap.add_argument("-B", type=int, default=20_000)
    ap.add_argument("--out-json", type=Path, default=None)
    args = ap.parse_args(argv)

    models, blocks, rungs = load(args.rows_dir)
    succ, size = block_matrix(models, blocks)

    per_lane = {}
    for m in MODELS:
        _, lb, _ = load_joint_cells([args.rows_dir / m / "verified_rows.jsonl"],
                                    models=(m,))
        tot = sum(len(c) for c in lb.values())
        hit = sum(cm[m] for c in lb.values() for cm in c.values())
        per_lane[m] = hit / tot

    if args.mode == "sweep":
        mode_sweep(succ, size, models)
    else:
        mode_report(succ, size, models, blocks, per_lane, args.B, args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
