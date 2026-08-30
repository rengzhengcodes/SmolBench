"""Guard the deduction study's pinned theorem set, offline.

The pin is underivable from a clean clone (seeded sample over an S3-only sidecar),
and a one-theorem pool change reshuffles all 300 silently, so pin the digest.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re

import pytest

from tests._paths import NOTEBOOKS, SCRIPTS

MANIFEST = NOTEBOOKS / "deduction" / "pinned_theorems.json"

#: The pinned set's identity. Both are load-bearing: the count alone would
#: pass a swap of one theorem for another, and the digest alone would not
#: localize a size change.
EXPECTED_COUNT = 300
EXPECTED_SHA256 = "292194deb832f75ae2f4008a7d597e4d6ac765ff9c0c4e4a31b7eeab377e5b36"

#: Corpus provenance. Pinned so a corpus swap cannot happen silently -- the
#: recency finding (notebooks/deduction/README.md, "Corpus date vs. model
#: cutoffs") is stated ENTIRELY in terms of this commit's trace date, so a
#: different corpus invalidates that section.
EXPECTED_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"
EXPECTED_CREATION_TIME = "2024-03-24 23:38:32.469290"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_pinned_manifest_identity(manifest):
    """Membership digest, corpus provenance, and the recorded draw recipe."""
    names = manifest["full_names"]
    assert manifest["count"] == EXPECTED_COUNT == len(names)
    assert len(set(names)) == EXPECTED_COUNT, "pinned set contains duplicates"
    assert names == sorted(names), "full_names must be stored sorted"
    digest = hashlib.sha256("\n".join(names).encode()).hexdigest()
    assert digest == EXPECTED_SHA256 == manifest["sha256_of_sorted_full_names"]

    corpus = manifest["corpus"]
    assert corpus["from_repo"]["commit"] == EXPECTED_COMMIT
    assert corpus["creation_time"] == EXPECTED_CREATION_TIME
    assert corpus["from_repo"]["url"].endswith("leanprover-community/mathlib4")

    d = manifest["derivation"]
    assert (d["source"], d["kind"], d["split"]) == ("replay_passing", "novel_premises", "val")
    assert (d["limit"], d["seed"], d["pool_size"]) == (300, 0, 805)


def test_slug_theorem_maps_pinned_names_injectively():
    """The lossy on-disk slug must not collide two distinct pinned theorems."""
    spec = importlib.util.spec_from_file_location(
        "_audit", SCRIPTS / "results" / "audit_lean_pinning.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)

    from smolbench.deduction.lean import runner

    names = json.loads(MANIFEST.read_text())["full_names"]
    assert len({audit.slug_theorem(n) for n in names}) == len(names)
    assert all(audit.slug_theorem(n) == runner.slug_theorem(n) for n in names)
    assert any(re.search(r"[?']", n) for n in names)


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location(
        "_audit", SCRIPTS / "results" / "audit_lean_pinning.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_layer4_counts_a_missing_prompt_artifact_as_divergent(audit):
    """A cell no lane spooled a prompt for must not certify as byte-identical."""
    lanes = audit.LANES
    shared = {lane: {"thm|stepk-1": "etag-a", "thm|hint-2": "etag-b"} for lane in lanes}
    assert audit.divergent_prompt_cells({"thm|stepk-1", "thm|hint-2"}, shared) == set()
    assert audit.divergent_prompt_cells({"thm|absent"}, shared) == {"thm|absent"}
    one_missing = {**shared, lanes[0]: {"thm|hint-2": "etag-b"}}
    assert audit.divergent_prompt_cells({"thm|stepk-1"}, one_missing) == {"thm|stepk-1"}
    differing = {**shared, lanes[1]: {**shared[lanes[1]], "thm|stepk-1": "etag-z"}}
    assert audit.divergent_prompt_cells({"thm|stepk-1"}, differing) == {"thm|stepk-1"}


def test_fetch_recovery_tolerates_absence_but_propagates_real_errors(audit):
    """Only "no such key" becomes an empty lane; AccessDenied must surface."""
    class _Err(Exception):
        def __init__(self, response):
            self.response = response

    class _S3:
        def __init__(self, response):
            self.response = response

        def get_object(self, **kwargs):
            raise _Err(self.response)

    missing = {"Error": {"Code": "NoSuchKey"}, "ResponseMetadata": {"HTTPStatusCode": 404}}
    assert audit.fetch_recovery(_S3(missing)) == {lane: set() for lane in audit.LANES}
    denied = {"Error": {"Code": "AccessDenied"}, "ResponseMetadata": {"HTTPStatusCode": 403}}
    with pytest.raises(_Err):
        audit.fetch_recovery(_S3(denied))
