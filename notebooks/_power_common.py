"""Shared analysis constants and result-path helpers.

Kept dependency-light (numpy plus smolbench) so either study can import it.
"""

from pathlib import Path

import numpy as np

from smolbench.evals.results_store import repo_root

#: Fixed for reproducible output.
SEED = 0
#: Two-sided familywise level; the per-test alphas are Bonferroni shares of it.
ALPHA = 0.05
#: Power levels the replicate-count scans report.
POWER_TARGETS = (0.80, 0.90)


def results_dir(study: str) -> Path:
    """Return the study results directory.

    Mirrors ``Experiment.results_dir``: ``notebooks/<study>/results`` is the path
    ``experiment_name`` parses into the S3 experiment key, so it derives from the
    study name rather than from the caller's file location.

    Parameters
    ----------
    study : str
        Study directory name under ``notebooks/``.

    Returns
    -------
    Path
        ``<repo>/notebooks/<study>/results``.
    """
    return repo_root() / "notebooks" / study / "results"


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


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a replicate count.

    Parameters
    ----------
    r : int | None
        ``None`` means the scan cap was reached without hitting the target.
    max_replicates : int
        Scan cap displayed when the target was not reached.

    Returns
    -------
    str
        Formatted replicate count.
    """
    return f">{max_replicates}" if r is None else str(r)
