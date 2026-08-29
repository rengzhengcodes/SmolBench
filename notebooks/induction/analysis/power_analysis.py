"""
Power analysis for the family-ladder SCALING study (notebooks/induction).

This uses the periodic induction task, harmonic strata, and
stratified-CMH statistics. Two design facts drive everything below:

  1. The MODEL SET is 7 model families x 3 parameter-count rungs each = 21
     models (see `MODELS` / `FAMILIES` below). This is a SCALING study: it
     asks how accuracy moves along a family's small -> medium -> large
     ladder, not just across families.
  2. The CONTRAST FAMILY is three PRE-REGISTERED tiers (see "Contrast
     tiers" below). An
     all-pairs family over 21 models would need C(21, 2) x len(INFOS) =
     210 x 4 = 840 model-vs-model contrasts alone, before even counting
     the within-model info-arm contrasts. Bonferroni-correcting for that
     many tests would cost roughly a further 4x hit to alpha (840 vs the
     ~210 this script actually plans), for comparisons the study never
     intended to make in the first place. For example, "does glm_flash
     beat exaone_33b on extens" is not a question this study is designed
     to answer; it is an accidental byproduct of enumerating every pair.
     The scaling question this study asks is (a) what happens ALONG a
     family's ladder and (b) how the four info arms separate WITHIN one
     model. Those two questions form the PRIMARY family,
     Bonferroni-corrected at full force. Cross-family comparisons are
     secondary: size-matched rung-vs-rung, on `intens` only, as a coarse
     "are the families roughly comparable at each size class" check. They
     get a less punishing Benjamini-Hochberg FDR correction on that single
     primary info arm.

Contrast tiers
--------------
Tier 1 -- family omnibus gates (7 tests, alpha = ALPHA / 7): "does this
    family's 3 rungs differ AT ALL". This is a generalized
    (Cochran-)Mantel-Haenszel test (see `gcmh_reject`), stratified by
    harmonic x info (K = 36 strata), df = 2 (3 rungs). A family's Tier-2
    ladder contrasts count as more than exploratory only once its omnibus
    gate rejects -- see `main`'s printed output.
Tier 2 -- PRIMARY pairwise family (N_PRIMARY = 210, Bonferroni,
    ALPHA_PRIMARY = ALPHA / 210): 84 within-family ladder contrasts (7
    families x 4 infos x 3 rung-pairs) plus 126 within-model info
    contrasts (21 models x 6 info-pairs). See `build_primary_contrasts`.
Tier 3 -- SECONDARY pairwise family (N_SECONDARY = 63, Benjamini-Hochberg,
    q = 0.05): cross-family, size-matched rung-vs-rung contrasts on
    `intens` only (3 rung levels x C(7, 2) = 21 family-pairs). This tier
    is sized at the conservative rank-1 BH threshold ALPHA_SECONDARY =
    Q_SECONDARY / N_SECONDARY. That threshold is an UPPER BOUND on the R
    that BH will actually need at analysis time: BH's per-test threshold
    equals q * rank / m, so only the single MOST significant test is held
    to q/m. Every other rank gets a LESS strict (larger) threshold, and
    this script has no way to know in advance which rank a given contrast
    will land at. See `build_secondary_contrasts`.

Design notes (stratified CMH, unchanged from periodic_moe)
------------------------------------------------------------
This script reads exactly one binary outcome per harmonic k = 1..9 per
condition, from the PILOT run. `numeric_count_query_gen` yields one count
question per period, in ascending period order, so mark order recovers
the harmonic. Difficulty varies systematically with k, so the data form a
stratified binomial with the harmonic as the stratum, NOT 9 iid Bernoulli
draws. Power therefore scales with replicates per harmonic. The planned
PAIRWISE analysis-time test is the Cochran-Mantel-Haenszel (CMH) test,
stratified by harmonic (`cmh_reject`). The planned FAMILY-OMNIBUS test
additionally stratifies by info arm and generalizes CMH to 3 categories
(`gcmh_reject`). This script could add harmonics instead, but that would
change task difficulty (and blow up lcm(1..n) context length), which
would confound the comparison.

The simulation shrinks each condition's single observed outcome y_k
toward the assumed true per-harmonic rate, using the condition mean
p_bar: p_k = (y_k + c * p_bar) / (1 + c) with c = 1 (a harmonic that
failed once is not assumed to fail with certainty). A sensitivity pass
with pure condition-mean rates (no per-harmonic structure) is reported
alongside.

Data availability
------------------
This study is user-locked to BASE_SEED = 0 (see `PILOT_SEED` below). Its
results are S3-backed (SMOLBENCH_RESULTS_S3), not committed to the repo as
a flat or per-replicate YAML tree.
So `load_outcomes` raises a `SystemExit` with an actionable message
(instead of an obscure FileNotFoundError traceback). That message names
the exact missing path and points at
``InductionExperiment.harness.sync_down()`` as the fix: that call pulls
the S3-backed append-only log down into the local
``{model}_{info}/rep_{seed}.yaml`` layout this script reads. If the pilot
(seed 0) has not run at all, run it via notebooks/induction/run_study.py
first. If it has run but the local results/ tree is stale or absent (for
example, a fresh checkout), run sync_down() instead.

Run (ephemeral env via --no-project: plain `uv run` would sync the project
and strip the notebook/dev extras from .venv):
    uv run --no-project --with numpy --with scipy --with statsmodels python notebooks/induction/analysis/power_analysis.py
"""

import re
import sys
from itertools import combinations
from pathlib import Path

# notebooks/ (where _power_common.py lives) is one level up from this
# script's directory. The path is __file__-anchored, so the import works
# regardless of the caller's cwd (repo convention -- see _power_common.py
# itself).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from scipy.stats import chi2

from _power_common import (
    ALPHA,
    POWER_TARGETS,
    SEED,
    fmt_r,
    results_dir,
)

# ---------------------------------------------------------------------------
# Experiment design: 7 model families x 3 parameter-count rungs = 21 models,
# same periodic induction task and 4 info arms as periodic_moe. MODELS and
# FAMILIES are given verbatim by the study spec.
# ---------------------------------------------------------------------------
MODELS = (
    "qwen35_27b", "qwen35_122b", "qwen35_397b",
    "nemo3_4b", "nemo3_30b", "nemo3_120b",
    "gemma4_e2b", "gemma4_12b", "gemma4_31b",
    "glm_flash", "glm_air", "glm_47",
    "min3_3b", "min3_8b", "min3_14b",
    "exaone_32b", "exaone_33b", "exaone_236b",
    "ds_flash", "ds_v31", "ds_pro",
)

FAMILIES: dict[str, tuple[str, str, str]] = {
    "qwen35":  ("qwen35_27b", "qwen35_122b", "qwen35_397b"),
    "nemo3":   ("nemo3_4b", "nemo3_30b", "nemo3_120b"),
    "gemma4":  ("gemma4_e2b", "gemma4_12b", "gemma4_31b"),
    "glm":     ("glm_flash", "glm_air", "glm_47"),
    "min3":    ("min3_3b", "min3_8b", "min3_14b"),
    "exaone":  ("exaone_32b", "exaone_33b", "exaone_236b"),
    "ds":      ("ds_flash", "ds_v31", "ds_pro"),
}

# Drift guard: hand-maintained tables. MODELS is a flat tuple for
# iteration order; FAMILIES holds the ladder/omnibus structure. The two
# must never disagree about which 21 models exist or what order they are
# in.
#
# This check runs at MODULE scope, not just inside `main`, so importing
# this module for its constants elsewhere (for example, a notebook) also
# gets the guard for free. `main` re-asserts it too, per the spec's
# explicit "assert BOTH" requirement. That is a second, load-bearing line
# of defense against a future edit that changes one table without the
# other.
assert MODELS == tuple(rung for rungs in FAMILIES.values() for rung in rungs), (
    "MODELS must equal the concatenation of FAMILIES' rungs, in FAMILIES order"
)

INFOS = ("intens", "extens", "noise_intens", "zero")   # unchanged from periodic_moe
N_HARMONICS = 9                                         # unchanged
PILOT_SEED = 0                                          # CHANGED: seed 0, file rep_0.yaml
# NOTE: PILOT_SEED (which replicate seed's YAML to read) and SEED (from
# _power_common, the RNG seed for this script's OWN Monte Carlo
# simulations) both happen to equal 0 in this study. That is a
# coincidence: this study is locked to BASE_SEED = 0. The two constants
# are conceptually unrelated -- one names a results file, the other
# reseeds `np.random.default_rng` before every contrast. Do not assume
# they stay interchangeable if either changes independently in the
# future.

RESULTS_DIR = results_dir(__file__, up=1)

# Simulation parameters specific to this script's stratified-CMH design
# (not shared with chromatic's quiz-level design). Values are unchanged
# from periodic_moe. This study's larger contrast family (210 + 63 vs. 30)
# makes the script slower to run, not less precise. N_SIMS is NOT reduced
# to compensate (see module docstring).
N_SIMS = 10_000
MAX_REPLICATES = 200
SHRINKAGE = 1.0  # c in p_k = (y_k + c * p_bar) / (1 + c)

# ---------------------------------------------------------------------------
# Tier alphas. These are defined before the functions below, so their
# `alpha=...` default arguments bind to these study-specific values. The
# archived script had only one tier and one ALPHA_CORRECTED. This study's
# PRIMARY and SECONDARY tiers need different per-test alphas, so `alpha`
# becomes an explicit parameter throughout -- see the NOTE on
# `simulated_power`.
# ---------------------------------------------------------------------------

# Tier 2 -- PRIMARY: 84 ladder contrasts (7 families x 4 infos x
# C(3, 2)=3 rung-pairs) + 126 info contrasts (21 models x C(4, 2)=6
# info-pairs). Bonferroni over the full family.
N_PRIMARY = 210
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# Tier 3 -- SECONDARY: 3 rung levels x C(7, 2)=21 family-pairs, on `intens`
# only. Benjamini-Hochberg FDR at q=0.05; sized at BH's conservative rank-1
# threshold (see module docstring's "Contrast tiers" section).
Q_SECONDARY = 0.05
N_SECONDARY = 63
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

# Tier 1 -- family omnibus gates: one generalized-CMH test per family.
N_FAMILIES = len(FAMILIES)  # 7
ALPHA_OMNIBUS = ALPHA / N_FAMILIES


def load_outcomes() -> dict[tuple[str, str], np.ndarray]:
    """Load per-condition PILOT harmonic outcome vectors.

    Reads the pilot run's replicate file,
    ``{model}_{info}/rep_{PILOT_SEED}.yaml`` (PILOT_SEED = 0 for this
    study -- see the module docstring's "Data availability" section).

    Unlike the archived periodic_moe version, this function keeps no
    flat-file fallback: this study never had a flat layout. Its results
    are S3-backed, so a missing file most likely means the results have
    not synced down yet, rather than that they were archived under an
    older layout. The `SystemExit` message says so.

    The result YAMLs carry !!python/object tags, so this function avoids
    an unsafe load. Instead it regexes the per-mark `score:` lines. Marks
    are serialized in the generator's ascending-period order, so position
    recovers the harmonic.

    Returns
    -------
    dict of (str, str) -> ndarray
        Maps each ``(model, info)`` condition to a length-`N_HARMONICS`
        array of outcomes, index k-1 for harmonic k. Each entry is 1.0
        for a correct mark and 0.0 for a failure (score 0 or a null,
        invalid, mark).

    Raises
    ------
    SystemExit
        If the pilot replicate file for a condition is missing. The
        message names the exact missing path and points at
        ``InductionExperiment.harness.sync_down()`` as the fix.
    """
    outcomes: dict[tuple[str, str], np.ndarray] = {}
    for model in MODELS:
        for info in INFOS:
            path = RESULTS_DIR / f"{model}_{info}" / f"rep_{PILOT_SEED}.yaml"
            if not path.exists():
                raise SystemExit(
                    f"No pilot replicate for ({model}, {info}); expected\n  {path}\n"
                    f"This analysis SIZES R from the pilot (seed {PILOT_SEED}) -- "
                    f"run the pilot in notebooks/induction/run_study.py first. "
                    f"This study's results are S3-backed (SMOLBENCH_RESULTS_S3): "
                    f"if the pilot already ran (elsewhere, or in an earlier "
                    f"session), sync it down before re-running this script -- "
                    f"call InductionExperiment.harness.sync_down() to pull the "
                    f"S3-backed append-only log into the local "
                    f"{{model}}_{{info}}/rep_{{seed}}.yaml layout this script "
                    f"reads (it never talks to S3 directly)."
                )
            text = path.read_text()
            scores = re.findall(r"^\s*score:\s*(\S+)", text, re.M)
            assert len(scores) == N_HARMONICS, (model, info, len(scores))
            # score 1 = correct; 0 or null (invalid) = failure.
            outcomes[(model, info)] = np.array(
                [1.0 if s == "1" else 0.0 for s in scores]
            )
    return outcomes


def shrunk_rates(y: np.ndarray, c: float = SHRINKAGE) -> np.ndarray:
    """Per-harmonic rates shrunk toward the condition mean."""
    return (y + c * y.mean()) / (1.0 + c)


def cmh_reject(
    succ_a: np.ndarray, succ_b: np.ndarray, n_per_stratum: int, alpha: float
) -> np.ndarray:
    """Run a vectorized CMH test (2 x 2 x K strata, continuity-corrected).

    Unchanged from the archived periodic_moe version. This is the
    PAIRWISE (2-condition) test used by Tier 2 and Tier 3, stratified by
    harmonic only (K = N_HARMONICS). It is a distinct statistic from
    `gcmh_reject` below, which compares 3 categories at once, stratifies
    by harmonic x info, and skips the continuity correction. The two are
    not literally the same formula specialized to R=2, so this docstring
    claims no equivalence between them.

    Parameters
    ----------
    succ_a, succ_b : ndarray of int, shape (n_sims, K)
        Success counts out of `n_per_stratum` per stratum, for each of
        the two compared conditions.
    n_per_stratum : int
        Trials per stratum, the same for both conditions.
    alpha : float
        Two-sided significance threshold for the test.

    Returns
    -------
    ndarray of bool, shape (n_sims,)
        True where the statistic exceeds ``chi2.isf(alpha, df=1)``.
    """
    n = n_per_stratum
    big_n = 2 * n  # total per stratum
    m1 = succ_a + succ_b  # successes per stratum
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.abs((succ_a - expect).sum(axis=1)) - 0.5
    num = np.clip(num, 0.0, None) ** 2
    denom = var.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        stat = np.where(denom > 0, num / denom, 0.0)
    return stat > chi2.isf(alpha, df=1)


def gcmh_reject(succ: np.ndarray, n_per_stratum: int, alpha: float) -> np.ndarray:
    """Run a vectorized generalized CMH ("general association") test, R=3 rungs.

    This is the Tier-1 family omnibus gate. It tests whether a family's 3
    rungs (small/medium/large) differ AT ALL, stratified by K =
    N_HARMONICS * len(INFOS) = 36 strata (one per harmonic x info-arm
    combination).

    Parameters
    ----------
    succ : ndarray of int, shape (n_sims, 3, K)
        Per-simulation success counts. Axis 0 indexes independent Monte
        Carlo simulations, axis 1 the family's 3 rungs (in ladder order),
        axis 2 the K strata.
    n_per_stratum : int
        Trials per rung per stratum. Must be identical for every rung and
        every stratum: this power simulation always scans one candidate
        replicate count R and applies it uniformly to every condition, so
        the covariance derived below collapses to a scalar multiple of a
        fixed matrix (see "Derivation"). Must be >= 1.
    alpha : float
        Two-sided significance threshold for this test (ALPHA_OMNIBUS =
        ALPHA / N_FAMILIES for the Tier-1 gates in this study).

    Returns
    -------
    ndarray of bool, shape (n_sims,)
        True where the statistic exceeds ``chi2.isf(alpha, df=2)``.

    Raises
    ------
    ValueError
        If `succ`'s rung axis (axis 1) does not have length 3, or if
        `n_per_stratum` < 1.

    Notes
    -----
    Derivation
    ~~~~~~~~~~
    This is the standard R-category generalization of the 2x2xK CMH
    statistic (Agresti, *Categorical Data Analysis*, Sec. 7.5; SAS PROC
    FREQ's "general association" CMH statistic). Here it is specialized
    to R = 3 nominal rungs and a binary (success/failure) response.

    Fix a stratum j. Rung r contributes n_rj = n_per_stratum trials.
    Write N_j = sum_r n_rj = 3 * n_per_stratum for the stratum total, and
    M_j = sum_r succ_rj for the stratum's total successes. Assume the
    null hypothesis: all 3 rungs share one success probability, specific
    to the stratum but the same across rungs. Under that null, the vector
    of rung success counts (succ_1j, succ_2j, succ_3j), CONDITIONAL on
    the rung sample sizes n_rj and the stratum total M_j, follows a
    multivariate hypergeometric distribution. This is exactly the
    distribution of drawing M_j balls without replacement from an urn of
    N_j balls split into 3 groups of sizes n_1j, n_2j, n_3j, where a
    drawn ball means that trial succeeded. This is the natural
    generalization of the 2x2 CMH null (itself a hypergeometric) to R > 2
    categories.

    The multivariate hypergeometric has known moments:
        E[succ_rj]            = n_rj * M_j / N_j
        Var[succ_rj]          = M_j * (n_rj/N_j) * (1 - n_rj/N_j) * (N_j - M_j) / (N_j - 1)
        Cov[succ_rj, succ_sj] = -M_j * (n_rj/N_j) * (n_sj/N_j) * (N_j - M_j) / (N_j - 1)   (r != s)

    Only R - 1 = 2 of the 3 per-stratum residuals are free: they sum to
    zero by construction (sum_r (succ_rj - E[succ_rj]) == 0). So the test
    statistic uses the first 2 rungs' residuals, summed over strata:
        T     = sum_j (succ_1j - E[succ_1j], succ_2j - E[succ_2j])   (a 2-vector)
        Sigma = sum_j Sigma_j                                        (2x2, from the moments above)
        Q     = T' Sigma^-1 T   ~   chi2(df=2)   under H0.

    In this simulation, n_rj == n_per_stratum for EVERY rung r and
    stratum j (the whole point of scanning "one candidate R applied
    uniformly"). So n_rj / N_j == 1/3 is the SAME constant in every
    stratum. That makes Sigma_j = w_j * C0, for a fixed matrix
    C0 = [[2/9, -1/9], [-1/9, 2/9]] and a per-stratum, per-simulation
    scalar w_j = M_j * (N_j - M_j) / (N_j - 1). The sum over strata gives
    Sigma = (sum_j w_j) * C0 EXACTLY. This is an algebraic consequence of
    the design, not an approximation.

    # Design: the code below DELIBERATELY TAKES the C0 collapse proved in
    # the Derivation above. It does not build a per-stratum (S, K, 2, 2)
    # covariance stack and sum it. `p = n / total_n` is a single scalar.
    # `shape` is the ONE fixed 2x2 matrix built from that scalar. And
    # `sigma = w[:, None, None] * shape[None, :, :]` forms Sigma from a
    # per-simulation scalar `w = common.sum(axis=1)`. In other words, the
    # per-stratum w_j terms are summed as plain scalars before the code
    # builds any matrix.
    #
    # This collapse is EXACT, not an approximation. But it holds only
    # because `n_per_stratum` is a single scalar `int`, applied uniformly
    # to every rung and every stratum. That is this function's documented
    # precondition, enforced by the signature itself: there is no way to
    # pass a per-rung or per-stratum trial count today. That scalar
    # signature is precisely what keeps the shortcut safe; it is not a
    # happy accident. A generalization to unequal n_rj (for example,
    # per-rung or per-stratum replicate counts) would NOT "keep working
    # unmodified". p would no longer be a single constant, the C0
    # collapse would no longer hold, and `sigma` would need rebuilding
    # as a genuine per-stratum (S, K, 2, 2) stack, summed over K,
    # before inversion. That is a real code change this function does
    # not attempt, not a free property of the current one.
    #
    # Exact singularity of Sigma occurs exactly when w_j == 0 in every
    # stratum at once (that is, M_j in {0, N_j} everywhere -- no stratum
    # has any cross-rung variance to test). This happens routinely at R=1:
    # a stratum where all 3 rungs agree, success or failure, has zero
    # variance. `numpy.linalg.solve` raises `LinAlgError` on an exactly
    # singular batched system (verified empirically: a batch containing
    # even one singular matrix aborts the WHOLE batched solve). So the
    # fallback below uses the fully-vectorized Moore-Penrose pseudo-inverse
    # (`numpy.linalg.pinv`, itself batched over simulations via SVD),
    # instead of re-solving one simulation at a time. `pinv` of an
    # all-zero Sigma is the all-zero matrix. And Sigma == 0 forces T == 0
    # too, because zero variance means every stratum's counts sit exactly
    # at their null expectation. So the fallback's Q = T' @ 0 @ T = 0 is
    # the mathematically correct "no evidence against the null" answer
    # for that simulation, not an artifact of the fallback.
    """
    _, n_rungs, _ = succ.shape
    if n_rungs != 3:
        raise ValueError(
            f"gcmh_reject assumes 3 rungs (ladder-of-3 families); got axis-1 "
            f"size {n_rungs}"
        )
    if n_per_stratum < 1:
        raise ValueError(f"n_per_stratum must be >= 1, got {n_per_stratum}")
    df = n_rungs - 1  # 2

    n = float(n_per_stratum)
    total_n = n_rungs * n  # N_j: constant across strata AND rungs by this design

    total_succ = succ.sum(axis=1)  # (S, K) == M_j
    # E[succ_rj] = n_rj * M_j / N_j == M_j / n_rungs for every r (n_rj constant).
    expected = total_succ / n_rungs  # (S, K)
    resid = succ - expected[:, None, :]  # (S, 3, K)
    # Drop the R-th (redundant) category: sum_r resid_rj == 0 by construction.
    t_vec = resid[:, :df, :].sum(axis=2)  # (S, df)

    p = n / total_n  # == 1 / n_rungs
    common = total_succ * (total_n - total_succ) / (total_n - 1.0)  # (S, K) == w_j
    shape = np.full((df, df), -p * p)
    np.fill_diagonal(shape, p * (1.0 - p))
    w = common.sum(axis=1)  # (S,) == sum_j w_j
    sigma = w[:, None, None] * shape[None, :, :]  # (S, df, df)

    try:
        solved = np.linalg.solve(sigma, t_vec[:, :, None])[:, :, 0]
        stat = np.einsum("sd,sd->s", t_vec, solved)
    except np.linalg.LinAlgError:
        # Singular-Sigma fallback: see the "Design" note above.
        sigma_inv = np.linalg.pinv(sigma)  # batched SVD pseudo-inverse
        stat = np.einsum("sd,sde,se->s", t_vec, sigma_inv, t_vec)

    return stat > chi2.isf(alpha, df=df)


def simulated_power(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_PRIMARY,
    n_sims: int = N_SIMS,
) -> float:
    """Compute power of the harmonic-stratified CMH test with n_reps per harmonic.

    Parameters
    ----------
    rates_a, rates_b : ndarray
        Assumed true per-harmonic rates for each of the two conditions.
    n_reps : int
        Candidate replicate count per harmonic.
    rng : numpy.random.Generator
        Source of randomness for the simulated binomial draws.
    alpha : float, default ALPHA_PRIMARY
        Two-sided significance threshold for the CMH test.
    n_sims : int, default N_SIMS
        Number of Monte Carlo simulations.

    Returns
    -------
    float
        Fraction of simulations in which `cmh_reject` rejects the null.

    Notes
    -----
    # Design: the archived periodic_moe version defaulted `alpha` to a
    # single module-global ALPHA_CORRECTED, because that study had only
    # one pairwise contrast family. This study has two (PRIMARY,
    # Bonferroni; SECONDARY, BH-worst-case) with different per-test
    # alphas. So `main` threads `alpha` through explicitly at every call
    # site. The ALPHA_PRIMARY default here exists only so the function
    # still works standalone, for example in ad hoc REPL use.
    """
    succ_a = rng.binomial(n_reps, rates_a, size=(n_sims, rates_a.size))
    succ_b = rng.binomial(n_reps, rates_b, size=(n_sims, rates_b.size))
    return cmh_reject(succ_a, succ_b, n_reps, alpha).mean()


def replicates_needed(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    rng: np.random.Generator,
    alpha: float = ALPHA_PRIMARY,
) -> tuple[dict[float, int | None], dict[int, float]]:
    """Find the smallest replicate count R that reaches each power target.

    Scans R = 1, 2, ... and stops once every target is met.

    Parameters
    ----------
    rates_a, rates_b : ndarray
        Assumed true per-harmonic rates for each of the two conditions.
    rng : numpy.random.Generator
        Source of randomness for the simulated binomial draws.
    alpha : float, default ALPHA_PRIMARY
        Two-sided significance threshold, passed to `simulated_power`.

    Returns
    -------
    needed : dict of float -> (int or None)
        Maps each power target in `POWER_TARGETS` to the smallest R that
        reaches it, or `None` if no R up to `MAX_REPLICATES` reaches it.
    curve : dict of int -> float
        Maps each scanned R to its simulated power.

    Notes
    -----
    # NOTE: `alpha` was added for the same reason as `simulated_power` --
    # see its Notes section. The archived version took no `alpha`
    # argument.
    """
    needed: dict[float, int | None] = {t: None for t in POWER_TARGETS}
    curve: dict[int, float] = {}
    for n_reps in range(1, MAX_REPLICATES + 1):
        power = simulated_power(rates_a, rates_b, n_reps, rng, alpha=alpha)
        curve[n_reps] = power
        for target in POWER_TARGETS:
            if needed[target] is None and power >= target:
                needed[target] = n_reps
        if all(needed[t] is not None for t in POWER_TARGETS):
            break
    return needed, curve


def fisher_check(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_PRIMARY,
) -> float:
    """Cross-check power with a pooled (unstratified) two-sided Fisher exact test.

    Parameters
    ----------
    rates_a, rates_b : ndarray
        Assumed true per-harmonic rates for each of the two conditions.
    n_reps : int
        Candidate replicate count per harmonic.
    rng : numpy.random.Generator
        Source of randomness for the simulated binomial draws.
    alpha : float, default ALPHA_PRIMARY
        Two-sided significance threshold for the Fisher exact test.

    Returns
    -------
    float
        Fraction of simulations in which the pooled Fisher exact test
        rejects the null.

    Notes
    -----
    This function memoizes results on the discrete success counts, so the
    scipy call count stays small despite N_SIMS simulations.

    # NOTE: `alpha` was added for the same reason as `simulated_power` --
    # see its Notes section. The archived version hard-coded the single
    # module-global ALPHA_CORRECTED inside the function body.
    """
    from scipy.stats import fisher_exact

    total = n_reps * N_HARMONICS
    succ_a = rng.binomial(n_reps, rates_a, size=(N_SIMS, rates_a.size)).sum(axis=1)
    succ_b = rng.binomial(n_reps, rates_b, size=(N_SIMS, rates_b.size)).sum(axis=1)
    cache: dict[tuple[int, int], bool] = {}
    rejections = 0
    for ka, kb in zip(succ_a, succ_b):
        key = (int(ka), int(kb))
        if key not in cache:
            _, p = fisher_exact([[ka, total - ka], [kb, total - kb]])
            cache[key] = p < alpha
        rejections += cache[key]
    return rejections / N_SIMS


def equivalence_replicates(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    delta: float,
    rng: np.random.Generator,
    alpha: float = ALPHA,
    n_sims: int = N_SIMS,
) -> int | None:
    """Find the smallest R at which TOST shows equivalence with 80% power.

    Assumes the contrast is a TRUE tie: both conditions share per-harmonic
    rates equal to the mean of the two conditions' assumed rates. This
    function declares equivalence when the (1 - 2*alpha) Wald CI for the
    pooled accuracy difference lies inside (-delta, +delta). That is the
    standard two one-sided tests (TOST) at alpha each.

    The test is pooled (unstratified) on purpose: under exact equality,
    the stratified and pooled risk differences coincide.

    Unchanged from the archived periodic_moe version.

    Parameters
    ----------
    rates_a, rates_b : ndarray
        Assumed true per-harmonic rates for each of the two conditions.
    delta : float
        Equivalence margin: the pooled accuracy difference must fall
        inside (-delta, +delta).
    rng : numpy.random.Generator
        Source of randomness for the simulated binomial draws.
    alpha : float, default ALPHA
        Per-one-sided-test significance threshold.
    n_sims : int, default N_SIMS
        Number of Monte Carlo simulations.

    Returns
    -------
    int or None
        The smallest R in ``range(1, MAX_REPLICATES + 1)`` reaching 80%
        equivalence power, or `None` if no R in that range reaches it.
    """
    from scipy.stats import norm

    common = (rates_a + rates_b) / 2.0
    z = norm.isf(alpha)
    for n_reps in range(1, MAX_REPLICATES + 1):
        total = n_reps * N_HARMONICS
        succ_a = rng.binomial(n_reps, common, size=(n_sims, common.size)).sum(axis=1)
        succ_b = rng.binomial(n_reps, common, size=(n_sims, common.size)).sum(axis=1)
        p_a, p_b = succ_a / total, succ_b / total
        diff = p_a - p_b
        se = np.sqrt(p_a * (1 - p_a) / total + p_b * (1 - p_b) / total)
        power = ((diff + z * se < delta) & (diff - z * se > -delta)).mean()
        if power >= 0.80:
            return n_reps
    return None


def omnibus_power(
    rates: dict[tuple[str, str], np.ndarray],
    family: str,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_OMNIBUS,
    n_sims: int = N_SIMS,
) -> float:
    """Compute simulated power of `family`'s Tier-1 omnibus gate at `n_reps` replicates.

    Parameters
    ----------
    rates : dict of (str, str) -> ndarray
        Per-(model, info) assumed true per-harmonic rates (the same
        shrunk-toward-mean rates used everywhere else in this script), keyed
        exactly like `load_outcomes`'s return value.
    family : str
        A key of `FAMILIES`; its 3 rungs (in ladder order) are the 3
        categories the generalized CMH test compares.
    n_reps : int
        Candidate replicate count R, applied uniformly to every rung and
        every stratum (`gcmh_reject`'s precondition on `n_per_stratum`).
    rng : numpy.random.Generator
        Source of randomness for the simulated binomial draws. Callers pass
        a freshly-seeded generator so repeated calls are reproducible (this
        script's "same RNG stream per contrast/gate" discipline).
    alpha : float, default ALPHA_OMNIBUS
        Significance threshold passed through to `gcmh_reject`.
    n_sims : int, default N_SIMS
        Number of Monte Carlo simulations.

    Returns
    -------
    float
        Fraction of simulations in which `gcmh_reject` rejects the null --
        the simulated statistical power of the family's omnibus gate at
        this replicate count, assuming `rates` are the true
        per-(rung, harmonic, info) success probabilities.

    Notes
    -----
    Builds a (3, K) grid of assumed rates (3 rungs x K = N_HARMONICS *
    len(INFOS) = 36 strata), draws Binomial(n_reps, rate) success counts
    for every (simulation, rung, stratum) cell, and hands the result to
    `gcmh_reject`. Time complexity is O(n_sims * K) for the draw plus the
    (cheap, 2x2) linear algebra inside `gcmh_reject`.
    """
    rungs = FAMILIES[family]
    strata = [(k, info) for info in INFOS for k in range(N_HARMONICS)]  # K = 36
    cell_rates = np.array(
        [[rates[(rung, info)][k] for k, info in strata] for rung in rungs]
    )  # (3, K)
    succ = rng.binomial(
        n_reps, cell_rates[None, :, :], size=(n_sims, len(rungs), len(strata))
    )
    return gcmh_reject(succ, n_reps, alpha).mean()


def omnibus_interaction_power(
    rates: dict[tuple[str, str], np.ndarray], n_reps: int, n_sims: int = 1000
) -> float:
    """Compute power of the model x info-type interaction (logit LR test).

    This function fits Bernoulli GLMs with harmonic, model, and info
    fixed effects, with and without the model:info interaction. It fits
    them on simulated data with n_reps replicates per harmonic per
    condition, at alpha = 0.05. This is a single planned omnibus test,
    not part of either pairwise contrast family.

    With 21 models and 4 infos, this interaction term has
    (21 - 1) * (4 - 1) = 60 degrees of freedom. That is far too coarse a
    test to localize WHICH model/info combination drives a rejection. The
    report treats it as a design-level diagnostic (does model x info
    interaction exist AT ALL, in aggregate), not as a decision gate the
    way the Tier 1/2/3 tests are. Nothing in this script's contrast
    families depends on its result.

    Parameters
    ----------
    rates : dict of (str, str) -> ndarray
        Per-(model, info) assumed true per-harmonic rates, keyed exactly
        like `load_outcomes`'s return value.
    n_reps : int
        Candidate replicate count per harmonic per condition.
    n_sims : int, default 1000
        Number of Monte Carlo simulations.

    Returns
    -------
    float
        Fraction of simulations, out of `n_sims`, in which the
        likelihood-ratio statistic exceeds the chi-squared critical value
        at `df_extra` = 60 degrees of freedom. A simulation that fails to
        fit (for example, perfect separation at a tiny `n_reps`) counts
        as a non-rejection, so this fraction can slightly understate true
        power at very small `n_reps`.
    """
    import statsmodels.api as sm
    from scipy.stats import chi2 as chi2_dist

    rng = np.random.default_rng(SEED + 1)
    # Design matrices are fixed across sims: one weighted row per
    # (model, info, harmonic) cell, n_reps trials each.
    cells = [(m, i, k) for m in MODELS for i in INFOS for k in range(N_HARMONICS)]

    def design(interaction: bool) -> np.ndarray:
        cols = [np.ones(len(cells))]
        for m in MODELS[1:]:
            cols.append(np.array([c[0] == m for c in cells], float))
        for i in INFOS[1:]:
            cols.append(np.array([c[1] == i for c in cells], float))
        for k in range(1, N_HARMONICS):
            cols.append(np.array([c[2] == k for c in cells], float))
        if interaction:
            for m in MODELS[1:]:
                for i in INFOS[1:]:
                    cols.append(
                        np.array([c[0] == m and c[1] == i for c in cells], float)
                    )
        return np.column_stack(cols)

    x_null, x_full = design(False), design(True)
    df_extra = x_full.shape[1] - x_null.shape[1]
    crit = chi2_dist.isf(ALPHA, df=df_extra)
    cell_rates = np.array([rates[(m, i)][k] for m, i, k in cells])

    rejections = 0
    for _ in range(n_sims):
        succ = rng.binomial(n_reps, cell_rates)
        endog = np.column_stack([succ, n_reps - succ])
        try:
            llf_null = sm.GLM(endog, x_null, family=sm.families.Binomial()).fit().llf
            llf_full = sm.GLM(endog, x_full, family=sm.families.Binomial()).fit().llf
        except Exception:  # perfect separation etc. at tiny n_reps
            continue
        if 2 * (llf_full - llf_null) > crit:
            rejections += 1
    return rejections / n_sims


def build_primary_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build the 210 PRIMARY (Bonferroni, Tier 2) pairwise contrasts.

    The 210 contrasts are 84 within-family LADDER contrasts (does
    accuracy change along a family's rungs, within one info arm) plus 126
    within-model INFO contrasts (does accuracy separate across the 4 info
    arms, within one model).

    Returns
    -------
    list of (str, (str, str), (str, str))
        Each entry is ``(label, key_a, key_b)``. `key_a` and `key_b` are
        ``(model, info)`` condition keys to compare.

        The list holds all 84 ladder contrasts first, then all 126 info
        contrasts. The ladder contrasts group by family, in `FAMILIES`
        order; within each family, they group by info, in `INFOS` order;
        within each info group, rung pairs follow
        `itertools.combinations(rungs, 2)` order. The info contrasts
        group by model, in `MODELS` order; within each model, info pairs
        follow `itertools.combinations(INFOS, 2)` order.

        Ladder labels: ``f"[{family} ladder | {info}] {rung_a} vs {rung_b}"``.
        Info labels: ``f"[{model}] {info_a} vs {info_b}"``.
    """
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    # Ladder contrasts: does accuracy change along a family's parameter-count rungs?
    for family, rungs in FAMILIES.items():
        for info in INFOS:
            for rung_a, rung_b in combinations(rungs, 2):
                label = f"[{family} ladder | {info}] {rung_a} vs {rung_b}"
                contrasts.append((label, (rung_a, info), (rung_b, info)))
    # Info contrasts: does accuracy separate across the 4 info arms, within one model?
    for model in MODELS:
        for info_a, info_b in combinations(INFOS, 2):
            label = f"[{model}] {info_a} vs {info_b}"
            contrasts.append((label, (model, info_a), (model, info_b)))
    return contrasts


def build_secondary_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build the 63 SECONDARY (Benjamini-Hochberg, Tier 3) pairwise contrasts.

    These are cross-family, SIZE-MATCHED rung-vs-rung contrasts on
    `intens` only. For each rung level r in (0, 1, 2) (small/medium/large)
    and each of the `itertools.combinations(FAMILIES, 2)` = C(7, 2) = 21
    family pairs, this function compares `FAMILIES[fam_a][r]` against
    `FAMILIES[fam_b][r]`.

    Returns
    -------
    list of (str, (str, str), (str, str))
        Same shape as `build_primary_contrasts`'s return value, always
        with `info == "intens"` in both condition keys.

        The list groups by rung level r = 0, 1, 2; within each rung
        level, family pairs follow `itertools.combinations(FAMILIES, 2)`
        order (that is, `FAMILIES`' dict-iteration order, its literal
        definition order).

        Labels: ``f"[rung {r} | intens] {model_a} vs {model_b}"``.
    """
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    for r in range(3):
        for fam_a, fam_b in combinations(FAMILIES, 2):
            model_a, model_b = FAMILIES[fam_a][r], FAMILIES[fam_b][r]
            label = f"[rung {r} | intens] {model_a} vs {model_b}"
            contrasts.append((label, (model_a, "intens"), (model_b, "intens")))
    return contrasts


# A "sizing result" is (label, key_a, key_b, needed, needed_pooled): the
# contrast tuple plus its `replicates_needed` output for the assumed
# per-harmonic-shrunk rates and, as a sensitivity check, the pure
# condition-mean ("pooled") rates. Both tiers' tables share this shape.
_SizingResult = tuple[
    str, tuple[str, str], tuple[str, str], dict[float, int | None], dict[float, int | None]
]


def _compute_sizing_results(
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]],
    rates: dict[tuple[str, str], np.ndarray],
    pooled: dict[tuple[str, str], np.ndarray],
    alpha: float,
) -> list[_SizingResult]:
    """Run `replicates_needed` for every contrast, at both rate assumptions.

    # Design: this step is split out from `main`'s printing loop. The
    # archived script computed and printed each contrast's row in the
    # same loop iteration. This study's report layout needs the PRIMARY
    # tier's results TWICE, before either table prints. It computes them
    # once for the recommended R (`main`'s item 6, needed as early as
    # item 3's omnibus-power report), and again to render the table
    # itself (item 4). So the compute step must be a reusable,
    # side-effect-free pass over the contrast list, not an interleaved
    # compute-and-print loop.

    Parameters
    ----------
    contrasts : list of (str, (str, str), (str, str))
        A tier's contrast list, as returned by `build_primary_contrasts` or
        `build_secondary_contrasts`.
    rates, pooled : dict of (str, str) -> ndarray
        Per-condition assumed true per-harmonic rates: `rates` is the
        shrunk-toward-mean assumption used for the headline R(80%)/R(90%)
        columns, `pooled` is the condition-mean-only sensitivity check.
    alpha : float
        This tier's per-test significance threshold (ALPHA_PRIMARY or
        ALPHA_SECONDARY), passed to `replicates_needed` for both the
        `rates` and `pooled` runs.

    Returns
    -------
    list of _SizingResult
        One entry per input contrast, in the same order.

    Notes
    -----
    This function re-seeds `np.random.default_rng(SEED)` before each
    contrast, and again before its pooled counterpart. That preserves the
    "same RNG stream per contrast" discipline, so re-running this script
    gives byte-identical output.
    """
    results: list[_SizingResult] = []
    for name, key_a, key_b in contrasts:
        rng = np.random.default_rng(SEED)
        needed, _ = replicates_needed(rates[key_a], rates[key_b], rng, alpha=alpha)
        rng_pooled = np.random.default_rng(SEED)
        needed_pooled, _ = replicates_needed(
            pooled[key_a], pooled[key_b], rng_pooled, alpha=alpha
        )
        results.append((name, key_a, key_b, needed, needed_pooled))
    return results


def _sizing_header(label_w: int) -> str:
    """Build a sizing-table column header, at label column width `label_w`."""
    return (
        f"{'contrast':{label_w}s} {'rates':13s} {'R(80%)':>7s} {'R(90%)':>7s} "
        f"{'R80 pooled':>11s} {'extra runs':>11s}"
    )


def _print_sizing_rows(
    results: list[_SizingResult],
    outcomes: dict[tuple[str, str], np.ndarray],
    label_w: int,
) -> None:
    """Print one row per sizing result, aligned to a shared `label_w`.

    Columns match `_sizing_header`: observed rates; R(80%) and R(90%)
    under the shrunk-rate assumption; R(80%) under the pooled
    (condition-mean) sensitivity check; and the additional quiz-question
    count that R(80%) implies beyond the existing pilot run.
    """
    for name, key_a, key_b, needed, needed_pooled in results:
        r80, r90 = needed[0.80], needed[0.90]
        fmt = lambda r: fmt_r(r, MAX_REPLICATES)
        extra = "n/a" if r80 is None else f"{(r80 - 1) * N_HARMONICS}q"
        obs = f"{outcomes[key_a].mean():.2f} vs {outcomes[key_b].mean():.2f}"
        print(
            f"{name:{label_w}s} {obs:13s} {fmt(r80):>7s} {fmt(r90):>7s} "
            f"{fmt(needed_pooled[0.80]):>11s} {extra:>11s}"
        )


def main() -> None:
    """Run the full family-ladder power analysis and print the report.

    Report layout (see the module docstring's "Contrast tiers" section for
    what each tier means):
      1. Observed accuracy table, grouped by family.
      2. Design banner (the three tiers, their sizes and corrected alphas).
      3. The 7 Tier-1 family omnibus gates' simulated power.
      4. The 210-row PRIMARY (Tier 2) contrast table.
      5. The 63-row SECONDARY (Tier 3) contrast table.
      6. Recommended replicate count R (driven by Tier 2 / PRIMARY only).
      7. Fisher-exact cross-check and TOST equivalence sizing for PRIMARY
         near-tie contrasts.
      8. The model x info-type interaction diagnostic.
    """
    # Drift guards: pre-registered contrast-family sizes must never
    # silently change. A silent change would invalidate the Bonferroni/BH
    # corrections baked into ALPHA_PRIMARY/ALPHA_SECONDARY above. These
    # guards run before touching any pilot data, so a structural
    # regression is caught even on a checkout with no results synced
    # down yet.
    assert MODELS == tuple(rung for rungs in FAMILIES.values() for rung in rungs)
    assert len(build_primary_contrasts()) == N_PRIMARY == 210
    assert len(build_secondary_contrasts()) == N_SECONDARY == 63

    outcomes = load_outcomes()
    rates = {key: shrunk_rates(y) for key, y in outcomes.items()}
    pooled = {key: np.full(N_HARMONICS, y.mean()) for key, y in outcomes.items()}

    # --- 1. Observed accuracy table, grouped by family --------------------
    print(
        f"Observed accuracy (n=9, one question per harmonic k=1..9; "
        f"{len(MODELS)} models x {len(INFOS)} infos):"
    )
    for family, rungs in FAMILIES.items():
        print(f"  {family}:")
        for model in rungs:
            row = "  ".join(
                f"{info}={outcomes[(model, info)].mean():.3f}" for info in INFOS
            )
            print(f"    {model:14s} {row}")
    print()

    # --- 2. Design banner ---------------------------------------------------
    print(
        "Design: three pre-registered contrast tiers over the 7-family x "
        "3-rung (21-model) scaling grid (see module docstring):"
    )
    print(
        f"  Tier 1 (family omnibus gates):  {N_FAMILIES} tests, "
        f"alpha = {ALPHA}/{N_FAMILIES} = {ALPHA_OMNIBUS:.5f} (Bonferroni)"
    )
    print(
        f"  Tier 2 (PRIMARY pairwise):      {N_PRIMARY} tests, "
        f"alpha = {ALPHA}/{N_PRIMARY} = {ALPHA_PRIMARY:.6f} (Bonferroni)"
    )
    print(
        f"  Tier 3 (SECONDARY pairwise):    {N_SECONDARY} tests, "
        f"Benjamini-Hochberg q = {Q_SECONDARY}, sized at the conservative "
        f"rank-1 threshold alpha = {Q_SECONDARY}/{N_SECONDARY} = "
        f"{ALPHA_SECONDARY:.6f} (an UPPER BOUND on the R BH will actually need)"
    )
    print(f"{N_SIMS} sims per point, seed={SEED}.")
    print(
        f"Assumed rates: per-harmonic outcomes shrunk toward condition mean "
        f"(c={SHRINKAGE}); 'pooled' column = sensitivity with condition-mean "
        f"rates only."
    )
    print()

    # PRIMARY results drive the recommended R (item 6) and feed the
    # omnibus-gate report (item 3). Compute them before printing either
    # -- see `_compute_sizing_results`'s "Design" note.
    primary_contrasts = build_primary_contrasts()
    primary_results = _compute_sizing_results(
        primary_contrasts, rates, pooled, ALPHA_PRIMARY
    )
    feasible = [n[0.80] for *_, n, _pooled in primary_results if n[0.80] is not None]
    r_star = max(feasible)
    primary_label_w = max(len(name) for name, *_ in primary_results)

    # --- 3. Tier-1 family omnibus gates -------------------------------------
    print(
        "Tier 1 -- family omnibus gates: generalized CMH test (df=2) of "
        "whether a family's 3 rungs differ at all, stratified by harmonic x "
        f"info (K={N_HARMONICS * len(INFOS)}). alpha = {ALPHA_OMNIBUS:.5f}."
    )
    print(
        "A family's omnibus gate must reject before that family's Tier-2 "
        "ladder contrasts are reported as more than exploratory -- an "
        "ungated ladder contrast risks chasing noise the family-level test "
        "says isn't there."
    )
    for family in FAMILIES:
        power_star = omnibus_power(rates, family, r_star, np.random.default_rng(SEED))
        power_1 = omnibus_power(rates, family, 1, np.random.default_rng(SEED))
        print(
            f"  {family:8s} power(R={r_star}) = {power_star:.3f}   "
            f"power(R=1) = {power_1:.3f}"
        )
    print()

    # --- 4. PRIMARY contrast table ------------------------------------------
    print(f"Tier 2 -- PRIMARY pairwise contrasts ({N_PRIMARY} tests):")
    header = _sizing_header(primary_label_w)
    print(header)
    print("-" * len(header))
    print("-- ladder contrasts (within family, across rungs) --")
    n_ladder = N_FAMILIES * len(INFOS) * len(list(combinations(range(3), 2)))  # 84
    _print_sizing_rows(primary_results[:n_ladder], outcomes, primary_label_w)
    print()
    print("-- info-arm contrasts (within model, across info types) --")
    _print_sizing_rows(primary_results[n_ladder:], outcomes, primary_label_w)
    print()

    # --- 5. SECONDARY contrast table ----------------------------------------
    secondary_contrasts = build_secondary_contrasts()
    secondary_results = _compute_sizing_results(
        secondary_contrasts, rates, pooled, ALPHA_SECONDARY
    )
    secondary_label_w = max(len(name) for name, *_ in secondary_results)
    print(
        f"Tier 3 -- SECONDARY pairwise contrasts ({N_SECONDARY} tests, "
        f"cross-family, size-matched, intens only):"
    )
    header = _sizing_header(secondary_label_w)
    print(header)
    print("-" * len(header))
    _print_sizing_rows(secondary_results, outcomes, secondary_label_w)
    print()

    # --- 6. Recommended R ----------------------------------------------------
    print(
        f"Recommended replicates per condition (max feasible PRIMARY R at "
        f"80%): {r_star}"
    )
    print(
        f"  = {r_star - 1} additional quiz runs ({(r_star - 1) * N_HARMONICS} "
        f"more questions) per condition beyond the existing pilot run."
    )
    print(
        "  (Tier 3 / SECONDARY contrasts are exploratory and do not drive "
        "this recommendation -- see the Tier 3 table above for their own "
        "sizing.)"
    )
    print()

    # --- 7. Fisher cross-check + TOST equivalence (PRIMARY only) -----------
    print(
        f"Cross-check at R={r_star} (pooled two-sided Fisher exact, PRIMARY "
        f"alpha={ALPHA_PRIMARY:.6f}):"
    )
    for name, key_a, key_b, needed, _pooled in primary_results:
        if needed[0.80] is None:
            continue
        rng = np.random.default_rng(SEED)
        p_fisher = fisher_check(rates[key_a], rates[key_b], r_star, rng, alpha=ALPHA_PRIMARY)
        print(f"  {name:{primary_label_w}s} fisher power = {p_fisher:.3f}")

    # Equivalence (TOST) sizing for the near-tie PRIMARY contrasts. This
    # assumes they are TRUE ties, and asks how many replicates show the
    # difference is within +/-delta at 80% power. A "near-tie" is a
    # contrast whose pairwise difference test above needed R > 20 (or was
    # never powered) -- unchanged threshold from the archived script.
    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed, _pooled in primary_results
        if needed[0.80] is None or needed[0.80] > 20
    ]
    print()
    if not near_ties:
        # Design: the archived script's near-tie family was never empty.
        # Its 30 contrasts, over 3 near-identical MoE models, reliably
        # produced some near-ties, so it never guarded this case. With
        # 210 PRIMARY contrasts spanning genuinely different model sizes,
        # "zero near-ties" is a plausible outcome: every contrast could
        # be well-powered within the R<=20 cap. ALPHA divided by an empty
        # family's length would raise ZeroDivisionError, so this guard is
        # a defensive addition. It does not change behavior for any case
        # the archived script actually hit.
        print(
            "No near-tie PRIMARY contrasts (all reached 80% power within "
            "R(80%) <= 20) -- skipping TOST equivalence sizing."
        )
    else:
        deltas = (0.10, 0.15, 0.20)
        # The equivalence tests form their own planned family; Bonferroni-
        # correct the per-one-sided-test alpha across it.
        alpha_eq = ALPHA / len(near_ties)
        print(
            "Equivalence (TOST) sizing for near-tie PRIMARY contrasts, "
            f"assuming a true tie at the contrasts' mean rate (alpha="
            f"{ALPHA}/{len(near_ties)} = {alpha_eq:.4f} per one-sided test, "
            f"Bonferroni over the {len(near_ties)}-test family; 80% power):"
        )
        eq_header = f"{'contrast':{primary_label_w}s} " + " ".join(
            f"{f'R(d={d:.2f})':>10s}" for d in deltas
        )
        print(eq_header)
        print("-" * len(eq_header))
        for name, key_a, key_b in near_ties:
            cells = []
            for delta in deltas:
                rng = np.random.default_rng(SEED)
                r_eq = equivalence_replicates(
                    rates[key_a], rates[key_b], delta, rng, alpha=alpha_eq
                )
                cells.append(f">{MAX_REPLICATES}" if r_eq is None else str(r_eq))
            print(f"{name:{primary_label_w}s} " + " ".join(f"{c:>10s}" for c in cells))

    # --- 8. Model x info-type interaction diagnostic -------------------------
    print()
    p_omni = omnibus_interaction_power(rates, r_star)
    print(
        f"Omnibus model x info-type interaction (logit LR test, harmonic "
        f"fixed effects, alpha={ALPHA}, df=60; design-level diagnostic, not "
        f"a gate) at R={r_star}: power = {p_omni:.3f}"
    )
    p_omni_1 = omnibus_interaction_power(rates, 1)
    print(f"  ... at the current R=1: power = {p_omni_1:.3f}")


if __name__ == "__main__":
    main()
