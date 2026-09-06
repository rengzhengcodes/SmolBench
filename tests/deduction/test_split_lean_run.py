"""Gates in scripts/deduction/split_lean_run_into_shards.py (13-04, 13-07).

The split script is the mirror of `merge_lean_shards.py` and carries the same
duplicate-cell gate, so it inherits the same bug: `runner._existing_keys`
deliberately re-runs a cell whose only row is an ``"exception"`` and the sweep
APPENDS the retry, so any lane that resumed past one exception carries duplicate
keys and the gate called that a mis-sharded lane.

Theorem-to-shard assignment goes through `runner._select_theorems`, which needs a
bootstrapped corpus; it is stubbed here so these tests exercise the ROW gates
(what this module is about) rather than corpus selection, which
`test_lean_runner.py` already covers.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from types import SimpleNamespace

import pytest

import smolbench.deduction.lean.runner as runner
from tests._paths import SCRIPTS

_PATH = SCRIPTS / "deduction" / "split_lean_run_into_shards.py"
_SPEC = importlib.util.spec_from_file_location("split_lean_run_into_shards", _PATH)
split_mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = split_mod
_SPEC.loader.exec_module(split_mod)

#: Every fixture row belongs to this theorem, so one shard owns everything.
THEOREM = "Mini.theoremA"


@pytest.fixture
def one_shard(monkeypatch):
    """Stub `_select_theorems` so shard 0 of 1 owns `THEOREM` and nothing else."""
    def _select(spec, *, cell_whitelist=None):
        shard = spec.get("shard", "0/1")
        return [SimpleNamespace(full_name=THEOREM)] if shard.startswith("0/") else []

    monkeypatch.setattr(runner, "_select_theorems", _select)


def _cell(verdict, *, rung="stepk:1", rep=0):
    return {"kind": "cell", "model": "m", "theorem_id": THEOREM, "k": 1,
            "rung": rung, "replicate_idx": rep, "verdict": verdict}


def _source(tmp_path, rows):
    src = tmp_path / "source"
    src.mkdir()
    (src / "all_rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return src


def _split(tmp_path, rows, *, n=1):
    return split_mod.split_run(
        "k", n, source=_source(tmp_path, rows), runs_root=tmp_path / "runs",
        theorems_spec={"source": "explicit", "full_names": [THEOREM]})


def test_split_collapses_an_exception_then_retry_duplicate(tmp_path, one_shard):
    """13-04: a resumed lane's duplicate key is ordinary, not a mis-sharded lane.

    Both rows still land in the shard -- every row goes to exactly one shard,
    and the superseded exception row is the audit trail for what the lane did.
    Only the ABORT is gone.
    """
    shards = _split(tmp_path, [_cell("exception"), _cell("success")])
    rows = [json.loads(x)
            for x in (shards[0] / "all_rows.jsonl").read_text().splitlines()]
    assert [r["verdict"] for r in rows] == ["exception", "success"]


def test_split_still_aborts_on_two_surviving_rows_for_one_key(tmp_path, one_shard):
    """13-04: two graded rows for one key is still a double-run lane, and still exits."""
    with pytest.raises(SystemExit, match="(?i)duplicate"):
        _split(tmp_path, [_cell("success"), _cell("lean_error")])
    assert not (tmp_path / "runs").exists(), "a failed gate must write nothing"


def test_split_keeps_distinct_replicates(tmp_path, one_shard):
    """Replicate index is part of the key, so two replicates are two cells."""
    shards = _split(tmp_path, [_cell("success", rep=0), _cell("success", rep=1)])
    rows = [json.loads(x)
            for x in (shards[0] / "all_rows.jsonl").read_text().splitlines()]
    assert [r["replicate_idx"] for r in rows] == [0, 1]


def test_split_drops_a_torn_final_line(tmp_path, one_shard):
    """13-07's premise: a torn FINAL line is dropped rather than aborting the split.

    Pinned here because 13-07 makes this script's docstring claim ("a torn
    final line ... regenerates on resume") actually true, by truncating the
    torn line before the resumed sweep appends onto it; this gate is the other
    half of that story and must keep working. The mid-file case has no test
    here -- `test_merge_lean_shards.py` covers the identical rule.
    """
    src = _source(tmp_path, [_cell("success")])
    with (src / "all_rows.jsonl").open("a") as f:
        f.write('{"kind": "cell", "theo')
    shards = split_mod.split_run(
        "k", 1, source=src, runs_root=tmp_path / "runs",
        theorems_spec={"source": "explicit", "full_names": [THEOREM]})
    rows = (shards[0] / "all_rows.jsonl").read_text().splitlines()
    assert len(rows) == 1 and json.loads(rows[0])["verdict"] == "success"
