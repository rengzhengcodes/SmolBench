"""Contracts for induction-analysis statistical plumbing."""

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


def test_power_analysis_roster_comes_from_the_study_config(power_analysis: ModuleType) -> None:
    """Analysis roster derives from the study configuration."""
    from smolbench.evals import study_config

    assert power_analysis.MODELS == tuple(
        study_config.tag_for(key) for key in study_config.roster_keys()
    )
    assert power_analysis.FAMILIES == {
        family: tuple(study_config.tag_for(key) for key in rungs)
        for family, rungs in study_config.families().items()
    }


def _tie_heavy_vectors(n: int = 200) -> Iterator[np.ndarray]:
    """Yield tie-heavy p-value vectors for correction tests."""
    rng = np.random.default_rng(20260905)
    pool = np.array([2 / 2**30, 2 / 2**16, 1.0, 0.05, 0.05 / 210, 1e-8, 0.5, 0.02])
    for i in range(n):
        m = int(rng.integers(2, 80))
        if i % 3 == 0:
            yield np.round(rng.random(m), 2)
        else:
            yield rng.choice(pool, size=m)


@pytest.mark.parametrize("name", ("holm", "hochberg", "bh"))
def test_rejection_sets_do_not_depend_on_contrast_build_order(paired_analysis: ModuleType,
                                                              significance_report: ModuleType,
                                                              name: str) -> None:
    """Tie ordering cannot change rank-monotone correction decisions."""
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
    assert power_analysis.mcnemar_exact_p(np.array([0]), np.array([0]))[0] == 1.0
    assert power_analysis.mcnemar_exact_p(0, 0) == 1.0
    rng = np.random.default_rng(3)
    b, c = rng.integers(0, 40, 300), rng.integers(0, 40, 300)
    ref = np.minimum(1.0, 2 * binom.cdf(np.minimum(b, c), b + c, 0.5))
    np.testing.assert_allclose(power_analysis.mcnemar_exact_p(b, c), ref, rtol=1e-12)
    assert power_analysis.mcnemar_exact_p(4, 4) == 1.0


def test_design_invariants_are_checked_at_module_scope_and_raise(
    power_analysis: ModuleType,
) -> None:
    """Design gates raise at import because optimization removes assertions."""
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
    """Design gates survive ``python -O``."""
    code = (
        "import sys;"
        f"sys.path.insert(0, {str(ANALYSIS_DIR)!r});"
        f"sys.path.insert(0, {str(NOTEBOOKS_DIR)!r});"
        "import power_analysis as pa;"
        "assert False, 'asserts are live -- this subprocess is not under -O';"
    )
    ok = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True,
                        text=True, cwd=str(REPO_ROOT))
    assert ok.returncode == 0, ok.stderr

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
    """Analysis gates cannot use assertions removed by ``python -O``."""
    source = (ANALYSIS_DIR / f"{module}.py").read_text()
    offenders = [ln for ln in source.splitlines()
                 if ln.lstrip().startswith("assert ")]
    assert not offenders, offenders


@pytest.fixture(scope="module")
def small_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> tuple[Path, tuple[str, str]]:
    """A 6-seed tree with one unparsable replicate filename."""
    tmp_path = tmp_path_factory.mktemp("small-tree")
    build_tree(tmp_path, power_analysis.MODELS, power_analysis.INFOS,
               lambda m, i: ((0.10 if i == "zero" else 0.90), 0.0, "empty",
                             range(SHALLOW_DEPTH)))
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
    assert census[cell]["n"] == SHALLOW_DEPTH * 9


def test_the_census_consumes_the_loader_rather_than_re_reading_the_tree(
    repoint: Callable[[Path], None],
    paired_analysis: ModuleType,
    significance_report: ModuleType,
    small_tree: tuple[Path, tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrasts and census share one loader pass."""
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
    """Focused contrasts reuse family p-values."""
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

    assert len(calls) == power_analysis.N_PRIMARY, len(calls)


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
    """``part2`` uses ``R_DEFAULT`` so resizing remains consistent."""
    source = inspect.getsource(multiplicity_sim.part2)
    assert "30" not in source.replace("R_DEFAULT", ""), source

    assert multiplicity_sim.EQ_R_GRID[0] == multiplicity_sim.R_DEFAULT
    assert list(multiplicity_sim.EQ_R_GRID) == sorted(multiplicity_sim.EQ_R_GRID)
    assert multiplicity_sim.EQ_R_GRID[-1] == max(multiplicity_sim.EQ_R_GRID)


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
    """Checkpoint JSON uses the general ignored results directory."""
    import _power_common

    expected = _power_common.results_dir(multiplicity_sim.__file__, up=1)
    assert multiplicity_sim.OUT_PATH.parent == expected
    assert multiplicity_sim.OUT_PATH.name.endswith(".json")

    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert "multiplicity_sim_results.json" not in gitignore
    assert "notebooks/*/results/" in gitignore


def test_dump_creates_its_own_results_directory(multiplicity_sim: ModuleType, tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """Dump creates the ignored results directory on fresh checkouts."""
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
    source = inspect.getsource(multiplicity_sim.part5)
    assert "pre-registered" not in source.lower().replace("not pre-registered", "")


def test_replicates_needed_is_memoized_on_its_rate_vectors(power_analysis: ModuleType) -> None:
    """Sizing scans cache repeated rate vectors."""
    fn = power_analysis.replicates_needed
    assert hasattr(fn, "cache_info") and hasattr(fn, "cache_clear"), \
        "replicates_needed must expose its cache for auditing"
    fn.cache_clear()

    a = np.full(power_analysis.N_HARMONICS, 0.9)
    b = np.full(power_analysis.N_HARMONICS, 0.5)
    first = fn(a, b)
    second = fn(a.copy(), b.copy())
    assert first == second
    info = fn.cache_info()
    assert info.hits == 1 and info.misses == 1, info


def test_paired_powers_has_a_stats_free_fast_path(multiplicity_sim: ModuleType) -> None:
    """Grid searches skip unneeded diagnostics to limit memory."""
    params = inspect.signature(multiplicity_sim._paired_powers).parameters
    assert "stats" in params and params["stats"].default is True

    args = (0.95, 0.05, 0.5, 30, 400)
    full = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=True)
    fast = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=False)
    assert fast[0] == full[0] and fast[1] == full[1]
    assert fast[2] is None and fast[3] is None


def test_omnibus_interaction_power_is_cheaper_by_default(power_analysis: ModuleType) -> None:
    """Non-gate defaults avoid expensive GLM fits."""
    default = inspect.signature(
        power_analysis.omnibus_interaction_power).parameters["n_sims"].default
    assert default < 1000, default


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
    """Return mean within-replicate item correlation."""
    x = marks.reshape(-1, marks.shape[-1]).astype(float)
    mu = x.mean()
    centered = x - mu
    row_sums = centered.sum(axis=1)
    k = x.shape[1]
    cross = ((row_sums ** 2) - (centered ** 2).sum(axis=1)).mean() / (k * (k - 1))
    return float(cross / (mu * (1 - mu)))


def test_a_positive_icc_clusters_a_replicates_items_without_moving_the_rate(
        multiplicity_sim: ModuleType) -> None:
    """A replicate latent preserves marginal arm rates."""
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
    """Arm-specific offsets keep independent arms uncorrelated."""
    marks_a, marks_b = multiplicity_sim.paired_marks(
        0.9, 0.9, 0.0, 400, 30, np.random.default_rng(13), icc=0.4)
    per_replicate_a = marks_a.mean(axis=2).ravel()
    per_replicate_b = marks_b.mean(axis=2).ravel()
    assert abs(np.corrcoef(per_replicate_a, per_replicate_b)[0, 1]) < 0.05
    assert within_replicate_phi(marks_a) > 0.10


def test_clustering_inflates_the_item_level_mcnemar_type_i_error(
    multiplicity_sim: ModuleType,
) -> None:
    """Clustering inflates item-level McNemar Type-I error."""
    def type_i(icc: float) -> float:
        _unpaired, mcnemar, _phi, _agree = multiplicity_sim._paired_powers(
            0.90, 0.0, 0.5, multiplicity_sim.R_DEFAULT, 4000,
            np.random.default_rng(17), stats=False, icc=icc)
        return mcnemar

    flat, clustered = type_i(0.0), type_i(0.4)
    assert clustered > flat
    assert clustered > multiplicity_sim.ALPHA_BONF


def test_part2_reports_every_icc(multiplicity_sim: ModuleType) -> None:
    """Each ICC has a labeled output block."""
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        multiplicity_sim.part2(np.random.default_rng(2), n_sims=200, search_sims=100)
    out = multiplicity_sim.OUT["part2"]

    assert set(out["icc"]) == {"0.0", "0.2", "0.4"}
    for icc_key, block in out["icc"].items():
        assert block["rows"] and "nulls" in block
        assert {row["icc"] for row in block["rows"]} == {float(icc_key)}
    printed = buf.getvalue()
    for icc in ("0.0", "0.2", "0.4"):
        assert f"icc={icc}" in printed, printed[:400]


def test_the_module_docstring_relates_the_study_design_effect_to_an_icc(
        multiplicity_sim: ModuleType) -> None:
    """Module documentation identifies the study design effect and ICC."""
    doc = multiplicity_sim.__doc__
    assert "design effect" in doc.lower()
    assert "icc" in doc.lower()
    assert "design_effect" in doc
    assert multiplicity_sim.study_design_effect() is None


def test_each_icc_block_reports_the_design_effect_it_produces(
    multiplicity_sim: ModuleType,
) -> None:
    """Each ICC block reports its simulated design effect."""
    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        multiplicity_sim.part2(np.random.default_rng(3), n_sims=200, search_sims=100)
    blocks = multiplicity_sim.OUT["part2"]["icc"]
    deffs = [blocks[k]["design_effect_simulated"] for k in ("0.0", "0.2", "0.4")]
    assert all(isinstance(d, float) for d in deffs), deffs
    assert 0.8 < deffs[0] < 1.3, deffs
    assert deffs[0] < deffs[1] < deffs[2], deffs


def test_dropping_invalid_items_keeps_each_survivor_in_its_own_harmonic(
    paired_analysis: ModuleType,
) -> None:
    """Alignment reports original harmonic positions, not retained-item offsets."""
    n = paired_analysis.N_HARMONICS
    seeds = (0, 1, 2)
    # Each seed loses a different harmonic, so retained offsets diverge from positions.
    invalid = {0: 0, 1: n // 2, 2: n - 1}
    key_a, key_b = ("m", "intens"), ("m", "extens")
    correct = {k: {s: np.ones(n, dtype=bool) for s in seeds} for k in (key_a, key_b)}
    valid = {}
    for k in (key_a, key_b):
        valid[k] = {s: np.ones(n, dtype=bool) for s in seeds}
    for s, pos in invalid.items():
        valid[key_a][s][pos] = False

    _a, _b, sidx, hidx = paired_analysis.aligned(correct, valid, key_a, key_b, True)

    for i, s in enumerate(seeds):
        expected = [h for h in range(n) if h != invalid[s]]
        assert list(hidx[sidx == i]) == expected, (s, hidx[sidx == i])
    assert list(np.unique(hidx)) == list(range(n))
