"""Monte Carlo study of test and correction choices for the induction study.

`study_design_effect` compares the observed design effect with simulated `icc` clustering;
they differ because `icc` is latent share and `design_effect` an observed variance ratio.

Rejection boundary: a p-value rejects when ``p <= alpha`` (the statsmodels convention
`paired_analysis.holm` and `significance_report.hochberg` follow). Tests decided on a
chi-square statistic use ``stat > crit``, equivalent for a continuous statistic.
"""

from __future__ import annotations

import functools
import json
import os
import sys
import tempfile
import time
from itertools import combinations, product
from pathlib import Path

# Anchor paths to this file so sibling imports do not depend on invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import paired_analysis
import power_analysis
from _power_common import ALPHA, SEED, apply_corrections
from power_analysis import (
    ALPHA_OMNIBUS,
    ALPHA_PRIMARY,
    INFOS,
    MODELS,
    N_FAMILIES,
    N_HARMONICS,
    N_INFOS,
    N_LADDER_CONTRASTS,
    N_LADDERS,
    N_PRIMARY,
    N_REPLICATES,
    N_RUNGS,
    RESULTS_DIR,
    cmh_p,
    cmh_stat,
    gcmh_stat,
    mcnemar_exact_p,
)
from scipy.stats import chi2, norm

from smolbench.evals.results_store import LocalResultsStore

#: Start at study depth so "pairing bought nothing" stays reachable.
EQ_R_GRID = (N_REPLICATES, 35, 40, 45, 50, 60, 70, 85, 100, 120, 145, 175, 210, 250)
EQ_R_GRID += (300, 360, 430, 520, 620, 750, 900)

#: Paired-vs-unpaired power gap treated as equal in the eq_R search: about one
#: Monte-Carlo standard error of a power estimate near 0.8 at N_SIMS.
EQ_R_TOL = 0.005

#: Include the unclustered baseline and plausible clustering range.
ICC_GRID = (0.0, 0.2, 0.4)

#: Replace each ladder's pairwise contrasts with one trend test.
N_REDUCED = N_LADDERS + N_PRIMARY - N_LADDER_CONTRASTS
#: Anchor checkpoints to the study results tree.
OUT_NAME = "multiplicity_sim_results.json"
OUT_PATH = RESULTS_DIR / OUT_NAME


def dump(out: dict, path: Path, tag: str) -> None:
    """Atomically write a checkpoint JSON via a sibling temp file.

    Failed writes preserve the previous checkpoint; directory creation is lazy.

    Parameters
    ----------
    out : dict
        Simulation results to checkpoint.
    path : Path
        Destination JSON.
    tag : str
        Checkpoint label written to the log.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, default=float)
        os.replace(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    print(f"[checkpoint written after {tag}]", flush=True)


def trend_stat(
    succ: np.ndarray,
    n: int,
    scores: tuple[float, ...] = tuple(float(i) for i in range(1, N_RUNGS + 1)),
) -> np.ndarray:
    """Compute the 1-df CMH linear trend across the three rungs.

    Parameters
    ----------
    succ : np.ndarray
        Success counts with trailing rung and harmonic axes.
    n : int
        Trials per cell.
    scores : tuple[float, ...]
        Ordered rung scores.

    Returns
    -------
    np.ndarray
        Statistic per simulation; zero where variance is zero.
    """
    x = np.asarray(scores)
    n_rungs = succ.shape[-2]
    total_n = float(n_rungs * n)
    m = succ.sum(axis=-2)  # (..., K) successes
    t = (succ * x[:, None]).sum(axis=(-2, -1))  # observed
    sum_nx = n * x.sum()
    sum_nx2 = n * (x**2).sum()
    e_j = sum_nx * m / total_n
    v_j = (m * (total_n - m) / (total_n**2 * (total_n - 1.0))) * (
        total_n * sum_nx2 - sum_nx**2
    )
    e = e_j.sum(axis=-1)
    v = v_j.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(v > 0, (t - e) ** 2 / v, 0.0)


def paired_marks(
    p_a: float,
    p_b: float,
    rho: float,
    n_sims: int,
    reps: int,
    rng: np.random.Generator,
    icc: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate matched marks from a latent bivariate normal.

    Skip zero-`icc` clustering draws to preserve RNG order. Replicate and item
    latents both correlate at `rho`, avoiding attenuation to ``(1 - icc) * rho``.

    Parameters
    ----------
    p_a, p_b : float
        Marginal mark rates for arms A and B.
    rho : float
        Tetrachoric correlation between matched marks.
    n_sims, reps : int
        Number of experiments and replicates per experiment.
    rng : np.random.Generator
        Random generator for latent draws.
    icc : float, optional
        Shared per-replicate latent variance fraction; default is zero.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Simulated Boolean marks for arms A and B.

    Raises
    ------
    ValueError
        If `icc` is outside [0, 1).
    """
    if not 0.0 <= icc < 1.0:
        raise ValueError(f"icc must be in [0.0, 1.0), got {icc!r}")
    z1 = rng.standard_normal((n_sims, reps, N_HARMONICS), dtype=np.float32)
    z2 = rng.standard_normal((n_sims, reps, N_HARMONICS), dtype=np.float32)
    zb = rho * z1 + np.sqrt(max(1.0 - rho * rho, 0.0)) * z2
    if icc > 0.0:
        u_a = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        u_b = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        u_b = rho * u_a + np.sqrt(max(1.0 - rho * rho, 0.0)) * u_b
        w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
        z1 = w1 * u_a + w2 * z1
        zb = w1 * u_b + w2 * zb
    return z1 < norm.ppf(p_a), zb < norm.ppf(p_b)


def part1(rng: np.random.Generator, n_sims: int = 20000, step: float = 0.0025) -> dict:
    """Find minimum detectable differences at each ceiling.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Number of simulations per baseline rate and gap.
    step : float, optional
        Accuracy-gap increment to scan.

    Returns
    -------
    dict
        Simulation count, grid step, and minimum-detectable-difference rows.
    """
    print("\n=== PART 1: minimum detectable difference (80% power) ===", flush=True)
    rows = []
    for p_a in (0.99, 0.97, 0.95, 0.90, 0.70, 0.50):
        found = {}
        d = step
        while d <= min(p_a, 0.60) + 1e-9 and len(found) < 2:
            p_b = max(0.0, p_a - d)
            sa = rng.binomial(N_REPLICATES, p_a, (n_sims, N_HARMONICS))
            sb = rng.binomial(N_REPLICATES, p_b, (n_sims, N_HARMONICS))
            st = cmh_stat(sa, sb, N_REPLICATES)
            for a_lab, a in (("bonf", ALPHA_PRIMARY), ("naive", ALPHA)):
                if a_lab not in found:
                    pw = (st > chi2.isf(a, df=1)).mean()
                    if pw >= 0.80:
                        found[a_lab] = (round(d, 4), float(pw))
            d += step
        mdd_bonf, pow_bonf = found.get("bonf", (None, None))
        mdd_naive, pow_naive = found.get("naive", (None, None))
        row = {
            "p_a": p_a,
            "mdd_bonf": mdd_bonf,
            "pow_bonf": pow_bonf,
            "mdd_naive": mdd_naive,
            "pow_naive": pow_naive,
            "ratio": mdd_bonf / mdd_naive if mdd_bonf and mdd_naive else None,
        }
        rows.append(row)
        print(
            f"  p_A={p_a:.2f}  MDD(alpha={ALPHA_PRIMARY:.2e})={row['mdd_bonf']}  "
            f"MDD(alpha={ALPHA})={row['mdd_naive']}  ratio={row['ratio']}",
            flush=True,
        )
    return {"n_sims": n_sims, "grid_step": step, "rows": rows}


def part3(rng: np.random.Generator, n_sims: int = 200000, chunk: int = 20000) -> dict:
    """Measure Type I error under within-replicate clustering.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    n_sims : int, optional
        Total simulations per grid configuration.
    chunk : int, optional
        Bounds peak memory.

    Returns
    -------
    dict
        Type-I error and binary-correlation rows.
    """
    print(
        "\n=== PART 3: within-replicate clustering -> actual Type I error ===",
        flush=True,
    )
    crit05 = chi2.isf(ALPHA, df=1)
    critb = chi2.isf(ALPHA_PRIMARY, df=1)
    rows = []
    for p, icc, variant in product(
        (0.90, 0.70), (0.0, 0.1, 0.2, 0.4), ("independent", "shared")
    ):
        if p == 0.70 and variant == "shared":
            continue
        thr = norm.ppf(p)
        r05 = rb = 0
        done = 0
        phis = []
        while done < n_sims:
            s = min(chunk, n_sims - done)
            u_a = rng.standard_normal((s, N_REPLICATES, 1), dtype=np.float32)
            u_b = (
                u_a
                if variant == "shared"
                else rng.standard_normal((s, N_REPLICATES, 1), dtype=np.float32)
            )
            ea = rng.standard_normal((s, N_REPLICATES, N_HARMONICS), dtype=np.float32)
            eb = rng.standard_normal((s, N_REPLICATES, N_HARMONICS), dtype=np.float32)
            w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
            ma = (w1 * u_a + w2 * ea) < thr
            mb = (w1 * u_b + w2 * eb) < thr
            if len(phis) < 3:  # empirical binary within-replicate corr
                x = ma.astype(np.float64)
                mu = x.mean()
                cx = x - mu
                # mean over k<k' of E[cx_k cx_k'] / var
                ssum = cx.sum(axis=2)
                cross = (ssum**2 - (cx**2).sum(axis=2)).mean() / (
                    N_HARMONICS * (N_HARMONICS - 1)
                )
                phis.append(cross / (mu * (1 - mu)))
            sa = ma.sum(axis=1)
            sb = mb.sum(axis=1)
            st = cmh_stat(sa, sb, N_REPLICATES)
            r05 += int((st > crit05).sum())
            rb += int((st > critb).sum())
            done += s
        row = {
            "p": p,
            "icc": icc,
            "variant": variant,
            "phi_binary": float(np.mean(phis)),
            "t1_alpha05": r05 / n_sims,
            "t1_alpha_bonf": rb / n_sims,
            "infl05": (r05 / n_sims) / ALPHA,
            "inflb": (rb / n_sims) / ALPHA_PRIMARY,
            "n_sims": n_sims,
        }
        rows.append(row)
        print(
            f"  p={p} icc={icc} {variant:11s} phi_bin={row['phi_binary']:.3f} "
            f"T1@{ALPHA}={row['t1_alpha05']:.4f} ({row['infl05']:.2f}x)  "
            f"T1@{ALPHA_PRIMARY:.2e}={row['t1_alpha_bonf']:.6f} "
            f"({row['inflb']:.2f}x)",
            flush=True,
        )
    return {"rows": rows}


def part5(rng: np.random.Generator, n_sims: int = 20000) -> dict:
    """Compare the 1-df trend test against the 2-df omnibus and 3 pairwise tests.

    Six monotone/non-monotone scenarios span small, mid and ceiling effects.
    Local uncorrected-family alphas isolate test choice from correction.
    `trend_studywide` uses PART 4's ``ALPHA / N_REDUCED`` family;
    ``ALPHA / N_LADDERS`` is sensitivity-only because it is not pre-registered.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Simulations per rate scenario.

    Returns
    -------
    dict
        Rejection-rate rows, simulation count, and correction thresholds.
    """
    print("\n=== PART 5: 1-df trend vs 2-df omnibus vs 3 pairwise ===", flush=True)
    # The same N_LADDERS trend tests as PART 4's reduced family.
    alpha_trend_studywide = ALPHA / N_REDUCED
    # Sensitivity only: correcting the trend tests among themselves.
    alpha_trend_only = ALPHA / N_LADDERS
    rows = []
    for label, rates in (
        ("monotone 0.60/0.75/0.88", (0.60, 0.75, 0.88)),
        ("non-monotone 0.60/0.88/0.75", (0.60, 0.88, 0.75)),
        ("monotone-small 0.60/0.66/0.72", (0.60, 0.66, 0.72)),
        ("non-monotone-small 0.60/0.72/0.66", (0.60, 0.72, 0.66)),
        ("monotone-ceiling 0.99/0.96/0.93", (0.99, 0.96, 0.93)),
        ("non-monotone-ceiling 0.99/0.93/0.96", (0.99, 0.93, 0.96)),
    ):
        succ = np.stack(
            [rng.binomial(N_REPLICATES, r, (n_sims, N_HARMONICS)) for r in rates],
            axis=1,
        )
        tr = trend_stat(succ, N_REPLICATES)
        gc = gcmh_stat(succ, N_REPLICATES)
        pair_stats = [
            cmh_stat(succ[:, i, :], succ[:, j, :], N_REPLICATES)
            for i, j in combinations(range(N_RUNGS), 2)
        ]
        res = {"label": label, "rates": rates}
        res["trend_studywide"] = float((tr > chi2.isf(alpha_trend_studywide, 1)).mean())
        # Same statistic at the narrower, not pre-registered, trend-only alpha.
        res["trend_trend_only_family"] = float(
            (tr > chi2.isf(alpha_trend_only, 1)).mean()
        )
        res["gcmh_studywide"] = float((gc > chi2.isf(ALPHA_OMNIBUS, 2)).mean())
        res["pairwise_any_studywide"] = float(
            np.any([s > chi2.isf(ALPHA_PRIMARY, 1) for s in pair_stats], axis=0).mean()
        )
        # local, uncorrected-family alphas (test choice isolated from correction)
        res["trend_local05"] = float((tr > chi2.isf(ALPHA, 1)).mean())
        res["gcmh_local05"] = float((gc > chi2.isf(ALPHA, 2)).mean())
        res["pairwise_any_local"] = float(
            np.any(
                [s > chi2.isf(ALPHA / N_RUNGS, 1) for s in pair_stats], axis=0
            ).mean()
        )
        rows.append(res)
        print(
            f"  {label}\n"
            f"    study-wide: trend[a={ALPHA}/{N_REDUCED}]="
            f"{res['trend_studywide']:.4f} "
            f"gcmh(2df)[a={ALPHA}/{N_FAMILIES}]={res['gcmh_studywide']:.4f} "
            f"any-pairwise[a={ALPHA}/{N_PRIMARY}]="
            f"{res['pairwise_any_studywide']:.4f}\n"
            f"    sensitivity: trend[a={ALPHA}/{N_LADDERS}, trend-only family, "
            f"not pre-registered]={res['trend_trend_only_family']:.4f}\n"
            f"    local a={ALPHA}: trend={res['trend_local05']:.4f} "
            f"gcmh={res['gcmh_local05']:.4f} any-pairwise={res['pairwise_any_local']:.4f}",
            flush=True,
        )
    return {
        "rows": rows,
        "n_sims": n_sims,
        "alpha_trend_studywide": alpha_trend_studywide,
        "alpha_trend_only": alpha_trend_only,
        "alpha_pairwise": ALPHA_PRIMARY,
        "alpha_gcmh": ALPHA_OMNIBUS,
    }


def _paired_powers(
    p_a: float,
    delta: float,
    rho: float,
    reps: int,
    n_sims: int,
    rng: np.random.Generator,
    stats: bool = True,
    icc: float = 0.0,
) -> tuple[float, float, float | None, float | None]:
    """Compute unpaired and paired power on identical simulated marks.

    Item-level McNemar assumes independent marks, so it is anticonservative
    at ``icc > 0`` (PART 3); the study's primary test uses seed-level sign-flips.
    Disabling diagnostics preserves powers and avoids costly float upcasts.

    Parameters
    ----------
    p_a, delta, rho : float
        Arm A rate, A-minus-B rate gap, and latent cross-arm correlation.
    reps, n_sims : int
        Replicates per simulation and number of simulated datasets.
    rng : np.random.Generator
        Random-number generator for matched marks.
    stats : bool, optional
        Whether to compute the mark-level diagnostics.
    icc : float, optional
        Within-replicate latent correlation.

    Returns
    -------
    tuple
        ``(power_unpaired, power_paired, phi_binary, agreement)``.
    """
    ma, mb = paired_marks(p_a, p_a - delta, rho, n_sims, reps, rng, icc=icc)
    unp = (
        cmh_stat(ma.sum(axis=1), mb.sum(axis=1), reps) > chi2.isf(ALPHA_PRIMARY, 1)
    ).mean()
    b = (ma & ~mb).sum(axis=(1, 2))
    c = (~ma & mb).sum(axis=(1, 2))
    pv = mcnemar_exact_p(b, c)
    powers = float(unp), float((pv <= ALPHA_PRIMARY).mean())
    if not stats:
        # ``None`` distinguishes unmeasured diagnostics from zero.
        return powers[0], powers[1], None, None
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    return *powers, float(phi), float((ma == mb).mean())


def study_design_effect(results_dir: Path) -> float | None:
    """Read the study's measured design effect.

    Return ``None`` when no study replicate lane exists (a checkpoint JSON alone
    does not count); propagate failures once data is present.

    Parameters
    ----------
    results_dir : Path
        Study replicate tree.

    Returns
    -------
    float | None
        Median measurable design effect, or no measurable contrast.
    """
    store = LocalResultsStore(results_dir)
    if not any(
        store.list_seeds(None, model, info) for model in MODELS for info in INFOS
    ):
        return None
    marks = paired_analysis.load_marks(results_dir)
    deffs = []
    for _label, key_a, key_b in power_analysis.build_primary_contrasts():
        d = paired_analysis.design_effect(
            *paired_analysis.aligned(marks, key_a, key_b, drop_invalid=False)
        )
        if d is not None:
            deffs.append(d)
    return float(np.median(deffs)) if deffs else None


def part2(
    rng: np.random.Generator,
    results_dir: Path,
    n_sims: int = 20000,
    search_sims: int = 8000,
) -> dict:
    """Measure pairing gains over unpaired testing.

    McNemar is anticonservative at ``icc > 0``, biasing ``eq_R`` upward;
    compare each simulated design effect with the study estimate.
    Search only for power gaps above `EQ_R_TOL` (Monte-Carlo error).
    Unpaired power within `EQ_R_TOL` counts as matching; smaller initial
    gaps and first-rung matches are unsearched at `N_REPLICATES`.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    results_dir : Path
        Study replicate tree for the measured design effect.
    n_sims, search_sims : int, optional
        Main power and per-rung equivalent-R search simulation counts.

    Returns
    -------
    dict
        Pairing gains and calibration by ICC, with search grid and alpha.
    """
    measured = study_design_effect(results_dir)
    measured_str = (
        f"{measured:.3f}"
        if measured is not None
        else f"unknown (no results tree at {results_dir})"
    )
    print(
        "\n=== PART 2: pairing gain (matched items) ===\n"
        "  paired = item-level exact McNemar, anticonservative at icc>0 (see "
        "PART 3); it is not the seed-level sign-flip primary test\n"
        f"  study's own measured design effect: {measured_str} -- compare "
        f"against each icc block's design_effect_simulated below\n"
        f"  eq_R: smallest grid R whose unpaired power reaches paired power "
        f"(within {EQ_R_TOL}); gaps <= {EQ_R_TOL} are within Monte-Carlo error "
        f"and reported unsearched at R={N_REPLICATES}",
        flush=True,
    )
    grid_r = list(EQ_R_GRID)
    icc_blocks = {}
    for icc in ICC_GRID:
        print(f"\n--- PART 2 table, icc={icc} ---", flush=True)
        rows = []
        for p_a, delta, rho in product(
            (0.95, 0.70), (0.05, 0.10), (0.0, 0.3, 0.5, 0.7, 0.9)
        ):
            if p_a == 0.70 and rho not in (0.5, 0.7):
                continue
            unp, pair, phi, agree = _paired_powers(
                p_a, delta, rho, N_REPLICATES, n_sims, rng, icc=icc
            )
            # Smallest R where the unpaired test matches paired power at study depth.
            searched = pair > unp + EQ_R_TOL
            eq_r = None
            if searched:
                for rr in grid_r:
                    # stats=False: only unpaired power is read here.
                    u2 = _paired_powers(
                        p_a, delta, rho, rr, search_sims, rng, stats=False, icc=icc
                    )[0]
                    if u2 >= pair - EQ_R_TOL:
                        eq_r = rr
                        searched = rr != N_REPLICATES
                        break
            else:
                eq_r = N_REPLICATES
            rows.append(
                {
                    "p_a": p_a,
                    "delta": delta,
                    "rho": rho,
                    "power_unpaired": unp,
                    "power_paired": pair,
                    "eq_R": eq_r,
                    "eq_searched": searched,
                    "cap": EQ_R_GRID[-1],
                    "phi_binary": phi,
                    "agreement": agree,
                    "eq_ratio": None if eq_r is None else eq_r / N_REPLICATES,
                    "icc": icc,
                }
            )
            suffix = "" if searched else f" (gap <= {EQ_R_TOL}, unsearched)"
            print(
                f"  icc={icc} p_A={p_a} d={delta} rho={rho}: "
                f"phi_bin={phi:.3f} agree={agree:.3f} "
                f"unpaired={unp:.4f} paired(item-McNemar)={pair:.4f} "
                f"eqR={eq_r}{suffix}",
                flush=True,
            )
        nulls = {}
        for rho in (0.0, 0.5, 0.9):
            u, p = _paired_powers(
                0.90, 0.0, rho, N_REPLICATES, 60000, rng, stats=False, icc=icc
            )[:2]
            nulls[rho] = {"unpaired_t1": u, "mcnemar_t1": p}
            print(
                f"  icc={icc} NULL rho={rho}: unpaired T1={u:.6f} "
                f"mcnemar T1={p:.6f}",
                flush=True,
            )

        # Match the null calibration at p_a=p_b=0.90, rho=0.5.
        ma, mb = paired_marks(0.90, 0.90, 0.5, n_sims, N_REPLICATES, rng, icc=icc)
        seed_idx = np.repeat(np.arange(N_REPLICATES), N_HARMONICS)
        harm_idx = np.tile(np.arange(N_HARMONICS), N_REPLICATES)
        deffs = [
            paired_analysis.design_effect(
                ma[i].ravel(), mb[i].ravel(), seed_idx, harm_idx
            )
            for i in range(n_sims)
        ]
        measurable = [d for d in deffs if d is not None]
        if measurable:
            deff_sim = float(np.median(measurable))
            print(
                f"  icc={icc} design_effect_simulated: {deff_sim:.3f} "
                f"(median of {len(measurable)}/{n_sims} measurable)",
                flush=True,
            )
        else:
            # An unmeasurable block must not report a placeholder number.
            deff_sim = None
            print(
                f"  icc={icc} design_effect_simulated: no measurable ratio "
                f"in {n_sims} simulations",
                flush=True,
            )

        icc_blocks[str(icc)] = {
            "rows": rows,
            "nulls": nulls,
            "design_effect_simulated": deff_sim,
        }

    # icc keys are strings: JSON has no float keys.
    return {
        "n_sims": n_sims,
        "alpha": ALPHA_PRIMARY,
        "grid_r": grid_r,
        "icc": icc_blocks,
    }


def part4(rng: np.random.Generator, n_sims: int = 4000) -> dict:
    """Measure multiplicity-correction cost against known truth.

    The fixed-size trend arm separates test choice from correction-family size.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Number of simulated p-value families.

    Returns
    -------
    dict
        Correction summaries and the simulated true-rate configuration.

    Raises
    ------
    RuntimeError
        If contrast counts disagree with the study correction denominators.
    """
    print("\n=== PART 4: correction cost ===", flush=True)
    # Family 0 is a ceiling ladder at every info; ladders (1, info 1) and (2, info 1)
    # plant mid-range effects; every other contrast is null.
    rates = np.zeros((N_FAMILIES, N_RUNGS, N_INFOS))
    for f, rate in enumerate([0.99, 0.97, 0.95, 0.92, 0.85, 0.75, 0.62]):
        rates[f] = rate
    rates[0] = np.array([0.99, 0.96, 0.925])[:, None]
    rates[1, :, 1] = [0.97, 0.91, 0.83]
    rates[2, :, 1] = [0.95, 0.86, 0.74]
    contrasts = [
        (f, a, i, f, b, i)
        for f, i in np.ndindex(N_FAMILIES, N_INFOS)
        for a, b in combinations(range(N_RUNGS), 2)
    ] + [
        (f, r, a, f, r, b)
        for f, r in np.ndindex(N_FAMILIES, N_RUNGS)
        for a, b in combinations(range(N_INFOS), 2)
    ]
    m_full = len(contrasts)
    # Raise survives ``-O``; this family sets every correction denominator.
    if m_full != N_PRIMARY:
        raise RuntimeError(
            f"PART 4 built {m_full} contrasts but N_PRIMARY = {N_PRIMARY}; "
            "the simulated Bonferroni alpha would be wrong."
        )
    true_diff = np.array([abs(rates[c[:3]] - rates[c[3:]]) for c in contrasts])
    is_null = true_diff == 0.0
    n_true = int((~is_null).sum())
    ladder_rates = rates.transpose(0, 2, 1).reshape(N_LADDERS, N_RUNGS)
    ladder_nonflat = ~np.all(ladder_rates == ladder_rates[:, :1], axis=1)
    print(
        f"  config: {n_true} true effects / {int(is_null.sum())} true nulls; "
        f"non-flat ladders = {int(ladder_nonflat.sum())}/{N_LADDERS}\n"
        f"  true-effect deltas: {np.sort(true_diff[~is_null])}",
        flush=True,
    )

    succ = np.empty((n_sims, N_FAMILIES, N_RUNGS, N_INFOS, N_HARMONICS), dtype=np.int32)
    for f, r, i in np.ndindex(N_FAMILIES, N_RUNGS, N_INFOS):
        succ[:, f, r, i, :] = rng.binomial(
            N_REPLICATES, rates[f, r, i], (n_sims, N_HARMONICS)
        )
    pv = np.empty((n_sims, m_full))
    for t, c in enumerate(contrasts):
        pv[:, t] = cmh_p(
            succ[:, c[0], c[1], c[2], :], succ[:, c[3], c[4], c[5], :], N_REPLICATES
        )
    trend_p = np.column_stack(
        [
            chi2.sf(trend_stat(succ[:, f, :, i, :], N_REPLICATES), df=1)
            for f, i in np.ndindex(N_FAMILIES, N_INFOS)
        ]
    )
    pv_red = np.concatenate([trend_p, pv[:, N_LADDER_CONTRASTS:]], axis=1)
    null_red = np.concatenate([~ladder_nonflat, is_null[N_LADDER_CONTRASTS:]])
    m_red = pv_red.shape[1]
    # PART 5 uses this reduced-family correction denominator.
    if m_red != N_REDUCED:
        raise RuntimeError(
            f"PART 4 built {m_red} reduced tests but N_REDUCED = {N_REDUCED}; "
            "PART 5's study-wide alpha would be wrong."
        )

    summaries = {}
    for key, name, rejmap, nullmask, tests_per_ladder in (
        (
            "full",
            f"m={N_PRIMARY}",
            apply_corrections(pv, ALPHA),
            is_null,
            N_LADDER_CONTRASTS // N_LADDERS,
        ),
        ("reduced", f"m={N_REDUCED}", apply_corrections(pv_red, ALPHA), null_red, 1),
        # Fixed size isolates test choice from correction size.
        (
            "test_swap_fixed_alpha",
            f"test-swap only (alpha={ALPHA_PRIMARY:.2e})",
            {f"Bonferroni@{N_PRIMARY}": pv_red <= ALPHA_PRIMARY},
            null_red,
            1,
        ),
    ):
        res = {}
        for proc, rej in rejmap.items():
            v = (rej & nullmask).sum(axis=1)
            s = (rej & ~nullmask).sum(axis=1)
            tot = rej.sum(axis=1)
            # `contrasts` is ladder-major: the leading columns are contiguous blocks of
            # `tests_per_ladder` rung pairs, one block per ladder.
            ladders = (
                rej[:, : N_LADDERS * tests_per_ladder]
                .reshape(n_sims, N_LADDERS, tests_per_ladder)
                .any(axis=2)
            )
            res[proc] = {
                "true_rej": float(s.mean()),
                "false_rej": float(v.mean()),
                "fwer": float((v > 0).mean()),
                "fdr": float(np.where(tot > 0, v / np.maximum(tot, 1), 0.0).mean()),
                "ladders_flagged": float(ladders[:, ladder_nonflat].sum(axis=1).mean()),
                "power_per_true": float(s.mean() / max((~nullmask).sum(), 1)),
            }
            print(
                f"  [{name}] {proc:12s} trueRej={res[proc]['true_rej']:.2f} "
                f"FWER={res[proc]['fwer']:.4f} FDR={res[proc]['fdr']:.4f} "
                f"ladders={res[proc]['ladders_flagged']:.2f}",
                flush=True,
            )
        summaries[key] = res
    return {
        "n_sims": n_sims,
        "n_true": n_true,
        "n_null": int(is_null.sum()),
        "n_true_reduced": int((~null_red).sum()),
        "nonflat_ladders": int(ladder_nonflat.sum()),
        "true_deltas": sorted(set(np.round(true_diff[~is_null], 4).tolist())),
        **summaries,
        "rates": rates.tolist(),
    }


def main(results_dir: Path = RESULTS_DIR, out_path: Path | None = None) -> None:
    """Run and checkpoint all simulation parts.

    Part-number seeds keep reordering from changing draws.

    Parameters
    ----------
    results_dir : Path
        Study replicate tree and default checkpoint directory.
    out_path : Path | None
        Explicit checkpoint path, or the results-directory default.
    """
    out_path = results_dir / OUT_NAME if out_path is None else out_path
    t0 = time.time()
    out: dict[str, dict] = {}
    parts = (
        part1,
        functools.partial(part2, results_dir=results_dir),
        part3,
        part4,
        part5,
    )
    for i, part in enumerate(parts, 1):
        out[f"part{i}"] = part(np.random.default_rng(SEED + i))
        dump(out, out_path, f"part{i}")
    print(f"\nTOTAL {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
