"""Contracts for induction-analysis statistical plumbing."""

import contextlib
import io
import json
import subprocess
import sys
import warnings
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

# pylint: disable=unused-import  # fixture names register pytest fixtures
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


def test_power_analysis_roster_comes_from_the_study_config(
    power_analysis: ModuleType,
) -> None:
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
def test_rejection_sets_do_not_depend_on_contrast_build_order(
    paired_analysis: ModuleType, significance_report: ModuleType, name: str
) -> None:
    """Tie ordering cannot change rank-monotone correction decisions."""
    fn = getattr(significance_report if name == "hochberg" else paired_analysis, name)
    rng = np.random.default_rng(7)
    for pvals in _tie_heavy_vectors(60):
        perm = rng.permutation(pvals.size)
        base = fn(pvals, 0.05)
        permuted = fn(pvals[perm], 0.05)
        assert np.array_equal(permuted, base[perm]), (pvals, perm)


def test_mcnemar_is_defined_once(
    power_analysis: ModuleType,
    paired_analysis: ModuleType,
    multiplicity_sim: ModuleType,
) -> None:
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


def test_design_invariants_pin_roster_identity(
    power_analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A same-family checkpoint swap keeps every count but must still fail."""
    power_analysis.check_design_invariants()
    old, new = power_analysis.MODELS[0], "qwen35_9b"
    monkeypatch.setattr(
        power_analysis,
        "FAMILIES",
        {
            fam: tuple(new if t == old else t for t in rungs)
            for fam, rungs in power_analysis.FAMILIES.items()
        },
    )
    monkeypatch.setattr(
        power_analysis,
        "MODELS",
        tuple(new if t == old else t for t in power_analysis.MODELS),
    )
    assert len(power_analysis.build_primary_contrasts()) == power_analysis.N_PRIMARY
    with pytest.raises(RuntimeError, match="pre-registered tags"):
        power_analysis.check_design_invariants()


def test_design_invariants_pin_roster_keys_not_only_tags(
    power_analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A checkpoint swap that keeps the old tag must still fail on the key."""
    keys = list(power_analysis.ROSTER_KEYS)
    keys[0] = "qwen3.5-9b"
    monkeypatch.setattr(power_analysis, "ROSTER_KEYS", tuple(keys))
    assert power_analysis.MODELS == power_analysis.PREREGISTERED_MODELS
    with pytest.raises(RuntimeError, match="pre-registered roster"):
        power_analysis.check_design_invariants()


def test_design_invariants_survive_python_dash_o() -> None:
    """Design gates survive ``python -O``."""
    code = (
        "import sys;"
        f"sys.path.insert(0, {str(ANALYSIS_DIR)!r});"
        f"sys.path.insert(0, {str(NOTEBOOKS_DIR)!r});"
        "import power_analysis as pa;"
        "assert False, 'asserts are live -- this subprocess is not under -O';"
        "pa.N_PRIMARY = pa.N_PRIMARY - 1;"
        "pa.check_design_invariants()"
    )
    result = subprocess.run(
        [sys.executable, "-O", "-c", code],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert result.returncode != 0, result.stdout
    assert "RuntimeError" in result.stderr, result.stderr


@pytest.fixture(scope="module")
def small_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> tuple[Path, tuple[str, str]]:
    """A 6-seed tree with one unparsable replicate filename."""
    tmp_path = tmp_path_factory.mktemp("small-tree")
    build_tree(
        tmp_path,
        power_analysis.MODELS,
        power_analysis.INFOS,
        lambda m, i: (
            (0.10 if i == "zero" else 0.90),
            0.0,
            "empty",
            range(SHALLOW_DEPTH),
        ),
    )
    bogus = Marks(
        model="stub-model",
        marks=tuple(
            Mark(query=f"q{i}", answer=i, response="x", score=0, compliance="empty")
            for i in range(9)
        ),
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


def test_paired_report_handles_no_measurable_design_effects(
    repoint: Callable[[Path], None],
    power_analysis: ModuleType,
    paired_analysis: ModuleType,
    tmp_path: Path,
) -> None:
    """Identical cells produce no measurable design effects but still report cleanly."""
    source = (power_analysis.MODELS[0], power_analysis.INFOS[0])
    copies = {
        (model, info): source
        for model in power_analysis.MODELS
        for info in power_analysis.INFOS
        if (model, info) != source
    }
    build_tree(
        tmp_path,
        power_analysis.MODELS,
        power_analysis.INFOS,
        lambda _model, _info: (
            0.90,
            0.0,
            "empty",
            range(SHALLOW_DEPTH),
        ),
        copies=copies,
    )
    repoint(tmp_path)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        paired_analysis.main()
    assert (
        "Clustering / cross-stratum covariance: no measurable PRIMARY contrasts "
        "(every contrast has zero independence-assumed variance), so no design "
        "effect is reported."
    ) in buf.getvalue()


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
        Marks,
        "load",
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
    paired_analysis: ModuleType,
    power_analysis: ModuleType,
    small_tree: tuple[Path, tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Focused contrasts reuse family p-values."""
    root, _cell = small_tree
    repoint(root)
    calls = []
    real = paired_analysis.signflip_exact_p
    monkeypatch.setattr(
        paired_analysis,
        "signflip_exact_p",
        lambda diffs: calls.append(1) or real(diffs),
    )

    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        extens_vs_noise.main()

    assert len(calls) == power_analysis.N_PRIMARY, len(calls)


def test_monte_carlo_output_lands_in_the_results_dir(
    multiplicity_sim: ModuleType,
) -> None:
    """Checkpoint JSON uses the general ignored results directory."""
    import _power_common

    expected = _power_common.results_dir(multiplicity_sim.__file__, up=1)
    assert multiplicity_sim.OUT_PATH.parent == expected
    assert multiplicity_sim.OUT_PATH.name.endswith(".json")


def test_dump_creates_its_own_results_directory(
    multiplicity_sim: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dump creates the ignored results directory on fresh checkouts."""
    target = tmp_path / "results" / "multiplicity_sim_results.json"
    assert not target.parent.exists()
    monkeypatch.setattr(multiplicity_sim, "OUT_PATH", target)
    monkeypatch.setattr(multiplicity_sim, "OUT", {"probe": 1})

    multiplicity_sim.dump("probe")

    assert target.exists()
    assert json.loads(target.read_text()) == {"probe": 1}


def test_dump_keeps_previous_checkpoint_when_write_fails(
    multiplicity_sim: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed checkpoint write does not replace the previous JSON."""
    target = tmp_path / "multiplicity_sim_results.json"
    monkeypatch.setattr(multiplicity_sim, "OUT_PATH", target)
    monkeypatch.setattr(multiplicity_sim, "OUT", {"first": 1})
    multiplicity_sim.dump("first")

    def fail_dump(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("simulated checkpoint failure")

    monkeypatch.setattr(multiplicity_sim.json, "dump", fail_dump)
    monkeypatch.setattr(multiplicity_sim, "OUT", {"second": 2})
    with pytest.raises(RuntimeError, match="simulated checkpoint failure"):
        multiplicity_sim.dump("second")

    assert json.loads(target.read_text()) == {"first": 1}
    assert [p.name for p in tmp_path.iterdir()] == [target.name]


def test_contrast_row_handles_empty_drop_invalid_pairs(
    paired_analysis: ModuleType,
) -> None:
    """Dropping all invalid marks returns empty accuracies without warnings."""
    key_a = ("model_a", "intens")
    key_b = ("model_b", "noise_intens")
    correct = {
        key_a: {seed: np.ones(9, dtype=bool) for seed in range(2)},
        key_b: {seed: np.zeros(9, dtype=bool) for seed in range(2)},
    }
    valid = {
        key_a: {seed: np.ones(9, dtype=bool) for seed in range(2)},
        key_b: {seed: np.zeros(9, dtype=bool) for seed in range(2)},
    }
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        row = paired_analysis.contrast_row(
            correct, valid, key_a, key_b, drop_invalid=True
        )

    assert row["n"] == 0
    assert row["acc_a"] is None
    assert row["acc_b"] is None


def test_part5_prices_the_trend_test_in_the_same_family_as_part4(
    multiplicity_sim: ModuleType,
) -> None:
    """One trend test cannot cost `ALPHA/28` in part 5 and `ALPHA/154` in part 4 of the same family."""
    alpha = multiplicity_sim.ALPHA
    rng = np.random.default_rng(0)
    with contextlib.redirect_stdout(io.StringIO()):
        multiplicity_sim.part5(rng, n_sims=200)
    part5 = multiplicity_sim.OUT["part5"]

    assert part5["alpha_trend_studywide"] == pytest.approx(alpha / 154)
    assert part5["alpha_trend_only"] == pytest.approx(alpha / 28)
    assert part5["alpha_pairwise"] == pytest.approx(alpha / 210)
    for row in part5["rows"]:
        assert "trend_studywide" in row and "trend_trend_only_family" in row


def test_replicates_needed_is_memoized_on_its_rate_vectors(
    power_analysis: ModuleType,
) -> None:
    """Sizing scans cache repeated rate vectors."""
    fn = power_analysis.replicates_needed
    assert hasattr(fn, "cache_info") and hasattr(
        fn, "cache_clear"
    ), "replicates_needed must expose its cache for auditing"
    fn.cache_clear()

    a = np.full(power_analysis.N_HARMONICS, 0.9)
    b = np.full(power_analysis.N_HARMONICS, 0.5)
    first = fn(a, b)
    second = fn(a.copy(), b.copy())
    assert first == second
    info = fn.cache_info()
    assert info.hits == 1 and info.misses == 1, info


def test_equivalence_replicates_does_not_accept_saturated_arms_at_r_one(
    power_analysis: ModuleType,
) -> None:
    """Agresti–Coull intervals prevent saturated arms from having zero width."""
    rates = np.ones(power_analysis.N_HARMONICS)
    result = power_analysis.equivalence_replicates(
        rates, rates, 0.05, np.random.default_rng(0), n_sims=500
    )
    assert result is None or result > 1


def test_equivalence_replicates_finds_generous_margin_quickly(
    power_analysis: ModuleType,
) -> None:
    """A generous equivalence margin remains easy to satisfy."""
    rates = np.full(power_analysis.N_HARMONICS, 0.5)
    result = power_analysis.equivalence_replicates(
        rates, rates, 0.5, np.random.default_rng(0), n_sims=500
    )
    assert isinstance(result, int) and result <= 5


def test_equivalence_power_pools_successes_across_harmonics(
    power_analysis: ModuleType,
) -> None:
    """Saturated arms pool to total/total; per-harmonic counts would sit near 1/9."""
    rates = np.ones(power_analysis.N_HARMONICS)
    curve = power_analysis._equivalence_power_curve(
        rates, 0.05, np.random.default_rng(0), 0.05, 200
    )
    # Pooled: diff = 0 and the Agresti–Caffo half-width at R=10 is ~0.025 < 0.05.
    # Unpooled counts give adjusted rates near 0.12 and a half-width near 0.08.
    assert curve[10] == 1.0


def test_sizing_scan_uses_common_random_numbers(power_analysis: ModuleType) -> None:
    """Nested draws make the power curve reproducible, and the crossing is sustained."""
    fn = power_analysis.replicates_needed
    fn.cache_clear()
    a = np.full(power_analysis.N_HARMONICS, 0.75)
    b = np.full(power_analysis.N_HARMONICS, 0.55)
    needed, curve = fn(a, b)
    fn.cache_clear()
    needed_again, curve_again = fn(a, b)
    assert needed == needed_again and curve == curve_again

    reps = sorted(curve)
    assert reps == list(range(1, power_analysis.MAX_REPLICATES + 1))
    for target, r_hit in needed.items():
        assert r_hit == min(
            (
                r
                for r in reps
                if all(curve[later] >= target for later in reps if later >= r)
            ),
            default=None,
        )


def test_sizing_crossing_is_sustained_not_first_hit(
    power_analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A noisy first crossing is not accepted when later power dips below target."""

    def fake_cmh_stat(_succ_a: np.ndarray, _succ_b: np.ndarray, n: int) -> np.ndarray:
        fraction = 0.85 if n in (5, 6) else 0.79 if n == 7 else 0.85 if n >= 8 else 0.1
        n_reject = int(round(fraction * power_analysis.N_SIMS))
        return np.concatenate(
            (np.full(n_reject, 1e6), np.zeros(power_analysis.N_SIMS - n_reject))
        )

    power_analysis._sizing_scan.cache_clear()
    monkeypatch.setattr(power_analysis, "cmh_stat", fake_cmh_stat)
    try:
        rates = np.full(power_analysis.N_HARMONICS, 0.5)
        needed, curve = power_analysis.replicates_needed(rates, rates)
        assert needed[0.80] == 8
        assert needed[0.90] is None
        assert curve[5] == pytest.approx(0.85)
        assert curve[7] == pytest.approx(0.79)
    finally:
        power_analysis._sizing_scan.cache_clear()


def test_equivalence_crossing_is_sustained_not_first_hit(
    power_analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equivalence sizing rejects a noisy first crossing."""

    def fake_power_curve(
        _common: np.ndarray,
        _delta: float,
        _rng: np.random.Generator,
        _alpha: float,
        _n_sims: int,
    ) -> dict[int, float]:
        return {
            n: 0.85 if n in (5, 6) else 0.79 if n == 7 else 0.85 if n >= 8 else 0.1
            for n in range(1, power_analysis.MAX_REPLICATES + 1)
        }

    monkeypatch.setattr(power_analysis, "_equivalence_power_curve", fake_power_curve)
    rates = np.full(power_analysis.N_HARMONICS, 0.5)
    assert (
        power_analysis.equivalence_replicates(
            rates, rates, 0.5, np.random.default_rng(0), n_sims=500
        )
        == 8
    )


def test_recommended_replicates_carries_censored_contrasts(
    power_analysis: ModuleType,
) -> None:
    """A censored family has no whole-family R, and the render says so instead of dropping them."""
    censored = power_analysis.recommended_replicates(40, 3, 210)
    assert censored["family_r"] is None
    assert censored["n_powered"] == 207 and censored["n_primary"] == 210
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        power_analysis.render_recommended_replicates(censored)
    out = buf.getvalue()
    assert "CENSORED" in out and "3 of 210" in out and "207 of 210" in out, out
    assert "excluded" not in out.lower(), out

    full = power_analysis.recommended_replicates(40, 0, 210)
    assert full["family_r"] == 40
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        power_analysis.render_recommended_replicates(full)
    assert "fully powered" in buf.getvalue()


def test_primary_contrasts_table_reports_the_family_size(
    power_analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`r_star` covers every powerable contrast and `family_r` is `None` while any is censored."""

    def fake_results(contrasts: list, *_args: Any) -> list:
        rows = []
        for i, (name, _ka, _kb) in enumerate(contrasts):
            r80 = None if i == 0 else 10 + (i % 5)
            rows.append((name, None, None, {0.80: r80, 0.90: None}, None))
        return rows

    monkeypatch.setattr(power_analysis, "_compute_sizing_results", fake_results)
    data = power_analysis.primary_contrasts_table({}, {})
    assert data["n_primary"] == len(data["results"]) == power_analysis.N_PRIMARY
    assert data["n_censored"] == 1 and data["family_r"] is None
    assert data["r_star"] == 14


def test_paired_powers_has_a_stats_free_fast_path(multiplicity_sim: ModuleType) -> None:
    """Grid searches skip unneeded diagnostics to limit memory."""
    args = (0.95, 0.05, 0.5, 30, 400)
    full = multiplicity_sim._paired_powers(*args, np.random.default_rng(11), stats=True)
    fast = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=False
    )
    assert fast[0] == full[0] and fast[1] == full[1]
    assert fast[2] is None and fast[3] is None


def test_icc_zero_is_the_published_simulation_byte_for_byte(
    multiplicity_sim: ModuleType,
) -> None:
    """`icc=0.0` must draw exactly what the un-clustered simulation drew, including RNG call order."""

    def draw(**kwargs: Any) -> Any:
        return multiplicity_sim.paired_marks(
            0.9, 0.8, 0.5, 64, 30, np.random.default_rng(7), **kwargs
        )

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
    cross = ((row_sums**2) - (centered**2).sum(axis=1)).mean() / (k * (k - 1))
    return float(cross / (mu * (1 - mu)))


def test_a_positive_icc_clusters_a_replicates_items_without_moving_the_rate(
    multiplicity_sim: ModuleType,
) -> None:
    """A replicate latent preserves marginal arm rates."""
    args = (0.9, 0.8, 0.5, 400, 30)
    flat_a, flat_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.0
    )
    clustered_a, clustered_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.4
    )

    assert abs(within_replicate_phi(flat_a)) < 0.02
    assert within_replicate_phi(clustered_a) > 0.10
    for flat, clustered, rate in (
        (flat_a, clustered_a, 0.9),
        (flat_b, clustered_b, 0.8),
    ):
        assert abs(flat.mean() - rate) < 0.01
        assert abs(clustered.mean() - rate) < 0.01


def test_the_replicate_latent_is_arm_specific_not_shared(
    multiplicity_sim: ModuleType,
) -> None:
    """Arm-specific offsets keep independent arms uncorrelated."""
    marks_a, marks_b = multiplicity_sim.paired_marks(
        0.9, 0.9, 0.0, 400, 30, np.random.default_rng(13), icc=0.4
    )
    per_replicate_a = marks_a.mean(axis=2).ravel()
    per_replicate_b = marks_b.mean(axis=2).ravel()
    assert abs(np.corrcoef(per_replicate_a, per_replicate_b)[0, 1]) < 0.05
    assert within_replicate_phi(marks_a) > 0.10


def test_icc_does_not_attenuate_the_requested_cross_arm_correlation(
    multiplicity_sim: ModuleType,
) -> None:
    """Clustering must not dilute `rho`; the mark-level phi should match the un-clustered draw."""

    def phi(marks_a: np.ndarray, marks_b: np.ndarray) -> float:
        return float(
            np.corrcoef(marks_a.ravel().astype(float), marks_b.ravel().astype(float))[
                0, 1
            ]
        )

    args = (0.7, 0.7, 0.6, 400, 30)
    flat = phi(*multiplicity_sim.paired_marks(*args, np.random.default_rng(17)))
    clustered = phi(
        *multiplicity_sim.paired_marks(*args, np.random.default_rng(19), icc=0.4)
    )
    assert flat > 0.3
    assert abs(clustered - flat) < 0.03
    # A dilution to (1 - icc) * rho would move phi by far more than that.
    diluted = phi(
        *multiplicity_sim.paired_marks(
            0.7, 0.7, 0.36, 400, 30, np.random.default_rng(17)
        )
    )
    assert flat - diluted > 0.1


def test_clustering_inflates_the_item_level_mcnemar_type_i_error(
    multiplicity_sim: ModuleType,
) -> None:
    """Clustering inflates item-level McNemar Type-I error."""

    def type_i(icc: float) -> float:
        _unpaired, mcnemar, _phi, _agree = multiplicity_sim._paired_powers(
            0.90,
            0.0,
            0.5,
            multiplicity_sim.R_DEFAULT,
            4000,
            np.random.default_rng(17),
            stats=False,
            icc=icc,
        )
        return mcnemar

    flat, clustered = type_i(0.0), type_i(0.4)
    assert clustered > flat
    assert clustered > multiplicity_sim.ALPHA_BONF


def test_part2_reports_every_icc(multiplicity_sim: ModuleType) -> None:
    """Each ICC has a labeled output block."""
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


def test_study_design_effect_ignores_checkpoint_without_replicates(
    multiplicity_sim: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A checkpoint directory is not a measured study lane."""
    (tmp_path / "multiplicity_sim_results.json").write_text("{}", encoding="utf-8")
    paired_analysis = sys.modules["paired_analysis"]
    monkeypatch.setattr(paired_analysis, "RESULTS_DIR", tmp_path)
    assert multiplicity_sim.study_design_effect() is None


def test_each_icc_block_reports_the_design_effect_it_produces(
    multiplicity_sim: ModuleType,
) -> None:
    """Each ICC block reports its simulated design effect."""
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
