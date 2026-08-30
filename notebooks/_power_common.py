"""Constants and path helpers shared by the two power-analysis scripts.

``notebooks/{induction,deduction}/analysis/power_analysis.py`` import `ALPHA`,
`POWER_TARGETS`, `SEED`, `fmt_r` and `results_dir` from here; each still defines
its own roster, contrast family, and statistics. Stdlib-only on purpose: both
callers run under ``uv run --no-project`` with only numpy/scipy pulled in via
``--with``.
"""

from pathlib import Path

# SEED is fixed for reproducibility: running either script twice must
# produce identical output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str, up: int = 0) -> Path:
    """Resolve a study's ``results/`` dir: `up` levels above `file`'s directory.

    `file` is the caller's ``__file__`` (a path string). `up` counts directory
    levels ABOVE the caller's own directory: ``0`` means ``results/`` is the
    caller's sibling; a caller in a role subdirectory passes ``up=1`` (e.g.
    ``notebooks/induction/analysis/power_analysis.py`` -> ``notebooks/induction/results``).
    Anchored on `__file__`, never the process cwd, since ``uv run --no-project`` may
    be invoked from any shell directory.

    `up` is a level count rather than an explicit study path because the study
    directory name is load-bearing: it is the ``<study>`` segment of this repo's S3
    experiment keys (`results_store.experiment_name` matches
    ``notebooks/<study>/results`` exactly three components deep), so a
    caller-supplied path with a typo would silently mint a new S3 prefix.
    """
    return Path(file).resolve().parents[up] / "results"


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a replicate count: `r`, or ``">max_replicates"`` when `r` is `None`
    (the power target was not reached within the caller's own scan cap).
    """
    return f">{max_replicates}" if r is None else str(r)
