"""Power analysis for the harmonic-stratified family-ladder study.

Tier-2 contrasts require omnibus gates; Tier 3 uses rank-1 BH sizing. Rates
shrink toward condition means because sparse pilot harmonics can degenerate.
"""

import functools
import sys
from itertools import combinations
from pathlib import Path

# Support execution from any cwd.
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

# Derive tags from the committed configuration.
MODELS = tuple(tag_for(key) for key in roster_keys())

FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(tag_for(key) for key in rungs)
    for family, rungs in _study_families().items()
}

INFOS = ("intens", "extens", "noise_intens", "zero")
N_HARMONICS = 9
PILOT_SEED = 0  # Equals _power_common.SEED only because the study is locked to BASE_SEED=0; unrelated.

RESULTS_DIR = results_dir(__file__, up=1)

# Warn when sync and analysis use different roots.
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

# Replicates are the sampling unit; more harmonics change the task.
N_SIMS = 10_000  # Monte Carlo SE of a power estimate <= 0.005.
MAX_REPLICATES = 200  # Search ceiling only: still-unpowered contrasts are censored, not sized.
SHRINKAGE = 1.0  # c in p_k = (y_k + c*p_bar)/(1+c); c=1 pulls a one-replicate rate halfway to its mean.

N_PRIMARY = 210  # 84 ladder (7x4x3) + 126 info (21x6).
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# Size BH contrasts at the conservative rank-1 threshold.
Q_SECONDARY = 0.05
N_SECONDARY = 63  # 3 rung levels x C(7,2)=21 family pairs.
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

N_FAMILIES = len(FAMILIES)  # 7
ALPHA_OMNIBUS = ALPHA / N_FAMILIES


def load_outcomes() -> dict[tuple[str, str], np.ndarray]:
    """Load pilot outcomes by model and information type.

    ``LocalResultsStore`` excludes trace text from marks.
    """
    outcomes: dict[tuple[str, str], np.ndarray] = {}
    # Honor a rebound RESULTS_DIR.
    store = LocalResultsStore(RESULTS_DIR)
    for model in MODELS:
        for info in INFOS:
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
                # Survive ``python -O``.
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
    """Compute two-sided exact McNemar p-values.

    No discordant pairs return 1.0.

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
    # NumPy evaluates both branches.
    p = 2.0 * binom.cdf(np.minimum(b, c), np.maximum(nd, 1), 0.5)
    # Doubling the one-sided tail exceeds 1 when b == c.
    p = np.where(nd == 0, 1.0, np.clip(p, 0.0, 1.0))
    # Preserve scalar output for serialization.
    return p[()] if p.ndim == 0 else p


def cmh_stat(
    succ_a: np.ndarray, succ_b: np.ndarray, n: int | np.ndarray
) -> np.ndarray:
    """Compute the continuity-corrected 2 x 2 x K CMH statistic.

    Stratifies by harmonic; generalized CMH is distinct. Conditions require equal
    trial counts per stratum.

    Parameters
    ----------
    succ_a : np.ndarray
        First-condition counts.
    succ_b : np.ndarray
        Second-condition counts.
    n : int or np.ndarray
        Per-condition trials, scalar or per stratum.

    Returns
    -------
    np.ndarray
        Statistics by batch index.
    """
    n = np.asarray(n)
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
    """Two-sided chi2 (df=1) p-value for `cmh_stat`."""
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def gcmh_stat(succ: np.ndarray, n_per_stratum: int) -> np.ndarray:
    """Compute generalized-CMH statistics for three-rung families.

    Uniform rung and stratum trials permit the fixed covariance shortcut.
    Singular batches return zero because their residual is zero.

    Parameters
    ----------
    succ : np.ndarray
        Counts by simulation, rung, and stratum.
    n_per_stratum : int
        Uniform trials per rung and stratum.

    Returns
    -------
    np.ndarray
        Statistics by simulation.

    Raises
    ------
    ValueError
        Rung axis is not length 3 or trials are below 1.
    """
    _, n_rungs, _ = succ.shape
    if n_rungs != 3:
        raise ValueError(
            f"gcmh_stat assumes 3 rungs (ladder-of-3 families); got axis-1 "
            f"size {n_rungs}"
        )
    if n_per_stratum < 1:
        raise ValueError(f"n_per_stratum must be >= 1, got {n_per_stratum}")
    df = n_rungs - 1

    n = float(n_per_stratum)
    total_n = n_rungs * n

    total_succ = succ.sum(axis=1)
    expected = total_succ / n_rungs
    resid = succ - expected[:, None, :]
    # Drop the redundant category.
    t_vec = resid[:, :df, :].sum(axis=2)

    p = n / total_n
    common = total_succ * (total_n - total_succ) / (total_n - 1.0)
    shape = np.full((df, df), -p * p)
    np.fill_diagonal(shape, p * (1.0 - p))
    w = common.sum(axis=1)
    sigma = w[:, None, None] * shape[None, :, :]

    sigma_inv = np.linalg.pinv(sigma)
    return np.einsum("sd,sde,se->s", t_vec, sigma_inv, t_vec)


def gcmh_reject(succ: np.ndarray, n_per_stratum: int, alpha: float) -> np.ndarray:
    """Return generalized-CMH decisions for three-rung families.

    Parameters
    ----------
    succ : np.ndarray
        Counts by simulation, rung, and stratum.
    n_per_stratum : int
        Uniform trials per rung and stratum.
    alpha : float
        Significance threshold.

    Returns
    -------
    np.ndarray
        Rejection decisions.

    Raises
    ------
    ValueError
        Rung axis is not length 3 or trials are below 1.
    """
    stat = gcmh_stat(succ, n_per_stratum)

    return stat > chi2.isf(alpha, df=2)


def simulated_power(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_PRIMARY,
    n_sims: int = N_SIMS,
) -> float:
    """Estimate harmonic-stratified CMH power.

    Callers pass tier-specific ``alpha`` because defaults differ by tier.

    Parameters
    ----------
    rates_a : np.ndarray
        First-condition rates.
    rates_b : np.ndarray
        Second-condition rates.
    n_reps : int
        Replicates per harmonic.
    rng : np.random.Generator
        Simulation generator.
    alpha : float, optional
        Per-test threshold.
    n_sims : int, optional
        Simulated experiments.

    Returns
    -------
    float
        Estimated rejection fraction.
    """
    succ_a = rng.binomial(n_reps, rates_a, size=(n_sims, rates_a.size))
    succ_b = rng.binomial(n_reps, rates_b, size=(n_sims, rates_b.size))
    return (cmh_stat(succ_a, succ_b, n_reps) > chi2.isf(alpha, df=1)).mean()


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
    """Find the smallest replicate count for each power target.

    Cache rate values and seed each scan so hits and recomputations agree.

    Parameters
    ----------
    rates_a : np.ndarray
        First-condition rates.
    rates_b : np.ndarray
        Second-condition rates.
    alpha : float, optional
        Per-test threshold.

    Returns
    -------
    _SizingScan
        Target counts and simulated-power curve; copies protect the cache.

    Raises
    ------
    ValueError
        Rate shapes differ.
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
    """Cross-check power with pooled two-sided Fisher tests.

    Cache discrete counts to limit SciPy calls.

    Parameters
    ----------
    rates_a : np.ndarray
        First-condition rates.
    rates_b : np.ndarray
        Second-condition rates.
    n_reps : int
        Replicates per harmonic.
    rng : np.random.Generator
        Simulation generator.
    alpha : float, optional
        Significance threshold.

    Returns
    -------
    float
        Rejection fraction.
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
    """Find the smallest R for 80% TOST equivalence power.

    Simulate both arms at their mean because this tests a true tie.

    Parameters
    ----------
    rates_a : np.ndarray
        First-condition rates.
    rates_b : np.ndarray
        Second-condition rates.
    delta : float
        Equivalence margin.
    rng : np.random.Generator
        Simulation generator.
    alpha : float, optional
        One-sided threshold.
    n_sims : int, optional
        Simulated experiments.

    Returns
    -------
    int | None
        Smallest qualifying R, or ``None``.
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
    """Estimate a family's Tier-1 omnibus-gate power.

    Use uniform trials across rungs and strata because generalized CMH requires it.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates by model and information type.
    family : str
        Family to test.
    n_reps : int
        Uniform replicates per rung and stratum.
    rng : np.random.Generator
        Simulation generator.
    alpha : float, optional
        Significance threshold.
    n_sims : int, optional
        Simulated experiments.

    Returns
    -------
    float
        Estimated rejection fraction.
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


#: Diagnostic default: 200 keeps two GLM passes affordable; its worst-case
#: Monte Carlo SE is 0.035, adequate for a non-gate.
N_SIMS_OMNIBUS_DIAGNOSTIC = 200


def omnibus_interaction_power(
    rates: dict[tuple[str, str], np.ndarray],
    n_reps: int,
    n_sims: int = N_SIMS_OMNIBUS_DIAGNOSTIC,
) -> float:
    """Estimate model-by-information interaction power.

    The 60-df test is diagnostic, not a gate. Failed fits count as non-rejections.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Rates by model and information type.
    n_reps : int
        Replicates per cell.
    n_sims : int, optional
        Simulated experiments.

    Returns
    -------
    float
        Rejection fraction.
    """
    import statsmodels.api as sm
    from scipy.stats import chi2 as chi2_dist

    # Isolate diagnostic draws from sizing draws.
    rng = np.random.default_rng(SEED + 1)
    # Design matrices are fixed across simulations.
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
        except Exception:  # Perfect separation at tiny n_reps.
            continue
        if 2 * (llf_full - llf_null) > crit:
            rejections += 1
    return rejections / n_sims


def build_primary_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build PRIMARY ladder and information contrasts.

    Keep ladder contrasts first because the report slices at that boundary.
    """
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    for family, rungs in FAMILIES.items():
        for info in INFOS:
            for rung_a, rung_b in combinations(rungs, 2):
                label = f"[{family} ladder | {info}] {rung_a} vs {rung_b}"
                contrasts.append((label, (rung_a, info), (rung_b, info)))
    for model in MODELS:
        for info_a, info_b in combinations(INFOS, 2):
            label = f"[{model}] {info_a} vs {info_b}"
            contrasts.append((label, (model, info_a), (model, info_b)))
    return contrasts


def build_secondary_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build SECONDARY size-matched, cross-family contrasts.

    Use only ``intens`` and group by rung level.
    """
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    for r in range(3):
        for fam_a, fam_b in combinations(FAMILIES, 2):
            model_a, model_b = FAMILIES[fam_a][r], FAMILIES[fam_b][r]
            label = f"[rung {r} | intens] {model_a} vs {model_b}"
            contrasts.append((label, (model_a, "intens"), (model_b, "intens")))
    return contrasts


# Both sizing tables use this shared result shape.
_SizingResult = tuple[
    str, tuple[str, str], tuple[str, str], dict[float, int | None], dict[float, int | None]
]


def _compute_sizing_results(
    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]],
    rates: dict[tuple[str, str], np.ndarray],
    pooled: dict[tuple[str, str], np.ndarray],
    alpha: float,
) -> list[_SizingResult]:
    """Size every contrast under shrunk and pooled assumptions.

    Parameters
    ----------
    contrasts : list[tuple[str, tuple[str, str], tuple[str, str]]]
        Contrasts in output order.
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean sensitivity assumption.
    alpha : float
        Per-test threshold.

    Returns
    -------
    list[_SizingResult]
        Results in input order.
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
    """Print aligned sizing rows.

    Parameters
    ----------
    results : list[_SizingResult]
        Sizing results.
    outcomes : dict[tuple[str, str], np.ndarray]
        Pilot marks for observed rates.
    label_w : int
        Contrast-label width.
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
    """Check protocol denominators and contrast builders agree.

    Wrong counts invalidate correction thresholds. Raises ``RuntimeError`` because
    ``python -O`` removes assertions.

    Reads the module globals on each call so a patched constant re-checks; that
    is how a test demonstrates the gate fires.
    """
    # Literal protocol denominators prevent silent redesign.
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

    # Builders depend on both structures.
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


# Run after contrast builders and before pilot data access.
check_design_invariants()


def observed_accuracy(
    outcomes: dict[tuple[str, str], np.ndarray]
) -> list[tuple[str, list[tuple[str, list[tuple[str, float]]]]]]:
    """Compute observed pilot accuracy by family, model, and information type.

    Parameters
    ----------
    outcomes : dict[tuple[str, str], np.ndarray]
        Pilot outcomes by model and information type.

    Returns
    -------
    list[tuple[str, list[tuple[str, list[tuple[str, float]]]]]]
        Accuracy rows in family and information order.
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
    """Gather design constants for the report banner."""
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
    """Build PRIMARY sizing data and recommendation inputs.

    Use the maximum powered R, not the ceiling, so censored contrasts do not set
    the recommendation.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean sensitivity assumption.

    Returns
    -------
    dict
        Results, recommendation inputs, and layout widths.

    Raises
    ------
    SystemExit
        No PRIMARY contrast reaches 80% power within the search range.
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
    """Compute family omnibus-gate power at recommended R and R=1.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates by model and information type.
    r_star : int
        Recommended replicate count.

    Returns
    -------
    list[tuple[str, float, float]]
        Per-family power rows.
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
    """Build SECONDARY sizing data.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk-rate assumption.
    pooled : dict[tuple[str, str], np.ndarray]
        Condition-mean sensitivity assumption.

    Returns
    -------
    dict
        Results and contrast-label width.
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
    """Derive recommendation figures from PRIMARY sizing.

    Parameters
    ----------
    r_star : int
        PRIMARY recommendation.
    n_censored : int
        Censored PRIMARY contrasts.

    Returns
    -------
    dict
        Recommendation and additional-run counts.
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
    """Compute Fisher and TOST checks at recommended R.

    Parameters
    ----------
    primary_results : list[_SizingResult]
        PRIMARY sizing results.
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates by model and information type.
    r_star : int
        Fisher replicate count.

    Returns
    -------
    dict
        Fisher, near-tie, and equivalence-sizing data.
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

    # The 20-R cut is a report grouping, not an inferential threshold.
    # Saturated rates yield zero-width Wald intervals and R=1.
    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed, _pooled in primary_results
        if needed[0.80] is None or needed[0.80] > 20
    ]
    deltas = (0.10, 0.15, 0.20)
    if not near_ties:
        # Avoid division by zero.
        return dict(fisher=fisher, near_ties=near_ties, deltas=deltas, alpha_eq=None,
                    table=[])

    # Correct the planned equivalence family.
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
    """Compute interaction-diagnostic power at recommended R and R=1.

    Parameters
    ----------
    rates : dict[tuple[str, str], np.ndarray]
        Shrunk rates by model and information type.
    r_star : int
        Recommended replicate count.

    Returns
    -------
    tuple[float, float]
        Power at recommended R and R=1.
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
    """Run and print the family-ladder power analysis."""
    outcomes = load_outcomes()
    rates = {key: shrunk_rates(y) for key, y in outcomes.items()}
    pooled = {key: np.full(N_HARMONICS, y.mean()) for key, y in outcomes.items()}

    render_observed_accuracy(observed_accuracy(outcomes))  # 1
    render_design_banner(design_banner())  # 2

    # Reuse PRIMARY results for gates and recommendation.
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
