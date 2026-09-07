"""``notebooks/README.md`` and ``notebooks/ARCHIVE.md``, pinned against the code.

Entry points a reader hits before any script: ARCHIVE.md says where artifacts
live on S3, the README says what each study directory holds and which paths
may not move.

* retirement writes a ``.superseded`` S3 marker key or renames the local file
  to ``rep_<seed>.SUPERSEDED-<run_ts>.yaml``; readers skip retired runs, then
  earliest-wins over what survives.
* ``regrade.py`` writes a replacement carrying ``regraded_from`` and
  supersedes the run it replaces.
* deduction analysis reads rows straight from S3 via ``rows_source.py``.

Marker spellings below are imported from the store module, not typed here, so
a doc quoting a marker the code no longer writes fails this file.
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


def _store_markers() -> tuple[str, str]:
    """The two supersede spellings, read from the module that writes them."""
    from smolbench.evals.results_store import (
        LOCAL_SUPERSEDED_INFIX,
        S3_SUPERSEDED_SUFFIX,
    )
    return S3_SUPERSEDED_SUFFIX, LOCAL_SUPERSEDED_INFIX


def test_archive_documents_both_supersede_spellings(archive):
    """Both supersede spellings must be named: quoting only one leaves the other looking like corruption."""
    s3_suffix, local_infix = _store_markers()
    assert s3_suffix in archive, f"ARCHIVE.md never names the {s3_suffix} marker key"
    assert local_infix in archive, \
        f"ARCHIVE.md never names the local {local_infix} rename"
    assert "earliest-wins" in archive


def test_both_docs_describe_the_regrade_path(archive, readme):
    """`regraded_from` makes a regraded run traceable to the run it replaced; both docs must mention it."""
    from smolbench.evals.quiz import Marks

    assert "regraded_from" in Marks.__dataclass_fields__, \
        "Marks no longer carries regraded_from; this test's premise is stale"
    for name, text in (("ARCHIVE.md", archive), ("README.md", readme)):
        assert "regrade" in text, f"notebooks/{name} never mentions regrading"
        assert "regraded_from" in text, f"notebooks/{name} never names regraded_from"


def test_the_docs_do_not_send_a_reader_to_sync_the_store(archive, readme):
    """No sync-down instructions: report scripts read S3 directly, so a local-mirror step is wasted bandwidth and a second, divergent path in."""
    for name, text in (("ARCHIVE.md", archive), ("README.md", readme)):
        assert "aws s3 sync" not in text, f"notebooks/{name} still tells a reader to sync"
    assert "--s3" in readme, "notebooks/README.md never mentions the --s3 readers"
    assert "rows_source" in readme, \
        "notebooks/README.md never names the shared row reader"


def test_archive_locates_the_recovery_rows_the_notebook_reads(archive):
    """A reader who cannot find the recovery-run prefix here cannot verify what the notebook and audit script both read."""
    from tests._paths import SCRIPTS

    audit = (SCRIPTS / "results" / "audit_lean_pinning.py").read_text()
    run = re.search(r'RECOVERY_RUN = "([^"]+)"', audit)
    assert run, "audit_lean_pinning no longer declares RECOVERY_RUN"
    assert run.group(1) in archive, \
        f"ARCHIVE.md never locates the {run.group(1)} rows"
    assert "recovered_rows.jsonl" in archive


def test_archive_names_the_prefix_the_readers_actually_default_to(archive):
    """ARCHIVE.md must name the re-collection prefix `rows_source.spool_prefix()` actually defaults to, not the retired pre-cutoff one."""
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


def test_every_file_the_notebooks_readme_names_exists(readme):
    """No path in the README may point at a file the tree does not have (counterpart to the root README's own map check)."""
    named = sorted(set(re.findall(r"[\w./-]*[\w-]+\.(?:py|ipynb|md|yaml|toml)", readme)))
    assert named, "the README names no files at all"
    skip = {"pyproject.toml"}                     # named as a concept, at the root

    def resolves(name: str) -> bool:
        # A placeholder segment (``notebooks/<study>/run_study.py``) truncates
        # the token at the ``>``, leaving a leading "/": resolve what is left
        # by basename rather than reporting a ghost the README never wrote.
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
