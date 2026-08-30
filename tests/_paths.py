"""Single source of truth for repo-relative path anchors used across the test suite.

tests/ is grouped into subject subdirectories (evals/, induction/, deduction/,
tooling/) while tests/conftest.py and tests/fixtures/ stay at the tests/ root
(one fixtures tree serves the groups that need one -- evals/, induction/ and
deduction/ -- and pytest resolves conftest.py by directory ancestry). Import
these constants instead of hand-counting
``Path(__file__).resolve().parents[N]``, which silently breaks whenever a
test file moves to a different directory depth.
"""

from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
LEAN_MINI = FIXTURES / "lean_mini"
SCRIPTS = REPO_ROOT / "scripts"
NOTEBOOKS = REPO_ROOT / "notebooks"
