"""Keep shared estimators explicit to prevent import and notebook-copy drift."""
from __future__ import annotations
import collections
import math
import random
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from itertools import combinations
from typing import Any
import numpy as np
from scipy.stats import binomtest
from smolbench.deduction.lean import runner
MIN_R_FOR_EQUIVALENCE = 5
DEFAULT_MEI = 0.05
BOOT_TAIL_TARGET = 50
BOOT_RESAMPLE_CAP = 200000
CLUSTER_SD = 1.4
CAL_N_SIM = 4000
CAL_CLUSTER_SDS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, CLUSTER_SD)
UNGRADED_VERDICT = 'unverified'
_DEPENDENCY_PACKAGE_MARKER = '.lake/packages/'
_BOOT_CAP_WARNED: set[float] = set()
PASS_AT_1_SE_CAVEAT = "Normal-approximation SE (and the Clopper-Pearson CI) assume independent cells. Several cells in this sample can share a theorem (different rungs/replicates of it), which this estimate does not account for -- see flip_stats' docstring Notes. Treat as a rough, likely-too-narrow bound, not exact."

def posterior_family(models: Sequence[str], infos: Sequence[str]) -> int:
    """Count all model-within-info and info-within-model pairs.


Parameters
----------
models : Sequence[str]
    Model names.
infos : Sequence[str]
    Information-arm names.

Returns
-------
int
    Number of pairwise contrasts."""
    return len(infos) * math.comb(len(models), 2) + len(models) * math.comb(len(infos), 2)

def build_posterior_contrasts(models: Sequence[str], infos: Sequence[str]) -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build every labelled contrast in the posterior family.


Parameters
----------
models : Sequence[str]
    Model names.
infos : Sequence[str]
    Information-arm names.

Returns
-------
list[tuple[str, tuple[str, str], tuple[str, str]]]
    Label and two condition keys for each contrast."""
    out = []
    for info in infos:
        for model_a, model_b in combinations(models, 2):
            out.append((f'[{info}] {model_a} vs {model_b}', (model_a, info), (model_b, info)))
    for model in models:
        for info_a, info_b in combinations(infos, 2):
            out.append((f'[{model}] {info_a} vs {info_b}', (model, info_a), (model, info_b)))
    return out

def classify(p: float, ci_lo: float, ci_hi: float, mei: float, r_min: int, alpha: float, min_r: int=MIN_R_FOR_EQUIVALENCE) -> str:
    """Classify one contrast as decided, equivalent, or undecided.


Parameters
----------
p : float
    Contrast p-value.
ci_lo : float
    Lower confidence bound for the effect.
ci_hi : float
    Upper confidence bound for the effect.
mei : float
    Minimum effect of interest.
r_min : int
    Smaller arm's replicate count.
alpha : float
    Decision threshold.
min_r : int
    Minimum replicates required for equivalence.

Returns
-------
str
    ``DECIDED``, ``EQUIVALENT``, or ``UNDECIDED``."""
    if p < alpha:
        return 'DECIDED'
    if ci_lo > -mei and ci_hi < mei and (r_min >= min_r):
        return 'EQUIVALENT'
    return 'UNDECIDED'

def boot_resamples(alpha: float, target: int=BOOT_TAIL_TARGET, cap: int=BOOT_RESAMPLE_CAP) -> int:
    """Derive a bootstrap count from the two-sided interval level.


Parameters
----------
alpha : float
    Two-sided interval error rate.
target : int
    Target draws in each tail.
cap : int
    Maximum affordable resample count.

Returns
-------
int
    Derived count, bounded by ``cap``."""
    tail = alpha / 2
    wanted = math.ceil(target / tail)
    if wanted <= cap:
        return wanted
    if alpha not in _BOOT_CAP_WARNED:
        _BOOT_CAP_WARNED.add(alpha)
        print(f'WARNING: alpha={alpha:.6g} wants {wanted} resamples for {target} draws in each tail; capping at {cap}. The interval endpoints are NOT resolved to this alpha -- at the cap only {cap * tail:.3g} resamples land in the tail an endpoint is read from. Raising the cap would not fix it: see the resample sweep below, where no B on error_bars.B_GRID reaches error_bars.DRIFT_TOL at this alpha, and the R = 30 block-count note beside it for why.')
    return cap

def paired_diff_ci(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray, alpha: float, n_boot: int | None=None, seed: int=0, *, error_bars: Any) -> dict[str, float]:
    """Bootstrap ``a - b`` while resampling replicate blocks.


Parameters
----------
a : np.ndarray
    First arm's outcome marks.
b : np.ndarray
    Second arm's outcome marks.
seed_idx : np.ndarray
    Replicate-block index aligned with both arms.
alpha : float
    Two-sided interval error rate.
n_boot : int or None
    Resample count, or ``None`` to derive it from ``alpha``.
seed : int
    Bootstrap random seed.
error_bars : Any
    Deduction error-bar module.

Returns
-------
dict[str, float]
    Difference and confidence-interval fields from ``diff_ci``."""
    n_boot = boot_resamples(alpha) if n_boot is None else n_boot
    seeds = np.unique(seed_idx)
    succ = np.array([[a[seed_idx == value].sum(), b[seed_idx == value].sum()] for value in seeds], dtype=float)
    size = np.array([(seed_idx == value).sum() for value in seeds], dtype=float)
    stats = error_bars.bootstrap_stats(succ, size, B=n_boot, seed=seed, alpha=alpha)
    return error_bars.diff_ci(stats, 1, 0)

def synth(rate: float, n_seeds: int, gen: np.random.Generator, cluster_sd: float=0.0, *, n_harm: int) -> tuple[np.ndarray, np.ndarray]:
    """Draw flat marks and their replicate indices.


Parameters
----------
rate : float
    Marginal success probability.
n_seeds : int
    Number of replicate blocks.
gen : np.random.Generator
    Random-number generator.
cluster_sd : float
    Standard deviation of the replicate-level logit offset.
n_harm : int
    Harmonic cells per replicate.

Returns
-------
tuple[np.ndarray, np.ndarray]
    Flat Boolean marks and aligned replicate indices.

Raises
------
ValueError
    If ``cluster_sd`` is negative or clustering is requested at a boundary"""
    if cluster_sd < 0:
        raise ValueError(f'synth: cluster_sd must be >= 0, got {cluster_sd}')
    if cluster_sd == 0:
        marks = gen.random((n_seeds, n_harm)) < rate
    else:
        if not 0.0 < rate < 1.0:
            raise ValueError(f'synth: clustering applies the offset on the logit scale, so rate must be strictly inside (0, 1), got {rate}')
        offset = gen.normal(0.0, cluster_sd, size=n_seeds)
        p_rep = 1.0 / (1.0 + np.exp(-(np.log(rate / (1.0 - rate)) + offset)))
        marks = gen.random((n_seeds, n_harm)) < p_rep[:, None]
    return (marks.reshape(-1), np.repeat(np.arange(n_seeds), n_harm))

def resample_sweep(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray, alpha: float, grid: Sequence[int] | None=None, *, error_bars: Any) -> list[dict[str, float | int | None]]:
    """Measure interval-endpoint drift over resample counts.


Parameters
----------
a : np.ndarray
    First arm's outcome marks.
b : np.ndarray
    Second arm's outcome marks.
seed_idx : np.ndarray
    Replicate-block index aligned with both arms.
alpha : float
    Two-sided interval error rate.
grid : Sequence[int] or None
    Resample counts, or ``None`` for ``error_bars.B_GRID``.
error_bars : Any
    Deduction error-bar module.

Returns
-------
list[dict[str, float | int | None]]
    Interval endpoints, drift, and expected tail count per grid point."""
    counts = error_bars.B_GRID if grid is None else grid
    rows: list[dict[str, float | int | None]] = []
    prev: tuple[float, float] | None = None
    for index, n_boot in enumerate(counts):
        ci = paired_diff_ci(a, b, seed_idx, alpha, n_boot, 1000 + index, error_bars=error_bars)
        drift = None if prev is None else max(abs(ci['lo'] - prev[0]), abs(ci['hi'] - prev[1]))
        rows.append({'B': n_boot, 'lo': ci['lo'], 'hi': ci['hi'], 'drift': drift, 'expected_tail': n_boot * alpha / 2})
        prev = (ci['lo'], ci['hi'])
    return rows

# Inspect the function's global reads so a literal grid cannot silently replace
# the error-bars module's shared tuning contract.
assert 'B_GRID' in resample_sweep.__code__.co_names

def _true_null_draws(cluster_sd: float, n_sim: int, r: int, rate: float, gen: np.random.Generator, measure: Callable[[float, np.ndarray, np.ndarray, np.ndarray], Any], who: str, *, n_harm: int, paired: Any) -> tuple[list[Any], float]:
    """Simulate true-null contrasts and measure their design effect.


Parameters
----------
cluster_sd : float
    Standard deviation of the replicate-level logit offset.
n_sim : int
    Number of simulated contrasts.
r : int
    Replicate blocks per arm.
rate : float
    Shared true-null success probability.
gen : np.random.Generator
    Random-number generator.
measure : Callable[[float, np.ndarray, np.ndarray, np.ndarray], Any]
    Statistic computed from each draw.
who : str
    Caller name for diagnostic errors.
n_harm : int
    Harmonic cells per replicate.
paired : Any
    Paired-analysis module.

Returns
-------
tuple[list[Any], float]
    Measurements and median measurable design effect.

Raises
------
ValueError
    If no draw has a measurable design effect."""
    measured, deffs = ([], [])
    for _ in range(n_sim):
        a, seed_idx = synth(rate, r, gen, cluster_sd, n_harm=n_harm)
        b, _ = synth(rate, r, gen, cluster_sd, n_harm=n_harm)
        measured.append(measure(paired.cmh_unpaired_p(a, b, seed_idx), a, b, seed_idx))
        deff = paired.design_effect(a, b, seed_idx)
        if deff is not None:
            deffs.append(deff)
    if not deffs:
        raise ValueError(f'{who}: design_effect returned None for all {n_sim} draws at cluster_sd={cluster_sd}, so the clustering this cell claims to measure cannot be verified')
    return (measured, float(np.median(deffs)))

def verdict_distribution(cluster_sd: float, n_sim: int=60, rate: float=0.5, n_seeds: int=40, mei: float=0.15, alpha: float=0.05, seed: int=20260904, *, n_harm: int, paired: Any, error_bars: Any) -> dict[str, Any]:
    """Tally posterior verdicts over repeated true-null contrasts.


Parameters
----------
cluster_sd : float
    Standard deviation of the replicate-level logit offset.
n_sim : int
    Number of simulated contrasts.
rate : float
    Shared true-null success probability.
n_seeds : int
    Replicate blocks per arm.
mei : float
    Minimum effect of interest.
alpha : float
    Decision threshold.
seed : int
    Simulation random seed.
n_harm : int
    Harmonic cells per replicate.
paired : Any
    Paired-analysis module.
error_bars : Any
    Deduction error-bar module.

Returns
-------
dict[str, Any]
    Verdict counts, median design effect, and simulation count."""

    def verdict(p: float, a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> str:
        """Classify one simulated contrast.


Parameters
----------
p : float
    Contrast p-value.
a : np.ndarray
    First arm's outcome marks.
b : np.ndarray
    Second arm's outcome marks.
seed_idx : np.ndarray
    Replicate-block index aligned with both arms.

Returns
-------
str
    Posterior verdict."""
        ci = paired_diff_ci(a, b, seed_idx, 2 * alpha, seed=0, error_bars=error_bars)
        return classify(p, ci['lo'], ci['hi'], mei, n_seeds, alpha)
    verdicts, median_deff = _true_null_draws(cluster_sd, n_sim, n_seeds, rate, np.random.default_rng(seed), verdict, 'verdict_distribution', n_harm=n_harm, paired=paired)
    return {'verdicts': collections.Counter(verdicts), 'median_deff': median_deff, 'n_sim': n_sim}

def false_decided_rate(cluster_sd: float, n_sim: int, *, r: int, alpha: float, n_harm: int, paired: Any, rate: float=0.5, seed: int=20260906, gen: np.random.Generator | None=None) -> dict[str, Any]:
    """Measure the false-decided rate of clustered true-null contrasts.


Parameters
----------
cluster_sd : float
    Standard deviation of the replicate-level logit offset.
n_sim : int
    Number of simulated contrasts.
r : int
    Replicate blocks per arm.
alpha : float
    Decision threshold.
n_harm : int
    Harmonic cells per replicate.
paired : Any
    Paired-analysis module.
rate : float
    Shared true-null success probability.
seed : int
    Simulation random seed.
gen : np.random.Generator or None
    Generator override, or ``None`` to construct one from ``seed``.

Returns
-------
dict[str, Any]
    Count, rate, interval, design effect, and inflation verdict."""
    active_gen = np.random.default_rng(seed) if gen is None else gen
    draws, median_deff = _true_null_draws(cluster_sd, n_sim, r, rate, active_gen, lambda p, *_: p < alpha, 'false_decided_rate', n_harm=n_harm, paired=paired)
    decided = int(sum(draws))
    interval = binomtest(decided, n_sim).proportion_ci(confidence_level=0.95, method='exact')
    return {'cluster_sd': cluster_sd, 'r': r, 'alpha': alpha, 'n_sim': n_sim, 'decided': decided, 'rate': decided / n_sim, 'median_deff': median_deff, 'ci_lo': interval.low, 'ci_hi': interval.high, 'inflated': interval.low > alpha}

def group_rows_by_cell(rows: Iterable[dict[str, Any]]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    """Group cell rows by key while preserving file order.


Parameters
----------
rows : Iterable[dict[str, Any]]
    Result records, including non-cell rows to ignore.

Returns
-------
dict[tuple[Any, ...], list[dict[str, Any]]]
    Cell key to all of its rows."""
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        if row.get('kind') != 'cell':
            continue
        key = runner._row_key(row.get('model', ''), row.get('theorem_id', ''), int(row.get('k', -1)), row.get('rung', ''), int(row.get('replicate_idx', -1)))
        grouped.setdefault(key, []).append(row)
    return grouped

def surviving_verdict(verdicts: Iterable[str | None], unmeasurable: Collection[str]) -> str | None:
    """Return the first verdict outside the live unmeasurable set.


Parameters
----------
verdicts : Iterable[str | None]
    Verdicts in attempt order.
unmeasurable : Collection[str]
    Verdicts excluded by the live grader.

Returns
-------
str or None
    First surviving verdict, or ``None``."""
    return next((verdict for verdict in verdicts if verdict not in unmeasurable), None)

def is_mathlib_cell(row: Mapping[str, Any]) -> bool:
    """Identify a Mathlib theorem rather than a vendored Lake dependency.


Parameters
----------
row : Mapping[str, Any]
    Cell row carrying an optional file path.

Returns
-------
bool
    ``False`` only for paths below ``.lake/packages``."""
    return not str(row.get('file_path') or '').startswith(_DEPENDENCY_PACKAGE_MARKER)

def measurable_cell_keys(rows: Iterable[dict[str, Any]], unmeasurable: Collection[str]) -> list[tuple[Any, ...]]:
    """Select sorted Mathlib cell keys with a measured verdict.


Parameters
----------
rows : Iterable[dict[str, Any]]
    Result records, including non-cell rows to ignore.
unmeasurable : Collection[str]
    Verdicts excluded by the live grader.

Returns
-------
list[tuple[Any, ...]]
    Deterministically sorted measurable Mathlib keys."""
    keys: list[tuple] = []
    for key, group in group_rows_by_cell(rows).items():
        verdict = surviving_verdict((row.get('verdict') for row in group), unmeasurable)
        if verdict is None or verdict == UNGRADED_VERDICT or (not is_mathlib_cell(group[0])):
            continue
        keys.append(key)
    return sorted(keys)

def select_sample_keys(measurable: Sequence[tuple[Any, ...]], n: int, seed: int) -> list[tuple[Any, ...]]:
    """Draw a reproducible sample from an already-sorted population.


Parameters
----------
measurable : Sequence[tuple[Any, ...]]
    Deterministically ordered eligible keys.
n : int
    Sample size.
seed : int
    Sampling random seed.

Returns
-------
list[tuple[Any, ...]]
    Sampled keys."""
    return random.Random(seed).sample(list(measurable), n)

def clopper_pearson_interval(k: int, n: int, alpha: float=0.05) -> tuple[float, float]:
    """Calculate an exact two-sided Clopper-Pearson interval.


Parameters
----------
k : int
    Success count.
n : int
    Trial count.
alpha : float
    Two-sided interval error rate.

Returns
-------
tuple[float, float]
    Lower and upper probability bounds.

Raises
------
ValueError
    If ``n`` is non-positive or ``k`` is outside ``[0, n]``."""
    if n <= 0:
        raise ValueError(f'clopper_pearson_interval: n must be positive, got {n}')
    if not 0 <= k <= n:
        raise ValueError(f'clopper_pearson_interval: k must be in [0, {n}], got {k}')
    lower = 0.0
    if k:
        lo, hi = (0.0, 1.0)
        for _ in range(100):
            mid = (lo + hi) / 2
            cdf = sum((math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k)))
            lo, hi = (mid, hi) if cdf > 1 - alpha / 2 else (lo, mid)
        lower = (lo + hi) / 2
    upper = 1.0
    if k < n:
        lo, hi = (0.0, 1.0)
        for _ in range(100):
            mid = (lo + hi) / 2
            cdf = sum((math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k + 1)))
            lo, hi = (mid, hi) if cdf > alpha / 2 else (lo, mid)
        upper = (lo + hi) / 2
    return (lower, upper)

def is_pass(verdict: str) -> bool:
    """Return whether a measured verdict is exactly ``success``.


Parameters
----------
verdict : str
    Measured grader verdict.

Returns
-------
bool
    Whether the verdict is a success.

Raises
------
ValueError
    If the verdict is the generation-time ungraded sentinel."""
    if verdict == UNGRADED_VERDICT:
        raise ValueError(f'is_pass: verdict is "{UNGRADED_VERDICT}" -- the generation-time sentinel for an ungraded row, not a graded outcome. Filter ungraded rows out before calling is_pass (see measurable_cell_keys).')
    return verdict == 'success'

def flip_stats(pairs: Mapping[tuple[Any, ...], tuple[str, str]]) -> dict[str, Any]:
    """Calculate McNemar-style flip statistics for paired verdicts.


Parameters
----------
pairs : Mapping[tuple[Any, ...], tuple[str, str]]
    Cell keys mapped to original and rerun verdicts.

Returns
-------
dict[str, Any]
    Contingency counts, flip rate, interval, standard error, and keys."""
    n = len(pairs)
    a = b = c = d = 0
    flipped_keys: list[tuple] = []
    for key, (original_verdict, rerun_verdict) in pairs.items():
        original, rerun = (is_pass(original_verdict), is_pass(rerun_verdict))
        if original and rerun:
            a += 1
        elif original:
            b += 1
            flipped_keys.append(key)
        elif rerun:
            c += 1
            flipped_keys.append(key)
        else:
            d += 1
    discordant = b + c
    flip_rate = discordant / n if n else 0.0
    ci_lo, ci_hi = clopper_pearson_interval(discordant, n) if n else (0.0, 0.0)
    se = math.sqrt(flip_rate * (1 - flip_rate) / n) if n else 0.0
    return {'n': n, 'a_both_pass': a, 'b_orig_pass_rerun_fail': b, 'c_orig_fail_rerun_pass': c, 'd_both_fail': d, 'discordant': discordant, 'flip_rate': flip_rate, 'flip_rate_ci95': [ci_lo, ci_hi], 'pass_at_1_se': se, 'pass_at_1_se_caveat': PASS_AT_1_SE_CAVEAT, 'flipped_keys': [list(key) for key in flipped_keys]}

def verifier_drift_stats(pairs: Mapping[tuple[Any, ...], tuple[str, str]]) -> dict[str, Any]:
    """Measure exact verdict-text agreement after reverification.


Parameters
----------
pairs : Mapping[tuple[Any, ...], tuple[str, str]]
    Cell keys mapped to study and reverified verdicts.

Returns
-------
dict[str, Any]
    Agreement count, rate, and disagreement records."""
    disagreements = [{'key': list(key), 'study_verdict': study, 'reverified_verdict': reverified} for key, (study, reverified) in pairs.items() if study != reverified]
    agree = len(pairs) - len(disagreements)
    return {'n': len(pairs), 'agree': agree, 'agreement_rate': agree / len(pairs) if pairs else 0.0, 'disagreements': disagreements}
