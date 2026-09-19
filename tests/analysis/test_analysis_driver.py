"""Pin analysis-driver order and its computation/render split."""

import contextlib
import inspect
import io
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest

# Fixture names register pytest fixtures.
# pylint: disable=unused-import
from tests.analysis._trees import (  # noqa: F401 -- imported for the fixtures
    DEEP_DEPTH, build_tree, extens_vs_noise, load_analysis, multiplicity_sim,
    paired_analysis, power_analysis, repoint, significance_report)

#: Exclude costly, result-free multiplicity_sim unless explicitly requested.
CHAIN = ("power_analysis", "paired_analysis", "significance_report", "extens_vs_noise")


@pytest.fixture(scope="session")
def run_all(extens_vs_noise: ModuleType) -> ModuleType:
    """Load the driver after its chain modules."""
    return load_analysis("run_all")


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
    # A subprocess import of the driver alone must not pull the simulation in.
    code = (
        "import sys, importlib.util;"
        f"spec = importlib.util.spec_from_file_location('run_all', {str(run_all.__file__)!r});"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        "print('multiplicity_sim' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False", out.stdout


def test_the_driver_runs_the_chain_in_order(
    run_all: ModuleType, recorded: list[str]
) -> None:
    """Run result-reading scripts in dependency order."""
    assert run_all.main([]) == 0
    assert recorded == list(CHAIN)


def test_the_simulation_runs_only_behind_its_flag(
    run_all: ModuleType, recorded: list[str]
) -> None:
    """Run multiplicity simulation only when requested."""
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
    """Run the chain against a synthetic tree."""
    repoint(driver_tree)
    monkeypatch.setattr(sys.modules["power_analysis"], "main", lambda *a, **k: None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        assert run_all.main([]) == 0
    out = buf.getvalue()
    # Ordered banners keep long logs attributable.
    positions = [out.find(name) for name in CHAIN]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions), positions
    assert "compliance" in out.lower()


# power_analysis computation/render split.


def section_pairs(module: ModuleType) -> list[tuple[str, str]]:
    """Return render/data function pairs."""
    return [
        (name, name[len("render_") :])
        for name in dir(module)
        if name.startswith("render_") and inspect.isfunction(getattr(module, name))
    ]


def test_every_printed_section_has_a_data_function_behind_it(
    power_analysis: ModuleType,
) -> None:
    """Keep data/render pairs reusable without captured stdout."""
    pairs = section_pairs(power_analysis)
    assert len(pairs) >= 8, [name for name, _ in pairs]
    for render_name, data_name in pairs:
        data = getattr(power_analysis, data_name, None)
        assert inspect.isfunction(
            data
        ), f"{render_name} has no {data_name} data function behind it"


def test_the_data_functions_do_not_print(power_analysis: ModuleType) -> None:
    """Only render functions print."""
    for _render_name, data_name in section_pairs(power_analysis):
        source = inspect.getsource(getattr(power_analysis, data_name))
        assert "print(" not in source, f"{data_name} prints"


def test_main_is_a_short_orchestrator(power_analysis: ModuleType) -> None:
    """Keep ``main()`` a short orchestrator."""
    lines = inspect.getsource(power_analysis.main).splitlines()
    assert len(lines) <= 60, len(lines)


# multiplicity_sim.apply_corrections parameters.


def test_apply_corrections_keeps_only_the_parameter_it_reads(
    multiplicity_sim: ModuleType,
) -> None:
    """Reject unused parameters that could mis-correct p-values."""
    assert list(inspect.signature(multiplicity_sim.apply_corrections).parameters) == [
        "pv"
    ]


def test_apply_corrections_matches_statsmodels(multiplicity_sim: ModuleType) -> None:
    """Batched masks agree with statsmodels row by row away from exact ties."""
    from statsmodels.stats.multitest import multipletests

    alpha = multiplicity_sim.ALPHA
    rng = np.random.default_rng(7)
    pv = np.vstack(
        [
            rng.uniform(0, 1, size=(40, 6)),
            rng.uniform(0, 0.02, size=(10, 6)),
            np.array([[0.001, 0.011, 0.021, 0.031, 0.041, 0.9]]),
        ]
    )
    got = multiplicity_sim.apply_corrections(pv)
    methods = {
        "Bonferroni": "bonferroni",
        "Holm": "holm",
        "Hochberg": "simes-hochberg",
        "BH(q=0.05)": "fdr_bh",
    }
    for name, method in methods.items():
        for row, mask in zip(pv, got[name]):
            expected = multipletests(row, alpha=alpha, method=method)[0]
            assert list(mask) == list(expected), (name, row.tolist())


def test_apply_corrections_share_one_inclusive_boundary(
    multiplicity_sim: ModuleType,
) -> None:
    """Every procedure rejects a p-value sitting exactly on its threshold (``<=``)."""
    alpha = multiplicity_sim.ALPHA
    m = 4
    # Row 1: p exactly at the Bonferroni bar, then exactly at Holm's second step.
    # Row 2: all p exactly at the BH ranks i * alpha / m.
    pv = np.array(
        [
            [alpha / m, alpha / (m - 1), 0.5, 0.9],
            [alpha * 1 / m, alpha * 2 / m, alpha * 3 / m, alpha * 4 / m],
        ]
    )
    got = multiplicity_sim.apply_corrections(pv)
    assert list(got["Bonferroni"][0]) == [True, False, False, False]
    assert list(got["Holm"][0]) == [True, True, False, False]
    assert list(got["Hochberg"][0]) == [True, True, False, False]
    assert list(got["BH(q=0.05)"][1]) == [True, True, True, True]
    assert list(got["Hochberg"][1]) == [True, True, True, True]
    assert list(got["Bonferroni"][1]) == [True, False, False, False]
