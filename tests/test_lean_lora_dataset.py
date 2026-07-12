"""Offline tests for ``scripts/lean_lora_sft.py``'s dataset loader (WP-A2's
``--extra-dataset`` support).

Two layers are exercised separately, per the file's own docstring:

- ``_read_chat_rows``: a pure function (no ``datasets`` import) covering row
  shape and the empty-file ``SystemExit``. Runs on any interpreter.
- ``_load_chat_dataset``: needs a real ``datasets`` install to build/shuffle
  a ``Dataset``. Neither offline venv in this repo ships ``datasets`` (it is
  a training-only dependency -- see ``scripts/requirements-train.txt``), so
  these are guarded with ``pytest.importorskip("datasets")`` and simply skip
  rather than fail when it's absent, in EITHER venv (per
  ``spec_a2_train_wiring.md``'s guidance).

The load-bearing property under test in the merge-path tests is the
backward-compat invariant documented on ``_load_chat_dataset``: with no
``--extra-dataset``, the returned rows/order must be BYTE-IDENTICAL to the
pre-``--extra-dataset`` code path (``Dataset.from_list(rows).shuffle(seed)
.select(range(max_examples))``), because a mid-flight training run resumed
from a checkpoint depends on that exact row order never changing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import lean_lora_sft as sft  # noqa: E402  (needs the sys.path insert above)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write `rows` (each a ``{system, user, assistant}`` dict) as one JSON object per line."""
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _make_rows(n: int, prefix: str) -> list[dict]:
    """`n` distinctly-tagged SFT rows so the merge tests can tell main vs. extra rows apart by content."""
    return [{"system": "S", "user": f"{prefix}-u{i}", "assistant": f"{prefix}-a{i}"} for i in range(n)]


# ---------------------------------------------------------------------------
# _read_chat_rows: pure, no `datasets` import -- safe on any interpreter.
# ---------------------------------------------------------------------------


def test_read_chat_rows_shape(tmp_path):
    p = tmp_path / "main.jsonl"
    _write_jsonl(p, [
        {"system": "sys0", "user": "u0", "assistant": "a0"},
        {"system": "sys1", "user": "u1", "assistant": "a1"},
    ])
    assert sft._read_chat_rows(p) == [
        {"messages": [
            {"role": "system", "content": "sys0"},
            {"role": "user", "content": "u0"},
            {"role": "assistant", "content": "a0"},
        ]},
        {"messages": [
            {"role": "system", "content": "sys1"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
        ]},
    ]


def test_read_chat_rows_preserves_file_order(tmp_path):
    """No shuffling inside `_read_chat_rows` -- ordering is the caller's job
    (a single seeded shuffle spanning multiple concatenated files)."""
    p = tmp_path / "main.jsonl"
    _write_jsonl(p, _make_rows(10, prefix="row"))
    rows = sft._read_chat_rows(p)
    assert [r["messages"][1]["content"] for r in rows] == [f"row-u{i}" for i in range(10)]


def test_read_chat_rows_empty_file_raises_systemexit(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    with pytest.raises(SystemExit, match="empty dataset"):
        sft._read_chat_rows(p)


# ---------------------------------------------------------------------------
# --extra-dataset argparse wiring
# ---------------------------------------------------------------------------


def test_extra_dataset_flag_defaults_to_none():
    ns = sft.build_parser().parse_args(["--base-model", "m", "--dataset", "d", "--output-dir", "o"])
    assert ns.extra_dataset is None


def test_extra_dataset_flag_is_repeatable_and_typed_as_path():
    ns = sft.build_parser().parse_args(
        ["--base-model", "m", "--dataset", "d", "--output-dir", "o",
         "--extra-dataset", "a.jsonl", "--extra-dataset", "b.jsonl"]
    )
    assert ns.extra_dataset == [Path("a.jsonl"), Path("b.jsonl")]


# ---------------------------------------------------------------------------
# _load_chat_dataset: needs a real `datasets` install (training-only dep).
# Design: `pytest.importorskip` is called INSIDE each test (via this
# fixture), not at module level -- a module-level importorskip would raise
# during collection and skip the WHOLE file, including the pure
# `_read_chat_rows` tests above that need no `datasets` install at all.
# ---------------------------------------------------------------------------


@pytest.fixture
def datasets_mod():
    return pytest.importorskip("datasets")


def test_load_chat_dataset_no_extras_matches_current_semantics(tmp_path, datasets_mod):
    """CRITICAL BACKWARD-COMPAT INVARIANT: `extra_paths=()` must reproduce
    the pre-`--extra-dataset` code path bit-for-bit -- computed here inline
    from the CURRENT semantics, not copy-pasted expected data, so a future
    accidental change to that branch is caught."""
    main_path = tmp_path / "main.jsonl"
    _write_jsonl(main_path, _make_rows(5, prefix="main"))

    got = sft._load_chat_dataset(main_path, max_examples=3, seed=1776)

    rows = sft._read_chat_rows(main_path)
    expected = datasets_mod.Dataset.from_list(rows).shuffle(seed=1776).select(range(3))
    assert got.to_list() == expected.to_list()


def test_load_chat_dataset_no_extras_uncapped_returns_all_rows_unshuffled(tmp_path, datasets_mod):
    """max_examples=0 (or >= len(ds)) skips the shuffle entirely in the
    current code path -- rows stay in file order."""
    main_path = tmp_path / "main.jsonl"
    _write_jsonl(main_path, _make_rows(4, prefix="main"))

    got = sft._load_chat_dataset(main_path, max_examples=0, seed=1776)
    assert [r["messages"][1]["content"] for r in got.to_list()] == ["main-u0", "main-u1", "main-u2", "main-u3"]


def test_load_chat_dataset_with_extras_includes_all_extra_and_capped_main(tmp_path, datasets_mod):
    main_path = tmp_path / "main.jsonl"
    _write_jsonl(main_path, _make_rows(5, prefix="main"))
    extra_path = tmp_path / "extra.jsonl"
    _write_jsonl(extra_path, _make_rows(4, prefix="extra"))

    got = sft._load_chat_dataset(main_path, max_examples=3, seed=1776, extra_paths=(extra_path,))
    rows = got.to_list()

    main_rows = [r for r in rows if r["messages"][1]["content"].startswith("main-")]
    extra_rows = [r for r in rows if r["messages"][1]["content"].startswith("extra-")]
    assert len(main_rows) == 3  # capped, like the main-only path
    assert len(extra_rows) == 4  # every extra row included, uncapped
    assert {r["messages"][1]["content"] for r in extra_rows} == {f"extra-u{i}" for i in range(4)}


def test_load_chat_dataset_multiple_extra_paths_are_all_included(tmp_path, datasets_mod):
    """Multiple --extra-dataset files concatenate into ONE extra pool before
    the final shuffle (not capped against each other or the main set)."""
    main_path = tmp_path / "main.jsonl"
    _write_jsonl(main_path, _make_rows(2, prefix="main"))
    extra_a = tmp_path / "extra_a.jsonl"
    _write_jsonl(extra_a, _make_rows(2, prefix="extraA"))
    extra_b = tmp_path / "extra_b.jsonl"
    _write_jsonl(extra_b, _make_rows(3, prefix="extraB"))

    got = sft._load_chat_dataset(main_path, max_examples=0, seed=1776, extra_paths=(extra_a, extra_b))
    users = {r["messages"][1]["content"] for r in got.to_list()}
    assert users == {
        "main-u0", "main-u1",
        "extraA-u0", "extraA-u1",
        "extraB-u0", "extraB-u1", "extraB-u2",
    }


def test_load_chat_dataset_logs_row_counts(tmp_path, capsys, datasets_mod):
    main_path = tmp_path / "main.jsonl"
    _write_jsonl(main_path, _make_rows(5, prefix="main"))
    extra_path = tmp_path / "extra.jsonl"
    _write_jsonl(extra_path, _make_rows(4, prefix="extra"))

    sft._load_chat_dataset(main_path, max_examples=3, seed=1776, extra_paths=(extra_path,))
    assert "rows: main=3 extra=4" in capsys.readouterr().out
