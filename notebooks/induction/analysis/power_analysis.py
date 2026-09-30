"""Power analysis for the harmonic-stratified family-ladder study.

Tier-2 ladder contrasts require their family's omnibus gate; Tier 3 uses rank-1
BH sizing. Rates shrink toward condition means because sparse pilot harmonics can
degenerate.

Every sizing here powers the pre-registered harmonic-stratified CMH test on
independent per-harmonic Bernoulli streams. The PRIMARY inference in
`significance_report` is the exact seed-level sign-flip, whose power depends on
within-seed dependence a one-replicate pilot cannot estimate; these tables are
therefore the pre-registration sizing check and a descriptive sensitivity
analysis, not a power statement about the sign-flip test.

This study is exploratory end to end: it is pilot-sized, its sizing rests on an
independent-harmonic approximation, and it makes no confirmatory claims.
The Tier-1 omnibus gate and the Holm/BH corrections order the evidence within
that exploratory frame; a gated ladder finding is a stronger exploratory
signal, not a confirmed effect.
"""

import functools
import math
import sys
import warnings
from itertools import combinations
from pathlib import Path
from typing import Optional

# Support execution from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import statsmodels.api as sm
from _power_common import ALPHA, POWER_TARGETS, SEED, results_dir
from scipy.stats import binom, chi2, fisher_exact, norm
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress
from smolbench.evals.study_config import families, roster_keys, tag_for
from smolbench.induction.periodic import CONDITIONS

# Derive tags from the committed configuration.
ROSTER_KEYS = tuple(roster_keys())
MODELS = tuple(tag_for(key) for key in ROSTER_KEYS)

FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(tag_for(key) for key in rungs) for family, rungs in families().items()
}

# Arm names in the order run_study collects them.
INFOS = tuple(CONDITIONS)
RESULTS_DIR = results_dir("induction")
# run_study.py owns BASE_SEED, N_REPLICATES and PeriodicConfig(n=9). Importing it
# configures logging, loads keys.env and builds the env-configured EXPERIMENT at
# module scope, so the analysis restates the three values. A BASE_SEED or
# N_HARMONICS drift surfaces in load_outcomes (missing pilot replicate, wrong mark
# count); an N_REPLICATES drift surfaces in paired_analysis.load_marks (a seed past
# the expected range exits) or its depth WARNING, and multiplicity_sim simulates
# every part at this depth.
BASE_SEED = 0
N_REPLICATES = 30
# Replicates are the sampling unit; more harmonics would change the task.
N_HARMONICS = 9

N_SIMS = 10_000  # Monte Carlo SE of a power estimate <= 0.005.
#: 200 keeps two GLM passes affordable (worst-case MC SE 0.035).
N_SIMS_OMNIBUS_DIAGNOSTIC = 200
#: Search ceiling only: still-unpowered contrasts are censored, not sized.
MAX_REPLICATES = 200
#: R(80%) above which a PRIMARY contrast is reported as a near tie; a report grouping,
#: not an inferential threshold (saturated rates give R=1).
NEAR_TIE_R = 20
#: TOST equivalence margins in accuracy points.
EQUIVALENCE_DELTAS = (0.10, 0.15, 0.20)
#: c in p_k = (y_k + c*p_bar)/(1+c); c=1 pulls a one-replicate rate halfway to its mean.
SHRINKAGE = 1.0

# The pre-registered roster as (checkpoint key, tag) pairs. Counts alone would
# pass a same-family checkpoint swap, so the keys (what the study runs) and
# their tags (what names the result directories) are both pinned.
PREREGISTERED_ROSTER: tuple[tuple[str, str], ...] = (
    ("qwen3.5-27b", "qwen35_27b"),
    ("qwen3.5-122b-a10b", "qwen35_122b"),
    ("qwen3.5-397b-a17b", "qwen35_397b"),
    ("nemotron-3-nano-4b", "nemo3_4b"),
    ("nemotron-3-nano-30b-a3b", "nemo3_30b"),
    ("nemotron-3-super-120b-a12b", "nemo3_120b"),
    ("gemma-4-e2b", "gemma4_e2b"),
    ("gemma-4-12b", "gemma4_12b"),
    ("gemma-4-31b", "gemma4_31b"),
    ("glm-4.7-flash", "glm_flash"),
    ("glm-4.5-air", "glm_air"),
    ("glm-4.7", "glm_47"),
    ("ministral-3-3b", "min3_3b"),
    ("ministral-3-8b", "min3_8b"),
    ("ministral-3-14b", "min3_14b"),
    ("exaone-4.0-32b", "exaone_32b"),
    ("exaone-4.5-33b", "exaone_33b"),
    ("k-exaone-236b-a23b", "exaone_236b"),
    ("deepseek-v4-flash", "ds_flash"),
    ("deepseek-v3.1", "ds_v31"),
    ("deepseek-v4-pro", "ds_pro"),
)
PREREGISTERED_MODELS = tuple(tag for _key, tag in PREREGISTERED_ROSTER)

N_RUNGS = 3
N_INFOS = len(INFOS)
N_FAMILIES = len(FAMILIES)
N_LADDERS = N_FAMILIES * N_INFOS
N_LADDER_CONTRASTS = N_LADDERS * math.comb(N_RUNGS, 2)
N_INFO_CONTRASTS = len(MODELS) * math.comb(N_INFOS, 2)
N_PRIMARY = N_LADDER_CONTRASTS + N_INFO_CONTRASTS
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# Size BH contrasts at the conservative rank-1 threshold.
#: BH's FDR level is the familywise level; a separate knob would need its own derivation.
Q_SECONDARY = ALPHA
N_SECONDARY = N_RUNGS * math.comb(N_FAMILIES, 2)
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

ALPHA_OMNIBUS = ALPHA / N_FAMILIES

# Degrees of freedom of the model-by-info interaction diagnostic.
DF_INTERACTION = (len(MODELS) - 1) * (N_INFOS - 1)

#: One length-`N_HARMONICS` vector per ``(model tag, info)`` cell: pilot marks or
#: per-harmonic rates.
CellVectors = dict[tuple[str, str], np.ndarray]
#: ``(label, cell_a, cell_b)``: the two cells a pairwise contrast compares.
_Contrast = tuple[str, tuple[str, str], tuple[str, str]]


def load_outcomes(results_dir: Path = RESULTS_DIR) -> CellVectors:
    """Load pilot outcomes by model and information type.

    Only ``Mark.score`` is read: a harmonic counts as a success when its score is 1.

    Parameters
    ----------
    results_dir : Path, optional
        Local results tree in the ``rep_<seed>.yaml`` layout.

    Returns
    -------
    CellVectors
        One length-`N_HARMONICS` 0/1 vector per ``(model, info)`` cell.

    Raises
    ------
    SystemExit
        If a pilot replicate is missing or does not have `N_HARMONICS` marks.
    """
    outcomes: CellVectors = {}
    store = LocalResultsStore(results_dir)
    for model in MODELS:
        for info in INFOS:
            addr = ReplicateAddress(tag=model, info=info, seed=BASE_SEED)
            path = store.path(addr)
            if not store.exists(addr):
                # sync_down() pulls S3 results into the rep_{seed}.yaml layout this script reads.
                raise SystemExit(
                    f"No pilot replicate for ({model}, {info}) at {path}\n"
                    "Run the pilot in notebooks/induction/run_study.py first, or "
                    "InductionExperiment.harness.sync_down() if it ran elsewhere."
                )
            scores = [m.score for m in store.load_marks(addr).marks]
            if len(scores) != N_HARMONICS:
                raise SystemExit(
                    f"Pilot replicate {path} has {len(scores)} marks, "
                    f"expected {N_HARMONICS}; the sync is incomplete."
                )
            outcomes[(model, info)] = np.array([s == 1 for s in scores], float)
    return outcomes


def shrunk_rates(y: np.ndarray) -> np.ndarray:
    """Per-harmonic rates shrunk toward the condition mean."""
    return (y + SHRINKAGE * y.mean()) / (1.0 + SHRINKAGE)


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


def cmh_stat(succ_a: np.ndarray, succ_b: np.ndarray, n: int | np.ndarray) -> np.ndarray:
    """Compute the continuity-corrected 2 x 2 x K CMH statistic.

    Stratifies by harmonic; generalized CMH is distinct. Conditions require equal
    trial counts per stratum.

    Parameters
    ----------
    succ_a : np.ndarray
        Success counts for the first condition, shaped ``(..., K)``.
    succ_b : np.ndarray
        Success counts for the second condition, shaped ``(..., K)``.
    n : int or np.ndarray
        Trial count per condition and stratum.

    Returns
    -------
    np.ndarray
        One statistic per leading batch index.
    """
    n = np.asarray(n)
    big_n = 2 * n
    m1 = succ_a + succ_b
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.clip(np.abs((succ_a - expect).sum(axis=-1)) - 0.5, 0.0, None) ** 2
    denom = var.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denom > 0, num / denom, 0.0)


def cmh_p(succ_a: np.ndarray, succ_b: np.ndarray, n: int | np.ndarray) -> np.ndarray:
    """Two-sided chi2 (df=1) p-value for `cmh_stat`."""
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def gcmh_stat(succ: np.ndarray, n_per_stratum: int) -> np.ndarray:
    """Compute generalized-CMH statistics for three-rung families.

    Uniform rung and stratum trials permit the fixed covariance shortcut.
    Singular batches return zero because their residual is zero.

    Parameters
    ----------
    succ : np.ndarray
        Success counts with shape ``(n_sims, 3, K)``.
    n_per_stratum : int
        Trials per rung and stratum.

    Returns
    -------
    np.ndarray
        GCMH statistics.

    Raises
    ------
    ValueError
        If the rung axis is not length `N_RUNGS` or counts are invalid.
    """
    n_rungs = succ.shape[1]
    if n_rungs != N_RUNGS:
        raise ValueError(
            f"gcmh_stat assumes {N_RUNGS} rungs (ladder-of-{N_RUNGS} families); "
            f"got axis-1 size {n_rungs}"
        )
    if n_per_stratum < 1:
        raise ValueError(f"n_per_stratum must be >= 1, got {n_per_stratum}")
    df = n_rungs - 1

    n = float(n_per_stratum)
    total_n = n_rungs * n

    total_succ = succ.sum(axis=1)
    # Drop the redundant category.
    t_vec = (succ - (total_succ / n_rungs)[:, None, :])[:, :df, :].sum(axis=2)

    p = n / total_n
    common = total_succ * (total_n - total_succ) / (total_n - 1.0)
    shape = np.full((df, df), -p * p)
    np.fill_diagonal(shape, p * (1.0 - p))
    sigma = common.sum(axis=1)[:, None, None] * shape[None, :, :]
    # pinv: a stratum with every rung at ceiling makes sigma singular; the
    # generalized inverse keeps the Wald form defined there.
    return np.einsum("sd,sde,se->s", t_vec, np.linalg.pinv(sigma), t_vec)


#: Power target -> smallest R from which power stays at or above it; ``None`` when
#: the target is not sustained within `MAX_REPLICATES`.
_Needed = dict[float, Optional[int]]
_SizingScan = tuple[_Needed, dict[int, float]]


def _cumulative_successes(
    rng: np.random.Generator, rates: np.ndarray, n_sims: int
) -> np.ndarray:
    """Cumulative successes of one `MAX_REPLICATES`-long Bernoulli stream per harmonic.

    Shape ``(n_sims, MAX_REPLICATES, rates.size)``.
    """
    trials = rng.random((n_sims, MAX_REPLICATES, rates.size), dtype=np.float32) < rates
    return np.cumsum(trials, axis=1, dtype=np.int16)


@functools.lru_cache(maxsize=None)
def _sizing_scan(rates_a: tuple, rates_b: tuple, alpha: float) -> _SizingScan:
    """`replicates_needed`'s memoized core, keyed on hashable rate tuples.

    Common random numbers: the R-replicate design is the first R trials of one
    `MAX_REPLICATES`-long Bernoulli stream per harmonic and arm, so successive R
    share their noise and sampling error cannot reorder neighbouring R. Each
    target's R is the `_sustained_crossing`, so the maximum over contrasts powers
    every contrast at that R.
    """
    a, b = np.asarray(rates_a), np.asarray(rates_b)
    rng = np.random.default_rng(SEED)
    crit = chi2.isf(alpha, df=1)
    cum_a = _cumulative_successes(rng, a, N_SIMS)
    cum_b = _cumulative_successes(rng, b, N_SIMS)
    curve: dict[int, float] = {}
    for n_reps in range(1, MAX_REPLICATES + 1):
        stat = cmh_stat(
            cum_a[:, n_reps - 1].astype(np.int64),
            cum_b[:, n_reps - 1].astype(np.int64),
            n_reps,
        )
        curve[n_reps] = float((stat > crit).mean())
    return {t: _sustained_crossing(curve, t) for t in POWER_TARGETS}, curve


def _sustained_crossing(curve: dict[int, float], target: float) -> Optional[int]:
    """Return the smallest R from which `curve` stays at or above `target`.

    A first noisy crossing could dip back below the target at a larger R set by
    another contrast; the sustained crossing cannot.
    """
    needed = None
    for n_reps in range(MAX_REPLICATES, 0, -1):
        if curve[n_reps] < target:
            break
        needed = n_reps
    return needed


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
        Per-harmonic rates for the first condition.
    rates_b : np.ndarray
        Per-harmonic rates for the second condition.
    alpha : float, optional
        Per-test significance threshold.

    Returns
    -------
    _SizingScan
        ``(needed, curve)``: power target -> smallest R from which power stays at or above it, and power by R.

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
    total = n_reps * N_HARMONICS
    succ_a = rng.binomial(n_reps, rates_a, size=(N_SIMS, rates_a.size)).sum(axis=1)
    succ_b = rng.binomial(n_reps, rates_b, size=(N_SIMS, rates_b.size)).sum(axis=1)
    cache: dict[tuple[int, int], bool] = {}
    rejections = 0
    for ka, kb in zip(succ_a, succ_b):
        key = (int(ka), int(kb))
        if key not in cache:
            _, p = fisher_exact([[ka, total - ka], [kb, total - kb]])
            cache[key] = p <= alpha
        rejections += cache[key]
    return rejections / N_SIMS


def _equivalence_power_curve(
    common: np.ndarray,
    delta: float,
    rng: np.random.Generator,
    alpha: float,
    n_sims: int,
) -> dict[int, float]:
    """Estimate nested Agresti–Caffo equivalence power at every replicate count."""
    z = norm.isf(alpha)
    cum_a = _cumulative_successes(rng, common, n_sims)
    cum_b = _cumulative_successes(rng, common, n_sims)
    curve: dict[int, float] = {}
    for n_reps in range(1, MAX_REPLICATES + 1):
        total = n_reps * N_HARMONICS
        succ_a = cum_a[:, n_reps - 1].sum(axis=1, dtype=np.int64)
        succ_b = cum_b[:, n_reps - 1].sum(axis=1, dtype=np.int64)
        adj_a, adj_b = (succ_a + 1) / (total + 2), (succ_b + 1) / (total + 2)
        diff = adj_a - adj_b
        se = np.sqrt(
            adj_a * (1 - adj_a) / (total + 2) + adj_b * (1 - adj_b) / (total + 2)
        )
        curve[n_reps] = float(
            ((diff + z * se < delta) & (diff - z * se > -delta)).mean()
        )
    return curve


def equivalence_replicates(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    delta: float,
    rng: np.random.Generator,
    alpha: float = ALPHA,
    n_sims: int = N_SIMS,
) -> Optional[int]:
    """Find the smallest R for TOST equivalence power at ``POWER_TARGETS[0]``.

    Simulate both arms at their mean because this tests a true tie.
    The interval is Agresti–Caffo: one success and one failure are added to each
    arm, and both the centre and the standard error use those adjusted
    proportions, so a saturated arm never yields a zero-width interval.
    Power uses common random numbers across nested replicate counts and the
    `_sustained_crossing` of the first `POWER_TARGETS` target.

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
    Optional[int]
        Smallest replicate count reaching the requested power.
    """
    common = (rates_a + rates_b) / 2.0
    curve = _equivalence_power_curve(common, delta, rng, alpha, n_sims)
    return _sustained_crossing(curve, POWER_TARGETS[0])


def omnibus_power(
    rates: CellVectors,
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
    rates : CellVectors
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
    strata = [(k, info) for info in INFOS for k in range(N_HARMONICS)]
    cell_rates = np.array(
        [[rates[(rung, info)][k] for k, info in strata] for rung in rungs]
    )  # (N_RUNGS, K)
    succ = rng.binomial(
        n_reps, cell_rates[None, :, :], size=(n_sims, len(rungs), len(strata))
    )
    return (gcmh_stat(succ, n_reps) > chi2.isf(alpha, df=N_RUNGS - 1)).mean()


def omnibus_interaction_power(rates: CellVectors, n_reps: int) -> float:
    """Estimate model-by-information interaction power.

    The ``DF_INTERACTION``-df test is diagnostic, not a gate. It is a likelihood
    ratio (deviance) test, not a Wald test, because separation is the norm here:
    a ceiling cell shrinks to exactly 1.0, so the interaction fit puts that cell
    at 1.0 with a divergent coefficient. The deviance still converges, so every
    simulation counts; statsmodels 0.14 fits such a model with a finite llf.

    Parameters
    ----------
    rates : CellVectors
        Rates keyed by model and info type.
    n_reps : int
        Replicates per cell.

    Returns
    -------
    float
        Rejection fraction over `N_SIMS_OMNIBUS_DIAGNOSTIC` simulations.
    """
    # Isolate diagnostic draws from sizing draws.
    rng = np.random.default_rng(SEED + 1)
    # Design matrices are fixed across simulations.
    cells = [(m, i, k) for m in MODELS for i in INFOS for k in range(N_HARMONICS)]

    def design(interaction: bool) -> np.ndarray:
        cols = [np.ones(len(cells))]
        cols += [np.array([c[0] == m for c in cells], float) for m in MODELS[1:]]
        cols += [np.array([c[1] == i for c in cells], float) for i in INFOS[1:]]
        cols += [
            np.array([c[2] == k for c in cells], float) for k in range(1, N_HARMONICS)
        ]
        if interaction:
            cols += [
                np.array([c[0] == m and c[1] == i for c in cells], float)
                for m in MODELS[1:]
                for i in INFOS[1:]
            ]
        return np.column_stack(cols)

    x_null, x_full = design(False), design(True)
    df_extra = x_full.shape[1] - x_null.shape[1]
    if df_extra != DF_INTERACTION:
        raise RuntimeError(
            f"interaction design gained {df_extra} df, expected "
            f"DF_INTERACTION={DF_INTERACTION}"
        )
    crit = chi2.isf(ALPHA, df=df_extra)
    cell_rates = np.array([rates[(m, i)][k] for m, i, k in cells])

    rejections = 0
    for _ in range(N_SIMS_OMNIBUS_DIAGNOSTIC):
        succ = rng.binomial(n_reps, cell_rates)
        endog = np.column_stack([succ, n_reps - succ])
        # A fully separated draw only warns (once per IRLS step, hundreds per
        # sim) and still fits with a finite llf; nothing here raises.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PerfectSeparationWarning)
            llf_null, llf_full = (
                sm.GLM(endog, x, family=sm.families.Binomial()).fit().llf
                for x in (x_null, x_full)
            )
        if 2 * (llf_full - llf_null) > crit:
            rejections += 1
    return rejections / N_SIMS_OMNIBUS_DIAGNOSTIC


def build_primary_contrasts() -> list[_Contrast]:
    """Build PRIMARY ladder and information contrasts.

    Keep ladder contrasts first because the report slices at that boundary.
    """
    ladders = [
        (
            f"[{family} ladder | {info}] {rung_a} vs {rung_b}",
            (rung_a, info),
            (rung_b, info),
        )
        for family, rungs in FAMILIES.items()
        for info in INFOS
        for rung_a, rung_b in combinations(rungs, 2)
    ]
    infos = [
        (f"[{model}] {info_a} vs {info_b}", (model, info_a), (model, info_b))
        for model in MODELS
        for info_a, info_b in combinations(INFOS, 2)
    ]
    return ladders + infos


def build_secondary_contrasts() -> list[_Contrast]:
    """Build SECONDARY size-matched, cross-family contrasts.

    Use only ``intens`` and group by rung level.
    """
    return [
        (
            f"[rung {r} | intens] {FAMILIES[fam_a][r]} vs {FAMILIES[fam_b][r]}",
            (FAMILIES[fam_a][r], "intens"),
            (FAMILIES[fam_b][r], "intens"),
        )
        for r in range(N_RUNGS)
        for fam_a, fam_b in combinations(FAMILIES, 2)
    ]


#: A `_Contrast` with its R per power target under the shrunk, then the pooled, rates.
_SizingResult = tuple[str, tuple[str, str], tuple[str, str], _Needed, _Needed]


def _compute_sizing_results(
    contrasts: list[_Contrast], rates: CellVectors, pooled: CellVectors, alpha: float
) -> list[_SizingResult]:
    """Size every contrast under the shrunk `rates` and the `pooled` rates at `alpha`, in input order."""
    return [
        (
            name,
            key_a,
            key_b,
            replicates_needed(rates[key_a], rates[key_b], alpha=alpha)[0],
            replicates_needed(pooled[key_a], pooled[key_b], alpha=alpha)[0],
        )
        for name, key_a, key_b in contrasts
    ]


def _fmt_r(r: Optional[int]) -> str:
    """Format a replicate count; ``None`` means the scan cap was reached short of the target."""
    return f">{MAX_REPLICATES}" if r is None else str(r)


def _print_sizing_table(
    sections: list[tuple[Optional[str], list[_SizingResult]]],
    outcomes: CellVectors,
    label_w: int,
) -> None:
    """Print the sizing column header, then each ``(caption, rows)`` section, at label width `label_w`."""
    header = (
        f"{'contrast':{label_w}s} {'rates':13s} "
        f"{f'R({POWER_TARGETS[0]:.0%})':>7s} {f'R({POWER_TARGETS[1]:.0%})':>7s} "
        f"{f'R{POWER_TARGETS[0]:.0%} pooled':>11s} {'extra questions':>15s}"
    )
    print(f"{header}\n{'-' * len(header)}")
    for caption, rows in sections:
        if caption is not None:
            print(caption)
        for name, key_a, key_b, needed, needed_pooled in rows:
            r80, r90 = needed[POWER_TARGETS[0]], needed[POWER_TARGETS[1]]
            # Questions beyond the pilot run: (R - 1) more runs of N_HARMONICS each.
            extra = "n/a" if r80 is None else str((r80 - 1) * N_HARMONICS)
            obs = f"{outcomes[key_a].mean():.2f} vs {outcomes[key_b].mean():.2f}"
            print(
                f"{name:{label_w}s} {obs:13s} {_fmt_r(r80):>7s} {_fmt_r(r90):>7s} "
                f"{_fmt_r(needed_pooled[POWER_TARGETS[0]]):>11s} {extra:>15s}"
            )
    print()


def check_design_invariants() -> None:
    """Check protocol denominators and contrast builders agree.

    Wrong counts invalidate correction thresholds. Raises ``RuntimeError`` because
    ``python -O`` removes assertions.
    """
    # MODELS is derived from ROSTER_KEYS one to one, so the pair-up cannot
    # misalign; a drift of any kind surfaces as the RuntimeError below.
    roster = tuple(zip(ROSTER_KEYS, MODELS))
    if roster != PREREGISTERED_ROSTER:
        raise RuntimeError(
            f"study_config roster {roster!r} disagrees with the pre-registered "
            f"roster {PREREGISTERED_ROSTER!r}; re-pin PREREGISTERED_ROSTER "
            "deliberately if the study changed"
        )

    # A MODELS/FAMILIES disagreement silently changes which contrasts exist.
    expected_models = tuple(rung for rungs in FAMILIES.values() for rung in rungs)
    if MODELS != expected_models:
        raise RuntimeError(
            f"MODELS {MODELS!r} disagrees with FAMILIES' rungs {expected_models!r}"
        )

    n_primary = len(build_primary_contrasts())
    if n_primary != N_PRIMARY:
        raise RuntimeError(
            f"build_primary_contrasts() returns {n_primary}, expected "
            f"N_PRIMARY={N_PRIMARY}; ALPHA_PRIMARY={ALPHA_PRIMARY:.6g} was "
            "frozen at import"
        )

    n_secondary = len(build_secondary_contrasts())
    if n_secondary != N_SECONDARY:
        raise RuntimeError(
            f"build_secondary_contrasts() returns {n_secondary}, expected "
            f"N_SECONDARY={N_SECONDARY}; ALPHA_SECONDARY={ALPHA_SECONDARY:.6g} "
            "was frozen at import"
        )


# Run after contrast builders and before pilot data access.
check_design_invariants()


def render_observed_accuracy(outcomes: CellVectors) -> None:
    """Print observed pilot accuracy by family, model, and information type."""
    print(
        f"Observed accuracy (n={N_HARMONICS}, one question per harmonic "
        f"k=1..{N_HARMONICS}; {len(MODELS)} models x {N_INFOS} infos):"
    )
    for family, rungs in FAMILIES.items():
        print(f"  {family}:")
        for model in rungs:
            row = "  ".join(
                f"{info}={outcomes[(model, info)].mean():.3f}" for info in INFOS
            )
            print(f"    {model:14s} {row}")
    print()


def render_design_banner() -> None:
    """Print the design banner: contrast tiers, their thresholds, and the sizing assumptions."""
    print(
        f"Design: three pre-registered contrast tiers over the "
        f"{N_FAMILIES}-family x {N_RUNGS}-rung "
        f"({len(MODELS)}-model) scaling grid (see module docstring):\n"
        f"  Tier 1 (family omnibus gates):  {N_FAMILIES} tests, "
        f"alpha = {ALPHA}/{N_FAMILIES} = {ALPHA_OMNIBUS:.5f} (Bonferroni)\n"
        f"  Tier 2 (PRIMARY pairwise):      {N_PRIMARY} tests, "
        f"alpha = {ALPHA}/{N_PRIMARY} = {ALPHA_PRIMARY:.6f} (Bonferroni)\n"
        f"  Tier 3 (SECONDARY pairwise):    {N_SECONDARY} tests, "
        f"Benjamini-Hochberg q = {Q_SECONDARY}, sized at the conservative rank-1 "
        f"threshold alpha = {Q_SECONDARY}/{N_SECONDARY} = {ALPHA_SECONDARY:.6f} "
        "(an UPPER BOUND on the R BH will actually need)\n"
        f"{N_SIMS} sims per point, seed={SEED}.\n"
        "Sizing test: harmonic-stratified CMH on independent per-harmonic "
        "Bernoulli streams (the pre-registered sizing). The PRIMARY inference "
        "is the exact seed-level sign-flip (significance_report.py); all R "
        "figures below are descriptive sensitivity for that test, whose power "
        "also depends on within-seed dependence the R=1 pilot cannot estimate.\n"
        f"Assumed rates: per-harmonic outcomes shrunk toward condition mean "
        f"(c={SHRINKAGE}); 'pooled' column = sensitivity with "
        "condition-mean rates only.\n"
    )


def primary_contrasts_table(rates: CellVectors, pooled: CellVectors) -> dict:
    """Build PRIMARY sizing data and recommendation inputs.

    `r_star` is the smallest R that powers every contrast that is powerable
    within `MAX_REPLICATES`; `n_censored` counts the contrasts it leaves unpowered, and
    `family_r` is the whole-family R (``None`` when any contrast is censored).

    Parameters
    ----------
    rates : CellVectors
        Shrunk-rate assumption for PRIMARY sizing.
    pooled : CellVectors
        Condition-mean-only sensitivity assumption.

    Returns
    -------
    dict
        With keys `results`, `r_star`, `family_r`, `n_censored`, `label_w`.

    Raises
    ------
    SystemExit
        If no PRIMARY contrast reaches ``POWER_TARGETS[0]`` power within `MAX_REPLICATES`.
    """
    results = _compute_sizing_results(
        build_primary_contrasts(), rates, pooled, ALPHA_PRIMARY
    )
    feasible = [
        n[POWER_TARGETS[0]]
        for *_, n, _pooled in results
        if n[POWER_TARGETS[0]] is not None
    ]
    if not feasible:
        raise SystemExit(
            f"No PRIMARY contrast reaches {POWER_TARGETS[0]:.0%} power within "
            f"R <= {MAX_REPLICATES}; the pilot cannot size R at all."
        )
    r_star = max(feasible)
    n_censored = len(results) - len(feasible)
    return {
        "results": results,
        "r_star": r_star,
        "family_r": r_star if n_censored == 0 else None,
        "n_censored": n_censored,
        "label_w": max(len(name) for name, *_ in results),
    }


def render_primary_contrasts_table(data: dict, outcomes: CellVectors) -> None:
    """Print the PRIMARY sizing table `primary_contrasts_table` returns."""
    results = data["results"]
    print(f"Tier 2 -- PRIMARY pairwise contrasts ({N_PRIMARY} tests):")
    _print_sizing_table(
        [
            (
                "-- ladder contrasts (within family, across rungs) --",
                results[:N_LADDER_CONTRASTS],
            ),
            (
                "\n-- info-arm contrasts (within model, across info types) --",
                results[N_LADDER_CONTRASTS:],
            ),
        ],
        outcomes,
        data["label_w"],
    )


def render_omnibus_gates(rates: CellVectors, r_star: int) -> None:
    """Print each family's Tier 1 omnibus-gate power at recommended R and at R=1."""
    print(
        f"Tier 1 -- family omnibus gates: generalized CMH test (df={N_RUNGS - 1}) of "
        f"whether a family's {N_RUNGS} rungs differ at all, stratified by harmonic x "
        f"info (K={N_HARMONICS * N_INFOS}). alpha = {ALPHA_OMNIBUS:.5f}.\n"
        "A family's omnibus gate must reject before that family's Tier-2 "
        "ladder contrasts are reported as gated (rather than ungated) -- an "
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


def render_secondary_contrasts_table(
    rates: CellVectors, pooled: CellVectors, outcomes: CellVectors
) -> None:
    """Print the Tier 3 SECONDARY sizing table under the shrunk and the pooled rates."""
    results = _compute_sizing_results(
        build_secondary_contrasts(), rates, pooled, ALPHA_SECONDARY
    )
    print(
        f"Tier 3 -- SECONDARY pairwise contrasts ({N_SECONDARY} tests, "
        f"cross-family, size-matched, intens only):"
    )
    _print_sizing_table(
        [(None, results)], outcomes, max(len(name) for name, *_ in results)
    )


def render_recommended_replicates(primary: dict) -> None:
    """Print the recommended-R section from `primary_contrasts_table`'s result."""
    r_star, n_censored = primary["r_star"], primary["n_censored"]
    n_primary = len(primary["results"])
    print(
        f"Recommended replicates per condition: {r_star} -- the smallest "
        f"R at which every\n  PRIMARY contrast that is powerable within "
        f"R <= {MAX_REPLICATES} reaches {POWER_TARGETS[0]:.0%} "
        f"({n_primary - n_censored} of {n_primary}).\n"
        f"  = {r_star - 1} additional quiz runs "
        f"({(r_star - 1) * N_HARMONICS} more questions) per condition beyond "
        f"the existing pilot run."
    )
    if primary["family_r"] is None:
        print(
            f"  Whole-family sizing is CENSORED: {n_censored} of "
            f"{n_primary} PRIMARY contrasts never reached "
            f"{POWER_TARGETS[0]:.0%}\n  within "
            f"R <= {MAX_REPLICATES}, so no R in range powers the full family. "
            f"At R={r_star} they stay\n  underpowered and are reported as "
            f"such; the recommendation does not size them away."
        )
    else:
        print(
            f"  All {n_primary} PRIMARY contrasts reach "
            f"{POWER_TARGETS[0]:.0%} by "
            f"R={primary['family_r']}; the family is fully powered."
        )
    print(
        f"  The study itself collects R={N_REPLICATES} (user-locked in "
        "run_study.py, uniform across checkpoints); this prospective figure is "
        "the sizing check that decision was made against, not a superseding "
        "value.\n"
        "  This R powers the CMH sizing test, not the PRIMARY seed sign-flip; "
        "nine harmonics sharing a seed give R independent units, not 9R, so "
        "the sign-flip may need more replicates than shown here.\n"
        "  (Tier 3 / SECONDARY contrasts are exploratory and do not drive "
        "this recommendation -- see the Tier 3 table above for their own "
        "sizing.)\n"
    )


def render_equivalence_checks(
    primary_results: list[_SizingResult], rates: CellVectors, label_w: int, r_star: int
) -> None:
    """Print the Fisher cross-check at `r_star`, then TOST sizing for the near-tie PRIMARY contrasts.

    Parameters
    ----------
    primary_results : list[_SizingResult]
        PRIMARY sizing results in input order.
    rates : CellVectors
        Shrunk rates keyed by model and information type.
    label_w : int
        Contrast label column width.
    r_star : int
        Replicate count for the Fisher cross-check.
    """
    print(
        f"Cross-check at R={r_star} (pooled two-sided Fisher exact, PRIMARY "
        f"alpha={ALPHA_PRIMARY:.6f}):"
    )
    for name, key_a, key_b, needed, _pooled in primary_results:
        if needed[POWER_TARGETS[0]] is not None:
            p_fisher = fisher_check(
                rates[key_a], rates[key_b], r_star, np.random.default_rng(SEED)
            )
            print(f"  {name:{label_w}s} fisher power = {p_fisher:.3f}")

    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed, _pooled in primary_results
        if needed[POWER_TARGETS[0]] is None or needed[POWER_TARGETS[0]] > NEAR_TIE_R
    ]
    n_ties = len(near_ties)
    print()
    if not n_ties:
        print(
            f"No near-tie PRIMARY contrasts (all reached "
            f"{POWER_TARGETS[0]:.0%} power within "
            f"R({POWER_TARGETS[0]:.0%}) <= {NEAR_TIE_R}) -- skipping TOST equivalence "
            "sizing."
        )
        return
    # Correct the planned equivalence family.
    alpha_eq = ALPHA / n_ties
    eq_header = f"{'contrast':{label_w}s} " + " ".join(
        f"{f'R(d={d:.2f})':>10s}" for d in EQUIVALENCE_DELTAS
    )
    print(
        "Equivalence (TOST) sizing for near-tie PRIMARY contrasts, "
        f"assuming a true tie at the contrasts' mean rate (alpha="
        f"{ALPHA}/{n_ties} = {alpha_eq:.4f} per one-sided test, "
        f"Bonferroni over the {n_ties}-test family; "
        f"{POWER_TARGETS[0]:.0%} power):\n{eq_header}\n{'-' * len(eq_header)}"
    )
    for name, key_a, key_b in near_ties:
        cells = [
            equivalence_replicates(
                rates[key_a],
                rates[key_b],
                delta,
                np.random.default_rng(SEED),
                alpha=alpha_eq,
            )
            for delta in EQUIVALENCE_DELTAS
        ]
        print(f"{name:{label_w}s} " + " ".join(f"{_fmt_r(c):>10s}" for c in cells))


def render_interaction_diagnostic(rates: CellVectors, r_star: int) -> None:
    """Print `omnibus_interaction_power` at recommended R and at R=1."""
    print(
        f"\nOmnibus model x info-type interaction (logit LR test, harmonic "
        f"fixed effects, alpha={ALPHA}, df={DF_INTERACTION}, "
        f"{N_SIMS_OMNIBUS_DIAGNOSTIC} sims; design-level diagnostic, not a gate) "
        f"at R={r_star}: power = {omnibus_interaction_power(rates, r_star):.3f}\n"
        f"  ... at the current R=1: power = {omnibus_interaction_power(rates, 1):.3f}"
    )


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Run and print the family-ladder power analysis."""
    outcomes = load_outcomes(results_dir)
    rates = {key: shrunk_rates(y) for key, y in outcomes.items()}
    pooled = {key: np.full(N_HARMONICS, y.mean()) for key, y in outcomes.items()}

    render_observed_accuracy(outcomes)
    render_design_banner()

    # Reuse PRIMARY results for gates and recommendation.
    primary = primary_contrasts_table(rates, pooled)
    r_star = primary["r_star"]

    render_omnibus_gates(rates, r_star)
    render_primary_contrasts_table(primary, outcomes)
    render_secondary_contrasts_table(rates, pooled, outcomes)
    render_recommended_replicates(primary)

    render_equivalence_checks(primary["results"], rates, primary["label_w"], r_star)
    render_interaction_diagnostic(rates, r_star)


if __name__ == "__main__":
    main()
