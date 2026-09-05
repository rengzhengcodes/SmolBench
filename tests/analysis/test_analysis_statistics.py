"""Pins for the statistical plumbing under ``notebooks/induction/analysis/``.

Covers the hand-rolled multiplicity corrections replaced by ``statsmodels``
(12-25), the pre-registration gates that had to survive ``python -O``
(12-12), the results walkers routed through ``LocalResultsStore`` (12-24),
the single loader shared by the contrasts and the compliance census
(12-26), and ``multiplicity_sim``'s constants, alphas, output path and
cost (12-10, 12-27, 12-28, 12-31).

See ``tests/analysis/_trees.py`` for the synthetic replicate tree these use
and for why this directory has no ``conftest.py``.
"""

import inspect
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT
from tests._paths import REPO_ROOT

from tests.analysis._trees import (  # noqa: F401
    ANALYSIS_DIR,
    SHALLOW_DEPTH,
    build_tree,
    extens_vs_noise,
    load_analysis,
    paired_analysis,
    power_analysis,
    repoint,
    significance_report,
)

NOTEBOOKS_DIR = REPO_ROOT / "notebooks"


@pytest.fixture(scope="session")
def multiplicity_sim(power_analysis):
    """The standalone Monte Carlo module (12-27 gives it sibling imports)."""
    return load_analysis("multiplicity_sim")


# ===========================================================================
# 12-25 -- Holm / Hochberg / BH were hand-rolled beside a statsmodels dependency
# ===========================================================================

def _legacy_holm(pvals, alpha):
    """The pre-swap ``paired_analysis.holm``, vendored verbatim from f3a13c9a."""
    m = pvals.size
    order = np.argsort(pvals, kind="stable")
    reject = np.zeros(m, dtype=bool)
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


def _legacy_hochberg(pvals, alpha):
    """The pre-swap ``significance_report.hochberg``, vendored verbatim."""
    m = pvals.size
    order = np.argsort(pvals, kind="stable")
    sorted_p = pvals[order]
    reject = np.zeros(m, dtype=bool)
    for i in range(m - 1, -1, -1):
        if sorted_p[i] <= alpha / (m - i):
            reject[order[: i + 1]] = True
            break
    return reject


def _legacy_bh(p, q):
    """The pre-swap nested ``bh()`` closure from ``paired_analysis.main``."""
    m = p.size
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1)) / m
    passed = p[order] <= thresh
    k = np.max(np.nonzero(passed)[0]) + 1 if passed.any() else 0
    rej = np.zeros(m, dtype=bool)
    rej[order[:k]] = True
    return rej


def _tie_heavy_vectors(n=200):
    """Yield `n` p-value vectors dominated by EXACT ties.

    Ties are pervasive in this study, not incidental: ``signflip_exact_p`` has
    a hard resolution floor at ``2/2**S`` and lanes sit exactly on it (three
    did in the 2026-08 data), 1.0 is returned verbatim whenever a contrast has
    no discordant pairs, and the Bonferroni threshold itself is an attainable
    value. A correction swap is only safe if it agrees THERE.
    """
    rng = np.random.default_rng(20260905)
    pool = np.array([2 / 2**30, 2 / 2**16, 1.0, 0.05, 0.05 / 210, 1e-8, 0.5, 0.02])
    for i in range(n):
        m = int(rng.integers(2, 80))
        if i % 3 == 0:
            yield np.round(rng.random(m), 2)          # coarse rounding -> ties
        else:
            yield rng.choice(pool, size=m)            # exact study-shaped ties


@pytest.mark.parametrize("alpha", (0.05, 0.05 / 210))
def test_holm_and_hochberg_match_the_hand_rolled_versions(paired_analysis,
                                                          significance_report,
                                                          alpha):
    """The statsmodels swap is drop-in on tie-heavy p-vectors, at both alphas.

    Verified BEFORE deleting the hand-rolled loops, which is the only way to
    know the swap preserved every published rejection set. 0 mismatches over
    200 vectors.
    """
    for pvals in _tie_heavy_vectors():
        assert np.array_equal(paired_analysis.holm(pvals, alpha),
                              _legacy_holm(pvals, alpha)), pvals
        assert np.array_equal(significance_report.hochberg(pvals, alpha),
                              _legacy_hochberg(pvals, alpha)), pvals


def test_bh_is_a_module_level_function_matching_the_old_closure(paired_analysis):
    """BH moves out of ``main``'s body and keeps its rejection set.

    The old nested ``bh()`` sorted with a BARE ``np.argsort`` while its two
    siblings documented a STABLE sort as load-bearing -- an inconsistency that
    only did not bite because the per-rank thresholds are monotone.
    """
    assert callable(getattr(paired_analysis, "bh", None)), \
        "bh must be importable, not buried in main()"
    for pvals in _tie_heavy_vectors():
        assert np.array_equal(paired_analysis.bh(pvals, 0.05),
                              _legacy_bh(pvals, 0.05)), pvals


@pytest.mark.parametrize("name", ("holm", "hochberg", "bh"))
def test_rejection_sets_do_not_depend_on_contrast_build_order(paired_analysis,
                                                              significance_report,
                                                              name):
    """Permuting the inputs permutes the mask exactly -- the property the stable
    sort protected.

    ``multipletests`` sorts with a bare ``np.argsort``, so the explicit
    ``kind="stable"`` the hand-rolled versions documented is gone. It is safe
    because every per-rank threshold here is MONOTONE increasing in rank
    (``alpha/(m-i)`` for Holm/Hochberg, ``q*i/m`` for BH): if one member of a
    tie clears its threshold, every later member clears a looser one, so no
    tie can straddle the boundary and tie order cannot move the decision.
    This test is that argument, executed.
    """
    fn = getattr(significance_report if name == "hochberg" else paired_analysis, name)
    rng = np.random.default_rng(7)
    for pvals in _tie_heavy_vectors(60):
        perm = rng.permutation(pvals.size)
        base = fn(pvals, 0.05)
        permuted = fn(pvals[perm], 0.05)
        assert np.array_equal(permuted, base[perm]), (pvals, perm)


def test_mcnemar_is_defined_once_and_the_vectorized_form_agrees(paired_analysis,
                                                                multiplicity_sim):
    """``multiplicity_sim``'s vectorized McNemar equals ``paired_analysis``'s scalar.

    Two independent implementations of one exact test is one implementation
    too many; the vectorized form now delegates to ``scipy.stats.binom`` on
    the same conditional-binomial definition.
    """
    rng = np.random.default_rng(3)
    b = rng.integers(0, 40, 300)
    c = rng.integers(0, 40, 300)
    vec = multiplicity_sim.mcnemar_exact_p(b, c)
    for i in range(b.size):
        assert vec[i] == pytest.approx(
            paired_analysis.mcnemar_exact_p(int(b[i]), int(c[i])), rel=1e-12
        ), (int(b[i]), int(c[i]))
    # The no-discordance convention must survive the swap.
    assert multiplicity_sim.mcnemar_exact_p(np.array([0]), np.array([0]))[0] == 1.0


# ===========================================================================
# 12-12 -- pre-registration gates were bare asserts, stripped by python -O
# ===========================================================================

def test_design_invariants_are_checked_at_module_scope_and_raise(power_analysis):
    """The family-size gates run on IMPORT and raise; they are not asserts in main().

    ``ALPHA_PRIMARY`` is ``0.05 / N_PRIMARY`` and ``ALPHA_SECONDARY`` is
    ``0.05 / N_SECONDARY``, so a drift between the hand-written counts and
    ``build_*_contrasts()`` silently invalidates every correction in the
    study. The only checks of that were asserts inside ``main()``, which no
    importer calls.
    """
    check = getattr(power_analysis, "check_design_invariants", None)
    assert callable(check), "the gate must be a callable run at module scope"
    assert check() is None

    original = power_analysis.N_PRIMARY
    try:
        power_analysis.N_PRIMARY = original - 1
        with pytest.raises(RuntimeError):
            check()
    finally:
        power_analysis.N_PRIMARY = original


def test_design_invariants_survive_python_dash_o():
    """Under ``python -O`` the gate still fires -- the whole point of a raise.

    Executed at f3a13c9a: ``python -O`` imported the module with
    ``len(MODELS)`` disagreeing with ``FAMILIES`` and ``ALPHA_PRIMARY`` still
    ``0.05/210``.
    """
    code = (
        "import sys;"
        f"sys.path.insert(0, {str(ANALYSIS_DIR)!r});"
        f"sys.path.insert(0, {str(NOTEBOOKS_DIR)!r});"
        "import power_analysis as pa;"
        "assert False, 'asserts are live -- this subprocess is not under -O';"
    )
    # 1. -O really is in force (the bare assert above must NOT fire).
    ok = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True,
                        text=True, cwd=str(REPO_ROOT))
    assert ok.returncode == 0, ok.stderr

    # 2. ... and the gate still raises under it.
    broken = (
        "import sys;"
        f"sys.path.insert(0, {str(ANALYSIS_DIR)!r});"
        f"sys.path.insert(0, {str(NOTEBOOKS_DIR)!r});"
        "import power_analysis as pa;"
        "pa.N_PRIMARY = pa.N_PRIMARY - 1;"
        "pa.check_design_invariants()"
    )
    result = subprocess.run([sys.executable, "-O", "-c", broken],
                            capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert result.returncode != 0, result.stdout
    assert "RuntimeError" in result.stderr, result.stderr


@pytest.mark.parametrize("module", ("power_analysis", "paired_analysis"))
def test_no_bare_assert_gates_remain(module):
    """No ``assert`` survives as a GATE in either module.

    A bare assert vanishes under ``python -O``; ``power_analysis`` says so
    itself at ``load_outcomes`` ("A raise, not an assert: this gate must
    survive ``python -O``") while four other gates in the same chain were
    asserts.
    """
    source = (ANALYSIS_DIR / f"{module}.py").read_text()
    offenders = [ln for ln in source.splitlines()
                 if ln.lstrip().startswith("assert ")]
    assert not offenders, offenders


# ===========================================================================
# 12-24 / 12-26 -- one store-backed loader, consumed by contrasts AND census
# ===========================================================================

@pytest.fixture
def small_tree(tmp_path, power_analysis):
    """A 6-seed tree with one deliberately UNPARSABLE replicate filename."""
    build_tree(tmp_path, power_analysis.MODELS, power_analysis.INFOS,
               lambda m, i: ((0.10 if i == "zero" else 0.90), 0.0, "empty",
                             range(SHALLOW_DEPTH)))
    # Not a replicate: its seed segment does not parse as an int. The
    # hand-rolled walkers did `int(path.stem.split("_")[1])` (ValueError) or
    # silently folded it into the census; LocalResultsStore.list_seeds skips it.
    bogus = Marks(
        model="stub-model",
        marks=tuple(Mark(query=f"q{i}", answer=i, response="x", score=0,
                         compliance="empty") for i in range(9)),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    cell = power_analysis.MODELS[0], "intens"
    bogus.dump(tmp_path / f"{cell[0]}_{cell[1]}" / "rep_bogus.yaml")
    return tmp_path, cell


def test_walkers_skip_an_unparsable_replicate_filename(repoint, paired_analysis,
                                                        significance_report,
                                                        small_tree):
    """A non-replicate file in the tree is skipped, by BOTH the loader and the census.

    ``LocalResultsStore.list_seeds`` already owns this rule and documents it;
    the three scripts each re-implemented the walk without it, so one stray
    file either raised ``ValueError`` mid-load or silently entered the census
    denominator as a 100%-non-compliant replicate.
    """
    root, cell = small_tree
    repoint(root)
    loaded = paired_analysis.load_marks()
    correct = loaded[0]
    assert sorted(correct[cell]) == list(range(SHALLOW_DEPTH))

    census = significance_report.compliance_census(loaded[2])
    # 6 replicates x 9 marks; the 9 bogus marks must not be in the denominator.
    assert census[cell]["n"] == SHALLOW_DEPTH * 9


def test_the_census_consumes_the_loader_rather_than_re_reading_the_tree(
        repoint, paired_analysis, significance_report, small_tree, monkeypatch):
    """Each replicate is opened ONCE for both the contrasts and the census.

    ``compliance_census`` re-walked and re-YAML-parsed every ``rep_*.yaml``
    that ``load_marks()`` had opened two lines earlier: 504 file opens on a
    6-seed tree, 2,520 at full depth, and a second, differently-denominated
    expression of ``Marks.noncompliant``'s rule.
    """
    root, _cell = small_tree
    repoint(root)

    reads = []
    original = Marks.load.__func__
    monkeypatch.setattr(
        Marks, "load",
        classmethod(lambda cls, path: reads.append(str(path)) or original(cls, path)),
    )

    loaded = paired_analysis.load_marks()
    after_load = len(reads)
    census = significance_report.compliance_census(loaded[2])

    n_cells = len(loaded[0])
    assert n_cells == 84
    # Exactly one open per (cell, seed) -- and NONE added by the census.
    assert after_load == n_cells * SHALLOW_DEPTH, after_load
    assert len(reads) == after_load, reads[after_load:]
    assert len(census) == n_cells


def test_extens_vs_noise_reuses_the_family_p_values_it_already_computed(
        repoint, extens_vs_noise, power_analysis, small_tree, monkeypatch):
    """The 21 focused contrasts read their p-values off the 210-contrast pass.

    ``extens_vs_noise`` computed the full pre-registered family (so the Holm
    decision is the real one), then recomputed the same 21 sign-flip and
    McNemar p-values a second time for its own table -- 231 exact
    randomization tests where 210 were needed.
    """
    root, _cell = small_tree
    repoint(root)
    calls = []
    real = extens_vs_noise.signflip_exact_p
    monkeypatch.setattr(extens_vs_noise, "signflip_exact_p",
                        lambda diffs: calls.append(1) or real(diffs))

    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()), \
            contextlib.redirect_stderr(io.StringIO()):
        extens_vs_noise.main()

    # 210 for the pre-registered family, and NOT 210 + 21.
    assert len(calls) == power_analysis.N_PRIMARY, len(calls)


# ===========================================================================
# 12-27 / 12-28 / 12-10 / 12-31 -- multiplicity_sim constants, alphas, path, cost
# ===========================================================================

def test_design_constants_are_imported_not_re_declared(multiplicity_sim,
                                                       power_analysis):
    """``multiplicity_sim`` no longer copies four constants it names in comments.

    Value equality alone is vacuous here -- the copies were CORRECT copies, and
    that is exactly why nothing caught them. The source check is what makes
    this test bite: a re-declaration that happens to agree today would pass the
    equality and fail the import.
    """
    import _power_common

    assert multiplicity_sim.ALPHA == _power_common.ALPHA
    assert multiplicity_sim.N_PRIMARY == power_analysis.N_PRIMARY
    assert multiplicity_sim.K_HARM == power_analysis.N_HARMONICS
    assert multiplicity_sim.ALPHA_BONF == power_analysis.ALPHA_PRIMARY

    source = (ANALYSIS_DIR / "multiplicity_sim.py").read_text()
    assert "from _power_common import" in source, source[:2000]
    assert "from power_analysis import" in source, source[:2000]
    for redeclared in ("N_PRIMARY = 210", "ALPHA = 0.05", "K_HARM = 9"):
        assert redeclared not in source, redeclared


def test_no_bare_replicate_count_literals_survive(multiplicity_sim):
    """``part2`` used ``eq_r = 30`` and ``eq_r / 30.0`` beside ``R_DEFAULT``.

    Two spellings of one design constant is how a re-sizing silently applies
    to half a report.
    """
    source = inspect.getsource(multiplicity_sim.part2)
    assert "30" not in source.replace("R_DEFAULT", ""), source

    # The equivalent-R search ladder moved to a module constant so that its
    # genuine grid point 300 is not mistaken for a spelling of R_DEFAULT. Pin
    # the relationship that DOES matter where it now lives: the ladder starts
    # at the study's own R, because eq_R is defined as "the smallest R at which
    # the UNPAIRED test matches the paired test's power at R_DEFAULT" -- a
    # ladder starting anywhere else could not express eq_R == R_DEFAULT.
    assert multiplicity_sim.EQ_R_GRID[0] == multiplicity_sim.R_DEFAULT
    assert list(multiplicity_sim.EQ_R_GRID) == sorted(multiplicity_sim.EQ_R_GRID)
    # part2's `cap` default is the ladder's top, so its docstring's "largest
    # entry `cap`" holds by construction rather than by two literals agreeing.
    assert (inspect.signature(multiplicity_sim.part2).parameters["cap"].default
            == multiplicity_sim.EQ_R_GRID[-1])


def test_part_seeds_derive_from_the_shared_seed(multiplicity_sim):
    """``main`` seeded ``default_rng(1/3/5/2/4)`` though ``_power_common.SEED`` exists."""
    import _power_common

    source = inspect.getsource(multiplicity_sim.main)
    for literal in ("default_rng(1)", "default_rng(2)", "default_rng(3)",
                    "default_rng(4)", "default_rng(5)"):
        assert literal not in source, literal
    assert "SEED" in source
    assert _power_common.SEED == 0


def test_monte_carlo_output_lands_in_the_results_dir(multiplicity_sim):
    """The checkpoint JSON goes under ``results/``, covered by the general rule.

    It was written next to the script and covered by a one-off ``.gitignore``
    literal, so the numbers justifying the TEST and CORRECTION choice existed
    only on whichever machine last ran it.
    """
    import _power_common

    expected = _power_common.results_dir(multiplicity_sim.__file__, up=1)
    assert multiplicity_sim.OUT_PATH.parent == expected
    assert multiplicity_sim.OUT_PATH.name.endswith(".json")

    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert "multiplicity_sim_results.json" not in gitignore
    # ... because the general rule already covers the new location.
    assert "notebooks/*/results/" in gitignore


def test_dump_creates_its_own_results_directory(multiplicity_sim, tmp_path,
                                                monkeypatch, capsys):
    """Moving OUT_PATH into results/ requires dump() to mkdir -- that dir is not in the tree.

    ``notebooks/induction/results/`` is gitignored and absent from a fresh
    checkout, while ``dump()`` is a bare ``open(OUT_PATH, "w")``. Relocating
    the checkpoint without creating the parent turns every part's checkpoint
    into a ``FileNotFoundError`` after the Monte Carlo has already run -- the
    most expensive possible place to fail.
    """
    target = tmp_path / "results" / "multiplicity_sim_results.json"
    assert not target.parent.exists()
    monkeypatch.setattr(multiplicity_sim, "OUT_PATH", target)
    monkeypatch.setattr(multiplicity_sim, "OUT", {"probe": 1})

    multiplicity_sim.dump("probe")

    assert target.exists()
    import json
    assert json.loads(target.read_text()) == {"probe": 1}


def test_part5_prices_the_trend_test_in_the_same_family_as_part4(multiplicity_sim):
    """One trend test cannot cost ALPHA/28 in PART 5 and ALPHA/154 in PART 4.

    PART 5's head-to-head handed the trend test 0.05/28 against pairwise
    0.05/210 -- 7.5x looser -- which mechanically favours the "trend wins"
    conclusion it then draws. Nothing outside this file pre-registers any
    trend test, so the ALPHA/28 family stays only as a labelled sensitivity
    row.
    """
    alpha = multiplicity_sim.ALPHA
    rng = np.random.default_rng(0)
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        multiplicity_sim.part5(rng, n_sims=200)
    part5 = multiplicity_sim.OUT["part5"]

    assert part5["alpha_trend_studywide"] == pytest.approx(alpha / 154)
    assert part5["alpha_trend_only"] == pytest.approx(alpha / 28)
    assert part5["alpha_pairwise"] == pytest.approx(alpha / 210)
    for row in part5["rows"]:
        assert "trend_studywide" in row and "trend_trend_only_family" in row
    # "pre-registered" must no longer be claimed for the trend-only family.
    source = inspect.getsource(multiplicity_sim.part5)
    assert "pre-registered" not in source.lower().replace("not pre-registered", "")


def test_replicates_needed_is_memoized_on_its_rate_vectors(power_analysis):
    """The fixed-seed sizing scan is re-run per contrast though inputs repeat.

    ``pooled`` admits only 10 distinct rate vectors across 273 contrasts, so
    the scan was recomputed up to ~27x per distinct input. The cache is keyed
    on ``(rates_a.tobytes(), rates_b.tobytes(), alpha)``; the ``rng`` is
    deliberately NOT part of the key because every caller re-seeds
    ``default_rng(SEED)` immediately before the call.
    """
    fn = power_analysis.replicates_needed
    assert hasattr(fn, "cache_info") and hasattr(fn, "cache_clear"), \
        "replicates_needed must expose its cache for auditing"
    fn.cache_clear()

    a = np.full(power_analysis.N_HARMONICS, 0.9)
    b = np.full(power_analysis.N_HARMONICS, 0.5)
    first = fn(a, b, np.random.default_rng(power_analysis.SEED))
    # Equal VALUES in a distinct array object: the key is the bytes, not the id.
    second = fn(a.copy(), b.copy(), np.random.default_rng(power_analysis.SEED))
    assert first == second
    info = fn.cache_info()
    assert info.hits == 1 and info.misses == 1, info


def test_paired_powers_has_a_stats_free_fast_path(multiplicity_sim):
    """``part2``'s grid search discards 3 of 4 returns yet paid for all of them.

    The discarded ``phi`` upcast both boolean mark arrays to float64 -- 1.55 GB
    at the top of ``grid_r`` -- for a number the search never reads.
    """
    params = inspect.signature(multiplicity_sim._paired_powers).parameters
    assert "stats" in params and params["stats"].default is True

    args = (0.95, 0.05, 0.5, 30, 400)
    full = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=True)
    fast = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=False)
    # The two powers are unchanged; only the diagnostics are skipped.
    assert fast[0] == full[0] and fast[1] == full[1]
    assert fast[2] is None and fast[3] is None


def test_omnibus_interaction_power_is_cheaper_by_default(power_analysis):
    """4,000 GLM fits (~380 s per call, called twice) for an explicit non-gate.

    Its own docstring calls it "a design-level diagnostic, not a gate: no
    contrast family depends on it", so its default cost must match that role.
    """
    default = inspect.signature(
        power_analysis.omnibus_interaction_power).parameters["n_sims"].default
    assert default < 1000, default
    source = inspect.getsource(power_analysis.omnibus_interaction_power)
    assert str(default) in source or "n_sims" in source
