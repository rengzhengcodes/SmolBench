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
# The near-duplicate stage: MEASURED, not asserted in a comment.
# ---------------------------------------------------------------------------

import random  # noqa: E402 -- section-local, keeps this block self-contained

import smolbench.deduction.lean.decontam as D  # noqa: E402

#: A statement long enough to shingle meaningfully, in the shape K2 indexes
#: (a step-0 `state_before`).
_LSH_BASE = ("n : \u2115\nhn : n > 0\nhab : a \u2264 b\nhbc : b \u2264 c\n"
             "\u22a2 \u2200 m : \u2115, m \u2264 n \u2192 P m \u2192 Q (m + n) \u2227 R (m * n)")

#: Fixed, because the MinHash permutation seed is fixed: this whole test is
#: deterministic, so the numbers below are a pin, not a sample with sampling
#: error.
_LSH_RNG_SEED = 20260905

#: What the HAND-ROLLED MinHash/LSH index this stage replaced scored on the
#: corpus below, measured before the swap: 152 candidates at exact Jaccard
#: >= 0.85, of which it detected 150, and zero false positives among the 688
#: below. The two it missed both sat at J = 0.8864, just above the decision
#: threshold, which is where 8x8 banding is weakest. The datasketch-backed
#: index reproduces every decision it made and additionally catches those two,
#: which is what `test_near_duplicate_decisions_are_reproduced_and_improved`
#: pins.
_OLD_INDEX_DETECTED, _N_ABOVE, _N_BELOW = 150, 152, 688


def _perturbed(rng, text, n_edits):
    """`text` with `n_edits` single-character substitutions -- an alpha-rename analogue."""
    out = text
    for _ in range(n_edits):
        i = rng.randrange(len(out))
        out = out[:i] + rng.choice("xyzuvw") + out[i + 1:]
    return out


def _index_one_statement(text):
    """A `HoldoutIndex` holding only `text`'s K2 statement variants.

    Built through the real `_add_theorem` on a synthetic one-tactic theorem,
    NOT by populating the index's internals by hand: the near-duplicate
    structures are `datasketch` objects now, and a test that reached into them
    would pin an implementation rather than the behaviour. Returns the index
    and the indexed variants' exact shingle sets, which are the ground truth
    the LSH stage is scored against.
    """
    idx = D.HoldoutIndex()
    idx._add_theorem(corpus.BenchmarkTheorem(
        url="https://github.com/leanprover-community/mathlib4", commit="0" * 40,
        file_path="Mini/Base.lean", full_name="Mini.base", start=(1, 1), end=(1, 1),
        traced_tactics=[corpus.TracedTactic(
            tactic="simp", state_before=text, state_after="no goals", premises=[])]))
    return idx, [D._shingles(v) for v in D._index_variants(text)]


def _decisions(idx, indexed):
    """Score the 840-candidate corpus: ``[(exact_jaccard, was_detected), ...]``.

    Ground truth is the exact shingle Jaccard, maximised over every (candidate
    variant, indexed variant) pair -- the same quantity `_near_statement`
    confirms against -- because `_index_variants` indexes more than one variant
    per statement and comparing against only the full normalized text would
    misattribute legitimate matches as false positives.
    """
    rng = random.Random(_LSH_RNG_SEED)
    out = []
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
            if hit is not None:
                assert hit.key == "statement_near", hit
            out.append((true_j, hit is not None))
    return out


def test_near_duplicate_decisions_are_reproduced_and_improved():
    """The datasketch index makes every decision the hand-rolled one made.

    This is the acceptance criterion for replacing a hand-rolled universal-hash
    MinHash + band-bucket dict with `datasketch`. The permutations are NOT the
    same family (datasketch seeds its own), so signature-level identity was
    never available; what had to be preserved is the DECISIONS, and the
    exact-Jaccard confirm behind the LSH is what makes that possible to state
    crisply:

    * PRECISION is exact by construction -- an under-threshold candidate can
      never be reported, however the banding surfaced it. Asserted at zero.
    * RECALL is the only thing that could regress, and it did not: 152/152 here
      against the old index's 150/152.

    Because the old index's misses were exactly the two candidates at
    J = 0.8864 and it detected every other above-threshold candidate,
    "detects all 152 with no false positives" is strictly stronger than
    "reproduces every decision the old index made" -- so the two assertions
    below cover the reproduction claim without needing the old vector on disk.
    """
    idx, indexed = _index_one_statement(_LSH_BASE)
    assert len(indexed) >= 1
    threshold = D._JACCARD_THRESHOLD
    decisions = _decisions(idx, indexed)

    above = [detected for true_j, detected in decisions if true_j >= threshold]
    below = [detected for true_j, detected in decisions if true_j < threshold]
    assert (len(above), len(below)) == (_N_ABOVE, _N_BELOW), (
        f"the corpus changed shape: {len(above)} above / {len(below)} below "
        f"threshold, expected {_N_ABOVE}/{_N_BELOW}"
    )
    assert sum(below) == 0, (
        f"{sum(below)} candidates below J={threshold} were reported; the "
        "exact-Jaccard confirm must reject every one"
    )
    assert sum(above) == _N_ABOVE, (
        f"recall on true near-duplicates fell to {sum(above)}/{_N_ABOVE}; the "
        f"hand-rolled index this replaced scored {_OLD_INDEX_DETECTED}/{_N_ABOVE}, "
        "so anything below that is a regression and anything below 152 loses a "
        "decision the replacement was measured to make"
    )


def test_the_lsh_banding_is_the_configured_one_not_an_optimised_one():
    """`MinHashLSH` must be built with explicit `params`, or it re-derives (b, r).

    Left at ``params=None`` it optimises the banding from the threshold and
    picks ``(b, r) == (4, 15)`` at these values -- which does not even cover
    all 64 signature slots -- silently discarding the 8x8 banding
    ``decontam_config.toml`` documents, with no error raised. Nothing else in
    this file would notice: the exact-Jaccard confirm keeps precision perfect
    either way, so the only symptom would be a quiet change in which
    near-duplicates ever become candidates.
    """
    from datasketch import MinHashLSH

    cfg = D._CONFIG.minhash
    optimised = MinHashLSH(threshold=cfg.jaccard_threshold, num_perm=cfg.num_perm)
    assert (optimised.b, optimised.r) != (cfg.bands, cfg.rows), (
        "datasketch's optimiser now happens to agree with the configured "
        "banding, so this test no longer proves `params` is being passed; "
        "assert on the index's own (b, r) instead"
    )
    built = D._new_stmt_lsh()
    assert (built.b, built.r) == (cfg.bands, cfg.rows)


def test_the_shingle_set_is_the_grams_themselves():
    """Shingles are the n-grams, not hashes of them -- one less collision surface.

    They used to be stored as 64-bit blake2b digests, to keep the sets cheap.
    Measured over the corpus above, the maximum absolute difference between the
    gram-string Jaccard and the blake2b-hash Jaccard was exactly 0.0, so
    dropping the hashing changed no decision. Pinned here because a future
    "optimisation" back to hashing would silently reintroduce that surface.
    """
    grams = D._shingles("abcdefg")
    assert grams == {"abcde", "bcdef", "cdefg"}
    assert all(isinstance(g, str) for g in grams)
    # Text shorter than the shingle width contributes itself as one shingle.
    assert D._shingles("ab") == {"ab"}
    assert D._shingles("") == frozenset()


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
