"""Offline tests for cmd_analyze's pass@N and truncation additions."""

from __future__ import annotations

import itertools
import json
from argparse import Namespace
from pathlib import Path

import pytest

from smolbench.deduction.lean.cli import cmd_analyze


def _row(**kw) -> dict:
    """Build one synthetic ``kind: "cell"`` sweep row."""
    row = {
        "kind": "cell", "theorem_id": "Mini.theoremA", "k": 1, "rung": "stepk:0",
        "replicate_idx": 0, "model": "model-a", "verdict": "success",
        "raw_response": "```lean\nrfl\n```", "prompt_tokens": 10,
        "completion_tokens": 5, "gen_ms": 100, "verify_ms": 50,
    }
    row.update(kw)
    return row


def _sanity_row(*, model: str = "model-a", verdict: str = "success") -> dict:
    """Build one synthetic ``kind: "sanity"`` row."""
    return {"kind": "sanity", "model": model, "verdict": verdict}


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write `rows` as newline-delimited JSON to `path`."""
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _run_analyze(tmp_path, rows, capsys) -> tuple[int, str]:
    """Write `rows` to all_rows.jsonl, invoke `cmd_analyze` as `cli.main` would."""
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)
    rc = cmd_analyze(Namespace(path=str(p)))
    return rc, capsys.readouterr().out


def _header_index(lines: list[str], *markers: str) -> int:
    """Index of the first line containing every string in `markers` (anchors a table)."""
    return next(i for i, line in enumerate(lines) if all(m in line for m in markers))


def _rows_after(lines: list[str], idx: int) -> list[str]:
    """Non-blank lines starting at `idx`, up to the blank line closing the block."""
    return list(itertools.takewhile(lambda line: line.strip(), lines[idx:]))


def _table_rows(lines: list[str], header_idx: int) -> list[str]:
    """Data rows of a table: header line, separator line, then rows."""
    return _rows_after(lines, header_idx + 2)


def _section_rows(out: str, marker: str) -> list[str]:
    """Data rows of a title-only section (no separator line)."""
    lines = out.splitlines()
    idx = next(i for i, line in enumerate(lines) if line.strip() == marker)
    return _rows_after(lines, idx + 1)


def test_single_replicate_omits_passn_table(tmp_path, capsys):
    """One replicate per cell: no pass@N tables, and a trunc column of zeros."""
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, verdict="success"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, verdict="lean_error"),
        _row(model="model-b", rung="stepk:1", theorem_id="T1", k=2, verdict="incomplete"),
    ]
    rc, out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 0
    assert "pass@N" not in out
    assert "# 3 cells from" in out
    assert "# sanity gate: 0 pass / 0 fail" in out
    assert "# per-model totals" in out
    assert "model-a" in out and "model-b" in out
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    assert "trunc" in lines[hdr]
    detail = _table_rows(lines, hdr)
    assert detail
    assert all(r.split()[-1] == "0" for r in detail)


def test_pass_at_n_grouping(tmp_path, capsys):
    """pass@N: any success in a (theorem, k) group passes; N is the max replicate count."""
    reps = {
        ("stepk:0", "T1"): ["success", "given_up", "replay_failed"],
        ("stepk:0", "T2"): ["lean_error", "lean_error", "success"],
        ("stepk:1", "T3"): ["lean_error", "lean_error"],
        ("stepk:1", "T4"): ["success"],
    }
    rows = [
        _row(rung=rung, theorem_id=thm, replicate_idx=i, verdict=v)
        for (rung, thm), verdicts in reps.items()
        for i, v in enumerate(verdicts)
    ]
    rc, out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 0
    assert "# pass@N per rung × model (N=3)" in out
    lines = out.splitlines()
    passn_rows = _table_rows(lines, _header_index(lines, "grp"))
    assert len(passn_rows) == 2
    by_rung = {r.split()[0]: r.split() for r in passn_rows}
    assert by_rung["stepk:0"][1] == "model-a"
    assert by_rung["stepk:0"][2] == "2/2" and by_rung["stepk:0"][3] == "100.0%"
    assert by_rung["stepk:1"][2] == "1/2" and by_rung["stepk:1"][3] == "50.0%"
    (rollup_row,) = _section_rows(out, "# pass@N per-model totals")
    assert "model-a" in rollup_row
    assert "3/4" in rollup_row and "75.0%" in rollup_row


def test_trunc_column_classification(tmp_path, capsys):
    """trunc counts unclosed <think> in raw_response/content, plus reasoning-only rows."""
    rows = [
        _row(theorem_id="T1", raw_response="<think>\nreasoning that never finishes"),
        _row(theorem_id="T2", raw_response="", content="<think>\nstill going"),
        _row(theorem_id="T3", raw_response="", reasoning_content="never finished"),
        _row(theorem_id="T4", raw_response="```lean\nrfl\n```", reasoning_content="done"),
        _row(theorem_id="T5", raw_response="<think>\nok\n</think>\n\n```lean\nrfl\n```"),
        _row(theorem_id="T6", raw_response="exact h"),
    ]
    rc, out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 0
    lines = out.splitlines()
    (row,) = _table_rows(lines, _header_index(lines, "lerr", "trunc"))
    assert row.split()[-1] == "3"


def test_sanity_rows_excluded_from_passn_and_trunc(tmp_path, capsys):
    """Sanity rows are reported separately and never enter cell counts, pass@N or trunc."""
    rows = [
        _sanity_row(model="model-a", verdict="lean_error"),
        _row(theorem_id="T1", replicate_idx=0, raw_response="<think>\nunclosed"),
        _row(theorem_id="T1", replicate_idx=1, verdict="lean_error"),
    ]
    rc, out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 0
    assert "# sanity gate: 0 pass / 1 fail" in out
    assert "!! 1 sanity-gate failures" in out
    assert "# 2 cells from" in out
    assert "(N=2)" in out
    lines = out.splitlines()
    (passn_row,) = _table_rows(lines, _header_index(lines, "grp"))
    fields = passn_row.split()
    assert fields[2] == "1/1" and fields[3] == "100.0%"
    (detail_row,) = _table_rows(lines, _header_index(lines, "lerr", "trunc"))
    assert detail_row.split()[-1] == "1"


@pytest.mark.parametrize("rows", [[], [_sanity_row()]], ids=["empty", "sanity-only"])
def test_no_cell_rows_returns_1(tmp_path, capsys, rows):
    """A file with no cell rows is an error, not an empty report."""
    rc, _out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 1


def test_cmd_analyze_refuses_a_superseded_rows_file(tmp_path):
    """A retired artifact must fail loudly and name the file, not be summarized."""
    p = tmp_path / "all_rows_SUPERSEDED-20260815T000000Z.jsonl"
    _write_jsonl(p, [_row()])
    with pytest.raises(ValueError) as excinfo:
        cmd_analyze(Namespace(path=str(p)))
    assert "SUPERSEDED" in str(excinfo.value)
    assert p.name in str(excinfo.value)


def test_analyze_reports_no_answer_in_its_own_column(tmp_path, capsys):
    """13-01: `analyze`'s table separates `noans` from `lerr`.

    An empty candidate used to be recorded as `lean_error`, so `analyze` showed
    a lane of truncated reasoning traces as a lane of wrong Lean proofs. Pins
    the new column by NAME and by value (not by position), and pins header/row
    width agreement so the `"-" * len(header)` rule cannot drift from the rows
    it underlines.
    """
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", verdict="no_answer",
             raw_response=""),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", verdict="lean_error"),
        _row(model="model-a", rung="stepk:0", theorem_id="T3", verdict="success"),
    ]
    rc, out = _run_analyze(tmp_path, rows, capsys)
    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "noans", "trunc")
    header = lines[hdr].split()
    detail = _table_rows(lines, hdr)
    assert len(detail) == 1, detail
    row = detail[0].split()
    assert len(row) == len(header), f"header/row width mismatch\n{header}\n{row}"
    assert row[header.index("noans")] == "1"
    assert row[header.index("lerr")] == "1"
    assert row[2] == "1/3"
