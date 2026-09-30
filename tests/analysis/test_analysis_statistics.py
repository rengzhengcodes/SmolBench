"""Contracts for induction-analysis statistical plumbing."""

import contextlib
import inspect
import io
import json
import shutil
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pytest
from scipy.stats import chi2, norm
from statsmodels.stats.multitest import multipletests

from smolbench.evals import Marks, study_config
from tests._paths import NOTEBOOKS, REPO_ROOT
from tests.analysis._trees import (
    ANALYSIS_DIR,
    DEEP_DEPTH,
    INFOS,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    N_REPLICATES,
    SHALLOW_DEPTH,
    _power_common,
    build_tree,
    extens_vs_noise,
    multiplicity_sim,
    paired_analysis,
    power_analysis,
    profile_for,
    run_captured,
    significance_report,
)

#: First roster cell: the copy source of the all-identical tree, and the cell small_tree's rep_bogus.yaml sits in.
_FIRST_CELL = (MODELS[0], "intens")


def _noisy_curve(n: int) -> float:
    """Simulated power at `n` replicates whose first crossing is not sustained: it dips at seven."""
    return 0.79 if n == 7 else 0.85 if n >= 5 else 0.1


def test_apply_corrections_matches_statsmodels() -> None:
    """Batched masks agree with statsmodels row by row away from exact ties."""
    alpha = _power_common.ALPHA
    rng = np.random.default_rng(7)
    pv = np.vstack(
        [
            rng.uniform(0, 1, size=(40, 6)),
            rng.uniform(0, 0.02, size=(10, 6)),
            np.array([[0.001, 0.011, 0.021, 0.031, 0.041, 0.9]]),
        ]
    )
    got = _power_common.apply_corrections(pv, alpha)
    methods = {
        "Bonferroni": "bonferroni",
        "Holm": "holm",
        "Hochberg": "simes-hochberg",
        "BH": "fdr_bh",
    }
    for name, method in methods.items():
        for row, mask in zip(pv, got[name]):
            expected = multipletests(row, alpha=alpha, method=method)[0]
            assert list(mask) == list(expected), (name, row.tolist())


def test_apply_corrections_share_one_inclusive_boundary() -> None:
    """Every procedure rejects a p-value sitting exactly on its threshold."""
    alpha = _power_common.ALPHA
    m = 4
    pv = np.array(
        [
            [alpha / m, alpha / (m - 1), 0.5, 0.9],
            [alpha * 1 / m, alpha * 2 / m, alpha * 3 / m, alpha * 4 / m],
        ]
    )
    got = _power_common.apply_corrections(pv, alpha)
    assert list(got["Bonferroni"][0]) == [True, False, False, False]
    assert list(got["Holm"][0]) == [True, True, False, False]
    assert list(got["Hochberg"][0]) == [True, True, False, False]
    assert list(got["BH"][1]) == [True, True, True, True]


def test_power_analysis_roster_comes_from_the_study_config() -> None:
    """Analysis roster derives from the study configuration."""
    assert power_analysis.MODELS == tuple(
        study_config.tag_for(key) for key in study_config.roster_keys()
    )
    assert power_analysis.FAMILIES == {
        family: tuple(study_config.tag_for(key) for key in rungs)
        for family, rungs in study_config.families().items()
    }


@pytest.mark.parametrize("method", ("Holm", "Hochberg", "BH"))
def test_rejection_sets_do_not_depend_on_contrast_build_order(method: str) -> None:
    """Tie ordering cannot change `method`'s rank-monotone rejection decisions."""
    alpha = _power_common.ALPHA
    rng = np.random.default_rng(7)
    tie_rng = np.random.default_rng(20260905)
    # Sign-flip floors at study and deep depth, ALPHA, the primary share, and tie-prone values.
    pool = np.array(
        [
            2 / 2**N_REPLICATES,
            2 / 2**DEEP_DEPTH,
            1.0,
            alpha,
            alpha / N_PRIMARY,
            1e-8,
            0.5,
            0.02,
        ]
    )
    for i in range(60):
        m = int(tie_rng.integers(2, 80))
        pvals = (
            np.round(tie_rng.random(m), 2)
            if i % 3 == 0
            else tie_rng.choice(pool, size=m)
        )
        perm = rng.permutation(pvals.size)
        base = paired_analysis.rejections(pvals, method, alpha)
        permuted = paired_analysis.rejections(pvals[perm], method, alpha)
        assert np.array_equal(permuted, base[perm]), (pvals, perm)


def test_mcnemar_is_defined_once() -> None:
    """One implementation serves every call site."""
    assert paired_analysis.mcnemar_exact_p is power_analysis.mcnemar_exact_p
    assert multiplicity_sim.mcnemar_exact_p is power_analysis.mcnemar_exact_p


def test_design_invariants_pin_roster_identity(monkeypatch: pytest.MonkeyPatch) -> None:
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
    with pytest.raises(RuntimeError, match="pre-registered roster"):
        power_analysis.check_design_invariants()


def test_design_invariants_pin_roster_keys_not_only_tags(
    monkeypatch: pytest.MonkeyPatch,
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
        f"sys.path.insert(0, {str(NOTEBOOKS)!r});"
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
def small_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a 6-seed tree with one unparsable replicate filename in `_FIRST_CELL`."""
    tmp_path = tmp_path_factory.mktemp("small-tree")
    build_tree(tmp_path, profile_for(depth=SHALLOW_DEPTH))
    cell_dir = tmp_path / f"{_FIRST_CELL[0]}_{_FIRST_CELL[1]}"
    shutil.copyfile(cell_dir / "rep_0.yaml", cell_dir / "rep_bogus.yaml")
    return tmp_path


def test_walkers_skip_an_unparsable_replicate_filename(small_tree: Path) -> None:
    """The loader skips a non-replicate filename and the census inherits its seed set."""
    loaded = paired_analysis.load_marks(small_tree)
    assert sorted(loaded.correct[_FIRST_CELL]) == list(range(SHALLOW_DEPTH))

    census = significance_report.compliance_census(loaded)
    assert census[_FIRST_CELL]["n"] == SHALLOW_DEPTH * N_HARMONICS


def test_paired_report_handles_no_measurable_design_effects(tmp_path: Path) -> None:
    """Identical cells produce no measurable design effects but report cleanly."""
    copies = {
        (model, info): _FIRST_CELL
        for model in MODELS
        for info in INFOS
        if (model, info) != _FIRST_CELL
    }
    build_tree(tmp_path, lambda _m, _i: (0.90, 0.0, range(SHALLOW_DEPTH)), copies)
    assert (
        "Clustering / cross-stratum covariance: no measurable PRIMARY contrasts "
        "(every contrast has zero independence-assumed variance), so no design "
        "effect is reported."
    ) in run_captured(lambda: paired_analysis.main(tmp_path))


def test_the_census_consumes_the_loader_rather_than_re_reading_the_tree(
    small_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Contrasts and census share one loader pass."""
    reads = []
    original = Marks.load.__func__
    monkeypatch.setattr(
        Marks,
        "load",
        classmethod(lambda cls, path: reads.append(str(path)) or original(cls, path)),
    )
    loaded = paired_analysis.load_marks(small_tree)
    after_load = len(reads)
    census = significance_report.compliance_census(loaded)

    n_cells = len(loaded.correct)
    assert n_cells == len(MODELS) * len(INFOS)
    assert after_load == n_cells * SHALLOW_DEPTH, after_load
    assert len(reads) == after_load, reads[after_load:]
    assert len(census) == n_cells


def test_extens_vs_noise_reuses_the_family_p_values_it_already_computed(
    small_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Focused contrasts reuse family p-values."""
    calls = []
    real = paired_analysis.signflip_exact_p
    monkeypatch.setattr(
        paired_analysis,
        "signflip_exact_p",
        lambda diffs: calls.append(1) or real(diffs),
    )
    run_captured(lambda: extens_vs_noise.main(small_tree))

    assert len(calls) == N_PRIMARY, len(calls)


def test_monte_carlo_main_routes_default_output_to_explicit_results_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit results directory controls the default checkpoint path."""
    for i in range(1, 6):
        monkeypatch.setattr(
            multiplicity_sim, f"part{i}", lambda *_a, part=i, **_k: {"part": part}
        )
    multiplicity_sim.main(results_dir=tmp_path)

    target = tmp_path / multiplicity_sim.OUT_NAME
    assert target.exists()
    assert json.loads(target.read_text())["part5"] == {"part": 5}
    # main()'s own default is the study results tree run_all hands every script.
    assert inspect.signature(multiplicity_sim.main).parameters[
        "results_dir"
    ].default == _power_common.results_dir("induction")


def test_dump_creates_its_own_results_directory(tmp_path: Path) -> None:
    """Dump creates the ignored results directory on fresh checkouts."""
    target = tmp_path / "results" / multiplicity_sim.OUT_NAME
    assert not target.parent.exists()
    multiplicity_sim.dump({"probe": 1}, target, "probe")

    assert target.exists()
    assert json.loads(target.read_text()) == {"probe": 1}


def test_dump_keeps_previous_checkpoint_when_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed checkpoint write does not replace the previous JSON."""
    target = tmp_path / multiplicity_sim.OUT_NAME
    multiplicity_sim.dump({"first": 1}, target, "first")

    def failing_dump(*_args: object, **_kwargs: object) -> None:
        """Stand in for ``json.dump``: always raise before anything reaches the file."""
        raise RuntimeError("simulated checkpoint failure")

    monkeypatch.setattr(multiplicity_sim.json, "dump", failing_dump)
    with pytest.raises(RuntimeError, match="simulated checkpoint failure"):
        multiplicity_sim.dump({"second": 2}, target, "second")

    assert json.loads(target.read_text()) == {"first": 1}
    assert [p.name for p in tmp_path.iterdir()] == [target.name]


def test_labeled_rows_handles_empty_drop_invalid_pairs() -> None:
    """Dropping all invalid marks returns empty accuracies without warnings."""
    key_a = ("model_a", "intens")
    key_b = ("model_b", "noise_intens")
    ones = {seed: np.ones(N_HARMONICS, dtype=bool) for seed in range(2)}
    correct = {key_a: ones, key_b: ones}
    valid = {key_a: ones, key_b: {seed: ~v for seed, v in ones.items()}}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        row = paired_analysis.labeled_rows(
            paired_analysis.CellMarks(correct, valid, {}),
            [("empty", key_a, key_b)],
            True,
        )[0]

    assert row["n"] == 0
    assert row["acc_a"] is None
    assert row["acc_b"] is None


def test_part5_prices_the_trend_test_in_the_same_family_as_part4() -> None:
    """Part 5 and part 4 use the same reduced-family correction denominator."""
    alpha = multiplicity_sim.ALPHA
    rng = np.random.default_rng(0)
    with contextlib.redirect_stdout(io.StringIO()):
        part5 = multiplicity_sim.part5(rng, n_sims=200)

    assert part5["alpha_trend_studywide"] == pytest.approx(
        alpha / multiplicity_sim.N_REDUCED
    )
    assert part5["alpha_trend_only"] == pytest.approx(
        alpha / multiplicity_sim.N_LADDERS
    )
    assert part5["alpha_pairwise"] == pytest.approx(alpha / multiplicity_sim.N_PRIMARY)
    for row in part5["rows"]:
        assert "trend_studywide" in row and "trend_trend_only_family" in row


def test_replicates_needed_is_memoized_on_its_rate_vectors() -> None:
    """Sizing scans cache repeated rate vectors."""
    power_analysis._sizing_scan.cache_clear()
    a = np.full(N_HARMONICS, 0.9)
    b = np.full(N_HARMONICS, 0.5)
    first = power_analysis.replicates_needed(a, b)
    second = power_analysis.replicates_needed(a.copy(), b.copy())
    assert first == second
    # pylint: disable-next=no-value-for-parameter  # lru_cache brain mistypes cache_info
    info = power_analysis._sizing_scan.cache_info()
    assert info.hits == 1 and info.misses == 1, info


def test_equivalence_replicates_does_not_accept_saturated_arms_at_r_one() -> None:
    """Agresti–Caffo intervals prevent saturated arms from having zero width."""
    rates = np.ones(N_HARMONICS)
    result = power_analysis.equivalence_replicates(
        rates, rates, 0.05, np.random.default_rng(0), n_sims=500
    )
    # test_equivalence_power_pools_successes_across_harmonics shows power is 1.0 by R=10
    # at this margin, so the scan can neither return 1 nor censor.
    assert 1 < result <= 10


def test_equivalence_replicates_finds_generous_margin_quickly() -> None:
    """A generous equivalence margin remains easy to satisfy."""
    rates = np.full(N_HARMONICS, 0.5)
    result = power_analysis.equivalence_replicates(
        rates, rates, 0.5, np.random.default_rng(0), n_sims=500
    )
    assert isinstance(result, int) and result <= 5


def test_equivalence_power_pools_successes_across_harmonics() -> None:
    """Saturated arms pool to total/total; per-harmonic counts would sit near 1/9."""
    rates = np.ones(N_HARMONICS)
    curve = power_analysis._equivalence_power_curve(
        rates, 0.05, np.random.default_rng(0), _power_common.ALPHA, 200
    )
    # Pooled: diff = 0 and the Agresti–Caffo half-width at R=10 is ~0.025 < 0.05.
    # Unpooled counts give adjusted rates near 0.12 and a half-width near 0.08.
    assert curve[10] == 1.0


def test_sizing_scan_uses_common_random_numbers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The curve is read off two nested Bernoulli streams, one per arm, not fresh draws per R."""
    streams: list[np.ndarray] = []
    real = power_analysis._cumulative_successes
    monkeypatch.setattr(
        power_analysis,
        "_cumulative_successes",
        lambda rng, rates, n: streams.append(real(rng, rates, n)) or streams[-1],
    )
    power_analysis._sizing_scan.cache_clear()
    a = np.full(N_HARMONICS, 0.75)
    b = np.full(N_HARMONICS, 0.55)
    needed, curve = power_analysis.replicates_needed(a, b)
    assert len(streams) == 2, len(streams)
    cum_a, cum_b = streams[0], streams[1]
    crit = chi2.isf(power_analysis.ALPHA_PRIMARY, df=1)
    for r in (1, 5, N_REPLICATES, power_analysis.MAX_REPLICATES):
        stat = power_analysis.cmh_stat(
            cum_a[:, r - 1].astype(np.int64), cum_b[:, r - 1].astype(np.int64), r
        )
        assert curve[r] == float((stat > crit).mean()), r

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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A noisy first crossing is rejected when later power dips below target."""

    def fake_cmh_stat(_succ_a: np.ndarray, _succ_b: np.ndarray, n: int) -> np.ndarray:
        """Return statistics whose rejection fraction at `n` replicates is `_noisy_curve(n)`."""
        n_reject = int(round(_noisy_curve(n) * power_analysis.N_SIMS))
        return np.concatenate(
            (np.full(n_reject, 1e6), np.zeros(power_analysis.N_SIMS - n_reject))
        )

    power_analysis._sizing_scan.cache_clear()
    try:
        monkeypatch.setattr(power_analysis, "cmh_stat", fake_cmh_stat)
        rates = np.full(N_HARMONICS, 0.5)
        needed, curve = power_analysis.replicates_needed(rates, rates)
        assert needed[power_analysis.POWER_TARGETS[0]] == 8
        assert needed[power_analysis.POWER_TARGETS[1]] is None
        assert curve[5] == pytest.approx(0.85)
        assert curve[7] == pytest.approx(0.79)
    finally:
        # The fake's curve would otherwise stay cached for the later sizing tests.
        power_analysis._sizing_scan.cache_clear()


def test_equivalence_crossing_is_sustained_not_first_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Equivalence sizing rejects a noisy first crossing."""
    curve = {n: _noisy_curve(n) for n in range(1, power_analysis.MAX_REPLICATES + 1)}
    rates = np.full(N_HARMONICS, 0.5)
    monkeypatch.setattr(
        power_analysis, "_equivalence_power_curve", lambda *_a, **_k: curve
    )
    assert (
        power_analysis.equivalence_replicates(
            rates, rates, 0.5, np.random.default_rng(0), n_sims=500
        )
        == 8
    )


def test_render_recommended_replicates_carries_censored_contrasts() -> None:
    """A censored family has no whole-family R, and the render says so instead of dropping them."""
    results = [()] * N_PRIMARY
    out = run_captured(
        lambda: power_analysis.render_recommended_replicates(
            {"results": results, "r_star": 40, "family_r": None, "n_censored": 3}
        )
    )
    assert (
        "CENSORED" in out
        and f"3 of {N_PRIMARY}" in out
        and f"{N_PRIMARY - 3} of {N_PRIMARY}" in out
    ), out

    assert "fully powered" in run_captured(
        lambda: power_analysis.render_recommended_replicates(
            {"results": results, "r_star": 40, "family_r": 40, "n_censored": 0}
        )
    )


def test_primary_contrasts_table_reports_the_family_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`r_star` covers powerable contrasts; censored ones prevent `family_r`."""

    def fake_results(
        contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]],
        _rates: dict,
        _pooled: dict,
        _alpha: float,
    ) -> list[power_analysis._SizingResult]:
        """Size every contrast except the first, which stays censored, to exercise whole-family reporting."""
        return [
            (
                name,
                key_a,
                key_b,
                {
                    power_analysis.POWER_TARGETS[0]: None if i == 0 else 10 + i % 5,
                    power_analysis.POWER_TARGETS[1]: None,
                },
                {},
            )
            for i, (name, key_a, key_b) in enumerate(contrasts)
        ]

    monkeypatch.setattr(power_analysis, "_compute_sizing_results", fake_results)
    data = power_analysis.primary_contrasts_table({}, {})
    assert len(data["results"]) == N_PRIMARY
    assert data["n_censored"] == 1 and data["family_r"] is None
    assert data["r_star"] == 14


def test_interaction_diagnostic_is_defined_under_separation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fully saturated pilot separates every interaction fit (statsmodels warns per IRLS step, never raises), yet the LR diagnostic returns a finite rate and lets no warning out."""
    monkeypatch.setattr(power_analysis, "N_SIMS_OMNIBUS_DIAGNOSTIC", 5)
    rates = {(m, i): np.ones(N_HARMONICS) for m in MODELS for i in INFOS}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        power = power_analysis.omnibus_interaction_power(rates, N_REPLICATES)
    assert isinstance(power, float) and 0.0 <= power <= 1.0


def test_paired_powers_has_a_stats_free_fast_path() -> None:
    """Grid searches skip unneeded diagnostics to limit memory."""
    args = (0.95, 0.05, 0.5, N_REPLICATES, 400)
    full = multiplicity_sim._paired_powers(*args, np.random.default_rng(11), stats=True)
    fast = multiplicity_sim._paired_powers(
        *args, np.random.default_rng(11), stats=False
    )
    assert fast[0] == full[0] and fast[1] == full[1]
    assert fast[2] is None and fast[3] is None


def test_icc_zero_consumes_only_the_two_item_latent_draws() -> None:
    """`icc=0.0` draws exactly the two item latents and nothing for the replicate latent, leaving the stream where the un-clustered draw leaves it."""
    n_sims = 64
    rng = np.random.default_rng(7)
    marks_a, _ = multiplicity_sim.paired_marks(
        0.9, 0.8, 0.5, n_sims, N_REPLICATES, rng, icc=0.0
    )
    reference = np.random.default_rng(7)
    z1 = reference.standard_normal(
        (2, n_sims, N_REPLICATES, N_HARMONICS), dtype=np.float32
    )[0]
    assert rng.bit_generator.state == reference.bit_generator.state
    assert np.array_equal(marks_a, z1 < norm.ppf(0.9))


def _within_replicate_phi(marks: np.ndarray) -> float:
    """Mean ``np.corrcoef`` over distinct item pairs (items on the last axis): an independent reference for the pooled-moment ``phi_binary`` PART 3 prints."""
    x = marks.reshape(-1, marks.shape[-1]).astype(float)
    corr = np.corrcoef(x.T)
    return float(corr[np.triu_indices(x.shape[1], 1)].mean())


def test_a_positive_icc_clusters_a_replicates_items_without_moving_the_rate() -> None:
    """A replicate latent preserves marginal arm rates."""
    args = (0.9, 0.8, 0.5, 400, N_REPLICATES)
    flat_a, flat_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.0
    )
    clustered_a, clustered_b = multiplicity_sim.paired_marks(
        *args, np.random.default_rng(11), icc=0.4
    )

    assert abs(_within_replicate_phi(flat_a)) < 0.02
    assert _within_replicate_phi(clustered_a) > 0.10
    for flat, clustered, rate in (
        (flat_a, clustered_a, 0.9),
        (flat_b, clustered_b, 0.8),
    ):
        assert abs(flat.mean() - rate) < 0.01
        assert abs(clustered.mean() - rate) < 0.01


def test_the_replicate_latent_is_arm_specific_not_shared() -> None:
    """Arm-specific offsets keep independent arms uncorrelated."""
    marks_a, marks_b = multiplicity_sim.paired_marks(
        0.9, 0.9, 0.0, 400, N_REPLICATES, np.random.default_rng(13), icc=0.4
    )
    per_replicate_a = marks_a.mean(axis=2).ravel()
    per_replicate_b = marks_b.mean(axis=2).ravel()
    assert abs(np.corrcoef(per_replicate_a, per_replicate_b)[0, 1]) < 0.05
    assert _within_replicate_phi(marks_a) > 0.10


def test_icc_does_not_attenuate_the_requested_cross_arm_correlation() -> None:
    """Clustering must not dilute `rho`; the mark-level phi should match the un-clustered draw."""
    correlations = []
    for rho, seed, icc in ((0.6, 17, 0.0), (0.6, 19, 0.4), (0.36, 17, 0.0)):
        arms = multiplicity_sim.paired_marks(
            0.7, 0.7, rho, 400, N_REPLICATES, np.random.default_rng(seed), icc=icc
        )
        correlations.append(
            np.corrcoef(np.asarray(arms, dtype=float).reshape(2, -1))[0, 1]
        )
    flat, clustered, diluted = np.array(correlations)
    assert flat > 0.3
    assert abs(clustered - flat) < 0.03
    # A dilution to (1 - icc) * rho would move phi by far more than that.
    assert flat - diluted > 0.1


def test_clustering_inflates_the_item_level_mcnemar_type_i_error() -> None:
    """Clustering inflates item-level McNemar Type-I error."""

    flat, clustered = [
        multiplicity_sim._paired_powers(
            0.90,
            0.0,
            0.5,
            N_REPLICATES,
            4000,
            np.random.default_rng(17),
            stats=False,
            icc=icc,
        )[1]
        for icc in (0.0, 0.4)
    ]
    assert clustered > flat
    assert clustered > multiplicity_sim.ALPHA_PRIMARY


def test_part2_reports_every_icc_and_its_design_effect(tmp_path: Path) -> None:
    """Each ICC block labels its rows and reports the simulated design effect; the empty `tmp_path` keeps synced lanes out of it."""
    buf = io.StringIO()
    # main() seeds part2 from SEED + 2; the test reads the same stream.
    with contextlib.redirect_stdout(buf):
        out = multiplicity_sim.part2(
            np.random.default_rng(_power_common.SEED + 2),
            tmp_path,
            n_sims=200,
            search_sims=100,
        )

    icc_keys = [str(icc) for icc in multiplicity_sim.ICC_GRID]
    assert set(out["icc"]) == set(icc_keys)
    for icc_key, block in out["icc"].items():
        assert block["rows"] and "nulls" in block
        assert {row["icc"] for row in block["rows"]} == {float(icc_key)}
    printed = buf.getvalue()
    for icc in icc_keys:
        assert f"icc={icc}" in printed, printed[:400]
    deffs = [out["icc"][k]["design_effect_simulated"] for k in icc_keys]
    assert all(isinstance(d, float) for d in deffs), deffs
    assert 0.8 < deffs[0] < 1.3, deffs
    assert deffs[0] < deffs[1] < deffs[2], deffs


@pytest.mark.parametrize("match_rung", (0, 1))
def test_part2_searches_eq_r_from_the_first_matching_rung(
    match_rung: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The equivalent-R search lands on `EQ_R_GRID[match_rung]` and records whether it moved beyond study depth."""

    def fake_powers(
        _p_a: float,
        _delta: float,
        _rho: float,
        reps: int,
        _n_sims: int,
        _rng: np.random.Generator,
        stats: bool = True,
        icc: float = 0.0,
    ) -> tuple[float, float, Optional[float], Optional[float]]:
        """Initial estimate when `stats`; otherwise unpaired power matches at every rung except study depth when `match_rung` is 1."""
        if stats:
            return 0.50, 0.80, 0.1, 0.9
        if match_rung == 1 and reps == N_REPLICATES:
            return 0.50, 0.0, None, None
        return 0.80 - multiplicity_sim.EQ_R_TOL / 2, 0.0, None, None

    monkeypatch.setattr(multiplicity_sim, "_paired_powers", fake_powers)
    monkeypatch.setattr(multiplicity_sim, "study_design_effect", lambda *_a, **_k: None)
    with contextlib.redirect_stdout(io.StringIO()):
        out = multiplicity_sim.part2(
            np.random.default_rng(2), tmp_path, n_sims=50, search_sims=50
        )

    rows = out["icc"]["0.0"]["rows"]
    assert all(row["eq_R"] == multiplicity_sim.EQ_R_GRID[match_rung] for row in rows)
    assert all(row["eq_r_advanced"] is (match_rung == 1) for row in rows)


def test_study_design_effect_ignores_checkpoint_without_replicates(
    tmp_path: Path,
) -> None:
    """A checkpoint-only directory is not a measured study lane."""
    (tmp_path / multiplicity_sim.OUT_NAME).write_text("{}", encoding="utf-8")
    assert multiplicity_sim.study_design_effect(tmp_path) is None


def test_dropping_invalid_items_keeps_each_survivor_in_its_own_harmonic() -> None:
    """Alignment reports original harmonic positions, not retained-item offsets."""
    n = N_HARMONICS
    seeds = (0, 1, 2)
    # Each seed loses a different harmonic, so retained offsets diverge from positions.
    invalid = {0: 0, 1: n // 2, 2: n - 1}
    key_a, key_b = ("m", "intens"), ("m", "extens")
    correct = {k: {s: np.ones(n, dtype=bool) for s in seeds} for k in (key_a, key_b)}
    valid = {k: {s: np.ones(n, dtype=bool) for s in seeds} for k in (key_a, key_b)}
    for s, pos in invalid.items():
        valid[key_a][s][pos] = False

    marks = paired_analysis.CellMarks(correct, valid, {})
    _a, _b, sidx, hidx = paired_analysis.aligned(marks, key_a, key_b, True)

    for i, s in enumerate(seeds):
        expected = [h for h in range(n) if h != invalid[s]]
        assert list(hidx[sidx == i]) == expected, (s, hidx[sidx == i])
    assert list(np.unique(hidx)) == list(range(n))
