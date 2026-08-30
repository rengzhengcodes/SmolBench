"""Constants and path helpers shared by ``notebooks/{induction,deduction}/analysis/power_analysis.py``.

Each caller still defines its own roster, contrast family, and statistics.
Stdlib-only on purpose: both callers run under ``uv run --no-project`` with only
numpy/scipy pulled in via ``--with``.
"""

from pathlib import Path

# SEED is fixed for reproducibility: running either script twice must
# produce identical output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str, up: int = 0) -> Path:
    """Resolve a study's ``results/`` dir, anchored on `file` and never the process cwd.

    `up` is a level count rather than an explicit study path because the study
    directory name is load-bearing: it is the ``<study>`` segment of this repo's S3
    experiment keys (`results_store.experiment_name` matches
    ``notebooks/<study>/results`` exactly three components deep), so a
    caller-supplied path with a typo would silently mint a new S3 prefix.

    Parameters
    ----------
    file : str
        The caller's ``__file__``.
    up : int
        Directory levels ABOVE the caller's directory; ``0`` = sibling ``results/``,
        ``1`` for a caller in a role subdirectory (``notebooks/induction/analysis/``
        -> ``notebooks/induction/results``).
    """
    return Path(file).resolve().parents[up] / "results"


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a replicate count; ``None`` (target not reached within the caller's own
    scan cap) renders as ``">max_replicates"``.
    """
    return f">{max_replicates}" if r is None else str(r)
