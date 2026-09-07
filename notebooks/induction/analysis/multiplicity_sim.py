"""Monte Carlo study of TEST and CORRECTION choice for the induction study.

Companion to the family-ladder study (21 models x 4 info arms, R=30 x 9
harmonics); everything here is simulated except `study_design_effect`, which
reads the study's own measured design effect (`paired_analysis.design_effect`)
so PART 2's icc rows can be compared against it -- `None` on a fresh
checkout. Design constants are imported from `_power_common`/`power_analysis`,
never re-declared, so a re-sizing cannot apply to only one of the two. PART
2's icc grid models the study's within-replicate clustering; `1 + (k-1)*icc`
is not used to relate icc to design_effect since the two are different
scales (latent share vs observed variance ratio).

Run (repo root):
  .venv/bin/python notebooks/induction/analysis/multiplicity_sim.py
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable
from pathlib import Path

# __file__-anchored, not cwd-relative, so the sibling imports below resolve
# however this file is invoked. Inserted before importing power_analysis,
# which also inserts notebooks/ itself -- relying on that would make the
# _power_common import depend on a sibling's side effect and statement order.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy.stats import chi2

from _power_common import ALPHA, SEED, results_dir
from power_analysis import (ALPHA_PRIMARY, N_HARMONICS, N_PRIMARY, cmh_p,
                            cmh_stat, mcnemar_exact_p)

# Local names for two imported constants, kept as aliases rather than renamed
# at every call site -- the values still have exactly one owner: power_analysis.
K_HARM = N_HARMONICS         # harmonic count -> CMH strata (k = 1..9)
ALPHA_BONF = ALPHA_PRIMARY   # per-test alpha over the pairwise family (2.381e-4)

R_DEFAULT = 30  # replicates; run_study.N_REPLICATES, not imported here because
                # importing run_study runs load_dotenv and freezes ec2 config
                # at import time, which an offline Monte Carlo should not pull in.

# PART 2's equivalent-R search ladder: replicate counts to re-simulate the
# unpaired test at, hunting for the smallest R matching the paired test's
# power at R_DEFAULT. Starts at R_DEFAULT (a ratio of 1 = "pairing bought
# nothing") and climbs roughly geometrically.
EQ_R_GRID = (R_DEFAULT, 35, 40, 45, 50, 60, 70, 85, 100, 120, 145, 175, 210,
             250, 300, 360, 430, 520, 620, 750, 900)

# PART 2's clustering grid. 0.0 is the published un-clustered baseline; 0.2
# and 0.4 bracket the clustering the study's own measured design effect can
# plausibly show.
ICC_GRID = (0.0, 0.2, 0.4)

# PART 4's reduced family: 28 one-df trend tests replace the 84 pairwise
# ladder contrasts; the other 126 info contrasts are common to both families.
# PART 5 prices its trend row at ALPHA / N_REDUCED so the two families are
# corrected comparably.
N_REDUCED = 154

OUT = {}
# __file__-anchored so the checkpoint lands in the study's own results/ tree
# regardless of invocation directory; already covered by the general
# notebooks/*/results/ gitignore rule.
OUT_PATH = results_dir(__file__, up=1) / "multiplicity_sim_results.json"


def dump(tag: str) -> None:
    """Write the accumulated `OUT` results to the checkpoint JSON, logging `tag`.

    The mkdir happens here, not at import, so merely importing this module
    writes nothing -- ``results/`` is gitignored and absent from a fresh
    checkout, and creating it only when a checkpoint is taken avoids a
    `FileNotFoundError` after an expensive Monte Carlo has already run.

    Parameters
    ----------
    tag : str
        Checkpoint label written to the log.
    """
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(OUT, fh, indent=2, default=float)
    print(f"[checkpoint written after {tag}]", flush=True)


# ------------------------------------------------------------------------- statistics
def gcmh_stat(succ: np.ndarray, n: int) -> np.ndarray:
    """Generalized CMH "general association" statistic across 3 rungs (chi2, df=2).

    Parameters
    ----------
    succ : np.ndarray
        Success counts across rungs and strata.
    n : int
        Must be identical across every rung and stratum -- the equal-n.
        precondition behind the covariance collapse used in
        ``power_analysis.gcmh_reject``.

    Returns
    -------
    np.ndarray
        Generalized CMH statistics.
    """
    n_rungs = succ.shape[-2]
    total_n = float(n_rungs * n)
    total_succ = succ.sum(axis=-2)                       # (..., K)
    resid = succ - (total_succ / n_rungs)[..., None, :]
    t_vec = resid[..., :2, :].sum(axis=-1)               # (..., 2)
    p = n / total_n
    common = total_succ * (total_n - total_succ) / (total_n - 1.0)
    shape = np.full((2, 2), -p * p)
    np.fill_diagonal(shape, p * (1.0 - p))
    w = common.sum(axis=-1)
    sigma = w[..., None, None] * shape
    sigma_inv = np.linalg.pinv(sigma)
    return np.einsum("...d,...de,...e->...", t_vec, sigma_inv, t_vec)


def trend_stat(
    succ: np.ndarray, n: int, scores: tuple[float, ...] = (1.0, 2.0, 3.0)
) -> np.ndarray:
    """1-df CMH correlation (linear trend) statistic across the 3 rungs, `n` trials per cell."""
    x = np.asarray(scores)
    n_rungs = succ.shape[-2]
    total_n = float(n_rungs * n)
    m = succ.sum(axis=-2)                                 # (..., K) successes
    t = (succ * x[:, None]).sum(axis=(-2, -1))            # observed
    sum_nx = n * x.sum()
    sum_nx2 = n * (x ** 2).sum()
    e_j = sum_nx * m / total_n
    v_j = (m * (total_n - m) / (total_n ** 2 * (total_n - 1.0))) * (
        total_n * sum_nx2 - sum_nx ** 2
    )
    e = e_j.sum(axis=-1)
    v = v_j.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(v > 0, (t - e) ** 2 / v, 0.0)


def paired_marks(p_a: float, p_b: float, rho: float, n_sims: int, reps: int,
                 rng: np.random.Generator, icc: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Simulate matched marks from a latent bivariate normal (tetrachoric `rho`).
    `z1`/`z2` are drawn in the same order used before `icc` existed, and the
    icc-clustering draw is skipped entirely (not drawn then zero-weighted)
    when `icc == 0.0` -- a zero-weighted draw would still advance `rng` and
    perturb every downstream draw. This makes an `icc=0.0` call reproduce
    every already-published PART 2 figure byte-for-byte. The per-replicate
    latents `u_a`, `u_b` are drawn independently per arm, never shared
    between arms, because sharing one would couple the arms and inflate the
    paired test's apparent power advantage -- the opposite of what `icc`
    exists to expose. The mix is unit-variance, so it reproduces the same
    marginal rate (`p_a`, `p_b`) as `icc=0`.

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
        Share of each arm's latent variance from a per-replicate latent.
        shared by that replicate's `K_HARM` items, modelling a replicate's shared
        seed (PART 3's "independent" variant). Must be in ``[0.0, 1.0)`` -- 1.0
        would make every item in a replicate identical, collapsing the `K_HARM`
        axis.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Simulated Boolean marks for arms A and B.
    """
    if not (0.0 <= icc < 1.0):
        raise ValueError(f"icc must be in [0.0, 1.0), got {icc!r}")
    z1 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    z2 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    zb = rho * z1 + np.sqrt(max(1.0 - rho * rho, 0.0)) * z2
    if icc > 0.0:
        u_a = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        u_b = rng.standard_normal((n_sims, reps, 1), dtype=np.float32)
        w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
        z1 = w1 * u_a + w2 * z1
        zb = w1 * u_b + w2 * zb
    from scipy.stats import norm
    return z1 < norm.ppf(p_a), zb < norm.ppf(p_b)


# =============================================================== PART 1: ceiling headroom
def part1(rng: np.random.Generator, n_sims: int = 20000, step: float = 0.0025) -> None:
    """Find the minimum detectable difference (80% power) at each ceiling.

    Per baseline rate `p_a`, scans the accuracy gap `d` in `step` increments
    for the smallest `d` reaching 80% power under both ALPHA_BONF and the naive
    alpha=0.05. Writes ``OUT["part1"]``.

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
        row = dict(p_a=p_a,
                   mdd_bonf=found.get("bonf", (None, None))[0],
                   pow_bonf=found.get("bonf", (None, None))[1],
                   mdd_naive=found.get("naive", (None, None))[0],
                   pow_naive=found.get("naive", (None, None))[1])
        row["ratio"] = (row["mdd_bonf"] / row["mdd_naive"]
                        if row["mdd_bonf"] and row["mdd_naive"] else None)
        rows.append(row)
        print(f"  p_A={p_a:.2f}  MDD(alpha=2.38e-4)={row['mdd_bonf']}  "
              f"MDD(alpha=0.05)={row['mdd_naive']}  ratio={row['ratio']}", flush=True)
    OUT["part1"] = dict(n_sims=n_sims, grid_step=step, rows=rows)


# ======================================================= PART 3: clustering / Type I error
def part3(rng: np.random.Generator, n_sims: int = 200000, chunk: int = 20000) -> None:
    """Measure actual Type I error under within-replicate clustering.

    Simulates marks with a shared per-replicate latent factor (intraclass
    correlation `icc`) over a grid of baseline rates, iccs and an "independent"
    vs "shared" latent-draw variant, reporting the realized binary (phi)
    within-replicate correlation and the actual Type I error at alpha=0.05 and
    at ALPHA_BONF. Writes ``OUT["part3"]``.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    n_sims : int, optional
        Total simulations per grid configuration.
    chunk : int, optional
        Bounds peak memory.
    """
    print("\n=== PART 3: within-replicate clustering -> actual Type I error ===", flush=True)
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
                    u_b = (u_a if variant == "shared"
                           else rng.standard_normal((s, R_DEFAULT, 1), dtype=np.float32))
                    ea = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
                    eb = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
                    w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
                    ma = (w1 * u_a + w2 * ea) < thr
                    mb = (w1 * u_b + w2 * eb) < thr
                    if len(phis) < 3:            # empirical binary within-replicate corr
                        x = ma.astype(np.float64)
                        mu = x.mean()
                        cx = x - mu
                        # mean over k<k' of E[cx_k cx_k'] / var
                        ssum = cx.sum(axis=2)
                        cross = (ssum ** 2 - (cx ** 2).sum(axis=2)).mean() / (
                            K_HARM * (K_HARM - 1))
                        phis.append(cross / (mu * (1 - mu)))
                    sa = ma.sum(axis=1)
                    sb = mb.sum(axis=1)
                    st = cmh_stat(sa, sb, R_DEFAULT)
                    r05 += int((st > crit05).sum())
                    rb += int((st > critb).sum())
                    done += s
                row = dict(p=p, icc=icc, variant=variant,
                           phi_binary=float(np.mean(phis)),
                           t1_alpha05=r05 / n_sims, t1_alpha_bonf=rb / n_sims,
                           infl05=(r05 / n_sims) / ALPHA,
                           inflb=(rb / n_sims) / ALPHA_BONF, n_sims=n_sims)
                rows.append(row)
                print(f"  p={p} icc={icc} {variant:11s} phi_bin={row['phi_binary']:.3f} "
                      f"T1@0.05={row['t1_alpha05']:.4f} ({row['infl05']:.2f}x)  "
                      f"T1@2.38e-4={row['t1_alpha_bonf']:.6f} ({row['inflb']:.2f}x)",
                      flush=True)
    OUT["part3"] = dict(rows=rows)


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
    # The same 28 trend tests as PART 4's reduced family, corrected over that
    # whole family so trend and pairwise are corrected comparably.
    alpha_trend_studywide = ALPHA / N_REDUCED
    # Sensitivity only: correcting the 28 trend tests among themselves.
    alpha_trend_only = ALPHA / 28
    alpha_pair = ALPHA_BONF               # pairwise inside the 210 family
    rows = []
    for label, rates in (("monotone 0.60/0.75/0.88", (0.60, 0.75, 0.88)),
                         ("non-monotone 0.60/0.88/0.75", (0.60, 0.88, 0.75)),
                         ("monotone-small 0.60/0.66/0.72", (0.60, 0.66, 0.72)),
                         ("non-monotone-small 0.60/0.72/0.66", (0.60, 0.72, 0.66)),
                         ("monotone-ceiling 0.99/0.96/0.93", (0.99, 0.96, 0.93)),
                         ("non-monotone-ceiling 0.99/0.93/0.96", (0.99, 0.93, 0.96))):
        succ = np.stack([rng.binomial(R_DEFAULT, r, (n_sims, K_HARM)) for r in rates],
                        axis=1)
        tr = trend_stat(succ, R_DEFAULT)
        gc = gcmh_stat(succ, R_DEFAULT)
        pair_stats = [cmh_stat(succ[:, i, :], succ[:, j, :], R_DEFAULT)
                      for i, j in ((0, 1), (1, 2), (0, 2))]
        res = dict(label=label, rates=rates)
        # study-wide alphas
        res["trend_studywide"] = float((tr > chi2.isf(alpha_trend_studywide, 1)).mean())
        # Same statistic at the narrower, not pre-registered, trend-only
        # alpha, reported beside the headline rather than instead of it.
        res["trend_trend_only_family"] = float(
            (tr > chi2.isf(alpha_trend_only, 1)).mean())
        res["gcmh_studywide"] = float((gc > chi2.isf(ALPHA / 7, 2)).mean())
        res["pairwise_any_studywide"] = float(
            np.any([s > chi2.isf(alpha_pair, 1) for s in pair_stats], axis=0).mean())
        # local, uncorrected-family alphas (test choice isolated from correction)
        res["trend_local05"] = float((tr > chi2.isf(ALPHA, 1)).mean())
        res["gcmh_local05"] = float((gc > chi2.isf(ALPHA, 2)).mean())
        res["pairwise_any_local"] = float(
            np.any([s > chi2.isf(ALPHA / 3, 1) for s in pair_stats], axis=0).mean())
        rows.append(res)
        print(f"  {label}", flush=True)
        print(f"    study-wide: trend[a=.05/{N_REDUCED}]="
              f"{res['trend_studywide']:.4f} "
              f"gcmh(2df)[a=.05/7]={res['gcmh_studywide']:.4f} "
              f"any-pairwise[a=.05/{N_PRIMARY}]="
              f"{res['pairwise_any_studywide']:.4f}", flush=True)
        print(f"    sensitivity: trend[a=.05/28, trend-only family, "
              f"not pre-registered]={res['trend_trend_only_family']:.4f}",
              flush=True)
        print(f"    local a=.05: trend={res['trend_local05']:.4f} "
              f"gcmh={res['gcmh_local05']:.4f} any-pairwise={res['pairwise_any_local']:.4f}",
              flush=True)
    OUT["part5"] = dict(rows=rows, n_sims=n_sims,
                        alpha_trend_studywide=alpha_trend_studywide,
                        alpha_trend_only=alpha_trend_only,
                        alpha_pairwise=ALPHA_BONF, alpha_gcmh=ALPHA / 7)


# ================================================================== PART 2: pairing gain
def _paired_powers(
    p_a: float, delta: float, rho: float, reps: int, n_sims: int,
    rng: np.random.Generator, stats: bool = True, icc: float = 0.0,
) -> tuple[float, float, float | None, float | None]:
    """Unpaired-CMH and paired-McNemar power on the SAME simulated marks (arm B = p_a - delta).

    `stats=False` skips the two mark-level diagnostics (`phi_binary`,
    `agreement`) -- they consume no randomness, so the two powers are
    identical either way; skip them for cost. Computing `phi` upcasts both
    boolean mark arrays to float64, ~1.55 GB at the top of `EQ_R_GRID`, for
    numbers `part2`'s equivalent-R search then discards.

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
        ``(power_unpaired, power_paired, phi_binary, agreement)``; the last.
        two are `None` when ``stats=False``.
    """
    p_b = p_a - delta
    ma, mb = paired_marks(p_a, p_b, rho, n_sims, reps, rng, icc=icc)
    sa = ma.sum(axis=1)
    sb = mb.sum(axis=1)
    unp = (cmh_stat(sa, sb, reps) > chi2.isf(ALPHA_BONF, 1)).mean()
    b = (ma & ~mb).sum(axis=(1, 2))
    c = (~ma & mb).sum(axis=(1, 2))
    pv = mcnemar_exact_p(b, c)
    powers = float(unp), float((pv < ALPHA_BONF).mean())
    if not stats:
        # Explicit Nones, not zeros: "not measured" must not be mistakable
        # for "measured as uncorrelated".
        return powers[0], powers[1], None, None
    # realized binary (phi) correlation between the two arms' marks, and agreement
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    agree = float((ma == mb).mean())
    return powers[0], powers[1], float(phi), agree


def study_design_effect() -> float | None:
    """Read the induction study's OWN measured design effect from the real tree.

    Median, over the 210 PRIMARY contrasts, of `paired_analysis.design_effect`
    on each contrast's item-matched marks -- the same estimator `part2`'s icc
    blocks report on their own simulated marks, for direct comparison.
    Returns `None` if no results tree exists (a fresh checkout) or every
    contrast's design_effect came back `None`; any other read failure
    propagates rather than being swallowed, so a malformed replicate cannot
    silently produce a design effect computed from a partial read.
    """
    # Imported here, not at module scope: this module's simulation consumes
    # constants only, never results, and a bare `import multiplicity_sim`
    # must not depend on a results-reading sibling's import-time side effects.
    import paired_analysis
    import power_analysis

    if not paired_analysis.RESULTS_DIR.exists():
        return None
    correct, valid, _compliance = paired_analysis.load_marks()
    deffs = []
    for _label, key_a, key_b in power_analysis.build_primary_contrasts():
        a, b, seed_idx = paired_analysis.aligned(correct, valid, key_a, key_b,
                                                  drop_invalid=False)
        d = paired_analysis.design_effect(a, b, seed_idx)
        if d is not None:
            deffs.append(d)
    return float(np.median(deffs)) if deffs else None


def part2(
    rng: np.random.Generator, n_sims: int = 20000, search_sims: int = 8000,
    cap: int = EQ_R_GRID[-1],
) -> None:
    """Measure the power gain from pairing (matched items) over unpaired testing.

    Over a grid of baseline rates, accuracy gaps and latent correlations,
    compares unpaired CMH against paired exact McNemar on the same matched
    marks. Where pairing helps, searches `EQ_R_GRID` for the smallest
    unpaired replicate count matching the paired test's power at
    `R_DEFAULT`; `cap` defaults to the grid's own last rung so the two
    ceilings cannot silently disagree. Also reports null-calibration Type I
    error for both tests.

    Run once per `icc` in `ICC_GRID`, simulating the within-replicate
    clustering the study's items have. Each icc block also reports
    `design_effect_simulated`, the median `design_effect` its own
    null-configuration marks produce, comparable against
    `study_design_effect` (printed once up front). Writes ``OUT["part2"]``.

    Parameters
    ----------
    rng : np.random.Generator
        Random-number generator for simulated marks.
    n_sims : int, optional
        Number of simulations for the main power calculations.
    search_sims : int, optional
        Number of simulations at each equivalent-R search rung.
    cap : int, optional
        Upper replicate-count bound recorded with each result.
    """
    # Imported here, not at module scope, for the same reason as
    # study_design_effect: the simulation must not gain a results-reading
    # import-time dependency.
    import paired_analysis

    measured = study_design_effect()
    measured_str = (f"{measured:.3f}" if measured is not None
                    else f"unknown (no results tree at {paired_analysis.RESULTS_DIR})")
    print("\n=== PART 2: pairing gain (matched items) ===", flush=True)
    print(f"  study's own measured design effect: {measured_str} -- compare "
          f"against each icc block's design_effect_simulated below", flush=True)
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
                        p_a, delta, rho, R_DEFAULT, n_sims, rng, icc=icc)
                    # smallest R at which the unpaired test matches the paired
                    # power at R_DEFAULT (paired data throughout).
                    eq_r = None
                    if pair > unp + 0.005:
                        for rr in grid_r:
                            # stats=False: only the unpaired power is read
                            # here, so the diagnostics would otherwise be
                            # computed and discarded once per rung.
                            u2 = _paired_powers(p_a, delta, rho, rr, search_sims,
                                                rng, stats=False, icc=icc)[0]
                            if u2 >= pair:
                                eq_r = rr
                                break
                    else:
                        # Pairing did not help: record R_DEFAULT with the
                        # eq_searched flag below, rather than overload eq_R's
                        # meaning between "matched by search" and "unsearched".
                        eq_r = R_DEFAULT
                    rows.append(dict(p_a=p_a, delta=delta, rho=rho,
                                     power_unpaired=unp, power_paired=pair,
                                     eq_R=eq_r, eq_searched=pair > unp + 0.005,
                                     cap=cap, phi_binary=phi, agreement=agree,
                                     eq_ratio=(None if eq_r is None
                                               else eq_r / R_DEFAULT),
                                     icc=icc))
                    print(f"  icc={icc} p_A={p_a} d={delta} rho={rho}: "
                          f"phi_bin={phi:.3f} agree={agree:.3f} "
                          f"unpaired={unp:.4f} paired={pair:.4f} eqR={eq_r}",
                          flush=True)
        # null calibration of both tests under matched data
        nulls = {}
        for rho in (0.0, 0.5, 0.9):
            # stats=False as above; `[:2]` already shows the diagnostics are
            # unread, and this call uses the largest n_sims here.
            u, p = _paired_powers(0.90, 0.0, rho, R_DEFAULT, 60000, rng,
                                  stats=False, icc=icc)[:2]
            nulls[rho] = dict(unpaired_t1=u, mcnemar_t1=p)
            print(f"  icc={icc} NULL rho={rho}: unpaired T1={u:.6f} "
                  f"mcnemar T1={p:.6f}", flush=True)

        # This block's own design_effect: same null config as the
        # calibration row above (p_a=p_b=0.90, rho=0.5), median over the
        # measurable simulated blocks -- the same quantity study_design_effect
        # reports over real contrasts.
        ma, mb = paired_marks(0.90, 0.90, 0.5, n_sims, R_DEFAULT, rng, icc=icc)
        seed_idx = np.repeat(np.arange(R_DEFAULT), K_HARM)
        deffs = [paired_analysis.design_effect(ma[i].ravel(), mb[i].ravel(), seed_idx)
                 for i in range(n_sims)]
        measurable = [d for d in deffs if d is not None]
        if measurable:
            deff_sim = float(np.median(measurable))
            print(f"  icc={icc} design_effect_simulated: {deff_sim:.3f} "
                  f"(median of {len(measurable)}/{n_sims} measurable)", flush=True)
        else:
            # No placeholder number: a genuinely unmeasurable block says so.
            deff_sim = None
            print(f"  icc={icc} design_effect_simulated: no measurable ratio "
                  f"in {n_sims} simulations", flush=True)

        icc_blocks[str(icc)] = dict(rows=rows, nulls=nulls,
                                    design_effect_simulated=deff_sim)

    # icc keys are strings: JSON has no float keys, so the in-memory shape
    # already matches the on-disk shape.
    OUT["part2"] = dict(n_sims=n_sims, alpha=ALPHA_BONF, grid_r=grid_r,
                        icc=icc_blocks)


# ============================================================== PART 4: correction cost
def build_rate_matrix() -> np.ndarray:
    """Build a stylized 7-family x 3-rung x 4-info true-rate matrix for PART 4.

    30 true effects near ceiling and mid-range per the brief; the remaining
    180 contrasts are exact nulls.
    """
    rates = np.zeros((7, 3, 4))
    flat = [0.99, 0.97, 0.95, 0.92, 0.85, 0.75, 0.62]
    for f in range(7):
        rates[f, :, :] = flat[f]
    # F0: near-ceiling WHOLE-MODEL ladder (all 4 arms shift together)
    #     -> 4 infos x 3 rung-pairs = 12 true ladder contrasts, 0 true info contrasts
    for i in range(4):
        rates[0, :, i] = [0.99, 0.96, 0.925]
    # F1: upper-mid ladder on extens only -> 3 ladder + 6 info = 9 true
    rates[1, :, 1] = [0.97, 0.91, 0.83]
    # F2: mid-range ladder on extens only -> 3 ladder + 6 info = 9 true
    rates[2, :, 1] = [0.95, 0.86, 0.74]
    # total = 12 + 9 + 9 = 30 true effects, 180 exact nulls (per the brief)
    return rates


def _stepup(
    sortedp: np.ndarray, order: np.ndarray, thresholds: np.ndarray
) -> np.ndarray:
    """Apply a step-up multiple-testing procedure and scatter it back to input order.

    Shared mechanics for Hochberg and BH, which differ only in `thresholds`'
    formula: walk the sorted p-values from the largest rank down, reject at
    the first (largest) rank at or below its own threshold, and reject every
    rank below that one too. (Holm is step-down and keeps its own loop --
    see `apply_corrections`.)

    ``ok[:, ::-1].argmax(axis=1)`` finds the last True per row by reversing
    and taking the first True from the end. Rows with no True get sentinel
    index -1, so nothing is rejected for that row without a separate branch.

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
    """Apply Bonferroni, Holm, Hochberg, and BH(q=0.05) to a batch of p-value families.

    `m` is read from `pv.shape[1]` rather than taken as a parameter,
    so a caller cannot pass a mismatched `m` and get every threshold
    silently computed from the wrong family size.

    Holm (step-down) keeps its own loop: it walks from the smallest p-value
    and stops at the first violation, the opposite traversal and stopping
    rule from Hochberg and BH (step-up), which share `_stepup`.

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
    # Bonferroni
    out["Bonferroni"] = pv < ALPHA / m
    # Holm (step-down): first VIOLATION of alpha/(m-i+1) stops the walk; every
    # rank strictly before it is rejected.
    thr = ALPHA / (m - ranks + 1)
    viol = sortedp > thr
    first = np.where(viol.any(axis=1), viol.argmax(axis=1), m)
    keep = np.arange(m)[None, :] < first[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Holm"] = rej
    # Hochberg (step-up, alpha/(m-i+1) -- the SAME per-rank thresholds as
    # Holm's, but the last-passing-rank stopping rule `_stepup` implements).
    out["Hochberg"] = _stepup(sortedp, order, thr)
    # BH (step-up, alpha*i/m)
    bh_thr = ALPHA * ranks / m
    out["BH(q=0.05)"] = _stepup(sortedp, order, bh_thr)
    return out


def part4(rng: np.random.Generator, n_sims: int = 4000) -> None:
    """Measure the cost of multiplicity correction against `build_rate_matrix`'s truth.

    Compares the full 210-contrast PRIMARY family (84 ladder + 126 info)
    with a reduced 154-test family (28 one-df trend tests replacing the 84
    pairwise ladder contrasts) under Bonferroni, Holm, Hochberg and BH,
    reporting true/false rejection counts, FWER, FDR and non-flat ladders
    flagged. A third "test-swap only" arm holds the family size at 210 while
    swapping in the trend test, isolating test choice from correction.
    Writes ``OUT["part4"]``.

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
    # A raise, not an assert: python -O strips asserts, and this gate ties the
    # simulated family to the study's real PRIMARY family size, the
    # denominator every alpha here divides by.
    if m_full != N_PRIMARY:
        raise RuntimeError(
            f"PART 4 built {m_full} full-family contrasts but power_analysis "
            f"declares N_PRIMARY = {N_PRIMARY}; the simulated family no longer "
            "matches the study's, so its Bonferroni alpha is wrong."
        )
    # truth
    true_diff = np.array([abs(rates[c[0], c[1], c[2]] - rates[c[3], c[4], c[5]])
                          for c in contrasts])
    is_null = true_diff == 0.0
    n_true = int((~is_null).sum())
    # trend-family truth: ladder non-flat (all 28 ladders)
    ladder_rates = np.array([[rates[f, r, i] for r in range(3)]
                             for f in range(7) for i in range(4)])
    ladder_nonflat = ~np.all(ladder_rates == ladder_rates[:, :1], axis=1)
    print(f"  config: {n_true} true effects / {int(is_null.sum())} true nulls; "
          f"non-flat ladders = {int(ladder_nonflat.sum())}/28", flush=True)
    print(f"  true-effect deltas: {np.sort(true_diff[~is_null])}", flush=True)

    # simulate
    succ = np.empty((n_sims, 7, 3, 4, K_HARM), dtype=np.int32)
    for f in range(7):
        for r in range(3):
            for i in range(4):
                succ[:, f, r, i, :] = rng.binomial(R_DEFAULT, rates[f, r, i],
                                                   (n_sims, K_HARM))
    pv = np.empty((n_sims, m_full))
    for t, c in enumerate(contrasts):
        pv[:, t] = cmh_p(succ[:, c[0], c[1], c[2], :], succ[:, c[3], c[4], c[5], :],
                         R_DEFAULT)
    # reduced family: 28 trend tests + 126 info contrasts
    trend_p = np.empty((n_sims, 28))
    t = 0
    for f in range(7):
        for i in range(4):
            trend_p[:, t] = chi2.sf(trend_stat(succ[:, f, :, i, :], R_DEFAULT), df=1)
            t += 1
    pv_red = np.concatenate([trend_p, pv[:, 84:]], axis=1)
    null_red = np.concatenate([~ladder_nonflat, is_null[84:]])
    m_red = pv_red.shape[1]
    # Same reasoning as the m_full gate above; N_REDUCED is what PART 5 prices
    # its study-wide trend row against.
    if m_red != N_REDUCED:
        raise RuntimeError(
            f"PART 4 built {m_red} reduced-family tests but N_REDUCED is "
            f"{N_REDUCED}; PART 5's alpha_trend_studywide (ALPHA / N_REDUCED) "
            "would then correct the trend test in a family that does not exist."
        )

    def summarize(
        name: str, rejmap: dict[str, np.ndarray], nullmask: np.ndarray,
        ladder_flag_fn: Callable[[np.ndarray], np.ndarray],
    ) -> dict[str, dict]:
        res = {}
        for proc, rej in rejmap.items():
            v = (rej & nullmask).sum(axis=1)
            s = (rej & ~nullmask).sum(axis=1)
            tot = rej.sum(axis=1)
            res[proc] = dict(
                true_rej=float(s.mean()), false_rej=float(v.mean()),
                fwer=float((v > 0).mean()),
                fdr=float(np.where(tot > 0, v / np.maximum(tot, 1), 0.0).mean()),
                ladders_flagged=float(ladder_flag_fn(rej).mean()),
                power_per_true=float(s.mean() / max((~nullmask).sum(), 1)))
            print(f"  [{name}] {proc:12s} trueRej={res[proc]['true_rej']:.2f} "
                  f"FWER={res[proc]['fwer']:.4f} FDR={res[proc]['fdr']:.4f} "
                  f"ladders={res[proc]['ladders_flagged']:.2f}", flush=True)
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
    # Holds family size at 210 (alpha unchanged) but swaps 3 pairwise for 1
    # trend test per ladder; difference vs the m=154 arm isolates the
    # correction's contribution from the test's.
    fixed_alpha = summarize(
        "test-swap only (alpha=0.05/210)",
        {"Bonferroni@210": pv_red < ALPHA / N_PRIMARY}, null_red, flag_red)
    OUT["part4"] = dict(n_sims=n_sims, n_true=n_true, n_null=int(is_null.sum()),
                        n_true_reduced=int((~null_red).sum()),
                        nonflat_ladders=int(ladder_nonflat.sum()),
                        true_deltas=sorted(set(np.round(true_diff[~is_null], 4).tolist())),
                        full=full, reduced=red2, test_swap_fixed_alpha=fixed_alpha,
                        rates=rates.tolist())


def main() -> None:
    """Run PARTs 1, 3, 5, 2, 4 in that order (not PART-number order), checkpointing each.

    Each part gets its own generator, seeded `SEED + <part number>` (the
    part number, not run-order position, so reordering the calls below
    cannot perturb another part's draws).
    """
    t0 = time.time()
    part1(np.random.default_rng(SEED + 1)); dump("part1")
    part3(np.random.default_rng(SEED + 3)); dump("part3")
    part5(np.random.default_rng(SEED + 5)); dump("part5")
    part2(np.random.default_rng(SEED + 2)); dump("part2")
    part4(np.random.default_rng(SEED + 4)); dump("part4")
    print(f"\nTOTAL {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
