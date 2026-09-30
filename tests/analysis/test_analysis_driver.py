"""Pin the analysis driver: chain order, the ``--with-sim`` gate, and by-path imports."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests._paths import REPO_ROOT
from tests.analysis._trees import (
    ANALYSIS_DIR,
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
def recorded(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace every script's ``main`` with a call recorder.

    Returns
    -------
    list[str]
        Module names in the order their ``main`` was called.
    """
    calls: list[str] = []
    for module in run_all.CHAIN + (multiplicity_sim,):
        monkeypatch.setattr(
            module, "main", lambda *a, name=module.__name__, **k: calls.append(name)
        )
    return calls


def test_the_simulation_runs_only_behind_its_flag(recorded: list[str]) -> None:
    """The chain runs in order; the simulation only when ``--with-sim`` is passed."""
    run_all.main([])
    assert recorded == [m.__name__ for m in run_all.CHAIN]
    recorded.clear()
    run_all.main(["--with-sim"])
    assert recorded == [m.__name__ for m in run_all.CHAIN] + ["multiplicity_sim"]


def test_the_driver_really_runs_the_chain_in_one_process(
    driver_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the chain against a synthetic tree; banners appear in chain order."""
    monkeypatch.setattr(power_analysis, "main", lambda *a, **k: None)
    out = run_captured(lambda: run_all.main([], results_dir=driver_tree))
    positions = [out.find(m.__name__) for m in run_all.CHAIN]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    assert "compliance" in out.lower()


@pytest.mark.parametrize("name", sorted(p.stem for p in ANALYSIS_DIR.glob("*.py")))
def test_analysis_scripts_import_by_path(name: str) -> None:
    """Each analysis script imports with only the repository root on ``PYTHONPATH``."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy, sys; runpy.run_path(sys.argv[1])",
            str(ANALYSIS_DIR / f"{name}.py"),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
