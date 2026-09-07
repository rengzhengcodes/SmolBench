"""Shared machinery for the ``statistical_analyses.ipynb`` cell tests.

``tests/tooling/test_analysis_stats.py`` exercises the analysis MODULES that
notebook imports. Its ``test_stats_notebook_*`` siblings exercise the code the
notebook implements INLINE: sections 0, 7 and 8 define an archive reader, a
posterior-power classifier and a set of flip-rate estimators that live nowhere
else in the tree, so nothing else in the suite can catch them drifting from the
live modules they are supposed to agree with.

Each test pulls one cell's source out of the ``.ipynb`` by a stable needle and
``exec``s it, the same way ``tests/deduction/test_postcutoff_docs.py`` already
does for ``is_mathlib_cell``. Nothing here executes the notebook: the cells
under test are pure, and the one that builds an S3 client is handed a stubbed
``_aws.fresh_client`` so no AWS call is possible.

Not named ``test_*`` on purpose -- it holds no tests and must not be collected.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys

from tests._paths import NOTEBOOKS, REPO_ROOT

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"


def load_notebook() -> dict:
    """Parse ``statistical_analyses.ipynb``."""
    return json.loads(STATS_NB.read_text())


def cell_source(nb: dict, needle: str) -> str:
    """Return the source of the ONE cell containing `needle`.

    Cells are addressed by content, never by index: the notebook gains and
    loses cells, and an index-keyed test would silently start asserting about
    a different cell instead of failing.
    """
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


def _load(name: str, rel: str):
    """Exec ``notebooks/<rel>`` under `name`, registering it before exec."""
    spec = importlib.util.spec_from_file_location(name, NOTEBOOKS / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclass annotations resolve early
    spec.loader.exec_module(module)
    return module


def load_analysis_modules() -> dict:
    """Execute the notebook's OWN loader cell and return the namespace it binds.

    Exec'd rather than mirrored: both legs ship a ``power_analysis.py`` whose
    siblings import it by BARE name, so the bind-and-unbind order is
    load-bearing, and a second copy of it here would be free to drift from the
    order the notebook actually runs.

    The cell anchors the repo on ``Path.cwd()``, prints a provenance banner,
    inserts the repo root on ``sys.path``, and loads
    ``notebooks/induction/run_study.py``, which calls ``load_dotenv`` and parses
    ``INDUCTION_SHARD`` at MODULE SCOPE. So it is run from the repo root with
    its banner swallowed, and the whole environment is snapshotted and restored
    around it: ``load_dotenv`` writes keys that cannot be named in advance, so a
    per-key monkeypatch would not cover it.
    """
    namespace: dict = {}
    saved_modules = {k: sys.modules.get(k)
                     for k in ("power_analysis", "error_bars", "rows_source")}
    saved_env = dict(os.environ)
    saved_path = list(sys.path)
    try:
        source = cell_source(load_notebook(), "def _bound")
        with contextlib.chdir(REPO_ROOT), contextlib.redirect_stdout(io.StringIO()):
            exec(compile(source, str(STATS_NB), "exec"), namespace)
    finally:
        for key, old in saved_modules.items():
            if old is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = old
        os.environ.clear()
        os.environ.update(saved_env)
        sys.path[:] = saved_path
    return namespace


def load_deduction_power_analysis():
    """Load just the deduction ``power_analysis`` the notebook binds as ``ded_pa``."""
    return _load("nbt_ded_power_analysis_only", "deduction/analysis/power_analysis.py")
