"""Offline tests for `smolbench.deduction.lean.cli.cmd_analyze`'s pass@N and
truncation additions.

`cmd_analyze` is pure JSONL aggregation (no Dojo session, no lean_dojo import),
so these tests build small synthetic ``all_rows.jsonl`` fixtures by hand --
using only the row-schema fields `cmd_analyze` actually reads (see
`runner.py`'s `base_row`/`row` construction inside its `sweep` function for
the authoritative field list) -- and drive `cmd_analyze` the same way `main`
does: build an `argparse.Namespace` with a `path` attribute and call it
directly, capturing stdout with `capsys`. This runs on either venv.

Row-extraction helpers below are marker-anchored rather than naive
``str.startswith`` scans: `cmd_analyze` prints THREE different tables whose
rows can all start with the same rung slug (e.g. ``"stepk:0"``) -- the ASCII
bar chart, the detail table, and (when triggered) the pass@N table -- so a
plain "first line starting with the rung" search can silently grab a row
from the wrong table. Anchoring on each table's unique header text avoids
that trap.
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from smolbench.deduction.lean.cli import cmd_analyze


def _row(
    *,
    model: str = "model-a",
    rung: str = "stepk:0",
    theorem_id: str = "Mini.theoremA",
    k: int = 1,
    rollout_idx: int = 0,
    verdict: str = "success",
    raw_response: str = "```lean\nrfl\n```",
    content: str | None = None,
    reasoning_content: str | None = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    gen_ms: int = 100,
    verify_ms: int = 50,
) -> dict:
    """Build one synthetic ``kind: "cell"`` sweep row.

    Parameters
    ----------
    model, rung, theorem_id, k : see module row schema
        Identify the (model, rung, theorem_id, k) cell this rollout belongs
        to -- `cmd_analyze` groups pass@N on exactly this tuple.
    rollout_idx : int, default 0
        Recorded but NOT read by `cmd_analyze`'s pass@N grouping (which
        groups by row occurrence, not by distinct `rollout_idx`); kept here
        only for schema fidelity with real sweep output.
    verdict : str, default "success"
        One of the verdict strings `cmd_analyze` recognizes
        (``success``/``lean_error``/``incomplete``/``given_up``/
        ``replay_failed``/``exception``); anything else falls into the
        ``exception`` bucket, mirroring the real aggregator.
    raw_response : str, default a closed fenced tactic block
        Populates the row's ``raw_response`` field, the primary source for
        the trunc (unclosed ``<think>``) check.
    content : str or None, default None
        When given, also written under the row's ``content`` key -- used to
        exercise `cmd_analyze`'s ``raw_response``-missing fallback path.
    reasoning_content : str or None, default None
        When given, also written under the row's ``reasoning_content`` key
        -- used to exercise `cmd_analyze`'s reasoning-parser-served
        truncation path (reasoning present, `raw_response` empty).
    prompt_tokens, completion_tokens, gen_ms, verify_ms : int
        Small nonzero defaults so avg_in/avg_out/avg_s arithmetic in the
        detail table has something to divide.

    Returns
    -------
    dict
        A JSON-serializable row matching the real sweep schema's ``kind:
        "cell"`` rows closely enough for `cmd_analyze` to aggregate.
    """
    row = {
        "kind": "cell",
        "theorem_id": theorem_id,
        "k": k,
        "rung": rung,
        "rollout_idx": rollout_idx,
        "model": model,
        "verdict": verdict,
        "raw_response": raw_response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "gen_ms": gen_ms,
        "verify_ms": verify_ms,
    }
    if content is not None:
        row["content"] = content
    if reasoning_content is not None:
        row["reasoning_content"] = reasoning_content
    return row


def _sanity_row(*, model: str = "model-a", verdict: str = "success") -> dict:
    """Build one synthetic ``kind: "sanity"`` row (pre-sweep sanity-gate check)."""
    return {"kind": "sanity", "model": model, "verdict": verdict}


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write `rows` as newline-delimited JSON, one object per line, to `path`."""
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _run_analyze(path: Path, capsys) -> tuple[int, str]:
    """Invoke `cmd_analyze` the way `cli.main` would and capture stdout.

    Parameters
    ----------
    path : Path
        Sweep JSONL file to analyze.
    capsys : pytest fixture
        Standard pytest stdout/stderr capture fixture, passed through from
        the calling test (not imported -- injected by pytest itself).

    Returns
    -------
    tuple[int, str]
        `(exit_code, stdout)`.
    """
    rc = cmd_analyze(Namespace(path=str(path)))
    return rc, capsys.readouterr().out


def _header_index(lines: list[str], *markers: str) -> int:
    """Return the index of the first line containing every string in `markers`.

    Design: both the detail table and the pass@N table print a header
    starting with the ``rung`` column, and both tables' data rows can start
    with the same rung slug -- so callers must locate a table by header
    text unique to it (e.g. ``"trunc"`` for the detail table, ``"grp"`` for
    the pass@N table) rather than by scanning for a data-row prefix, or they
    risk silently reading a row from the wrong table.

    Raises
    ------
    StopIteration
        If no line contains all of `markers` (propagated from `next`) --
        deliberately left unwrapped so a broken assumption fails loudly at
        the assertion site instead of being masked by a default.
    """
    return next(i for i, line in enumerate(lines) if all(m in line for m in markers))


def _table_rows(lines: list[str], header_idx: int) -> list[str]:
    """Collect a table's data rows, given the index of its header line.

    Assumes the layout `cmd_analyze` always prints: header line, then a
    ``"-" * len(header)`` separator line, then one line per data row, then
    a blank line (or end of output) closing the table.
    """
    rows = []
    for line in lines[header_idx + 2:]:
        if not line.strip():
            break
        rows.append(line)
    return rows


def _section_rows(out: str, marker: str) -> list[str]:
    """Collect the non-blank lines immediately following the line equal to
    `marker` (used for the per-model rollup sections, which have no
    ``"---"`` separator of their own -- just a title line then data rows).
    """
    lines = out.splitlines()
    idx = next(i for i, line in enumerate(lines) if line.strip() == marker)
    rows = []
    for line in lines[idx + 1:]:
        if not line.strip():
            break
        rows.append(line)
    return rows


# ---------------------------------------------------------------------------
# Single-rollout sweeps: pass@N tables must be entirely absent, and every
# existing line must be untouched apart from the new trailing `trunc` column.
# ---------------------------------------------------------------------------


def test_single_rollout_omits_passn_table(tmp_path, capsys):
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, verdict="success"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, verdict="lean_error"),
        _row(model="model-b", rung="stepk:1", theorem_id="T1", k=2, verdict="incomplete"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    assert "pass@N" not in out
    # Existing sections still present and correctly computed.
    assert "# 3 cells from" in out
    assert "# sanity gate: 0 pass / 0 fail" in out
    assert "# per-model totals" in out
    assert "model-a" in out and "model-b" in out


def test_single_rollout_detail_table_gets_trunc_column_only(tmp_path, capsys):
    """The one sanctioned change to old output: a `trunc` column is always
    added to the detail table's header and rows, even when every cell has
    exactly one rollout and the pass@N tables are skipped."""
    rows = [_row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, verdict="success")]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    assert "trunc" in lines[hdr]
    (row,) = _table_rows(lines, hdr)
    # 1 rollout, no <think> in raw_response -> trailing trunc count is 0.
    assert row.split()[-1] == "0"


# ---------------------------------------------------------------------------
# pass@N: multi-rollout sweeps.
# ---------------------------------------------------------------------------


def test_multi_rollout_pass_at_n_counts_any_success(tmp_path, capsys):
    rows = [
        # T1: rollouts [lean_error, success] -> counts as ONE pass.
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=0, verdict="lean_error"),
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=1, verdict="success"),
        # T2: rollouts [lean_error, lean_error] -> fail.
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, rollout_idx=0, verdict="lean_error"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, rollout_idx=1, verdict="lean_error"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    assert "# pass@N per rung × model (N=2)" in out

    lines = out.splitlines()
    hdr = _header_index(lines, "grp")
    (row,) = _table_rows(lines, hdr)
    fields = row.split()
    assert fields[0] == "stepk:0"
    assert fields[1] == "model-a"
    # 1 pass out of 2 groups (T1 passes, T2 doesn't) = 50.0%.
    assert fields[2] == "1/2"
    assert fields[3] == "50.0%"

    (rollup_row,) = _section_rows(out, "# pass@N per-model totals")
    assert "model-a" in rollup_row
    assert "1/2" in rollup_row and "50.0%" in rollup_row


def test_multi_rollout_group_pass_ignores_which_rollout_succeeded(tmp_path, capsys):
    """Order/index of the successful rollout must not matter -- ANY success
    in the group is enough (rollout 0 succeeding here, not the last one)."""
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=0, verdict="success"),
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=1, verdict="given_up"),
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=2, verdict="replay_failed"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    assert "# pass@N per rung × model (N=3)" in out

    lines = out.splitlines()
    hdr = _header_index(lines, "grp")
    (row,) = _table_rows(lines, hdr)
    fields = row.split()
    assert fields[2] == "1/1"
    assert fields[3] == "100.0%"


def test_multi_rollout_n_is_max_across_all_cells(tmp_path, capsys):
    """N in the header reflects the MAX rollout count seen anywhere in the
    file, even if most cells only have 1 rollout (mixed replication)."""
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=0, verdict="success"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, rollout_idx=0, verdict="lean_error"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, rollout_idx=1, verdict="lean_error"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, rollout_idx=2, verdict="success"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    assert "(N=3)" in out

    lines = out.splitlines()
    hdr = _header_index(lines, "grp")
    (row,) = _table_rows(lines, hdr)
    fields = row.split()
    # 2 groups total (T1, T2), both pass -> 2/2, 100%.
    assert fields[2] == "2/2"
    assert fields[3] == "100.0%"


def test_multi_rollout_per_model_rollup_sums_across_rungs(tmp_path, capsys):
    rows = [
        # rung stepk:0, T1: pass.
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=0, verdict="success"),
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=1, verdict="lean_error"),
        # rung stepk:1, T2: fail.
        _row(model="model-a", rung="stepk:1", theorem_id="T2", k=2, rollout_idx=0, verdict="lean_error"),
        _row(model="model-a", rung="stepk:1", theorem_id="T2", k=2, rollout_idx=1, verdict="lean_error"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "grp")
    passn_rows = _table_rows(lines, hdr)
    assert len(passn_rows) == 2  # one row per (rung, model): stepk:0 and stepk:1

    (rollup_row,) = _section_rows(out, "# pass@N per-model totals")
    # model-a: 1 pass out of 2 groups total, summed across both rungs.
    assert "1/2" in rollup_row and "50.0%" in rollup_row


# ---------------------------------------------------------------------------
# Truncation ("trunc") column.
# ---------------------------------------------------------------------------


def test_trunc_counts_unclosed_think_blocks(tmp_path, capsys):
    rows = [
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1,
            verdict="incomplete", raw_response="<think>\nreasoning that never finishes",
        ),
        _row(
            model="model-a", rung="stepk:0", theorem_id="T2", k=1,
            verdict="success", raw_response="<think>\nok\n</think>\n\n```lean\nrfl\n```",
        ),
        _row(
            model="model-a", rung="stepk:0", theorem_id="T3", k=1,
            verdict="success", raw_response="```lean\nrfl\n```",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    # 3 rows total, exactly 1 has an unclosed <think> -> trunc == 1.
    assert row.split()[-1] == "1"


def test_trunc_zero_for_model_that_never_emits_think(tmp_path, capsys):
    rows = [
        _row(model="model-a", rung="stepk:0", theorem_id="T1", k=1, raw_response="```lean\nrfl\n```"),
        _row(model="model-a", rung="stepk:0", theorem_id="T2", k=1, raw_response="exact h"),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    assert row.split()[-1] == "0"


def test_trunc_falls_back_to_content_field_when_raw_response_missing(tmp_path, capsys):
    """`cmd_analyze` must check `content` defensively when `raw_response`
    itself is empty/absent -- exercise a row where only `content` carries an
    unclosed <think> block."""
    rows = [
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1,
            raw_response="", content="<think>\nstill going",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    assert row.split()[-1] == "1"


def test_trunc_counts_reasoning_parser_death_with_empty_raw_response(tmp_path, capsys):
    """When the box is served WITH a vLLM --reasoning-parser, a truncated
    generation's <think> content is split server-side into
    `reasoning_content` and never reaches `raw_response`/`content` at all --
    so the unclosed-<think>-in-raw_text check alone reads 0. A row with
    non-empty `reasoning_content` and empty `raw_response` must still count
    as truncated (the generation died inside the think channel)."""
    rows = [
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1,
            verdict="incomplete", raw_response="", reasoning_content="still reasoning, never finished",
        ),
        _row(
            model="model-a", rung="stepk:0", theorem_id="T2", k=1,
            verdict="success", raw_response="```lean\nrfl\n```", reasoning_content="ok, done",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    # T1: reasoning present, raw_response empty -> trunc. T2: raw_response
    # non-empty (closed tactic block, reasoning_content present too) -> not
    # trunc. Total trunc == 1.
    assert row.split()[-1] == "1"


def test_trunc_reasoning_content_with_nonempty_raw_response_not_counted(tmp_path, capsys):
    """A reasoning-parser-served row whose `raw_response` DID come through
    (the model finished inside its think channel and still emitted an
    answer) must not be misclassified as truncated just because
    `reasoning_content` is also present."""
    rows = [
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1,
            raw_response="```lean\nrfl\n```", reasoning_content="because rfl closes it",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    assert row.split()[-1] == "0"


def test_trunc_closed_think_not_counted(tmp_path, capsys):
    rows = [
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1,
            raw_response="<think>\nreasoning\n</think>\n\n```lean\nrfl\n```",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    lines = out.splitlines()
    hdr = _header_index(lines, "lerr", "trunc")
    (row,) = _table_rows(lines, hdr)
    assert row.split()[-1] == "0"


# ---------------------------------------------------------------------------
# Sanity rows must not leak into either pass@N grouping or trunc counting.
# ---------------------------------------------------------------------------


def test_sanity_rows_excluded_from_passn_and_trunc(tmp_path, capsys):
    rows = [
        _sanity_row(model="model-a", verdict="lean_error"),
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=0,
            verdict="success", raw_response="<think>\nunclosed",
        ),
        _row(
            model="model-a", rung="stepk:0", theorem_id="T1", k=1, rollout_idx=1,
            verdict="lean_error",
        ),
    ]
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, rows)

    rc, out = _run_analyze(p, capsys)

    assert rc == 0
    assert "# sanity gate: 0 pass / 1 fail" in out
    assert "!! 1 sanity-gate failures" in out
    # 2 cell rows (the sanity row is excluded from the cell count).
    assert "# 2 cells from" in out

    lines = out.splitlines()

    # Both cell rows share one (theorem_id, k) group -> 1 group total, 1 pass.
    assert "(N=2)" in out
    hdr_passn = _header_index(lines, "grp")
    (passn_row,) = _table_rows(lines, hdr_passn)
    fields = passn_row.split()
    assert fields[2] == "1/1"
    assert fields[3] == "100.0%"

    # trunc counts only the cell row with the unclosed <think> -> 1, not 2
    # (the sanity row has no raw_response/content at all and must not crash
    # or contribute).
    hdr_detail = _header_index(lines, "lerr", "trunc")
    (detail_row,) = _table_rows(lines, hdr_detail)
    assert detail_row.split()[-1] == "1"


# ---------------------------------------------------------------------------
# Pre-existing behavior, unaffected by this change (regression guard).
# ---------------------------------------------------------------------------


def test_empty_file_returns_1(tmp_path, capsys):
    p = tmp_path / "all_rows.jsonl"
    p.write_text("")

    rc, _out = _run_analyze(p, capsys)

    assert rc == 1


def test_only_sanity_rows_returns_1(tmp_path, capsys):
    p = tmp_path / "all_rows.jsonl"
    _write_jsonl(p, [_sanity_row()])

    rc, _out = _run_analyze(p, capsys)

    assert rc == 1
