"""Shared analysis constants and the batched multiplicity corrections.

Kept dependency-light (numpy plus smolbench) so any study's analysis scripts can
import it.
"""

import numpy as np

from smolbench.evals.study_config import load_study_config

#: The ``[analysis]`` section of study_config.toml, where each knob's rationale lives.
ANALYSIS = load_study_config().analysis
SEED = ANALYSIS.seed
ALPHA = ANALYSIS.alpha
POWER_TARGETS = ANALYSIS.power_targets
#: TOST equivalence margins.
EQUIVALENCE_DELTAS = ANALYSIS.equivalence_deltas


def _stepup(ok: np.ndarray) -> np.ndarray:
    """Reject every sorted position at or below the last threshold-satisfying one."""
    return np.logical_or.accumulate(ok[:, ::-1], axis=1)[:, ::-1]


def _unsort(rejected: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Scatter a sorted-position mask back to the input column order."""
    out = np.zeros_like(rejected)
    np.put_along_axis(out, order, rejected, axis=1)
    return out


def apply_corrections(pv: np.ndarray, alpha: float) -> dict[str, np.ndarray]:
    """Apply Bonferroni, Holm, Hochberg, and BH corrections.

    Vectorized over rows because multiplicity_sim corrects thousands of simulated
    families per call, which ``statsmodels.stats.multitest.multipletests`` (one
    family per call) cannot do at that volume;
    ``test_apply_corrections_matches_statsmodels`` pins row-wise agreement.

    Parameters
    ----------
    pv : np.ndarray
        Two-dimensional p-value families, one family per row.
    alpha : float
        Familywise error-rate or false-discovery-rate level.

    Returns
    -------
    dict[str, np.ndarray]
        Rejection masks in the original column order.

    Raises
    ------
    ValueError
        If ``pv`` is not two-dimensional.
    """
    if pv.ndim != 2:
        raise ValueError(f"pv must be two-dimensional, got shape {pv.shape}")
    m = pv.shape[1]
    order = np.argsort(pv, axis=1)
    sortedp = np.take_along_axis(pv, order, axis=1)
    ranks = np.arange(1, m + 1)
    # Holm steps down and Hochberg steps up through the same thresholds.
    fwer_ok = sortedp <= alpha / (m - ranks + 1)
    return {
        "Bonferroni": pv <= alpha / m,
        "Holm": _unsort(np.logical_and.accumulate(fwer_ok, axis=1), order),
        "Hochberg": _unsort(_stepup(fwer_ok), order),
        "BH": _unsort(_stepup(sortedp <= alpha * ranks / m), order),
    }
