"""Pin notebook README path claims against the tree."""

from __future__ import annotations

import re

import pytest

from tests._paths import NOTEBOOKS, REPO_ROOT

README_MD = NOTEBOOKS / "README.md"


@pytest.fixture(scope="module")
def readme() -> str:
    """Read notebooks/README.md once per module."""
    return README_MD.read_text()


def test_every_file_the_notebooks_readme_names_exists(readme: str) -> None:
    """README paths resolve, as the counterpart to the root README map check."""
    named = sorted(
        set(re.findall(r"[\w./-]*[\w-]+\.(?:py|ipynb|md|yaml|toml)", readme))
    )
    assert named, "the README names no files at all"
    skip = {"pyproject.toml"}  # Named as a root-level concept.

    def resolves(name: str) -> bool:
        # Placeholder paths truncate at ``>``; resolve the remaining basename.
        name = name.lstrip("/")
        if "<" in name or name in skip:
            return True
        if "/" in name:
            return (REPO_ROOT / name).exists() or any(
                p.as_posix().endswith(f"/{name}")
                for p in REPO_ROOT.rglob(name.rsplit("/", 1)[1])
            )
        return any(REPO_ROOT.rglob(name))

    ghosts = [n for n in named if not resolves(n)]
    assert not ghosts, f"notebooks/README.md names files that do not exist: {ghosts}"
