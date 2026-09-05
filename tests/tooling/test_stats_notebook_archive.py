"""Section 0's archive reader, exercised without touching AWS.

``S3Archive`` is copied into the notebook rather than imported (``tests/`` is
not an importable package), so nothing else in the suite pins it. What it must
NOT be is a private re-implementation of primitives ``smolbench`` already
exports: the client and the URI parser are shared, and these tests are what
keeps them shared.

See ``tests/tooling/_notebook_cells.py`` for the cell-extraction machinery.
"""

from __future__ import annotations

import json

import pytest

from tests.tooling._notebook_cells import STATS_NB, cell_source, load_notebook


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


_cell_source = cell_source


def test_archive_cell_builds_on_the_shared_aws_primitives(nb, monkeypatch):
    """``S3Archive`` must use ``_aws.fresh_client`` and ``results_store.parse_s3_uri``.

    ``boto3.client`` goes through the process-wide default session, which
    resolves credentials ONCE; ``_aws.fresh_client``'s docstring names
    "notebook kernels driving multi-hour evals" as the exact process it exists
    for, so a cached session here keeps signing every archive read with
    credentials that expired hours ago. A privately re-declared
    ``parse_s3_uri`` is a second implementation of the key layout the results
    store writes, free to drift from the writer's.

    The stub is installed on the module attribute, so this passes only if the
    cell calls ``_aws.fresh_client`` rather than binding the function at import
    time -- which is also what makes the call swappable at all.
    """
    from smolbench.evals import _aws
    from smolbench.evals.results_store import parse_s3_uri

    src = _cell_source(nb, "class S3Archive")
    calls: list[tuple] = []
    monkeypatch.setattr(
        _aws, "fresh_client",
        lambda service, region=None: calls.append((service, region)) or object())

    namespace = {"json": json}          # cell 2 binds ``json`` for ``.json()``
    exec(compile(src, str(STATS_NB), "exec"), namespace)

    assert calls == [("s3", "us-west-2")], calls
    archive = namespace["archive"]
    assert (archive.bucket, archive.prefix) == parse_s3_uri(namespace["ARCHIVE"])
    # Pin the resolved key too: swapping the parser must not move the prefix.
    assert (archive.bucket, archive.prefix) == (
        "smolbench-results-414266451290", "archives/2026-08-25")
    assert "def parse_s3_uri" not in src, "notebook still re-declares the parser"
    assert "boto3" not in src, "notebook still builds a default-session client"


def test_archive_cell_carries_no_unused_aws_surface(nb):
    """``keys()``/``exists()`` are never called; a lister that nothing calls is dead.

    They also widen what this notebook can do to the archive beyond the ruling
    it states one line above -- read the bytes, write nothing.
    """
    src = _cell_source(nb, "class S3Archive")
    assert "def keys(" not in src
    assert "def exists(" not in src
    for method in ("open", "read", "text", "json", "size", "sha256"):
        assert f"def {method}(" in src, f"S3Archive lost {method}()"


def test_archive_prose_does_not_promise_removed_methods(nb):
    """Two cells describe this class; both named ``keys`` in its logic summary."""
    for cell in nb["cells"]:
        text = "".join(cell["source"])
        if "S3Archive" in text:
            assert "read/keys/sha256" not in text, text[:200]
