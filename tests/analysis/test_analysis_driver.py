"""The one driver over the analysis chain, and power_analysis's section split.

``analysis/`` had five separate ``__main__`` entry points chained by sibling
imports and no driver at all, while ``power_analysis.main()`` interleaved 8
numbered sections of computation with 43 ``print`` calls. These pin the shape
that replaced both: one data function per section, a ``render_*`` that prints
it, a short ``main()``, and ``run_all.py`` over the chain.

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
#: deliberately absent: it reads no results tree and is a Monte Carlo study,
#: so it runs only behind an explicit flag.
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

    The scripts themselves are covered by their own tests; what the driver
    owns is WHICH ones run and in WHAT ORDER, and stubbing is also what keeps
    this test off ``power_analysis.main``'s ~2-minute Monte Carlo and
    ``multiplicity_sim.main``'s much longer one.
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
    """`multiplicity_sim` is a Monte Carlo study that reads no results tree, so
    a default run must not spend minutes on it -- and a caller who wants it
    must not have to invoke a second script by hand."""
    run_all.main([])
    assert "multiplicity_sim" not in recorded
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == list(CHAIN) + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(run_all, repoint,
                                                         driver_tree, monkeypatch):
    """End to end on a synthetic tree, with only the slow script stubbed.

    The three fast scripts run FOR REAL here (about a second all told), so
    this catches a driver that imports the chain but cannot actually drive it
    -- a wrong call signature, a missing sys.path insert, or a script that
    only works as ``__main__``. ``power_analysis.main`` is stubbed because its
    10,000-sim sizing takes about two minutes; its own sections are pinned
    below.
    """
    import sys

    repoint(driver_tree)
    monkeypatch.setattr(sys.modules["power_analysis"], "main", lambda *a, **k: None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert run_all.main([]) == 0
    out = buf.getvalue()
    # One banner per script, in order, so a reader of a long log can tell
    # whose output they are looking at.
    positions = [out.find(name) for name in CHAIN]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    # ... and the real scripts' own output is in there too.
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
    """One function per numbered section returning plain data, one ``render_*``
    printing it -- so the numbers can be tested, and reused, without capturing
    stdout. ``main()`` had 8 numbered sections; each keeps its pair."""
    pairs = section_pairs(power_analysis)
    assert len(pairs) >= 8, [name for name, _ in pairs]
    for render_name, data_name in pairs:
        data = getattr(power_analysis, data_name, None)
        assert inspect.isfunction(data), (
            f"{render_name} has no {data_name} data function behind it")


def test_the_data_functions_do_not_print(power_analysis):
    """A section's data function returns; only its ``render_*`` twin prints.

    Checked on the SOURCE rather than by capturing stdout, because that is the
    property being fixed: computation and printing were interleaved, 43 print
    calls deep, so the numbers could not be consumed by anything but a human.
    """
    for _render_name, data_name in section_pairs(power_analysis):
        source = inspect.getsource(getattr(power_analysis, data_name))
        assert "print(" not in source, f"{data_name} prints"


def test_main_is_a_short_orchestrator(power_analysis):
    """``main()`` calls the pairs above and does nothing else.

    It was 227 lines interleaving computation with printing; the ceiling here
    is the spec's, and it is what stops the split from silently regrowing.
    """
    lines = inspect.getsource(power_analysis.main).splitlines()
    assert len(lines) <= 60, len(lines)


# ---------------------------------------------------------------------------
# multiplicity_sim.apply_corrections: no dead parameters, one step-up helper
# ---------------------------------------------------------------------------

def legacy_apply_corrections(pv, is_null, m, alpha):
    """The pre-split ``apply_corrections``, vendored verbatim from HEAD.

    ``is_null`` was never read and ``m`` was always ``pv.shape[1]``; the three
    sort-scatter idioms below are what one ``_stepup`` helper replaces. Kept
    here so the rewrite is pinned to produce IDENTICAL rejections, procedure
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
    """``apply_corrections(pv)``: ``is_null`` was never read and ``m`` was
    always ``pv.shape[1]``, so a caller could pass a wrong ``m`` and get
    silently mis-corrected p-values."""
    assert list(inspect.signature(multiplicity_sim.apply_corrections)
                .parameters) == ["pv"]


def test_apply_corrections_is_unchanged_procedure_for_procedure(multiplicity_sim):
    """Every procedure's rejection mask matches the vendored pre-split code.

    The p-value families below straddle each procedure's step-up boundary:
    all-null, all-significant, and a mixture with exact ties and values
    exactly at a threshold, which is where a rewritten step-up is most likely
    to be off by one rank.
    """
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
