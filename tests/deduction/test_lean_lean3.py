"""Test smolbench.deduction.lean.lean3 (the detector and the corrupter).

Five sections: detection, corruption, synth_error, build_repair_user, AlignMap.load.
Only the AlignMap.load section sets SMOLBENCH_LEAN_DATA (its default-path branch).
"""

from __future__ import annotations

import gzip
import json
import random

import pytest

from smolbench.deduction.lean.lean3 import (
    ALIGN_ASSET_NAME,
    AlignMap,
    Relic,
    build_repair_user,
    corrupt_tail,
    find_relics,
    has_relics,
    synth_error,
)

FIXTURE_ALIGN = AlignMap.from_pairs(
    {
        "supr_le": "iSup_le",
        "category_theory.iso.inv_comp_eq": "Iso.inv_comp_eq",
        "finset.mem_univ": "Finset.mem_univ",
        "linear_map.is_compl_of_proj": "LinearMap.isCompl_of_proj",
        "filter.prod_bot": "Filter.prod_bot",
    }
)


# ---------------------------------------------------------------------------
# 1. Detection
# ---------------------------------------------------------------------------

CLEAN_CASES = [
    pytest.param("exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩", id="nested-comma-in-anglebrackets"),
    pytest.param("exact fun s hs ↦ x c ⟨s, hs⟩", id="arrow-before-nested-comma"),
    pytest.param("rw [CategoryTheory.Limits.prod.leftUnitor_inv_naturality]", id="lean4-name-snake-suffix"),
    pytest.param("simp [Iso.inv_comp_eq]", id="already-lean4-name"),
    pytest.param("exact le_refl x", id="refl-not-in-head-position"),
    pytest.param("refine ⟨foo,\n  bar⟩", id="trailing-comma-inside-open-bracket"),
    pytest.param("simp only [stdBasis_eq_pi_diag]", id="snake-ish-with-no-align-hit"),
]


@pytest.mark.parametrize("text", CLEAN_CASES)
def test_find_relics_clean_cases_produce_zero_relics(text):
    assert find_relics(text, FIXTURE_ALIGN) == []
    assert has_relics(text, FIXTURE_ALIGN) is False


FLAGGED_CASES = [
    pytest.param("λ _ s, x _ s", {"binder-comma"}, id="bare-lambda-comma-binder"),
    pytest.param("exact funext (λ i, eval_f i (finset.mem_univ _))", {"binder-comma", "lean3-name"}, id="lambda-comma-plus-lean3-name"),
    pytest.param("apply supr_le,", {"lean3-name", "trailing-comma"}, id="lean3-name-plus-trailing-comma"),
    pytest.param("existsi z", {"existsi"}, id="existsi-anywhere"),
    pytest.param("refl", {"refl"}, id="bare-refl-whole-line"),
    pytest.param("rw [x] <;> refl", {"refl"}, id="refl-after-semicolon-combinator"),
    pytest.param("rw [iso.inv_comp_eq]", {"lean3-name"}, id="lean3-name-via-unique-suffix"),
    pytest.param("intros f,", {"trailing-comma"}, id="trailing-comma-only"),
    pytest.param("begin\n  simp\nend", {"begin-end"}, id="begin-end-block"),
]


@pytest.mark.parametrize("text, expected_kinds", FLAGGED_CASES)
def test_find_relics_flagged_cases(text, expected_kinds):
    relics = find_relics(text, FIXTURE_ALIGN)
    assert {r.kind for r in relics} == expected_kinds
    assert has_relics(text, FIXTURE_ALIGN) is True


def test_relic_fixes_and_dedup():
    """Each relic kind carries its Lean 4 fix, and (kind, text, line) dedups."""
    assert [r.fix for r in find_relics("refl", FIXTURE_ALIGN) if r.kind == "refl"] == ["rfl"]
    assert [r.fix for r in find_relics("existsi z", FIXTURE_ALIGN) if r.kind == "existsi"] == ["use"]
    (name_relic,) = find_relics("rw [iso.inv_comp_eq]", FIXTURE_ALIGN)
    assert name_relic.text == "iso.inv_comp_eq"
    assert name_relic.fix == "Iso.inv_comp_eq"
    assert len([r for r in find_relics("refl <;> refl", FIXTURE_ALIGN) if r.kind == "refl"]) == 1


def test_lean3_name_disabled_without_align_map():
    """Rule 6 degrades to parse-level-only detection when align is None."""
    assert find_relics("apply supr_le,", None) == [
        Relic(kind="trailing-comma", text="apply supr_le,", fix="apply supr_le", line=0)
    ]


# ---------------------------------------------------------------------------
# 2. Corruption
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tail",
    ["exact ⟨z, sq z⟩", "simp [iSup_le]\nrfl", "use z\nrfl", "exact rfl", "rfl"],
)
def test_corrupt_tail_invariants(tail):
    """Every injected kind is independently detectable; refl only in tactic-head position."""
    saw_refl = False
    for align in (None, FIXTURE_ALIGN):
        for seed in range(20):
            result = corrupt_tail(tail, random.Random(seed), align)
            if result is None:
                continue
            corrupted, injected = result
            assert corrupted != tail
            detected = find_relics(corrupted, align)
            assert detected != []
            kinds = {r.kind for r in injected}
            assert kinds <= {r.kind for r in detected}
            if tail == "exact rfl":
                assert "refl" not in kinds, "term-position rfl must not be rewritten"
            if tail == "rfl" and "refl" in kinds:
                saw_refl = True
                assert corrupted.startswith("refl")
    if tail == "rfl":
        assert saw_refl, "tactic-head rfl must still be reachable"

    fixed = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    assert fixed is not None
    assert fixed == corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)


def test_corrupt_tail_edge_cases():
    """No applicable transform returns None; a lone depth-0 line takes a trailing comma."""
    assert corrupt_tail("", random.Random(1776), None) is None
    assert corrupt_tail("", random.Random(1776), FIXTURE_ALIGN) is None

    result = corrupt_tail("norm_num", random.Random(1776), None)
    assert result is not None
    corrupted, injected = result
    assert corrupted == "norm_num,"
    assert {r.kind for r in injected} == {"trailing-comma"}
    assert find_relics(corrupted, None) != []


def test_rename_truncates_to_token_component_count():
    """The injected lean3 name truncates to the token's own dotted arity."""
    result = corrupt_tail("rw [Iso.inv_comp_eq]", random.Random(1776), FIXTURE_ALIGN)
    assert result is not None
    corrupted, injected = result
    assert any(r.kind == "lean3-name" for r in injected)
    assert "iso.inv_comp_eq" in corrupted
    assert "category_theory.iso.inv_comp_eq" not in corrupted


def test_rename_skips_identity_align_pairs():
    """Identity ``#align`` pairs (``#align inv_inv inv_inv``) are never claimed as relics."""
    align = AlignMap.from_pairs({"inv_inv": "inv_inv", "supr_le": "iSup_le"})
    for seed in range(20):
        result = corrupt_tail("rw [inv_inv]", random.Random(seed), align)
        if result is None:
            continue
        corrupted, injected = result
        assert all(r.kind != "lean3-name" for r in injected)
        assert {r.kind for r in injected} <= {r.kind for r in find_relics(corrupted, align)}


def test_candidate_tokens_keep_subscript_digits_whole():
    """Identifiers ending in subscript digits (``div_mul_cancel₀``) tokenize whole."""
    align = AlignMap.from_pairs({"div_mul_cancel'": "div_mul_cancel"})
    tail = "rw [div_mul_cancel₀ _ hd]"
    assert [r for r in find_relics(tail, align) if r.kind == "lean3-name"] == []
    for seed in range(10):
        result = corrupt_tail(tail, random.Random(seed), align)
        if result is None:
            continue
        corrupted, injected = result
        assert all(r.kind != "lean3-name" for r in injected)
        assert "div_mul_cancel'" not in corrupted


# ---------------------------------------------------------------------------
# 3. synth_error
# ---------------------------------------------------------------------------

_UNKNOWN_TACTIC = "<stdin>:1:1: unknown tactic"
_UNEXPECTED_COMMA = "<stdin>:1:1: unexpected token ','; expected command"

SYNTH_ERROR_CASES = [
    (Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0), "unknown identifier 'supr_le'"),
    (Relic(kind="refl", text="refl", fix="rfl", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="existsi", text="existsi", fix="use", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="begin-end", text="begin", fix=None, line=0), _UNKNOWN_TACTIC),
    (Relic(kind="binder-comma", text="λ x,", fix=None, line=0), _UNEXPECTED_COMMA),
    (Relic(kind="trailing-comma", text="apply foo,", fix="apply foo", line=0), _UNEXPECTED_COMMA),
]


@pytest.mark.parametrize("relic, expected", SYNTH_ERROR_CASES)
def test_synth_error_per_kind(relic, expected):
    assert synth_error([relic]) == expected


def test_synth_error_first_relic_only_and_empty_raises():
    relics = [
        Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0),
        Relic(kind="refl", text="refl", fix="rfl", line=1),
    ]
    assert synth_error(relics) == "unknown identifier 'supr_le'"
    with pytest.raises(ValueError):
        synth_error([])


# ---------------------------------------------------------------------------
# 4. build_repair_user
# ---------------------------------------------------------------------------

_COORDINATION = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)


def test_build_repair_user_golden():
    """Golden repair template, with and without a Lean error block."""
    assert build_repair_user("USER TURN", "ATTEMPT LINE") == (
        "USER TURN\n\n## Previous attempt\n```lean\nATTEMPT LINE\n```\n" + _COORDINATION
    )
    assert build_repair_user(
        "USER TURN", "ATTEMPT LINE", error="unknown identifier 'supr_le'"
    ) == (
        "USER TURN\n\n## Previous attempt\n```lean\nATTEMPT LINE\n```\n"
        "Lean reported:\n```\nunknown identifier 'supr_le'\n```\n\n" + _COORDINATION
    )


# ---------------------------------------------------------------------------
# 5. AlignMap.load
# ---------------------------------------------------------------------------


def test_align_map_load_round_trip(tmp_path, monkeypatch):
    """A missing asset loads as None; the default path is data_root().parent."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "leandojo_benchmark_4"))
    assert AlignMap.load() is None

    with gzip.open(tmp_path / ALIGN_ASSET_NAME, "wt", encoding="utf-8") as f:
        json.dump(
            {"lean3_to_lean4": {"supr_le": "iSup_le", "finset.mem_univ": "Finset.mem_univ"}}, f
        )
    loaded = AlignMap.load()
    assert loaded is not None
    assert loaded.lookup_lean3("supr_le") == "iSup_le"
    assert loaded.lookup_lean3("finset.mem_univ") == "Finset.mem_univ"
    assert loaded.lookup_lean3("mem_univ") == "Finset.mem_univ"
    assert loaded.is_lean4_name("Finset.mem_univ") is True
    assert loaded.is_lean4_name("mem_univ") is True
    assert loaded.reverse_unique == {"iSup_le": "supr_le", "Finset.mem_univ": "finset.mem_univ"}

    explicit = tmp_path / "custom_name.json.gz"
    with gzip.open(explicit, "wt", encoding="utf-8") as f:
        json.dump({"lean3_to_lean4": {"filter.prod_bot": "Filter.prod_bot"}}, f)
    assert AlignMap.load(explicit).lookup_lean3("filter.prod_bot") == "Filter.prod_bot"
