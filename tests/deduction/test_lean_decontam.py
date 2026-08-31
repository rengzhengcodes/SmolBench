"""Test smolbench.deduction.lean.decontam against the lean_mini fixture.

Fixture (tests/fixtures/lean_mini/random/val.json): Mini.theoremA has 3 tactics
(``intro h``, ``simp``, ``exact Mini.premiseA h (Mini.premiseB n)``); Mini.theoremB
has 2, too short for chain/3-gram keys, so it only gives pair keys.
"""
import pytest

import smolbench.deduction.lean.corpus as corpus
from smolbench.deduction.lean.decontam import HoldoutIndex, normalize_text, state_variants
from tests._paths import LEAN_MINI as FIXTURE

THEOREM_A_STMT = "n : ℕ\nhn : n > 0\n⊢ P n → Q n"
THEOREM_A_STEP2_STATE = "n : ℕ\nh : P n\n⊢ R n"
THEOREM_A_CHAIN = ["intro h", "simp", "exact Mini.premiseA h (Mini.premiseB n)"]


@pytest.fixture
def index(monkeypatch) -> HoldoutIndex:
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    idx = HoldoutIndex.build([("random", "val")])
    yield idx
    corpus.reset_caches()


def _add_fake(index, name, state):
    """Index one extra synthetic single-tactic theorem named `name` at `state`."""
    ref = corpus.load_split("random", "val")[0]
    tactic = corpus.TracedTactic(
        tactic="simp", state_before=state, state_after="no goals", premises=[])
    index._add_theorem(corpus.BenchmarkTheorem(
        url=ref.url, commit=ref.commit, file_path=f"Mini/{name}.lean",
        full_name=f"Mini.{name}", start=(1, 1), end=(1, 1), traced_tactics=[tactic]))


def test_normalization_and_variants():
    """normalize_text collapses whitespace/NFC and per-elaboration counters."""
    assert normalize_text("  a \n\n  b\tc ") == "a b c"
    assert normalize_text("caf\u00e9") == normalize_text("cafe\u0301")  # NFC vs NFD
    assert normalize_text("⊢ ?m.248692 = ?m.99") == normalize_text("⊢ ?m.5 = ?m.6")
    assert normalize_text("inst✝⁶ : Field F") == normalize_text("inst✝ : Field F")
    assert normalize_text("F : Type u_1") == normalize_text("F : Type u")
    a = "K : Type u_1\ninst✝ : Field K\n⊢ ?m.100 ∈ ⊥"
    b = "K : Type u_7\ninst✝³ : Field K\n⊢ ?m.42 ∈ ⊥"
    assert normalize_text(a) == normalize_text(b)
    assert state_variants(THEOREM_A_STMT) == [
        "n : ℕ hn : n > 0 ⊢ P n → Q n",
        "⊢ P n → Q n",
    ]
    assert state_variants("⊢ 1 + 1 = 2") == ["⊢ 1 + 1 = 2"]


def test_index_stats(index):
    """Only theoremA (3 tactics) contributes chain/3-gram keys."""
    s = index.stats()
    assert s["names"] == 2
    # theoremB's hypothesis-free "⊢ 1 + 1 = 2" is its own goal-only variant and
    # below `_MIN_GOAL_KEY_CHARS`, so it yields no statement/state key at all.
    assert s["statements"] == 1
    assert s["chains"] == 1 and s["tactic_ngrams"] == 1
    assert s["pairs"] > 0


def test_planted_leaks_by_key_family(index):
    """One planted leak per key family: K1 name, K2 statement, K3 state, K4 chain/pair."""
    assert [h.key for h in index.check(name="Mini.theoremA")] == ["name"]
    hits = index.check(statement="n : ℕ\n  hn : n > 0\n\n⊢ P n  →  Q n")
    assert hits and hits[0].key == "statement" and hits[0].theorem == "Mini.theoremA"
    hits = index.check(states=[THEOREM_A_STEP2_STATE])
    assert hits and hits[0].key == "state" and hits[0].theorem == "Mini.theoremA"
    hits = index.check(statement=THEOREM_A_STEP2_STATE)
    assert hits and hits[0].key == "state"
    assert {h.key for h in index.check(tactics=THEOREM_A_CHAIN)} == {"chain", "tactic_ngram"}
    hits = index.check(tactics=["intro x"] + THEOREM_A_CHAIN + ["done"])
    assert any(h.key == "tactic_ngram" for h in hits)
    hits = index.check(pairs=[(THEOREM_A_STEP2_STATE, "exact Mini.premiseA h (Mini.premiseB n)")])
    assert hits and hits[0].key == "pair" and hits[0].theorem == "Mini.theoremA"


def test_long_and_near_duplicate_statements(index):
    """Long goal-only and alpha-renamed restatements hit; short generic goals do not."""
    long_goal = "⊢ ∀ (s t : Set F) (m : F ≃+* F), s ⊆ Set.range ↑m → s / t ⊆ Set.range ↑m"
    _add_fake(index, "longGoal", f"F : Type u_1\ninst : Field F\n{long_goal}")
    hits = index.check(statement=long_goal)
    assert hits and hits[0].key == "statement" and hits[0].theorem == "Mini.longGoal"
    long_stmt = (
        "F : Type u_1\ninst : Field F\ns t : Set F\nm : F ≃+* F\n"
        "hs : s ⊆ Set.range ↑m\nht : t ⊆ Set.range ↑m\n⊢ s / t ⊆ Set.range ↑m"
    )
    _add_fake(index, "longStatement", long_stmt)
    hits = index.check(statement=long_stmt.replace("hs :", "h1 :"))
    assert hits and hits[0].key == "statement_near" and hits[0].theorem == "Mini.longStatement"
    assert index.check(statement="⊢ P n → Q n") == []
    # Hypothesis-free short goal: one variant, and the floor still drops it.
    assert index.check(statement="⊢ 1 + 1 = 2") == []
    assert index.check(states=["⊢ 1 + 1 = 2"]) == []


def test_clean_rows_and_mentions(index):
    """Unrelated rows, short generic chains and name mentions never drop a row."""
    assert index.check(
        name="Other.lemma",
        statement="x y : ℤ\n⊢ x * y = y * x",
        states=["x y : ℤ\n⊢ x * y = y * x"],
        tactics=["ring_nf", "omega", "norm_num"],
        pairs=[("x y : ℤ\n⊢ x * y = y * x", "ring")],
    ) == []
    assert index.check(tactics=["rfl"]) == []
    assert index.check(tactics=["rfl", "exact Mini.premiseA h"]) == []
    hits = index.check(pairs=[("⊢ 1 + 1 = 2", "rfl")])
    assert hits and hits[0].key == "pair" and hits[0].theorem == "Mini.theoremB"
    text = "have h := Mini.theoremA x hx\nexact Mini.theoremA y hy"
    assert index.count_name_mentions(text) == 2
    assert index.count_name_mentions("Mini.theoremA' and Foo.Mini.theoremA") == 0
    assert index.check(tactics=["exact Mini.theoremA h", "simp", "ring"]) == []
