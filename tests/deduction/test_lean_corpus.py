"""Test smolbench.deduction.lean.corpus against the committed lean_mini fixture."""

import json
import shutil

import pytest

import smolbench.deduction.lean.corpus as corpus
from tests._paths import LEAN_MINI as FIXTURE, LEAN_MINI_POSTCUTOFF as POSTCUTOFF


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


def test_unbootstrapped_loaders_name_the_remedy(monkeypatch, tmp_path):
    """Every loader's FileNotFoundError names the missing file and the bootstrap doc."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path))
    corpus.reset_caches()
    for call in (lambda: corpus.load_split("random", "val"), corpus.metadata,
                 lambda: list(corpus.iter_replay_passing("random", "val"))):
        with pytest.raises(FileNotFoundError, match="not found"):
            call()
    corpus.reset_caches()


# ---------------------------------------------------------------------------
# Post-cutoff corpus contract (A1) and the traced-root commit filter (A4)
# ---------------------------------------------------------------------------

NEW_COMMIT = "2ca39e62989124794bd8405bb2e60805f63d37bc"
OLD_COMMIT = "69c8a067c87c2bb6ba583f03fbf46090564be370"


@pytest.fixture
def postcutoff_data(monkeypatch):
    """Repoint the dataset root at the POST-CUTOFF fixture and clear loaders."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(POSTCUTOFF))
    corpus.reset_caches()
    yield POSTCUTOFF
    corpus.reset_caches()


def _copy_fixture(tmp_path, src=None):
    """Copy a corpus fixture into `tmp_path` so a test can corrupt its metadata."""
    dest = tmp_path / "corpus_copy"
    shutil.copytree(src or POSTCUTOFF, dest)
    return dest


def test_postcutoff_metadata_reports_the_whole_block(postcutoff_data):
    """The block round-trips verbatim and every documented key is present."""
    block = corpus.postcutoff_metadata()
    assert block is not None
    assert set(block) == {"method", "new_commit", "new_commit_date", "old_commit",
                          "old_commit_date", "target_date", "n_new_decls",
                          "n_old_decls", "n_postcutoff_decls"}
    assert block["method"] == "name-set-difference"
    assert (block["new_commit"], block["old_commit"]) == (NEW_COMMIT, OLD_COMMIT)
    assert block["target_date"] == "2026-07-31"
    assert corpus.is_postcutoff_corpus() is True
    assert corpus.metadata()["from_repo"]["commit"] == NEW_COMMIT


def test_postcutoff_flag_is_read_off_every_theorem_row(postcutoff_data):
    """`BenchmarkTheorem.postcutoff` comes from the row, not from the metadata."""
    thms = corpus.load_split("random", "val")
    assert len(thms) == 2
    assert all(t.postcutoff is True for t in thms)


def test_absent_block_is_none_and_rows_default_to_not_postcutoff(lean_data):
    """The old (2024-03-24) corpus stays legal to load and reports itself honestly."""
    assert corpus.postcutoff_metadata() is None
    assert corpus.is_postcutoff_corpus() is False
    assert all(t.postcutoff is False for t in corpus.load_split("random", "val"))


def test_commit_mismatch_between_from_repo_and_block_raises(monkeypatch, tmp_path):
    """A corpus whose trace commit is not the block's `new_commit` is incoherent."""
    root = _copy_fixture(tmp_path)
    meta = json.loads((root / "metadata.json").read_text())
    meta["from_repo"]["commit"] = OLD_COMMIT
    (root / "metadata.json").write_text(json.dumps(meta, indent=2))
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(root))
    corpus.reset_caches()
    for call in (corpus.postcutoff_metadata, corpus.is_postcutoff_corpus):
        with pytest.raises(ValueError, match=NEW_COMMIT):
            call()
    corpus.reset_caches()


def _make_cache(home, *commits):
    """Build ``<home>/.cache/lean_dojo/leanprover-community-mathlib4-<c>/mathlib4`` dirs."""
    for commit in commits:
        (home / ".cache" / "lean_dojo" /
         f"leanprover-community-mathlib4-{commit}" / "mathlib4").mkdir(parents=True)


def test_traced_root_picks_the_cache_dir_matching_the_corpus_commit(
    postcutoff_data, monkeypatch, tmp_path
):
    """Two cached traces, and the WRONG one sorts first -- name order must not decide."""
    from smolbench.deduction.lean import premises

    decoy = "0" * 40
    assert decoy < NEW_COMMIT, "the decoy must sort BEFORE the real commit"
    monkeypatch.setenv("HOME", str(tmp_path))
    _make_cache(tmp_path, decoy, NEW_COMMIT)
    corpus.reset_caches()
    root = premises._traced_root()
    assert root is not None
    assert root.parent.name == f"leanprover-community-mathlib4-{NEW_COMMIT}"


def test_traced_root_is_none_when_no_cache_dir_matches(postcutoff_data, monkeypatch, tmp_path):
    """The pass-5 contract: None, never an exception, when the trace is absent."""
    from smolbench.deduction.lean import premises

    monkeypatch.setenv("HOME", str(tmp_path))
    _make_cache(tmp_path, "0" * 40, "f" * 40)
    corpus.reset_caches()
    assert premises._traced_root() is None
    corpus.reset_caches()


def test_traced_root_is_none_when_the_corpus_is_not_bootstrapped(monkeypatch, tmp_path):
    """No metadata.json means no commit to match on -- still None, still no raise."""
    from smolbench.deduction.lean import premises

    empty = tmp_path / "no_corpus"
    empty.mkdir()
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(empty))
    monkeypatch.setenv("HOME", str(tmp_path))
    _make_cache(tmp_path, NEW_COMMIT)
    corpus.reset_caches()
    assert premises._traced_root() is None
    corpus.reset_caches()
