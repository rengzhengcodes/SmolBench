"""Share scaffolding for the induction and deduction power-analysis scripts.

Two live scripts import this module: ``notebooks/induction/power_analysis.py``
and ``notebooks/deduction/power_analysis.py``. Both need the same
reproducibility guarantee, a fixed `SEED` so a re-run gives byte-identical
output, and the same small presentation helpers, `fmt_r` and `results_dir`.
That is genuinely all they share: each script defines its own model
roster, its own contrast family, and its own statistics, and imports only
`ALPHA`, `POWER_TARGETS`, `SEED`, `fmt_r`, and `results_dir` from here.

`MODELS`, `INFOS`, `N_TESTS`, `ALPHA_CORRECTED`, and `build_contrasts`
below predate both current callers. They pin the 3-model-archetype x
3-information-type design of two retired induction analyses (periodic
and chromatic). Neither current script imports them: each study's
roster and contrast family are given verbatim by its own spec instead
(see each script's module docstring for why `_power_common`'s design
does not apply). `notebooks/induction/response_audit.py` and
`notebooks/induction/compare_selection_rules.py` also reference this
module, but only for its YAML-safety convention below and its
``sys.modules``-clearing pattern, not for these design constants.

YAML-scanning technique (not shared as code)
-----------------------------------------------------------------------
A pre-``Marks.dump`` serializer writes mark-shaped result files as YAML
and tags dataclass instances with ``!!python/object:...``. ``yaml.safe_load``
refuses those tags. `notebooks/induction/power_analysis.py` avoids an
unsafe loader for arbitrary repository-generated files: that risk is not
worth taking, just to save one regex. So it reads the file as plain text
and uses a regex to pull out the fields it needs (a `` score:`` line per
mark, one per harmonic), instead of parsing YAML at all. This technique
originated in periodic's power analysis and survives in induction's,
which descends from it.

`notebooks/deduction/power_analysis.py` reads a differently shaped
format, JSONL verified-tactic rows, not YAML marks, so this technique
does not apply there. This module stops at the pieces above because a
shared "parse a mark" primitive would need to special-case each caller's
format anyway; duplication here costs less than a leaky shared scanner.
"""

from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Experiment design (identical in both scripts: same conditions, same planned
# contrast family, same multiple-comparisons correction).
# ---------------------------------------------------------------------------

MODELS = ("decode", "cot", "moe")
INFOS = ("intens", "extens", "noise_intens")

# SEED is fixed for reproducibility. The repo rule requires seeded
# generations everywhere: running either script twice must produce
# identical output.
SEED = 0
ALPHA = 0.05
N_TESTS = 18  # 9 archetype contrasts + 9 info-type contrasts
ALPHA_CORRECTED = ALPHA / N_TESTS
POWER_TARGETS = (0.80, 0.90)


def results_dir(file: str) -> Path:
    """Resolve a script's sibling ``results/`` directory, anchored on ``__file__``.

    Parameters
    ----------
    file : str
        The caller's ``__file__``, e.g. ``results_dir(__file__)``. Must be a
        path string, not already a `Path` (matches the ``__file__`` builtin's
        type).

    Returns
    -------
    Path
        ``{resolved parent directory of file}/results``.

    Notes
    -----
    # Design: anchor on `__file__`, not the process cwd, to follow repo
    # convention. Otherwise `uv run --no-project ... python
    # notebooks/x/power_analysis.py` would resolve `results/` relative to the
    # shell's invocation directory, and break silently when run from a
    # different directory.

    `.resolve()` normalizes the path, for example through symlinks. Both
    call sites' `__file__` values are already absolute during normal
    execution, so this call is a no-op there. It matters only for unusual
    invocations.
    """
    return Path(file).resolve().parent / "results"


def build_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build the 18 planned pairwise contrasts.

    The 18 contrasts are 9 archetype-within-info contrasts (compare the 3
    models pairwise, within each of the 3 information types) plus 9
    info-within-model contrasts (compare the 3 information types pairwise,
    within each of the 3 models).

    Returns
    -------
    list of (str, (str, str), (str, str))
        Each entry is ``(label, key_a, key_b)``. ``key_a`` and ``key_b`` are
        ``(model, info)`` condition keys to compare.

        The list holds all 9 archetype contrasts first, then all 9
        info-type contrasts. The archetype contrasts group by info, in
        `INFOS` order; within each info group, pairs follow
        `itertools.combinations(MODELS, 2)` order. The info-type contrasts
        group by model, in `MODELS` order; within each model group, pairs
        follow `itertools.combinations(INFOS, 2)` order.

    Notes
    -----
    A check confirmed this function's output is structurally identical
    (element-for-element `==`) to periodic's former inline
    contrast-building loop, the loop this function replaced. See the commit
    that introduced this module for that check.
    """
    contrasts = []
    for info in INFOS:
        for m_a, m_b in combinations(MODELS, 2):
            contrasts.append((f"[{info}] {m_a} vs {m_b}", (m_a, info), (m_b, info)))
    for model in MODELS:
        for i_a, i_b in combinations(INFOS, 2):
            contrasts.append((f"[{model}] {i_a} vs {i_b}", (model, i_a), (model, i_b)))
    return contrasts


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
