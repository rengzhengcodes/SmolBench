"""Section 7's bootstrap resolution and its behaviour under clustering.

Two contracts live here. First, the number of bootstrap resamples must follow
the alpha in use: a fixed 4,000 puts 0.2 draws in the tail the posterior
family's alpha asks about, and an endpoint that IS the extreme order statistic
is biased inward -- toward EQUIVALENT, the verdict that closes a contrast.
Second, the classifier's synthetic self-test must exercise data shaped like the
study's own: harmonics inside a replicate are strata, not exchangeable draws,
and an arm-specific replicate effect changes the verdicts materially.

See ``tests/tooling/_notebook_cells.py`` for the cell-extraction machinery.
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


_cell_source = cell_source


@pytest.fixture(scope="module")
def posterior_ns(nb) -> dict:
    """The executed namespace of section 7's classifier cell."""
    namespace = load_analysis_modules()
    exec(compile(_cell_source(nb, "def paired_diff_ci"), str(STATS_NB), "exec"), namespace)
    return namespace


#: ``(two-sided alpha, resamples)``. ``bootstrap_stats`` takes a TWO-SIDED
#: level and cuts each tail at ``alpha/2``, so the criterion "at least
#: `BOOT_TAIL_TARGET` resamples land in the tail being read" is
#: ``ceil(TARGET / (alpha/2))``, capped. Values computed from the rule, not
#: read off the cell.
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
    """4,000 resamples put 0.2 draws in the tail this notebook reads at alpha/2.

    An endpoint that IS the extreme order statistic is biased inward, which
    biases the classifier toward EQUIVALENT -- the verdict that closes a
    contrast. B has to follow alpha.
    """
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
    """A capped B does not meet the criterion; saying so is the whole point.

    Silently returning the cap would restore the defect in a new place: the
    reader would believe the endpoint resolves alpha when it does not.
    """
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
    """``cluster_sd=0`` must consume the SAME RNG stream as before the change.

    The self-test threads one generator through its cases in order; an extra
    draw taken on the i.i.d. path would shift every case after it and could
    silently flip the EQUIVALENT assertion this fix is required to KEEP.
    """
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(_cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
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
    """The clustered arm must actually be clustered, measured by the live metric.

    ``paired_analysis.design_effect`` is the same statistic section 2 reports
    on the real data. A clustered case whose deff is ~1 would be an i.i.d. case
    with a different name, and the diagnostic below would prove nothing.
    """
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(_cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
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
    """The diagnostic must be able to come out the other way, and does not.

    This is the PR #12 ``multiplicity_sim`` finding recurring: with an
    arm-specific replicate effect the unpaired CMH denominator is too small, so
    a TRUE NULL is 'DECIDED' far more often than alpha allows. A diagnostic
    whose two columns agreed would be evidence of nothing.
    """
    namespace = dict(posterior_ns)
    exec(compile(_cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    exec(compile(_cell_source(nb, "def verdict_distribution"), str(STATS_NB), "exec"),
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
    """The clustered case is reported, never asserted.

    Asserting EQUIVALENT on clustered data is exactly the defect: the reviewer
    measured that assertion failing 38 times in 60 at deff 3.19.
    """
    import ast

    source = _cell_source(nb, "self-test PASSED")
    tree = ast.parse(source)
    offenders = [
        ast.get_source_segment(source, node) for node in ast.walk(tree)
        if isinstance(node, ast.Assert)
        and "cluster" in (ast.get_source_segment(source, node) or "").lower()
    ]
    assert not offenders, offenders


def test_section_7_markdown_names_the_recurrence(nb):
    """The reviewer drew the parallel to PR #12; the section has to acknowledge it.

    It must also name ``design_effect`` -- the live metric section 2 already
    reports on the real data, and the one this diagnostic is calibrated against
    -- so a reader can check the clustered case against the study's own numbers
    instead of taking the notebook's word for it.
    """
    sources = ["".join(cell["source"]) if cell["cell_type"] == "markdown" else ""
               for cell in nb["cells"]]
    start = next(i for i, s in enumerate(sources) if s.startswith("## Section 7"))
    end = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    joined = "\n".join(sources[start:end])
    for token in ("design_effect", "multiplicity_sim", "PR #12"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


def test_resample_sweep_reuses_error_bars_grid_and_tolerance(nb):
    """The sweep must not fork ``B_GRID``/``DRIFT_TOL`` into local literals.

    ``error_bars.py`` chooses B against exactly this criterion and sweeps that
    grid; a private copy here would drift from the module whose convention it
    claims to mirror.
    """
    source = _cell_source(nb, "def resample_sweep")
    assert "error_bars.B_GRID" in source
    assert "error_bars.DRIFT_TOL" in source


def test_resample_sweep_shows_the_posterior_alpha_is_not_resolved(nb, posterior_ns):
    """At the posterior alpha, no B on the grid reaches the drift tolerance.

    This is the honest outcome, and the reason the derived count is capped
    rather than obeyed: 500,000 resamples put 25.9 draws in a tail that wants
    50, and the endpoints still move by an order of magnitude more than
    ``DRIFT_TOL``. A sweep that came out under tolerance would mean the cap was
    harmless -- it is not, and the cell has to say so.
    """
    import numpy as np

    namespace = dict(posterior_ns)
    exec(compile(_cell_source(nb, "def synth("), str(STATS_NB), "exec"), namespace)
    exec(compile(_cell_source(nb, "def resample_sweep"), str(STATS_NB), "exec"), namespace)

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
    # Every markdown cell from the section-7 heading up to section 8's, so the
    # note may live beside the sweep instead of in the section preamble.
    sources = ["".join(cell["source"]) if cell["cell_type"] == "markdown" else ""
               for cell in nb["cells"]]
    start = next(i for i, s in enumerate(sources) if s.startswith("## Section 7"))
    end = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert start < end, (start, end)
    joined = "\n".join(sources[start:end])
    for token in ("B_GRID", "DRIFT_TOL", "R = 30"):
        assert token in joined, f"section 7 markdown never mentions {token!r}"


# --- the false-DECIDED calibration at the study's own R and alpha ----------
#
# The verdict-distribution cell above measures the mechanism at R=40,
# alpha=0.05, where 60 simulations are enough to see it. That is not the
# operating point: the study collected R = `run_study.N_REPLICATES` and reads
# the all-pairs family's `ALPHA_POSTERIOR`. The calibration cell answers the
# question the classifier's user actually has -- "how clustered may my data be
# before a DECIDED verdict stops meaning what it says?" -- and the tests below
# pin that it measures rather than asserts, and that it cannot quietly stop
# measuring.


@pytest.fixture(scope="module")
def calibration(nb, posterior_ns) -> tuple[dict, str]:
    """Execute the calibration cell once; return its namespace and its output.

    Module-scoped and captured with ``redirect_stdout`` rather than ``capsys``
    (which is function-scoped) because the cell simulates a full ladder: paying
    for it once per module keeps the suite honest about cost.
    """
    import contextlib
    import io

    namespace = dict(posterior_ns)
    for needle in ("def synth(", "def verdict_distribution", "def false_decided_rate"):
        with contextlib.redirect_stdout(io.StringIO()) as sink:
            exec(compile(_cell_source(nb, needle), str(STATS_NB), "exec"), namespace)
        captured = sink.getvalue()
    return namespace, captured


def test_calibration_runs_at_the_studys_own_R_and_alpha(calibration, posterior_ns):
    """The calibration's parameters must BE the study's, read from the live sources.

    A calibration at some other R or alpha would be a different question with
    the same name: the false-DECIDED rate is a tail probability, so it moves by
    orders of magnitude with alpha, and the tail is exactly where clustering
    bites hardest.
    """
    namespace, _out = calibration
    assert namespace["STUDY_R"] == posterior_ns["run_study"].N_REPLICATES
    rows = namespace["CALIBRATION_ROWS"]
    assert rows, "the calibration produced no rows"
    for row in rows:
        assert row["r"] == posterior_ns["run_study"].N_REPLICATES, row
        assert row["alpha"] == posterior_ns["ALPHA_POSTERIOR"], row
        assert row["decided"] <= row["n_sim"], row


def test_calibration_reports_both_numbers(calibration):
    """Both headline numbers must reach the reader's screen, not just the namespace.

    The two are the whole deliverable: the design-effect ceiling below which no
    inflation was measured, and what the rate actually is on data shaped like
    the study's. A cell that computed them and printed a summary without them
    would leave the verdict table beside it uninterpreted.
    """
    namespace, out = calibration
    ceiling = namespace["CALIBRATED_DEFF_CEILING"]
    study_row = namespace["CALIBRATION_ROWS"][-1]
    assert f"{ceiling:.2f}" in out, out[-1500:]
    assert f"{study_row['decided']}/{study_row['n_sim']}" in out, out[-1500:]


def test_calibration_states_its_detection_floor(calibration):
    """"No measured inflation" is not "calibrated to alpha", and must say so.

    At this alpha a nominal run puts well under one false DECIDED in `n_sim`
    draws, so an admissible rung's zero count bounds its rate only at roughly
    ``3/n_sim`` -- orders of magnitude above alpha. Without that floor on the
    screen the ceiling reads far stronger than the evidence behind it.
    """
    _namespace, out = calibration
    lowered = out.lower()
    assert "detect" in lowered, out[-1500:]
    # the expected number of false DECIDEDs a nominal rung would produce
    assert "expected" in lowered, out[-1500:]


def test_the_ceiling_sits_below_the_studys_own_design_effect(calibration):
    """The substantive claim: at deff ~3 the classifier's DECIDED is not valid.

    Section 2 reports `design_effect` on the real induction data in this range,
    and `CLUSTER_SD` is calibrated to it. If the ceiling were at or above that,
    the note this cell justifies would be pointless -- so this is the assertion
    that makes the whole calibration worth printing.
    """
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
    """The estimator must be able to report NO inflation, and does on i.i.d. draws.

    A measurement that cannot return the negative answer is not a measurement.
    Run at a small `n_sim` on purpose: this is the control, not the ladder.
    """
    namespace, _out = calibration
    # 400 draws, not 200: at the study-shaped rate (about 2%) a 200-draw
    # control has a few percent chance of coming back empty, which would read
    # as "the estimator cannot see clustering" rather than as thin sampling.
    iid = namespace["false_decided_rate"](0.0, n_sim=400)
    clustered = namespace["false_decided_rate"](namespace["CLUSTER_SD"], n_sim=400)
    assert iid["decided"] == 0, iid
    assert iid["median_deff"] == pytest.approx(1.0, abs=0.2), iid
    assert clustered["decided"] > 0, clustered
    assert clustered["rate"] > iid["rate"], (iid, clustered)


def test_the_calibration_prints_beside_the_verdict_table(nb):
    """The two must read as one exhibit: same section, nothing but prose between.

    The calibration answers a question the verdict table raises (it is measured
    at the study's own R and alpha, where the table's 60 draws could see
    nothing), so a reader who stops at the table must not have to go looking.
    """
    sources = ["".join(cell["source"]) for cell in nb["cells"]]
    table = next(i for i, s in enumerate(sources) if "def verdict_distribution" in s)
    calibration = next(i for i, s in enumerate(sources) if "def false_decided_rate" in s)
    section_8 = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    assert table < calibration < section_8, (table, calibration, section_8)
    between = [i for i in range(table + 1, calibration)
               if nb["cells"][i]["cell_type"] != "markdown"]
    assert not between, f"code cells {between} sit between the table and its calibration"


def test_section_7_markdown_states_the_validity_rule_without_a_literal(nb, calibration):
    """The note states the RULE; the number lives only in the cell's output.

    Cell 27 already establishes the house convention ("the conclusion as
    computed figures, so it cannot drift from the table above"). A threshold
    typed into markdown is exactly the drift that convention exists to
    prevent -- it would keep reading as authoritative after a re-run moved it.
    """
    namespace, _out = calibration
    sources = ["".join(cell["source"]) if cell["cell_type"] == "markdown" else ""
               for cell in nb["cells"]]
    start = next(i for i, s in enumerate(sources) if s.startswith("## Section 7"))
    end = next(i for i, s in enumerate(sources) if s.startswith("## Section 8"))
    joined = "\n".join(sources[start:end])
    lowered = joined.lower()
    for token in ("design effect", "calibrat", "valid"):
        assert token in lowered, f"section 7 markdown never mentions {token!r}"
    literal = f"{namespace['CALIBRATED_DEFF_CEILING']:.2f}"
    assert literal not in joined, \
        f"section 7 markdown hardcodes the calibrated ceiling {literal}"
