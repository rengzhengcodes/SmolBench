"""Pin analysis-driver order and its computation/render split."""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests._paths import REPO_ROOT

# pylint: disable=unused-import  # fixture names register pytest fixtures
from tests.analysis._trees import (  # noqa: F401 -- imported for the fixtures
    extens_vs_noise,
    multiplicity_sim,
    power_analysis,
    profile_for,
    run_all,
    run_captured,
    tree_fixture,
)

driver_tree = tree_fixture(
    "driver_tree", profile_for(rate=0.99), "Build a complete synthetic tree."
)


@pytest.fixture
def recorded(
    monkeypatch: pytest.MonkeyPatch, run_all: ModuleType, multiplicity_sim: ModuleType
) -> list[str]:
    """Record script calls without running costly simulations."""
    calls: list = []
    chain = tuple(m.__name__ for m in run_all.CHAIN)

    def recorder(name: str) -> Callable[..., None]:
        def _main(*args: Any, **kwargs: Any) -> None:
            calls.append(name)

        return _main

    for name in chain + ("multiplicity_sim",):
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
    chain = tuple(m.__name__ for m in run_all.CHAIN)
    assert run_all.main([]) == 0
    assert "multiplicity_sim" not in recorded
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == list(chain) + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(
    run_all: ModuleType,
    driver_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run the chain against a synthetic tree."""
    chain = tuple(m.__name__ for m in run_all.CHAIN)
    monkeypatch.setattr(sys.modules["power_analysis"], "main", lambda *a, **k: None)
    out = run_captured(lambda: run_all.main([], results_dir=driver_tree))
    # Ordered banners keep long logs attributable.
    positions = [out.find(name) for name in chain]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    assert "compliance" in out.lower()


@pytest.mark.parametrize(
    "name",
    (
        "power_analysis",
        "paired_analysis",
        "significance_report",
        "extens_vs_noise",
        "multiplicity_sim",
    ),
)
def test_analysis_scripts_import_by_path(name: str) -> None:
    """Each analysis script imports with only the repository root on ``PYTHONPATH``."""
    path = REPO_ROOT / "notebooks" / "induction" / "analysis" / f"{name}.py"
    code = """
import importlib.util
import sys

name, path = sys.argv[1:]
spec = importlib.util.spec_from_file_location(name, path)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
"""
    env = {"PYTHONPATH": str(REPO_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code, name, str(path)],
        cwd=REPO_ROOT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
