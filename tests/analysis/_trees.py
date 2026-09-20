"""Sibling test directories import root conftest by bare name; a second conftest here would shadow it."""

import hashlib
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
sys.path.insert(0, str(ANALYSIS_DIR))
sys.path.insert(0, str(NOTEBOOKS))
import extens_vs_noise  # noqa: E402
import multiplicity_sim  # noqa: E402
import paired_analysis  # noqa: E402
import power_analysis  # noqa: E402
import run_all  # noqa: E402
import significance_report  # noqa: E402

#: Sign-flip floor 2/2**6 is above the primary correction threshold.
SHALLOW_DEPTH = 6
#: 2/2**16 is below the primary correction threshold.
DEEP_DEPTH = 16

N_HARMONICS = power_analysis.N_HARMONICS
N_PRIMARY = power_analysis.N_PRIMARY


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
def run_all() -> ModuleType:
    """Return the analysis driver module."""
    return sys.modules["run_all"]


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
