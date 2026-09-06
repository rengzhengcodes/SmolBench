"""Run a Monte Carlo study of TEST and CORRECTION choice for the induction study.

Companion to the periodic-induction family-ladder scaling study (21 models x 4
info arms, R=30 replicates x 9 harmonics). Every POWER and error-rate figure
here is simulated (the test statistics themselves use the usual chi-square
reference distributions). The pairwise test is byte-for-byte the repo's
continuity-corrected 2x2xK CMH
(notebooks/induction/analysis/power_analysis.py::cmh_reject) and the 2-df
general-association statistic mirrors that file's gcmh_reject. The design
constants the simulation is priced against are IMPORTED from the modules that
own them (`_power_common` and `power_analysis`) rather than re-declared here,
so a re-sizing of the study cannot apply to the report and not to this
simulation. The SIMULATION still consumes constants only, never results --
that claim is unchanged. `study_design_effect` is the one exception: it reads
the study's own measured design effect (`paired_analysis.design_effect`, a
variance ratio on binary per-seed differences) from the real results tree
when one exists, purely so PART 2's icc rows below can be interpreted against
it. A fresh checkout ships no results tree, so `study_design_effect` returns
``None`` there, and PART 2 prints that as `unknown` -- this repository is in
that state. Results are checkpointed to
`notebooks/induction/results/multiplicity_sim_results.json` after each part.

PART 2 (pairing gain) runs at three intraclass correlations (`ICC_GRID`:
0.0, 0.2, 0.4), modelling the within-replicate clustering the real study's
items have -- a replicate's `K_HARM` items share a seed and so rise and fall
together -- which PART 2's marks did not model before. Each icc block reports
the design effect its OWN simulated marks produce, under the exact same
`design_effect` estimator the study's paired report uses, so a reader holding
their own study's measured design effect compares LIKE WITH LIKE against a
row that actually used that estimator, rather than against a formula. The
textbook shortcut `1 + (k-1)*icc` is deliberately NOT used to relate an `icc`
to a design effect: `icc` is a knob on the LATENT scale (a share of latent
variance shared within a replicate) while `design_effect` measures a variance
RATIO on the observed binary per-seed differences the CMH denominator omits;
relating the two by that formula would compare two different scales as if
they were one.

Run (repo root):
  .venv/bin/python notebooks/induction/analysis/multiplicity_sim.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Two __file__-anchored inserts, never cwd-relative, so the sibling imports
# below resolve however this file is invoked (as __main__, by path, or from any
# working directory). This module's own directory carries `power_analysis`
# (only __main__ gets that directory for free); `notebooks/`, two levels up,
# carries `_power_common`. `power_analysis` also inserts `notebooks/` itself,
# but relying on that would make the `_power_common` import depend on a
# sibling's side effect and on statement order.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy.stats import binom, chi2

from _power_common import ALPHA, SEED, results_dir
from power_analysis import ALPHA_PRIMARY, N_HARMONICS, N_PRIMARY

# ----------------------------------------------------------------------------- design
# Local ALIASES for two imported constants. Both spellings are kept because the
# short names are used throughout this file and renaming every use would be
# churn; the point is that the VALUES now have exactly one owner.
K_HARM = N_HARMONICS            # power_analysis owns the harmonic count
                                # (k = 1..9 -> CMH strata for pairwise tests)
ALPHA_BONF = ALPHA_PRIMARY      # power_analysis owns the PRIMARY per-test alpha
                                # (ALPHA over the pairwise family; 2.381e-4)

R_DEFAULT = 30          # replicates (seeds 0..29) -- run_study.N_REPLICATES,
                        # user-locked there; see that constant's comment for
                        # why 30 (a budget ruling checked against
                        # power_analysis.py's prospective sizing).
                        # Deliberately NOT imported, unlike its neighbours
                        # above: there is no import-safe home for the replicate
                        # count. run_study.py owns it, but that module is a
                        # driver -- importing it runs load_dotenv and the ec2
                        # import-time constant freeze -- so importing it from an
                        # offline Monte Carlo would drag live deployment config
                        # into this script.

# PART 2's equivalent-R search ladder: the replicate counts at which the
# UNPAIRED test is re-simulated while hunting for the smallest R that matches
# the paired test's power at R_DEFAULT. It starts AT R_DEFAULT by construction
# (a ratio of 1 is the "pairing bought nothing" answer) and then climbs roughly
# geometrically to its final rung, so the ladder is a design constant of the
# comparison rather than an implementation detail of the loop that walks it.
EQ_R_GRID = (R_DEFAULT, 35, 40, 45, 50, 60, 70, 85, 100, 120, 145, 175, 210,
             250, 300, 360, 430, 520, 620, 750, 900)

# PART 2's clustering grid: the intraclass correlations at which the whole
# pairing-gain block is re-run. 0.0 is the published un-clustered baseline
# (every PART 2 figure already published assumes it implicitly); 0.2 and 0.4
# bracket the clustering the study's own measured design effect
# (`study_design_effect`) can plausibly show, so a reader with a measured
# design effect in hand lands between two rows rather than off the end of the
# grid.
ICC_GRID = (0.0, 0.2, 0.4)

# PART 4's reduced contrast family: 28 one-df trend tests replacing the 84
# pairwise ladder contrasts, plus the 126 info contrasts that are common to
# both families. PART 4 re-derives and checks this count against the family it
# actually builds; PART 5 prices its trend row at ALPHA / N_REDUCED so trend and
# pairwise are corrected in comparable families.
N_REDUCED = 154

OUT = {}
# Anchored on __file__, not the cwd, so the output lands in the study's own
# results/ tree whatever directory this script is invoked from (repo
# convention -- see notebooks/_power_common.py's results_dir). That tree is
# where the rest of the study's results live and is already covered by the
# general `notebooks/*/results/` gitignore rule, so the checkpoint needs no
# one-off ignore entry of its own.
OUT_PATH = results_dir(__file__, up=1) / "multiplicity_sim_results.json"


def dump(tag: str) -> None:
    """Write the accumulated `OUT` results to the checkpoint JSON, logging `tag`.

    Creates ``OUT_PATH``'s parent directory if it is missing.

    Parameters
    ----------
    tag : str
        Name of the part just finished, echoed in the progress line.

    Notes
    -----
    Writes to disk. The mkdir lives HERE rather than at module import so that
    merely importing this module (as the sibling tests and any REPL session do)
    writes nothing: the directory appears only when a checkpoint is actually
    taken. It is required because ``results/`` is gitignored and S3-mirrored, so
    it is absent from a fresh checkout -- without the mkdir every checkpoint
    would raise `FileNotFoundError` AFTER its Monte Carlo had already run, the
    most expensive possible place to fail.
    """
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(OUT, fh, indent=2, default=float)
    print(f"[checkpoint written after {tag}]", flush=True)


# ------------------------------------------------------------------------- statistics
def cmh_stat(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    """Compute the repo's continuity-corrected 2x2xK CMH statistic (chi2, df=1).

    Parameters
    ----------
    succ_a, succ_b : ndarray, shape (..., K)
        Success counts out of `n` trials per stratum, `n` the same for both.

    Returns
    -------
    ndarray, shape (...)
        One statistic per leading batch index.
    """
    big_n = 2 * n
    m1 = succ_a + succ_b
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.abs((succ_a - expect).sum(axis=-1)) - 0.5
    num = np.clip(num, 0.0, None) ** 2
    denom = var.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denom > 0, num / denom, 0.0)


def cmh_p(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    """Compute the two-sided chi2 (df=1) p-value for `cmh_stat`."""
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def gcmh_stat(succ: np.ndarray, n: int) -> np.ndarray:
    """Compute the generalized CMH "general association" statistic, 3 rungs (chi2, df=2).

    Parameters
    ----------
    succ : ndarray, shape (..., 3, K)
        Success counts per (rung, stratum).
    n : int
        Trials per rung per stratum, identical for every rung and stratum --
        the equal-n precondition behind the covariance collapse documented on
        ``power_analysis.gcmh_reject``.

    Returns
    -------
    ndarray, shape (...)
        One statistic per leading batch index.
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


def trend_stat(succ: np.ndarray, n: int, scores=(1.0, 2.0, 3.0)) -> np.ndarray:
    """Compute the 1-df CMH correlation (linear trend) statistic.

    Parameters
    ----------
    succ : ndarray, shape (..., 3, K)
        Success counts per (rung, stratum), `n` trials per cell.
    scores : sequence of float
        Ladder scores assigned to the 3 rungs, in rung order.

    Returns
    -------
    ndarray, shape (...)
        One statistic per leading batch index.
    """
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


def mcnemar_exact_p(b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Compute the two-sided exact conditional (binomial) McNemar p-value, BATCHED.

    ``paired_analysis.mcnemar_exact_p`` holds the SCALAR reference
    implementation of this test; this is the batched form of the IDENTICAL
    test, on the same conditional-binomial definition
    ``min(1, 2 * P[Bin(b + c, 1/2) <= min(b, c)])`` and through the same
    ``scipy.stats.binom``. It exists separately only because this module
    evaluates it over whole simulation batches (shape ``(n_sims,)`` and larger)
    where a Python-level loop over the reference would dominate the runtime.

    Parameters
    ----------
    b, c : ndarray
        Counts of A-succeeds/B-fails pairs and the reverse, broadcast together.

    Returns
    -------
    ndarray
        The p-value; 1.0 where ``b + c == 0`` (no discordant pairs), the same
        convention the scalar reference uses.
    """
    nd = b + c
    lo = np.minimum(b, c)
    # `np.maximum(nd, 1)` is NOT a silent fallback answer. Unlike the scalar
    # reference, which returns early, numpy evaluates `binom.cdf` across the
    # WHOLE array before `np.where` selects per entry, so the no-discordance
    # entries are computed and then thrown away. Flooring their trial count at
    # 1 makes that dead branch a well-defined Bin(1, 1/2) rather than leaning
    # on scipy's convention for a zero-trial binomial; the nd == 0 answer comes
    # from `np.where` below, never from this line.
    p = 2.0 * binom.cdf(lo, np.maximum(nd, 1), 0.5)
    # The vectorized spelling of the reference's `min(1.0, ...)`: doubling a
    # one-sided tail exceeds 1 whenever b == c. The 0.0 lower bound is inert (a
    # CDF is never negative) and is kept only so the bound reads as a range.
    p = np.clip(p, 0.0, 1.0)
    return np.where(nd == 0, 1.0, p)


def paired_marks(p_a: float, p_b: float, rho: float, n_sims: int, reps: int,
                 rng: np.random.Generator, icc: float = 0.0):
    """Simulate matched marks from a latent bivariate normal (tetrachoric `rho`).

    Optionally clusters each arm's items within a replicate at intraclass
    correlation `icc`, modelling the fact that a replicate's `K_HARM` items
    share a seed and so rise and fall together -- the same latent model PART 3
    calls its "independent" variant (an arm-specific per-replicate latent, not
    a single latent shared by both arms).

    Parameters
    ----------
    p_a, p_b : float
        Marginal success rate of arm A and arm B.
    rho : float
        Tetrachoric (latent-scale) correlation between the two arms' marks.
    n_sims : int
        Number of independent Monte Carlo simulations to draw at once.
    reps : int
        Number of replicates (seeds) per simulation.
    rng : numpy.random.Generator
        Source of randomness, consumed in a fixed order (see Notes).
    icc : float, default 0.0
        Intraclass correlation: the share of each arm's latent variance
        contributed by a per-replicate latent shared by that replicate's
        `K_HARM` items, rather than drawn fresh per item. Must lie in
        ``[0.0, 1.0)``; ``1.0`` is excluded because it would make every item
        within a replicate identical, collapsing the `K_HARM` axis.

    Returns
    -------
    tuple of ndarray
        ``(marks_a, marks_b)``, bool arrays of shape ``(n_sims, reps, K_HARM)``
        with marginal success rates `p_a` and `p_b` regardless of `icc` (see
        Notes: the mix is variance-preserving).

    Raises
    ------
    ValueError
        If `icc` is outside ``[0.0, 1.0)``.

    Notes
    -----
    `z1`, `z2` and their mix `zb` are drawn in exactly the order this function
    used before `icc` existed. This is load-bearing: it is what makes an
    `icc=0.0` call consume `rng` identically to the pre-`icc` code, so every
    PART 2 figure already published (all produced at the implicit icc=0) is
    reproduced byte-for-byte by an explicit `icc=0.0` call. The
    icc-clustering draw below is skipped ENTIRELY when `icc == 0.0` -- not
    performed and then multiplied by a zero weight -- for exactly that
    reason: a zero-weighted draw still advances `rng`'s state, which would
    silently change every draw downstream of this call even though the
    weight makes its OWN contribution zero.

    When `icc > 0.0`, one per-replicate latent is drawn per ARM (`u_a`, `u_b`),
    INDEPENDENTLY of each other, each shape ``(n_sims, reps, 1)`` broadcasting
    over the `K_HARM` items of a replicate. The two latents are never shared
    between arms: a single latent shared by both arms would couple them
    through the back door, inflating the paired test's apparent correlation
    and hence its apparent power advantage over the unpaired test -- the
    opposite of the effect `icc` exists to expose.

    Each arm's mixed latent is ``w1 * u + w2 * z`` with
    ``w1, w2 = sqrt(icc), sqrt(1 - icc)``. Because ``w1**2 + w2**2 == icc +
    (1 - icc) == 1`` and `u` and `z` are independent unit-variance normals,
    the mix is itself unit-variance, so thresholding it at ``norm.ppf(p_a)``
    (resp. `p_b`) reproduces the SAME marginal success rate as icc=0 -- an
    icc row is the same task with clustering added, not a different task with
    a different rate.
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
def part1(rng: np.random.Generator, n_sims: int = 20000, step: float = 0.0025):
    """Find the minimum detectable difference (80% power) at each ceiling.

    Per baseline rate `p_a`, scans the accuracy gap `d` in `step` increments
    for the smallest `d` reaching 80% power under both ALPHA_BONF and the naive
    alpha=0.05. Writes ``OUT["part1"]``.
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
def part3(rng: np.random.Generator, n_sims: int = 200000, chunk: int = 20000):
    """Measure actual Type I error under within-replicate clustering.

    Simulates marks with a shared per-replicate latent factor (intraclass
    correlation `icc`) over a grid of baseline rates, iccs and an "independent"
    vs "shared" latent-draw variant, reporting the realized binary (phi)
    within-replicate correlation and the actual Type I error at alpha=0.05 and
    at ALPHA_BONF. `chunk` bounds peak memory. Writes ``OUT["part3"]``.
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
def part5(rng: np.random.Generator, n_sims: int = 20000):
    """Compare the 1-df trend test against the 2-df omnibus and 3 pairwise tests.

    Six rate scenarios (monotone and non-monotone, at small, mid and ceiling
    effect sizes), one simulated 3-rung ladder each, reporting every test's
    rejection rate under the study-wide alphas and again under local
    uncorrected-family alphas, which isolates test choice from correction.
    Writes ``OUT["part5"]``.

    Notes
    -----
    The trend test is priced TWICE, and the distinction is the point of this
    part. The headline `trend_studywide` uses ``ALPHA / N_REDUCED``, the family
    PART 4 actually puts these 28 trend tests in, so it is comparable with the
    pairwise row's ``ALPHA / N_PRIMARY``. The `trend_trend_only_family` row
    keeps the narrower ``ALPHA / 28`` -- correcting only within the trend tests
    themselves -- as a labelled SENSITIVITY figure. That narrower family is
    not pre-registered anywhere (nothing outside this file registers any trend
    test at all), and at 7.5x the headline alpha it would hand the trend test a
    threshold no pairwise contrast is judged at, which is precisely the
    comparison this part exists to make honestly.
    """
    print("\n=== PART 5: 1-df trend vs 2-df omnibus vs 3 pairwise ===", flush=True)
    # Study-wide: the same 28 trend tests as PART 4's reduced family, corrected
    # over that whole family, so trend and pairwise are corrected comparably.
    alpha_trend_studywide = ALPHA / N_REDUCED
    # Sensitivity only: correcting the 28 one-df trend tests among themselves.
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
        # ... and the same trend statistic at the narrower, not pre-registered,
        # trend-only family alpha, reported beside it rather than instead of it.
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
def _paired_powers(p_a, delta, rho, reps, n_sims, rng, stats: bool = True,
                   icc: float = 0.0):
    """Compute unpaired-CMH and paired-McNemar power on the SAME simulated marks.

    Arm B's rate is ``p_a - delta``; `rho` is the latent (tetrachoric)
    correlation between the arms' marks.

    Parameters
    ----------
    stats : bool, default True
        Also compute the two mark-level DIAGNOSTICS (`phi_binary`,
        `agreement`). Pass ``False`` from callers that read only the powers.
    icc : float, default 0.0
        Forwarded verbatim to `paired_marks`: the within-replicate intraclass
        correlation to simulate before computing either power.

    Returns
    -------
    tuple
        ``(power_unpaired, power_paired, phi_binary, agreement)`` -- the two
        powers (both at `ALPHA_BONF`, always floats), the realized binary (phi)
        correlation between the arms' marks, and their raw agreement rate. The
        last two are `None` when ``stats=False``.

    Notes
    -----
    The two powers do NOT depend on `stats`: the diagnostics consume no
    randomness, so a ``stats=False`` call returns exactly the powers the
    ``stats=True`` call on the same `rng` state would. `stats` exists purely for
    cost. Computing `phi` upcasts BOTH boolean mark arrays to float64, which at
    the top of `EQ_R_GRID` is ~1.55 GB of temporaries -- paid, in `part2`'s
    equivalent-R search, for two numbers the search then discards.
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
        # Explicit Nones, not zeros: "not measured" must not be mistakable for
        # "measured as uncorrelated" if a caller ever stores the result.
        return powers[0], powers[1], None, None
    # realized BINARY (phi) correlation between the two arms' marks, and agreement
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    agree = float((ma == mb).mean())
    return powers[0], powers[1], float(phi), agree


def study_design_effect() -> float | None:
    """Read the induction study's OWN measured design effect from the real tree.

    Median, over the 210 PRIMARY contrasts (`power_analysis.build_primary_contrasts`),
    of `paired_analysis.design_effect` computed on each contrast's item-matched
    marks (`paired_analysis.aligned`, ``drop_invalid=False``) -- the exact same
    estimator each of `part2`'s icc blocks reports on its own simulated marks,
    so the two numbers are directly comparable.

    Returns
    -------
    float or None
        `None` means exactly one of two things, both benign: no results tree
        exists at `paired_analysis.RESULTS_DIR` (the normal state of a fresh
        checkout -- this repository's own state), or every one of the 210
        contrasts came back with its own `design_effect` `None` (too few
        shared seeds, identical arms, or a degenerate stratum). There is no
        third case: any OTHER failure while reading an existing tree is
        allowed to propagate (see Notes).

    Notes
    -----
    `paired_analysis` and `power_analysis` are imported HERE, inside the
    function, rather than at module scope. This module's SIMULATION consumes
    constants only, never results (see the module docstring); importing a
    results-reading sibling at module scope would make every other function
    in this file -- and a bare ``import multiplicity_sim`` with no results
    tree present -- depend on that sibling's import-time side effects.

    Nothing here is wrapped in a bare ``except``. If a tree exists but a
    replicate in it is malformed, `paired_analysis.load_marks` raises, and
    that exception is left to propagate: silently swallowing it would let
    this function report a design effect computed from a silently partial
    read, which is precisely the failure mode a printed banner must not have.
    """
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


def part2(rng, n_sims=20000, search_sims=8000, cap=EQ_R_GRID[-1]):
    """Measure the power gain from pairing (matched items) over unpaired testing.

    Over a grid of baseline rates, accuracy gaps and latent correlations,
    compares unpaired CMH against paired exact McNemar on the same matched
    marks (`_paired_powers`). Where pairing helps, searches `EQ_R_GRID` (largest
    entry `cap`) with `search_sims` sims for the smallest unpaired replicate
    count matching the paired test's power at `R_DEFAULT`. Also reports
    null-calibration Type I error for both tests.

    The whole comparison above is run once per `icc` in `ICC_GRID` (0.0, 0.2,
    0.4), simulating the within-replicate clustering the real study's items
    have but earlier runs of this comparison did not model. Every printed
    block's header names its `icc`; every row dict carries an `icc` field;
    and every block additionally reports `design_effect_simulated`, the
    median `paired_analysis.design_effect` its own null-configuration marks
    (`p_a=p_b=0.90`, `rho=0.5`, the calibration row's configuration) produce,
    so a reader can compare that number against the study's own measured
    design effect (`study_design_effect`, printed once up front) and pick the
    icc row that describes their study. Writes ``OUT["part2"]``.

    Parameters
    ----------
    cap : int
        Search ceiling recorded on every row. Defaults to `EQ_R_GRID`'s last
        rung, so the docstring's "largest entry `cap`" holds by construction
        rather than by two literals agreeing.

    Notes
    -----
    `paired_analysis` is imported HERE, inside the function, for the same
    reason `study_design_effect` imports it locally: this module's SIMULATION
    consumes constants only, and a results-reading sibling must not become an
    import-time dependency of it.
    """
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
                    # equivalent R: smallest R at which the UNPAIRED test matches
                    # the paired test's power at R_DEFAULT (paired data throughout).
                    eq_r = None
                    if pair > unp + 0.005:
                        for rr in grid_r:
                            # stats=False: the search reads only the unpaired
                            # power, so the phi/agreement diagnostics would be
                            # computed and thrown away once per rung (see
                            # `_paired_powers`).
                            u2 = _paired_powers(p_a, delta, rho, rr, search_sims,
                                                rng, stats=False, icc=icc)[0]
                            if u2 >= pair:
                                eq_r = rr
                                break
                    else:
                        # Pairing did not help here, so no search ran; record the
                        # default R with the flag below rather than overloading
                        # eq_R (R_DEFAULT-from-search and R_DEFAULT-because-
                        # unsearched are different facts; None still means "grid
                        # exhausted").
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
            # stats=False for the same reason as the search above: `[:2]` already
            # says the diagnostics are unread, and this is the largest n_sims here.
            u, p = _paired_powers(0.90, 0.0, rho, R_DEFAULT, 60000, rng,
                                  stats=False, icc=icc)[:2]
            nulls[rho] = dict(unpaired_t1=u, mcnemar_t1=p)
            print(f"  icc={icc} NULL rho={rho}: unpaired T1={u:.6f} "
                  f"mcnemar T1={p:.6f}", flush=True)

        # This block's OWN measured design effect: draw the same null
        # configuration the calibration row above uses (p_a=p_b=0.90, rho=0.5),
        # then run the study's own `design_effect` estimator over each of the
        # `n_sims` simulated replicate blocks and report the median of the
        # measurable ones -- the same summary `study_design_effect` reports
        # over real contrasts, so the two numbers describe the same quantity.
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

    # Backward-compatible top level: `rows`/`nulls` keep meaning exactly the
    # icc=0.0 run, as they always have, while the clustered levels arrive
    # under the new `icc` key rather than by changing the shape underneath an
    # existing reader. The `icc` sub-keys are STRINGS (`str(icc)`) because
    # this dict is checkpointed to JSON and JSON has no float keys, so the
    # in-memory shape here is already the on-disk shape.
    OUT["part2"] = dict(rows=icc_blocks["0.0"]["rows"],
                        nulls=icc_blocks["0.0"]["nulls"],
                        n_sims=n_sims, alpha=ALPHA_BONF, grid_r=grid_r,
                        icc=icc_blocks)


# ============================================================== PART 4: correction cost
def build_rate_matrix():
    """Build a stylized 21-model x 4-info true-rate matrix for PART 4.

    Stylized per the brief: 30 true effects spread near ceiling and in the
    mid-range, the remaining 180 contrasts exact nulls.

    Returns
    -------
    ndarray, shape (7, 3, 4)
        True per-(family, rung, info) success rates.
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

    A step-up procedure (Hochberg; Benjamini-Hochberg) walks the SORTED
    p-values from the largest rank down, rejects at the first (largest) rank
    whose sorted p-value is at or below its own per-rank threshold, and then
    rejects every rank at or below that one too. Hochberg and BH differ only
    in `thresholds`' formula (``alpha / (m - i + 1)`` vs ``alpha * i / m``);
    this helper is that shared mechanics, parameterized on the threshold
    array so both callers share one implementation. Holm is a step-DOWN
    procedure (walks from the SMALLEST p-value up, stops at the first
    VIOLATION) and is different enough in direction and stopping rule that it
    keeps its own loop in `apply_corrections` rather than reusing this one.

    Parameters
    ----------
    sortedp : ndarray, shape (S, m)
        p-values sorted ascending along axis 1 (`np.take_along_axis(pv, order,
        axis=1)`), across `S` simulated families of `m` tests each.
    order : ndarray, shape (S, m)
        The permutation that produced `sortedp` from the original array
        (`np.argsort(pv, axis=1)`); used here only to scatter the rejection
        mask back to `pv`'s original column order.
    thresholds : ndarray, shape (m,)
        Per-rank threshold, rank 1 first (the smallest p-value's rank), in
        the same units as `sortedp` (i.e. already includes `alpha`).

    Returns
    -------
    ndarray of bool, shape (S, m)
        Per-simulation, per-test rejection mask, in `pv`'s ORIGINAL column
        order (not sorted order).

    Notes
    -----
    ``ok[:, ::-1].argmax(axis=1)`` finds the LAST True along axis 1 by
    reversing and taking the first True from the end; ``m - 1 - ...`` maps
    that reversed index back to the original (ascending-rank) position. Rows
    with no True at all (``ok.any(axis=1)`` False) get sentinel index -1, so
    ``keep = ranks <= idx`` is all-False for that row -- nothing rejected,
    without a separate branch.
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

    Parameters
    ----------
    pv : ndarray, shape (S, m)
        p-values for `m` tests, across `S` simulations. `m` is read from
        `pv.shape[1]` rather than taken as a parameter: a caller passing a
        wrong `m` here would get every threshold below computed from it and
        every returned mask silently mis-corrected, with nothing to signal
        the mistake.

    Returns
    -------
    dict of str -> ndarray of bool, shape (S, m)
        Procedure name -> per-simulation, per-test rejection mask, in `pv`'s
        original column order.

    Notes
    -----
    This used to also take `is_null`, a per-test truth vector -- but the
    function never read it (only `part4`'s caller did, combining the masks
    returned here with its OWN truth vector to compute FWER/FDR/power), so it
    was dead weight on every call site.

    Holm (step-down) keeps its own loop: it walks sorted p-values from
    smallest to largest and stops at the first VIOLATION of its threshold,
    the opposite traversal and stopping rule from Hochberg and BH (both
    step-up), which now share the `_stepup` helper.
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


def part4(rng, n_sims=4000):
    """Measure the cost of multiplicity correction against `build_rate_matrix`'s truth.

    Compares the full 210-contrast PRIMARY family (84 ladder + 126 info) with a
    reduced 154-test family (28 one-df trend tests replacing the 84 pairwise
    ladder contrasts) under Bonferroni, Holm, Hochberg and BH
    (`apply_corrections`), reporting true/false rejection counts, FWER, FDR and
    how many of the truly non-flat ladders each procedure flags (the rate
    matrix fixes their count; the code computes and prints it rather than
    trusting this docstring). A third
    "test-swap only" arm holds the family size at 210 (alpha unchanged) while
    swapping in the trend test, isolating test choice from correction. Writes
    ``OUT["part4"]``.
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
    # A raise, not an assert: `python -O` strips asserts, and this gate is what
    # ties the simulated family to the study's real PRIMARY family size -- the
    # denominator every alpha in this part divides by.
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
    # Same reasoning as the m_full gate above, against the module constant PART
    # 5 prices its study-wide trend row at.
    if m_red != N_REDUCED:
        raise RuntimeError(
            f"PART 4 built {m_red} reduced-family tests but N_REDUCED is "
            f"{N_REDUCED}; PART 5's alpha_trend_studywide (ALPHA / N_REDUCED) "
            "would then correct the trend test in a family that does not exist."
        )

    def summarize(name, rejmap, nullmask, ladder_flag_fn):
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

    def flag_full(rej):
        nf = np.where(ladder_nonflat)[0]
        got = np.zeros((rej.shape[0], 28), dtype=bool)
        for t_ in range(84):
            got[:, lad_pair_ladder[t_]] |= rej[:, t_]
        return got[:, nf].sum(axis=1)

    def flag_red(rej):
        nf = np.where(ladder_nonflat)[0]
        return rej[:, :28][:, nf].sum(axis=1)

    full = summarize("m=210", apply_corrections(pv), is_null, flag_full)
    red2 = summarize("m=154", apply_corrections(pv_red), null_red, flag_red)
    # DECOMPOSITION: hold the family size at 210 (alpha unchanged) but swap the TEST
    # (3 pairwise -> 1 trend per ladder). Difference vs the m=154 arm isolates the
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


def main():
    """Run PARTs 1, 3, 5, 2, 4 in that order (not PART-number order), checkpointing each.

    Each part gets its OWN generator, derived from `_power_common.SEED` as
    ``SEED + <part number>``, so a re-run is reproducible.

    Notes
    -----
    Per-part offsets rather than one shared stream: each part then draws from a
    stream of its own, so adding, removing or reordering a part cannot perturb
    another part's draws. (That is the same rationale
    `power_analysis.omnibus_interaction_power` gives for its ``SEED + 1``.)
    The offset is the PART NUMBER, not the position in the run order above, so
    the mapping survives the reordering.

    ``SEED`` is 0, so ``SEED + 1 .. SEED + 5`` are the seeds 1..5 these parts
    were previously given as literals: this is a readability change with no
    numerical effect on any published figure.
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
