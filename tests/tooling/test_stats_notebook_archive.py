"""Section 0's shared archive reader, exercised without touching AWS."""

from __future__ import annotations

import json

import pytest

from tests.tooling._notebook_cells import STATS_NB, cell_source, load_notebook


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


def test_archive_cell_builds_on_the_shared_aws_primitives(
        nb: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """``S3Archive`` must call `_aws.fresh_client` and `results_store.parse_s3_uri`, not private re-implementations that sign with stale credentials or drift from the writer's key layout."""
    from smolbench.evals import _aws
    from smolbench.evals.results_store import parse_s3_uri

    src = cell_source(nb, "from smolbench.evals.s3_archive import S3Archive")
    calls: list[tuple] = []
    # Stubbed on the module `_aws`, where the cell resolves the client: a stub
    # bound to a local name here is never reached by the exec'd cell.
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


def test_archive_exposes_the_live_read_surface() -> None:
    """The shared reader retains every notebook method that has a live caller."""
    from smolbench.evals.s3_archive import S3Archive

    for method in ("open", "read", "text", "json", "size", "sha256"):
        assert callable(getattr(S3Archive, method)), f"S3Archive lost {method}()"
