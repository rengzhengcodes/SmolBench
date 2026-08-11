"""Offline tests for smolbench.deduction.lean.corpus against a tiny committed fixture.

All tests point SMOLBENCH_LEAN_DATA at tests/fixtures/lean_mini/ (a hand-built
LeanDojo-Benchmark-4-shaped tree) and reset the corpus/premises lru_caches so
the loaders re-read from the fixture rather than any real dataset root.
"""

from pathlib import Path

import pytest

import smolbench.deduction.lean.corpus as corpus

FIXTURE = Path(__file__).parent / "fixtures" / "lean_mini"


@pytest.fixture
def lean_data(monkeypatch):
    """Repoint the dataset root at the fixture and clear memoized loaders."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    yield FIXTURE
    corpus.reset_caches()


def test_load_split_parses_both_theorems(lean_data):
    thms = corpus.load_split("random", "val")
    assert len(thms) == 2
    by_name = {t.full_name: t for t in thms}
    assert set(by_name) == {"Mini.theoremA", "Mini.theoremB"}

    a = by_name["Mini.theoremA"]
    assert a.file_path == "Mini/A.lean"
    assert a.url.endswith("mathlib4")
    assert a.commit == "fe4454af900584467d21f4fd4fe951d29d9332a7"
    assert a.start == (1, 1)
    assert len(a.traced_tactics) == 3
    assert a.has_proof
    # premises are sourced from annotated_tactic[1] (see corpus._from_json).
    assert [p["full_name"] for p in a.traced_tactics[2].premises] == [
        "Mini.premiseA",
        "Mini.premiseB",
    ]
    assert a.traced_tactics[0].premises == []
    assert "⊢" in a.traced_tactics[2].state_before
    assert a.traced_tactics[0].tactic == "intro h"

    b = by_name["Mini.theoremB"]
    assert len(b.traced_tactics) == 2
    assert b.traced_tactics[0].state_before.strip().startswith("⊢")


def test_iter_with_proof_filters(lean_data):
    names = [t.full_name for t in corpus.iter_with_proof("random", "val")]
    assert names == ["Mini.theoremA", "Mini.theoremB"]


def test_metadata_loads(lean_data):
    md = corpus.metadata()
    assert md["dataset_name"].startswith("LeanDojo Benchmark 4")


def test_replay_passing_path_under_data_parent(lean_data):
    p = corpus.replay_passing_path("random", "val")
    assert p.name == "replay_passing_random_val.jsonl"
    # Lands alongside the dataset dir (the data/ layout), not inside it.
    assert p.parent == corpus.data_root().parent
    assert p.parent == FIXTURE.parent


def test_data_root_env_override(lean_data):
    assert corpus.data_root() == FIXTURE


def test_data_root_default_anchoring(monkeypatch):
    """With no env override, data_root() is repo-anchored, never cwd-relative."""
    monkeypatch.delenv("SMOLBENCH_LEAN_DATA", raising=False)
    corpus.reset_caches()
    root = corpus.data_root()
    assert root.is_absolute()
    assert root.parts[-4:] == ("notebooks", "deduction", "data", "leandojo_benchmark_4")


# ---------------------------------------------------------------------------
# Sidecar resolution off data_root().parent -- teeth for the notebooks/lean ->
# notebooks/deduction relocation.
#
# These assert the resolved default paths EXIST on disk rather than only
# re-deriving the path arithmetic: all four sidecars are COMMITTED files
# (unlike leandojo_benchmark_4/ itself, which is wholesale-gitignored), so a
# checkout always has them and the existence check is a real gate. If
# data_root() still pointed at the retired notebooks/lean/data, every one of
# these paths would resolve to a nonexistent file and these tests fail --
# which is exactly the regression they exist to catch.
# ---------------------------------------------------------------------------


def test_replay_passing_sidecars_resolve_to_committed_files(monkeypatch):
    """The replay-passing sidecars follow data_root() to notebooks/deduction/data."""
    monkeypatch.delenv("SMOLBENCH_LEAN_DATA", raising=False)
    corpus.reset_caches()
    for split in ("val", "test"):
        p = corpus.replay_passing_path("novel_premises", split)
        assert p.parent.parts[-3:] == ("notebooks", "deduction", "data"), p
        assert p.exists(), f"committed sidecar missing at resolved path: {p}"


def test_align_asset_loads_from_relocated_data_dir(monkeypatch):
    """`lean3.AlignMap.load()` resolves its asset off `data_root().parent`.

    `load()` returns None (not an error) when the asset is absent, so a
    non-None result is the proof that the default resolution actually lands
    on the committed `lean3_align.json.gz` in its new home.
    """
    import smolbench.deduction.lean.lean3 as lean3

    monkeypatch.delenv("SMOLBENCH_LEAN_DATA", raising=False)
    corpus.reset_caches()

    expected = corpus.data_root().parent / lean3.ALIGN_ASSET_NAME
    assert expected.parent.parts[-3:] == ("notebooks", "deduction", "data"), expected
    assert expected.exists(), f"committed align asset missing at: {expected}"

    amap = lean3.AlignMap.load()
    assert amap is not None, "align asset did not load from its default path"
    assert amap.lean3_to_lean4, "align map loaded but is empty"
