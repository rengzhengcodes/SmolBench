"""Sibling test directories import root conftest by bare name; a second conftest here would shadow it."""

# pylint: disable=import-error,unused-import,wrong-import-order,function-redefined,no-member
# The analysis scripts are imported by bare name off a runtime sys.path insert,
# and the session fixtures deliberately shadow those module names.

import contextlib
import hashlib
import importlib.util
import io
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
MODELS = power_analysis.MODELS
FAMILIES = power_analysis.FAMILIES
INFOS = power_analysis.INFOS

Cell = (
    tuple[float, float | Callable[[int], float], str, Sequence[int]]
    | tuple[float, float | Callable[[int], float], str, Sequence[int], float]
)


def run_captured(fn: Callable[[], object]) -> str:
    """Call `fn`, returning everything it wrote to stdout and stderr.

    Parameters
    ----------
    fn : Callable[[], object]
        Zero-argument callable to run under capture.

    Returns
    -------
    str
        Combined stdout and stderr text.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        fn()
    return buf.getvalue()


def profile_for(
    overrides: Mapping[tuple[str, str], Cell] | None = None,
    rate: float = 0.90,
    depth: int = DEEP_DEPTH,
) -> Callable[[str, str], Cell]:
    """Build a cell profile: `rate` everywhere (0.10 on the zero arm) unless overridden.

    Parameters
    ----------
    overrides : Mapping[tuple[str, str], Cell] | None
        Explicit cells keyed by ``(model, info)``; all others use the default.
    rate : float
        Accuracy of the default non-zero cells.
    depth : int
        Number of seeds in the default cells.

    Returns
    -------
    Callable[[str, str], Cell]
        ``profile(model, info)`` for `build_tree`.
    """

    def profile(model: str, info: str) -> Cell:
        base: Cell = (0.10 if info == "zero" else rate), 0.0, "empty", range(depth)
        return (overrides or {}).get((model, info), base)

    return profile


def _marks_for(
    rate: float,
    noncompliance: float,
    mode: str,
    rng: np.random.Generator,
    invalid: float = 0.0,
) -> Marks:
    """Build one replicate with independent score, validity, and compliance axes."""
    scores = (rng.random(N_HARMONICS) < rate).astype(int).tolist()
    bad = rng.random(N_HARMONICS) < noncompliance
    null = rng.random(N_HARMONICS) < invalid
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(
                query=f"q{i}",
                answer=i,
                response=str(i),
                score=None if nl else int(s),
                compliance=(mode if b else COMPLIANT),
            )
            for i, (s, b, nl) in enumerate(zip(scores, bad, null))
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def build_tree(
    root: Path,
    profile: Callable[[str, str], Cell],
    copies: Mapping[tuple[str, str], tuple[str, str]] | None = None,
) -> None:
    """Write a ``{model}_{info}/rep_{seed}.yaml`` tree under `root` for every study cell."""
    for model in MODELS:
        for info in INFOS:
            rate, noncompliance, mode, seeds, *rest = profile(model, info)
            invalid = rest[0] if rest else 0.0
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
                _marks_for(rate, rate_of(seed), mode, rng, invalid=invalid).dump(
                    cdir / f"rep_{seed}.yaml"
                )
    for dst, src in (copies or {}).items():
        dst_dir = root / f"{dst[0]}_{dst[1]}"
        src_dir = root / f"{src[0]}_{src[1]}"
        shutil.rmtree(dst_dir, ignore_errors=True)
        shutil.copytree(src_dir, dst_dir)


#: Every bare module name the induction and deduction analysis scripts share.
_BARE_SIBLINGS = (
    "_power_common",
    "power_analysis",
    "paired_analysis",
    "error_bars",
    "hint_vs_noise",
    "rows_source",
    "significance_report",
    "extens_vs_noise",
    "multiplicity_sim",
    "run_all",
)


def _owned_by(module: ModuleType, directory: Path) -> bool:
    """Whether `module` was loaded from a file directly inside `directory`."""
    file = getattr(module, "__file__", None)
    if not file:
        return False
    return Path(file).resolve().parent == Path(directory).resolve()


def load_analysis(name: str, analysis_dir: Path = ANALYSIS_DIR) -> ModuleType:
    """Import one ``analysis/`` script by path, under its own bare module name.

    The scripts import each other by bare name off a ``sys.path`` insert they
    perform themselves, so they must be registered in ``sys.modules`` under
    exactly that bare name or a sibling import re-executes the module and the
    two copies disagree about ``RESULTS_DIR``. `analysis_dir` lets both study
    trees share the same collision-safe loader.

    Parameters
    ----------
    name : str
        Bare module name to load.
    analysis_dir : Path, optional
        Directory containing the analysis scripts.

    Returns
    -------
    ModuleType
        Loaded analysis module.
    """
    # Reuse the cached module only when it really is THIS directory's script.
    # The deduction leg's analysis scripts (notebooks/deduction/analysis/) use
    # the same bare names (power_analysis, error_bars, ...) and register
    # themselves under them via their own sys.path insert, so after a deduction
    # test has run, ``sys.modules["power_analysis"]`` may be the deduction
    # module: returning it here would hand this fixture the wrong study's
    # constants. Evict every stale sibling before loading so the scripts'
    # bare-name imports re-resolve against analysis_dir.
    cached = sys.modules.get(name)
    if cached is not None and _owned_by(cached, analysis_dir):
        return cached
    for sibling in _BARE_SIBLINGS:
        mod = sys.modules.get(sibling)
        if mod is not None and not _owned_by(mod, analysis_dir):
            del sys.modules[sibling]
    sys.path.insert(0, str(analysis_dir))
    sys.path.insert(0, str(NOTEBOOKS))
    spec = importlib.util.spec_from_file_location(name, analysis_dir / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tree_fixture(
    name: str,
    profile: Callable[[str, str], Cell],
    doc: str,
    copies: Mapping[tuple[str, str], tuple[str, str]] | None = None,
) -> Callable[[pytest.TempPathFactory], Path]:
    """Return a session fixture named `name` that builds `profile` once.

    Parameters
    ----------
    name : str
        Fixture name; also the ``tmp_path_factory`` directory basename.
    profile : Callable[[str, str], Cell]
        Cell profile handed to `build_tree`.
    doc : str
        Docstring given to the generated fixture.
    copies : Mapping[tuple[str, str], tuple[str, str]] | None
        Forwarded to `build_tree`.

    Returns
    -------
    Callable[[pytest.TempPathFactory], Path]
        The fixture function, to be bound at module scope.
    """

    @pytest.fixture(scope="session", name=name)
    def fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
        root = tmp_path_factory.mktemp(name)
        build_tree(root, profile, copies=copies)
        return root

    fixture.__doc__ = doc
    return fixture


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
