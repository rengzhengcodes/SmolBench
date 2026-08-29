"""Single source of truth for repo-relative path anchors used across the test suite.

tests/ is grouped into subject subdirectories (evals/, induction/, deduction/,
tooling/) while tests/conftest.py and tests/fixtures/ stay at the tests/ root
(fixtures like lean_mini are shared across groups, and pytest resolves
conftest.py by directory ancestry). Individual test modules used to compute
these anchors by hand-counting `Path(__file__).resolve().parents[N]`, which
silently breaks whenever a test file moves to a different directory depth.
Importing the constants below instead means a future move only has to update
this one file.
"""

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
LEAN_MINI = FIXTURES / "lean_mini"
SCRIPTS = REPO_ROOT / "scripts"
NOTEBOOKS = REPO_ROOT / "notebooks"
