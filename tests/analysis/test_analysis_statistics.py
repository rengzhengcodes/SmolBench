"""Pins for the statistical plumbing under ``notebooks/induction/analysis/``.

Covers the hand-rolled multiplicity corrections replaced by ``statsmodels``,
the pre-registration gates that had to survive ``python -O``, the results
walkers routed through ``LocalResultsStore``, the single loader shared by
the contrasts and the compliance census, and ``multiplicity_sim``'s
constants, alphas, output path and cost.

See ``tests/analysis/_trees.py`` for the synthetic replicate tree these use
and for why this directory has no ``conftest.py``.
"""

import inspect
import subprocess
import sys
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest
from scipy.stats import binom

from smolbench.evals import Mark, Marks
from tests._paths import REPO_ROOT

from tests.analysis._trees import (  # noqa: F401
    ANALYSIS_DIR,
    SHALLOW_DEPTH,
    build_tree,
    extens_vs_noise,
    multiplicity_sim,
    paired_analysis,
    power_analysis,
    repoint,
    significance_report,
)

NOTEBOOKS_DIR = REPO_ROOT / "notebooks"


# ===========================================================================
# The roster is read from the committed study config, not re-declared here
# ===========================================================================

def test_power_analysis_roster_comes_from_the_study_config(power_analysis: ModuleType) -> None:
    """MODELS/FAMILIES are the config's roster rendered into analysis tags, with one owner (``study_config.toml``)."""
    from smolbench.evals import study_config

    assert power_analysis.MODELS == tuple(
        study_config.tag_for(key) for key in study_config.roster_keys()
    )
    assert power_analysis.FAMILIES == {
        family: tuple(study_config.tag_for(key) for key in rungs)
        for family, rungs in study_config.families().items()
    }


# ===========================================================================
# Holm / Hochberg / BH were hand-rolled beside a statsmodels dependency
# ===========================================================================

def _tie_heavy_vectors(n: int = 200) -> Iterator[np.ndarray]:
    """Yield `n` p-value vectors dominated by exact ties.

    Ties are pervasive here, not incidental: ``signflip_exact_p`` has a hard
    resolution floor at ``2/2**S``, 1.0 is returned verbatim when a contrast
    has no discordant pairs, and the Bonferroni threshold is itself an
    attainable value. A correction swap is only safe if it agrees at these
    points.
    """
    rng = np.random.default_rng(20260905)
    pool = np.array([2 / 2**30, 2 / 2**16, 1.0, 0.05, 0.05 / 210, 1e-8, 0.5, 0.02])
    for i in range(n):
        m = int(rng.integers(2, 80))
        if i % 3 == 0:
            yield np.round(rng.random(m), 2)          # coarse rounding -> ties
        else:
            yield rng.choice(pool, size=m)            # exact study-shaped ties


@pytest.mark.parametrize("name", ("holm", "hochberg", "bh"))
def test_rejection_sets_do_not_depend_on_contrast_build_order(paired_analysis: ModuleType,
                                                              significance_report: ModuleType,
                                                              name: str) -> None:
    """Permuting the inputs permutes the mask exactly, because each procedure's per-rank threshold is monotone increasing in rank, so tie order cannot move the decision."""
    fn = getattr(significance_report if name == "hochberg" else paired_analysis, name)
    rng = np.random.default_rng(7)
    for pvals in _tie_heavy_vectors(60):
        perm = rng.permutation(pvals.size)
        base = fn(pvals, 0.05)
        permuted = fn(pvals[perm], 0.05)
        assert np.array_equal(permuted, base[perm]), (pvals, perm)


def test_mcnemar_is_defined_once(power_analysis: ModuleType, paired_analysis: ModuleType,
                                 multiplicity_sim: ModuleType) -> None:
    """One broadcasting implementation serves the scalar and batched call sites."""
    assert paired_analysis.mcnemar_exact_p is power_analysis.mcnemar_exact_p
    assert multiplicity_sim.mcnemar_exact_p is power_analysis.mcnemar_exact_p
    # The no-discordance convention must survive the swap, batched and scalar.
    assert power_analysis.mcnemar_exact_p(np.array([0]), np.array([0]))[0] == 1.0
    assert power_analysis.mcnemar_exact_p(0, 0) == 1.0
    rng = np.random.default_rng(3)
    b, c = rng.integers(0, 40, 300), rng.integers(0, 40, 300)
    ref = np.minimum(1.0, 2 * binom.cdf(np.minimum(b, c), b + c, 0.5))
    np.testing.assert_allclose(power_analysis.mcnemar_exact_p(b, c), ref, rtol=1e-12)
    assert power_analysis.mcnemar_exact_p(4, 4) == 1.0


# ===========================================================================
# pre-registration gates were bare asserts, stripped by python -O
# ===========================================================================

def test_design_invariants_are_checked_at_module_scope_and_raise(
    power_analysis: ModuleType,
) -> None:
    """The family-size gates run on import and raise, not assert in ``main()``, since a drift between the hand-written counts and ``build_*_contrasts()`` would silently invalidate every correction."""
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


def test_design_invariants_survive_python_dash_o() -> None:
    """Under ``python -O`` the gate still fires -- the whole point of a raise."""
    code = (
        "import sys;"
        f"sys.path.insert(0, {str(ANALYSIS_DIR)!r});"
        f"sys.path.insert(0, {str(NOTEBOOKS_DIR)!r});"
        "import power_analysis as pa;"
        "assert False, 'asserts are live -- this subprocess is not under -O';"
    )
    # 1. -O is in force (the bare assert above must not fire).
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
def test_no_bare_assert_gates_remain(module: str) -> None:
    """No ``assert`` survives as a gate in either module; a bare assert vanishes under ``python -O``."""
    source = (ANALYSIS_DIR / f"{module}.py").read_text()
    offenders = [ln for ln in source.splitlines()
                 if ln.lstrip().startswith("assert ")]
    assert not offenders, offenders


# ===========================================================================
# one store-backed loader, consumed by contrasts and census
# ===========================================================================

@pytest.fixture(scope="module")
def small_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> tuple[Path, tuple[str, str]]:
    """A 6-seed tree with one unparsable replicate filename."""
    tmp_path = tmp_path_factory.mktemp("small-tree")
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


def test_walkers_skip_an_unparsable_replicate_filename(
    repoint: Callable[[Path], None],
    paired_analysis: ModuleType,
    significance_report: ModuleType,
    small_tree: tuple[Path, tuple[str, str]],
) -> None:
    """A non-replicate file in the tree is skipped, by both the loader and the census."""
    root, cell = small_tree
    repoint(root)
    loaded = paired_analysis.load_marks()
    correct = loaded[0]
    assert sorted(correct[cell]) == list(range(SHALLOW_DEPTH))

    census = significance_report.compliance_census(loaded[2])
    # 6 replicates x 9 marks; the 9 bogus marks must not be in the denominator.
    assert census[cell]["n"] == SHALLOW_DEPTH * 9


def test_the_census_consumes_the_loader_rather_than_re_reading_the_tree(
    repoint: Callable[[Path], None],
    paired_analysis: ModuleType,
    significance_report: ModuleType,
    small_tree: tuple[Path, tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each replicate is opened once for both the contrasts and the census."""
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
    # Exactly one open per (cell, seed) -- and none added by the census.
    assert after_load == n_cells * SHALLOW_DEPTH, after_load
    assert len(reads) == after_load, reads[after_load:]
    assert len(census) == n_cells


def test_extens_vs_noise_reuses_the_family_p_values_it_already_computed(
    repoint: Callable[[Path], None],
    extens_vs_noise: ModuleType,
    power_analysis: ModuleType,
    small_tree: tuple[Path, tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The 21 focused contrasts read their p-values off the 210-contrast pass, instead of recomputing them."""
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

    # 210 for the pre-registered family, and not 210 + 21.
    assert len(calls) == power_analysis.N_PRIMARY, len(calls)


# ===========================================================================
# multiplicity_sim constants, alphas, path, cost
# ===========================================================================

def test_design_constants_are_imported_not_re_declared(multiplicity_sim: ModuleType,
                                                       power_analysis: ModuleType) -> None:
    """``multiplicity_sim`` imports its four design constants instead of copying them."""
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


def test_no_bare_replicate_count_literals_survive(multiplicity_sim: ModuleType) -> None:
    """``part2`` spells the replicate count only as ``R_DEFAULT``, so a re-sizing cannot apply to half a report."""
    source = inspect.getsource(multiplicity_sim.part2)
    assert "30" not in source.replace("R_DEFAULT", ""), source

    # The equivalent-R search ladder moved to a module constant so its grid
    # point 300 isn't mistaken for a spelling of R_DEFAULT. The ladder must
    # start at the study's own R, since eq_R is "the smallest R at which the
    # unpaired test matches the paired test's power at R_DEFAULT" -- starting
    # elsewhere couldn't express eq_R == R_DEFAULT.
    assert multiplicity_sim.EQ_R_GRID[0] == multiplicity_sim.R_DEFAULT
    assert list(multiplicity_sim.EQ_R_GRID) == sorted(multiplicity_sim.EQ_R_GRID)
    assert "cap=EQ_R_GRID[-1]" in source


def test_part_seeds_derive_from_the_shared_seed(multiplicity_sim: ModuleType) -> None:
    """``main`` derives every part's RNG from ``_power_common.SEED`` rather than a per-part literal."""
    import _power_common

    source = inspect.getsource(multiplicity_sim.main)
    for literal in ("default_rng(1)", "default_rng(2)", "default_rng(3)",
                    "default_rng(4)", "default_rng(5)"):
        assert literal not in source, literal
    assert "SEED" in source
    assert _power_common.SEED == 0


def test_monte_carlo_output_lands_in_the_results_dir(multiplicity_sim: ModuleType) -> None:
    """The checkpoint JSON goes under ``results/``, covered by the general ``.gitignore`` rule instead of a one-off literal."""
    import _power_common

    expected = _power_common.results_dir(multiplicity_sim.__file__, up=1)
    assert multiplicity_sim.OUT_PATH.parent == expected
    assert multiplicity_sim.OUT_PATH.name.endswith(".json")

    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert "multiplicity_sim_results.json" not in gitignore
    # ... because the general rule already covers the new location.
    assert "notebooks/*/results/" in gitignore


def test_dump_creates_its_own_results_directory(multiplicity_sim: ModuleType, tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """Moving ``OUT_PATH`` into ``results/`` requires ``dump()`` to mkdir, since that directory is gitignored and absent from a fresh checkout."""
    target = tmp_path / "results" / "multiplicity_sim_results.json"
    assert not target.parent.exists()
    monkeypatch.setattr(multiplicity_sim, "OUT_PATH", target)
    monkeypatch.setattr(multiplicity_sim, "OUT", {"probe": 1})

    multiplicity_sim.dump("probe")

    assert target.exists()
    import json
    assert json.loads(target.read_text()) == {"probe": 1}


def test_part5_prices_the_trend_test_in_the_same_family_as_part4(
    multiplicity_sim: ModuleType,
) -> None:
    """One trend test cannot cost `ALPHA/28` in part 5 and `ALPHA/154` in part 4 of the same family."""
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


def test_replicates_needed_is_memoized_on_its_rate_vectors(power_analysis: ModuleType) -> None:
    """The fixed-seed sizing scan is cached on rate values and alpha, since only 10 distinct rate vectors repeat across 273 contrasts."""
    fn = power_analysis.replicates_needed
    assert hasattr(fn, "cache_info") and hasattr(fn, "cache_clear"), \
        "replicates_needed must expose its cache for auditing"
    fn.cache_clear()

    a = np.full(power_analysis.N_HARMONICS, 0.9)
    b = np.full(power_analysis.N_HARMONICS, 0.5)
    first = fn(a, b)
    # Equal values in a distinct array object: the key is the values, not the id.
    second = fn(a.copy(), b.copy())
    assert first == second
    info = fn.cache_info()
    assert info.hits == 1 and info.misses == 1, info


def test_paired_powers_has_a_stats_free_fast_path(multiplicity_sim: ModuleType) -> None:
    """``part2``'s grid search discards 3 of 4 returns yet paid for all of them (the discarded ``phi`` upcast cost 1.55 GB)."""
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


def test_omnibus_interaction_power_is_cheaper_by_default(power_analysis: ModuleType) -> None:
    """4,000 GLM fits (~380 s per call) is too expensive a default for an explicit non-gate."""
    default = inspect.signature(
        power_analysis.omnibus_interaction_power).parameters["n_sims"].default
    assert default < 1000, default


# ===========================================================================
# The simulations that certify the tests must model the clustering the study
# assumes: an arm-specific per-replicate latent shared by a replicate's items
# ===========================================================================

def test_icc_zero_is_the_published_simulation_byte_for_byte(multiplicity_sim: ModuleType) -> None:
    """`icc=0.0` must draw exactly what the un-clustered simulation drew, including RNG call order."""
    def draw(**kwargs: Any) -> Any:
        return multiplicity_sim.paired_marks(
            0.9, 0.8, 0.5, 64, 30, np.random.default_rng(7), **kwargs)

    plain_a, plain_b = draw()
    zero_a, zero_b = draw(icc=0.0)
    assert np.array_equal(plain_a, zero_a)
    assert np.array_equal(plain_b, zero_b)


def within_replicate_phi(marks: np.ndarray) -> float:
    """Mean correlation between two items of the same replicate.

    The clustering the study's design effect measures: with `K_HARM` items per
    replicate, a positive value means a replicate's items rise and fall
    together instead of being independent draws.
    """
    x = marks.reshape(-1, marks.shape[-1]).astype(float)
    mu = x.mean()
    centered = x - mu
    row_sums = centered.sum(axis=1)
    k = x.shape[1]
    cross = ((row_sums ** 2) - (centered ** 2).sum(axis=1)).mean() / (k * (k - 1))
    return float(cross / (mu * (1 - mu)))


def test_a_positive_icc_clusters_a_replicates_items_without_moving_the_rate(
        multiplicity_sim: ModuleType) -> None:
    """The latent is a within-replicate effect, not a change of difficulty: marginal rates must stay at `p_a`/`p_b`."""
    args = (0.9, 0.8, 0.5, 400, 30)
    flat_a, flat_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.0)
    clustered_a, clustered_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.4)

    assert abs(within_replicate_phi(flat_a)) < 0.02
    assert within_replicate_phi(clustered_a) > 0.10
    for flat, clustered, rate in ((flat_a, clustered_a, 0.9), (flat_b, clustered_b, 0.8)):
        assert abs(flat.mean() - rate) < 0.01
        assert abs(clustered.mean() - rate) < 0.01


def test_the_replicate_latent_is_arm_specific_not_shared(multiplicity_sim: ModuleType) -> None:
    """Each arm draws its own per-replicate offset, so at rho=0 the two arms' replicate means stay uncorrelated."""
    marks_a, marks_b = multiplicity_sim.paired_marks(
        0.9, 0.9, 0.0, 400, 30, np.random.default_rng(13), icc=0.4)
    per_replicate_a = marks_a.mean(axis=2).ravel()
    per_replicate_b = marks_b.mean(axis=2).ravel()
    assert abs(np.corrcoef(per_replicate_a, per_replicate_b)[0, 1]) < 0.05
    # ... each arm on its own is still clustered at this icc.
    assert within_replicate_phi(marks_a) > 0.10


def test_clustering_inflates_the_item_level_mcnemar_type_i_error(
    multiplicity_sim: ModuleType,
) -> None:
    """Item-level McNemar treats a replicate's 9 marks as 9 independent pairs, so a per-replicate latent inflates its Type I error above nominal."""
    def type_i(icc: float) -> float:
        _unpaired, mcnemar, _phi, _agree = multiplicity_sim._paired_powers(
            0.90, 0.0, 0.5, multiplicity_sim.R_DEFAULT, 4000,
            np.random.default_rng(17), stats=False, icc=icc)
        return mcnemar

    flat, clustered = type_i(0.0), type_i(0.4)
    assert clustered > flat
    assert clustered > multiplicity_sim.ALPHA_BONF


def test_part2_reports_every_icc(multiplicity_sim: ModuleType) -> None:
    """One block and one printed table per icc, each labelled with its icc."""
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        multiplicity_sim.part2(np.random.default_rng(2), n_sims=200, search_sims=100)
    out = multiplicity_sim.OUT["part2"]

    assert set(out["icc"]) == {"0.0", "0.2", "0.4"}
    for icc_key, block in out["icc"].items():
        assert block["rows"] and "nulls" in block
        # Every row records the icc it was simulated at, so a reader of the
        # flattened rows never has to infer it from which block it came from.
        assert {row["icc"] for row in block["rows"]} == {float(icc_key)}
    printed = buf.getvalue()
    for icc in ("0.0", "0.2", "0.4"):
        assert f"icc={icc}" in printed, printed[:400]


def test_the_module_docstring_relates_the_study_design_effect_to_an_icc(
        multiplicity_sim: ModuleType) -> None:
    """A reader must be able to tell which icc row describes this study, from the module docstring naming the measured design effect (or "unknown")."""
    doc = multiplicity_sim.__doc__
    assert "design effect" in doc.lower()
    assert "icc" in doc.lower()
    assert "design_effect" in doc
    # Prose alone is not the contract: the module must actually be able to
    # READ the study's measured design effect, and to say "unknown" when there
    # is no results tree to read it from (this repo ships none).
    assert multiplicity_sim.study_design_effect() is None


def test_each_icc_block_reports_the_design_effect_it_produces(
    multiplicity_sim: ModuleType,
) -> None:
    """Each icc block reports the design effect its own marks produce, since the textbook ``1 + (k-1)*icc`` formula would compare the wrong scales."""
    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        multiplicity_sim.part2(np.random.default_rng(3), n_sims=200, search_sims=100)
    blocks = multiplicity_sim.OUT["part2"]["icc"]
    deffs = [blocks[k]["design_effect_simulated"] for k in ("0.0", "0.2", "0.4")]
    assert all(isinstance(d, float) for d in deffs), deffs
    # No clustering -> the CMH denominator is right, i.e. a ratio of about 1.
    assert 0.8 < deffs[0] < 1.3, deffs
    # ... and more clustering means a more anticonservative denominator.
    assert deffs[0] < deffs[1] < deffs[2], deffs
