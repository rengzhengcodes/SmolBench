"""Offline contract for scripts/results/snapshot_analysis_data.py; no AWS.

``MANIFEST.json`` no longer carries hand-written per-dataset notes; the
reading rules live in a dated, version-controlled provenance doc copied
next to the data instead.
"""

import json
import sys
from collections.abc import Callable
from typing import Any

import pytest

from scripts.results import snapshot_analysis_data as snap
from tests._paths import REPO_ROOT

#: The dataset-specific figures that must no longer be emitted from Python.
DATASET_LITERALS = ("74 cells", "232", "712", "68/30/50", "5.9", "24.6")


class FakeS3:
    """Records every call; serves one tiny listing per prefix."""

    def __init__(self, listings: dict[str, list[dict[str, Any]]]) -> None:
        self.listings = listings
        self.puts: list = []
        self.copies: list = []
        self.listed: list = []

    # -- paginator ------------------------------------------------------
    def get_paginator(self, name: str) -> "FakeS3":
        assert name == "list_objects_v2"
        return self

    def paginate(self, Bucket: str, Prefix: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.listed.append((Bucket, Prefix))
        return [{"Contents": self.listings.get(Prefix, [])}]

    # -- object ops -----------------------------------------------------
    def head_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        raise RuntimeError("absent")  # nothing is already present at the destination

    def copy_object(self, **kwargs: Any) -> None:
        self.copies.append(kwargs)

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:
        self.puts.append((Bucket, Key, Body))


@pytest.fixture
def run_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., tuple[FakeS3, dict[str, Any]]]:
    """Drive `main` against a fake S3 and return (fake, manifest)."""

    def _run(*argv: str, bucket_env: str | None = None) -> tuple[FakeS3, dict[str, Any]]:
        if bucket_env is None:
            monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
        else:
            monkeypatch.setenv("SMOLBENCH_RESULTS_S3", bucket_env)
        fake = FakeS3({
            "induction/": [{"Key": "induction/glm-4.7/seed=0/intens--x.yaml", "Size": 10}],
            "dp/": [{"Key": "dp/scaling_glm-4.7/all_rows.jsonl", "Size": 20}],
        })
        # head_object is only consulted for the skip check; a copy must still
        # verify, so serve the expected size on the second lookup.
        sizes = {"analysis/t/induction/glm-4.7/seed=0/intens--x.yaml": 10,
                 "analysis/t/deduction/glm-4.7/all_rows.jsonl": 20}
        seen: set = set()

        def head_object(Bucket: str, Key: str) -> dict[str, int]:
            if Key in seen:
                return {"ContentLength": sizes[Key]}
            seen.add(Key)
            raise RuntimeError("absent")

        fake.head_object = head_object
        monkeypatch.setattr(snap, "_s3", lambda: fake)
        monkeypatch.setattr(sys, "argv", [
            "snapshot_analysis_data.py", "--dest", "analysis/t",
            "--spool-prefix", "dp", *argv])
        assert snap.main() == 0
        manifest = json.loads(
            [body for _b, key, body in fake.puts if key.endswith("MANIFEST.json")][0])
        return fake, manifest

    return _run


def test_manifest_carries_only_computed_fields(
    run_snapshot: Callable[..., tuple[FakeS3, dict[str, Any]]],
) -> None:
    """No prose notes; the provenance pointer is built from what was written."""
    fake, manifest = run_snapshot()
    assert "notes" not in manifest
    assert set(manifest) == {
        "snapshot_prefix", "source_bucket", "total_objects", "total_bytes",
        "copied", "skipped_already_present", "provenance_docs", "per_model",
        "provenance_keys",
    }
    # Computed from this run's walk, not from constants.
    assert manifest["total_objects"] == 2 and manifest["total_bytes"] == 30
    assert manifest["copied"] == 2
    # provenance_keys mirrors the actual put_object calls, so a missing doc
    # shows up instead of being claimed present. notebooks/README.md and
    # notebooks/deduction/README.md share a basename and collide to one key;
    # this assertion holds either way.
    put_provenance = [key for _b, key, _body in fake.puts if "/provenance/" in key]
    assert manifest["provenance_keys"] == put_provenance
    assert manifest["provenance_docs"] == len(put_provenance)
    assert "analysis/t/provenance/SNAPSHOT_NOTES.md" in put_provenance


def test_the_reading_rules_ship_as_a_dated_document() -> None:
    """The counts moved into git, where they can be dated and reviewed."""
    doc = REPO_ROOT / "notebooks" / "deduction" / "analysis" / "SNAPSHOT_NOTES.md"
    assert "notebooks/deduction/analysis/SNAPSHOT_NOTES.md" in snap.PROVENANCE_DOCS
    text = doc.read_text()
    for literal in ("74", "232", "151", "81", "712", "944", "5.9", "24.6", "68/30/50"):
        assert literal in text, literal
    assert "2026-08-16" in text  # dated: these counts describe ONE dataset
    # ...and none of them is emitted from Python any more.
    source = (REPO_ROOT / "scripts" / "results" / "snapshot_analysis_data.py").read_text()
    for literal in DATASET_LITERALS:
        assert literal not in source, literal


def test_the_bucket_follows_smolbench_results_s3(
    run_snapshot: Callable[..., tuple[FakeS3, dict[str, Any]]],
) -> None:
    """A redirected results store must not silently miss this script."""
    fake, manifest = run_snapshot(bucket_env="s3://redirected-bucket/base")
    assert manifest["source_bucket"] == "redirected-bucket"
    assert {b for b, _p in fake.listed} == {"redirected-bucket"}
    assert {b for b, _k, _body in fake.puts} == {"redirected-bucket"}
    assert {c["Bucket"] for c in fake.copies} == {"redirected-bucket"}
    assert {c["CopySource"]["Bucket"] for c in fake.copies} == {"redirected-bucket"}
    # Default (env unset) is the documented fallback literal.
    _fake2, manifest2 = run_snapshot()
    assert manifest2["source_bucket"] == "smolbench-results-414266451290"
