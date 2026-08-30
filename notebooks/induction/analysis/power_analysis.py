"""
Power analysis for the family-ladder SCALING study (notebooks/induction):
periodic induction task, 7 families x 3 parameter-count rungs = 21 models
(`MODELS` / `FAMILIES`), 4 info arms, harmonic-stratified CMH.

Contrast tiers
--------------
Pre-registered; all-pairs would be 840 tests this study never asks.
  Tier 1 -- 7 family omnibus gates at ALPHA/7 (`gcmh_reject`, df=2, K=36
      harmonic x info strata); a family's Tier-2 contrasts stay exploratory
      until its own gate rejects.
  Tier 2 -- PRIMARY, N_PRIMARY=210 pairwise contrasts under Bonferroni.
  Tier 3 -- SECONDARY, N_SECONDARY=63 cross-family, size-matched, `intens`-only
      contrasts under Benjamini-Hochberg q=0.05, sized at BH's rank-1 threshold
      q/N -- an UPPER BOUND on the R BH needs, since only the most significant
      test is held to q/m.

Notes
-----
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

import re
import sys
from itertools import combinations
from pathlib import Path

# notebooks/ (where _power_common.py lives) is `parents[2]`, __file__-anchored
# so the import works from any cwd (repo convention -- see _power_common.py).
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
# Experiment design; MODELS and FAMILIES are given verbatim by the study spec.
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

# Drift guard: MODELS (iteration order) and FAMILIES (ladder/omnibus structure)
# are hand-maintained and must never disagree about which 21 models exist or in
# what order. At MODULE scope so importers get the guard too; `main` re-asserts
# it, per the spec's "assert BOTH" requirement.
assert MODELS == tuple(rung for rungs in FAMILIES.values() for rung in rungs), (
    "MODELS must equal the concatenation of FAMILIES' rungs, in FAMILIES order"
)

INFOS = ("intens", "extens", "noise_intens", "zero")
N_HARMONICS = 9
PILOT_SEED = 0                                          # seed 0 -> rep_0.yaml
# PILOT_SEED (which replicate's YAML to read) and SEED (_power_common's RNG
# seed for this script's OWN Monte Carlo) both equal 0 only because the study
# is locked to BASE_SEED = 0; they are unrelated and may diverge.

RESULTS_DIR = results_dir(__file__, up=1)

# Stratified-CMH simulation parameters (not chromatic's quiz-level design).
# The larger contrast family (210 + 63) makes the script slower, not less
# precise, so N_SIMS is NOT reduced to compensate (see the module docstring's
# "Contrast tiers" section).
N_SIMS = 10_000
MAX_REPLICATES = 200
SHRINKAGE = 1.0  # c in p_k = (y_k + c * p_bar) / (1 + c)

# ---------------------------------------------------------------------------
# Tier alphas, defined before the functions below so their `alpha=...` defaults
# bind to these values. PRIMARY and SECONDARY need different per-test alphas, so
# `alpha` is an explicit parameter throughout (see `simulated_power`'s Notes).
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

    Regexes the per-mark ``score:`` lines of
    ``{model}_{info}/rep_{PILOT_SEED}.yaml``: those YAMLs carry !!python/object
    tags, so a safe load is impossible. Marks are serialized in ascending-period
    order, so position recovers the harmonic.

    Returns
    -------
    dict
        ``(model, info)`` -> length-`N_HARMONICS` array, index k-1 for harmonic
        k: 1.0 for a correct mark, 0.0 for score 0 or null (invalid).

    Raises
    ------
    SystemExit
        If a pilot replicate file is missing.
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
    """Vectorized CMH test (2 x 2 x K, continuity-corrected) -- the Tier-2/3 pairwise test.

    Stratified by harmonic only (K = N_HARMONICS); `gcmh_reject` is a distinct
    statistic (3 categories, harmonic x info strata, no continuity correction).

    Parameters
    ----------
    succ_a, succ_b : ndarray, shape (n_sims, K)
        Success counts out of `n_per_stratum` trials per stratum -- the same
        trial count for both conditions.

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
    """Vectorized generalized CMH ("general association") test, 3 rungs -- the Tier-1 gate.

    Tests whether a family's 3 rungs differ AT ALL, stratified by
    K = N_HARMONICS * len(INFOS) = 36 harmonic x info strata. Standard
    R-category generalization of the 2x2xK CMH statistic (Agresti, *Categorical
    Data Analysis*, Sec. 7.5; SAS PROC FREQ "general association"): at R=3
    nominal rungs and a binary response only R-1 = 2 per-stratum residuals are
    free, so Q = T' Sigma^-1 T ~ chi2(df=2).

    Parameters
    ----------
    succ : ndarray, shape (n_sims, 3, K)
        Success counts per (simulation, rung in ladder order, stratum).
    n_per_stratum : int
        Trials per rung per stratum: ONE scalar applied uniformly to every rung
        and stratum (see Notes). ALPHA_OMNIBUS is this study's `alpha`.

    Returns
    -------
    ndarray of bool, shape (n_sims,)
        True where the statistic exceeds ``chi2.isf(alpha, df=2)``.

    Raises
    ------
    ValueError
        If the rung axis is not length 3, or `n_per_stratum` < 1.

    Notes
    -----
    Uniform `n_per_stratum` holds n_rj/N_j == 1/3 constant, collapsing the
    per-stratum covariances EXACTLY to Sigma = (sum_j w_j) * C0, with fixed
    C0 = [[2/9, -1/9], [-1/9, 2/9]] and w_j = M_j (N_j - M_j) / (N_j - 1) --
    the shortcut the code takes; unequal per-rung or per-stratum counts break
    it.

    Sigma is exactly singular when every stratum has zero cross-rung variance,
    and one singular matrix aborts the WHOLE batched ``numpy.linalg.solve``,
    hence the `LinAlgError` pseudo-inverse fallback. Sigma == 0 also forces
    T == 0, so the fallback's Q = 0 is the correct "no evidence against the
    null", not an artifact.
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
        # Singular-Sigma fallback: see this function's Notes section.
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

    Parameters
    ----------
    rates_a, rates_b : ndarray
        The two conditions' assumed true per-harmonic rates.

    Notes
    -----
    The ALPHA_PRIMARY default is for standalone/REPL use only: the two pairwise
    tiers have different per-test alphas, so `main` always passes `alpha`.
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
    """Find the smallest replicate count R reaching each `POWER_TARGETS` entry.

    Scans R = 1, 2, ... up to `MAX_REPLICATES`, stopping once every target is met.

    Returns
    -------
    needed : dict of float -> int or None
        Power target -> smallest R reaching it, `None` if no R within
        `MAX_REPLICATES` does.
    curve : dict of int -> float
        Each scanned R -> its simulated power.
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

    Memoizes on the discrete success counts, so the scipy call count stays
    small despite `N_SIMS` simulations.

    Returns
    -------
    float
        Fraction of `N_SIMS` simulations rejecting at `alpha`.
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

    Assumes a TRUE tie: both conditions are simulated at the mean of their
    assumed per-harmonic rates. Equivalence is declared when the (1 - 2*alpha)
    Wald CI for the pooled accuracy difference lies inside
    (-`delta`, +`delta`) -- two one-sided tests at `alpha` each. Pooling is
    deliberate: under exact equality the stratified and pooled risk differences
    coincide.

    Returns
    -------
    int or None
        Smallest R in ``range(1, MAX_REPLICATES + 1)`` reaching 80% equivalence
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
    and stratum, as `gcmh_reject` requires.

    Parameters
    ----------
    rates : dict
        Keyed like `load_outcomes`'s return value; the shrunk-toward-mean rates.
    rng : numpy.random.Generator
        Freshly seeded by the caller, so repeated calls reproduce.
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
    """Power of the model x info-type interaction (logit LR test) at `n_reps` replicates.

    Fits Bernoulli GLMs with harmonic, model, and info fixed effects, with and
    without the model:info interaction, at alpha = ALPHA. The interaction has
    (21-1) * (4-1) = 60 df -- too coarse to localize WHICH model/info
    combination drives a rejection -- so it is a design-level diagnostic, not a
    gate: no contrast family depends on it.

    Returns
    -------
    float
        Rejection fraction over `n_sims`. Fits that fail (perfect separation at
        a tiny `n_reps`) count as non-rejections, so power can be understated
        there.
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
    """Build the 210 PRIMARY (Tier 2, Bonferroni) contrasts: 84 ladder + 126 info.

    Returns
    -------
    list of (str, tuple, tuple)
        ``(label, key_a, key_b)`` over ``(model, info)`` keys, all 84 ladder
        contrasts first (`main` slices on that boundary), then the 126 info
        contrasts. Labels, parsed downstream:
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

    Returns
    -------
    list of (str, tuple, tuple)
        As `build_primary_contrasts`, always ``info == "intens"``, grouped by
        rung level. Labels: ``"[rung {r} | intens] {model_a} vs {model_b}"``.
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

    Parameters
    ----------
    rates : dict
        Shrunk-toward-mean assumption, behind the headline R(80%)/R(90%).
    pooled : dict
        Condition-mean-only rates: the sensitivity check.
    alpha : float
        The tier's per-test threshold (ALPHA_PRIMARY or ALPHA_SECONDARY), for
        both runs.

    Returns
    -------
    list of _SizingResult
        One per contrast, in input order.

    Notes
    -----
    Side-effect-free and separate from printing because `main` derives the
    recommended R from the PRIMARY results before the omnibus section that
    precedes their table. Re-seeds ``np.random.default_rng(SEED)`` before each
    contrast and again before its pooled counterpart, so re-runs are
    byte-identical.
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

    Columns match `_sizing_header`: observed rates; R(80%) and R(90%) under the
    shrunk-rate assumption; R(80%) pooled; and the extra quiz questions R(80%)
    implies beyond the pilot run.
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

    Prints the eight numbered sections marked in the body; the recommended R
    comes from Tier 2 alone.
    """
    # Drift guards: a silent change to the pre-registered family sizes would
    # invalidate the Bonferroni/BH corrections baked into ALPHA_PRIMARY /
    # ALPHA_SECONDARY. They run before any pilot data is touched, so a
    # structural regression is caught even with no results synced down.
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
    # omnibus-gate report (item 3), so compute them before printing either
    # -- see `_compute_sizing_results`'s Notes section.
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

    # Equivalence (TOST) sizing for near-tie PRIMARY contrasts: assume a TRUE
    # tie and ask how many replicates show the difference within +/-delta at
    # 80% power. "Near-tie" = the difference test above needed R > 20 or was
    # never powered (threshold unchanged from the archived script).
    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed, _pooled in primary_results
        if needed[0.80] is None or needed[0.80] > 20
    ]
    print()
    if not near_ties:
        # With 210 contrasts over genuinely different model sizes, "zero
        # near-ties" is plausible, and ALPHA / len(near_ties) would then raise
        # ZeroDivisionError.
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
