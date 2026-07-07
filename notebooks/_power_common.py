"""Shared scaffolding for the periodic and chromatic power-analysis scripts.

``notebooks/periodic/power_analysis.py`` and ``notebooks/chromatic/power_analysis.py``
are sibling analyses over sibling induction-eval benchmarks: the same
experiment design (3 model archetypes x 3 information types), the same
planned family of 18 pairwise contrasts (9 archetype-within-info + 9
info-within-model), Bonferroni-corrected at the same alpha, and the same
reproducibility requirement (a fixed SEED so a re-run is byte-identical).

Only the experiment-design constants and small presentation helpers that are
genuinely identical between the two scripts live here. The STATISTICS
deliberately stay in each script, because they differ for a load-bearing
reason, not an accidental one:

  * periodic's outcome is a stratified binomial -- one binary result per
    harmonic k = 1..9 -- so its planned test is Cochran-Mantel-Haenszel (CMH)
    stratified by harmonic.
  * chromatic's outcome is a single ~120-question quiz whose answers are
    bias-correlated (not per-difficulty strata), so the natural unit of
    observation is the whole quiz, and its planned test is a quiz-level
    two-sample Welch t-test across replicate quizzes.

Merging those analyses behind a shared abstraction would either force one
script's statistics onto the other's data-generating process or produce a
leaky abstraction that saves no real duplication -- so this module stops at
the pieces that are truly shared.

Shared YAML-scanning TECHNIQUE (also intentionally not shared as code)
-----------------------------------------------------------------------
Both scripts' result files are YAMLs written by a pre-``Marks.dump``
serializer that tags dataclass instances with ``!!python/object:...``;
``yaml.safe_load`` refuses those tags, and unsafe-loading arbitrary
repository-generated files is not worth the risk just to save a regex. Both
scripts therefore read the file as plain text and regex out the fields they
need (a `` score:`` line per mark) rather than parsing YAML at all. Despite
sharing this technique, each script keeps its own bespoke scanner: periodic
needs exactly one ``score:`` per harmonic in generator order, while
chromatic needs paired ``answer:``/``score:`` fields per True/False question
grouped by mark boundary. The fields, shapes, and failure modes differ
enough that a shared "parse a mark" primitive would need to special-case
both callers anyway -- duplication here is cheaper than a leaky shared
scanner.
"""

from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Experiment design (identical in both scripts: same conditions, same planned
# contrast family, same multiple-comparisons correction).
# ---------------------------------------------------------------------------

MODELS = ("decode", "cot", "moe")
INFOS = ("intens", "extens", "noise_intens")

# SEED is fixed for reproducibility (repo rule: seeded generations
# everywhere) -- running either script twice must produce identical output.
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
    # Design: anchored on `__file__` (never on the process cwd) per repo
    # convention -- otherwise `uv run --no-project ... python
    # notebooks/x/power_analysis.py` would resolve `results/` relative to
    # wherever the shell happened to be invoked from, silently breaking when
    # run from a different directory.
    Calling `.resolve()` normalizes the path (e.g. through symlinks); both
    call sites' `__file__` are already absolute during normal execution, so
    this is a no-op there and only matters for exotic invocations.
    """
    return Path(file).resolve().parent / "results"


def build_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """Build the 18 planned pairwise contrasts.

    9 archetype-within-info contrasts (compare the 3 models pairwise, within
    each of the 3 information types) plus 9 info-within-model contrasts
    (compare the 3 information types pairwise, within each of the 3 models).

    Returns
    -------
    list of (str, (str, str), (str, str))
        Each entry is ``(label, key_a, key_b)`` where ``key_a``/``key_b`` are
        ``(model, info)`` condition keys to compare. Order: all 9 archetype
        contrasts (grouped by info, in `INFOS` order; within each info group,
        pairs in `itertools.combinations(MODELS, 2)` order), followed by all
        9 info-type contrasts (grouped by model, in `MODELS` order; within
        each model group, pairs in `itertools.combinations(INFOS, 2)` order).

    Notes
    -----
    Verified structurally identical (element-for-element `==`) to periodic's
    former inline contrast-building loop before this function replaced it;
    see the commit that introduced this module for the check.
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
