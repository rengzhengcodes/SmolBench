"""Pins the analysis driver's shape and power_analysis's section split: one
data function per section, a ``render_*`` that prints it, a short ``main()``,
and ``run_all.py`` running the chain in order.

See ``tests/analysis/_trees.py`` for the synthetic replicate tree and for why
this directory has no ``conftest.py``.
"""

import inspect
import io
import contextlib

import pytest

from tests.analysis._trees import (  # noqa: F401 -- imported for the fixtures
    DEEP_DEPTH,
    build_tree,
    extens_vs_noise,
    load_analysis,
    paired_analysis,
    power_analysis,
    repoint,
    significance_report,
)

#: The chain, in the order the driver must run it. `multiplicity_sim` is
#: absent: it consumes design constants rather than results and costs
#: minutes, so it runs only behind an explicit flag.
CHAIN = ("power_analysis", "paired_analysis", "significance_report",
         "extens_vs_noise")


@pytest.fixture(scope="session")
def run_all(extens_vs_noise):
    """The driver module (imports the whole chain, so it loads last)."""
    return load_analysis("run_all")


@pytest.fixture(scope="session")
def multiplicity_sim(power_analysis):
    return load_analysis("multiplicity_sim")


@pytest.fixture(scope="session")
def driver_tree(tmp_path_factory, power_analysis):
    """A complete, unremarkable tree: every arm 0.99, the zero arm at chance."""
    root = tmp_path_factory.mktemp("driver")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS,
               lambda model, info: ((0.10 if info == "zero" else 0.99), 0.0,
                                    "empty", range(DEEP_DEPTH)))
    return root


@pytest.fixture
def recorded(monkeypatch, run_all, multiplicity_sim):
    """Replace every script's ``main`` with a recorder; return the call list.

    The scripts themselves are covered by their own tests; the driver only
    owns which ones run and in what order, so stubbing also keeps this off
    ``power_analysis.main``'s ~2-minute Monte Carlo and
    ``multiplicity_sim.main``'s longer one.
    """
    calls: list = []

    def recorder(name):
        def _main(*args, **kwargs):
            calls.append(name)
        return _main

    import sys

    for name in CHAIN + ("multiplicity_sim",):
        monkeypatch.setattr(sys.modules[name], "main", recorder(name))
    return calls


def test_the_driver_runs_the_chain_in_order(run_all, recorded):
    """The four result-reading scripts run once each, in dependency order."""
    assert run_all.main([]) == 0
    assert recorded == list(CHAIN)


def test_the_simulation_runs_only_behind_its_flag(run_all, recorded):
    """A default run must not spend minutes on the Monte Carlo, and enabling it must not require a second script."""
    run_all.main([])
    assert "multiplicity_sim" not in recorded
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == list(CHAIN) + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(run_all, repoint,
                                                         driver_tree, monkeypatch):
    """End to end on a synthetic tree, with only the slow ``power_analysis.main`` stubbed (its Monte Carlo sizing takes minutes)."""
    import sys

    repoint(driver_tree)
    monkeypatch.setattr(sys.modules["power_analysis"], "main", lambda *a, **k: None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert run_all.main([]) == 0
    out = buf.getvalue()
    # One banner per script, in order, so a long log stays attributable.
    positions = [out.find(name) for name in CHAIN]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    assert "compliance" in out.lower()


# ---------------------------------------------------------------------------
# power_analysis: computation split from printing
# ---------------------------------------------------------------------------

def section_pairs(module):
    """Return ``[(render_name, data_name)]`` for every ``render_*`` function."""
    return [(name, name[len("render_"):])
            for name in dir(module) if name.startswith("render_")
            and inspect.isfunction(getattr(module, name))]


def test_every_printed_section_has_a_data_function_behind_it(power_analysis):
    """Each of the 8 numbered sections keeps a data/render pair, so figures can be tested and reused without capturing stdout."""
    pairs = section_pairs(power_analysis)
    assert len(pairs) >= 8, [name for name, _ in pairs]
    for render_name, data_name in pairs:
        data = getattr(power_analysis, data_name, None)
        assert inspect.isfunction(data), (
            f"{render_name} has no {data_name} data function behind it")


def test_the_data_functions_do_not_print(power_analysis):
    """A section's data function returns; only its ``render_*`` twin prints."""
    for _render_name, data_name in section_pairs(power_analysis):
        source = inspect.getsource(getattr(power_analysis, data_name))
        assert "print(" not in source, f"{data_name} prints"


def test_main_is_a_short_orchestrator(power_analysis):
    """``main()`` calls the pairs above and does nothing else; the 60-line ceiling stops the split from silently regrowing."""
    lines = inspect.getsource(power_analysis.main).splitlines()
    assert len(lines) <= 60, len(lines)


# ---------------------------------------------------------------------------
# multiplicity_sim.apply_corrections: no dead parameters, one step-up helper
# ---------------------------------------------------------------------------

def legacy_apply_corrections(pv, is_null, m, alpha):
    """The pre-split ``apply_corrections``, vendored verbatim from HEAD.

    Kept so the rewrite is pinned against identical rejections, procedure
    for procedure, rather than merely something plausible.
    """
    import numpy as np

    out = {}
    order = np.argsort(pv, axis=1)
    sortedp = np.take_along_axis(pv, order, axis=1)
    ranks = np.arange(1, m + 1)
    out["Bonferroni"] = pv < alpha / m
    thr = alpha / (m - ranks + 1)
    viol = sortedp > thr
    first = np.where(viol.any(axis=1), viol.argmax(axis=1), m)
    keep = np.arange(m)[None, :] < first[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Holm"] = rej
    ok = sortedp <= thr
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Hochberg"] = rej
    bh_thr = alpha * ranks / m
    ok = sortedp <= bh_thr
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["BH(q=0.05)"] = rej
    return out


def test_apply_corrections_keeps_only_the_parameter_it_reads(multiplicity_sim):
    """Drops `is_null` (never read) and `m` (always `pv.shape[1]`), so a wrong `m` can no longer silently mis-correct p-values."""
    assert list(inspect.signature(multiplicity_sim.apply_corrections)
                .parameters) == ["pv"]


def test_apply_corrections_is_unchanged_procedure_for_procedure(multiplicity_sim):
    """Matches the vendored pre-split code across all-null, all-significant, and boundary-tie families, where an off-by-one rank is most likely."""
    import numpy as np

    alpha = multiplicity_sim.ALPHA
    rng = np.random.default_rng(0)
    m = 12
    families = [
        rng.uniform(size=(50, m)),                       # generic
        np.full((3, m), 0.99),                           # nothing rejectable
        np.full((3, m), 1e-9),                           # everything rejectable
        np.tile(alpha * np.arange(1, m + 1) / m, (2, 1)),  # exactly at BH's line
        np.tile(alpha / (m - np.arange(m)), (2, 1)),       # exactly at Holm's
    ]
    for pv in families:
        got = multiplicity_sim.apply_corrections(pv)
        want = legacy_apply_corrections(pv, np.ones(m, bool), m, alpha)
        assert set(got) == set(want)
        for name in want:
            assert np.array_equal(got[name], want[name]), name
