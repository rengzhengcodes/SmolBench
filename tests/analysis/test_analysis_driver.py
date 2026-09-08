"""Pins the analysis driver's shape and power_analysis's section split: one
data function per section, a ``render_*`` that prints it, a short ``main()``,
and ``run_all.py`` running the chain in order.

See ``tests/analysis/_trees.py`` for the synthetic replicate tree and for why
this directory has no ``conftest.py``.
"""

import inspect
import io
import contextlib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

from tests.analysis._trees import (  # noqa: F401 -- imported for the fixtures
    DEEP_DEPTH,
    build_tree,
    extens_vs_noise,
    load_analysis,
    multiplicity_sim,
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
def run_all(extens_vs_noise: ModuleType) -> ModuleType:
    """The driver module (imports the whole chain, so it loads last)."""
    return load_analysis("run_all")


@pytest.fixture(scope="session")
def driver_tree(tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType) -> Path:
    """A complete, unremarkable tree: every arm 0.99, the zero arm at chance."""
    root = tmp_path_factory.mktemp("driver")
    build_tree(root, power_analysis.MODELS, power_analysis.INFOS,
               lambda model, info: ((0.10 if info == "zero" else 0.99), 0.0,
                                    "empty", range(DEEP_DEPTH)))
    return root


@pytest.fixture
def recorded(
    monkeypatch: pytest.MonkeyPatch, run_all: ModuleType, multiplicity_sim: ModuleType
) -> list[str]:
    """Replace every script's ``main`` with a recorder; return the call list.

    The scripts themselves are covered by their own tests; the driver only
    owns which ones run and in what order, so stubbing also keeps this off
    ``power_analysis.main``'s ~2-minute Monte Carlo and
    ``multiplicity_sim.main``'s longer one.
    """
    calls: list = []

    def recorder(name: str) -> Callable[..., None]:
        def _main(*args: Any, **kwargs: Any) -> None:
            calls.append(name)
        return _main

    import sys

    for name in CHAIN + ("multiplicity_sim",):
        monkeypatch.setattr(sys.modules[name], "main", recorder(name))
    return calls


def test_the_driver_runs_the_chain_in_order(run_all: ModuleType, recorded: list[str]) -> None:
    """The four result-reading scripts run once each, in dependency order."""
    assert run_all.main([]) == 0
    assert recorded == list(CHAIN)


def test_the_simulation_runs_only_behind_its_flag(run_all: ModuleType, recorded: list[str]) -> None:
    """A default run must not spend minutes on the Monte Carlo, and enabling it must not require a second script."""
    run_all.main([])
    assert "multiplicity_sim" not in recorded
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == list(CHAIN) + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(
    run_all: ModuleType,
    repoint: Callable[[Path], None],
    driver_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

def section_pairs(module: ModuleType) -> list[tuple[str, str]]:
    """Return ``[(render_name, data_name)]`` for every ``render_*`` function."""
    return [(name, name[len("render_"):])
            for name in dir(module) if name.startswith("render_")
            and inspect.isfunction(getattr(module, name))]


def test_every_printed_section_has_a_data_function_behind_it(power_analysis: ModuleType) -> None:
    """Each of the 8 numbered sections keeps a data/render pair, so figures can be tested and reused without capturing stdout."""
    pairs = section_pairs(power_analysis)
    assert len(pairs) >= 8, [name for name, _ in pairs]
    for render_name, data_name in pairs:
        data = getattr(power_analysis, data_name, None)
        assert inspect.isfunction(data), (
            f"{render_name} has no {data_name} data function behind it")


def test_the_data_functions_do_not_print(power_analysis: ModuleType) -> None:
    """A section's data function returns; only its ``render_*`` twin prints."""
    for _render_name, data_name in section_pairs(power_analysis):
        source = inspect.getsource(getattr(power_analysis, data_name))
        assert "print(" not in source, f"{data_name} prints"


def test_main_is_a_short_orchestrator(power_analysis: ModuleType) -> None:
    """``main()`` calls the pairs above and does nothing else; the 60-line ceiling stops the split from silently regrowing."""
    lines = inspect.getsource(power_analysis.main).splitlines()
    assert len(lines) <= 60, len(lines)


# ---------------------------------------------------------------------------
# multiplicity_sim.apply_corrections: no dead parameters, one step-up helper
# ---------------------------------------------------------------------------

def test_apply_corrections_keeps_only_the_parameter_it_reads(multiplicity_sim: ModuleType) -> None:
    """Drops `is_null` (never read) and `m` (always `pv.shape[1]`), so a wrong `m` can no longer silently mis-correct p-values."""
    assert list(inspect.signature(multiplicity_sim.apply_corrections)
                .parameters) == ["pv"]
