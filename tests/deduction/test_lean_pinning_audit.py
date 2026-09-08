"""Exercise pinned-theorem manifest emission offline."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from types import ModuleType
from collections.abc import Iterator
from typing import Any

import pytest

from tests._paths import (
    LEAN_MINI_POSTCUTOFF as POSTCUTOFF,
    REPO_ROOT,
    SCRIPTS,
    load_by_path,
)

#: The post-cutoff fixture's own provenance, for the freshly-emitted manifest.
FIXTURE_COMMIT = "2ca39e62989124794bd8405bb2e60805f63d37bc"
FIXTURE_CREATION_TIME = "2026-08-30 15:43:26.000000"
FIXTURE_NAMES = ("Mini.theoremA", "Mini.theoremB")


@pytest.fixture(scope="module")
def emitted(tmp_path_factory: pytest.TempPathFactory, audit: ModuleType) -> dict[str, Any]:
    """A manifest freshly emitted by `--emit-manifest`, offline, from the fixture.

    Makes fixture provenance checkable without the full dataset or any AWS call.
    """
    tmp = tmp_path_factory.mktemp("emit")
    sidecar = tmp / "replay_passing_random_val.jsonl"
    sidecar.write_text("".join(
        json.dumps({"full_name": n, "verdict": "success"}) + "\n" for n in FIXTURE_NAMES))
    out = tmp / "reproduced_pin.json"
    assert audit.main([
        "--offline", "--emit-manifest", str(out),
        "--val-json", str(POSTCUTOFF / "random" / "val.json"),
        "--replay-jsonl", str(sidecar),
        "--metadata", str(POSTCUTOFF / "metadata.json"),
        "--limit", "2", "--seed", "0"]) == 0
    return json.loads(out.read_text())


def test_emitted_manifest_identity(emitted: dict[str, Any]) -> None:
    """The fixture manifest records its membership, provenance, and recipe."""
    manifest = emitted
    names = manifest["full_names"]
    assert manifest["count"] == len(names) == 2
    assert len(set(names)) == 2, "pinned set contains duplicates"
    assert names == sorted(names), "full_names must be stored sorted"

    corpus = manifest["corpus"]
    assert corpus["from_repo"]["commit"] == FIXTURE_COMMIT
    assert corpus["creation_time"] == FIXTURE_CREATION_TIME
    assert corpus["from_repo"]["url"].endswith("leanprover-community/mathlib4")
    assert corpus["postcutoff"]["target_date"] == "2026-07-31"
    assert corpus["postcutoff"]["new_commit"] == FIXTURE_COMMIT

    d = manifest["derivation"]
    assert (d["source"], d["kind"], d["split"]) == ("replay_passing", "random", "val")
    assert (d["limit"], d["seed"], d["pool_size"]) == (2, 0, 2)


@pytest.fixture(scope="module")
def audit() -> Iterator[ModuleType]:
    name = "_audit"
    module = load_by_path(SCRIPTS / "results" / "audit_lean_pinning.py", name)
    try:
        yield module
    finally:
        sys.modules.pop(name, None)


def test_layer4_counts_a_missing_prompt_artifact_as_divergent(audit: ModuleType) -> None:
    """A cell no lane spooled a prompt for must not certify as byte-identical."""
    lanes = audit.LANES
    shared = {lane: {"thm|stepk-1": "etag-a", "thm|hint-2": "etag-b"} for lane in lanes}
    assert audit.divergent_prompt_cells({"thm|stepk-1", "thm|hint-2"}, shared) == set()
    assert audit.divergent_prompt_cells({"thm|absent"}, shared) == {"thm|absent"}
    one_missing = {**shared, lanes[0]: {"thm|hint-2": "etag-b"}}
    assert audit.divergent_prompt_cells({"thm|stepk-1"}, one_missing) == {"thm|stepk-1"}
    differing = {**shared, lanes[1]: {**shared[lanes[1]], "thm|stepk-1": "etag-z"}}
    assert audit.divergent_prompt_cells({"thm|stepk-1"}, differing) == {"thm|stepk-1"}


@pytest.mark.parametrize("path,flag,argv", [
    ("results/audit_lean_pinning.py", "--expect-theorems",
     ["--val-json", "x", "--replay-jsonl", "x"]),
    ("results/audit_lean_pinning.py", "--expect-cells",
     ["--val-json", "x", "--replay-jsonl", "x"]),
    ("deduction/merge_lean_shards.py", "--expect-cells", ["k", "--n", "1"]),
    ("deduction/merge_lean_shards.py", "--expect-sanity", ["k", "--n", "1"]),
])
def test_every_consumer_requires_an_explicit_expected_shape(
    path: str, flag: str, argv: list[str],
) -> None:
    """No consumer may carry (or inherit) a default pinned shape: state it or fail.

    Checked through the CLI rather than by importing, so an import-time-fatal
    script on a box where these run also surfaces here.
    """
    script = SCRIPTS / path
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    proc = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True,
        text=True, cwd=str(REPO_ROOT), timeout=300, env=env)
    assert proc.returncode == 0, proc.stderr
    assert flag in proc.stdout, f"{path} lacks {flag}\n{proc.stdout}"
    bare = subprocess.run(
        [sys.executable, str(script), *argv], capture_output=True,
        text=True, cwd=str(REPO_ROOT), timeout=300, env=env)
    assert bare.returncode == 2 and flag in bare.stderr, (
        f"{path} {flag} is not required\n{bare.stderr}")
