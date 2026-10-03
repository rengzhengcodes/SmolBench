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
from typing import NamedTuple, Optional, Union

import numpy as np
import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.parsing import EMPTY
from smolbench.evals.quiz import COMPLIANT
from tests._paths import NOTEBOOKS

ANALYSIS_DIR = NOTEBOOKS / "induction" / "analysis"
sys.path[:0] = [str(NOTEBOOKS), str(ANALYSIS_DIR)]

# pylint: disable=wrong-import-order,unused-import  # sys.path scripts read as third party; re-exported to the tests
import _power_common
import extens_vs_noise
import multiplicity_sim
import paired_analysis
import power_analysis
import run_all
import significance_report
import study_design

# pylint: enable=wrong-import-order,unused-import

#: Sign-flip floor 2/2**6 is above the primary correction threshold.
SHALLOW_DEPTH = 6
#: 2/2**16 is below the primary correction threshold.
DEEP_DEPTH = 16
if not 2 / 2**DEEP_DEPTH <= study_design.ALPHA_PRIMARY < 2 / 2**SHALLOW_DEPTH:
    raise RuntimeError("SHALLOW_DEPTH and DEEP_DEPTH must straddle ALPHA_PRIMARY")

N_HARMONICS = study_design.N_HARMONICS
N_PRIMARY = study_design.N_PRIMARY
N_REPLICATES = study_design.N_REPLICATES
MODELS = study_design.MODELS
FAMILIES = study_design.FAMILIES
INFOS = study_design.INFOS

#: First roster cell: copy source of the all-identical trees, and the lane the loader tests corrupt.
FIRST_CELL: tuple[str, str] = (MODELS[0], INFOS[0])


def copies_from(
    source: tuple[str, str], infos: Sequence[str] = INFOS
) -> dict[tuple[str, str], tuple[str, str]]:
    """Byte-copy map for `build_tree`: every cell whose info is in `infos`, except `source`, copied from `source`.

    Parameters
    ----------
    source : tuple[str, str]
        Cell the listed cells are copied from.
    infos : Sequence[str], optional
        Arms to copy; every arm by default.

    Returns
    -------
    dict[tuple[str, str], tuple[str, str]]
        ``{destination: source}`` in `build_tree`'s ``copies`` shape.
    """
    return {(m, i): source for m in MODELS for i in infos if (m, i) != source}


class Cell(NamedTuple):
    """One cell's generating parameters; `noncompliance` may be a per-seed function."""

    rate: float
    noncompliance: Union[float, Callable[[int], float]]
    seeds: Sequence[int]
    invalid: float = 0.0


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
        Explicit cells keyed by ``(model, info)``, as `Cell` or positional tuple;
        all others use the default.
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
        base = ((0.10 if info == "zero" else rate), 0.0, range(depth), invalid)
        return Cell(*(overrides or {}).get((model, info), base))

    return profile


def _marks_for(
    rate: float, noncompliance: float, rng: np.random.Generator, invalid: float = 0.0
) -> Marks:
    """Draw one `N_HARMONICS`-mark replicate from independent per-mark probabilities.

    Parameters
    ----------
    rate : float
        P(score = 1) for each mark.
    noncompliance : float
        P(compliance = EMPTY) for each mark.
    rng : np.random.Generator
        Source of the draws, in the order scores, then non-compliance, then invalid.
    invalid : float
        P(score = None) for each mark.

    Returns
    -------
    Marks
        One `N_HARMONICS`-mark replicate for ``stub-model``.
    """
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
            cell = profile(model, info)
            cdir = root / f"{model}_{info}"
            cdir.mkdir(parents=True, exist_ok=True)
            for seed in cell.seeds:
                # Avoid randomized hash() so report assertions are reproducible.
                digest = hashlib.blake2b(
                    f"{model}/{info}/{seed}".encode(), digest_size=4
                ).digest()
                rng = np.random.default_rng(int.from_bytes(digest, "big"))
                nc = cell.noncompliance
                seed_nc = nc(seed) if callable(nc) else nc
                _marks_for(cell.rate, seed_nc, rng, cell.invalid).dump(
                    cdir / f"rep_{seed}.yaml"
                )
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
