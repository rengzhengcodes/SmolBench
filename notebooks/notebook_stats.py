"""Shared induction posterior-power and bootstrap estimators."""

from __future__ import annotations

import collections
import math
from collections.abc import Callable, Sequence
from itertools import combinations
from typing import Any

import numpy as np
from scipy.stats import binomtest, norm

MIN_R_FOR_EQUIVALENCE = 5
DEFAULT_MEI = 0.05
BOOT_TAIL_TARGET = 50
BOOT_RESAMPLE_CAP = 200000
CLUSTER_SD = 1.4
CAL_N_SIM = 4000
CAL_CLUSTER_SDS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, CLUSTER_SD)
_BOOT_CAP_WARNED: set[float] = set()

#: Independent streams make sweep drift measure Monte-Carlo error, not seed luck.
B_GRID = (1_000, 5_000, 20_000, 50_000, 100_000, 200_000, 500_000)

#: Batching bounds peak memory to ``CHUNK * n_blocks * n_models * 4`` bytes.
CHUNK = 2_000

#: 0.0005 cannot change a rate printed to 3 decimals.
DRIFT_TOL = 0.0005


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
    return len(infos) * math.comb(len(models), 2) + len(models) * math.comb(
        len(infos), 2
    )


def build_posterior_contrasts(
    models: Sequence[str], infos: Sequence[str]
) -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
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
            out.append(
                (f"[{info}] {model_a} vs {model_b}", (model_a, info), (model_b, info))
            )
    for model in models:
        for info_a, info_b in combinations(infos, 2):
            out.append(
                (f"[{model}] {info_a} vs {info_b}", (model, info_a), (model, info_b))
            )
    return out


def classify(
    p: float,
    ci_lo: float,
    ci_hi: float,
    mei: float,
    r_min: int,
    alpha: float,
    min_r: int = MIN_R_FOR_EQUIVALENCE,
) -> str:
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
        return "DECIDED"
    if ci_lo > -mei and ci_hi < mei and (r_min >= min_r):
        return "EQUIVALENT"
    return "UNDECIDED"


def boot_resamples(
    alpha: float, target: int = BOOT_TAIL_TARGET, cap: int = BOOT_RESAMPLE_CAP
) -> int:
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
        print(
            f"WARNING: alpha={alpha:.6g} wants {wanted} resamples for {target} draws in each tail; capping at {cap}. The interval endpoints are NOT resolved to this alpha -- at the cap only {cap * tail:.3g} resamples land in the tail an endpoint is read from. Raising the cap would not fix it: see the resample sweep below, where no B on B_GRID reaches DRIFT_TOL at this alpha, and the R = 30 block-count note beside it for why."
        )
    return cap


def _bca_bounds(
    theta_star: np.ndarray, theta_hat: float, jack: np.ndarray, alpha: float
) -> tuple[float, float, bool]:
    """Compute BCa interval endpoints.

    Parameters
    ----------
    theta_star : np.ndarray
        Bootstrap values.
    theta_hat : float
        Full-sample value.
    jack : np.ndarray
        One value per replicate block.
    alpha : float
        Two-sided error rate.

    Returns
    -------
    tuple[float, float, bool]
        Lower, upper, and percentile-fallback flag for undefined z0.
    """
    lo_pct, hi_pct = np.percentile(theta_star, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    prop = float(np.mean(theta_star < theta_hat))
    if prop <= 0.0 or prop >= 1.0:
        return float(lo_pct), float(hi_pct), True  # z0 undefined -> percentile
    z0 = norm.ppf(prop)
    jbar = jack.mean()
    num = float(np.sum((jbar - jack) ** 3))
    den = 6.0 * float(np.sum((jbar - jack) ** 2)) ** 1.5
    a = num / den if den > 0 else 0.0
    out = []
    for z in (norm.ppf(alpha / 2), norm.ppf(1 - alpha / 2)):
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        out.append(float(np.percentile(theta_star, 100 * norm.cdf(adj))))
    return out[0], out[1], False


# pylint: disable=use-dict-literal
def bootstrap_stats(
    succ: np.ndarray, size: np.ndarray, B: int, seed: int, alpha: float = 0.05
) -> dict:
    """Compute block-bootstrap marginal rates and BCa intervals.

    Each resample is a ratio estimator because its cell count varies with the block draw.

    Parameters
    ----------
    succ : np.ndarray
        Per-block success counts.
    size : np.ndarray
        Per-block cell counts.
    B : int
        Bootstrap resamples.
    seed : int
        RNG seed.
    alpha : float, optional
        Two-sided error rate.

    Returns
    -------
    dict
        Bootstrap arrays and marginal summaries; `star_rate` retains shared draws for `diff_ci`.
    """
    n_thm, n_mod = succ.shape
    rng = np.random.default_rng(seed)

    # Chunking avoids a roughly 90-GB intermediate at B=500k.
    star_rate = np.empty((B, n_mod), dtype=np.float64)
    done = 0
    while done < B:
        chunk = min(CHUNK, B - done)
        idx = rng.integers(0, n_thm, size=(chunk, n_thm))
        star_rate[done : done + chunk] = (
            succ[idx].sum(axis=1) / size[idx].sum(axis=1)[:, None]
        )
        done += chunk

    # The BCa acceleration jackknifes replicate blocks.
    tot_succ, tot_size = succ.sum(axis=0), size.sum()
    jack = (tot_succ - succ) / (tot_size - size)[:, None]  # (n_thm, n_models)

    theta_hat = tot_succ / tot_size
    marg = {}
    for j in range(n_mod):
        lo, hi, fb = _bca_bounds(
            star_rate[:, j], float(theta_hat[j]), jack[:, j], alpha
        )
        p_lo, p_hi = np.percentile(
            star_rate[:, j], [100 * alpha / 2, 100 * (1 - alpha / 2)]
        )
        marg[j] = dict(
            rate=float(theta_hat[j]),
            lo=lo,
            hi=hi,
            pct_lo=float(p_lo),
            pct_hi=float(p_hi),
            se=float(star_rate[:, j].std(ddof=1)),
            fallback=fb,
        )
    return dict(
        star_rate=star_rate, jack=jack, theta_hat=theta_hat, marginal=marg, alpha=alpha
    )


def diff_ci(bs: dict, ja: int, jb: int) -> dict:
    """Compute the paired BCa interval for rate(b) - rate(a).

    Differencing within each resample cancels the shared block draw.

    Parameters
    ----------
    bs : dict
        Bootstrap statistics.
    ja : int
        Baseline column.
    jb : int
        Comparison column.

    Returns
    -------
    dict
        Difference, BCa bounds, standard error, and fallback flag.
    """
    star = bs["star_rate"][:, jb] - bs["star_rate"][:, ja]
    hat = float(bs["theta_hat"][jb] - bs["theta_hat"][ja])
    jack = bs["jack"][:, jb] - bs["jack"][:, ja]
    lo, hi, fb = _bca_bounds(star, hat, jack, bs["alpha"])
    return dict(diff=hat, lo=lo, hi=hi, se=float(star.std(ddof=1)), fallback=fb)


# pylint: enable=use-dict-literal
def paired_diff_ci(
    a: np.ndarray,
    b: np.ndarray,
    seed_idx: np.ndarray,
    alpha: float,
    n_boot: int | None = None,
    seed: int = 0,
) -> dict[str, float]:
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

    Returns
    -------
    dict[str, float]
        Difference and confidence-interval fields from ``diff_ci``."""
    n_boot = boot_resamples(alpha) if n_boot is None else n_boot
    seeds = np.unique(seed_idx)
    succ = np.array(
        [[a[seed_idx == value].sum(), b[seed_idx == value].sum()] for value in seeds],
        dtype=float,
    )
    size = np.array([(seed_idx == value).sum() for value in seeds], dtype=float)
    stats = bootstrap_stats(succ, size, B=n_boot, seed=seed, alpha=alpha)
    return diff_ci(stats, 1, 0)


def synth(
    rate: float,
    n_seeds: int,
    gen: np.random.Generator,
    cluster_sd: float = 0.0,
    *,
    n_harm: int,
) -> tuple[np.ndarray, np.ndarray]:
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
        raise ValueError(f"synth: cluster_sd must be >= 0, got {cluster_sd}")
    if cluster_sd == 0:
        marks = gen.random((n_seeds, n_harm)) < rate
    else:
        if not 0.0 < rate < 1.0:
            raise ValueError(
                f"synth: clustering applies the offset on the logit scale, so rate must be strictly inside (0, 1), got {rate}"
            )
        offset = gen.normal(0.0, cluster_sd, size=n_seeds)
        p_rep = 1.0 / (1.0 + np.exp(-(np.log(rate / (1.0 - rate)) + offset)))
        marks = gen.random((n_seeds, n_harm)) < p_rep[:, None]
    return (marks.reshape(-1), np.repeat(np.arange(n_seeds), n_harm))


def resample_sweep(
    a: np.ndarray,
    b: np.ndarray,
    seed_idx: np.ndarray,
    alpha: float,
    grid: Sequence[int] | None = None,
) -> list[dict[str, float | int | None]]:
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
        Resample counts, or ``None`` for ``B_GRID``.

    Returns
    -------
    list[dict[str, float | int | None]]
        Interval endpoints, drift, and expected tail count per grid point."""
    counts = B_GRID if grid is None else grid
    rows: list[dict[str, float | int | None]] = []
    prev: tuple[float, float] | None = None
    for index, n_boot in enumerate(counts):
        ci = paired_diff_ci(a, b, seed_idx, alpha, n_boot, 1000 + index)
        drift = (
            None
            if prev is None
            else max(abs(ci["lo"] - prev[0]), abs(ci["hi"] - prev[1]))
        )
        rows.append(
            {
                "B": n_boot,
                "lo": ci["lo"],
                "hi": ci["hi"],
                "drift": drift,
                "expected_tail": n_boot * alpha / 2,
            }
        )
        prev = (ci["lo"], ci["hi"])
    return rows


# Inspect the function's global reads so a literal grid cannot silently replace
# the module's shared tuning contract.
assert "B_GRID" in resample_sweep.__code__.co_names


def _true_null_draws(
    cluster_sd: float,
    n_sim: int,
    r: int,
    rate: float,
    gen: np.random.Generator,
    measure: Callable[[float, np.ndarray, np.ndarray, np.ndarray], Any],
    who: str,
    *,
    n_harm: int,
    paired: Any,
) -> tuple[list[Any], float]:
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
    harm_idx = np.tile(np.arange(n_harm), r)
    for _ in range(n_sim):
        a, seed_idx = synth(rate, r, gen, cluster_sd, n_harm=n_harm)
        b, _ = synth(rate, r, gen, cluster_sd, n_harm=n_harm)
        p = paired.cmh_unpaired_p(a, b, harm_idx)
        measured.append(measure(p, a, b, seed_idx))
        deff = paired.design_effect(a, b, seed_idx, harm_idx)
        if deff is not None:
            deffs.append(deff)
    if not deffs:
        raise ValueError(
            f"{who}: design_effect returned None for all {n_sim} draws at cluster_sd={cluster_sd}, so the clustering this cell claims to measure cannot be verified"
        )
    return (measured, float(np.median(deffs)))


def verdict_distribution(
    cluster_sd: float,
    n_sim: int = 60,
    rate: float = 0.5,
    n_seeds: int = 40,
    mei: float = 0.15,
    alpha: float = 0.05,
    seed: int = 20260904,
    *,
    n_harm: int,
    paired: Any,
) -> dict[str, Any]:
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
        ci = paired_diff_ci(a, b, seed_idx, 2 * alpha, seed=0)
        return classify(p, ci["lo"], ci["hi"], mei, n_seeds, alpha)

    verdicts, median_deff = _true_null_draws(
        cluster_sd,
        n_sim,
        n_seeds,
        rate,
        np.random.default_rng(seed),
        verdict,
        "verdict_distribution",
        n_harm=n_harm,
        paired=paired,
    )
    return {
        "verdicts": collections.Counter(verdicts),
        "median_deff": median_deff,
        "n_sim": n_sim,
    }


def false_decided_rate(
    cluster_sd: float,
    n_sim: int,
    *,
    r: int,
    alpha: float,
    n_harm: int,
    paired: Any,
    rate: float = 0.5,
    seed: int = 20260906,
    gen: np.random.Generator | None = None,
) -> dict[str, Any]:
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
    draws, median_deff = _true_null_draws(
        cluster_sd,
        n_sim,
        r,
        rate,
        active_gen,
        lambda p, *_: p < alpha,
        "false_decided_rate",
        n_harm=n_harm,
        paired=paired,
    )
    decided = int(sum(draws))
    interval = binomtest(decided, n_sim).proportion_ci(
        confidence_level=0.95, method="exact"
    )
    return {
        "cluster_sd": cluster_sd,
        "r": r,
        "alpha": alpha,
        "n_sim": n_sim,
        "decided": decided,
        "rate": decided / n_sim,
        "median_deff": median_deff,
        "ci_lo": interval.low,
        "ci_hi": interval.high,
        "inflated": interval.low > alpha,
    }
