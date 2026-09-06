"""Merge gates in scripts/deduction/merge_lean_shards.py."""

import importlib.util
import json
import sys

import pytest

from tests._paths import SCRIPTS

_PATH = SCRIPTS / "deduction" / "merge_lean_shards.py"
_SPEC = importlib.util.spec_from_file_location("merge_lean_shards", _PATH)
merge_mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = merge_mod
_SPEC.loader.exec_module(merge_mod)


def _cell(theorem: str, rung: str = "stepk:1") -> dict:
    return {"kind": "cell", "model": "m", "theorem_id": theorem, "k": 1,
            "rung": rung, "replicate_idx": 0}


def _sanity(theorem: str) -> dict:
    return {"kind": "sanity", "theorem_id": theorem}


def _write_shard(runs, key, i, n, rows):
    name = f"scaling_{key}_shard{i}of{n}"
    d = runs / name
    d.mkdir(parents=True)
    (d / "all_rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "manifest.json").write_text(json.dumps({
        "run_name": name, "started_at": f"T{i}", "finished_at": f"T{i}b",
        "config": {"run_name": name, "theorems": {"limit": 300, "shard": f"{i}/{n}"}},
        "counts": {"written": len(rows), "skipped": 0, "success": 0},
    }))
    (d / "server_config.yaml").write_text(f"-   instance_id: box{i}\n")
    (d / "theorems" / f"Thm{i}").mkdir(parents=True)
    (d / "theorems" / f"Thm{i}" / "meta.json").write_text("{}")


def test_merge_combines_rows_sidecars_and_manifests(tmp_path):
    """Rows, server configs, theorems/ and manifests union in shard order."""
    runs = tmp_path / "runs"
    _write_shard(runs, "k", 0, 2, [_cell("A"), _sanity("A")])
    _write_shard(runs, "k", 1, 2, [_cell("B"), _sanity("B")])
    out = merge_mod.merge_shards("k", 2, runs_root=runs, expect_cells=2, expect_sanity=2)
    rows = [json.loads(x) for x in (out / "all_rows.jsonl").read_text().splitlines()]
    assert [r["theorem_id"] for r in rows] == ["A", "A", "B", "B"]
    cfg = (out / "server_config.yaml").read_text()
    assert cfg == "-   instance_id: box0\n-   instance_id: box1\n"
    assert (out / "theorems" / "Thm0" / "meta.json").is_file()
    assert (out / "theorems" / "Thm1" / "meta.json").is_file()
    assert (out / "manifest_shard0of2.json").is_file()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["run_name"] == "scaling_k"
    assert "shard" not in manifest["config"]["theorems"]
    assert manifest["counts"]["written"] == 4
    assert [s["shard"] for s in manifest["merged_from_shards"]] == ["0/2", "1/2"]


def test_merge_gates_fail_closed(tmp_path):
    """Duplicate cells, wrong totals, missing shards and clobbering all exit."""
    runs = tmp_path / "runs"
    _write_shard(runs, "dup", 0, 2, [_cell("A")])
    _write_shard(runs, "dup", 1, 2, [_cell("A")])
    with pytest.raises(SystemExit, match="(?i)duplicate"):
        merge_mod.merge_shards("dup", 2, runs_root=runs, expect_cells=None, expect_sanity=None)

    runs2 = tmp_path / "runs2"
    _write_shard(runs2, "tot", 0, 1, [_cell("A")])
    with pytest.raises(SystemExit, match="cell count 1 != expected 944"):
        merge_mod.merge_shards("tot", 1, runs_root=runs2, expect_cells=944, expect_sanity=None)

    runs3 = tmp_path / "runs3"
    with pytest.raises(SystemExit, match="missing"):
        merge_mod.merge_shards("gone", 2, runs_root=runs3, expect_cells=None, expect_sanity=None)

    runs4 = tmp_path / "runs4"
    _write_shard(runs4, "clob", 0, 1, [_cell("A")])
    canonical = runs4 / "scaling_clob"
    canonical.mkdir()
    (canonical / "all_rows.jsonl").write_text("precious\n")
    with pytest.raises(SystemExit, match="refusing to clobber"):
        merge_mod.merge_shards("clob", 1, runs_root=runs4, expect_cells=None, expect_sanity=None)
    assert (canonical / "all_rows.jsonl").read_text() == "precious\n"


def test_merge_drops_a_torn_tail_but_aborts_on_mid_file_corruption(tmp_path):
    """A shard's torn final line is dropped; a corrupt row anywhere else exits."""
    runs = tmp_path / "runs"
    _write_shard(runs, "torn", 0, 1, [_cell("A"), _sanity("A")])
    with (runs / "scaling_torn_shard0of1" / "all_rows.jsonl").open("a") as f:
        f.write('{"kind": "cell", "theo')
    out = merge_mod.merge_shards("torn", 1, runs_root=runs, expect_cells=1, expect_sanity=1)
    assert [json.loads(x)["kind"] for x in (out / "all_rows.jsonl").read_text().splitlines()] \
        == ["cell", "sanity"]

    runs2 = tmp_path / "runs2"
    _write_shard(runs2, "bad", 0, 1, [_cell("A"), _sanity("A")])
    path = runs2 / "scaling_bad_shard0of1" / "all_rows.jsonl"
    path.write_text("{oops\n" + path.read_text())
    with pytest.raises(SystemExit, match="corrupt row mid-file at line 1"):
        merge_mod.merge_shards("bad", 1, runs_root=runs2, expect_cells=None, expect_sanity=None)
    assert not (runs2 / "scaling_bad" / "all_rows.jsonl").exists()


def _cell_v(theorem, verdict, rung="stepk:1"):
    """A cell row carrying an explicit verdict (the duplicate-collapse rule reads it)."""
    return dict(_cell(theorem, rung), verdict=verdict)


def test_merge_collapses_an_exception_then_retry_duplicate(tmp_path):
    """13-04: ordinary resume produces duplicate keys; merge must not abort on them.

    `runner._existing_keys` deliberately re-runs a cell whose only row is an
    ``"exception"`` and the sweep APPENDS the retry, so any lane that resumed
    past one exception carries two rows for one key. The old gate called that
    "a mis-sharded/double-run lane" and exited.

    Both rows are KEPT in the merged file -- superseded data is labelled, never
    silently dropped, and `power_analysis.grade_verdicts` already applies
    earliest-surviving-wins to them -- but the key counts ONCE against
    ``--expect-cells``, which is the other half of the bug: 945 rows against a
    pinned 944 aborted just as hard.
    """
    runs = tmp_path / "runs"
    _write_shard(runs, "resumed", 0, 1, [
        _sanity("A"),
        _cell_v("A", "exception"),
        _cell_v("A", "success"),
    ])
    out = merge_mod.merge_shards("resumed", 1, runs_root=runs,
                                 expect_cells=1, expect_sanity=1)
    rows = [json.loads(x) for x in (out / "all_rows.jsonl").read_text().splitlines()]
    assert [r.get("verdict") for r in rows if r["kind"] == "cell"] == \
        ["exception", "success"], "both rows must survive the merge"


def test_merge_collapses_an_exception_only_cell(tmp_path):
    """13-04: a cell whose every row is an exception was never measured -- not an abort."""
    runs = tmp_path / "runs"
    _write_shard(runs, "allexc", 0, 1, [
        _cell_v("A", "exception"),
        _cell_v("A", "exception"),
    ])
    out = merge_mod.merge_shards("allexc", 1, runs_root=runs,
                                 expect_cells=1, expect_sanity=None)
    assert len((out / "all_rows.jsonl").read_text().splitlines()) == 2


def test_merge_still_aborts_on_two_surviving_rows_for_one_key(tmp_path):
    """13-04: the gate keeps its teeth for the failure it was written for.

    Two rows that both reached a real verdict for one cell key IS a mis-sharded
    or double-run lane. Checked across shards (the original scenario) and with
    two graded verdicts, so the collapse rule cannot be read as "any duplicate
    is fine now".
    """
    runs = tmp_path / "runs"
    _write_shard(runs, "twice", 0, 2, [_cell_v("A", "success")])
    _write_shard(runs, "twice", 1, 2, [_cell_v("A", "lean_error")])
    with pytest.raises(SystemExit, match="(?i)duplicate"):
        merge_mod.merge_shards("twice", 2, runs_root=runs,
                               expect_cells=None, expect_sanity=None)
