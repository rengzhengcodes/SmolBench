"""Offline contract for snapshot_analysis_data; no AWS.

``MANIFEST.json`` has no hand-written dataset notes; reading rules live in a
dated provenance document copied beside the data.
"""

import json
import sys
from collections.abc import Callable
from typing import Any

import pytest

from scripts.results import snapshot_analysis_data as snap
from tests._paths import REPO_ROOT


class FakeS3:
    """Record calls and serve listings."""

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
        # A copy still verifies after its skip check, so the second lookup succeeds.
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
        monkeypatch.setenv("LEAN_SPOOL_PREFIX", "dp")
        monkeypatch.setattr(sys, "argv", [
            "snapshot_analysis_data.py", "--dest", "analysis/t", *argv])
        assert snap.main() == 0
        manifest = json.loads(
            [body for _b, key, body in fake.puts if key.endswith("MANIFEST.json")][0])
        return fake, manifest

    return _run


def test_manifest_carries_only_computed_fields(
    run_snapshot: Callable[..., tuple[FakeS3, dict[str, Any]]],
) -> None:
    """Build the provenance pointer from written files."""
    fake, manifest = run_snapshot()
    assert set(manifest) == {
        "snapshot_prefix", "source_bucket", "total_objects", "total_bytes",
        "copied", "skipped_already_present", "provenance_docs", "per_model",
        "provenance_keys",
    }
    # Compute totals from this run, not constants.
    assert manifest["total_objects"] == 2 and manifest["total_bytes"] == 30
    assert manifest["copied"] == 2
    # Mirror writes so missing docs are not claimed present; duplicate README
    # basenames can collide to one key, so accept either result.
    put_provenance = [key for _b, key, _body in fake.puts if "/provenance/" in key]
    assert manifest["provenance_keys"] == put_provenance
    assert manifest["provenance_docs"] == len(put_provenance)
    assert "analysis/t/provenance/SNAPSHOT_NOTES.md" in put_provenance


def test_the_reading_rules_ship_as_a_dated_document() -> None:
    """Keep dated, reviewable counts in git."""
    doc = REPO_ROOT / "notebooks" / "deduction" / "analysis" / "SNAPSHOT_NOTES.md"
    assert "notebooks/deduction/analysis/SNAPSHOT_NOTES.md" in snap.PROVENANCE_DOCS
    text = doc.read_text()
    for literal in ("74", "232", "151", "81", "712", "944", "5.9", "24.6", "68/30/50"):
        assert literal in text, literal
    assert "2026-08-16" in text  # These counts describe one dated dataset.


def test_the_bucket_follows_smolbench_results_s3(
    run_snapshot: Callable[..., tuple[FakeS3, dict[str, Any]]],
) -> None:
    """Follow redirected results stores so this script is not silently skipped."""
    fake, manifest = run_snapshot(bucket_env="s3://redirected-bucket/base")
    assert manifest["source_bucket"] == "redirected-bucket"
    assert {b for b, _p in fake.listed} == {"redirected-bucket"}
    assert {b for b, _k, _body in fake.puts} == {"redirected-bucket"}
    assert {c["Bucket"] for c in fake.copies} == {"redirected-bucket"}
    assert {c["CopySource"]["Bucket"] for c in fake.copies} == {"redirected-bucket"}
    # The documented fallback applies when the environment is unset.
    _fake2, manifest2 = run_snapshot()
    assert manifest2["source_bucket"] == "smolbench-results-414266451290"
