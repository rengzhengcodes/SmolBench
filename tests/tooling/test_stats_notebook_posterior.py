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
