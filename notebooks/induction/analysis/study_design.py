"""Pre-registered induction design: roster, contrast tiers, correction thresholds, and the test statistics the tiers are evaluated with.

This study is exploratory end to end: it is pilot-sized, its sizing rests on an
independent-harmonic approximation, and it makes no confirmatory claims.
The Tier-1 omnibus gate and the Holm/BH corrections order the evidence within
that exploratory frame; a gated ladder finding is a stronger exploratory
signal, not a confirmed effect.
"""

import math
import sys
from itertools import combinations
from pathlib import Path

# Bare-name imports: sibling scripts from this directory, ``_power_common`` from ``notebooks/``.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import ALPHA, results_dir
from scipy.stats import binom, chi2

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
#: TOST equivalence margins in accuracy points.
EQUIVALENCE_DELTAS = (0.10, 0.15, 0.20)

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

#: ``(label, cell_a, cell_b)``: the two cells a pairwise contrast compares.
Contrast = tuple[str, tuple[str, str], tuple[str, str]]


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
