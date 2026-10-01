"""Pre-registered induction design.

Roster, contrast tiers, correction thresholds, and the CMH/McNemar/GCMH kernels
the tiers are evaluated with.
"""

import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Union

# Bare-name imports: sibling scripts from this directory, ``_power_common`` from ``notebooks/``.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import ALPHA
from scipy.stats import binom, chi2

from smolbench.evals.results_store import repo_root
from smolbench.evals.study_config import load_study_config
from smolbench.induction.periodic import CONDITIONS

# The committed study_config.toml, the same declaration run_study.py collects
# with; each value's rationale is written beside it there.
_CONFIG = load_study_config()

# Analysis tags in ladder order, which is the roster's declaration order.
FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(_CONFIG.roster.tags[key] for key in rungs)
    for family, rungs in _CONFIG.roster.families.items()
}
MODELS = tuple(rung for rungs in FAMILIES.values() for rung in rungs)

# Arm names in the order run_study collects them.
INFOS = tuple(CONDITIONS)
# Mirrors ``Experiment.results_dir``: notebooks/<study>/results is the path
# ``experiment_name`` parses into the S3 key, so it derives from the study name.
RESULTS_DIR = repo_root() / "notebooks" / "induction" / "results"
BASE_SEED = _CONFIG.study.base_seed
N_REPLICATES = _CONFIG.study.n_replicates
N_HARMONICS = _CONFIG.study.n_harmonics

N_RUNGS = _CONFIG.roster.n_rungs
N_INFOS = len(INFOS)
N_FAMILIES = len(FAMILIES)
N_LADDERS = N_FAMILIES * N_INFOS
N_LADDER_CONTRASTS = N_LADDERS * math.comb(N_RUNGS, 2)
N_INFO_CONTRASTS = len(MODELS) * math.comb(N_INFOS, 2)
N_PRIMARY = N_LADDER_CONTRASTS + N_INFO_CONTRASTS
ALPHA_PRIMARY = ALPHA / N_PRIMARY

#: BH's FDR level is the familywise level; a separate knob would need its own derivation.
Q_SECONDARY = ALPHA
N_SECONDARY = N_RUNGS * math.comb(N_FAMILIES, 2)
# Size BH contrasts at the conservative rank-1 threshold.
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

ALPHA_OMNIBUS = ALPHA / N_FAMILIES

#: ``(label, cell_a, cell_b)``: the two cells a pairwise contrast compares.
Contrast = tuple[str, tuple[str, str], tuple[str, str]]


def mcnemar_exact_p(
    b: Union[int, np.ndarray], c: Union[int, np.ndarray]
) -> Union[float, np.ndarray]:
    """Compute two-sided exact McNemar p-values.

    No discordant pairs return 1.0.

    Parameters
    ----------
    b : int or np.ndarray
        First discordant count.
    c : int or np.ndarray
        Second discordant count.

    Returns
    -------
    float or np.ndarray
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
    succ_a: np.ndarray, succ_b: np.ndarray, n: Union[int, np.ndarray]
) -> np.ndarray:
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


def cmh_p(
    succ_a: np.ndarray, succ_b: np.ndarray, n: Union[int, np.ndarray]
) -> np.ndarray:
    """Compute the two-sided chi-square (df=1) p-value of `cmh_stat`.

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
        Two-sided chi-square (df=1) p-value per leading batch index.
    """
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def gcmh_stat(succ: np.ndarray, n_per_stratum: int) -> np.ndarray:
    """Compute generalized-CMH statistics for `N_RUNGS`-rung families.

    Uniform rung and stratum trials permit the fixed covariance shortcut.
    Singular batches return zero because their residual is zero.

    Parameters
    ----------
    succ : np.ndarray
        Success counts with shape ``(n_sims, N_RUNGS, K)``.
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


def build_primary_contrasts() -> list[Contrast]:
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


def build_secondary_contrasts() -> list[Contrast]:
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
