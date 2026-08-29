"""Guard the deduction study's pinned theorem set, offline.

The 21-lane deduction study compares model checkpoints against each other,
so every cross-model claim it makes assumes the lanes are PAIRED: that each
model was asked the same questions. ``scripts/results/audit_lean_pinning.py``
verifies that against the S3 spool at five levels, down to byte-identical
prompts; ``notebooks/deduction/README.md`` ("The pinned 300") states the
contract.

That audit is a live-AWS check and cannot run here. What this file guards
is the artifact it checks against: ``notebooks/deduction/pinned_theorems.json``,
the committed record of WHICH 300 theorems the study ran. The record exists
because the pin is otherwise underivable from a clean clone -- it is a
seeded sample over the 805-theorem ``replay_passing`` sidecar, and the
2026-08-25 archive moved both that sidecar and the ~700 MB LeanDojo corpus
to S3. Neither is in git.

The pin is also fragile in a way that would be silent, which is the real
reason to pin the digest here rather than trust the recipe. The
``replay_passing`` pool is produced by LIVE Dojo replay, and Dojo init is
known to fail nondeterministically in this study -- that is what
``dojoinit_recovery_2026-08-18`` exists to repair. Regenerating the sidecar
can therefore shift the 805-theorem pool, and because ``random.Random(0).sample``
is sensitive to both the order and the membership of its population, a
ONE-theorem change to the pool reshuffles the entire 300. Nothing
downstream would notice. A digest here turns that into a failing test.

These tests assert on CONTENT, not counts, per the standing rule that a
completeness check which counts rows is not a completeness check (see
``scripts/results/audit_run_completeness.py``'s preamble for the incident that
established it).
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
#: recency finding in the audit doc is stated ENTIRELY in terms of this
#: commit's trace date, so a different corpus invalidates that document.
EXPECTED_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"
EXPECTED_CREATION_TIME = "2024-03-24 23:38:32.469290"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_pinned_manifest_digest_and_count(manifest):
    """The 300 names must hash to the audited digest.

    This is the test that fails if a sidecar regeneration reshuffles the
    seeded sample. `full_names` is stored sorted, so the digest is stable
    against ordering churn and sensitive only to membership.
    """
    names = manifest["full_names"]
    assert manifest["count"] == EXPECTED_COUNT == len(names)
    assert len(set(names)) == EXPECTED_COUNT, "pinned set contains duplicates"
    assert names == sorted(names), "full_names must be stored sorted"
    digest = hashlib.sha256("\n".join(names).encode()).hexdigest()
    assert digest == EXPECTED_SHA256 == manifest["sha256_of_sorted_full_names"]


def test_pinned_manifest_records_corpus_provenance(manifest):
    """The corpus the pin was drawn from must be recorded and unchanged.

    The audit's cutoff finding (0/300 theorems postdate any model's
    knowledge cutoff) rests on this commit being a 2024-03-24 snapshot. If
    the corpus is ever swapped, that finding must be re-derived rather
    than inherited.
    """
    corpus = manifest["corpus"]
    assert corpus["from_repo"]["commit"] == EXPECTED_COMMIT
    assert corpus["creation_time"] == EXPECTED_CREATION_TIME
    assert corpus["from_repo"]["url"].endswith("leanprover-community/mathlib4")


def test_pinned_manifest_records_the_derivation(manifest):
    """The recipe must stay consistent with the study config it describes.

    ``notebooks/deduction/run_study.py``'s ``build_config`` is separately
    pinned by ``tests/deduction/test_deduction_study.py``. This asserts the manifest
    documents the SAME draw, so the two cannot drift apart unnoticed.
    """
    d = manifest["derivation"]
    assert (d["source"], d["kind"], d["split"]) == ("replay_passing", "novel_premises", "val")
    assert (d["limit"], d["seed"], d["pool_size"]) == (300, 0, 805)


def test_slug_theorem_maps_the_pinned_names_injectively():
    """The on-disk slug must not collide two distinct pinned theorems.

    ``runner.slug_theorem`` is LOSSY -- it maps both ``'`` and ``?`` to
    ``_``, so ``List.get?_set_eq`` and a hypothetical ``List.get'_set_eq``
    would share a directory and silently overwrite each other's cells. It
    happens to collide nothing in this pinned set. That is a property of
    these 300 names, not a guarantee of the slug, so it is asserted rather
    than assumed -- and it is what licenses the audit script comparing
    slugged recovery ``theorem_id``s against directory names.
    """
    spec = importlib.util.spec_from_file_location(
        "_audit", SCRIPTS / "results" / "audit_lean_pinning.py"
    )
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)

    names = json.loads(MANIFEST.read_text())["full_names"]
    slugs = [audit.slug_theorem(n) for n in names]
    assert len(set(slugs)) == len(names), "slug collision among pinned theorems"

    # The audit script duplicates the slug rather than importing it (so a
    # bug in the module under audit is not inherited by its auditor). Pin
    # the two together here instead.
    from smolbench.deduction.lean import runner

    assert all(audit.slug_theorem(n) == runner.slug_theorem(n) for n in names)
    # And confirm the lossy pair really is exercised by this set, so the
    # collision check above is not vacuous.
    assert any(re.search(r"[?']", n) for n in names)
