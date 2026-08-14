"""Offline tests for scripts/merge_lean_shards.py's merge gates.

The merge is the single point where three shard boxes' outputs become the
canonical lane object the verify pass and analysis read, so its gates
(uniqueness, expected totals, no-clobber, theorems/ disjointness) are what
stand between a mis-sharded fleet and silently corrupt study data. Spool
behaviour is NOT re-tested here -- --spool reuses the deduction driver's own
spool_to_s3, which has its own tests.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "merge_lean_shards",
    Path(__file__).resolve().parents[1] / "scripts" / "merge_lean_shards.py",
)
merge_mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = merge_mod
_SPEC.loader.exec_module(merge_mod)


def _cell(theorem: str, rung: str = "stepk:1") -> dict:
    return {
        "kind": "cell",
        "model": "m",
        "theorem_id": theorem,
        "k": 1,
        "rung": rung,
        "replicate_idx": 0,
    }


def _sanity(theorem: str) -> dict:
    return {"kind": "sanity", "theorem_id": theorem}


def _write_shard(runs: Path, key: str, i: int, n: int, rows: list[dict]) -> Path:
    d = runs / f"scaling_{key}_shard{i}of{n}"
    d.mkdir(parents=True)
    with (d / "all_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (d / "manifest.json").write_text(json.dumps({
        "run_name": f"scaling_{key}_shard{i}of{n}",
        "started_at": f"T{i}",
        "finished_at": f"T{i}b",
        "config": {
            "run_name": f"scaling_{key}_shard{i}of{n}",
            "theorems": {"limit": 300, "shard": f"{i}/{n}"},
        },
        "counts": {"written": len(rows), "skipped": 0, "success": 0},
    }))
    (d / "server_config.yaml").write_text(f"-   instance_id: box{i}\n")
    tdir = d / "theorems" / f"Thm{i}"
    tdir.mkdir(parents=True)
    (tdir / "meta.json").write_text("{}")
    return d


def test_merge_combines_rows_sidecars_and_manifests(tmp_path):
    runs = tmp_path / "runs"
    _write_shard(runs, "k", 0, 2, [_cell("A"), _sanity("A")])
    _write_shard(runs, "k", 1, 2, [_cell("B"), _sanity("B")])

    out = merge_mod.merge_shards("k", 2, runs_root=runs, expect_cells=2, expect_sanity=2)

    rows = [json.loads(x) for x in (out / "all_rows.jsonl").read_text().splitlines()]
    assert [r["theorem_id"] for r in rows] == ["A", "A", "B", "B"]  # shard order
    assert (out / "server_config.yaml").read_text() == (
        "-   instance_id: box0\n-   instance_id: box1\n"
    )
    assert (out / "theorems" / "Thm0" / "meta.json").is_file()
    assert (out / "theorems" / "Thm1" / "meta.json").is_file()
    assert (out / "manifest_shard0of2.json").is_file()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["run_name"] == "scaling_k"
    assert "shard" not in manifest["config"]["theorems"]  # union == unsharded selection
    assert manifest["counts"]["written"] == 4
    assert [s["shard"] for s in manifest["merged_from_shards"]] == ["0/2", "1/2"]


def test_merge_gates_fail_closed(tmp_path):
    runs = tmp_path / "runs"
    _write_shard(runs, "dup", 0, 2, [_cell("A")])
    _write_shard(runs, "dup", 1, 2, [_cell("A")])  # same cell key on both shards
    with pytest.raises(SystemExit, match="duplicate cell"):
        merge_mod.merge_shards("dup", 2, runs_root=runs, expect_cells=None, expect_sanity=None)

    runs2 = tmp_path / "runs2"
    _write_shard(runs2, "tot", 0, 1, [_cell("A")])
    with pytest.raises(SystemExit, match="cell count 1 != expected 944"):
        merge_mod.merge_shards("tot", 1, runs_root=runs2, expect_cells=944, expect_sanity=None)

    # Missing shard artifacts fail before anything is written.
    runs3 = tmp_path / "runs3"
    with pytest.raises(SystemExit, match="missing"):
        merge_mod.merge_shards("gone", 2, runs_root=runs3, expect_cells=None, expect_sanity=None)

    # A canonical all_rows.jsonl must never be clobbered.
    runs4 = tmp_path / "runs4"
    _write_shard(runs4, "clob", 0, 1, [_cell("A")])
    canonical = runs4 / "scaling_clob"
    canonical.mkdir()
    (canonical / "all_rows.jsonl").write_text("precious\n")
    with pytest.raises(SystemExit, match="refusing to clobber"):
        merge_mod.merge_shards("clob", 1, runs_root=runs4, expect_cells=None, expect_sanity=None)
    assert (canonical / "all_rows.jsonl").read_text() == "precious\n"
