"""Synthetic result trees for the ``notebooks/induction/analysis/`` report scripts.

NOT a ``conftest.py``. ``tests/`` has no ``__init__.py`` (deliberately -- see
``tests/README.md``), so pytest imports every ``conftest.py`` under it as the
BARE module name ``conftest``; a second one here would win
``sys.modules["conftest"]`` and break the ``from conftest import
StubTokenizer`` that ``tests/evals/`` and ``tests/induction/`` do. The fixtures
below are imported into each analysis test module's namespace instead, which
pytest collects just the same.

The analysis chain has no fixtures of its own: every script walks a real
replicate tree (``{model}_{info}/rep_{seed}.yaml``, 21 models x 4 info arms)
and ``SystemExit``s on any missing cell, so nothing in it can be exercised
without one. These fixtures build that tree under ``tmp_path`` with
CONTROLLED per-cell accuracy and compliance, then load each analysis module
by path with its ``RESULTS_DIR`` repointed at it.

Depth is the load-bearing knob. The primary test is an exact seed-level
sign-flip whose resolution floor is ``2 / 2**S``, while Holm's LOOSEST
threshold over the 210-contrast family is ``0.05 / 210 = 2.381e-4``:

* ``2 / 2**13 = 2.44e-4`` -- above the threshold, so NO contrast can be
  rejected however large its effect; the report must say so rather than
  publish a null result.
* ``2 / 2**14 = 1.22e-4`` -- below it, so the normal path is reachable.

Hence ``SHALLOW_DEPTH`` (6 seeds, floor-bound) and ``DEEP_DEPTH`` (16 seeds,
resolvable) below.
"""

import hashlib
import importlib.util
import shutil
import sys
from datetime import datetime, timezone

import numpy as np
import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT, NOT_ASSESSED
from tests._paths import NOTEBOOKS

ANALYSIS_DIR = NOTEBOOKS / "induction" / "analysis"

#: Sign-flip floor 2/2**6 = 0.031 >> 0.05/210: nothing is rejectable.
SHALLOW_DEPTH = 6
#: 2/2**16 = 3.05e-5 < 0.05/210 = 2.381e-4: the normal path is reachable.
DEEP_DEPTH = 16

#: Marks per replicate; must equal ``power_analysis.N_HARMONICS`` or
#: ``paired_analysis.load_marks`` skips every replicate as partially written.
N_HARMONICS = 9


def _marks_for(rate: float, noncompliance: float, mode, rng) -> Marks:
    """Build one replicate: `N_HARMONICS` marks at accuracy `rate`.

    `noncompliance` is the share of marks carrying the violation label `mode`
    instead of `COMPLIANT`. Compliance is drawn INDEPENDENTLY of the score, so
    a lane can be well-formed and wrong, or malformed and (by luck) right --
    the two axes the census and the contrast machinery are supposed to keep
    separate. ``mode=None`` writes the whole replicate as `NOT_ASSESSED`
    (a pre-compliance-field legacy lane), which the census must EXCLUDE
    rather than publish as 0% non-compliant.
    """
    scores = (rng.random(N_HARMONICS) < rate).astype(int).tolist()
    bad = rng.random(N_HARMONICS) < noncompliance
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(query=f"q{i}", answer=i, response=str(i), score=int(s),
                 compliance=(NOT_ASSESSED if mode is None
                             else (mode if b else COMPLIANT)))
            for i, (s, b) in enumerate(zip(scores, bad))
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def build_tree(root, models, infos, profile, copies=None):
    """Write a full ``{model}_{info}/rep_{seed}.yaml`` tree under `root`.

    Parameters
    ----------
    profile : callable
        ``(model, info) -> (rate, noncompliance, mode, seeds)``. `seeds` is the
        iterable of seeds to write for that cell, so a cell can deliberately be
        SHALLOWER than its neighbours -- the mismatched-seed-set case the
        padding table has to handle. `noncompliance` may be a float or a
        ``seed -> float`` callable, so a cell's compliance can differ ON THE
        SEEDS A NEIGHBOURING CELL LACKS (which is what makes a whole-cell rate
        disagree with a common-seed rate).
    copies : dict, optional
        ``(model, info) -> (model, info)``: write the destination cell as a
        BYTE COPY of the source cell, for engineering an EXACT tie between two
        arms. Applied after `profile`, overwriting whatever it wrote.
    """
    for model in models:
        for info in infos:
            rate, noncompliance, mode, seeds = profile(model, info)
            rate_of = noncompliance if callable(noncompliance) else (
                lambda _seed, _v=noncompliance: _v)
            cdir = root / f"{model}_{info}"
            cdir.mkdir(parents=True, exist_ok=True)
            for seed in seeds:
                # One RNG per cell-seed, keyed by the names through a STABLE
                # digest: the tree is byte-identical across runs and across
                # machines, so a report assertion cannot flake. (Never
                # ``hash()`` -- PYTHONHASHSEED randomizes str hashing per
                # process, which would re-roll every cell on each run.)
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


def load_analysis(name: str):
    """Import one ``analysis/`` script by path, under its own bare module name.

    The scripts import each other by BARE name off a ``sys.path`` insert they
    perform themselves, so they must be registered in ``sys.modules`` under
    exactly that bare name or a sibling import re-executes the module and the
    two copies disagree about ``RESULTS_DIR``.
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
def power_analysis():
    """The root of the analysis import chain; owns MODELS/INFOS/RESULTS_DIR."""
    return load_analysis("power_analysis")


@pytest.fixture(scope="session")
def paired_analysis(power_analysis):
    """The paired re-analysis module (imports ``power_analysis``)."""
    return load_analysis("paired_analysis")


@pytest.fixture(scope="session")
def significance_report(paired_analysis):
    """The Holm/Hochberg report module (imports both of the above)."""
    return load_analysis("significance_report")


@pytest.fixture(scope="session")
def extens_vs_noise(significance_report):
    """The focused extens-vs-noise report module (imports all three)."""
    return load_analysis("extens_vs_noise")


@pytest.fixture
def repoint(monkeypatch):
    """Return a callable repointing every loaded analysis module at `root`.

    ``RESULTS_DIR`` is imported BY VALUE into each sibling (``from
    power_analysis import RESULTS_DIR``), so patching the owner alone leaves
    the importers reading the real tree.
    """

    def _repoint(root):
        for name in ("power_analysis", "paired_analysis", "significance_report",
                     "extens_vs_noise"):
            module = sys.modules.get(name)
            if module is not None and hasattr(module, "RESULTS_DIR"):
                monkeypatch.setattr(module, "RESULTS_DIR", root)

    return _repoint
