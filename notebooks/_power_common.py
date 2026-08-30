"""Constants and path helpers shared by ``notebooks/{induction,deduction}/analysis/power_analysis.py``.

Each caller keeps its own roster, contrast family, and statistics. Stdlib-only on
purpose: both run under ``uv run --no-project``, with only numpy/scipy pulled in
via ``--with``.
"""

from pathlib import Path

# Fixed so that running either script twice produces identical output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str, up: int = 0) -> Path:
    """Resolve a study's ``results/`` dir, anchored on `file` and never the process cwd.

    `up` is a level count, not a study path: the study directory name is the
    ``<study>`` segment of this repo's S3 experiment keys
    (`results_store.experiment_name` matches ``notebooks/<study>/results`` exactly
    three components deep), so a typo in a caller-supplied path would mint a new prefix.

    Parameters
    ----------
    file : str
        The caller's ``__file__``.
    up : int
        Levels above the caller's directory; ``0`` = sibling ``results/``, ``1`` for a
        caller in a role subdirectory like ``notebooks/induction/analysis/``.
    """
    return Path(file).resolve().parents[up] / "results"


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a replicate count; ``None`` means the caller's scan cap was reached
    without hitting the target, and renders as ``">max_replicates"``."""
    return f">{max_replicates}" if r is None else str(r)
