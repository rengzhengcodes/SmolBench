"""Provide synthetic result trees and imported analysis-module fixtures."""

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

_ROOT_CONFTEST = Path(__file__).parents[1] / "conftest.py"
_ROOT_SPEC = importlib.util.spec_from_file_location(
    "_smolbench_root_conftest", _ROOT_CONFTEST
)
if _ROOT_SPEC is None or _ROOT_SPEC.loader is None:
    raise ImportError(f"Cannot load {_ROOT_CONFTEST}")
_ROOT_MODULE = importlib.util.module_from_spec(_ROOT_SPEC)
_ROOT_SPEC.loader.exec_module(_ROOT_MODULE)
for _name in (
    "MergeEverythingTokenizer",
    "StubServer",
    "StubTokenizer",
    "TruncatingTokenizer",
    "_StubHandler",
    "chat_completion",
    "import_run_study",
):
    globals()[_name] = getattr(_ROOT_MODULE, _name)

ANALYSIS_DIR = NOTEBOOKS / "induction" / "analysis"
sys.path.extend(str(path) for path in (NOTEBOOKS, ANALYSIS_DIR))
import extens_vs_noise
import multiplicity_sim
import paired_analysis
import power_analysis
import significance_report

#: Sign-flip floor 2/2**6 = 0.031 >> 0.05/210: nothing is rejectable.
SHALLOW_DEPTH = 6
#: 2/2**16 = 3.05e-5 < 0.05/210 = 2.381e-4: the normal path is reachable.
DEEP_DEPTH = 16

N_HARMONICS = power_analysis.N_HARMONICS


def _marks_for(
    rate: float, noncompliance: float, mode: str, rng: np.random.Generator
) -> Marks:
    """Build one replicate with independent score and compliance axes."""
    scores = (rng.random(N_HARMONICS) < rate).astype(int).tolist()
    bad = rng.random(N_HARMONICS) < noncompliance
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(
                query=f"q{i}",
                answer=i,
                response=str(i),
                score=int(s),
                compliance=(mode if b else COMPLIANT),
            )
            for i, (s, b) in enumerate(zip(scores, bad))
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def build_tree(
    root: Path,
    models: Sequence[str],
    infos: Sequence[str],
    profile: Callable[
        [str, str], tuple[float, float | Callable[[int], float], str, Sequence[int]]
    ],
    copies: Mapping[tuple[str, str], tuple[str, str]] | None = None,
) -> None:
    """Write a ``{model}_{info}/rep_{seed}.yaml`` tree under `root`."""
    for model in models:
        for info in infos:
            rate, noncompliance, mode, seeds = profile(model, info)
            rate_of = (
                noncompliance
                if callable(noncompliance)
                else (lambda _seed, _v=noncompliance: _v)
            )
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


@pytest.fixture(scope="session")
def power_analysis() -> ModuleType:
    """Return the power-analysis module."""
    return sys.modules["power_analysis"]


@pytest.fixture(scope="session")
def multiplicity_sim() -> ModuleType:
    """Return the multiplicity-simulation module."""
    return sys.modules["multiplicity_sim"]


@pytest.fixture(scope="session")
def paired_analysis() -> ModuleType:
    """Return the paired-analysis module."""
    return sys.modules["paired_analysis"]


@pytest.fixture(scope="session")
def significance_report() -> ModuleType:
    """Return the significance-report module."""
    return sys.modules["significance_report"]


@pytest.fixture(scope="session")
def extens_vs_noise() -> ModuleType:
    """Return the extens-versus-noise module."""
    return sys.modules["extens_vs_noise"]
