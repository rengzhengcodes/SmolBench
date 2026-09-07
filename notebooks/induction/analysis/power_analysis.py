"""
Power analysis for the family-ladder SCALING study (notebooks/induction):
periodic induction task, 7 families x 3 parameter-count rungs = 21 models
(`MODELS` / `FAMILIES`), 4 info arms, harmonic-stratified CMH.

Contrast tiers, pre-registered (all-pairs would be 840 tests this study never
asks):
  Tier 1 -- 7 family omnibus gates at ALPHA/7 (`gcmh_reject`, df=2, K=36
      harmonic x info strata); a family's Tier-2 contrasts stay exploratory
      until its own gate rejects.
  Tier 2 -- PRIMARY, N_PRIMARY=210 pairwise contrasts under Bonferroni.
  Tier 3 -- SECONDARY, N_SECONDARY=63 cross-family, size-matched, `intens`-only
      contrasts under Benjamini-Hochberg q=0.05, sized at BH's conservative
      rank-1 threshold q/N (only the most significant test is held to q/m).

One binary outcome per harmonic k=1..9 per condition, from the PILOT run.
Difficulty varies with k, so power scales with REPLICATES per harmonic; adding
harmonics would change task difficulty and blow up lcm(1..n) context length.
Assumed rates shrink each harmonic toward its condition mean (`SHRINKAGE`),
with a pooled (condition-mean) sensitivity pass beside them. Results are
S3-backed (SMOLBENCH_RESULTS_S3), never committed, and locked to BASE_SEED = 0
(PILOT_SEED).

Run:
    .venv/bin/python notebooks/induction/analysis/power_analysis.py
"""

import functools
import sys
from itertools import combinations
from pathlib import Path

# notebooks/ (where _power_common.py lives) is `parents[2]`, __file__-anchored
# so the import works from any cwd (repo convention -- see _power_common.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from scipy.stats import binom, chi2

from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress
from smolbench.evals.study_config import families as _study_families
from smolbench.evals.study_config import roster_keys, tag_for

from _power_common import (
    ALPHA,
    POWER_TARGETS,
    SEED,
    fmt_r,
    results_dir,
)

# ---------------------------------------------------------------------------
# Experiment design: MODELS and FAMILIES are the committed study config
# (smolbench/evals/study_config.toml, the same file
# notebooks/induction/run_study.py's own MODELS reads) rendered into ANALYSIS
# TAGS through study_config.tag_for(), exactly once, here; everything below
# this point is keyed on the short analysis tag rather than the spec key.
# ---------------------------------------------------------------------------
MODELS = tuple(tag_for(key) for key in roster_keys())

FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(tag_for(key) for key in rungs)
    for family, rungs in _study_families().items()
}

# Both derive from the one committed config run_study.py itself reads, so
# drift between them is structurally impossible. `check_design_invariants`
# (near the bottom of this module) still guards that THIS module's own
# MODELS and FAMILIES agree with EACH OTHER, and the two pre-registered
# family sizes the contrast builders below are sized against; it cannot sit
# here because it also calls those builders, defined further down.

INFOS = ("intens", "extens", "noise_intens", "zero")
N_HARMONICS = 9
PILOT_SEED = 0                                          # seed 0 -> rep_0.yaml
# PILOT_SEED (which replicate's YAML to read) and SEED (_power_common's RNG
# seed for this script's OWN Monte Carlo) both equal 0 only because the study
# is locked to BASE_SEED = 0; they are unrelated and may diverge.

RESULTS_DIR = results_dir(__file__, up=1)

# Writer/reader anchor guard: sync_down() writes through the installed
# package's repo_root(); this chain reads through __file__. In a worktree
# those can be different checkouts, so warn (not exit: reading a
# deliberately copied tree is legal).
from smolbench.evals.results_store import repo_root as _installed_repo_root

_writer_results = _installed_repo_root() / "notebooks" / "induction" / "results"
if _writer_results.resolve() != RESULTS_DIR.resolve():
    print(
        f"WARNING: this script reads {RESULTS_DIR}\n"
        f"         but sync_down() writes {_writer_results}\n"
        "         (different checkouts?). A sync from this shell will not "
        "land where this script looks.",
        file=sys.stderr,
    )

# Stratified-CMH simulation parameters. The simulation unit is the replicate
# within a harmonic stratum, never the harmonic count (adding harmonics
# changes the task, not the sample size). N_SIMS is not reduced for the
# larger contrast family (210 + 63): that makes the script slower, not less
# precise. 10_000 sims puts the Monte Carlo SE of a power estimate at
# sqrt(p(1-p)/N) <= 0.005. MAX_REPLICATES is only a search ceiling, far above
# any affordable R; a contrast still unpowered there is reported as censored,
# not sized.
N_SIMS = 10_000
MAX_REPLICATES = 200
# c=1 pulls a one-replicate pilot rate halfway to its condition mean: a
# 0/9-or-9/9 harmonic seen once says little, and unshrunk boundary rates
# degenerate the sizing (zero variance).
SHRINKAGE = 1.0  # c in p_k = (y_k + c * p_bar) / (1 + c)

# ---------------------------------------------------------------------------
# Tier alphas, defined before the functions below so their `alpha=...`
# defaults bind to these values. PRIMARY and SECONDARY need different
# per-test alphas, so `alpha` is an explicit parameter throughout.
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

    Reads ``{model}_{info}/rep_{PILOT_SEED}.yaml`` through ``LocalResultsStore``,
    which owns that layout and reads each file with ``Marks.load``, so a
    ``score:``-shaped line inside a stored trace can never be scraped as a
    phantom mark. Marks serialize in ascending-period order, so position
    recovers the harmonic. Returns ``(model, info) -> length-N_HARMONICS
    array`` (1.0 for a correct mark, 0.0 for score 0 or null). Raises
    ``SystemExit`` if a pilot replicate file is missing.
    """
    outcomes: dict[tuple[str, str], np.ndarray] = {}
    # This is the only reader of the replicate tree in this module; it cannot
    # reuse `paired_analysis.results_store` either, since that module imports
    # this one. Constructed inside the call so a rebound `RESULTS_DIR` is
    # honoured.
    store = LocalResultsStore(RESULTS_DIR)
    for model in MODELS:
        for info in INFOS:
            # tag=model (the local directory key); model=None because
            # LocalResultsStore ignores that field and this script never
            # talks to S3 -- it reads the tree sync_down() produced.
            addr = ReplicateAddress(tag=model, info=info, seed=PILOT_SEED)
            path = store._path(addr)
            if not store.exists(addr):
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
            scores = [m.score for m in store.load_marks(addr).marks]
            if len(scores) != N_HARMONICS:
                # A raise, not an assert: this gate must survive `python -O`,
                # and a short pilot silently misaligns the harmonic axis.
                raise SystemExit(
                    f"Pilot replicate {path} has {len(scores)} marks, "
                    f"expected {N_HARMONICS}; the sync is incomplete or the "
                    "file is truncated."
                )
            outcomes[(model, info)] = np.array(
                [1.0 if s == 1 else 0.0 for s in scores]
            )
    return outcomes


def shrunk_rates(y: np.ndarray, c: float = SHRINKAGE) -> np.ndarray:
    """Per-harmonic rates shrunk toward the condition mean."""
    return (y + c * y.mean()) / (1.0 + c)


def mcnemar_exact_p(b: int | np.ndarray, c: int | np.ndarray) -> float | np.ndarray:
    """Two-sided exact conditional (binomial) McNemar p for discordant counts `b`, `c`.

    ``min(1, 2 * P[Bin(b + c, 1/2) <= min(b, c)])``, 1.0 where ``b + c == 0``
    (no discordant pairs). Broadcasts, so the same implementation serves the
    scalar call sites and the batched simulations.

    Parameters
    ----------
    b : int | np.ndarray
        First discordant count.
    c : int | np.ndarray
        Second discordant count.

    Returns
    -------
    float | np.ndarray
        Exact two-sided conditional p-values.
    """
    nd = b + c
    # `np.maximum(nd, 1)`: numpy evaluates `binom.cdf` over the WHOLE array
    # before `np.where` selects, so flooring the trial count keeps the
    # no-discordance entries a well-defined Bin(1, 1/2) instead of leaning on
    # scipy's zero-trial convention. The nd == 0 answer comes from `np.where`.
    p = 2.0 * binom.cdf(np.minimum(b, c), np.maximum(nd, 1), 0.5)
    # Doubling a one-sided tail exceeds 1 whenever b == c; the 0.0 bound is
    # inert (a CDF is never negative) and kept only so this reads as a range.
    p = np.where(nd == 0, 1.0, np.clip(p, 0.0, 1.0))
    # Scalar in, scalar out: a 0-d array is not JSON-serializable.
    return p[()] if p.ndim == 0 else p


def cmh_stat(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    """The repo's continuity-corrected 2 x 2 x K CMH statistic (chi2, df=1).

    Stratified by harmonic only (K = N_HARMONICS); `gcmh_reject` is a distinct
    statistic (3 categories, harmonic x info strata, no continuity correction).
    `succ_a`/`succ_b` are success counts out of `n` trials per stratum, shape
    (..., K), the same trial count for both conditions; returns one statistic
    per leading batch index.

    Parameters
    ----------
    succ_a : np.ndarray
        Success counts for the first condition, shaped ``(..., K)``.
    succ_b : np.ndarray
        Success counts for the second condition, shaped ``(..., K)``.
    n : int
        Trial count per condition and stratum.

    Returns
    -------
    np.ndarray
        One statistic per leading batch index.
    """
    big_n = 2 * n  # total per stratum
    m1 = succ_a + succ_b  # successes per stratum
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.abs((succ_a - expect).sum(axis=-1)) - 0.5
    num = np.clip(num, 0.0, None) ** 2
    denom = var.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denom > 0, num / denom, 0.0)


def cmh_p(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    """Two-sided chi2 (df=1) p-value for `cmh_stat`."""
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def cmh_reject(
    succ_a: np.ndarray, succ_b: np.ndarray, n_per_stratum: int, alpha: float
) -> np.ndarray:
    """`cmh_stat` rejections at `alpha` -- the Tier-2/3 pairwise test."""
    return cmh_stat(succ_a, succ_b, n_per_stratum) > chi2.isf(alpha, df=1)


def gcmh_reject(succ: np.ndarray, n_per_stratum: int, alpha: float) -> np.ndarray:
    """Vectorized generalized CMH ("general association") test, 3 rungs -- the Tier-1 gate.

    Tests whether a family's 3 rungs differ at all, stratified by
    K = N_HARMONICS * len(INFOS) = 36 harmonic x info strata. Standard
    R-category generalization of the 2x2xK CMH statistic (Agresti, *Categorical
    Data Analysis*, Sec. 7.5): at R=3 nominal rungs and a binary response only
    R-1 = 2 per-stratum residuals are free, so Q = T' Sigma^-1 T ~ chi2(df=2).

    `succ` has shape (n_sims, 3, K); `n_per_stratum` is trials per rung per
    stratum, one scalar applied uniformly to every rung and stratum -- this
    holds n_rj/N_j == 1/3 constant, collapsing the per-stratum covariances
    exactly to Sigma = (sum_j w_j) * C0 with fixed C0, the shortcut the code
    takes; unequal per-rung or per-stratum counts break it.

    Sigma is exactly singular when every stratum has zero cross-rung
    variance, and one singular matrix aborts the whole batched
    ``numpy.linalg.solve``, hence the `LinAlgError` pseudo-inverse fallback:
    Sigma == 0 also forces T == 0, so the fallback's Q = 0 is the correct
    "no evidence against the null," not an artifact.

    Parameters
    ----------
    succ : np.ndarray
        Success counts with shape ``(n_sims, 3, K)``.
    n_per_stratum : int
        Trials per rung per stratum.
    alpha : float
        Test significance threshold.

    Returns
    -------
    np.ndarray
        Whether each simulation rejects.

    Raises
    ------
    ValueError
        If the rung axis is not length 3, or `n_per_stratum` < 1.
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
        # Singular-Sigma fallback: Sigma == 0 forces T == 0, so Q = 0 (see docstring).
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
    """Simulated power of the harmonic-stratified CMH test at `n_reps` per harmonic.

    `rates_a`/`rates_b` are the two conditions' assumed true per-harmonic
    rates. The ALPHA_PRIMARY default is for standalone/REPL use only: the two
    pairwise tiers have different per-test alphas, so `main` always passes
    `alpha`.

    Parameters
    ----------
    rates_a : np.ndarray
        Assumed true per-harmonic rates for the first condition.
    rates_b : np.ndarray
        Assumed true per-harmonic rates for the second condition.
    n_reps : int
        Replicates per harmonic.
    rng : np.random.Generator
        Random-number generator for simulations.
    alpha : float, optional
        Per-test significance threshold.
    n_sims : int, optional
        Number of simulated experiments.

    Returns
    -------
    float
        Estimated CMH rejection fraction.
    """
    succ_a = rng.binomial(n_reps, rates_a, size=(n_sims, rates_a.size))
    succ_b = rng.binomial(n_reps, rates_b, size=(n_sims, rates_b.size))
    return cmh_reject(succ_a, succ_b, n_reps, alpha).mean()


_SizingScan = tuple[dict[float, int | None], dict[int, float]]


@functools.lru_cache(maxsize=None)
def _sizing_scan(rates_a: tuple, rates_b: tuple, alpha: float) -> _SizingScan:
    """`replicates_needed`'s memoized core, keyed on hashable rate tuples."""
    a, b = np.asarray(rates_a), np.asarray(rates_b)
    rng = np.random.default_rng(SEED)
    needed: dict[float, int | None] = {t: None for t in POWER_TARGETS}
    curve: dict[int, float] = {}
    for n_reps in range(1, MAX_REPLICATES + 1):
        power = simulated_power(a, b, n_reps, rng, alpha=alpha)
        curve[n_reps] = power
        for target in POWER_TARGETS:
            if needed[target] is None and power >= target:
                needed[target] = n_reps
        if all(needed[t] is not None for t in POWER_TARGETS):
            break
    return needed, curve


def replicates_needed(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    alpha: float = ALPHA_PRIMARY,
) -> _SizingScan:
    """Find the smallest replicate count R reaching each `POWER_TARGETS` entry.

    Scans R = 1, 2, ... up to `MAX_REPLICATES`, stopping once every target is
    met.

    Memoized on the rate VALUES, not array identity (`_compute_sizing_results`
    builds a new array object per contrast). Each scan seeds its own
    ``np.random.default_rng(SEED)``, so a memo hit and a recomputation agree
    and re-runs stay byte-identical.

    This scan is the expensive part of `main` (`N_SIMS` binomial draws per
    candidate R, per contrast), and the pooled (condition-mean) rate
    assumption admits only ~10 distinct rate vectors across the 273 primary +
    secondary contrasts, so an uncached scan would recompute up to ~27x per
    distinct input for a bit-identical answer.

    Parameters
    ----------
    rates_a : np.ndarray
        Per-harmonic rates for the first condition.
    rates_b : np.ndarray
        Per-harmonic rates for the second condition.
    alpha : float, optional
        Per-test significance threshold.

    Returns
    -------
    _SizingScan
        ``(needed, curve)``: `needed` maps power target -> smallest R reaching it.
        (`None` if no R within `MAX_REPLICATES` does); `curve` maps each scanned R ->
        its simulated power, freshly copied per call so a caller mutating it cannot
        corrupt the memo.

    Raises
    ------
    ValueError
        If `rates_a` and `rates_b` differ in shape.
    """
    if rates_a.shape != rates_b.shape:
        raise ValueError(
            f"rates_a and rates_b must have the same shape, got "
            f"{rates_a.shape} and {rates_b.shape}"
        )
    needed, curve = _sizing_scan(tuple(rates_a), tuple(rates_b), float(alpha))
    return dict(needed), dict(curve)


replicates_needed.cache_info = _sizing_scan.cache_info
replicates_needed.cache_clear = _sizing_scan.cache_clear


def fisher_check(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_PRIMARY,
) -> float:
    """Cross-check power with a pooled (unstratified) two-sided Fisher exact test.

    Memoizes on the discrete success counts, so the scipy call count stays
    small despite `N_SIMS` simulations.

    Parameters
    ----------
    rates_a : np.ndarray
        Per-harmonic rates for the first condition.
    rates_b : np.ndarray
        Per-harmonic rates for the second condition.
    n_reps : int
        Replicates per harmonic.
    rng : np.random.Generator
        Random-number generator for simulations.
    alpha : float, optional
        Test significance threshold.

    Returns
    -------
    float
        The fraction of `N_SIMS` simulations rejecting at `alpha`.
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

    Assumes a true tie: both conditions are simulated at the mean of their
    assumed per-harmonic rates. Equivalence is declared when the
    (1 - 2*alpha) Wald CI for the pooled accuracy difference lies inside
    (-`delta`, +`delta`) -- two one-sided tests at `alpha` each. Pooling is
    deliberate: under exact equality the stratified and pooled risk
    differences coincide.

    Parameters
    ----------
    rates_a : np.ndarray
        Assumed per-harmonic rates for the first condition.
    rates_b : np.ndarray
        Assumed per-harmonic rates for the second condition.
    delta : float
        Equivalence margin.
    rng : np.random.Generator
        Random-number generator for simulations.
    alpha : float, optional
        One-sided test significance threshold.
    n_sims : int, optional
        Number of simulated experiments.

    Returns
    -------
    int | None
        The smallest R in ``range(1, MAX_REPLICATES + 1)`` reaching 80% equivalence.
        power, else `None`.
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
    """Simulated power of `family`'s Tier-1 omnibus gate at `n_reps` replicates.

    Draws Binomial(`n_reps`, rate) counts over the (3, K=36) grid of `family`'s
    rungs x harmonic x info strata, so `n_reps` applies uniformly to every rung
    and stratum, as `gcmh_reject` requires. `rates` is keyed like
    `load_outcomes`'s return value (shrunk-toward-mean); `rng` should be
    freshly seeded by the caller so repeated calls reproduce.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-toward-mean rates keyed like `load_outcomes`'s return value.
    family : str
        Family whose rungs form the omnibus test.
    n_reps : int
        Replicates per rung and stratum.
    rng : np.random.Generator
        Random-number generator for simulations.
    alpha : float, optional
        Test significance threshold.
    n_sims : int, optional
        Number of simulated experiments.

    Returns
    -------
    float
        Estimated omnibus-gate rejection fraction.
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


#: `omnibus_interaction_power`'s default `n_sims`. Two GLM fits per sim and two
#: calls per `main` run made a default of 1,000 the single most expensive
#: thing in this script (~4,000 fits, minutes of wall clock) for a number
#: that is explicitly not a gate. At 200 the Monte Carlo SE of the reported
#: power is at most sqrt(0.25 / 200) = 0.035, finer than the diagnostic is
#: read to.
N_SIMS_OMNIBUS_DIAGNOSTIC = 200


def omnibus_interaction_power(
    rates: dict[tuple[str, str], np.ndarray],
    n_reps: int,
    n_sims: int = N_SIMS_OMNIBUS_DIAGNOSTIC,
) -> float:
    """Power of the model x info-type interaction (logit LR test) at `n_reps` replicates.

    Fits Bernoulli GLMs with harmonic, model, and info fixed effects, with and
    without the model:info interaction, at alpha = ALPHA. The interaction has
    (21-1) * (4-1) = 60 df -- too coarse to localize which model/info
    combination drives a rejection -- so it is a design-level diagnostic, not
    a gate: no contrast family depends on it.

    `n_sims` defaults to `N_SIMS_OMNIBUS_DIAGNOSTIC`, not the study-wide
    `N_SIMS`, since this is a diagnostic rather than a sizing input; pass a
    larger value for a one-off precise read. Fits that fail (perfect separation
    at a tiny `n_reps`) count as non-rejections, so power can be understated there.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Rates keyed by model and info type.
    n_reps : int
        Replicates per cell.
    n_sims : int, optional
        Number of simulated experiments.

    Returns
    -------
    float
        Rejection fraction over `n_sims`.
    """
    import statsmodels.api as sm
    from scipy.stats import chi2 as chi2_dist

    # SEED + 1: a distinct stream from the sizing sims, so adding or removing
    # this diagnostic can never perturb their draws.
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
    """Build the 210 PRIMARY (Tier 2, Bonferroni) contrasts: 84 ladder + 126 info.

    Returns ``(label, key_a, key_b)`` tuples over ``(model, info)`` keys, all
    84 ladder contrasts first (`main` slices on that boundary), then the 126
    info contrasts. Labels, parsed downstream:
    ``"[{family} ladder | {info}] {rung_a} vs {rung_b}"`` and
    ``"[{model}] {info_a} vs {info_b}"``.
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
    """Build the 63 SECONDARY (Tier 3, BH) cross-family, size-matched contrasts.

    For each rung level r in (0, 1, 2) and each of the C(7, 2) = 21 family
    pairs, compares ``FAMILIES[fam_a][r]`` against ``FAMILIES[fam_b][r]``.
    Returns tuples shaped like `build_primary_contrasts`, always
    ``info == "intens"``, grouped by rung level. Labels:
    ``"[rung {r} | intens] {model_a} vs {model_b}"``.
    """
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    for r in range(3):
        for fam_a, fam_b in combinations(FAMILIES, 2):
            model_a, model_b = FAMILIES[fam_a][r], FAMILIES[fam_b][r]
            label = f"[rung {r} | intens] {model_a} vs {model_b}"
            contrasts.append((label, (model_a, "intens"), (model_b, "intens")))
    return contrasts


# A "sizing result" is the contrast tuple plus `replicates_needed` under the
# shrunk-rate assumption and, as a sensitivity check, the condition-mean
# ("pooled") rates. Both tiers' tables share this shape.
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

    `rates` is the shrunk-toward-mean assumption behind the headline
    R(80%)/R(90%); `pooled` is the condition-mean-only sensitivity check;
    `alpha` is the tier's per-test threshold (ALPHA_PRIMARY or
    ALPHA_SECONDARY) for both runs.

    Side-effect-free and separate from printing because `main` derives the
    recommended R from the PRIMARY results before the omnibus section that
    precedes their table.

    Parameters
    ----------
    contrasts : list[tuple[str, tuple[str, str], tuple[str, str]]]
        Contrasts to size, in output order.
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption for the headline sizing results.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean-only sensitivity assumption.
    alpha : float
        Per-test threshold for both sizing runs.

    Returns
    -------
    list[_SizingResult]
        One `_SizingResult` per contrast, input order.
    """
    results: list[_SizingResult] = []
    for name, key_a, key_b in contrasts:
        needed, _ = replicates_needed(rates[key_a], rates[key_b], alpha=alpha)
        needed_pooled, _ = replicates_needed(pooled[key_a], pooled[key_b], alpha=alpha)
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

    Columns match `_sizing_header`: observed rates; R(80%) and R(90%) under the
    shrunk-rate assumption; R(80%) pooled; and the extra quiz questions R(80%)
    implies beyond the pilot run.

    Parameters
    ----------
    results : list[_SizingResult]
        Sizing results to render.
    outcomes : dict[tuple[str, str], np.ndarray]
        Pilot marks for the observed-rate columns.
    label_w : int
        Shared width of the contrast-label column.
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


def check_design_invariants() -> None:
    """Check the hand-written design constants against what the builders emit.

    Four facts of the pre-registered design must never drift apart: the two
    family sizes against their pre-registered literals, `MODELS` against
    `FAMILIES`, `N_PRIMARY` against `build_primary_contrasts`, and
    `N_SECONDARY` against `build_secondary_contrasts`. The two counts are
    what `ALPHA_PRIMARY` and `ALPHA_SECONDARY` divide by, and every
    correction in the study is taken at one of those thresholds, so a count
    that no longer matches its builder produces a well-formed report whose
    every published correction was computed at the wrong threshold. Raises
    ``RuntimeError`` (never ``assert``, which ``python -O`` strips) if any of
    the four disagree.

    Reads the module globals on each call rather than capturing them at
    definition time, so patching a constant and calling again re-checks the
    patched value -- the only way a test can demonstrate the gate fires. Called
    at module scope below so an importer gets the gate whether or not it
    calls `main`.
    """
    # Guard 1 -- the pre-registered family sizes, as literals. 210 and 63 were
    # fixed before the data existed; guards 3/4 below only check the
    # constants against their builders, which a consistent redesign would
    # satisfy silently. Changing either number is a protocol decision that
    # must be made deliberately, never ride along with a refactor.
    if N_PRIMARY != 210 or N_SECONDARY != 63:
        raise RuntimeError(
            f"The pre-registered family sizes have changed: N_PRIMARY is "
            f"{N_PRIMARY} (pre-registered 210) and N_SECONDARY is "
            f"{N_SECONDARY} (pre-registered 63). These were fixed before any "
            f"data was collected, and every PRIMARY and SECONDARY threshold "
            f"this study publishes divides by them. Re-sizing a family is a "
            f"protocol decision, not a refactor: if it is genuinely intended, "
            f"update these literals in check_design_invariants deliberately, "
            f"and re-state the pre-registration alongside the change."
        )

    # Guard 2 -- structure. Both contrast builders walk MODELS and FAMILIES, so
    # a disagreement changes WHICH contrasts the study tests and how many there
    # are; the size guards below are downstream of this one.
    expected_models = tuple(rung for rungs in FAMILIES.values() for rung in rungs)
    if MODELS != expected_models:
        raise RuntimeError(
            f"MODELS disagrees with FAMILIES. MODELS is {MODELS!r}, but the "
            f"concatenation of FAMILIES' rungs in FAMILIES order is "
            f"{expected_models!r}. Both contrast builders walk these two "
            f"structures, so a disagreement changes which contrasts exist and "
            f"how many of them there are -- and those counts are exactly what "
            f"ALPHA_PRIMARY and ALPHA_SECONDARY divide by, so every published "
            f"correction would have been computed at the wrong threshold."
        )

    # Guard 3 -- PRIMARY family size (Bonferroni denominator).
    n_primary = len(build_primary_contrasts())
    if n_primary != N_PRIMARY:
        raise RuntimeError(
            f"build_primary_contrasts() returns {n_primary} contrasts but "
            f"N_PRIMARY is {N_PRIMARY}. ALPHA_PRIMARY was frozen at import as "
            f"ALPHA / N_PRIMARY = {ALPHA_PRIMARY:.6g}, and every PRIMARY "
            f"Bonferroni and Holm decision in this study is taken at that "
            f"threshold, so a mismatch means the family is not the size its "
            f"threshold assumes and every published correction was computed at "
            f"the wrong one."
        )

    # Guard 4 -- SECONDARY family size (BH denominator and rank-1 sizing alpha).
    n_secondary = len(build_secondary_contrasts())
    if n_secondary != N_SECONDARY:
        raise RuntimeError(
            f"build_secondary_contrasts() returns {n_secondary} contrasts but "
            f"N_SECONDARY is {N_SECONDARY}. ALPHA_SECONDARY was frozen at "
            f"import as Q_SECONDARY / N_SECONDARY = {ALPHA_SECONDARY:.6g} (the "
            f"conservative rank-1 BH threshold this tier is sized at), and the "
            f"Benjamini-Hochberg thresholds q * i / m applied downstream use m "
            f"= the family size, so a mismatch means every SECONDARY discovery "
            f"was declared at the wrong threshold."
        )


# Called here, not beside N_PRIMARY: the gate calls the contrast builders, so
# it can only run after their definitions. Runs at import, so other modules
# importing this one get it without ever calling `main`, and before any
# pilot data is touched, so a structural regression is caught even with
# nothing synced down.
check_design_invariants()


def observed_accuracy(
    outcomes: dict[tuple[str, str], np.ndarray]
) -> list[tuple[str, list[tuple[str, list[tuple[str, float]]]]]]:
    """Compute observed per-(family, model, info) accuracy from the pilot marks.

    Parameters
    ----------
    outcomes : dict[tuple[str, str], np.ndarray]
        Keyed like `load_outcomes`'s return value.

    Returns
    -------
    list[tuple[str, list[tuple[str, list[tuple[str, float]]]]]]
        ``[(family, [(model, [(info, mean_accuracy), ...]), ...]), ...]``, in.
        `FAMILIES` and `INFOS` order.
    """
    return [
        (
            family,
            [
                (
                    model,
                    [(info, float(outcomes[(model, info)].mean())) for info in INFOS],
                )
                for model in rungs
            ],
        )
        for family, rungs in FAMILIES.items()
    ]


def render_observed_accuracy(
    data: list[tuple[str, list[tuple[str, list[tuple[str, float]]]]]]
) -> None:
    """Print the observed accuracy table `observed_accuracy` returns."""
    print(
        f"Observed accuracy (n=9, one question per harmonic k=1..9; "
        f"{len(MODELS)} models x {len(INFOS)} infos):"
    )
    for family, rows in data:
        print(f"  {family}:")
        for model, info_means in rows:
            row = "  ".join(f"{info}={mean:.3f}" for info, mean in info_means)
            print(f"    {model:14s} {row}")
    print()


def design_banner() -> dict:
    """Gather the Tier 1/2/3 design constants the report's banner states.

    Returns a dict of the module constants the banner reports (n_families,
    alpha_omnibus, n_primary, alpha_primary, n_secondary, q_secondary,
    alpha_secondary, n_sims, seed, shrinkage), gathered here so
    `render_design_banner` reads only its argument, never module globals.
    """
    return dict(
        n_families=N_FAMILIES,
        alpha_omnibus=ALPHA_OMNIBUS,
        n_primary=N_PRIMARY,
        alpha_primary=ALPHA_PRIMARY,
        n_secondary=N_SECONDARY,
        q_secondary=Q_SECONDARY,
        alpha_secondary=ALPHA_SECONDARY,
        n_sims=N_SIMS,
        seed=SEED,
        shrinkage=SHRINKAGE,
    )


def render_design_banner(data: dict) -> None:
    """Print the design banner `design_banner` returns."""
    print(
        "Design: three pre-registered contrast tiers over the 7-family x "
        "3-rung (21-model) scaling grid (see module docstring):"
    )
    print(
        f"  Tier 1 (family omnibus gates):  {data['n_families']} tests, "
        f"alpha = {ALPHA}/{data['n_families']} = {data['alpha_omnibus']:.5f} "
        f"(Bonferroni)"
    )
    print(
        f"  Tier 2 (PRIMARY pairwise):      {data['n_primary']} tests, "
        f"alpha = {ALPHA}/{data['n_primary']} = {data['alpha_primary']:.6f} "
        f"(Bonferroni)"
    )
    print(
        f"  Tier 3 (SECONDARY pairwise):    {data['n_secondary']} tests, "
        f"Benjamini-Hochberg q = {data['q_secondary']}, sized at the "
        f"conservative rank-1 threshold alpha = {data['q_secondary']}/"
        f"{data['n_secondary']} = {data['alpha_secondary']:.6f} (an UPPER "
        f"BOUND on the R BH will actually need)"
    )
    print(f"{data['n_sims']} sims per point, seed={data['seed']}.")
    print(
        f"Assumed rates: per-harmonic outcomes shrunk toward condition mean "
        f"(c={data['shrinkage']}); 'pooled' column = sensitivity with "
        f"condition-mean rates only."
    )
    print()


def primary_contrasts_table(
    rates: dict[tuple[str, str], np.ndarray], pooled: dict[tuple[str, str], np.ndarray]
) -> dict:
    """Build the Tier 2 PRIMARY sizing table, and the figures later sections need.

    Runs `_compute_sizing_results` over `build_primary_contrasts`'s 210-test
    family (`rates` shrunk-toward-mean, `pooled` the sensitivity assumption).
    Also derives `r_star` (max R(80%) over the powered contrasts only,
    deliberately not the search ceiling, so a handful of unpowered contrasts
    cannot drag the recommendation to MAX_REPLICATES) and `n_censored`
    (PRIMARY contrasts whose R(80%) was never reached), read from this same
    sizing pass by both the Tier-1 omnibus-gate section and the recommended-R
    section rather than recomputed there.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption for PRIMARY sizing.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean-only sensitivity assumption.

    Returns
    -------
    dict
        With keys `results`, `r_star`, `n_censored`, `label_w` (max.
        contrast-name length, for column alignment), and `n_ladder` (row index
        separating the 84 ladder contrasts from the 126 info-arm contrasts).

    Raises
    ------
    SystemExit
        If no PRIMARY contrast reaches 80% power within MAX_REPLICATES: the.
        pilot cannot size R at all, so nothing downstream can be recommended.
    """
    contrasts = build_primary_contrasts()
    results = _compute_sizing_results(contrasts, rates, pooled, ALPHA_PRIMARY)
    feasible = [n[0.80] for *_, n, _pooled in results if n[0.80] is not None]
    if not feasible:
        raise SystemExit(
            "No PRIMARY contrast reaches 80% power within "
            f"R <= {MAX_REPLICATES}; the pilot cannot size R at all."
        )
    r_star = max(feasible)
    n_censored = len(results) - len(feasible)
    label_w = max(len(name) for name, *_ in results)
    n_ladder = N_FAMILIES * len(INFOS) * len(list(combinations(range(3), 2)))  # 84
    return dict(
        results=results, r_star=r_star, n_censored=n_censored, label_w=label_w,
        n_ladder=n_ladder,
    )


def render_primary_contrasts_table(
    data: dict, outcomes: dict[tuple[str, str], np.ndarray]
) -> None:
    """Print the PRIMARY sizing table `primary_contrasts_table` returns."""
    print(f"Tier 2 -- PRIMARY pairwise contrasts ({N_PRIMARY} tests):")
    header = _sizing_header(data["label_w"])
    print(header)
    print("-" * len(header))
    print("-- ladder contrasts (within family, across rungs) --")
    _print_sizing_rows(data["results"][:data["n_ladder"]], outcomes, data["label_w"])
    print()
    print("-- info-arm contrasts (within model, across info types) --")
    _print_sizing_rows(data["results"][data["n_ladder"]:], outcomes, data["label_w"])
    print()


def omnibus_gates(
    rates: dict[tuple[str, str], np.ndarray], r_star: int
) -> list[tuple[str, float, float]]:
    """Compute Tier 1 family omnibus-gate power at R=`r_star` and at R=1.

    `rates` is shrunk-toward-mean, keyed like `load_outcomes`'s return value;
    `r_star` is the recommended replicate count.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates keyed by model and information type.
    r_star : int
        Recommended replicate count.

    Returns
    -------
    list[tuple[str, float, float]]
        ``(family, power_at_r_star, power_at_1)`` per family, in `FAMILIES`.
        order.
    """
    rows = []
    for family in FAMILIES:
        power_star = omnibus_power(rates, family, r_star, np.random.default_rng(SEED))
        power_1 = omnibus_power(rates, family, 1, np.random.default_rng(SEED))
        rows.append((family, power_star, power_1))
    return rows


def render_omnibus_gates(rows: list[tuple[str, float, float]], r_star: int) -> None:
    """Print the Tier 1 omnibus-gate section `omnibus_gates` returns."""
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
    for family, power_star, power_1 in rows:
        print(
            f"  {family:8s} power(R={r_star}) = {power_star:.3f}   "
            f"power(R=1) = {power_1:.3f}"
        )
    print()


def secondary_contrasts_table(
    rates: dict[tuple[str, str], np.ndarray], pooled: dict[tuple[str, str], np.ndarray]
) -> dict:
    """Build the Tier 3 SECONDARY sizing table.

    `rates` is shrunk-toward-mean, `pooled` the condition-mean-only
    sensitivity assumption, both keyed like `load_outcomes`'s return value.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption for SECONDARY sizing.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean-only sensitivity assumption.

    Returns
    -------
    dict
        With ``results`` (`build_secondary_contrasts` order) and ``label_w``.
        (max contrast-name length, for alignment).
    """
    contrasts = build_secondary_contrasts()
    results = _compute_sizing_results(contrasts, rates, pooled, ALPHA_SECONDARY)
    label_w = max(len(name) for name, *_ in results)
    return dict(results=results, label_w=label_w)


def render_secondary_contrasts_table(
    data: dict, outcomes: dict[tuple[str, str], np.ndarray]
) -> None:
    """Print the SECONDARY sizing table `secondary_contrasts_table` returns."""
    print(
        f"Tier 3 -- SECONDARY pairwise contrasts ({N_SECONDARY} tests, "
        f"cross-family, size-matched, intens only):"
    )
    header = _sizing_header(data["label_w"])
    print(header)
    print("-" * len(header))
    _print_sizing_rows(data["results"], outcomes, data["label_w"])
    print()


def recommended_replicates(r_star: int, n_censored: int) -> dict:
    """Derive the recommended-R section's figures from PRIMARY sizing.

    `r_star` and `n_censored` come from `primary_contrasts_table` and are not
    recomputed here.

    Parameters
    ----------
    r_star : int
        Recommended replicate count from PRIMARY sizing.
    n_censored : int
        Number of PRIMARY contrasts that never reached 80% power.

    Returns
    -------
    dict
        With ``r_star``, ``n_censored``, ``extra_runs`` (additional quiz runs.
        beyond the pilot's single run), and ``extra_questions``
        (``extra_runs * N_HARMONICS``).
    """
    return dict(
        r_star=r_star,
        n_censored=n_censored,
        extra_runs=r_star - 1,
        extra_questions=(r_star - 1) * N_HARMONICS,
    )


def render_recommended_replicates(data: dict) -> None:
    """Print the recommended-R section `recommended_replicates` returns."""
    print(
        f"Recommended replicates per condition (max feasible PRIMARY R at "
        f"80%): {data['r_star']}"
    )
    print(
        f"  = {data['extra_runs']} additional quiz runs "
        f"({data['extra_questions']} more questions) per condition beyond "
        f"the existing pilot run."
    )
    print(
        f"  ({data['n_censored']} PRIMARY contrasts never reached 80% within "
        f"R <= {MAX_REPLICATES} and are excluded from this max.)"
    )
    print(
        "  The study itself collects R=30 (user-locked in run_study.py, "
        "uniform across checkpoints); this prospective figure is the sizing "
        "check that decision was made against, not a superseding value."
    )
    print(
        "  (Tier 3 / SECONDARY contrasts are exploratory and do not drive "
        "this recommendation -- see the Tier 3 table above for their own "
        "sizing.)"
    )
    print()


def equivalence_checks(
    primary_results: list[_SizingResult],
    rates: dict[tuple[str, str], np.ndarray],
    r_star: int,
) -> dict:
    """Compute the Fisher cross-check and TOST equivalence sizing at R=`r_star`.

    `primary_results` is `primary_contrasts_table`'s ``results`` (input
    order); `rates` is shrunk-toward-mean, keyed like `load_outcomes`'s
    return value.

    Parameters
    ----------
    primary_results : list[_SizingResult]
        PRIMARY sizing results in input order.
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates keyed by model and information type.
    r_star : int
        Replicate count for the Fisher cross-check.

    Returns
    -------
    dict
        With:.
        fisher : list of (name, fisher_power), for every PRIMARY contrast whose
            R(80%) was reached, input order.
        near_ties : list of (name, key_a, key_b), for contrasts whose R(80%) was
            censored or exceeded 20 -- this report's "near-tie" grouping cut.
        deltas : the TOST equivalence margins probed.
        alpha_eq : Bonferroni-corrected one-sided alpha over `near_ties`, or
            `None` when `near_ties` is empty (dividing by zero near-ties would
            raise).
        table : list of (name, [r_eq for each delta]), `near_ties` order; an
            entry is `None` where equivalence was never reached within
            MAX_REPLICATES. Empty when `near_ties` is empty.
    """
    fisher = []
    for name, key_a, key_b, needed, _pooled in primary_results:
        if needed[0.80] is None:
            continue
        rng = np.random.default_rng(SEED)
        p_fisher = fisher_check(
            rates[key_a], rates[key_b], r_star, rng, alpha=ALPHA_PRIMARY
        )
        fisher.append((name, p_fisher))

    # Equivalence (TOST) sizing for near-tie PRIMARY contrasts: assume a true
    # tie and ask how many replicates show the difference within +/-delta at
    # 80% power. "Near-tie" = the difference test above needed R > 20 or was
    # never powered; 20 carries over from the archived sibling sizing script
    # (notebooks/ARCHIVE.md) for comparability, a report-grouping cut, not an
    # inferential threshold.
    # Known limitation: the Wald TOST degenerates at saturated rates -- a
    # contrast whose shrunk rates are exactly 1.0 in both arms simulates a
    # zero-width CI and reports R=1 for every delta. Read ceiling-pair rows
    # as "indistinguishable at ceiling", not as a sized equivalence claim.
    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed, _pooled in primary_results
        if needed[0.80] is None or needed[0.80] > 20
    ]
    deltas = (0.10, 0.15, 0.20)
    if not near_ties:
        # With 210 contrasts over genuinely different model sizes, "zero
        # near-ties" is plausible, and ALPHA / len(near_ties) would then raise
        # ZeroDivisionError.
        return dict(fisher=fisher, near_ties=near_ties, deltas=deltas, alpha_eq=None,
                    table=[])

    # The equivalence tests form their own planned family; Bonferroni-correct
    # the per-one-sided-test alpha across it.
    alpha_eq = ALPHA / len(near_ties)
    table = []
    for name, key_a, key_b in near_ties:
        cells = []
        for delta in deltas:
            rng = np.random.default_rng(SEED)
            r_eq = equivalence_replicates(
                rates[key_a], rates[key_b], delta, rng, alpha=alpha_eq
            )
            cells.append(r_eq)
        table.append((name, cells))
    return dict(fisher=fisher, near_ties=near_ties, deltas=deltas, alpha_eq=alpha_eq,
                table=table)


def render_equivalence_checks(data: dict, label_w: int, r_star: int) -> None:
    """Print the Fisher cross-check and TOST sections `equivalence_checks` returns."""
    print(
        f"Cross-check at R={r_star} (pooled two-sided Fisher exact, PRIMARY "
        f"alpha={ALPHA_PRIMARY:.6f}):"
    )
    for name, p_fisher in data["fisher"]:
        print(f"  {name:{label_w}s} fisher power = {p_fisher:.3f}")

    near_ties = data["near_ties"]
    print()
    if not near_ties:
        print(
            "No near-tie PRIMARY contrasts (all reached 80% power within "
            "R(80%) <= 20) -- skipping TOST equivalence sizing."
        )
        return
    deltas = data["deltas"]
    alpha_eq = data["alpha_eq"]
    print(
        "Equivalence (TOST) sizing for near-tie PRIMARY contrasts, "
        f"assuming a true tie at the contrasts' mean rate (alpha="
        f"{ALPHA}/{len(near_ties)} = {alpha_eq:.4f} per one-sided test, "
        f"Bonferroni over the {len(near_ties)}-test family; 80% power):"
    )
    eq_header = f"{'contrast':{label_w}s} " + " ".join(
        f"{f'R(d={d:.2f})':>10s}" for d in deltas
    )
    print(eq_header)
    print("-" * len(eq_header))
    for name, cells in data["table"]:
        formatted = [f">{MAX_REPLICATES}" if c is None else str(c) for c in cells]
        print(f"{name:{label_w}s} " + " ".join(f"{c:>10s}" for c in formatted))


def interaction_diagnostic(
    rates: dict[tuple[str, str], np.ndarray], r_star: int
) -> tuple[float, float]:
    """Compute the model x info-type interaction diagnostic's power at `r_star` and R=1.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-toward-mean, keyed like `load_outcomes`'s return value.
    r_star : int
        Recommended replicate count.

    Returns
    -------
    tuple[float, float]
        ``(power_at_r_star, power_at_1)``.
    """
    return omnibus_interaction_power(rates, r_star), omnibus_interaction_power(rates, 1)


def render_interaction_diagnostic(data: tuple[float, float], r_star: int) -> None:
    """Print the interaction diagnostic `interaction_diagnostic` returns."""
    p_omni, p_omni_1 = data
    print()
    print(
        f"Omnibus model x info-type interaction (logit LR test, harmonic "
        f"fixed effects, alpha={ALPHA}, df=60; design-level diagnostic, not "
        f"a gate) at R={r_star}: power = {p_omni:.3f}"
    )
    print(f"  ... at the current R=1: power = {p_omni_1:.3f}")


def main() -> None:
    """Run the full family-ladder power analysis and print the report.

    Computes each of the eight numbered sections via its data function, then
    prints it through its ``render_*`` twin, in the sections' original order.
    Sections 3 and 4 both read PRIMARY sizing (`primary_contrasts_table`), so
    it is computed once and passed to both -- see that function's docstring.
    """
    # check_design_invariants already ran at import; nothing to re-check here.
    outcomes = load_outcomes()
    rates = {key: shrunk_rates(y) for key, y in outcomes.items()}
    pooled = {key: np.full(N_HARMONICS, y.mean()) for key, y in outcomes.items()}

    render_observed_accuracy(observed_accuracy(outcomes))  # 1
    render_design_banner(design_banner())  # 2

    # PRIMARY results drive the recommended R (item 6) and feed the
    # omnibus-gate report (item 3), so compute them once, before either.
    primary = primary_contrasts_table(rates, pooled)
    r_star, n_censored = primary["r_star"], primary["n_censored"]

    render_omnibus_gates(omnibus_gates(rates, r_star), r_star)  # 3
    render_primary_contrasts_table(primary, outcomes)  # 4

    secondary = secondary_contrasts_table(rates, pooled)
    render_secondary_contrasts_table(secondary, outcomes)  # 5

    render_recommended_replicates(recommended_replicates(r_star, n_censored))  # 6

    render_equivalence_checks(
        equivalence_checks(primary["results"], rates, r_star),
        primary["label_w"], r_star,
    )  # 7

    render_interaction_diagnostic(interaction_diagnostic(rates, r_star), r_star)  # 8


if __name__ == "__main__":
    main()
