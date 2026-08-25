"""Test smolbench.deduction.lean.decontam against the lean_mini fixture.

Each test plants one leak from a key family: K1 name, K2 exact or near
statement, K3 mid-proof state, or K4 chain, 3-gram, or (state, tactic)
pair. Each test checks that `HoldoutIndex.check` catches its leak, and
that clean rows and premise-name-only mentions pass.

The tests point SMOLBENCH_LEAN_DATA at the committed 2-theorem fixture,
the same fixture test_lean_sft.py uses.

Fixture cheat-sheet (tests/fixtures/lean_mini/random/val.json):
- Mini.theoremA: 3 tactics (``intro h``, ``simp``, ``exact Mini.premiseA
  h (Mini.premiseB n)``), step-0 state ``n : ℕ\\nhn : n > 0\\n⊢ P n → Q n``.
- Mini.theoremB: 2 tactics. This is a short proof, so it gives NO
  chain or 3-gram keys, only pair keys.
"""

from pathlib import Path

import pytest

import smolbench.deduction.lean.corpus as corpus
from smolbench.deduction.lean.decontam import HoldoutIndex, normalize_text, state_variants

FIXTURE = Path(__file__).parent / "fixtures" / "lean_mini"

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


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def test_normalize_collapses_whitespace_and_nfc():
    assert normalize_text("  a \n\n  b\tc ") == "a b c"
    # NFC: composed vs decomposed é collide.
    assert normalize_text("café") == normalize_text("café")


def test_normalize_canonicalizes_incidental_counters():
    # Metavariables, inaccessible-autoname suffixes, and universe params are
    # per-elaboration counters -- two traces of the SAME goal collide.
    assert normalize_text("⊢ ?m.248692 = ?m.99") == normalize_text("⊢ ?m.5 = ?m.6")
    assert normalize_text("inst✝⁶ : Field F") == normalize_text("inst✝ : Field F")
    assert normalize_text("F : Type u_1") == normalize_text("F : Type u")
    # A whole state that differs only in these counters canonicalizes equal.
    a = "K : Type u_1\ninst✝ : Field K\n⊢ ?m.100 ∈ ⊥"
    b = "K : Type u_7\ninst✝³ : Field K\n⊢ ?m.42 ∈ ⊥"
    assert normalize_text(a) == normalize_text(b)


def test_state_variants_full_and_goal_only():
    variants = state_variants(THEOREM_A_STMT)
    assert variants == ["n : ℕ hn : n > 0 ⊢ P n → Q n", "⊢ P n → Q n"]
    # A bare goal has no distinct goal-only variant.
    assert state_variants("⊢ 1 + 1 = 2") == ["⊢ 1 + 1 = 2"]


# ---------------------------------------------------------------------------
# Index construction
# ---------------------------------------------------------------------------


def test_index_stats_cover_both_theorems(index):
    s = index.stats()
    assert s["names"] == 2
    # theoremA's full step-0 state plus theoremB's (goal-only-form) state.
    # theoremA's bare "⊢ P n → Q n" goal variant is under the
    # _MIN_GOAL_KEY_CHARS gate: short generic goals identify nothing.
    assert s["statements"] == 2
    # Only theoremA (3 tactics) contributes chain/3-gram keys.
    assert s["chains"] == 1 and s["tactic_ngrams"] == 1
    # Every (step state variant, tactic) pair across both theorems.
    assert s["pairs"] > 0


# ---------------------------------------------------------------------------
# One planted leak per key family
# ---------------------------------------------------------------------------


def test_k1_name_hit(index):
    hits = index.check(name="Mini.theoremA")
    assert [h.key for h in hits] == ["name"]


def test_k2_exact_statement_hit_despite_reformatting(index):
    # Same statement, different whitespace/line structure -> still caught.
    hits = index.check(statement="n : ℕ\n  hn : n > 0\n\n⊢ P n  →  Q n")
    assert hits and hits[0].key == "statement" and hits[0].theorem == "Mini.theoremA"


def test_k2_short_goal_only_restatement_is_not_a_key(index):
    # Bare short goals recur across unrelated theorems (⊢ False, ⊢ a = b).
    # They are below _MIN_GOAL_KEY_CHARS, so they are deliberately NOT
    # indexed. Only the full state, or a long, identifying goal, drops a row.
    assert index.check(statement="⊢ P n → Q n") == []


def test_k2_long_goal_only_restatement_hit(index):
    long_goal = "⊢ ∀ (s t : Set F) (m : F ≃+* F), s ⊆ Set.range ↑m → s / t ⊆ Set.range ↑m"
    theorem = corpus.load_split("random", "val")[0]
    fake = corpus.BenchmarkTheorem(
        url=theorem.url,
        commit=theorem.commit,
        file_path="Mini/LongGoal.lean",
        full_name="Mini.longGoal",
        start=(1, 1),
        end=(1, 1),
        traced_tactics=[
            corpus.TracedTactic(
                tactic="simp",
                state_before=f"F : Type u_1\ninst : Field F\n{long_goal}",
                state_after="no goals",
                premises=[],
            )
        ],
    )
    index._add_theorem(fake)
    # A corpus row stating just the (identifying) goal, hypotheses stripped,
    # matches the stepk:0 variant of the eval statement.
    hits = index.check(statement=long_goal)
    assert hits and hits[0].key == "statement" and hits[0].theorem == "Mini.longGoal"


def test_k2_near_duplicate_alpha_rename_hit(index):
    # Rename one hypothesis on a statement long enough for shingle overlap
    # to survive the rename; index it as an extra statement first.
    long_stmt = (
        "F : Type u_1\ninst : Field F\ns t : Set F\nm : F ≃+* F\n"
        "hs : s ⊆ Set.range ↑m\nht : t ⊆ Set.range ↑m\n⊢ s / t ⊆ Set.range ↑m"
    )
    theorem = corpus.load_split("random", "val")[0]
    fake = corpus.BenchmarkTheorem(
        url=theorem.url,
        commit=theorem.commit,
        file_path="Mini/Long.lean",
        full_name="Mini.longStatement",
        start=(1, 1),
        end=(1, 1),
        traced_tactics=[
            corpus.TracedTactic(
                tactic="simp", state_before=long_stmt, state_after="no goals", premises=[]
            )
        ],
    )
    index._add_theorem(fake)
    # One renamed hypothesis: shingle overlap stays >= 0.85. A larger rename would sink
    # the Jaccard score below threshold on a statement this short. The goal-only exact
    # variant's job is to catch heavier rewrites.
    renamed = long_stmt.replace("hs :", "h1 :")
    hits = index.check(statement=renamed)
    assert hits and hits[0].key == "statement_near" and hits[0].theorem == "Mini.longStatement"


def test_k3_mid_proof_state_hit(index):
    hits = index.check(states=["n : ℕ\nh : P n\n⊢ R n"])
    assert hits and hits[0].key == "state" and hits[0].theorem == "Mini.theoremA"


def test_k3_statement_matching_a_step_state_hit(index):
    # A "statement" that equals a mid-proof eval state (state-shaped
    # corpora like LeanNavigator) is caught via the statement facet too.
    hits = index.check(statement=THEOREM_A_STEP2_STATE)
    assert hits and hits[0].key == "state"


def test_k4_full_chain_and_ngram_hit(index):
    hits = index.check(tactics=THEOREM_A_CHAIN)
    assert {h.key for h in hits} == {"chain", "tactic_ngram"}
    # The same 3 tactics embedded in a longer proof still trip the 3-gram.
    hits = index.check(tactics=["intro x"] + THEOREM_A_CHAIN + ["done"])
    assert any(h.key == "tactic_ngram" for h in hits)


def test_k4_pair_hit(index):
    hits = index.check(pairs=[(THEOREM_A_STEP2_STATE, "exact Mini.premiseA h (Mini.premiseB n)")])
    assert hits and hits[0].key == "pair" and hits[0].theorem == "Mini.theoremA"


# ---------------------------------------------------------------------------
# Clean rows pass
# ---------------------------------------------------------------------------


def test_clean_row_passes(index):
    hits = index.check(
        name="Other.lemma",
        statement="x y : ℤ\n⊢ x * y = y * x",
        states=["x y : ℤ\n⊢ x * y = y * x"],
        tactics=["ring_nf", "omega", "norm_num"],
        pairs=[("x y : ℤ\n⊢ x * y = y * x", "ring")],
    )
    assert hits == []


def test_short_generic_chains_do_not_hit(index):
    # theoremB's whole proof is 2 tactics, so it is deliberately NOT
    # chain-indexed. ``rfl`` alone, or with company, must never be a drop
    # key without its state. The pair key is what covers short proofs.
    assert index.check(tactics=["rfl"]) == []
    assert index.check(tactics=["rfl", "exact Mini.premiseA h"]) == []
    # But the pair (state, tactic) IS answer-conditional and does hit.
    hits = index.check(pairs=[("⊢ 1 + 1 = 2", "rfl")])
    assert hits and hits[0].key == "pair" and hits[0].theorem == "Mini.theoremB"


def test_name_mentions_counted_not_dropped(index):
    # Invoking an eval theorem as a premise inside a proof is report-only.
    text = "have h := Mini.theoremA x hx\nexact Mini.theoremA y hy"
    assert index.count_name_mentions(text) == 2
    # Identifier boundaries: primed/namespaced look-alikes don't count.
    assert index.count_name_mentions("Mini.theoremA' and Foo.Mini.theoremA") == 0
    # check() itself never drops on mentions.
    assert index.check(tactics=["exact Mini.theoremA h", "simp", "ring"]) == []
