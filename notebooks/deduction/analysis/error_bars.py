"""Block-bootstrap error bars for deduction pass@1 and paired contrasts.

Resample theorem blocks because their cells share a proof prefix. BCa falls back to percentile for a degenerate bias correction; both are printed.
The PRIMARY test is block sign-flip; cell-level McNemar is descriptive because it ignores clustering.
``lane_outcomes`` grades through ``power_analysis.grade_verdicts``, shared with
``load_joint_cells`` and ``hint_vs_noise.load_rungs``; only denominator and recovery schemas live here.
A no-survivor cell scores 0 when another lane measured it; dropping makes denominators model-dependent and rewards a broken verifier.
"""

import argparse
import functools
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rows_source  # noqa: E402
from power_analysis import (  # noqa: E402; noqa: E402  # pylint: disable=import-error
    ALPHA,
    FAMILIES,
    MODELS,
    Q_SECONDARY,
    apply_corrections,
    benjamini_hochberg,
    build_cross_family_contrasts,
    build_within_family_contrasts,
    grade_verdicts,
    mcnemar_exact_p,
    pooled_discordant_counts,
    reject_unverified_verdicts,
)

# apply_corrections lives in _power_common but reaches here via power_analysis,
# whose import inserts ``notebooks/`` into sys.path.

#: 1/(B+1) is below Holm's 0.05/21 step, so the resolution floor decides no rejection.
B_SIGNFLIP = 1_000_000

#: Fixed seed keeps reports byte-reproducible from the same rows.
SIGNFLIP_SEED = 20260821

#: Independent streams make sweep drift measure Monte-Carlo error, not seed luck.
B_GRID = (1_000, 5_000, 20_000, 50_000, 100_000, 200_000, 500_000)

#: Batching bounds peak memory to ``CHUNK * n_theorems * n_models * 4`` bytes.
CHUNK = 2_000

#: 0.0005 cannot change a rate printed to 3 decimals.
DRIFT_TOL = 0.0005


def _cost(c: dict[str, Any], field: str) -> float | None:
    """Points the count-as-failure rule removes, or None where the drop rate is undefined."""
    return None if c[field] is None else 100 * (c[field] - c[f"{field[:-5]}_caf"])


def _fmt(value: float | None, width: int) -> str:
    return f"{value:{width}.3f}" if value is not None else f"{'n/a':>{width}}"


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Compute Holm step-down rejections.

    Delegates to ``_power_common.apply_corrections``; ties at the 1/(B+1) floor
    do not affect Holm because its stopping rule depends on sorted values.

    Parameters
    ----------
    pvals : np.ndarray
    alpha : float, optional

    Returns
    -------
    np.ndarray
        Rejection mask in input order.
    """
    return apply_corrections(np.atleast_2d(np.asarray(pvals, float)), alpha)["Holm"][0]


def block_matrix(models: list[str], blocks: dict) -> tuple[np.ndarray, np.ndarray]:
    """Flatten theorem blocks into arrays.

    Parameters
    ----------
    models : list[str]
    blocks : dict

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Successes and per-block cell counts in model/sorted-theorem order; blocks stay whole.
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


def _bca_bounds(
    theta_star: np.ndarray, theta_hat: float, jack: np.ndarray, alpha: float
) -> tuple[float, float, bool]:
    """Compute BCa interval endpoints.

    Parameters
    ----------
    theta_star : np.ndarray
    theta_hat : float
    jack : np.ndarray
        One value per theorem block.
    alpha : float

    Returns
    -------
    tuple[float, float, bool]
        Lower, upper, and percentile-fallback flag for undefined z0.
    """
    lo_pct, hi_pct = np.percentile(theta_star, [100 * alpha / 2, 100 * (1 - alpha / 2)])
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


def bootstrap_stats(
    succ: np.ndarray, size: np.ndarray, B: int, seed: int, alpha: float = 0.05
) -> dict:
    """Compute block-bootstrap marginal rates and BCa intervals.

    Each resample is a ratio estimator because its cell count varies with the block draw.

    Parameters
    ----------
    succ : np.ndarray
    size : np.ndarray
    B : int
    seed : int
    alpha : float, optional

    Returns
    -------
    dict
        Bootstrap arrays and marginal summaries; `star_rate` retains shared draws for `diff_ci`.
    """
    n_thm, n_mod = succ.shape
    rng = np.random.default_rng(seed)

    # Chunking avoids a roughly 90-GB intermediate at B=500k.
    star_rate = np.empty((B, n_mod), dtype=np.float64)
    done = 0
    while done < B:
        chunk = min(CHUNK, B - done)
        idx = rng.integers(0, n_thm, size=(chunk, n_thm))
        star_rate[done : done + chunk] = (
            succ[idx].sum(axis=1) / size[idx].sum(axis=1)[:, None]
        )
        done += chunk

    # The BCa acceleration jackknifes theorem blocks.
    tot_succ, tot_size = succ.sum(axis=0), size.sum()
    jack = (tot_succ - succ) / (tot_size - size)[:, None]  # (n_thm, n_models)

    theta_hat = tot_succ / tot_size
    marg = {}
    for j in range(n_mod):
        lo, hi, fb = _bca_bounds(
            star_rate[:, j], float(theta_hat[j]), jack[:, j], alpha
        )
        p_lo, p_hi = np.percentile(
            star_rate[:, j], [100 * alpha / 2, 100 * (1 - alpha / 2)]
        )
        marg[j] = {
            "rate": float(theta_hat[j]),
            "lo": lo,
            "hi": hi,
            "pct_lo": float(p_lo),
            "pct_hi": float(p_hi),
            "se": float(star_rate[:, j].std(ddof=1)),
            "fallback": fb,
        }
    return {
        "star_rate": star_rate,
        "jack": jack,
        "theta_hat": theta_hat,
        "marginal": marg,
        "alpha": alpha,
    }


def diff_ci(bs: dict, ja: int, jb: int) -> dict:
    """Compute the paired BCa interval for rate(b) - rate(a).

    Differencing within each resample cancels the shared theorem draw.

    Parameters
    ----------
    bs : dict
    ja : int
    jb : int

    Returns
    -------
    dict
        Difference, BCa bounds, standard error, and fallback flag.
    """
    star = bs["star_rate"][:, jb] - bs["star_rate"][:, ja]
    hat = float(bs["theta_hat"][jb] - bs["theta_hat"][ja])
    jack = bs["jack"][:, jb] - bs["jack"][:, ja]
    lo, hi, fb = _bca_bounds(star, hat, jack, bs["alpha"])
    return {
        "diff": hat,
        "lo": lo,
        "hi": hi,
        "se": float(star.std(ddof=1)),
        "fallback": fb,
    }


def paired_mcnemar(blocks: dict, a: str, b: str) -> tuple:
    """Compute discordant counts and exact paired-cell McNemar p.

    This descriptive statistic assumes independent cells and is never inferential.

    Parameters
    ----------
    blocks : dict
        Paired cell verdicts by theorem.
    a : str
    b : str

    Returns
    -------
    tuple
        Discordant counts and two-sided p-value.
    """
    nb, nc = pooled_discordant_counts(blocks, a, b)
    return nb, nc, mcnemar_exact_p(nb, nc)


def block_signflip_p(
    succ: np.ndarray,
    models: list[str],
    contrasts: list,
    B: int = B_SIGNFLIP,
    seed: int = SIGNFLIP_SEED,
    chunk: int = 2_000,
) -> np.ndarray:
    """Compute one block sign-flip p-value per contrast.

    The +1 correction keeps the permutation p-value valid at finite B.

    Parameters
    ----------
    succ : np.ndarray
    models : list[str]
    contrasts : list
        ``(label, a, b)`` triples sharing sign draws to retain family dependence.
    B : int, optional
    seed : int, optional
    chunk : int, optional

    Returns
    -------
    np.ndarray
        One p-value per contrast.
    """
    n_thm = succ.shape[0]
    jmap = {m: j for j, m in enumerate(models)}
    diff = np.empty((n_thm, len(contrasts)), dtype=np.float64)
    for ci, (_label, a, b) in enumerate(contrasts):
        diff[:, ci] = succ[:, jmap[b]] - succ[:, jmap[a]]
    observed = np.abs(diff.sum(axis=0))
    rng = np.random.default_rng(seed)
    count = np.zeros(len(contrasts))
    done = 0
    while done < B:
        take = min(chunk, B - done)
        eps = rng.integers(0, 2, size=(take, n_thm)).astype(np.float64) * 2 - 1
        # Tolerance keeps the observed integer sum, carried as float, counted.
        count += (np.abs(eps @ diff) >= observed - 1e-9).sum(axis=0)
        done += take
    return (count + 1) / (B + 1)


@functools.lru_cache(maxsize=None)
def lane_outcomes(
    rows_dir: Path,
    model: str,
    recovery_dir: Path | None = None,
) -> tuple[dict, set]:
    """Grade one lane and collect no-survivor cells.

    Recovery rows fill holes and never override measured cells. Screen each source on
    its own verdict field so `unverified` cannot silently bias rates. This R=1 study
    drops, never aggregates, `replicate_idx > 0` rows and warns once per cached call.

    Parameters
    ----------
    rows_dir : Path
    model : str
    recovery_dir : Path | None, optional

    Returns
    -------
    tuple[dict, set]
        Graded keys and unresolved keys; only `build_pool` can identify model-dependent faults.
    """
    rows: dict = {}
    sources = [(rows_dir / model / "verified_rows.jsonl", "verdict")]
    if recovery_dir is not None:
        sources.append(
            (recovery_dir / model / "recovered_rows.jsonl", "recovered_verdict")
        )
    rows_source.reject_superseded(path for path, _field in sources)
    for path, field in sources:
        # Each source needs its own field so recovery verdicts are screened too.
        parsed, cells, dropped_replicates = rows_source.read_cell_rows(path)
        reject_unverified_verdicts(parsed, field, path)
        for row in cells:
            key = (row["theorem_id"], row["k"], row["rung"])
            rows.setdefault(key, []).append(row.get(field))
        if dropped_replicates:
            print(
                f"WARNING: lane_outcomes({model!r}) dropped "
                f"{dropped_replicates} row(s) with replicate_idx > 0 from "
                f"{path} (this study collects R=1; rows past "
                f"replicate_idx == 0 are DISCARDED, not aggregated).",
                file=sys.stderr,
            )
    graded, no_survivor = {}, set()
    for key, verdicts in rows.items():
        grade = grade_verdicts(verdicts)
        if grade is None:
            no_survivor.add(key)
        else:
            graded[key] = grade
    return graded, no_survivor


def _rate(hits: int, n: int) -> float | None:
    """``hits / n``, or None for an empty denominator (an undefined rate)."""
    return hits / n if n else None


def build_pool(
    rows_dir: Path, recovery_dir: Path | None = None, count_as_failure: bool = True
) -> tuple:
    """Build the paired 21-way pool.

    Parameters
    ----------
    rows_dir : Path
    recovery_dir : Path | None, optional
    count_as_failure : bool, optional
        Score model-dependent no-survivors 0 instead of dropping them.

    Returns
    -------
    tuple
        Models, blocks, rungs, and rule-cost metadata.
    """
    graded, nosurv = {}, {}
    for model in MODELS:
        # Copy memoized rows because count-as-failure mutates them.
        lane, nosurv[model] = lane_outcomes(rows_dir, model, recovery_dir)
        graded[model] = dict(lane)

    # A no-survivor is model-dependent only if another lane graded it.
    measurable_somewhere = set().union(*(set(g) for g in graded.values()))
    added: dict[str, set] = {m: set() for m in MODELS}
    if count_as_failure:
        for model in MODELS:
            added[model] = nosurv[model] & measurable_somewhere
            for key in added[model]:
                graded[model][key] = 0

    paired = sorted(set.intersection(*(set(g) for g in graded.values())))
    blocks: dict = {}
    for thm, k, rung in paired:
        blocks.setdefault(thm, {})[(k, rung)] = {
            m: graded[m][(thm, k, rung)] for m in MODELS
        }
    prompt_rungs = sorted({ck[1] for cmap in blocks.values() for ck in cmap})

    # Measure rule cost: it changes denominators, not successes; per-cell subtraction understates lanes with multiple additions.
    cost = []
    for model in MODELS:
        if not added[model]:
            continue
        n_lane = len(graded[model])
        hit_lane = sum(graded[model].values())
        rungs_added = sorted({rung for _thm, _k, rung in added[model]})
        for rung in rungs_added:
            in_rung = sorted((thm, k) for thm, k, r in added[model] if r == rung)
            n_rung = sum(1 for key in graded[model] if key[2] == rung)
            hit_rung = sum(v for key, v in graded[model].items() if key[2] == rung)
            # An all-added denominator is undefined: report None, never 0.
            cost.append(
                {
                    "model": model,
                    "rung": rung,
                    "n_added": len(in_rung),
                    "theorems": [f"{thm}@k{k}" for thm, k in in_rung],
                    "pooled_caf": hit_lane / n_lane,
                    "pooled_drop": _rate(hit_lane, n_lane - len(added[model])),
                    "rung_caf": hit_rung / n_rung,
                    "rung_drop": _rate(hit_rung, n_rung - len(in_rung)),
                    "n_lane": n_lane,
                    "n_rung": n_rung,
                }
            )
    meta = {
        "count_as_failure": count_as_failure,
        "recovery": recovery_dir is not None,
        "added": {m: sorted(v) for m, v in added.items() if v},
        "rule_cost": cost,
        "n_unresolved": {m: len(nosurv[m] - measurable_somewhere) for m in MODELS},
        "own_denominator": {m: len(graded[m]) for m in MODELS},
        "own_rate": {m: sum(graded[m].values()) / len(graded[m]) for m in MODELS},
    }
    return sorted(MODELS), blocks, prompt_rungs, meta


def mode_sweep(succ: np.ndarray, size: np.ndarray, models: list[str]) -> None:
    """Measure Monte-Carlo drift across `B_GRID`.

    Choose B from drift against the next larger grid value.

    Parameters
    ----------
    succ : np.ndarray
    size : np.ndarray
    models : list[str]
    """
    print(
        f"Resample-count sweep -- {succ.shape[0]} theorem blocks, "
        f"{int(size.sum())} cells, {len(models)} models"
    )
    print(
        "Each B runs on an INDEPENDENT RNG stream; drift = max |endpoint "
        "change| vs the\nnext larger B, over all 21 marginal BCa intervals.\n"
    )
    print(
        f"{'B':>8s} {'max drift (pts)':>16s} {'median drift':>14s} "
        f"{'worst lane':>28s}"
    )
    print("-" * 72)
    prev = None
    for k, B in enumerate(B_GRID):
        bs = bootstrap_stats(succ, size, B, seed=1000 + k)
        cur = np.array(
            [
                [bs["marginal"][j]["lo"], bs["marginal"][j]["hi"]]
                for j in range(len(models))
            ]
        )
        if prev is not None:
            d = np.abs(cur - prev)
            worst = models[int(np.argmax(d.max(axis=1)))]
            print(f"{B:8d} {d.max():16.5f} {np.median(d):14.5f} {worst:>28s}")
        else:
            print(f"{B:8d} {'(baseline)':>16s} {'':>14s} {'':>28s}")
        prev = cur
    print(
        f"\nTolerance: {DRIFT_TOL} pts (rates are reported to 3 decimals, so "
        f"drift below\nhalf a thousandth cannot change a printed figure)."
    )


def mode_report(
    succ: np.ndarray,
    size: np.ndarray,
    models: list[str],
    blocks: dict,
    per_lane: dict[str, float],
    B: int,
    out_json: Path | None,
    meta: dict[str, Any] | None = None,
    sensitivity: list[tuple] | None = None,
) -> None:
    """Print the report and optionally write JSON.

    Includes marginal BCa intervals, paired contrasts, design effect, and sensitivity.
    A sensitivity row with `n_cells == 0` is a message, not a table row.

    Parameters
    ----------
    succ : np.ndarray
    size : np.ndarray
    models : list[str]
    blocks : dict
        Paired outcomes by theorem and cell.
    per_lane : dict[str, float]
        Rates over each lane's own measurable denominator.
    B : int
    out_json : Path | None
    meta : dict[str, Any] | None, optional
    sensitivity : list[tuple] | None, optional
    """
    bs = bootstrap_stats(succ, size, B, seed=20260816)
    n_thm = succ.shape[0]
    n_cells = int(size.sum())
    meta = meta or {}

    print("=" * 92)
    print("DEDUCTION LEG -- pass@1 with block-bootstrap 95% CIs")
    print("=" * 92)
    print(
        f"Resampling unit: THEOREM BLOCK. n = {n_thm} blocks "
        f"({n_cells} cells, {n_cells / n_thm:.1f} cells per block)."
    )
    print(f"B = {B:,} resamples, BCa intervals (percentile shown for contrast).")
    print(
        f"The effective sample size is {n_thm} THEOREMS, not {n_cells} cells "
        f"-- see the module docstring."
    )
    if meta:
        n_added = sum(len(v) for v in meta["added"].values())
        print("Denominator rule: COUNT-AS-FAILURE (default).", end=" ")
        if meta["count_as_failure"]:
            print(
                f"{n_added} model-dependent no-survivor cell(s) scored 0, in "
                f"{len(meta['added'])} lane(s)."
            )
            # Costs are reductions versus dropping, never signed deltas.
            print(
                f"  {'lane':28s} {'rung':9s} {'+cells':>6s}  "
                f"{'pooled pt':>10s} {'rung pt':>8s}  theorem(s)"
            )
            for c in sorted(
                meta["rule_cost"], key=lambda c: -(_cost(c, "rung_drop") or 0.0)
            ):
                print(
                    f"  {c['model']:28s} {c['rung']:9s} {c['n_added']:6d}  "
                    f"{_fmt(_cost(c, 'pooled_drop'), 10)} "
                    f"{_fmt(_cost(c, 'rung_drop'), 8)}  "
                    f"{', '.join(c['theorems'])}"
                )
            costs_p = [
                v
                for v in (_cost(c, "pooled_drop") for c in meta["rule_cost"])
                if v is not None
            ]
            costs_r = [
                v
                for v in (_cost(c, "rung_drop") for c in meta["rule_cost"])
                if v is not None
            ]
            if costs_p and costs_r:
                worst_p, worst_r = max(costs_p) / 100, max(costs_r) / 100
                print(
                    f"  Cost of the rule: it lowers a lane's rate by at most "
                    f"{100 * worst_p:.3f} accuracy\n  points pooled, and by at "
                    f"most {100 * worst_r:.3f} within a single prompt rung. "
                    f"Successes are\n  unchanged; only the denominator moves, "
                    f"and it moves to the SAME value in all 21 lanes."
                )
        if meta["recovery"]:
            print(
                "  DojoInit recovery rows POOLED IN -- a SENSITIVITY "
                "configuration. The headline\n  figures are Mathlib-only."
            )
    print()

    print(
        f"{'model':30s} {'pass@1':>7s} {'95% BCa':>17s} {'width':>7s} "
        f"{'percentile':>17s} {'own-lane':>9s}"
    )
    print("-" * 92)
    order = [m for fam in FAMILIES.values() for m in fam]
    jmap = {model: j for j, model in enumerate(models)}
    for m in order:
        j = jmap[m]
        r = bs["marginal"][j]
        flag = " *pct" if r["fallback"] else ""
        print(
            f"{m:30s} {r['rate']:7.3f} [{r['lo']:.3f}, {r['hi']:.3f}] "
            f"{r['hi'] - r['lo']:7.3f} [{r['pct_lo']:.3f}, {r['pct_hi']:.3f}] "
            f"{per_lane.get(m, float('nan')):9.3f}{flag}"
        )
    if meta:
        gaps = {
            m: abs(per_lane[m] - bs["marginal"][jmap[m]]["rate"])
            for m in order
            if m in per_lane
        }
        worst = max(gaps, key=gaps.get)
        denoms = sorted({meta["own_denominator"][m] for m in order})
        print(
            f"\nown-lane = each lane's rate over its OWN measurable "
            f"denominator ("
            f"{'/'.join(str(d) for d in denoms)} cells).\n  Max |own-lane - "
            f"paired| = {gaps[worst]:.4f} ({worst}); at the 3 decimals "
            f"printed that reads as\n  {gaps[worst]:.3f}."
        )

    naive = np.sqrt(bs["theta_hat"] * (1 - bs["theta_hat"]) / n_cells) * 1.96 * 2
    boot_w = np.array(
        [bs["marginal"][j]["hi"] - bs["marginal"][j]["lo"] for j in range(len(models))]
    )
    print(
        f"\nDesign effect: block-bootstrap intervals are "
        f"{np.median(boot_w / naive):.2f}x (median) the width a naive binomial "
        f"on {n_cells}\n  independent cells would give -- range "
        f"{np.min(boot_w / naive):.2f}x to {np.max(boot_w / naive):.2f}x. "
        f"Treating cells as independent\n  would overstate precision by that "
        f"factor."
    )

    results = {
        "n_theorem_blocks": n_thm,
        "n_cells": n_cells,
        "B": B,
        "marginals": {m: bs["marginal"][jmap[m]] for m in models},
        "contrasts": {},
    }

    for tier, contrasts, corrected in (
        ("PRIMARY -- within-family ladder", build_within_family_contrasts(), True),
        (
            "SECONDARY -- cross-family, size-matched",
            build_cross_family_contrasts(),
            False,
        ),
    ):
        p_block = block_signflip_p(succ, models, contrasts)
        rows = []
        for i, (label, a, b) in enumerate(contrasts):
            ci = diff_ci(bs, jmap[a], jmap[b])
            nb, nc, p_cell = paired_mcnemar(blocks, a, b)
            rows.append((label, a, b, ci, nb, nc, float(p_block[i]), p_cell))
        pv = np.array([r[6] for r in rows])  # PRIMARY inference
        pv_cell = np.array([r[7] for r in rows])  # descriptive
        # PRIMARY uses Holm for dependent FWER; exploratory SECONDARY uses preregistered BH q=0.05.
        rej = holm(pv) if corrected else benjamini_hochberg(pv, Q_SECONDARY)
        rej_cell = (
            holm(pv_cell) if corrected else benjamini_hochberg(pv_cell, Q_SECONDARY)
        )

        proc = "Holm" if corrected else "BH"
        print("\n" + rows_source.banner(f"{tier}: {len(rows)} contrasts", width=92))
        print(
            f"PRIMARY p = BLOCK SIGN-FLIP permutation over the {n_thm} theorem "
            f"blocks,\n  B = {B_SIGNFLIP:,} draws, fixed seed "
            f"{SIGNFLIP_SEED} (resolution floor {1 / (B_SIGNFLIP + 1):.1e}). "
            f"Cell-level\n  exact McNemar is shown beside it as a DESCRIPTIVE "
            f"figure -- it assumes the "
            f"{n_cells}\n  cells are independent, which is the assumption "
            f"every interval on this page rejects."
        )
        if corrected:
            print(
                "Holm-Bonferroni at FWER 0.05 over these 21 (arbitrary "
                "dependence).\n"
            )
        else:
            print(
                f"Benjamini-Hochberg FDR at q = {Q_SECONDARY} over these "
                f"{len(rows)} (pre-registered:\nexploratory tier, so FDR "
                f"rather than FWER).\n"
            )
        print(
            f"{'contrast':46s} {'diff':>7s} {'95% BCa':>17s} {'b/c':>10s} "
            f"{'p_block':>9s} {'p_cell':>9s} {proc:>5s}"
        )
        print("-" * 110)
        for (label, a, b, ci, nb, nc, p, p_cell), ok in zip(rows, rej):
            mark = " yes " if ok else "  .  "
            crosses = "" if (ci["lo"] > 0 or ci["hi"] < 0) else "  (CI spans 0)"
            short = label if len(label) <= 46 else label[:43] + "..."
            print(
                f"{short:46s} {ci['diff']:+7.3f} [{ci['lo']:+.3f}, "
                f"{ci['hi']:+.3f}] {nb:4d}/{nc:<5d} {p:9.2e} {p_cell:9.2e} "
                f"{mark}{crosses}"
            )
            results["contrasts"][label] = {
                "model_a": a,
                "model_b": b,
                **ci,
                "b": nb,
                "c": nc,
                "p": p,
                "p_cell": p_cell,
                "holm": bool(ok),
            }

        agree = sum(
            1
            for (_, _, _, ci, _, _, _, _), ok in zip(rows, rej)
            if ok == (ci["lo"] > 0 or ci["hi"] < 0)
        )
        print(
            f"\n{proc} rejects {int(rej.sum())} of {len(rows)}; "
            f"uncorrected p<{ALPHA} would be {int((pv < ALPHA).sum())}; "
            f"CIs excluding 0: "
            f"{sum(1 for r in rows if r[3]['lo'] > 0 or r[3]['hi'] < 0)}."
        )
        print(
            f"  On the SAME cells, cell-level McNemar + {proc} would reject "
            f"{int(rej_cell.sum())}. The\n  difference is entirely "
            f"clustering: cells inside a theorem share a ground truth and\n"
            f"  a proof prefix, so treating them as independent overstates the "
            f"evidence."
        )
        lost = [rows[i][0] for i in range(len(rows)) if rej_cell[i] and not rej[i]]
        for label in lost:
            print(f"    only under the cell-level test: {label}")
        print(
            f"  {proc} and the uncorrected CI agree on {agree}/{len(rows)}. "
            f"They are DIFFERENT questions: the CI is\n  uncorrected and "
            f"two-sided per contrast; {proc} controls error over the whole "
            f"tier."
        )

        if corrected:
            print(
                "\nPer-family ladder verdict (a family 'scales cleanly' only "
                "if all three\nrung-pairs are positive AND significant):"
            )
            for family, ladder in FAMILIES.items():
                idx = [
                    i for i, r in enumerate(rows) if r[1] in ladder and r[2] in ladder
                ]
                n_sig = sum(1 for i in idx if rej[i])
                n_pos = sum(1 for i in idx if rows[i][3]["diff"] > 0)
                clean = "CLEAN" if (n_sig == 3 and n_pos == 3) else "no"
                print(
                    f"  {family:12s} {n_sig}/3 significant, {n_pos}/3 "
                    f"positive  -> {clean}"
                )

    if sensitivity:
        print(
            "\n"
            + rows_source.banner(
                (
                    "SENSITIVITY -- the same PRIMARY test under other "
                    "denominator rules"
                ),
                width=92,
            )
        )
        print(
            "Each row re-pools the cells and re-runs the block sign-flip test "
            "from scratch.\nRe-pooling the DojoInit recovery rows is a "
            "sensitivity only: the headline figures\nare Mathlib-only.\n"
        )
        print(
            f"{'pool':46s} {'cells':>7s} {'blocks':>7s} {'Holm':>6s} "
            f"{'max own-vs-paired':>18s}"
        )
        print("-" * 90)
        for label, n_c, n_b, n_rej, gap in sensitivity:
            if n_c == 0:
                continue
            print(f"{label:46s} {n_c:7d} {n_b:7d} {n_rej:5d}/21 {gap:18.4f}")
        print(
            "\nmax own-vs-paired = largest gap between a lane's rate over its "
            "own denominator and\n  its rate on the 21-way paired pool. It is "
            "exactly 0 under count-as-failure,\n  because that rule gives "
            "every lane the same denominator as the pool."
        )
        for label, n_c, _n_b, _n_rej, _gap in sensitivity:
            if n_c == 0:
                print(f"\n{label}")

    if out_json:
        Path(out_json).write_text(
            json.dumps(results, indent=2, default=float), encoding="utf-8"
        )
        print(f"\nwrote {out_json}")


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, build a pool, and run a mode.

    `resolve_rows_dir` makes `--s3` and `--rows-dir` one local row directory.

    Parameters
    ----------
    argv : list[str] | None, optional

    Returns
    -------
    int
        Exit status.

    Raises
    ------
    SystemExit
        Missing lane rows, an empty S3 download, or a retired artifact.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    rows_source.add_source_args(ap)
    ap.add_argument("--mode", choices=("sweep", "report"), default="report")
    ap.add_argument("-B", type=int, default=20_000)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument(
        "--recovery-dir",
        type=Path,
        default=None,
        help="LOCAL directory of <model>/recovered_rows.jsonl "
        "(DojoInit recovery). These rows ARE archived, under "
        "their own dojoinit_recovery_<date>/<lane>/ tree, but "
        "that tree is neither scaling_* nor "
        "verified_rows.jsonl, so --s3 does not reach it and "
        "no --s3 form of this option is implemented. Pooled "
        "into the SENSITIVITY rows, never into the headline "
        "pool.",
    )
    args = ap.parse_args(argv)

    rows_dir = rows_source.resolve_from_args(args)

    missing = [rows_dir / m / "verified_rows.jsonl" for m in MODELS]
    missing = [f for f in missing if not f.exists()]
    if missing:
        raise SystemExit(f"missing row files: {[str(f) for f in missing]}")

    models, blocks, _rungs, meta = build_pool(rows_dir)
    succ, size = block_matrix(models, blocks)
    per_lane = dict(meta["own_rate"])

    if args.mode == "sweep":
        mode_sweep(succ, size, models)
        return 0

    # Sensitivity reruns PRIMARY under other rules so changes are attributable.
    sensitivity = []
    for caf in (True, False):
        for rec in [None] + ([args.recovery_dir] if args.recovery_dir else []):
            if caf and rec is None:
                continue
            _m, _b, _r, _meta = build_pool(
                rows_dir, recovery_dir=rec, count_as_failure=caf
            )
            _succ, _size = block_matrix(_m, _b)
            p = block_signflip_p(_succ, _m, build_within_family_contrasts())
            paired = _succ.sum(axis=0) / _size.sum()
            gap = max(
                abs(paired[_m.index(mm)] - _meta["own_rate"][mm]) for mm in MODELS
            )
            label = "count-as-failure" if caf else "drop no-survivor"
            label += " + DojoInit recovery" if rec else " (Mathlib only)"
            sensitivity.append(
                (label, int(_size.sum()), _succ.shape[0], int(holm(p).sum()), gap)
            )
    if args.recovery_dir is None:
        sensitivity.append(
            (
                "Post-recovery pools are NOT shown: pass --recovery-dir "
                "<dir-of-<model>/recovered_rows.jsonl>\n(e.g. "
                "notebooks/deduction/results/dojoinit_recovery_2026-08-18) to add "
                "them.",
                0,
                0,
                0,
                0.0,
            )
        )

    mode_report(
        succ,
        size,
        models,
        blocks,
        per_lane,
        args.B,
        args.out_json,
        meta=meta,
        sensitivity=sensitivity,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
