"""Synthetic result trees for the ``notebooks/induction/analysis/`` report scripts.

Not a ``conftest.py``: tests/ has no ``__init__.py``, so pytest would import a
second conftest.py here under the bare module name ``conftest`` and collide
with the ``from conftest import StubTokenizer`` that tests/evals/ and
tests/induction/ rely on. Fixtures are imported into each analysis test
module's namespace instead.

Each analysis script walks a real replicate tree and exits on any missing
cell, so these fixtures build one under ``tmp_path`` and load each module by
path with ``RESULTS_DIR`` repointed at it. Depth controls whether the
seed-level sign-flip test can resolve anything: its floor ``2 / 2**S`` must
clear Holm's loosest threshold, ``0.05 / 210 = 2.381e-4``, over the
210-contrast family (see ``SHALLOW_DEPTH`` / ``DEEP_DEPTH`` below).
"""

import hashlib
import importlib.util
import shutil
import sys
from datetime import datetime, timezone

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

#: Marks per replicate; must equal ``power_analysis.N_HARMONICS`` or
#: ``paired_analysis.load_marks`` skips every replicate as partially written.
N_HARMONICS = 9


def _marks_for(rate: float, noncompliance: float, mode, rng) -> Marks:
    """Build one replicate: `N_HARMONICS` marks at accuracy `rate`.

    `noncompliance` is the share of marks carrying the violation label `mode`
    instead of `COMPLIANT`, drawn independently of the score so a lane can be
    well-formed and wrong, or malformed and right by luck -- the two axes the
    census and contrast machinery keep separate.
    """
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


def build_tree(root, models, infos, profile, copies=None):
    """Write a full ``{model}_{info}/rep_{seed}.yaml`` tree under `root`.

    profile: ``(model, info) -> (rate, noncompliance, mode, seeds)``. `seeds`
        can be shallower for one cell than its neighbours, to exercise the
        mismatched-seed-set case; `noncompliance` can vary by seed, so a
        whole-cell rate can disagree with the common-seed rate.
    copies: ``(model, info) -> (model, info)`` pairs to byte-copy after
        `profile` runs, for engineering an exact tie between two arms.
    """
    for model in models:
        for info in infos:
            rate, noncompliance, mode, seeds = profile(model, info)
            rate_of = noncompliance if callable(noncompliance) else (
                lambda _seed, _v=noncompliance: _v)
            cdir = root / f"{model}_{info}"
            cdir.mkdir(parents=True, exist_ok=True)
            for seed in seeds:
                # Keyed by a stable digest, not hash() (PYTHONHASHSEED
                # randomizes that per process), so the tree is byte-identical
                # across runs and machines and a report assertion can't flake.
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


#: Every bare module name the induction and deduction analysis scripts share.
_BARE_SIBLINGS = ("_power_common", "power_analysis", "paired_analysis", "error_bars",
                  "hint_vs_noise", "rows_source", "significance_report",
                  "extens_vs_noise", "multiplicity_sim")


def _owned_by(module, directory) -> bool:
    """Whether `module` was loaded from a file directly inside `directory`."""
    file = getattr(module, "__file__", None)
    if not file:
        return False
    from pathlib import Path as _P
    return _P(file).resolve().parent == _P(directory).resolve()


def load_analysis(name: str):
    """Import one ``analysis/`` script by path, under its own bare module name.

    The scripts import each other by bare name off a ``sys.path`` insert they
    perform themselves, so they must be registered in ``sys.modules`` under
    exactly that bare name or a sibling import re-executes the module and the
    two copies disagree about ``RESULTS_DIR``.
    """
    # Reuse the cached module only when it really is THIS directory's script.
    # The deduction leg's analysis scripts (notebooks/deduction/analysis/) use
    # the same bare names (power_analysis, error_bars, ...) and register
    # themselves under them via their own sys.path insert, so after a deduction
    # test has run, ``sys.modules["power_analysis"]`` may be the deduction
    # module: returning it here would hand this fixture the wrong study's
    # constants. Evict every stale sibling before loading so the scripts'
    # bare-name imports re-resolve against ANALYSIS_DIR.
    cached = sys.modules.get(name)
    if cached is not None and _owned_by(cached, ANALYSIS_DIR):
        return cached
    for sibling in _BARE_SIBLINGS:
        mod = sys.modules.get(sibling)
        if mod is not None and not _owned_by(mod, ANALYSIS_DIR):
            del sys.modules[sibling]
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

    ``RESULTS_DIR`` is imported by value into each sibling (``from
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
