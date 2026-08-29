"""Test smolbench.deduction.lean.corpus against the committed lean_mini fixture."""

import pytest

import smolbench.deduction.lean.corpus as corpus
from tests._paths import LEAN_MINI as FIXTURE


@pytest.fixture
def lean_data(monkeypatch):
    """Repoint the dataset root at the fixture and clear memoized loaders."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    yield FIXTURE
    corpus.reset_caches()


def test_load_split_parses_fixture(lean_data):
    """Both fixture theorems parse with provenance, tactics and premises."""
    thms = corpus.load_split("random", "val")
    assert len(thms) == 2
    by_name = {t.full_name: t for t in thms}
    assert set(by_name) == {"Mini.theoremA", "Mini.theoremB"}
    a, b = by_name["Mini.theoremA"], by_name["Mini.theoremB"]
    assert (a.file_path, a.commit, a.start) == (
        "Mini/A.lean", "fe4454af900584467d21f4fd4fe951d29d9332a7", (1, 1))
    assert a.url.endswith("mathlib4") and a.has_proof
    assert len(a.traced_tactics) == 3 and a.traced_tactics[0].tactic == "intro h"
    assert [p["full_name"] for p in a.traced_tactics[2].premises] == [
        "Mini.premiseA", "Mini.premiseB"]
    assert a.traced_tactics[0].premises == []
    assert "⊢" in a.traced_tactics[2].state_before
    assert len(b.traced_tactics) == 2
    assert b.traced_tactics[0].state_before.strip().startswith("⊢")
    assert [t.full_name for t in corpus.iter_with_proof("random", "val")] == [
        "Mini.theoremA", "Mini.theoremB"]
    assert corpus.metadata()["dataset_name"].startswith("LeanDojo Benchmark 4")


def test_path_layout(lean_data):
    """The env override sets data_root(); sidecars land alongside the dataset dir."""
    assert corpus.data_root() == FIXTURE
    p = corpus.replay_passing_path("random", "val")
    assert p.name == "replay_passing_random_val.jsonl"
    assert p.parent == corpus.data_root().parent == FIXTURE.parent


def test_data_root_default_is_repo_anchored(monkeypatch):
    """With no env override, data_root() is repo-anchored, never cwd-relative."""
    monkeypatch.delenv("SMOLBENCH_LEAN_DATA", raising=False)
    corpus.reset_caches()
    root = corpus.data_root()
    assert root.is_absolute()
    assert root.parts[-4:] == ("notebooks", "deduction", "data", "leandojo_benchmark_4")
