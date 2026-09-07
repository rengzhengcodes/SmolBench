"""Section 7's bootstrap resolution and its behaviour under clustering.

Two contracts: the number of bootstrap resamples must follow the alpha in use
(a fixed 4,000 puts 0.2 draws in the tail the posterior family's alpha asks
about, biasing the endpoint toward EQUIVALENT); and the classifier's synthetic
self-test must exercise data shaped like the study's own, where harmonics
inside a replicate are strata, not exchangeable draws, and an arm-specific
replicate effect changes the verdicts materially.
"""

from __future__ import annotations

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


def _section_7_markdown(nb) -> str:
    """The markdown span from the section-7 heading up to section 8's.

    A span, not one cell: a note may live beside the cell it explains.
    """
    sources = ["".join(cell["source"]) if cell["cell_type"] == "markdown" else ""
               for cell in nb["cells"]]
    start = next(i for i, s in enumerate(sources) if s.startswith("## Section 7"))
    end = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert start < end, (start, end)
    return "\n".join(sources[start:end])


@pytest.fixture(scope="module")
def posterior_ns(nb) -> dict:
    """The executed namespace of section 7's classifier cell."""
    namespace = load_analysis_modules()
    exec(compile(cell_source(nb, "def paired_diff_ci"), str(STATS_NB), "exec"), namespace)
    return namespace


#: ``(two-sided alpha, resamples)``. ``bootstrap_stats`` cuts each tail at
#: ``alpha/2``, so B = ``ceil(BOOT_TAIL_TARGET / (alpha/2))``, capped. Values
#: computed from the rule, not read off the cell.
BOOT_CASES = [
    pytest.param(0.1, 1_000, id="alpha=0.1"),
    pytest.param(0.01, 10_000, id="alpha=0.01"),
    pytest.param(0.001, 100_000, id="alpha=0.001"),
    # The posterior family's own alpha: 0.05/966 per tail wants 966,000, which
    # is over the cap -- so the real-data call is capped, loudly.
    pytest.param(2 * 0.05 / 966, 200_000, id="alpha=2*ALPHA_POSTERIOR-capped"),
]


@pytest.mark.parametrize("alpha, expected", BOOT_CASES)
def test_boot_resamples_is_derived_from_the_alpha_in_use(posterior_ns, alpha, expected):
    """B must follow alpha: 4,000 resamples put only 0.2 draws in the tail read at alpha/2, biasing the endpoint toward EQUIVALENT."""
    assert posterior_ns["boot_resamples"](alpha) == expected


def test_boot_resamples_meets_its_own_tail_criterion(posterior_ns):
    """Uncapped, the derived B puts at least TARGET resamples in each tail."""
    target = posterior_ns["BOOT_TAIL_TARGET"]
    cap = posterior_ns["BOOT_RESAMPLE_CAP"]
    for alpha in (0.1, 0.05, 0.01, 0.001, 0.0005):
        n_boot = posterior_ns["boot_resamples"](alpha)
        if n_boot < cap:
            assert n_boot * (alpha / 2) >= target, alpha


def test_boot_resamples_warns_when_it_caps(posterior_ns, capsys):
    """A capped B must warn: silently returning the cap would let a reader believe the endpoint resolves alpha when it does not."""
    alpha = 2 * 0.05 / 966
    # An earlier test in this module already asked for this exact alpha, and the
    # warn-once ledger is module state; clear it or this test reads an empty
    # buffer and calls a correct implementation silent.
    posterior_ns["_BOOT_CAP_WARNED"].clear()
    capsys.readouterr()
    posterior_ns["boot_resamples"](alpha)
    first = capsys.readouterr().out
    assert "200000" in first.replace(",", "").replace("_", ""), first
    assert "966000" in first.replace(",", "").replace("_", ""), first
    # Section 7's real-data cell calls this 966 times; one warning, not 966.
    posterior_ns["boot_resamples"](alpha)
    assert capsys.readouterr().out == ""


def test_paired_diff_ci_defaults_to_the_derived_count(posterior_ns):
    """The default must be the derivation, not a second hardcoded number."""
    import numpy as np

    error_bars = posterior_ns["error_bars"]
    seen: list[int] = []
    real = error_bars.bootstrap_stats

    def spy(succ, size, B, seed, alpha=0.05):
        seen.append(B)
        return real(succ, size, B, seed, alpha)

    error_bars.bootstrap_stats = spy
    try:
        rng = np.random.default_rng(0)
        n_harm = posterior_ns["ind_pa"].N_HARMONICS
        a = (rng.random((6, n_harm)) < 0.5).reshape(-1)
        b = (rng.random((6, n_harm)) < 0.5).reshape(-1)
        seed_idx = np.repeat(np.arange(6), n_harm)
        posterior_ns["paired_diff_ci"](a, b, seed_idx, alpha=0.01)
    finally:
        error_bars.bootstrap_stats = real
    assert seen == [posterior_ns["boot_resamples"](0.01)], seen


def test_no_hardcoded_resample_count_survives(nb):
    """No cell may still pin B to 4000 by hand."""
    for cell in nb["cells"]:
        source = "".join(cell["source"])
        if "paired_diff_ci" in source:
            assert "n_boot=4000" not in source, source[:200]


def test_synth_iid_path_draws_exactly_what_it_used_to(nb, posterior_ns):
    """`cluster_sd=0` must consume the same RNG stream as before: an extra draw would shift every later case and could flip an EQUIVALENT assertion."""
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    synth = namespace["synth"]
    n_harm = posterior_ns["ind_pa"].N_HARMONICS

    got, seed_idx = synth(0.37, 11, np.random.default_rng(4))
    reference = np.random.default_rng(4)
    want = (reference.random((11, n_harm)) < 0.37).reshape(-1)
    assert np.array_equal(got, want)
    assert np.array_equal(seed_idx, np.repeat(np.arange(11), n_harm))
    # and the generator is left at the same position
    assert np.random.default_rng(4).random() != reference.random()


def test_clustered_synth_reaches_the_target_design_effect(nb, posterior_ns):
    """The clustered arm must measure as clustered by the live `design_effect` metric, not just be an i.i.d. case with a different name."""
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    synth, paired = namespace["synth"], posterior_ns["paired"]
    cluster_sd = namespace["CLUSTER_SD"]

    def median_deff(sd):
        gen = np.random.default_rng(3)
        deffs = []
        for _ in range(40):
            a, seed_idx = synth(0.5, 40, gen, cluster_sd=sd)
            b, _ = synth(0.5, 40, gen, cluster_sd=sd)
            value = paired.design_effect(a, b, seed_idx)
            if value is not None:
                deffs.append(value)
        return float(np.median(deffs))

    assert median_deff(0.0) == pytest.approx(1.0, abs=0.2)
    assert 2.5 <= median_deff(cluster_sd) <= 4.0, median_deff(cluster_sd)


def test_clustering_inflates_the_decided_rate_on_a_true_null(nb, posterior_ns):
    """The diagnostic must be able to come out the other way: with an arm-specific replicate effect, a true null is DECIDED far more often than alpha allows."""
    namespace = dict(posterior_ns)
    exec(compile(cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    exec(compile(cell_source(nb, "def verdict_distribution"), str(STATS_NB), "exec"),
         namespace)
    verdict_distribution = namespace["verdict_distribution"]

    n_sim = 60
    iid = verdict_distribution(cluster_sd=0.0, n_sim=n_sim)
    clustered = verdict_distribution(cluster_sd=namespace["CLUSTER_SD"], n_sim=n_sim)
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


def test_self_test_asserts_no_equivalence_under_clustering(nb):
    """The clustered case must be reported, never asserted: asserting EQUIVALENT on clustered data failed 38 times in 60 at deff 3.19."""
    import ast

    source = cell_source(nb, "self-test PASSED")
    tree = ast.parse(source)
    offenders = [
        ast.get_source_segment(source, node) for node in ast.walk(tree)
        if isinstance(node, ast.Assert)
        and "cluster" in (ast.get_source_segment(source, node) or "").lower()
    ]
    assert not offenders, offenders


def test_section_7_markdown_names_the_recurrence(nb):
    """Section 7 must name `design_effect` and the PR #12 parallel, so a reader can check the clustered case against the study's own numbers."""
    joined = _section_7_markdown(nb)
    for token in ("design_effect", "multiplicity_sim", "PR #12"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


def test_resample_sweep_reuses_error_bars_grid_and_tolerance(nb):
    """The sweep must reuse `error_bars.B_GRID`/`DRIFT_TOL`, not fork them into local literals that could drift."""
    source = cell_source(nb, "def resample_sweep")
    assert "error_bars.B_GRID" in source
    assert "error_bars.DRIFT_TOL" in source


def test_resample_sweep_shows_the_posterior_alpha_is_not_resolved(nb, posterior_ns):
    """At the posterior alpha, no B on the grid reaches DRIFT_TOL: 500,000 resamples put only 25.9 draws in a tail that wants 50, which is why the derived count is capped rather than obeyed."""
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    exec(compile(cell_source(nb, "def resample_sweep"), str(STATS_NB), "exec"), namespace)

    error_bars = posterior_ns["error_bars"]
    gen = np.random.default_rng(20260904)
    a, seed_idx = namespace["synth"](0.5, 30, gen)
    b, _ = namespace["synth"](0.5, 30, gen)
    alpha = 2 * posterior_ns["ALPHA_POSTERIOR"]

    rows = namespace["resample_sweep"](a, b, seed_idx, alpha=alpha)
    assert [row["B"] for row in rows] == list(error_bars.B_GRID)
    assert rows[0]["drift"] is None, rows[0]        # nothing to compare against
    drifts = [row["drift"] for row in rows[1:]]
    assert all(d is not None for d in drifts), rows
    assert max(drifts) > error_bars.DRIFT_TOL, drifts
    # the largest B on the grid still under-fills the tail it is asked about
    assert rows[-1]["B"] * alpha / 2 < posterior_ns["BOOT_TAIL_TARGET"], rows[-1]


def test_section_7_markdown_explains_the_block_count_limit(nb):
    """B buys Monte-Carlo precision only; R = 30 blocks bound what any B can say."""
    joined = _section_7_markdown(nb)
    for token in ("B_GRID", "DRIFT_TOL", "R = 30"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


# --- the false-DECIDED calibration at the study's own R and alpha ----------
#
# The verdict-distribution cell above measures the mechanism at R=40,
# alpha=0.05; the study's own operating point is R = `run_study.N_REPLICATES`
# and `ALPHA_POSTERIOR`. This calibration answers "how clustered may my data
# be before DECIDED stops meaning what it says?" at that real point, and the
# tests below pin that it measures rather than asserts.


@pytest.fixture(scope="module")
def calibration(nb, posterior_ns) -> tuple[dict, str]:
    """Execute the calibration cell once; return its namespace and its output.

    Module-scoped, using ``redirect_stdout`` (``capsys`` is function-scoped):
    the cell simulates a full ladder, so paying for it once per module keeps
    the suite honest about cost.
    """
    import contextlib
    import io

    namespace = dict(posterior_ns)
    for needle in ("def synth(", "def verdict_distribution", "def false_decided_rate"):
        with contextlib.redirect_stdout(io.StringIO()) as sink:
            exec(compile(cell_source(nb, needle), str(STATS_NB), "exec"), namespace)
        captured = sink.getvalue()
    return namespace, captured


def test_calibration_runs_at_the_studys_own_R_and_alpha(calibration, posterior_ns):
    """The calibration's R and alpha must be the study's own, read from live sources: a different alpha is a different question with the same name."""
    namespace, _out = calibration
    assert namespace["STUDY_R"] == posterior_ns["run_study"].N_REPLICATES
    rows = namespace["CALIBRATION_ROWS"]
    assert rows, "the calibration produced no rows"
    for row in rows:
        assert row["r"] == posterior_ns["run_study"].N_REPLICATES, row
        assert row["alpha"] == posterior_ns["ALPHA_POSTERIOR"], row
        assert row["decided"] <= row["n_sim"], row


def test_calibration_reports_both_numbers(calibration):
    """Both headline numbers (the deff ceiling and the study-shaped rate) must reach the reader's screen, not just the namespace."""
    namespace, out = calibration
    ceiling = namespace["CALIBRATED_DEFF_CEILING"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert f"{ceiling:.2f}" in out, out[-1500:]
    assert f"{study_row['decided']}/{study_row['n_sim']}" in out, out[-1500:]


def test_calibration_states_its_detection_floor(calibration):
    """"No measured inflation" is not "calibrated to alpha": the cell must state the detection floor, or the ceiling reads stronger than the evidence behind it."""
    _namespace, out = calibration
    lowered = out.lower()
    assert "detect" in lowered, out[-1500:]
    # the expected number of false DECIDEDs a nominal rung would produce
    assert "expected" in lowered, out[-1500:]


def test_the_ceiling_sits_below_the_studys_own_design_effect(calibration):
    """The substantive claim: at the study's own deff (~3, from `CLUSTER_SD`'s calibration), the classifier's DECIDED is not valid."""
    namespace, _out = calibration
    ceiling = namespace["CALIBRATED_DEFF_CEILING"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert 0.9 <= ceiling <= 2.0, ceiling
    assert study_row["median_deff"] >= 2.5, study_row
    assert ceiling < study_row["median_deff"] - 1.0, (ceiling, study_row)


def test_the_studys_shaped_rate_is_inflated_by_orders_of_magnitude(calibration,
                                                                   posterior_ns):
    """The measured rate at the study-shaped deff, against the alpha it claims."""
    namespace, _out = calibration
    alpha = posterior_ns["ALPHA_POSTERIOR"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert study_row["rate"] > 20 * alpha, (study_row, alpha)
    assert study_row["rate"] < 0.10, study_row       # still a tail, not a coin flip


def test_false_decided_rate_can_come_out_the_other_way(calibration, posterior_ns):
    """The estimator must be able to report no inflation (and does, on i.i.d. draws): a measurement that cannot return the negative answer is not one."""
    namespace, _out = calibration
    # 400 draws, not 200: at the study-shaped rate (~2%) a 200-draw control has
    # a few percent chance of coming back empty, which would misread as "the
    # estimator cannot see clustering" rather than as thin sampling.
    iid = namespace["false_decided_rate"](0.0, n_sim=400)
    clustered = namespace["false_decided_rate"](namespace["CLUSTER_SD"], n_sim=400)
    assert iid["decided"] == 0, iid
    assert iid["median_deff"] == pytest.approx(1.0, abs=0.2), iid
    assert clustered["decided"] > 0, clustered
    assert clustered["rate"] > iid["rate"], (iid, clustered)


def test_the_calibration_prints_beside_the_verdict_table(nb):
    """The verdict table and its calibration must read as one exhibit: same section, no code cell between them."""
    sources = ["".join(cell["source"]) for cell in nb["cells"]]
    table = next(i for i, s in enumerate(sources) if "def verdict_distribution" in s)
    calibration = next(i for i, s in enumerate(sources) if "def false_decided_rate" in s)
    section_8 = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert table < calibration < section_8, (table, calibration, section_8)
    between = [i for i in range(table + 1, calibration)
               if nb["cells"][i]["cell_type"] != "markdown"]
    assert not between, f"code cells {between} sit between the table and its calibration"


def test_section_7_markdown_states_the_validity_rule_without_a_literal(nb, calibration):
    """The markdown states the rule, not the number: a hardcoded threshold would keep reading as authoritative after a re-run moved it."""
    namespace, _out = calibration
    joined = _section_7_markdown(nb)
    lowered = joined.lower()
    for token in ("design effect", "calibrat", "valid"):
        assert token in lowered, f"section 7 markdown never mentions {token!r}"
    literal = f"{namespace['CALIBRATED_DEFF_CEILING']:.2f}"
    assert literal not in joined, \
        f"section 7 markdown hardcodes the calibrated ceiling {literal}"
