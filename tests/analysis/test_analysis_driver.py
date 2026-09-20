"""Pin analysis-driver order and its computation/render split."""

import contextlib
import io
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# pylint: disable=unused-import  # fixture names register pytest fixtures
from tests.analysis._trees import (  # noqa: F401 -- imported for the fixtures
    DEEP_DEPTH,
    build_tree,
    extens_vs_noise,
    multiplicity_sim,
    power_analysis,
    run_all,
)

CHAIN = ("power_analysis", "paired_analysis", "significance_report", "extens_vs_noise")


@pytest.fixture(scope="session")
def driver_tree(
    tmp_path_factory: pytest.TempPathFactory, power_analysis: ModuleType
) -> Path:
    """Build a complete synthetic tree."""
    root = tmp_path_factory.mktemp("driver")
    build_tree(
        root,
        power_analysis.MODELS,
        power_analysis.INFOS,
        lambda model, info: (
            (0.10 if info == "zero" else 0.99),
            0.0,
            "empty",
            range(DEEP_DEPTH),
        ),
    )
    return root


@pytest.fixture
def recorded(
    monkeypatch: pytest.MonkeyPatch, run_all: ModuleType, multiplicity_sim: ModuleType
) -> list[str]:
    """Record script calls without running costly simulations."""
    calls: list = []

    def recorder(name: str) -> Callable[..., None]:
        def _main(*args: Any, **kwargs: Any) -> None:
            calls.append(name)

        return _main

    for name in CHAIN + ("multiplicity_sim",):
        monkeypatch.setattr(sys.modules[name], "main", recorder(name))
    return calls


def test_the_driver_does_not_import_the_simulation_eagerly(
    run_all: ModuleType,
) -> None:
    """`multiplicity_sim` is loaded inside the `--with-sim` branch, never at module import."""
    assert not hasattr(run_all, "multiplicity_sim")
    assert run_all.SIM_MODULE == "multiplicity_sim"
    assert all(m.__name__ != "multiplicity_sim" for m in run_all.CHAIN)


def test_the_simulation_runs_only_behind_its_flag(
    run_all: ModuleType, recorded: list[str]
) -> None:
    """Run multiplicity simulation only when requested."""
    assert run_all.main([]) == 0
    assert "multiplicity_sim" not in recorded
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == list(CHAIN) + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(
    run_all: ModuleType,
    driver_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run the chain against a synthetic tree."""
    monkeypatch.setattr(sys.modules["power_analysis"], "main", lambda *a, **k: None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert run_all.main([], results_dir=driver_tree) == 0
    out = buf.getvalue()
    # Ordered banners keep long logs attributable.
    positions = [out.find(name) for name in CHAIN]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    assert "compliance" in out.lower()
