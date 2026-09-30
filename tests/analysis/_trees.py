"""Synthetic results trees, capture helpers, and script handles shared by the analysis tests.

Not a conftest: sibling test directories import the root conftest by bare name and a
second one here would shadow it.
"""

import contextlib
import hashlib
import io
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Optional

import numpy as np
import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.parsing import EMPTY
from smolbench.evals.quiz import COMPLIANT
from tests._paths import NOTEBOOKS

ANALYSIS_DIR = NOTEBOOKS / "induction" / "analysis"
sys.path[:0] = [str(NOTEBOOKS), str(ANALYSIS_DIR)]

# pylint: disable=wrong-import-order,unused-import  # sys.path scripts read as third party; re-exported to the tests
import _power_common  # noqa: E402
import extens_vs_noise  # noqa: E402
import multiplicity_sim  # noqa: E402
import paired_analysis  # noqa: E402
import power_analysis  # noqa: E402
import run_all  # noqa: E402
import significance_report  # noqa: E402

# pylint: enable=wrong-import-order,unused-import

#: Sign-flip floor 2/2**6 is above the primary correction threshold.
SHALLOW_DEPTH = 6
#: 2/2**16 is below the primary correction threshold.
DEEP_DEPTH = 16

N_HARMONICS = power_analysis.N_HARMONICS
N_PRIMARY = power_analysis.N_PRIMARY
N_REPLICATES = multiplicity_sim.N_REPLICATES
MODELS = power_analysis.MODELS
FAMILIES = power_analysis.FAMILIES
INFOS = power_analysis.INFOS

#: ``(rate, noncompliance, seeds[, invalid])``; `noncompliance` may be a per-seed function.
Cell = (
    tuple[float, float | Callable[[int], float], Sequence[int]]
    | tuple[float, float | Callable[[int], float], Sequence[int], float]
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
    overrides: Optional[Mapping[tuple[str, str], Cell]] = None,
    rate: float = 0.90,
    depth: int = DEEP_DEPTH,
    invalid: float = 0.0,
) -> Callable[[str, str], Cell]:
    """Build a cell profile: `rate` everywhere (0.10 on the zero arm) unless overridden.

    Parameters
    ----------
    overrides : Optional[Mapping[tuple[str, str], Cell]]
        Explicit cells keyed by ``(model, info)``; all others use the default.
    rate : float
        Accuracy of the default non-zero cells.
    depth : int
        Number of seeds in the default cells.
    invalid : float
        Fraction of unscored (invalid) marks in the default cells.

    Returns
    -------
    Callable[[str, str], Cell]
        ``profile(model, info)`` for `build_tree`.
    """

    def profile(model: str, info: str) -> Cell:
        base: Cell = ((0.10 if info == "zero" else rate), 0.0, range(depth), invalid)
        return (overrides or {}).get((model, info), base)

    return profile


def _marks_for(
    rate: float, noncompliance: float, rng: np.random.Generator, invalid: float = 0.0
) -> Marks:
    """Draw one `N_HARMONICS`-mark replicate; `rate`, `noncompliance` and `invalid` are independent per-mark probabilities."""
    scores = rng.random(N_HARMONICS) < rate
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
                compliance=(EMPTY if b else COMPLIANT),
            )
            for i, (s, b, nl) in enumerate(zip(scores, bad, null))
        ),
    )


def build_tree(
    root: Path,
    profile: Callable[[str, str], Cell],
    copies: Optional[Mapping[tuple[str, str], tuple[str, str]]] = None,
) -> None:
    """Write a ``{model}_{info}/rep_{seed}.yaml`` tree under `root` for every study cell.

    Parameters
    ----------
    root : Path
        Results directory to populate.
    profile : Callable[[str, str], Cell]
        ``profile(model, info)`` giving each cell's generating parameters.
    copies : Optional[Mapping[tuple[str, str], tuple[str, str]]]
        ``{destination: source}`` cells overwritten with a byte copy after generation.
    """
    for model in MODELS:
        for info in INFOS:
            rate, noncompliance, seeds, *rest = profile(model, info)
            invalid = rest[0] if rest else 0.0
            cdir = root / f"{model}_{info}"
            cdir.mkdir(parents=True, exist_ok=True)
            for seed in seeds:
                # Avoid randomized hash() so report assertions are reproducible.
                digest = hashlib.blake2b(
                    f"{model}/{info}/{seed}".encode(), digest_size=4
                ).digest()
                rng = np.random.default_rng(int.from_bytes(digest, "big"))
                seed_nc = (
                    noncompliance(seed) if callable(noncompliance) else noncompliance
                )
                _marks_for(rate, seed_nc, rng, invalid).dump(cdir / f"rep_{seed}.yaml")
    for dst, src in (copies or {}).items():
        dst_dir = root / f"{dst[0]}_{dst[1]}"
        shutil.rmtree(dst_dir, ignore_errors=True)
        shutil.copytree(root / f"{src[0]}_{src[1]}", dst_dir)


def tree_fixture(
    name: str,
    profile: Callable[[str, str], Cell],
    doc: str,
    copies: Optional[Mapping[tuple[str, str], tuple[str, str]]] = None,
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
    copies : Optional[Mapping[tuple[str, str], tuple[str, str]]]
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
