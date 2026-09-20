"""Merge gates in scripts/deduction/merge_lean_shards.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import cell_row, write_jsonl

from tests._paths import SCRIPTS, load_by_path

_PATH = SCRIPTS / "deduction" / "merge_lean_shards.py"
merge_mod = load_by_path(_PATH, "merge_lean_shards")


def _lines(run_dir: Path) -> list[str]:
    """Records, split on "\n" only -- `splitlines` also breaks on the U+2028 above."""
    return [x for x in (run_dir / "all_rows.jsonl").read_text().split("\n") if x]


def _write_shard(
    runs: Path, key: str, i: int, n: int, rows: list[dict[str, Any]]
) -> None:
    name = f"scaling_{key}_shard{i}of{n}"
    d = runs / name
    d.mkdir(parents=True)
    write_jsonl(d / "all_rows.jsonl", rows)
    (d / "manifest.json").write_text(
        json.dumps(
            {
                "run_name": name,
                "started_at": f"T{i}",
                "finished_at": f"T{i}b",
                "config": {
                    "run_name": name,
                    "theorems": {"limit": 300, "shard": f"{i}/{n}"},
                },
                "counts": {"written": len(rows), "skipped": 0, "success": 0},
            }
        )
    )
    (d / "server_config.yaml").write_text(f"-   instance_id: box{i}\n")
    (d / "theorems" / f"Thm{i}").mkdir(parents=True)
    (d / "theorems" / f"Thm{i}" / "meta.json").write_text("{}")


def test_merge_combines_rows_sidecars_and_manifests(tmp_path: Path) -> None:
    """Rows, server configs, theorems/ and manifests union in shard order."""
    runs = tmp_path / "runs"
    special = {"gen_ms": 1e-05, "lean_error": "\u00e9rreur\u2028line two", "model": "m"}
    _write_shard(
        runs,
        "k",
        0,
        2,
        [cell_row(theorem_id="A", **special), cell_row(kind="sanity", theorem_id="A")],
    )
    _write_shard(
        runs,
        "k",
        1,
        2,
        [cell_row(theorem_id="B", **special), cell_row(kind="sanity", theorem_id="B")],
    )
    out = merge_mod.merge_shards(
        "k", 2, runs_root=runs, expect_cells=2, expect_sanity=2
    )
    merged = (out / "all_rows.jsonl").read_text()
    assert merged == "".join(
        (runs / f"scaling_k_shard{i}of2" / "all_rows.jsonl").read_text() for i in (0, 1)
    ), "merged rows must be byte-identical to the shards'"
    rows = [json.loads(x) for x in merged.split("\n") if x]
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


def test_merge_gates_fail_closed(tmp_path: Path) -> None:
    """Duplicate cells, wrong totals, missing shards and clobbering all exit."""
    runs = tmp_path / "runs"
    _write_shard(runs, "dup", 0, 2, [cell_row(theorem_id="A")])
    _write_shard(runs, "dup", 1, 2, [cell_row(theorem_id="A")])
    with pytest.raises(SystemExit, match="(?i)duplicate"):
        merge_mod.merge_shards(
            "dup", 2, runs_root=runs, expect_cells=1, expect_sanity=0
        )

    runs2 = tmp_path / "runs2"
    _write_shard(runs2, "tot", 0, 1, [cell_row(theorem_id="A")])
    with pytest.raises(SystemExit, match="cell count 1 != expected 944"):
        merge_mod.merge_shards(
            "tot", 1, runs_root=runs2, expect_cells=944, expect_sanity=0
        )

    runs3 = tmp_path / "runs3"
    with pytest.raises(SystemExit, match="missing"):
        merge_mod.merge_shards(
            "gone", 2, runs_root=runs3, expect_cells=0, expect_sanity=0
        )

    runs4 = tmp_path / "runs4"
    _write_shard(runs4, "clob", 0, 1, [cell_row(theorem_id="A")])
    canonical = runs4 / "scaling_clob"
    canonical.mkdir()
    (canonical / "all_rows.jsonl").write_text("precious\n")
    with pytest.raises(SystemExit, match="refusing to clobber"):
        merge_mod.merge_shards(
            "clob", 1, runs_root=runs4, expect_cells=1, expect_sanity=0
        )
    assert (canonical / "all_rows.jsonl").read_text() == "precious\n"


def test_merge_drops_a_torn_tail_but_aborts_on_mid_file_corruption(
    tmp_path: Path,
) -> None:
    """A shard's torn final line is dropped; a corrupt row anywhere else exits."""
    runs = tmp_path / "runs"
    _write_shard(
        runs,
        "torn",
        0,
        1,
        [cell_row(theorem_id="A"), cell_row(kind="sanity", theorem_id="A")],
    )
    with (runs / "scaling_torn_shard0of1" / "all_rows.jsonl").open("a") as f:
        f.write('{"kind": "cell", "theo')
    out = merge_mod.merge_shards(
        "torn", 1, runs_root=runs, expect_cells=1, expect_sanity=1
    )
    assert [json.loads(x)["kind"] for x in _lines(out)] == ["cell", "sanity"]

    runs2 = tmp_path / "runs2"
    _write_shard(
        runs2,
        "bad",
        0,
        1,
        [cell_row(theorem_id="A"), cell_row(kind="sanity", theorem_id="A")],
    )
    path = runs2 / "scaling_bad_shard0of1" / "all_rows.jsonl"
    path.write_text("{oops\n" + path.read_text())
    with pytest.raises(SystemExit, match="corrupt row mid-file at line 1"):
        merge_mod.merge_shards(
            "bad", 1, runs_root=runs2, expect_cells=1, expect_sanity=1
        )
    assert not (runs2 / "scaling_bad" / "all_rows.jsonl").exists()


def test_merge_collapses_an_exception_then_retry_duplicate(tmp_path: Path) -> None:
    """Resumed exception/retry pairs stay; their key counts once for `--expect-cells`.

    Both rows are safe because ``power_analysis.grade_verdicts`` applies earliest-surviving-wins.
    """
    runs = tmp_path / "runs"
    _write_shard(
        runs,
        "resumed",
        0,
        1,
        [
            cell_row(kind="sanity", theorem_id="A"),
            cell_row(theorem_id="A", verdict="exception"),
            cell_row(theorem_id="A", verdict="success"),
        ],
    )
    out = merge_mod.merge_shards(
        "resumed", 1, runs_root=runs, expect_cells=1, expect_sanity=1
    )
    rows = [json.loads(x) for x in _lines(out)]
    assert [r.get("verdict") for r in rows if r["kind"] == "cell"] == [
        "exception",
        "success",
    ], "both rows must survive the merge"


def test_merge_collapses_an_exception_only_cell(tmp_path: Path) -> None:
    """A cell whose every row is an exception was never measured -- not an abort."""
    runs = tmp_path / "runs"
    _write_shard(
        runs,
        "allexc",
        0,
        1,
        [
            cell_row(theorem_id="A", verdict="exception"),
            cell_row(theorem_id="A", verdict="exception"),
        ],
    )
    out = merge_mod.merge_shards(
        "allexc", 1, runs_root=runs, expect_cells=1, expect_sanity=0
    )
    assert len(_lines(out)) == 2


def test_merge_still_aborts_on_two_surviving_rows_for_one_key(tmp_path: Path) -> None:
    """Two real verdicts for one key must abort as a mis-shard or double run."""
    runs = tmp_path / "runs"
    _write_shard(runs, "twice", 0, 2, [cell_row(theorem_id="A")])
    _write_shard(runs, "twice", 1, 2, [cell_row(theorem_id="A", verdict="lean_error")])
    with pytest.raises(SystemExit, match="(?i)duplicate"):
        merge_mod.merge_shards(
            "twice", 2, runs_root=runs, expect_cells=1, expect_sanity=0
        )
