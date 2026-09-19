"""Monte Carlo study of test and correction choices for the induction study.

`study_design_effect` compares the observed design effect with simulated `icc` clustering;
they differ because `icc` is latent share and `design_effect` an observed variance ratio.

Rejection boundary: a p-value rejects when ``p <= alpha`` (the statsmodels convention
`paired_analysis.holm` and `significance_report.hochberg` follow). Tests decided on a
chi-square statistic use ``stat > crit``, equivalent for a continuous statistic.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

# Anchor paths to this file so sibling imports do not depend on invocation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from _power_common import ALPHA, SEED, results_dir
from power_analysis import (
    ALPHA_PRIMARY,
    N_HARMONICS,
    N_PRIMARY,
    cmh_p,
    cmh_stat,
    gcmh_stat,
    mcnemar_exact_p,
)
from scipy.stats import chi2

from smolbench.evals.results_store import LocalResultsStore

K_HARM = N_HARMONICS
ALPHA_BONF = ALPHA_PRIMARY

R_DEFAULT = 30  # Avoid importing run_study, which freezes EC2 configuration.

# Equivalent-R search ladder, starting at R_DEFAULT so "pairing bought nothing" stays reachable.
EQ_R_GRID = (
    R_DEFAULT,
    35,
    40,
    45,
    50,
    60,
    70,
    85,
    100,
    120,
    145,
    175,
    210,
    250,
    300,
    360,
    430,
    520,
    620,
    750,
    900,
)

# Include the unclustered baseline and plausible clustering range.
ICC_GRID = (0.0, 0.2, 0.4)

N_REDUCED = (
    154  # 28 trend tests replacing 84 ladder contrasts + the 126 shared info contrasts.
)

OUT = {}
# Anchor checkpoints to the study results tree.
OUT_PATH = results_dir(__file__, up=1) / "multiplicity_sim_results.json"


def dump(tag: str) -> None:
    """Write `OUT` to the checkpoint JSON.

    Create the directory only when checkpointing so imports do not write.

    Parameters
    ----------
    tag : str
        Checkpoint label written to the log.
    """
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=OUT_PATH.name + ".", suffix=".tmp", dir=OUT_PATH.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(OUT, fh, indent=2, default=float)
        os.replace(tmp_name, OUT_PATH)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"[checkpoint written after {tag}]", flush=True)


def trend_stat(
    succ: np.ndarray, n: int, scores: tuple[float, ...] = (1.0, 2.0, 3.0)
) -> np.ndarray:
    """1-df CMH correlation (linear trend) statistic across the 3 rungs, `n` trials per cell."""
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

    Skip clustering draws at zero `icc` to preserve RNG order. The replicate latents are
    correlated at `rho` like the item latents, so mixing them in at `icc` leaves the
    cross-arm latent correlation at `rho` instead of attenuating it to ``(1 - icc) * rho``.

    Parameters
    ----------
    p_a : float
        Marginal mark rate for arm A.
    p_b : float
        Marginal mark rate for arm B.
    rho : float
        Tetrachoric correlation between matched marks.
    n_sims : int
        Number of simulated experiments.
    reps : int
        Number of replicates per experiment.
    rng : np.random.Generator
        Random generator for latent draws.
    icc : float, optional
        Shared per-replicate latent variance fraction; default is zero.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Simulated Boolean marks for arms A and B.
    """
    if not 0.0 <= icc < 1.0:
        raise ValueError(f"icc must be in [0.0, 1.0), got {icc!r}")
    z1 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    z2 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    zb = rho * z1 + np.sqrt(max(1.0 - rho * rho, 0.0)) * z2
    if icc > 0.0:
        u_a = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        u_b = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        u_b = rho * u_a + np.sqrt(max(1.0 - rho * rho, 0.0)) * u_b
        w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
        z1 = w1 * u_a + w2 * z1
        zb = w1 * u_b + w2 * zb
    from scipy.stats import norm

    return z1 < norm.ppf(p_a), zb < norm.ppf(p_b)


def part1(rng: np.random.Generator, n_sims: int = 20000, step: float = 0.0025) -> None:
    """Find minimum detectable differences at each ceiling.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Number of simulations per baseline rate and gap.
    step : float, optional
        Accuracy-gap increment to scan.
    """
    print("\n=== PART 1: minimum detectable difference (80% power) ===", flush=True)
    rows = []
    for p_a in (0.99, 0.97, 0.95, 0.90, 0.70, 0.50):
        found = {}
        d = step
        while d <= min(p_a, 0.60) + 1e-9 and len(found) < 2:
            p_b = p_a - d
            sa = rng.binomial(R_DEFAULT, p_a, (n_sims, K_HARM))
            sb = rng.binomial(R_DEFAULT, p_b, (n_sims, K_HARM))
            st = cmh_stat(sa, sb, R_DEFAULT)
            for a_lab, a in (("bonf", ALPHA_BONF), ("naive", ALPHA)):
                if a_lab not in found:
                    pw = (st > chi2.isf(a, df=1)).mean()
                    if pw >= 0.80:
                        found[a_lab] = (round(d, 4), float(pw))
            d += step
        row = {
            "p_a": p_a,
            "mdd_bonf": found.get("bonf", (None, None))[0],
            "pow_bonf": found.get("bonf", (None, None))[1],
            "mdd_naive": found.get("naive", (None, None))[0],
            "pow_naive": found.get("naive", (None, None))[1],
        }
        row["ratio"] = (
            row["mdd_bonf"] / row["mdd_naive"]
            if row["mdd_bonf"] and row["mdd_naive"]
            else None
        )
        rows.append(row)
        print(
            f"  p_A={p_a:.2f}  MDD(alpha=2.38e-4)={row['mdd_bonf']}  "
            f"MDD(alpha=0.05)={row['mdd_naive']}  ratio={row['ratio']}",
            flush=True,
        )
    OUT["part1"] = {"n_sims": n_sims, "grid_step": step, "rows": rows}


def part3(rng: np.random.Generator, n_sims: int = 200000, chunk: int = 20000) -> None:
    """Measure Type I error under within-replicate clustering.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    n_sims : int, optional
        Total simulations per grid configuration.
    chunk : int, optional
        Bounds peak memory.
    """
    print(
        "\n=== PART 3: within-replicate clustering -> actual Type I error ===",
        flush=True,
    )
    from scipy.stats import norm

    crit05 = chi2.isf(ALPHA, df=1)
    critb = chi2.isf(ALPHA_BONF, df=1)
    rows = []
    for p in (0.90, 0.70):
        for icc in (0.0, 0.1, 0.2, 0.4):
            for variant in ("independent", "shared"):
                if p == 0.70 and variant == "shared":
                    continue
                thr = norm.ppf(p)
                r05 = rb = 0
                done = 0
                phis = []
                while done < n_sims:
                    s = min(chunk, n_sims - done)
                    u_a = rng.standard_normal((s, R_DEFAULT, 1), dtype=np.float32)
                    u_b = (
                        u_a
                        if variant == "shared"
                        else rng.standard_normal((s, R_DEFAULT, 1), dtype=np.float32)
                    )
                    ea = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
                    eb = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
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
                            K_HARM * (K_HARM - 1)
                        )
                        phis.append(cross / (mu * (1 - mu)))
                    sa = ma.sum(axis=1)
                    sb = mb.sum(axis=1)
                    st = cmh_stat(sa, sb, R_DEFAULT)
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
                    "inflb": (rb / n_sims) / ALPHA_BONF,
                    "n_sims": n_sims,
                }
                rows.append(row)
                print(
                    f"  p={p} icc={icc} {variant:11s} phi_bin={row['phi_binary']:.3f} "
                    f"T1@0.05={row['t1_alpha05']:.4f} ({row['infl05']:.2f}x)  "
                    f"T1@2.38e-4={row['t1_alpha_bonf']:.6f} ({row['inflb']:.2f}x)",
                    flush=True,
                )
    OUT["part3"] = {"rows": rows}


# ============================================================ PART 5: trend vs pairwise
def part5(rng: np.random.Generator, n_sims: int = 20000) -> None:
    """Compare the 1-df trend test against the 2-df omnibus and 3 pairwise tests.

    Six rate scenarios (monotone/non-monotone at small, mid and ceiling
    effect sizes), one simulated 3-rung ladder each, reporting rejection rate
    under the study-wide alphas and again under local uncorrected-family
    alphas, to isolate test choice from correction. Writes ``OUT["part5"]``.

    The trend test is priced twice: `trend_studywide` at ``ALPHA /
    N_REDUCED``, the family PART 4 actually puts it in (comparable to the
    pairwise row's ``ALPHA / N_PRIMARY``); `trend_trend_only_family` at the
    narrower ``ALPHA / 28``, correcting only among the trend tests
    themselves, reported as a labelled sensitivity figure since that
    narrower family is not pre-registered anywhere.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Simulations per rate scenario.
    """
    print("\n=== PART 5: 1-df trend vs 2-df omnibus vs 3 pairwise ===", flush=True)
    # The same 28 trend tests as PART 4's reduced family, corrected comparably to pairwise.
    alpha_trend_studywide = ALPHA / N_REDUCED
    # Sensitivity only: correcting the 28 trend tests among themselves.
    alpha_trend_only = ALPHA / 28
    alpha_pair = ALPHA_BONF  # pairwise inside the 210 family
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
            [rng.binomial(R_DEFAULT, r, (n_sims, K_HARM)) for r in rates], axis=1
        )
        tr = trend_stat(succ, R_DEFAULT)
        gc = gcmh_stat(succ, R_DEFAULT)
        pair_stats = [
            cmh_stat(succ[:, i, :], succ[:, j, :], R_DEFAULT)
            for i, j in ((0, 1), (1, 2), (0, 2))
        ]
        res = {"label": label, "rates": rates}
        # study-wide alphas
        res["trend_studywide"] = float((tr > chi2.isf(alpha_trend_studywide, 1)).mean())
        # Same statistic at the narrower, not pre-registered, trend-only alpha.
        res["trend_trend_only_family"] = float(
            (tr > chi2.isf(alpha_trend_only, 1)).mean()
        )
        res["gcmh_studywide"] = float((gc > chi2.isf(ALPHA / 7, 2)).mean())
        res["pairwise_any_studywide"] = float(
            np.any([s > chi2.isf(alpha_pair, 1) for s in pair_stats], axis=0).mean()
        )
        # local, uncorrected-family alphas (test choice isolated from correction)
        res["trend_local05"] = float((tr > chi2.isf(ALPHA, 1)).mean())
        res["gcmh_local05"] = float((gc > chi2.isf(ALPHA, 2)).mean())
        res["pairwise_any_local"] = float(
            np.any([s > chi2.isf(ALPHA / 3, 1) for s in pair_stats], axis=0).mean()
        )
        rows.append(res)
        print(f"  {label}", flush=True)
        print(
            f"    study-wide: trend[a=.05/{N_REDUCED}]="
            f"{res['trend_studywide']:.4f} "
            f"gcmh(2df)[a=.05/7]={res['gcmh_studywide']:.4f} "
            f"any-pairwise[a=.05/{N_PRIMARY}]="
            f"{res['pairwise_any_studywide']:.4f}",
            flush=True,
        )
        print(
            f"    sensitivity: trend[a=.05/28, trend-only family, "
            f"not pre-registered]={res['trend_trend_only_family']:.4f}",
            flush=True,
        )
        print(
            f"    local a=.05: trend={res['trend_local05']:.4f} "
            f"gcmh={res['gcmh_local05']:.4f} any-pairwise={res['pairwise_any_local']:.4f}",
            flush=True,
        )
    OUT["part5"] = {
        "rows": rows,
        "n_sims": n_sims,
        "alpha_trend_studywide": alpha_trend_studywide,
        "alpha_trend_only": alpha_trend_only,
        "alpha_pairwise": ALPHA_BONF,
        "alpha_gcmh": ALPHA / 7,
    }


# ================================================================== PART 2: pairing gain
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

    Disabling diagnostics preserves powers and avoids costly float upcasts.

    Parameters
    ----------
    p_a : float
        Baseline success rate for arm A.
    delta : float
        Success-rate gap subtracted from `p_a` for arm B.
    rho : float
        Latent correlation between matched arm marks.
    reps : int
        Replicates in each simulation.
    n_sims : int
        Number of simulated datasets.
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
    p_b = p_a - delta
    ma, mb = paired_marks(p_a, p_b, rho, n_sims, reps, rng, icc=icc)
    sa = ma.sum(axis=1)
    sb = mb.sum(axis=1)
    unp = (cmh_stat(sa, sb, reps) > chi2.isf(ALPHA_BONF, 1)).mean()
    b = (ma & ~mb).sum(axis=(1, 2))
    c = (~ma & mb).sum(axis=(1, 2))
    pv = mcnemar_exact_p(b, c)
    powers = float(unp), float((pv <= ALPHA_BONF).mean())
    if not stats:
        # ``None`` distinguishes unmeasured diagnostics from zero.
        return powers[0], powers[1], None, None
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    agree = float((ma == mb).mean())
    return powers[0], powers[1], float(phi), agree


def study_design_effect() -> float | None:
    """Read the study's measured design effect.

    Return ``None`` when no study replicate lane exists (a checkpoint JSON alone
    does not count); propagate failures once data is present.
    """
    # Avoid results-reading import effects during simulation imports.
    import paired_analysis
    import power_analysis

    store = LocalResultsStore(paired_analysis.RESULTS_DIR)
    if not any(
        store.list_seeds(None, model, info)
        for model in power_analysis.MODELS
        for info in power_analysis.INFOS
    ):
        return None
    correct, valid, _compliance = paired_analysis.load_marks()
    deffs = []
    for _label, key_a, key_b in power_analysis.build_primary_contrasts():
        a, b, seed_idx, harm_idx = paired_analysis.aligned(
            correct, valid, key_a, key_b, drop_invalid=False
        )
        d = paired_analysis.design_effect(a, b, seed_idx, harm_idx)
        if d is not None:
            deffs.append(d)
    return float(np.median(deffs)) if deffs else None


def part2(
    rng: np.random.Generator,
    n_sims: int = 20000,
    search_sims: int = 8000,
) -> None:
    """Measure pairing gains over unpaired testing.

    Compare simulated `design_effect` at each `icc` with the study
    estimate.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    n_sims : int, optional
        Number of simulations for the main power calculations.
    search_sims : int, optional
        Number of simulations at each equivalent-R search rung.
    """
    # Avoid results-reading import effects during simulation imports.
    import paired_analysis

    measured = study_design_effect()
    measured_str = (
        f"{measured:.3f}"
        if measured is not None
        else f"unknown (no results tree at {paired_analysis.RESULTS_DIR})"
    )
    print("\n=== PART 2: pairing gain (matched items) ===", flush=True)
    print(
        f"  study's own measured design effect: {measured_str} -- compare "
        f"against each icc block's design_effect_simulated below",
        flush=True,
    )
    grid_r = list(EQ_R_GRID)
    icc_blocks: dict[str, dict] = {}
    for icc in ICC_GRID:
        print(f"\n--- PART 2 table, icc={icc} ---", flush=True)
        rows = []
        for p_a in (0.95, 0.70):
            for delta in (0.05, 0.10):
                for rho in (0.0, 0.3, 0.5, 0.7, 0.9):
                    if p_a == 0.70 and rho not in (0.5, 0.7):
                        continue
                    unp, pair, phi, agree = _paired_powers(
                        p_a, delta, rho, R_DEFAULT, n_sims, rng, icc=icc
                    )
                    # Smallest R where the unpaired test matches paired power at R_DEFAULT.
                    eq_r = None
                    if pair > unp + 0.005:
                        for rr in grid_r:
                            # stats=False: only unpaired power is read here.
                            u2 = _paired_powers(
                                p_a,
                                delta,
                                rho,
                                rr,
                                search_sims,
                                rng,
                                stats=False,
                                icc=icc,
                            )[0]
                            if u2 >= pair:
                                eq_r = rr
                                break
                    else:
                        # eq_searched distinguishes "matched by search" from "unsearched".
                        eq_r = R_DEFAULT
                    rows.append(
                        {
                            "p_a": p_a,
                            "delta": delta,
                            "rho": rho,
                            "power_unpaired": unp,
                            "power_paired": pair,
                            "eq_R": eq_r,
                            "eq_searched": pair > unp + 0.005,
                            "cap": EQ_R_GRID[-1],
                            "phi_binary": phi,
                            "agreement": agree,
                            "eq_ratio": None if eq_r is None else eq_r / R_DEFAULT,
                            "icc": icc,
                        }
                    )
                    print(
                        f"  icc={icc} p_A={p_a} d={delta} rho={rho}: "
                        f"phi_bin={phi:.3f} agree={agree:.3f} "
                        f"unpaired={unp:.4f} paired={pair:.4f} eqR={eq_r}",
                        flush=True,
                    )
        # null calibration of both tests under matched data
        nulls = {}
        for rho in (0.0, 0.5, 0.9):
            # stats=False as above; `[:2]` drops the unread diagnostics.
            u, p = _paired_powers(
                0.90, 0.0, rho, R_DEFAULT, 60000, rng, stats=False, icc=icc
            )[:2]
            nulls[rho] = {"unpaired_t1": u, "mcnemar_t1": p}
            print(
                f"  icc={icc} NULL rho={rho}: unpaired T1={u:.6f} "
                f"mcnemar T1={p:.6f}",
                flush=True,
            )

        # This block's own design_effect under the null config above (p_a=p_b=0.90, rho=0.5).
        ma, mb = paired_marks(0.90, 0.90, 0.5, n_sims, R_DEFAULT, rng, icc=icc)
        seed_idx = np.repeat(np.arange(R_DEFAULT), K_HARM)
        harm_idx = np.tile(np.arange(K_HARM), R_DEFAULT)
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
            # No placeholder number: a genuinely unmeasurable block says so.
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
    OUT["part2"] = {
        "n_sims": n_sims,
        "alpha": ALPHA_BONF,
        "grid_r": grid_r,
        "icc": icc_blocks,
    }


def build_rate_matrix() -> np.ndarray:
    """Build the stylized true-rate matrix for PART 4.

    30 true effects near ceiling and mid-range; the remaining 180 contrasts are exact nulls.
    """
    rates = np.zeros((7, 3, 4))
    flat = [0.99, 0.97, 0.95, 0.92, 0.85, 0.75, 0.62]
    for f in range(7):
        rates[f, :, :] = flat[f]
    for i in range(4):
        rates[0, :, i] = [0.99, 0.96, 0.925]
    rates[1, :, 1] = [0.97, 0.91, 0.83]
    rates[2, :, 1] = [0.95, 0.86, 0.74]
    return rates


def _stepup(
    sortedp: np.ndarray, order: np.ndarray, thresholds: np.ndarray
) -> np.ndarray:
    """Apply step-up thresholds and restore input order.

    A ``-1`` sentinel leaves rows with no passing p-value unrejected.

    Parameters
    ----------
    sortedp : np.ndarray
        P-values sorted in ascending order per row.
    order : np.ndarray
        Indices that map sorted p-values to input order.
    thresholds : np.ndarray
        Per-rank rejection thresholds.

    Returns
    -------
    np.ndarray
        Rejection mask in input order.
    """
    m = sortedp.shape[1]
    ok = sortedp <= thresholds
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(sortedp, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    return rej


def apply_corrections(pv: np.ndarray) -> dict[str, np.ndarray]:
    """Apply multiple-testing procedures to p-value families.

    Derive family size from input to prevent mismatched thresholds.

    Parameters
    ----------
    pv : np.ndarray
        Batch of p-value families, one family per row.

    Returns
    -------
    dict[str, np.ndarray]
        One rejection mask per procedure, in `pv`'s original column order.
    """
    m = pv.shape[1]
    out = {}
    order = np.argsort(pv, axis=1)
    sortedp = np.take_along_axis(pv, order, axis=1)
    ranks = np.arange(1, m + 1)
    out["Bonferroni"] = pv <= ALPHA / m
    thr = ALPHA / (m - ranks + 1)
    viol = sortedp > thr
    first = np.where(viol.any(axis=1), viol.argmax(axis=1), m)
    keep = np.arange(m)[None, :] < first[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Holm"] = rej
    out["Hochberg"] = _stepup(sortedp, order, thr)
    bh_thr = ALPHA * ranks / m
    out["BH(q=0.05)"] = _stepup(sortedp, order, bh_thr)
    return out


def part4(rng: np.random.Generator, n_sims: int = 4000) -> None:
    """Measure multiplicity-correction cost against known truth.

    The fixed-size trend arm separates test choice from correction-family size.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated counts.
    n_sims : int, optional
        Number of simulated p-value families.
    """
    print("\n=== PART 4: correction cost ===", flush=True)
    rates = build_rate_matrix()
    lad_idx, info_idx, ladder_of_pair = [], [], []
    for f in range(7):
        for i in range(4):
            for a, b in ((0, 1), (1, 2), (0, 2)):
                lad_idx.append((f, a, i, f, b, i))
                ladder_of_pair.append(f * 4 + i)
    for f in range(7):
        for r in range(3):
            for a, b in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)):
                info_idx.append((f, r, a, f, r, b))
    contrasts = lad_idx + info_idx
    m_full = len(contrasts)
    # Raise survives ``-O``; this family sets every correction denominator.
    if m_full != N_PRIMARY:
        raise RuntimeError(
            f"PART 4 built {m_full} contrasts but N_PRIMARY = {N_PRIMARY}; "
            "the simulated Bonferroni alpha would be wrong."
        )
    true_diff = np.array(
        [abs(rates[c[0], c[1], c[2]] - rates[c[3], c[4], c[5]]) for c in contrasts]
    )
    is_null = true_diff == 0.0
    n_true = int((~is_null).sum())
    ladder_rates = np.array(
        [[rates[f, r, i] for r in range(3)] for f in range(7) for i in range(4)]
    )
    ladder_nonflat = ~np.all(ladder_rates == ladder_rates[:, :1], axis=1)
    print(
        f"  config: {n_true} true effects / {int(is_null.sum())} true nulls; "
        f"non-flat ladders = {int(ladder_nonflat.sum())}/28",
        flush=True,
    )
    print(f"  true-effect deltas: {np.sort(true_diff[~is_null])}", flush=True)

    succ = np.empty((n_sims, 7, 3, 4, K_HARM), dtype=np.int32)
    for f in range(7):
        for r in range(3):
            for i in range(4):
                succ[:, f, r, i, :] = rng.binomial(
                    R_DEFAULT, rates[f, r, i], (n_sims, K_HARM)
                )
    pv = np.empty((n_sims, m_full))
    for t, c in enumerate(contrasts):
        pv[:, t] = cmh_p(
            succ[:, c[0], c[1], c[2], :], succ[:, c[3], c[4], c[5], :], R_DEFAULT
        )
    trend_p = np.empty((n_sims, 28))
    t = 0
    for f in range(7):
        for i in range(4):
            trend_p[:, t] = chi2.sf(trend_stat(succ[:, f, :, i, :], R_DEFAULT), df=1)
            t += 1
    pv_red = np.concatenate([trend_p, pv[:, 84:]], axis=1)
    null_red = np.concatenate([~ladder_nonflat, is_null[84:]])
    m_red = pv_red.shape[1]
    # PART 5 uses this reduced-family correction denominator.
    if m_red != N_REDUCED:
        raise RuntimeError(
            f"PART 4 built {m_red} reduced tests but N_REDUCED = {N_REDUCED}; "
            "PART 5's study-wide alpha would be wrong."
        )

    def summarize(
        name: str,
        rejmap: dict[str, np.ndarray],
        nullmask: np.ndarray,
        ladder_flag_fn: Callable[[np.ndarray], np.ndarray],
    ) -> dict[str, dict]:
        res = {}
        for proc, rej in rejmap.items():
            v = (rej & nullmask).sum(axis=1)
            s = (rej & ~nullmask).sum(axis=1)
            tot = rej.sum(axis=1)
            res[proc] = {
                "true_rej": float(s.mean()),
                "false_rej": float(v.mean()),
                "fwer": float((v > 0).mean()),
                "fdr": float(np.where(tot > 0, v / np.maximum(tot, 1), 0.0).mean()),
                "ladders_flagged": float(ladder_flag_fn(rej).mean()),
                "power_per_true": float(s.mean() / max((~nullmask).sum(), 1)),
            }
            print(
                f"  [{name}] {proc:12s} trueRej={res[proc]['true_rej']:.2f} "
                f"FWER={res[proc]['fwer']:.4f} FDR={res[proc]['fdr']:.4f} "
                f"ladders={res[proc]['ladders_flagged']:.2f}",
                flush=True,
            )
        return res

    lad_pair_ladder = np.array(ladder_of_pair)

    def flag_full(rej: np.ndarray) -> np.ndarray:
        nf = np.where(ladder_nonflat)[0]
        got = np.zeros((rej.shape[0], 28), dtype=bool)
        for t_ in range(84):
            got[:, lad_pair_ladder[t_]] |= rej[:, t_]
        return got[:, nf].sum(axis=1)

    def flag_red(rej: np.ndarray) -> np.ndarray:
        nf = np.where(ladder_nonflat)[0]
        return rej[:, :28][:, nf].sum(axis=1)

    full = summarize("m=210", apply_corrections(pv), is_null, flag_full)
    red2 = summarize("m=154", apply_corrections(pv_red), null_red, flag_red)
    # Fixed size isolates test choice from correction size.
    fixed_alpha = summarize(
        "test-swap only (alpha=0.05/210)",
        {"Bonferroni@210": pv_red <= ALPHA / N_PRIMARY},
        null_red,
        flag_red,
    )
    OUT["part4"] = {
        "n_sims": n_sims,
        "n_true": n_true,
        "n_null": int(is_null.sum()),
        "n_true_reduced": int((~null_red).sum()),
        "nonflat_ladders": int(ladder_nonflat.sum()),
        "true_deltas": sorted(set(np.round(true_diff[~is_null], 4).tolist())),
        "full": full,
        "reduced": red2,
        "test_swap_fixed_alpha": fixed_alpha,
        "rates": rates.tolist(),
    }


def main() -> None:
    """Run and checkpoint all simulation parts.

    Part-number seeds keep reordering from changing draws.
    """
    t0 = time.time()
    part1(np.random.default_rng(SEED + 1))
    dump("part1")
    part3(np.random.default_rng(SEED + 3))
    dump("part3")
    part5(np.random.default_rng(SEED + 5))
    dump("part5")
    part2(np.random.default_rng(SEED + 2))
    dump("part2")
    part4(np.random.default_rng(SEED + 4))
    dump("part4")
    print(f"\nTOTAL {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
