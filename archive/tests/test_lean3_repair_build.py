"""Offline tests for scripts/build_lean3_align_map.py and
scripts/build_lean3_repair_sft.py.

No real LeanDojo Benchmark 4 download and no traced mathlib4 checkout are
used: `SMOLBENCH_LEAN_DATA` is pointed at a per-test tmp directory (with
EMPTY ``novel_premises/{val,test}.json`` -- present only so
`smolbench.deduction.lean.decontam.HoldoutIndex.build()`'s default
`sft.DEFAULT_EVAL_SPECS` load succeeds; the repair-builder tests exercise
the decontamination *gate itself* via a monkeypatched
`HoldoutIndex.check`, not via real holdout content -- see
`test_decontam_drop_path_via_monkeypatched_check`), and the align-map
builder's "cache" is a hand-built two-file `.lean` tree under a tmp
``LEAN_DOJO_CACHE_DIR``. A hard count assertion against the real ~131k-pair
mathlib4 checkout would be brittle (the checkout is an external download
that changes over time) -- see `scripts/build_lean3_align_map.py`'s module
docstring for that expectation recorded as documentation, not a test.

Imports both scripts as TOP-LEVEL modules (scripts/ added to sys.path),
matching tests/test_lean_harvest.py's existing convention for scripts/
modules that are not `pip install`ed.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import build_lean3_align_map as align_map  # noqa: E402
import build_lean3_repair_sft as repair  # noqa: E402

import smolbench.deduction.lean.corpus as corpus  # noqa: E402
from smolbench.deduction.lean import decontam, lean3  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lean_data_env(tmp_path, monkeypatch):
    """Point SMOLBENCH_LEAN_DATA at a fresh tmp dir with EMPTY eval splits.

    `decontam.HoldoutIndex.build()` (called by `build_lean3_repair_sft`'s
    `build`) loads `sft.DEFAULT_EVAL_SPECS` (``novel_premises`` val + test)
    via `corpus.load_split`, which raises `FileNotFoundError` if the split
    file is absent entirely -- these two empty-array files exist purely to
    satisfy that, giving an index with zero holdout content (so the
    decontamination gate never drops anything by ACCIDENT; the one test
    that needs a drop forces it via monkeypatching `HoldoutIndex.check`
    instead of real fixture content -- real novel_premises content is
    already covered by tests/test_lean_decontam.py).
    """
    data_dir = tmp_path / "data"
    (data_dir / "novel_premises").mkdir(parents=True)
    (data_dir / "novel_premises" / "val.json").write_text("[]")
    (data_dir / "novel_premises" / "test.json").write_text("[]")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(data_dir))
    corpus.reset_caches()
    yield data_dir
    corpus.reset_caches()


def _write_gzip_align_asset(path: Path, pairs: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump({"lean3_to_lean4": pairs}, f)


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _manifest_path(out: Path) -> Path:
    """Mirror build_lean3_repair_sft.build's own `out.stem + ".manifest.json"` naming."""
    return out.with_name(out.stem + ".manifest.json")


# ---------------------------------------------------------------------------
# build_lean3_align_map.py
# ---------------------------------------------------------------------------

#: Fake commit -- arbitrary, but must match between the fixture metadata.json
#: and the fixture cache checkout directory name (see `_write_fake_cache`).
_FAKE_COMMIT = "deadbeef00000000000000000000000000000000"

#: `Mathlib/A.lean` sorts before `Mathlib/B.lean` (plain lexical file-walk
#: order) -- `foo.bar`'s FIRST occurrence is here, so its value must win
#: over B.lean's later (duplicate-key) redefinition.
_FAKE_A_LEAN = (
    "#align foo.bar Foo.Bar\n"
    "#align foo.baz Foo.Baz -- has a trailing comment, still 3+ tokens\n"
    "#align_import mathlib.tactic.norm_num\n"
)
#: `foo.bar` here is a DUPLICATE key (dropped, counted); `#align badline`
#: has only 2 whitespace-split tokens (malformed, counted).
_FAKE_B_LEAN = "#align foo.bar Foo.BarDUP\n#align badline\n"


def _write_fake_cache(cache_dir: Path) -> Path:
    """Build the fake `<cache>/leanprover-community-mathlib4-<commit>/mathlib4/Mathlib/` tree."""
    checkout = cache_dir / f"leanprover-community-mathlib4-{_FAKE_COMMIT}" / "mathlib4"
    mathlib = checkout / "Mathlib"
    mathlib.mkdir(parents=True)
    (mathlib / "A.lean").write_text(_FAKE_A_LEAN)
    (mathlib / "B.lean").write_text(_FAKE_B_LEAN)
    return checkout


@pytest.fixture
def align_map_env(lean_data_env, tmp_path, monkeypatch):
    """`lean_data_env` (for the output asset location) + a fake LeanDojo cache."""
    (lean_data_env / "metadata.json").write_text(
        json.dumps({"dataset_name": "fake", "from_repo": {"url": "https://x", "commit": _FAKE_COMMIT}})
    )
    cache_dir = tmp_path / "cache"
    checkout = _write_fake_cache(cache_dir)
    monkeypatch.setenv("LEAN_DOJO_CACHE_DIR", str(cache_dir))
    return lean_data_env, checkout


def test_align_map_builder_scans_and_dedupes(align_map_env):
    data_dir, checkout = align_map_env
    rc = align_map.main([])
    assert rc == 0

    # Asset + manifest land BESIDE the (fixture) benchmark dir -- the
    # committed-sidecar layout (data_root().parent; see build_lean3_align_map.main).
    manifest = json.loads((data_dir.parent / "lean3_align.manifest.json").read_text())
    assert manifest["config"] == {"source_commit": _FAKE_COMMIT, "cache_path": str(checkout)}
    assert manifest["stats"] == {
        "files_scanned": 2,
        "align_lines": 4,
        "pairs": 2,
        "duplicate_lean3_keys": 1,
        "malformed_lines": 1,
    }
    # Accounting identity the module docstring promises.
    s = manifest["stats"]
    assert s["align_lines"] == s["pairs"] + s["duplicate_lean3_keys"] + s["malformed_lines"]

    asset_path = data_dir.parent / lean3.ALIGN_ASSET_NAME
    asset_bytes = asset_path.read_bytes()
    assert manifest["asset"] == {
        "name": lean3.ALIGN_ASSET_NAME,
        "sha256": hashlib.sha256(asset_bytes).hexdigest(),
        "bytes": len(asset_bytes),
    }

    loaded = lean3.AlignMap.load(asset_path)
    assert loaded is not None
    # First-occurrence-wins: A.lean's foo.bar, not B.lean's duplicate.
    assert loaded.lean3_to_lean4 == {"foo.bar": "Foo.Bar", "foo.baz": "Foo.Baz"}


def test_align_map_builder_byte_reproducible_across_runs(align_map_env):
    data_dir, _checkout = align_map_env
    assert align_map.main([]) == 0
    asset_path = data_dir.parent / lean3.ALIGN_ASSET_NAME
    manifest_path = data_dir.parent / "lean3_align.manifest.json"
    first_asset = asset_path.read_bytes()
    first_manifest = manifest_path.read_bytes()

    assert align_map.main([]) == 0
    second_asset = asset_path.read_bytes()
    second_manifest = manifest_path.read_bytes()

    # mtime=0 in the gzip header (see build_lean3_align_map._encode_asset)
    # is what makes this byte-for-byte, not just content-equal.
    assert first_asset == second_asset
    assert first_manifest == second_manifest


def test_align_map_builder_missing_checkout_exits_1(lean_data_env, monkeypatch, tmp_path):
    (lean_data_env / "metadata.json").write_text(
        json.dumps({"from_repo": {"commit": _FAKE_COMMIT}})
    )
    monkeypatch.setenv("LEAN_DOJO_CACHE_DIR", str(tmp_path / "empty_cache"))
    assert align_map.main([]) == 1


def test_align_map_builder_missing_metadata_exits_1(lean_data_env, monkeypatch, tmp_path):
    # No metadata.json written at all under lean_data_env.
    monkeypatch.setenv("LEAN_DOJO_CACHE_DIR", str(tmp_path / "cache"))
    assert align_map.main([]) == 1


# ---------------------------------------------------------------------------
# build_lean3_repair_sft.py
# ---------------------------------------------------------------------------

#: 3-pair fixture align map, including iSup_le (needed for row "Mini.simp1"'s
#: `rename` transform) -- mirrors tests/test_lean_lean3.py's FIXTURE_ALIGN
#: shape (a small, hand-picked subset) rather than reusing that module-level
#: constant directly (it is not exported for reuse; duplicating 3 pairs here
#: is simpler than importing a private test fixture cross-file).
_REPAIR_ALIGN_PAIRS = {
    "supr_le": "iSup_le",
    "finset.mem_univ": "Finset.mem_univ",
    "iso.inv_comp_eq": "Iso.inv_comp_eq",
}


def _src_row(full_name: str, k: int, assistant: str) -> dict:
    """One minimal rendered SFT row, shaped like scripts/build_lean_sft.py's output."""
    user = (
        "## Current goal\n```\n⊢ True\n```\n\n"
        "## Full tactic state\n```\n⊢ True\n```\n\nProve the goal."
    )
    return {
        "system": "SYSTEM PROMPT",
        "user": user,
        "assistant": assistant,
        "meta": {"full_name": full_name, "k": k, "n_tail": 1},
    }


#: 6 corruptible tails (one per corruption transform, plus a multi-mechanism
#: combo) + 2 genuinely uncorruptible tails (empty, and a single line that
#: already ends in a comma with no rfl/use/binder/renamable token -- see
#: corrupt_tail's own test suite in tests/test_lean_lean3.py for why a plain
#: nonempty single line is otherwise ALWAYS `trailing`-eligible).
_SOURCE_ROWS = [
    _src_row("Mini.rfl1", 1, "rfl"),
    _src_row("Mini.use1", 1, "use z"),
    _src_row("Mini.simp1", 1, "simp [iSup_le]"),
    _src_row("Mini.fun1", 1, "fun x ↦ x"),
    _src_row("Mini.trail1", 1, "apply foo"),
    _src_row("Mini.combo1", 2, "intro h\nrfl"),
    _src_row("Mini.empty1", 1, ""),
    _src_row("Mini.commaonly1", 1, "trivial,"),
]
_UNCORRUPTIBLE_NAMES = {"Mini.empty1", "Mini.commaonly1"}


@pytest.fixture
def repair_fixture(lean_data_env, tmp_path):
    """Write the fixture align asset + 8-row source JSONL; return their paths."""
    align_path = tmp_path / "align.json.gz"
    _write_gzip_align_asset(align_path, _REPAIR_ALIGN_PAIRS)

    dataset_path = tmp_path / "source.jsonl"
    with dataset_path.open("w", encoding="utf-8") as f:
        for row in _SOURCE_ROWS:
            f.write(json.dumps(row) + "\n")

    return {"align": align_path, "dataset": dataset_path, "out": tmp_path / "out.jsonl"}


def _run_repair(fixture, **overrides) -> int:
    args = {
        "--dataset": str(fixture["dataset"]),
        "--out": str(fixture["out"]),
        "--align": str(fixture["align"]),
        "--limit": "2",
        "--identity-frac": "1.0",
        "--seed": "1776",
    }
    args.update({k: str(v) for k, v in overrides.items()})
    argv = [x for pair in args.items() for x in pair]
    return repair.main(argv)


def test_repair_builder_missing_align_asset_exits_1(repair_fixture):
    missing = repair_fixture["align"].with_name("nope.json.gz")
    rc = _run_repair(repair_fixture, **{"--align": missing})
    assert rc == 1


def test_repair_builder_missing_dataset_exits_1(repair_fixture):
    missing = repair_fixture["dataset"].with_name("nope.jsonl")
    rc = _run_repair(repair_fixture, **{"--dataset": missing})
    assert rc == 1


def test_repair_builder_emits_corrupted_and_identity_rows(repair_fixture):
    """End-to-end pipeline: counts, template shape, byte-unchanged targets.

    `--limit 2` (fewer than the 6 corruptible source rows) guarantees phase
    1 stops before exhausting the dataset, leaving rows for phase 2; with
    `--identity-frac 1.0` (`identity_target = floor(2 * 1.0) = 2`) and only
    2 of the 8 rows being genuinely uncorruptible, at least 4 rows remain
    available to phase 2 regardless of priority-hash order -- see
    `repair_fixture`'s and `_SOURCE_ROWS`' docstrings for the by-hand
    worst-case trace this relies on.
    """
    rc = _run_repair(repair_fixture)
    assert rc == 0

    out_rows = _read_jsonl(repair_fixture["out"])
    manifest = json.loads(_manifest_path(repair_fixture["out"]).read_text())

    assert manifest["stats"]["corrupted_emitted"] == 2
    assert manifest["stats"]["identity_emitted"] == 2
    corrupted = [r for r in out_rows if r["meta"]["repair"]["identity"] is False]
    identity = [r for r in out_rows if r["meta"]["repair"]["identity"] is True]
    assert len(corrupted) == 2
    assert len(identity) == 2
    assert len(out_rows) == manifest["stats"]["corrupted_emitted"] + manifest["stats"]["identity_emitted"]

    by_name = {r["meta"]["full_name"]: r for r in _SOURCE_ROWS}
    for row in corrupted:
        assert "Lean reported:\n```\n" in row["user"]
        assert "## Previous attempt\n```lean\n" in row["user"]
        assert row["assistant"] == by_name[row["meta"]["full_name"]]["assistant"]
        assert "transforms" in row["meta"]["repair"] and row["meta"]["repair"]["transforms"]
        # None of the genuinely-uncorruptible tails could have survived
        # corrupt_tail to become a corrupted row.
        assert row["meta"]["full_name"] not in _UNCORRUPTIBLE_NAMES

    for row in identity:
        assert "Lean reported:" not in row["user"]
        assert "## Previous attempt\n```lean\n" in row["user"]
        assert row["assistant"] == by_name[row["meta"]["full_name"]]["assistant"]
        assert row["meta"]["repair"] == {"identity": True}
        # The identity attempt block IS the row's own tail, verbatim.
        assert f"```lean\n{row['assistant']}\n```" in row["user"]

    # No row appears in both phases.
    assert {r["meta"]["full_name"] for r in corrupted}.isdisjoint({r["meta"]["full_name"] for r in identity})

    # Manifest bookkeeping matches the artifact.
    assert manifest["stats"]["source_rows"] == 8
    assert manifest["output_jsonl"] == repair_fixture["out"].name
    assert manifest["decontamination"]["holdout_size"] == 0


def test_repair_builder_identity_rows_never_get_error_block(repair_fixture):
    rc = _run_repair(repair_fixture, **{"--limit": "1", "--identity-frac": "3.0"})
    assert rc == 0
    out_rows = _read_jsonl(repair_fixture["out"])
    for row in out_rows:
        if row["meta"]["repair"]["identity"]:
            assert "Lean reported:" not in row["user"]
        else:
            assert "Lean reported:" in row["user"]


def test_repair_builder_deterministic_across_runs(repair_fixture):
    # Same `--out` path both times (not a second path) -- the manifest's
    # `config.out`/`output_jsonl` fields legitimately embed that path, so
    # comparing two DIFFERENT output paths' manifests would always differ
    # there regardless of any other nondeterminism; re-running onto the
    # SAME path isolates the property under test (identical seeded content).
    rc1 = _run_repair(repair_fixture)
    bytes1 = repair_fixture["out"].read_bytes()
    manifest1 = _manifest_path(repair_fixture["out"]).read_bytes()

    rc2 = _run_repair(repair_fixture)
    bytes2 = repair_fixture["out"].read_bytes()
    manifest2 = _manifest_path(repair_fixture["out"]).read_bytes()

    assert rc1 == 0 and rc2 == 0
    assert bytes1 == bytes2
    assert manifest1 == manifest2


def test_decontam_drop_path_via_monkeypatched_check(repair_fixture, monkeypatch):
    """Force a holdout hit for one specific full_name; assert it is dropped + counted."""
    target = "Mini.rfl1"
    original_check = decontam.HoldoutIndex.check

    def fake_check(self, *, name=None, statement=None, states=(), tactics=(), pairs=()):
        if name == target:
            return [decontam.Hit(key="name", theorem=target, detail="forced by test")]
        return original_check(self, name=name, statement=statement, states=states, tactics=tactics, pairs=pairs)

    monkeypatch.setattr(decontam.HoldoutIndex, "check", fake_check)

    # limit >= the 6 corruptible rows so phase 1 scans the whole dataset
    # (including `target`, which is otherwise trivially corruptible via
    # rfl_to_refl) -- if the gate did NOT drop it, it would certainly
    # otherwise have been emitted.
    rc = _run_repair(repair_fixture, **{"--limit": "6", "--identity-frac": "0.0"})
    assert rc == 0

    out_rows = _read_jsonl(repair_fixture["out"])
    assert target not in {r["meta"]["full_name"] for r in out_rows}

    manifest = json.loads(_manifest_path(repair_fixture["out"]).read_text())
    assert manifest["stats"]["decontam_dropped"].get("name", 0) >= 1
    assert manifest["stats"]["decontam_dropped_total"] >= 1
    # The other 5 corruptible rows are unaffected by the forced hit.
    assert manifest["stats"]["corrupted_emitted"] == 5


def test_self_check_rejects_unreproducible_error_block():
    """The recorded error must equal synth_error(find_relics(attempt)).

    Regression pin for the 2026-07-12 review finding (adversarially
    confirmed 2-0): the first real build emitted 109 rows whose recorded
    `unknown identifier 'X'` named a VALID Lean 4 identifier, because the
    error was synthesized from `corrupt_tail`'s (then-uncorroborated)
    `injected` claims rather than from what the detector actually reports
    on the attempt. `_self_check` now recomputes the error from the
    re-extracted attempt text and aborts on any mismatch -- so a phantom
    claim can never reach the training set even if a future transform
    reintroduces the bookkeeping bug upstream.
    """
    align = lean3.AlignMap.from_pairs({"supr_le": "iSup_le"})
    src = {"system": "s", "user": "U", "assistant": "apply iSup_le"}
    attempt = "apply supr_le"
    good_error = lean3.synth_error(lean3.find_relics(attempt, align))
    good_row = {
        "system": "s",
        "user": lean3.build_repair_user("U", attempt, good_error),
        "assistant": "apply iSup_le",
        "meta": {"full_name": "T.good", "repair": {"identity": False, "transforms": ["lean3-name"]}},
    }
    repair._self_check([(good_row, src)], identity=False, align=align)  # must not raise

    bad_row = dict(good_row)
    bad_row["user"] = lean3.build_repair_user("U", attempt, "unknown identifier 'inv_inv'")
    bad_row["meta"] = {"full_name": "T.bad", "repair": {"identity": False, "transforms": ["lean3-name"]}}
    with pytest.raises(SystemExit):
        repair._self_check([(bad_row, src)], identity=False, align=align)


def test_self_check_rejects_error_block_on_identity_row():
    """Identity rows must never carry a fabricated 'Lean reported:' block --
    that would train on a false compiler claim about a correct attempt."""
    align = lean3.AlignMap.from_pairs({"supr_le": "iSup_le"})
    src = {"system": "s", "user": "U", "assistant": "rfl"}
    row = {
        "system": "s",
        "user": lean3.build_repair_user("U", "rfl", "<stdin>:1:1: unknown tactic"),
        "assistant": "rfl",
        "meta": {"full_name": "T.ident", "repair": {"identity": True, "transforms": []}},
    }
    with pytest.raises(SystemExit):
        repair._self_check([(row, src)], identity=True, align=align)
