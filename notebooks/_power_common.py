"""Shared analysis constants and result-path helpers.

Stdlib-only so either study can import it.
"""

from pathlib import Path

# Fixed for reproducible output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str, up: int = 0) -> Path:
    """Resolve a study results directory from `file`.

    `up` is a level count, not a path: ``experiment_name`` matches
    ``notebooks/<study>/results`` exactly three deep, so a typo'd path would
    mint a new S3 prefix.

    Parameters
    ----------
    file : str
    up : int
    Returns
    -------
    Path
    """
    return Path(file).resolve().parents[up] / "results"


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a replicate count.

    Parameters
    ----------
    r : int | None
    max_replicates : int
    Returns
    -------
    str
    """
    return f">{max_replicates}" if r is None else str(r)
