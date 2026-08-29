"""Shared scaffolding for the induction and deduction power-analysis scripts.

``notebooks/induction/analysis/power_analysis.py`` and
``notebooks/deduction/analysis/power_analysis.py`` both import `ALPHA`,
`POWER_TARGETS`, `SEED`, `fmt_r`, and `results_dir` from here. That is all
they share: each script defines its own model roster, contrast family, and
statistics.

Stdlib-only on purpose: both callers run under ``uv run --no-project`` with
only numpy/scipy pulled in via ``--with``.
"""

from pathlib import Path

# SEED is fixed for reproducibility: running either script twice must
# produce identical output.
SEED = 0
ALPHA = 0.05
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str, up: int = 0) -> Path:
    """Resolve a script's study ``results/`` directory, anchored on ``__file__``.

    Parameters
    ----------
    file : str
        The caller's ``__file__``, e.g. ``results_dir(__file__)``. Must be a
        path string, not already a `Path` (matches the ``__file__`` builtin's
        type).
    up : int, optional
        How many directory levels ABOVE the caller's own directory the study
        root sits. Defaults to ``0`` -- ``results/`` is the caller's own
        sibling. Callers grouped into a role subdirectory of their study pass
        ``up=1``: ``notebooks/induction/analysis/power_analysis.py`` wants
        ``notebooks/induction/results``, not
        ``notebooks/induction/analysis/results``.

    Returns
    -------
    Path
        ``{the directory `up` levels above `file`}/results``.

    Notes
    -----
    Anchored on `__file__`, never the process cwd: otherwise ``uv run
    --no-project ... python notebooks/x/power_analysis.py`` would resolve
    ``results/`` against the shell's invocation directory and break silently.

    `up` is a level count rather than an explicit study path because the
    study directory name is load-bearing -- it is the ``<study>`` segment of
    this repo's S3 experiment keys (`results_store.experiment_name` matches
    ``notebooks/<study>/results`` exactly three components deep). Letting
    each caller name its own results path would let a typo silently mint a
    new S3 prefix.
    """
    return Path(file).resolve().parents[up] / "results"


def fmt_r(r: int | None, max_replicates: int) -> str:
    """Format a "replicates needed" result for tabular printing.

    Parameters
    ----------
    r : int or None
        A replicate count, or `None` meaning the target was not reached
        within the scanned range (a near-tie / infeasible-within-cap
        contrast).
    max_replicates : int
        The scan cap the caller used (each script defines its own
        `MAX_REPLICATES`, so it is passed in rather than assumed here).

    Returns
    -------
    str
        `str(r)` if `r` is not `None`, otherwise `f">{max_replicates}"` --
        i.e. "was not powered within the cap that was actually scanned."
    """
    return f">{max_replicates}" if r is None else str(r)
