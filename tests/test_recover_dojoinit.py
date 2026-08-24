"""Test scripts/recover_dojoinit_std.py. No network, no lean_dojo.

The tool's load-bearing property is the ADDITIVE CONTRACT. It must be
unable to write anywhere in the results bucket except its own recovery
prefix, and its gates must fail on content, not counts. These tests
pin exactly that.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def rec():
    spec = importlib.util.spec_from_file_location(
        "recover_dojoinit_std", REPO / "scripts" / "recover_dojoinit_std.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_imports_without_lean_dojo(rec):
    """The module must import in the plain venv: lean_dojo is lazy-loaded."""
    assert rec.RECOVERY_S3_PREFIX.startswith("deduction/runs/dojoinit_recovery")


def test_s3_put_guard_rejects_study_prefix(rec, tmp_path):
    """ADDITIVE CONTRACT.

    A PUT outside the recovery prefix must die on the assertion BEFORE any
    aws subprocess runs.

    Study scaling_* prefixes are read-only to this tool, per the
    append-only bucket directive.
    """
    f = tmp_path / "x.jsonl"
    f.write_text("{}\n")
    for bad in ("deduction/runs/scaling_gemma-4-e2b/verified_rows.jsonl",
                "deduction/runs/scaling_x/recovered_rows.jsonl",
                "induction/whatever.yaml"):
        with pytest.raises(AssertionError, match="ADDITIVE-CONTRACT"):
            rec.s3_put(f, bad)


def test_s3_put_accepts_recovery_prefix(rec, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(rec.subprocess, "run",
                        lambda *a, **k: calls.append(a) or None)
    f = tmp_path / "x.jsonl"
    f.write_text("{}\n")
    rec.s3_put(f, rec.RECOVERY_S3_PREFIX + "some-lane/recovered_rows.jsonl")
    assert len(calls) == 1


def test_golden_std_keys_arithmetic(rec):
    std45 = [
        {"theorem_id": "A", "ks": [1], "n_cells": 4},
        {"theorem_id": "B", "ks": [2], "n_cells": 2},
        {"theorem_id": "C", "ks": [0], "n_cells": 1},
    ]
    assert rec.golden_std_keys(std45) == {("A", 1), ("B", 2), ("C", 0)}


def test_gate_fails_on_dojoinit_in_sanity(rec, tmp_path, monkeypatch):
    """CONTENT gate.

    One DojoInitError among 45 'success' rows must fail the gate, even though the row
    COUNT is perfect.

    This recovery exists to fix exactly the failure mode of counting rows.
    """
    monkeypatch.setattr(rec, "require_lake", lambda: None)
    monkeypatch.setattr(rec, "LOCAL_ROOT", tmp_path)
    (tmp_path / "inputs").mkdir(parents=True)
    std45 = [{"theorem_id": f"T{i}", "ks": [1], "n_cells": 4} for i in range(37)]
    std45 += [{"theorem_id": f"S{i}", "ks": [1], "n_cells": 1} for i in range(3)]
    # 37*4 + 3*1 = 151 cells over 40 theorems -- pad to 45 theorems / 151 cells
    std45[0]["ks"] = [1]
    std45 = ([{"theorem_id": f"T{i}", "ks": [1], "n_cells": 4} for i in range(35)]
             + [{"theorem_id": f"U{i}", "ks": [1], "n_cells": 1} for i in range(9)]
             + [{"theorem_id": "V", "ks": [1], "n_cells": 2}])
    assert sum(t["n_cells"] for t in std45) == 151 and len(std45) == 45
    (tmp_path / "inputs" / "std_45.json").write_text(json.dumps(std45))
    sanity = [{"theorem_id": t["theorem_id"], "verdict": "success", "error": None}
              for t in std45]
    sanity[7] = {"theorem_id": "T7", "verdict": "success",
                 "error": "DojoInitError: Cannot find the *.ast.json file"}
    sj = tmp_path / "sanity.json"
    sj.write_text(json.dumps(sanity))

    class A:
        sanity_json = str(sj)

    with pytest.raises(SystemExit, match="CONTENT GATE FAILED"):
        rec.stage_gate(A())
    # and the clean version passes
    sanity[7]["error"] = None
    sj.write_text(json.dumps(sanity))
    rec.stage_gate(A())


def test_recover_lane_count_assert(rec, monkeypatch, tmp_path):
    """150 std rows (one lost) must die on the count assertion, loudly."""
    monkeypatch.setattr(rec, "require_lake", lambda: None)
    monkeypatch.setattr(rec, "LOCAL_ROOT", tmp_path)
    (tmp_path / "inputs").mkdir(parents=True)
    std45 = ([{"theorem_id": f"T{i}", "ks": [1], "n_cells": 4} for i in range(35)]
             + [{"theorem_id": f"U{i}", "ks": [1], "n_cells": 1} for i in range(9)]
             + [{"theorem_id": "V", "ks": [1], "n_cells": 2}])
    (tmp_path / "inputs" / "std_45.json").write_text(json.dumps(std45))
    rows = [{"theorem_id": "T0", "k": 1, "rung": "stepk:1", "kind": "cell",
             "file_path": ".lake/packages/std/Std/X.lean", "verdict": "replay_failed"}
            for _ in range(150)]
    # a sanity row (no file_path) must be skipped, not crash the filter
    rows.append({"theorem_id": "T0", "kind": "sanity", "verdict": "success"})
    # a DUPLICATE of an existing cell must be dropped earliest-wins, so it
    # must NOT rescue the 150-distinct count (151 rows, 150 distinct)
    rows.append(dict(rows[0]))
    monkeypatch.setattr(rec, "s3_stream_rows", lambda lane: iter(rows))
    with pytest.raises(AssertionError, match="expected 151 distinct std cells, found "):
        rec.recover_lane("some-lane")


def test_dedupe_earliest_surviving_wins(rec):
    a = {"theorem_id": "T", "k": 1, "rung": "stepk:1", "replicate_idx": 0, "verdict": "success"}
    b = dict(a, verdict="lean_error")  # later duplicate must lose to an earlier survivor
    kept, dupes = rec.dedupe_earliest([a, b])
    assert dupes == 1 and kept == [a] and kept[0]["verdict"] == "success"
    # ... but an exception PLACEHOLDER (spot-killed attempt) must NOT beat a
    # later surviving row: the study loader takes the first NON-exception row.
    e = dict(a, verdict="exception")
    kept2, dupes2 = rec.dedupe_earliest([e, b])
    assert dupes2 == 1 and kept2[0]["verdict"] == "lean_error"
    # all-exception cell keeps its first row (dropped later by measurability)
    kept3, _ = rec.dedupe_earliest([e, dict(e)])
    assert kept3[0]["verdict"] == "exception"
