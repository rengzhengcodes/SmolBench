"""Synthetic result trees for analysis-report tests.

Not ``conftest.py``: pytest would collide with the bare ``conftest`` module.
Depth controls whether ``2 / 2**S`` clears Holm's ``0.05 / 210`` threshold.
"""

import hashlib
import importlib.util
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT
from tests._paths import NOTEBOOKS

ANALYSIS_DIR = NOTEBOOKS / "induction" / "analysis"

#: Sign-flip floor 2/2**6 = 0.031 >> 0.05/210: nothing is rejectable.
SHALLOW_DEPTH = 6
#: 2/2**16 = 3.05e-5 < 0.05/210 = 2.381e-4: the normal path is reachable.
DEEP_DEPTH = 16

#: Must match ``power_analysis.N_HARMONICS`` or marks are treated as partial.
N_HARMONICS = 9


def _marks_for(rate: float, noncompliance: float, mode: str, rng: np.random.Generator) -> Marks:
    """Build one replicate with independent score and compliance axes."""
    scores = (rng.random(N_HARMONICS) < rate).astype(int).tolist()
    bad = rng.random(N_HARMONICS) < noncompliance
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(query=f"q{i}", answer=i, response=str(i), score=int(s),
                 compliance=(mode if b else COMPLIANT))
            for i, (s, b) in enumerate(zip(scores, bad))
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def build_tree(
    root: Path,
    models: Sequence[str],
    infos: Sequence[str],
    profile: Callable[[str, str], tuple[float, float | Callable[[int], float], str, Sequence[int]]],
    copies: Mapping[tuple[str, str], tuple[str, str]] | None = None,
) -> None:
    """Write a ``{model}_{info}/rep_{seed}.yaml`` tree under `root`."""
    for model in models:
        for info in infos:
            rate, noncompliance, mode, seeds = profile(model, info)
            rate_of = noncompliance if callable(noncompliance) else (
                lambda _seed, _v=noncompliance: _v)
            cdir = root / f"{model}_{info}"
            cdir.mkdir(parents=True, exist_ok=True)
            for seed in seeds:
                # Avoid randomized hash() so report assertions are reproducible.
                digest = hashlib.blake2b(
                    f"{model}/{info}/{seed}".encode(), digest_size=4
                ).digest()
                rng = np.random.default_rng(int.from_bytes(digest, "big"))
                _marks_for(rate, rate_of(seed), mode, rng).dump(
                    cdir / f"rep_{seed}.yaml"
                )
    for dst, src in (copies or {}).items():
        dst_dir = root / f"{dst[0]}_{dst[1]}"
        src_dir = root / f"{src[0]}_{src[1]}"
        shutil.rmtree(dst_dir, ignore_errors=True)
        shutil.copytree(src_dir, dst_dir)


def load_analysis(name: str) -> ModuleType:
    """Import an analysis script under its bare module name.

    Registration prevents sibling imports from creating a second ``RESULTS_DIR``.
    """
    if name in sys.modules:
        return sys.modules[name]
    sys.path.insert(0, str(ANALYSIS_DIR))
    sys.path.insert(0, str(NOTEBOOKS))
    spec = importlib.util.spec_from_file_location(name, ANALYSIS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def power_analysis() -> ModuleType:
    """The root of the analysis import chain; owns MODELS/INFOS/RESULTS_DIR."""
    return load_analysis("power_analysis")


@pytest.fixture(scope="session")
def multiplicity_sim(power_analysis: ModuleType) -> ModuleType:
    """The standalone Monte Carlo module."""
    return load_analysis("multiplicity_sim")


@pytest.fixture(scope="session")
def paired_analysis(power_analysis: ModuleType) -> ModuleType:
    """The paired re-analysis module (imports ``power_analysis``)."""
    return load_analysis("paired_analysis")


@pytest.fixture(scope="session")
def significance_report(paired_analysis: ModuleType) -> ModuleType:
    """The Holm/Hochberg report module (imports both of the above)."""
    return load_analysis("significance_report")


@pytest.fixture(scope="session")
def extens_vs_noise(significance_report: ModuleType) -> ModuleType:
    """The focused extens-vs-noise report module (imports all three)."""
    return load_analysis("extens_vs_noise")


@pytest.fixture
def repoint(monkeypatch: pytest.MonkeyPatch) -> Callable[[Path], None]:
    """Return a callable that repoints every loaded analysis module.

    Siblings import ``RESULTS_DIR`` by value.
    """

    def _repoint(root: Path) -> None:
        for name in ("power_analysis", "paired_analysis", "significance_report",
                     "extens_vs_noise"):
            module = sys.modules.get(name)
            if module is not None and hasattr(module, "RESULTS_DIR"):
                monkeypatch.setattr(module, "RESULTS_DIR", root)

    return _repoint
