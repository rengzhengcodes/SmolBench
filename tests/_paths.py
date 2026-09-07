"""Single source of truth for repo-relative path anchors used across the test suite.

tests/ is grouped into subject subdirectories (evals/, induction/, deduction/,
tooling/) while tests/conftest.py and tests/fixtures/ stay at the tests/ root
(one fixtures tree serves the groups that need one -- evals/, induction/ and
deduction/ -- and pytest resolves conftest.py by directory ancestry). Import
these constants instead of hand-counting
``Path(__file__).resolve().parents[N]``, which silently breaks whenever a
test file moves to a different directory depth.
"""

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
LEAN_MINI = FIXTURES / "lean_mini"
#: Same shape as `LEAN_MINI` plus the `postcutoff` metadata block and
#: per-row ``"postcutoff": true`` flags -- the corpus shape
#: `smolbench.deduction.lean.corpus.is_postcutoff_corpus` accepts and the
#: deduction driver requires.
LEAN_MINI_POSTCUTOFF = FIXTURES / "lean_mini_postcutoff"
SCRIPTS = REPO_ROOT / "scripts"
NOTEBOOKS = REPO_ROOT / "notebooks"


def load_by_path(name: str, path: Path, *, snapshot_env: bool = False) -> ModuleType:
    """Execute `path` as a module registered under `name`.

    Registered in ``sys.modules`` BEFORE exec, because a PEP 563 dataclass in
    the loaded module resolves its own module through that entry.
    ``snapshot_env`` restores ``os.environ`` afterwards, for scripts that call
    ``load_dotenv`` (or set ``EC2_*`` defaults) at module scope.
    """
    saved = dict(os.environ) if snapshot_env else None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        sys.modules[name] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if saved is not None:
            os.environ.clear()
            os.environ.update(saved)
    return module
