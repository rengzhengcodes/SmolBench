"""``notebooks/README.md`` and ``notebooks/ARCHIVE.md``, pinned against the code.

These two files are the entry points a reader hits before any script: ARCHIVE.md
says where the artifacts live and how they are addressed on S3, and the
notebooks README says what each study directory holds and which paths may not
move. Both were written when a run was retired by hand, when a regrade REFUSED,
and when reading the deduction rows meant syncing a snapshot to local disk --
none of which is true now:

* retirement is a store operation with two spellings, one per backend
  (``smolbench.evals.results_store``: a sibling ``.superseded`` marker key on
  S3, a ``rep_<seed>.SUPERSEDED-<run_ts>.yaml`` rename locally), and readers
  skip retired runs and then apply earliest-wins over what survives;
* ``scripts/results/regrade.py`` writes a replacement carrying
  ``regraded_from`` and supersedes the run it replaces;
* the deduction analysis scripts read their rows straight out of S3
  (``--s3``, through ``notebooks/deduction/analysis/rows_source.py``).

The marker spellings are read FROM the store module rather than typed here, so
this cannot pass while the docs quote a marker the code does not write. The
notebooks README additionally described a tree that did not exist yet
("this commit is slice 2 ... several paths below don't exist yet"); at this head
it does, so the forward references have to be gone and every path named has to
resolve.
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
    """A reader of the bucket meets ``.superseded`` keys; the map must name them.

    Both backends, because both appear in the artifacts this file indexes: the
    S3 log carries marker keys and the local replicate trees carry renamed
    files. Quoting only one leaves the other looking like corruption.
    """
    s3_suffix, local_infix = _store_markers()
    assert s3_suffix in archive, f"ARCHIVE.md never names the {s3_suffix} marker key"
    assert local_infix in archive, \
        f"ARCHIVE.md never names the local {local_infix} rename"
    # and says what a reader does with them
    assert "earliest-wins" in archive


def test_both_docs_describe_the_regrade_path(archive, readme):
    """Regrading goes THROUGH the store now; the refusal is gone.

    ``regraded_from`` is the field that makes a regraded run traceable to the
    run it replaced, so it is the thing a reader of the archive needs to know
    exists -- a replacement without it is indistinguishable from a re-run.
    """
    from smolbench.evals.quiz import Marks

    assert "regraded_from" in Marks.__dataclass_fields__, \
        "Marks no longer carries regraded_from; this test's premise is stale"
    for name, text in (("ARCHIVE.md", archive), ("README.md", readme)):
        assert "regrade" in text, f"notebooks/{name} never mentions regrading"
        assert "regraded_from" in text, f"notebooks/{name} never names regraded_from"


def test_the_docs_do_not_send_a_reader_to_sync_the_store(archive, readme):
    """No sync-down instructions: the report scripts read S3 themselves.

    ``rows_source.resolve_rows_dir`` fetches what a report needs into scratch,
    so prose telling a reader to mirror a prefix locally first is both wasted
    bandwidth and a second, divergent way in.
    """
    for name, text in (("ARCHIVE.md", archive), ("README.md", readme)):
        assert "aws s3 sync" not in text, f"notebooks/{name} still tells a reader to sync"
    assert "--s3" in readme, "notebooks/README.md never mentions the --s3 readers"
    assert "rows_source" in readme, \
        "notebooks/README.md never names the shared row reader"


def test_archive_locates_the_recovery_rows_the_notebook_reads(archive):
    """The sensitivity arm's inputs are archived artifacts; this file locates them.

    ``statistical_analyses.ipynb`` section 5 now fetches
    ``<spool>/dojoinit_recovery_2026-08-18/<lane>/recovered_rows.jsonl`` for its
    post-recovery pool, and ``scripts/results/audit_lean_pinning.py`` reads the
    same tree. A reader who cannot find that prefix here cannot check either.
    """
    from tests._paths import SCRIPTS

    audit = (SCRIPTS / "results" / "audit_lean_pinning.py").read_text()
    run = re.search(r'RECOVERY_RUN = "([^"]+)"', audit)
    assert run, "audit_lean_pinning no longer declares RECOVERY_RUN"
    assert run.group(1) in archive, \
        f"ARCHIVE.md never locates the {run.group(1)} rows"
    assert "recovered_rows.jsonl" in archive


def test_archive_names_the_prefix_the_readers_actually_default_to(archive):
    """The deduction spool row must be the re-collection's prefix, not the retired one.

    ``rows_source.spool_prefix()`` defaults to the re-collection and RAISES for
    the published pre-cutoff prefix unless ``LEAN_ALLOW_LEGACY_PREFIX=1``, so a
    table that lists only the pre-cutoff prefix sends a reader to the one
    location every reader in the tree refuses by default.
    """
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
    assert "LEAN_ALLOW_LEGACY_PREFIX" in archive, (
        "ARCHIVE.md lists the pre-cutoff prefix without the override that a "
        "reader needs to read it")


#: Forward references written when this branch was the induction-only slice.
#: Every path they hedge exists at this head, so the hedges are now misleading.
STALE_SLICE_MARKERS = (
    "This commit is slice 2",
    "don't exist yet",
    "Lands in later slices",
    "(slice 3)",
    "(slice 4)",
    "(slice 5)",
    "once it lands",
)


def test_notebooks_readme_has_no_stale_slice_forward_references(readme):
    """The README must describe the tree it ships with, not a future one."""
    offenders = [marker for marker in STALE_SLICE_MARKERS if marker in readme]
    assert not offenders, f"notebooks/README.md still hedges: {offenders}"


def test_every_file_the_notebooks_readme_names_exists(readme):
    """No path in the README may point at a file the tree does not have.

    The counterpart to the root README's own map check: this file names the
    drivers, the analysis modules and the tests that pin their path
    conventions, and a reader follows those names literally.
    """
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
