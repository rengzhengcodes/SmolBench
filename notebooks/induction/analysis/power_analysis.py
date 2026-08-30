"""
Power analysis for the family-ladder SCALING study (notebooks/induction):
periodic induction task, 7 families x 3 parameter-count rungs = 21 models
(`MODELS` / `FAMILIES`), 4 info arms, harmonic-stratified CMH.

Three PRE-REGISTERED contrast tiers (all-pairs would be 840 model-vs-model
tests, nearly all of them questions this study never asks):
  Tier 1 -- 7 family omnibus gates at ALPHA/7: do a family's 3 rungs differ AT
      ALL (`gcmh_reject`, df=2, stratified by harmonic x info, K=36)? Its
      Tier-2 ladder contrasts stay exploratory until that gate rejects.
  Tier 2 -- PRIMARY, N_PRIMARY=210 Bonferroni: 84 within-family ladder + 126
      within-model info contrasts (`build_primary_contrasts`).
  Tier 3 -- SECONDARY, N_SECONDARY=63 under Benjamini-Hochberg q=0.05:
      cross-family, size-matched rungs, `intens` only
      (`build_secondary_contrasts`), sized at BH's rank-1 threshold q/N -- an
      UPPER BOUND on the R BH needs, since only the most significant test is
      held to q/m.

One binary outcome per harmonic k=1..9 per condition, from the PILOT run, in
ascending-period (hence ascending-harmonic) order. Difficulty varies
systematically with k, so the data are a stratified binomial and power scales
with REPLICATES per harmonic -- adding harmonics instead would change task
difficulty and blow up lcm(1..n) context length. Assumed rates shrink each y_k
toward the condition mean: p_k = (y_k + c*p_bar)/(1+c), c = SHRINKAGE = 1, with
a pooled (condition-mean) sensitivity pass alongside.

Results are S3-backed (SMOLBENCH_RESULTS_S3), never committed, and locked to
BASE_SEED = 0 (PILOT_SEED); `load_outcomes` raises SystemExit naming the
missing path and pointing at ``InductionExperiment.harness.sync_down()``.

Run (plain `uv run` would sync the project and strip the notebook extras):
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

    Reads ``{model}_{info}/rep_{PILOT_SEED}.yaml`` and regexes its per-mark
    ``score:`` lines: the result YAMLs carry !!python/object tags, so a safe
    load is impossible. Marks are serialized in ascending-period order, so
    position recovers the harmonic. Returns each ``(model, info)`` condition's
    length-`N_HARMONICS` array, index k-1 for harmonic k: 1.0 for a correct
    mark, 0.0 for a failure (score 0 or a null, invalid, mark). Raises
    ``SystemExit`` if a condition's pilot replicate file is missing, naming the
    path and pointing at ``InductionExperiment.harness.sync_down()``.
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
    """Vectorized CMH test (2 x 2 x K, continuity-corrected) -- the Tier-2/3 pairwise test.

    Stratified by harmonic only (K = N_HARMONICS). A distinct statistic from
    `gcmh_reject`, which compares 3 categories, stratifies by harmonic x info,
    and skips the continuity correction. `succ_a` and `succ_b` are (n_sims, K)
    success counts out of `n_per_stratum` trials per stratum, that count being
    the same for both conditions. Returns a per-simulation bool: True where the
    statistic exceeds ``chi2.isf(alpha, df=1)``.
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
    Data Analysis*, Sec. 7.5; SAS PROC FREQ "general association") at R=3
    nominal rungs and a binary response: only R-1 = 2 per-stratum residuals are
    free, so Q = T' Sigma^-1 T ~ chi2(df=2). `succ` is
    ``(n_sims, 3, K)`` success counts per (simulation, rung in ladder order,
    stratum); the result is True per simulation where the statistic exceeds
    ``chi2.isf(alpha, df=2)`` (`alpha` is ALPHA_OMNIBUS for this study's
    gates). Raises ``ValueError`` if the rung axis is not length 3 or
    `n_per_stratum` < 1.

    `n_per_stratum` is trials per rung per stratum: ONE scalar applied
    uniformly to every rung and stratum. That uniformity keeps n_rj/N_j == 1/3
    constant, which collapses the per-stratum covariances EXACTLY (not
    approximately) to Sigma = (sum_j w_j) * C0, with fixed
    C0 = [[2/9, -1/9], [-1/9, 2/9]] and w_j = M_j (N_j - M_j) / (N_j - 1) --
    the shortcut the code takes. Unequal per-rung or per-stratum counts would
    break it and require rebuilding sigma as a genuine (n_sims, K, 2, 2) stack
    summed over K.

    Sigma is exactly singular when every stratum has zero cross-rung variance
    (routine at R=1), and one singular matrix aborts the WHOLE batched
    ``numpy.linalg.solve``, so the `LinAlgError` fallback uses the batched
    pseudo-inverse. Sigma == 0 also forces T == 0, so the fallback's Q = 0 is
    the correct "no evidence against the null", not an artifact.
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
    """Simulated power of the harmonic-stratified CMH test at `n_reps` per harmonic.

    `rates_a` and `rates_b` are the two conditions' assumed true per-harmonic
    rates. The ALPHA_PRIMARY default is for standalone/REPL use only: this
    study has two pairwise tiers with different per-test alphas, so `main`
    passes `alpha` explicitly at every call site. Returns the fraction of
    `n_sims` simulations in which `cmh_reject` rejects.
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

    Scans R = 1, 2, ... up to `MAX_REPLICATES`, stopping once every target is
    met. Returns ``(needed, curve)``: each power target mapped to the smallest
    R reaching it (`None` if no R within `MAX_REPLICATES` does), and each
    scanned R mapped to its simulated power.
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
    small despite `N_SIMS` simulations. Returns the fraction of `N_SIMS`
    simulations in which the pooled test rejects at `alpha`.
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

    Assumes the contrast is a TRUE tie: both conditions are simulated at the
    mean of their assumed per-harmonic rates. Equivalence is declared when the
    (1 - 2*alpha) Wald CI for the pooled accuracy difference lies inside
    (-`delta`, +`delta`) -- standard two one-sided tests at `alpha` each. The
    test is pooled on purpose: under exact equality the stratified and pooled
    risk differences coincide. Returns the smallest R in
    ``range(1, MAX_REPLICATES + 1)`` reaching 80% equivalence power, or `None`.
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

    Builds the (3, K=36) grid of assumed rates over `family`'s rungs and the
    harmonic x info strata, draws Binomial(`n_reps`, rate) counts per cell, and
    hands them to `gcmh_reject` -- so `n_reps` applies uniformly to every rung
    and stratum, as that function requires. `rates` is keyed like
    `load_outcomes`'s return value (the shrunk-toward-mean rates used
    throughout); callers pass a freshly-seeded `rng` so repeated calls
    reproduce. Returns the fraction of `n_sims` simulations that reject.
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
    (21-1) * (4-1) = 60 df -- far too coarse to localize WHICH model/info
    combination drives a rejection -- so this is a design-level diagnostic, not
    a gate: no contrast family depends on it. Returns the rejection fraction
    over `n_sims`; simulations that fail to fit (perfect separation at a tiny
    `n_reps`) count as non-rejections, so this can slightly understate power at
    very small `n_reps`.
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

    Ladder contrasts ask whether accuracy changes along a family's rungs within
    one info arm; info contrasts, whether the 4 info arms separate within one
    model. Returns ``(label, key_a, key_b)`` triples over ``(model, info)``
    keys: all 84 ladder contrasts first (by `FAMILIES` order, then `INFOS`
    order, then ``combinations(rungs, 2)``), then the 126 info contrasts (by
    `MODELS` order, then ``combinations(INFOS, 2)``). Labels:
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
    Returns the same triples as `build_primary_contrasts`, always with
    ``info == "intens"``, grouped by rung level and then by
    ``combinations(FAMILIES, 2)`` (that is, `FAMILIES`' definition) order.
    Labels: ``"[rung {r} | intens] {model_a} vs {model_b}"``.
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

    `rates` is the shrunk-toward-mean assumption behind the headline
    R(80%)/R(90%) columns and `pooled` the condition-mean-only sensitivity
    check; `alpha` is the tier's per-test threshold (ALPHA_PRIMARY or
    ALPHA_SECONDARY), used for both runs. Returns one `_SizingResult` per
    contrast, in input order. Kept side-effect-free and separate from printing
    because `main` needs the PRIMARY results twice: the recommended R is
    derived from them before the omnibus section that precedes the table
    itself. Re-seeds ``np.random.default_rng(SEED)`` before each contrast and
    again before its pooled counterpart, so re-runs are byte-identical.
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
    shrunk-rate assumption; R(80%) under the pooled sensitivity check; and the
    extra quiz questions R(80%) implies beyond the existing pilot run.
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

    Asserts the pre-registered family sizes (210 / 63) and the MODELS/FAMILIES
    agreement before touching pilot data: a silent change there would
    invalidate ALPHA_PRIMARY / ALPHA_SECONDARY. Prints, in order: the observed
    accuracy table grouped by family; a design banner (tiers, sizes, corrected
    alphas); the 7 Tier-1 omnibus gates' simulated power; the 210-row PRIMARY
    and 63-row SECONDARY contrast tables; the recommended replicate count R
    (driven by Tier 2 only); a Fisher-exact cross-check plus TOST equivalence
    sizing for PRIMARY near-ties (R(80%) > 20 or unpowered); and the
    model x info-type interaction diagnostic.
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
