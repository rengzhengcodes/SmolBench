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


# ---------------------------------------------------------------------------
# 13-30: the LSH stage's recall claim, measured instead of asserted in a comment
# ---------------------------------------------------------------------------

import random  # noqa: E402 -- section-local, keeps this block self-contained

import smolbench.deduction.lean.decontam as D  # noqa: E402

#: A statement long enough to shingle meaningfully, in the shape K2 indexes
#: (a step-0 `state_before`).
_LSH_BASE = ("n : ℕ\nhn : n > 0\nhab : a ≤ b\nhbc : b ≤ c\n"
             "⊢ ∀ m : ℕ, m ≤ n → P m → Q (m + n) ∧ R (m * n)")

#: Fixed, because `_PERM_SEED` is fixed: this whole test is deterministic, so
#: the numbers below are a pin, not a sample with sampling error.
_LSH_RNG_SEED = 20260905


def _perturbed(rng, text, n_edits):
    """`text` with `n_edits` single-character substitutions -- an alpha-rename analogue."""
    out = text
    for _ in range(n_edits):
        i = rng.randrange(len(out))
        out = out[:i] + rng.choice("xyzuvw") + out[i + 1:]
    return out


def _index_one_statement(text):
    """A `HoldoutIndex` holding only `text`'s K2 statement variants."""
    idx = D.HoldoutIndex()
    shingle_sets = []
    for vi, variant in enumerate(D._index_variants(text)):
        shingles = D._shingles(variant)
        sig = D._signature(shingles)
        key = ("Mini.base", vi)
        idx._stmt_shingles[key] = shingles
        shingle_sets.append(shingles)
        for band in range(D._BANDS):
            bucket = (band, sig[band * D._ROWS:(band + 1) * D._ROWS])
            idx._lsh.setdefault(bucket, []).append(key)
    return idx, shingle_sets


def test_lsh_near_duplicate_recall_and_precision():
    """13-30: measure the banded-LSH stage instead of asserting ~0.77 in a comment.

    `decontam` hand-rolls MinHash + 8x8 banded LSH and documents a candidate
    recall threshold of ``(1/8)**(1/8) ~= 0.77``, "below the 0.85 decision
    threshold, so true near-dups surface as candidates and are then confirmed
    by exact Jaccard (no false drops from LSH alone)". Nothing exercised that.

    840 synthetic near-duplicates of one statement, at edit distances spanning
    the whole similarity range. Ground truth is the exact shingle Jaccard,
    maximised over every (candidate variant, indexed variant) pair -- the same
    quantity `_near_statement` confirms against -- because `_index_variants`
    indexes more than one variant per statement and comparing against only the
    full normalized text misattributes legitimate matches as false positives.

    MEASURED on this corpus, deterministically (`_PERM_SEED` and the RNG seed
    are both fixed):

        true J >= 0.85 : 152 pairs, 150 detected -> recall 0.9868
        true J <  0.85 : 688 pairs,   0 reported -> no false positives

    The precision half is exact by construction (the exact-Jaccard confirm
    rejects every under-threshold candidate) and is asserted as zero. The
    recall half is probabilistic in the banding, so it is asserted against a
    floor with headroom rather than at 1.0 -- note this means the module's "no
    false drops from LSH alone" is optimistic: both misses sit at J = 0.8864,
    just above the decision threshold, which is exactly where 8x8 banding is
    weakest (~92% at J = 0.85, rising to ~99.98% at J = 0.95).
    """
    rng = random.Random(_LSH_RNG_SEED)
    idx, indexed = _index_one_statement(_LSH_BASE)
    assert len(indexed) >= 1

    n_above = n_below = detected = false_positives = 0
    for n_edits in range(0, 14):
        for _ in range(60):
            cand = _perturbed(rng, _LSH_BASE, n_edits)
            cand_variants = [D._shingles(v) for v in D._index_variants(cand)]
            true_j = max((D._jaccard(a, b) for a in cand_variants for b in indexed),
                         default=0.0)
            hit = None
            for v in D._index_variants(cand):
                hit = idx._near_statement(v)
                if hit is not None:
                    break
            if true_j >= D._JACCARD_THRESHOLD:
                n_above += 1
                detected += hit is not None
            else:
                n_below += 1
                false_positives += hit is not None

    assert n_above >= 100 and n_below >= 100, (
        f"the corpus must exercise both sides: {n_above} above / {n_below} below"
    )
    assert false_positives == 0, (
        f"{false_positives} candidates below J={D._JACCARD_THRESHOLD} were reported; "
        "the exact-Jaccard confirm must reject every one"
    )
    recall = detected / n_above
    assert recall >= 0.95, (
        f"LSH recall on true near-duplicates fell to {recall:.4f} "
        f"({detected}/{n_above}); measured 0.9868 when this test was written"
    )
    assert hit is None or hit.key == "statement_near"


# ---------------------------------------------------------------------------
# The holdout's default spec list comes from the corpus, not from a deleted
# module's literal.
# ---------------------------------------------------------------------------


def test_default_eval_specs_come_from_the_corpus(monkeypatch):
    """`HoldoutIndex.build()` with no arguments indexes `corpus.eval_split_specs()`.

    The default used to be `sft.DEFAULT_EVAL_SPECS` = ``novel_premises/{val,test}``,
    a split family the post-cutoff corpus this study now runs on does not have,
    so the no-argument default could only ever raise or hold out nothing. It is
    now resolved from the ACTIVE corpus at call time.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    try:
        assert corpus.eval_split_specs() == (("random", "val"),)
        default = HoldoutIndex.build()
        explicit = HoldoutIndex.build([("random", "val")])
        assert default.names == explicit.names == {"Mini.theoremA", "Mini.theoremB"}
        assert default.stats() == explicit.stats()
        # An explicitly empty list is honoured verbatim, never silently replaced
        # by the corpus default.
        assert HoldoutIndex.build([]).names == set()
    finally:
        corpus.reset_caches()


def test_decontam_does_not_import_the_deleted_sft_module():
    """The SFT-dataset builder is gone; `decontam` must not reach for it."""
    import smolbench.deduction.lean.decontam as decontam_module

    assert not hasattr(decontam_module, "DEFAULT_EVAL_SPECS")
    with pytest.raises(ModuleNotFoundError):
        __import__("smolbench.deduction.lean.sft")
