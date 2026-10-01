"""Monte Carlo study of test and correction choices for the induction study.

PART 2 prints the study's measured design effect (`study_design_effect`) beside each
simulated `icc` block's; they differ in kind because `icc` is a latent share and
`design_effect` an observed variance ratio.

Rejection boundary: p-value tests reject at ``p <= alpha`` (`_power_common.apply_corrections`;
``test_apply_corrections_share_one_inclusive_boundary`` pins it); tests decided on a
chi-square statistic use ``stat > crit``, equivalent for a continuous statistic.
"""

import json
import os
import sys
import tempfile
import time
from itertools import combinations, product
from pathlib import Path
from typing import Optional

# Bare-name imports: sibling scripts from this directory, ``_power_common`` from ``notebooks/``.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _power_common import ALPHA, POWER_TARGETS, SEED, apply_corrections
from paired_analysis import design_effect, labeled_rows, load_marks
from scipy.stats import chi2, norm
from study_design import (
    ALPHA_OMNIBUS,
    ALPHA_PRIMARY,
    INFOS,
    MODELS,
    N_FAMILIES,
    N_HARMONICS,
    N_INFO_CONTRASTS,
    N_INFOS,
    N_LADDER_CONTRASTS,
    N_LADDERS,
    N_PRIMARY,
    N_REPLICATES,
    N_RUNGS,
    RESULTS_DIR,
    build_primary_contrasts,
    cmh_p,
    cmh_stat,
    gcmh_stat,
    mcnemar_exact_p,
)

from smolbench.evals.results_store import LocalResultsStore

#: Depths the eq_R search may advance to; the last is its ceiling.
_EQ_R_DEPTHS = (35, 40, 45, 50, 60, 70, 85, 100, 120, 145, 175, 210, 250)
_EQ_R_DEPTHS += (300, 360, 430, 520, 620, 750, 900)
#: Start at study depth so "pairing bought nothing" stays reachable, then
#: ascend through the depths beyond it (none when the study is at the ceiling).
EQ_R_GRID = (N_REPLICATES, *(depth for depth in _EQ_R_DEPTHS if depth > N_REPLICATES))

#: PART 4's planted ladders and PART 5's rate triples are written per rung.
SCENARIO_RUNGS = 3
if N_RUNGS != SCENARIO_RUNGS:
    raise RuntimeError(
        f"multiplicity_sim's scenarios are written for {SCENARIO_RUNGS}-rung "
        f"ladders; study_config.toml declares {N_RUNGS} rungs per family"
    )

#: Paired-vs-unpaired power gap treated as equal in the eq_R search: about one
#: Monte-Carlo standard error of a power estimate near 0.8 at N_SIMS.
EQ_R_TOL = 0.005

#: Include the unclustered baseline and plausible clustering range.
ICC_GRID = (0.0, 0.2, 0.4)

#: Replace each ladder's pairwise contrasts with one trend test.
N_REDUCED = N_LADDERS + N_PRIMARY - N_LADDER_CONTRASTS
#: Checkpoint file name; main() places it under the study results tree.
OUT_NAME = "multiplicity_sim_results.json"
#: PART 1 sizes the same gap at the corrected and the naive alpha.
_MDD_ALPHAS = (("bonf", ALPHA_PRIMARY), ("naive", ALPHA))


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
    # A per-call temp name: two runs sharing a results directory must not
    # write through, replace or unlink each other's pending checkpoint.
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


def _reject_rate(stat: np.ndarray, alpha: float, df: int) -> float:
    """Fraction of simulations whose chi-square statistic exceeds the `alpha` critical value."""
    return float((stat > chi2.isf(alpha, df)).mean())


def trend_stat(succ: np.ndarray, n: int) -> np.ndarray:
    """Compute the 1-df CMH linear trend across the three rungs.

    Parameters
    ----------
    succ : np.ndarray
        Success counts with trailing rung and harmonic axes.
    n : int
        Trials per cell.

    Returns
    -------
    np.ndarray
        Statistic per simulation; zero where variance is zero.
    """
    x = np.arange(1.0, N_RUNGS + 1)  # equally spaced rung scores 1..N_RUNGS
    total_n = float(N_RUNGS * n)
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


def _binary_phi(marks: np.ndarray) -> float:
    """Mean within-replicate correlation between distinct items on the last axis."""
    x = marks.astype(np.float64)
    mu = x.mean()
    cx = x - mu
    # mean over k<k' of E[cx_k cx_k'] / var
    k = x.shape[-1]
    cross = (cx.sum(axis=-1) ** 2 - (cx**2).sum(axis=-1)).mean() / (k * (k - 1))
    return float(cross / (mu * (1 - mu)))


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
    """Find minimum detectable differences at each ceiling at ``POWER_TARGETS[0]`` power.

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
    print(
        f"\n=== PART 1: minimum detectable difference ({POWER_TARGETS[0]:.0%} power) ===",
        flush=True,
    )
    rows = []
    for p_a in (0.99, 0.97, 0.95, 0.90, 0.70, 0.50):
        found = {}
        d = step
        while d <= min(p_a, 0.60) + 1e-9 and len(found) < len(_MDD_ALPHAS):
            p_b = max(0.0, p_a - d)
            sa = rng.binomial(N_REPLICATES, p_a, (n_sims, N_HARMONICS))
            sb = rng.binomial(N_REPLICATES, p_b, (n_sims, N_HARMONICS))
            st = cmh_stat(sa, sb, N_REPLICATES)
            for a_lab, a in _MDD_ALPHAS:
                if a_lab not in found:
                    pw = _reject_rate(st, a, 1)
                    if pw >= POWER_TARGETS[0]:
                        found[a_lab] = (round(d, 4), pw)
            d += step
        row = {"p_a": p_a}
        for a_lab, _ in _MDD_ALPHAS:
            row[f"mdd_{a_lab}"], row[f"pow_{a_lab}"] = found.get(a_lab, (None, None))
        mdd_bonf, mdd_naive = row["mdd_bonf"], row["mdd_naive"]
        row["ratio"] = mdd_bonf / mdd_naive if mdd_bonf and mdd_naive else None
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
    # ICC_GRID plus 0.1: the CMH Type-I inflation is already ~1.3x at icc=0.1
    # (measured), so PART 3 resolves its onset; PART 2 keeps the coarser grid
    # because each of its icc blocks runs the eq_R search.
    for p, icc, variant in product(
        (0.90, 0.70), (0.0, 0.1, 0.2, 0.4), ("independent", "shared")
    ):
        # p=0.70 re-runs only the independent variant: a shared latent cancels
        # in the paired CMH statistic, which the p=0.90 rows show at every icc;
        # the independent-latent inflation is what grows as p leaves the ceiling.
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
            # Three chunks suffice for the empirical binary within-replicate
            # correlation; later chunks feed only the rejection counts.
            if len(phis) < 3:
                phis.append(_binary_phi(ma))
            st = cmh_stat(ma.sum(axis=1), mb.sum(axis=1), N_REPLICATES)
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
    Family-local alphas (Bonferroni over the three pairwise tests, uncorrected
    trend and omnibus) isolate test choice from correction.
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
    for kind, rates in (
        ("monotone", (0.60, 0.75, 0.88)),
        ("non-monotone", (0.60, 0.88, 0.75)),
        ("monotone-small", (0.60, 0.66, 0.72)),
        ("non-monotone-small", (0.60, 0.72, 0.66)),
        ("monotone-ceiling", (0.99, 0.96, 0.93)),
        ("non-monotone-ceiling", (0.99, 0.93, 0.96)),
    ):
        label = f"{kind} " + "/".join(f"{r:.2f}" for r in rates)
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
        # "Any pairwise rejects" is "the largest pairwise statistic rejects".
        pair_max = np.max(pair_stats, axis=0)
        res = {
            "label": label,
            "rates": rates,
            "trend_studywide": _reject_rate(tr, alpha_trend_studywide, 1),
            # Same statistic at the narrower, not pre-registered, trend-only alpha.
            "trend_trend_only_family": _reject_rate(tr, alpha_trend_only, 1),
            "gcmh_studywide": _reject_rate(gc, ALPHA_OMNIBUS, N_RUNGS - 1),
            "pairwise_any_studywide": _reject_rate(pair_max, ALPHA_PRIMARY, 1),
            # Family-local alphas: Bonferroni over the pairwise tests only.
            "trend_local05": _reject_rate(tr, ALPHA, 1),
            "gcmh_local05": _reject_rate(gc, ALPHA, N_RUNGS - 1),
            "pairwise_any_local": _reject_rate(pair_max, ALPHA / len(pair_stats), 1),
        }
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
) -> tuple[float, float, Optional[float], Optional[float]]:
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
    unp = _reject_rate(cmh_stat(ma.sum(axis=1), mb.sum(axis=1), reps), ALPHA_PRIMARY, 1)
    b = (ma & ~mb).sum(axis=(1, 2))
    c = (~ma & mb).sum(axis=(1, 2))
    pv = mcnemar_exact_p(b, c)
    powers = unp, float((pv <= ALPHA_PRIMARY).mean())
    if not stats:
        # ``None`` distinguishes unmeasured diagnostics from zero.
        return *powers, None, None
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    return *powers, float(phi), float((ma == mb).mean())


def study_design_effect(results_dir: Path) -> Optional[float]:
    """Read the study's measured design effect.

    Return ``None`` when no study replicate lane exists (a checkpoint JSON alone
    does not count); propagate failures once data is present.

    Parameters
    ----------
    results_dir : Path
        Study replicate tree.

    Returns
    -------
    Optional[float]
        Median measurable design effect, or no measurable contrast.
    """
    store = LocalResultsStore(results_dir)
    if not any(
        store.list_seeds(None, model, info) for model in MODELS for info in INFOS
    ):
        return None
    rows = labeled_rows(load_marks(results_dir), build_primary_contrasts())
    deffs = [row["de"] for row in rows if row["de"] is not None]
    return float(np.median(deffs)) if deffs else None


def _pairing_gain_rows(
    rng: np.random.Generator, icc: float, n_sims: int, search_sims: int
) -> list[dict]:
    """Power rows for one `icc`, each with its eq_R grid search, printed as computed."""
    rows = []
    for p_a, delta, rho in product(
        (0.95, 0.70), (0.05, 0.10), (0.0, 0.3, 0.5, 0.7, 0.9)
    ):
        # p_A=0.70 checks that the ceiling-rate pairing gain persists off
        # the ceiling; two mid rhos suffice, and each extra row costs an
        # eq_R search per icc block.
        if p_a == 0.70 and rho not in (0.5, 0.7):
            continue
        unp, pair, phi, agree = _paired_powers(
            p_a, delta, rho, N_REPLICATES, n_sims, rng, icc=icc
        )
        # Smallest R where the unpaired test matches paired power at study depth.
        within_tol = pair <= unp + EQ_R_TOL
        eq_r = N_REPLICATES if within_tol else None
        if not within_tol:
            for rr in EQ_R_GRID:
                # stats=False: only unpaired power is read here.
                u2 = _paired_powers(
                    p_a, delta, rho, rr, search_sims, rng, stats=False, icc=icc
                )[0]
                if u2 >= pair - EQ_R_TOL:
                    eq_r = rr
                    break
        rows.append(
            {
                "p_a": p_a,
                "delta": delta,
                "rho": rho,
                "power_unpaired": unp,
                "power_paired": pair,
                "eq_R": eq_r,
                # Whether a matching depth beyond study depth was found, not
                # whether the search ran.
                "eq_r_advanced": eq_r is not None and eq_r != N_REPLICATES,
                "cap": EQ_R_GRID[-1],
                "phi_binary": phi,
                "agreement": agree,
                "eq_ratio": None if eq_r is None else eq_r / N_REPLICATES,
                "icc": icc,
            }
        )
        suffix = f" (gap <= {EQ_R_TOL}, unsearched)" if within_tol else ""
        print(
            f"  icc={icc} p_A={p_a} d={delta} rho={rho}: "
            f"phi_bin={phi:.3f} agree={agree:.3f} "
            f"unpaired={unp:.4f} paired(item-McNemar)={pair:.4f} "
            f"eqR={eq_r}{suffix}",
            flush=True,
        )
    return rows


def _null_calibration(
    rng: np.random.Generator, icc: float, null_sims: int
) -> dict[float, dict[str, float]]:
    """Unpaired and item-McNemar Type-I rates at p_a = p_b = 0.90 for rho in (0.0, 0.5, 0.9), printed as computed."""
    nulls = {}
    for rho in (0.0, 0.5, 0.9):
        # 60000 draws give ~14 expected null rejections at ALPHA_PRIMARY,
        # enough to resolve the McNemar inflation.
        u, p = _paired_powers(
            0.90, 0.0, rho, N_REPLICATES, null_sims, rng, stats=False, icc=icc
        )[:2]
        nulls[rho] = {"unpaired_t1": u, "mcnemar_t1": p}
        print(
            f"  icc={icc} NULL rho={rho}: unpaired T1={u:.6f} mcnemar T1={p:.6f}",
            flush=True,
        )
    return nulls


def _simulated_design_effect(
    rng: np.random.Generator, icc: float, n_sims: int
) -> Optional[float]:
    """Median measurable design effect of null marks at rho=0.5, printed; ``None`` when none is measurable."""
    # Match the null calibration at p_a=p_b=0.90, rho=0.5.
    ma, mb = paired_marks(0.90, 0.90, 0.5, n_sims, N_REPLICATES, rng, icc=icc)
    seed_idx = np.repeat(np.arange(N_REPLICATES), N_HARMONICS)
    harm_idx = np.tile(np.arange(N_HARMONICS), N_REPLICATES)
    deffs = [
        design_effect(ma[i].ravel(), mb[i].ravel(), seed_idx, harm_idx)
        for i in range(n_sims)
    ]
    measurable = [d for d in deffs if d is not None]
    # An unmeasurable block must not report a placeholder number.
    deff_sim = float(np.median(measurable)) if measurable else None
    print(
        f"  icc={icc} design_effect_simulated: "
        + (
            f"{deff_sim:.3f} (median of {len(measurable)}/{n_sims} measurable)"
            if measurable
            else f"no measurable ratio in {n_sims} simulations"
        ),
        flush=True,
    )
    return deff_sim


def part2(
    rng: np.random.Generator,
    results_dir: Path,
    n_sims: int = 20000,
    search_sims: int = 8000,
    null_sims: int = 60000,
) -> dict:
    """Measure pairing gains over unpaired testing.

    McNemar is anticonservative at ``icc > 0``, biasing ``eq_R`` upward;
    compare each simulated design effect with the study estimate. Power gaps
    within `EQ_R_TOL` (Monte-Carlo error) are reported unsearched at `N_REPLICATES`.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    results_dir : Path
        Study replicate tree for the measured design effect.
    n_sims, search_sims, null_sims : int, optional
        Main power, per-rung equivalent-R search, and null-calibration simulation counts.

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
    icc_blocks = {}
    for icc in ICC_GRID:
        print(f"\n--- PART 2 table, icc={icc} ---", flush=True)
        # Rows, nulls, then the design effect: the RNG draw order main() checkpoints.
        rows = _pairing_gain_rows(rng, icc, n_sims, search_sims)
        nulls = _null_calibration(rng, icc, null_sims)
        deff_sim = _simulated_design_effect(rng, icc, n_sims)
        icc_blocks[str(icc)] = {
            "rows": rows,
            "nulls": nulls,
            "design_effect_simulated": deff_sim,
        }

    # icc keys are strings: JSON has no float keys.
    return {
        "n_sims": n_sims,
        "alpha": ALPHA_PRIMARY,
        "grid_r": list(EQ_R_GRID),
        "icc": icc_blocks,
    }


def _correction_summary(
    rej: np.ndarray, nullmask: np.ndarray, ladder_nonflat: np.ndarray
) -> dict[str, float]:
    """True/false rejections, FWER, FDR, flagged ladders and per-true power of one rejection mask."""
    v = (rej & nullmask).sum(axis=1)
    s = (rej & ~nullmask).sum(axis=1)
    tot = rej.sum(axis=1)
    # `contrasts` is ladder-major: the leading columns are one contiguous block
    # of rung-pair tests per ladder (3 in the full family, 1 trend test in the
    # reduced one); the trailing N_INFO_CONTRASTS columns are the same in both.
    ladders = (
        rej[:, : rej.shape[1] - N_INFO_CONTRASTS]
        .reshape(rej.shape[0], N_LADDERS, -1)
        .any(axis=2)
    )
    return {
        "true_rej": float(s.mean()),
        "false_rej": float(v.mean()),
        "fwer": float((v > 0).mean()),
        "fdr": float(np.where(tot > 0, v / np.maximum(tot, 1), 0.0).mean()),
        "ladders_flagged": float(ladders[:, ladder_nonflat].sum(axis=1).mean()),
        "power_per_true": float(s.mean() / max((~nullmask).sum(), 1)),
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
    # Family 0 is a ceiling ladder at every info (12 ladder effects). Ladders (1, info 1)
    # and (2, info 1) plant mid-range effects (6 ladder effects), and because only
    # info 1 moves there, the info-arm contrasts of rungs 1 and 2 that touch info 1
    # are also true effects (12); the remaining 180 contrasts are null.
    rates = np.empty((N_FAMILIES, N_RUNGS, N_INFOS))
    # Broadcasting raises if the family count ever disagrees with these rates.
    rates[:] = np.array([0.99, 0.97, 0.95, 0.92, 0.85, 0.75, 0.62])[:, None, None]
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
    n_true_ladder = int((~is_null[:N_LADDER_CONTRASTS]).sum())
    ladder_rates = rates.transpose(0, 2, 1).reshape(N_LADDERS, N_RUNGS)
    ladder_nonflat = ~np.all(ladder_rates == ladder_rates[:, :1], axis=1)
    print(
        f"  config: {n_true} true effects ({n_true_ladder} ladder, "
        f"{n_true - n_true_ladder} info-arm) / {int(is_null.sum())} true nulls; "
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
    for key, name, rejmap, nullmask in (
        ("full", f"m={N_PRIMARY}", apply_corrections(pv, ALPHA), is_null),
        ("reduced", f"m={N_REDUCED}", apply_corrections(pv_red, ALPHA), null_red),
        # Fixed size isolates test choice from correction size.
        (
            "test_swap_fixed_alpha",
            f"test-swap only (alpha={ALPHA_PRIMARY:.2e})",
            {f"Bonferroni@{N_PRIMARY}": pv_red <= ALPHA_PRIMARY},
            null_red,
        ),
    ):
        res = {}
        for proc, rej in rejmap.items():
            res[proc] = _correction_summary(rej, nullmask, ladder_nonflat)
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


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Run and checkpoint all simulation parts.

    Part-number seeds keep reordering from changing draws.

    Parameters
    ----------
    results_dir : Path
        Study replicate tree; the checkpoint is written inside it as ``OUT_NAME``.
    """
    t0 = time.time()
    out: dict[str, dict] = {}
    parts = (part1, lambda rng: part2(rng, results_dir), part3, part4, part5)
    for i, part in enumerate(parts, 1):
        out[f"part{i}"] = part(np.random.default_rng(SEED + i))
        dump(out, results_dir / OUT_NAME, f"part{i}")
    print(f"\nTOTAL {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
