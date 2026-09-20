"""Shared analysis constants and result-path helpers.

Kept dependency-light (numpy plus smolbench) so either study can import it.
"""

from pathlib import Path

import numpy as np

from smolbench.evals.results_store import repo_root

# Fixed for reproducible output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(study: str) -> Path:
    """Return the study results directory.

    This mirrors ``Experiment.results_dir``; ``notebooks/<study>/results`` is the path
    ``experiment_name`` parses into the S3 experiment key, so it is derived from the
    study name rather than from the caller's file location.
    """
    return repo_root() / "notebooks" / study / "results"


def _stepup(
    sortedp: np.ndarray, order: np.ndarray, thresholds: np.ndarray
) -> np.ndarray:
    """Apply step-up thresholds and restore input order."""
    m = sortedp.shape[1]
    ok = sortedp <= thresholds
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(sortedp, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    return rej


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
    """
    if pv.ndim != 2:
        raise ValueError(f"pv must be two-dimensional, got shape {pv.shape}")
    m = pv.shape[1]
    order = np.argsort(pv, axis=1)
    sortedp = np.take_along_axis(pv, order, axis=1)
    ranks = np.arange(1, m + 1)
    out = {"Bonferroni": pv <= alpha / m}
    thr = alpha / (m - ranks + 1)
    viol = sortedp > thr
    first = np.where(viol.any(axis=1), viol.argmax(axis=1), m)
    keep = np.arange(m)[None, :] < first[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Holm"] = rej
    out["Hochberg"] = _stepup(sortedp, order, thr)
    out["BH"] = _stepup(sortedp, order, alpha * ranks / m)
    return out


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
