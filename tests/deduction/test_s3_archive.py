"""S3 archive gates; stream objects rather than pulling them to disk, and skip offline::

    SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/2026-08-25 \\
        .venv/bin/python -m pytest tests/deduction/test_s3_archive.py -q
"""

from __future__ import annotations

import hashlib
import io
import json
import posixpath
import sys
import tarfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests._paths import SCRIPTS, load_by_path

RESULTS = "notebooks/deduction/results"


@pytest.fixture(scope="module")
def em() -> Iterator[Any]:
    """Load scripts/results/evidence_manifest.py by path."""
    name = "evidence_manifest_s3"
    module = load_by_path(SCRIPTS / "results" / "evidence_manifest.py", name)
    try:
        yield module
    finally:
        sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def tracked(s3_archive: Any) -> set[str]:
    """Every archive-relative path under the results tree; guards against a vacuous pass."""
    out = set(s3_archive.keys(RESULTS))
    assert len(out) >= 30, sorted(out)
    return out


def _sha256_of_reference(archive: Any, manifest_dir: str, relpath: str, em: Any) -> str:
    """sha256 of a manifest reference, streamed from S3 (tarball members via BytesIO)."""
    path, member = em._split_reference(relpath)
    rel = posixpath.normpath(posixpath.join(manifest_dir, path))
    if member is None:
        return archive.sha256(rel)
    with tarfile.open(fileobj=io.BytesIO(archive.read(rel)), mode="r:*") as tf:
        stream = tf.extractfile(member)
        if stream is None:
            raise FileNotFoundError(f"{rel}!{member}")
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
        return h.hexdigest()


def _verify_on_s3(archive: Any, manifest_dir: str, em: Any) -> list[str]:
    """Port of ``em.verify`` over S3 objects; returns the failure list."""
    data = json.loads(archive.text(f"{manifest_dir}/{em.MANIFEST_NAME}"))
    failures: list[str] = []
    raw_entries = data.get("entries")
    assert isinstance(raw_entries, list) and raw_entries, manifest_dir
    valid = [
        e for i, e in enumerate(raw_entries) if em._check_entry_schema(i, e, failures)
    ]
    allowlist = em._check_allowlist_schema(data.get("allowlist", []), failures)
    candidates = [c for e in valid for c in em._candidates(e["relpath"])]
    allowed = {a["name"] for a in allowlist}
    for entry in valid:
        relpath = entry["relpath"]
        try:
            actual = _sha256_of_reference(archive, manifest_dir, relpath, em)
        except (FileNotFoundError, KeyError, tarfile.TarError) as exc:
            failures.append(f"{relpath}: unresolvable on S3: {exc}")
            continue
        if actual != entry["sha256"]:
            failures.append(
                f"{relpath}: sha256 mismatch: manifest={entry['sha256']} actual={actual}"
            )
        if entry["role"] != "writeup":
            continue
        path, member = em._split_reference(relpath)
        rel = posixpath.normpath(posixpath.join(manifest_dir, path))
        if member is None:
            text = archive.text(rel)
        else:
            with tarfile.open(fileobj=io.BytesIO(archive.read(rel)), mode="r:*") as tf:
                text = tf.extractfile(member).read().decode("utf-8", errors="replace")
        for name in em.cited_artifacts(text):
            if name in allowed or any(em.covers(name, c) for c in candidates):
                continue
            failures.append(f"{relpath}: cited artifact not covered: {name}")
    return failures


def test_every_tracked_writeup_has_a_verified_manifest(
    tracked: set[str],
    s3_archive: Any,
    em: Any,
) -> None:
    """Every .md/.txt under results/ sits in a manifested dir and is listed."""
    writeups = sorted(
        p
        for p in tracked
        if Path(p).suffix in em.WRITEUP_SUFFIXES and Path(p).name != em.MANIFEST_NAME
    )
    assert len(writeups) >= 4, writeups
    for rel in writeups:
        d = posixpath.dirname(rel)
        mf = f"{d}/{em.MANIFEST_NAME}"
        assert mf in tracked, f"{rel}: no {em.MANIFEST_NAME} in {d}"
        manifest = json.loads(s3_archive.text(mf))
        listed = [
            e
            for e in manifest["entries"]
            if not e["relpath"].startswith("tarball:")
            and posixpath.normpath(posixpath.join(d, e["relpath"])) == rel
        ]
        assert listed, f"{rel}: not listed in {mf}"
        if rel.endswith(".md"):
            assert (
                listed[0]["role"] == "writeup"
            ), f"{rel}: listed as {listed[0]['role']!r}, must be 'writeup' to be scanned"


def test_every_tracked_manifest_verifies(
    tracked: set[str],
    s3_archive: Any,
    em: Any,
) -> None:
    """Every EVIDENCE.json in the archive verifies against its objects."""
    manifests = sorted(p for p in tracked if Path(p).name == em.MANIFEST_NAME)
    assert manifests, "no EVIDENCE.json in the archive"
    for mf in manifests:
        failures = _verify_on_s3(s3_archive, posixpath.dirname(mf), em)
        assert not failures, f"{mf}:\n  " + "\n  ".join(failures)
