"""Section 7's bootstrap resolution and clustered-data behavior."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest

from tests.tooling._notebook_cells import (
    STATS_NB,
    cell_source,
    load_analysis_modules,
    load_notebook,
)


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


def _section_7_markdown(nb: dict[str, Any]) -> str:
    """Return Section 7 markdown."""
    sources = ["".join(cell["source"]) if cell["cell_type"] == "markdown" else ""
               for cell in nb["cells"]]
    start = next(i for i, s in enumerate(sources) if s.startswith("## Section 7"))
    end = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert start < end, (start, end)
    return "\n".join(sources[start:end])


@pytest.fixture(scope="module")
def modules() -> dict[str, Any]:
    """Load analysis modules once."""
    return load_analysis_modules()


@pytest.fixture(scope="module")
def stats(modules: dict[str, Any]) -> ModuleType:
    """Return the shared estimator module."""
    return modules["notebook_stats"]


BOOT_CASES = [
    pytest.param(0.1, 1_000, id="alpha=0.1"),
    pytest.param(0.01, 10_000, id="alpha=0.01"),
    pytest.param(0.001, 100_000, id="alpha=0.001"),
    pytest.param(2 * 0.05 / 966, 200_000, id="alpha=2*ALPHA_POSTERIOR-capped"),
]


@pytest.mark.parametrize("alpha, expected", BOOT_CASES)
def test_boot_resamples_is_derived_from_the_alpha_in_use(
    stats: ModuleType, alpha: float, expected: int
) -> None:
    """B follows alpha; 4,000 gives 0.2 alpha/2-tail draws and biases EQUIVALENT."""
    assert stats.boot_resamples(alpha) == expected


def test_boot_resamples_meets_its_own_tail_criterion(stats: ModuleType) -> None:
    """Uncapped B provides at least TARGET draws per tail."""
    target = stats.BOOT_TAIL_TARGET
    cap = stats.BOOT_RESAMPLE_CAP
    for alpha in (0.1, 0.05, 0.01, 0.001, 0.0005):
        n_boot = stats.boot_resamples(alpha)
        if n_boot < cap:
            assert n_boot * (alpha / 2) >= target, alpha


def test_boot_resamples_warns_when_it_caps(
    stats: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """Capped B warns because the cap does not resolve alpha."""
    alpha = 2 * 0.05 / 966
    stats._BOOT_CAP_WARNED.clear()
    capsys.readouterr()
    stats.boot_resamples(alpha)
    first = capsys.readouterr().out
    assert "200000" in first.replace(",", "").replace("_", ""), first
    assert "966000" in first.replace(",", "").replace("_", ""), first
    # Section 7's real-data cell calls this 966 times; one warning, not 966.
    stats.boot_resamples(alpha)
    assert capsys.readouterr().out == ""


def test_paired_diff_ci_defaults_to_the_derived_count(
    stats: ModuleType, modules: dict[str, Any]
) -> None:
    """The default uses the derivation, not a second constant."""
    import numpy as np

    error_bars = modules["error_bars"]
    seen: list[int] = []
    real = error_bars.bootstrap_stats

    def spy(succ: Any, size: Any, B: int, seed: int, alpha: float = 0.05) -> dict:
        seen.append(B)
        return real(succ, size, B, seed, alpha)

    error_bars.bootstrap_stats = spy
    try:
        rng = np.random.default_rng(0)
        n_harm = modules["ind_pa"].N_HARMONICS
        a = (rng.random((6, n_harm)) < 0.5).reshape(-1)
        b = (rng.random((6, n_harm)) < 0.5).reshape(-1)
        seed_idx = np.repeat(np.arange(6), n_harm)
        stats.paired_diff_ci(a, b, seed_idx, alpha=0.01, error_bars=error_bars)
    finally:
        error_bars.bootstrap_stats = real
    assert seen == [stats.boot_resamples(0.01)], seen


def test_synth_iid_path_takes_exactly_one_draw(
    stats: ModuleType, modules: dict[str, Any]
) -> None:
    """``cluster_sd=0`` takes one draw; extras shift the shared stream and can flip EQUIVALENT."""
    import numpy as np

    n_harm = modules["ind_pa"].N_HARMONICS

    got, seed_idx = stats.synth(0.37, 11, np.random.default_rng(4), n_harm=n_harm)
    reference = np.random.default_rng(4)
    want = (reference.random((11, n_harm)) < 0.37).reshape(-1)
    assert np.array_equal(got, want)
    assert np.array_equal(seed_idx, np.repeat(np.arange(11), n_harm))
    # and the generator is left at the same position
    assert np.random.default_rng(4).random() != reference.random()


def test_clustered_synth_reaches_the_target_design_effect(
    stats: ModuleType, modules: dict[str, Any]
) -> None:
    """The clustered arm must measure as clustered by live ``design_effect``."""
    import numpy as np

    paired = modules["paired"]
    n_harm = modules["ind_pa"].N_HARMONICS

    def median_deff(sd: float) -> float:
        gen = np.random.default_rng(3)
        deffs = []
        for _ in range(40):
            a, seed_idx = stats.synth(0.5, 40, gen, sd, n_harm=n_harm)
            b, _ = stats.synth(0.5, 40, gen, sd, n_harm=n_harm)
            value = paired.design_effect(a, b, seed_idx)
            if value is not None:
                deffs.append(value)
        return float(np.median(deffs))

    assert median_deff(0.0) == pytest.approx(1.0, abs=0.2)
    assert 2.5 <= median_deff(stats.CLUSTER_SD) <= 4.0, median_deff(stats.CLUSTER_SD)


def test_clustering_inflates_the_decided_rate_on_a_true_null(
    stats: ModuleType, modules: dict[str, Any]
) -> None:
    """A clustered true null is DECIDED more often than alpha allows."""
    n_sim = 60
    kwargs = {"n_harm": modules["ind_pa"].N_HARMONICS,
              "paired": modules["paired"], "error_bars": modules["error_bars"]}
    iid = stats.verdict_distribution(0.0, n_sim=n_sim, **kwargs)
    clustered = stats.verdict_distribution(stats.CLUSTER_SD, n_sim=n_sim, **kwargs)
    assert sum(iid["verdicts"].values()) == n_sim, iid
    assert sum(clustered["verdicts"].values()) == n_sim, clustered

    # The diagnostic must MEASURE the clustering it reports, not assert it.
    assert iid["median_deff"] == pytest.approx(1.0, abs=0.2), iid
    assert 2.5 <= clustered["median_deff"] <= 4.0, clustered

    # i.i.d. false rejections stay near alpha = 0.05; clustered blow past it.
    iid_decided = iid["verdicts"]["DECIDED"]
    assert iid_decided <= 0.10 * n_sim, iid
    assert clustered["verdicts"]["DECIDED"] >= 2 * max(iid_decided, 1), (iid, clustered)
    assert clustered["verdicts"]["EQUIVALENT"] < iid["verdicts"]["EQUIVALENT"], \
        (iid, clustered)


def test_self_test_asserts_no_equivalence_under_clustering(nb: dict[str, Any]) -> None:
    """The clustered case must be reported, never asserted."""
    import ast

    source = cell_source(nb, "self-test PASSED")
    tree = ast.parse(source)
    offenders = [
        ast.get_source_segment(source, node) for node in ast.walk(tree)
        if isinstance(node, ast.Assert)
        and "cluster" in (ast.get_source_segment(source, node) or "").lower()
    ]
    assert not offenders, offenders


def test_section_7_markdown_names_the_recurrence(nb: dict[str, Any]) -> None:
    """Section 7 names ``design_effect`` and the PR #12 parallel."""
    joined = _section_7_markdown(nb)
    for token in ("design_effect", "multiplicity_sim", "PR #12"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


def test_resample_sweep_shows_the_posterior_alpha_is_not_resolved(
    stats: ModuleType, modules: dict[str, Any]
) -> None:
    """No grid B reaches DRIFT_TOL: 500,000 gives 25.9 tail draws, not 50, so cap B."""
    import numpy as np

    error_bars = modules["error_bars"]
    n_harm = modules["ind_pa"].N_HARMONICS
    gen = np.random.default_rng(20260904)
    a, seed_idx = stats.synth(0.5, 30, gen, n_harm=n_harm)
    b, _ = stats.synth(0.5, 30, gen, n_harm=n_harm)
    n_tests = stats.posterior_family(
        tuple(modules["run_study"].MODELS), tuple(modules["run_study"].INFO_TYPES))
    alpha = 2 * modules["power_common"].ALPHA / n_tests

    rows = stats.resample_sweep(a, b, seed_idx, alpha, error_bars=error_bars)
    assert [row["B"] for row in rows] == list(error_bars.B_GRID)
    assert rows[0]["drift"] is None, rows[0]        # nothing to compare against
    drifts = [row["drift"] for row in rows[1:]]
    assert all(d is not None for d in drifts), rows
    assert max(drifts) > error_bars.DRIFT_TOL, drifts
    # the largest B on the grid still under-fills the tail it is asked about
    assert rows[-1]["B"] * alpha / 2 < stats.BOOT_TAIL_TARGET, rows[-1]


def test_section_7_markdown_explains_the_block_count_limit(nb: dict[str, Any]) -> None:
    """B adds Monte-Carlo precision; R = 30 bounds inference."""
    joined = _section_7_markdown(nb)
    for token in ("B_GRID", "DRIFT_TOL", "R = 30"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


@pytest.fixture(scope="module")
def calibration(
    nb: dict[str, Any], modules: dict[str, Any], stats: ModuleType
) -> tuple[dict, str]:
    """Execute the calibration cell once."""
    import contextlib
    import io

    namespace = dict(modules)
    n_tests = stats.posterior_family(
        tuple(modules["run_study"].MODELS), tuple(modules["run_study"].INFO_TYPES))
    namespace.update(N_TESTS=n_tests,
                     ALPHA_POSTERIOR=modules["power_common"].ALPHA / n_tests,
                     N_HARM=modules["ind_pa"].N_HARMONICS,
                     CLUSTER_SD=stats.CLUSTER_SD)
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        exec(compile(cell_source(nb, "CALIBRATED_DEFF_CEILING ="),
                     str(STATS_NB), "exec"), namespace)
    return namespace, sink.getvalue()


def test_calibration_runs_at_the_studys_own_R_and_alpha(
    calibration: tuple[dict[str, Any], str], modules: dict[str, Any]
) -> None:
    """Use the study R and alpha; another alpha answers another question."""
    namespace, _out = calibration
    assert namespace["STUDY_R"] == modules["run_study"].N_REPLICATES
    rows = namespace["CALIBRATION_ROWS"]
    assert rows, "the calibration produced no rows"
    for row in rows:
        assert row["r"] == modules["run_study"].N_REPLICATES, row
        assert row["alpha"] == namespace["ALPHA_POSTERIOR"], row
        assert row["decided"] <= row["n_sim"], row


def test_calibration_reports_both_numbers(calibration: tuple[dict[str, Any], str]) -> None:
    """Print the deff ceiling and study-shaped rate."""
    namespace, out = calibration
    ceiling = namespace["CALIBRATED_DEFF_CEILING"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert f"{ceiling:.2f}" in out, out[-1500:]
    assert f"{study_row['decided']}/{study_row['n_sim']}" in out, out[-1500:]


def test_calibration_states_its_detection_floor(calibration: tuple[dict[str, Any], str]) -> None:
    """State the detection floor; no measured inflation does not calibrate alpha."""
    _namespace, out = calibration
    lowered = out.lower()
    assert "detect" in lowered, out[-1500:]
    # the expected number of false DECIDEDs a nominal rung would produce
    assert "expected" in lowered, out[-1500:]


def test_the_ceiling_sits_below_the_studys_own_design_effect(
    calibration: tuple[dict[str, Any], str]
) -> None:
    """At study deff ~3, calibrated from ``CLUSTER_SD``, ``DECIDED`` is invalid."""
    namespace, _out = calibration
    ceiling = namespace["CALIBRATED_DEFF_CEILING"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert 0.9 <= ceiling <= 2.0, ceiling
    assert study_row["median_deff"] >= 2.5, study_row
    assert ceiling < study_row["median_deff"] - 1.0, (ceiling, study_row)


def test_the_studys_shaped_rate_is_inflated_by_orders_of_magnitude(
    calibration: tuple[dict[str, Any], str]
) -> None:
    """Measure the study-shaped rate against claimed alpha."""
    namespace, _out = calibration
    alpha = namespace["ALPHA_POSTERIOR"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert study_row["rate"] > 20 * alpha, (study_row, alpha)
    assert study_row["rate"] < 0.10, study_row       # still a tail, not a coin flip


def test_false_decided_rate_can_come_out_the_other_way(
    calibration: tuple[dict[str, Any], str], stats: ModuleType,
    modules: dict[str, Any]
) -> None:
    """Allow no inflation because a measurement must be able to return the negative answer."""
    namespace, _out = calibration
    # Use 400 draws: a 200-draw ~2% control has a few-percent empty chance,
    # which would mimic thin sampling.
    kwargs = {"n_sim": 400, "r": modules["run_study"].N_REPLICATES,
              "alpha": namespace["ALPHA_POSTERIOR"],
              "n_harm": modules["ind_pa"].N_HARMONICS, "paired": modules["paired"]}
    iid = stats.false_decided_rate(0.0, **kwargs)
    clustered = stats.false_decided_rate(stats.CLUSTER_SD, **kwargs)
    assert iid["decided"] == 0, iid
    assert iid["median_deff"] == pytest.approx(1.0, abs=0.2), iid
    assert clustered["decided"] > 0, clustered
    assert clustered["rate"] > iid["rate"], (iid, clustered)


def test_the_calibration_prints_beside_the_verdict_table(nb: dict[str, Any]) -> None:
    """Keep both in the same section with no code cell between them."""
    sources = ["".join(cell["source"]) for cell in nb["cells"]]
    table = next(i for i, s in enumerate(sources) if "verdict_distribution =" in s)
    calibration = next(i for i, s in enumerate(sources) if "false_decided_rate =" in s)
    section_8 = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert table < calibration < section_8, (table, calibration, section_8)
    between = [i for i in range(table + 1, calibration)
               if nb["cells"][i]["cell_type"] != "markdown"]
    assert not between, f"code cells {between} sit between the table and its calibration"


def test_section_7_markdown_states_the_validity_rule_without_a_literal(
    nb: dict[str, Any], calibration: tuple[dict[str, Any], str]
) -> None:
    """Markdown states the rule because reruns move hardcoded thresholds."""
    namespace, _out = calibration
    joined = _section_7_markdown(nb)
    lowered = joined.lower()
    for token in ("design effect", "calibrat", "valid"):
        assert token in lowered, f"section 7 markdown never mentions {token!r}"
    literal = f"{namespace['CALIBRATED_DEFF_CEILING']:.2f}"
    assert literal not in joined, \
        f"section 7 markdown hardcodes the calibrated ceiling {literal}"
