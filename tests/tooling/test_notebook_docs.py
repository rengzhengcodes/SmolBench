"""Pin notebook README and archive claims against code.

Readers skip retired runs, then apply earliest-wins to what survives.
Import marker spellings from the store module so stale quoted markers fail here.
"""

from __future__ import annotations

import re

import pytest

from tests._paths import NOTEBOOKS, REPO_ROOT

ARCHIVE_MD = NOTEBOOKS / "ARCHIVE.md"
README_MD = NOTEBOOKS / "README.md"


@pytest.fixture(scope="module")
def archive() -> str:
    return ARCHIVE_MD.read_text()


@pytest.fixture(scope="module")
def readme() -> str:
    return README_MD.read_text()


def test_archive_documents_both_supersede_spellings(archive: str) -> None:
    """Document both spellings because naming only one makes the other look corrupt."""
    from smolbench.evals.results_store import (
        LOCAL_SUPERSEDED_INFIX,
        S3_SUPERSEDED_SUFFIX,
    )

    s3_suffix, local_infix = S3_SUPERSEDED_SUFFIX, LOCAL_SUPERSEDED_INFIX
    assert s3_suffix in archive, f"ARCHIVE.md never names the {s3_suffix} marker key"
    assert local_infix in archive, \
        f"ARCHIVE.md never names the local {local_infix} rename"
    assert "earliest-wins" in archive


def test_both_docs_describe_the_regrade_path(archive: str, readme: str) -> None:
    """Both docs name ``regraded_from`` for replacement traceability."""
    from smolbench.evals.quiz import Marks

    assert "regraded_from" in Marks.__dataclass_fields__, \
        "Marks no longer carries regraded_from; this test's premise is stale"
    for name, text in (("ARCHIVE.md", archive), ("README.md", readme)):
        assert "regrade" in text, f"notebooks/{name} never mentions regrading"
        assert "regraded_from" in text, f"notebooks/{name} never names regraded_from"


def test_the_docs_name_the_direct_s3_readers(readme: str) -> None:
    """The notebook guide points readers at the direct S3 path."""
    assert "--s3" in readme, "notebooks/README.md never mentions the --s3 readers"
    assert "rows_source" in readme, \
        "notebooks/README.md never names the shared row reader"


def test_archive_locates_the_recovery_rows_the_notebook_reads(archive: str) -> None:
    """Archive locates recovery rows read by notebook and audit."""
    from tests._paths import SCRIPTS

    audit = (SCRIPTS / "results" / "audit_lean_pinning.py").read_text()
    run = re.search(r'RECOVERY_RUN = "([^"]+)"', audit)
    assert run, "audit_lean_pinning no longer declares RECOVERY_RUN"
    assert run.group(1) in archive, \
        f"ARCHIVE.md never locates the {run.group(1)} rows"
    assert "recovered_rows.jsonl" in archive


def test_archive_names_the_prefix_the_readers_actually_default_to(archive: str) -> None:
    """Name the re-collection prefix ``rows_source.spool_prefix()`` defaults to, not the retired one."""
    import importlib.util
    import sys

    path = NOTEBOOKS / "deduction" / "analysis" / "rows_source.py"
    spec = importlib.util.spec_from_file_location("docs_rows_source", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module._DEDUCTION_SPOOL_PREFIX in archive, (
        f"ARCHIVE.md never names the re-collection prefix "
        f"{module._DEDUCTION_SPOOL_PREFIX!r}")


def test_every_file_the_notebooks_readme_names_exists(readme: str) -> None:
    """README paths resolve, as the counterpart to the root README map check."""
    named = sorted(set(re.findall(r"[\w./-]*[\w-]+\.(?:py|ipynb|md|yaml|toml)", readme)))
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
                for p in REPO_ROOT.rglob(name.rsplit("/", 1)[1]))
        return any(REPO_ROOT.rglob(name))

    ghosts = [n for n in named if not resolves(n)]
    assert not ghosts, f"notebooks/README.md names files that do not exist: {ghosts}"
