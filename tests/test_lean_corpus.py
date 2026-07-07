"""Offline tests for smolbench.lean.corpus against a tiny committed fixture.

All tests point SMOLBENCH_LEAN_DATA at tests/fixtures/lean_mini/ (a hand-built
LeanDojo-Benchmark-4-shaped tree) and reset the corpus/premises lru_caches so
the loaders re-read from the fixture rather than any real dataset root.
"""

from pathlib import Path

import pytest

import smolbench.lean.corpus as corpus

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
    assert root.parts[-4:] == ("notebooks", "lean", "data", "leandojo_benchmark_4")
