"""Shared helpers for ``statistical_analyses.ipynb`` cell tests.

Cells use stable content because indexes can silently target another cell.
This module is not named ``test_*`` because it holds no tests and must not be collected.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from types import ModuleType

from tests._paths import NOTEBOOKS, REPO_ROOT

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"


def load_notebook() -> dict:
    """Parse ``statistical_analyses.ipynb``."""
    return json.loads(STATS_NB.read_text())


def cell_source(nb: dict, needle: str) -> str:
    """Return the unique cell containing `needle`; indexes can silently drift."""
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


def _load(name: str, rel: str) -> ModuleType:
    """Exec ``notebooks/<rel>`` under `name`, registering it before exec."""
    spec = importlib.util.spec_from_file_location(name, NOTEBOOKS / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclass annotations resolve early
    spec.loader.exec_module(module)
    return module


def load_analysis_modules() -> dict:
    """Execute the notebook loader cell and return its namespace.

    Run from the repo root because ``find_repo()`` walks up from cwd; preserve load order
    because siblings use bare imports, and restore state because ``load_dotenv`` mutates unknown keys.
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
