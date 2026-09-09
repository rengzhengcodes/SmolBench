"""Tests parse-level Lean 3 relic detection and name-only negative controls.

Name-level detection stays absent because this tree has no on-disk rename map.
"""

import pytest

from smolbench.deduction.lean.lean3 import Relic, find_relics


@pytest.mark.parametrize("text, expected_kinds", [
    pytest.param("exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩", set(), id="nested-comma-in-anglebrackets"),
    pytest.param("exact fun s hs ↦ x c ⟨s, hs⟩", set(), id="arrow-before-nested-comma"),
    pytest.param("rw [CategoryTheory.Limits.prod.leftUnitor_inv_naturality]", set(), id="lean4-name-snake-suffix"),
    pytest.param("simp [Iso.inv_comp_eq]", set(), id="already-lean4-name"),
    pytest.param("simp [inv_comp_eq]", set(), id="bare-lean4-suffix"),
    pytest.param("exact le_refl x", set(), id="refl-not-in-head-position"),
    pytest.param("refine ⟨foo,\n  bar⟩", set(), id="trailing-comma-inside-open-bracket"),
    pytest.param("simp only [stdBasis_eq_pi_diag]", set(), id="snake-ish-identifier"),
    # Name-only Mathlib3 cases must stay clean under parse-level detection.
    pytest.param("rw [iso.inv_comp_eq]", set(), id="mathlib3-name-alone-is-clean"),
    pytest.param("exact funext (λ i, eval_f i (finset.mem_univ _))", {"binder-comma"}, id="mathlib3-name-only-its-binder-comma-counts"),
    pytest.param("apply supr_le,", {"trailing-comma"}, id="mathlib3-name-only-its-trailing-comma-counts"),
    pytest.param("λ _ s, x _ s", {"binder-comma"}, id="bare-lambda-comma-binder"),
    pytest.param("existsi z", {"existsi"}, id="existsi-anywhere"),
    pytest.param("refl", {"refl"}, id="bare-refl-whole-line"),
    pytest.param("rw [x] <;> refl", {"refl"}, id="refl-after-semicolon-combinator"),
    pytest.param("intros f,", {"trailing-comma"}, id="trailing-comma-only"),
    pytest.param("begin\n  simp\nend", {"begin-end"}, id="begin-end-block"),
])
def test_find_relics(text: str, expected_kinds: set[str]) -> None:
    assert {r.kind for r in find_relics(text)} == expected_kinds


def test_relic_fixes_and_dedup() -> None:
    assert [r.fix for r in find_relics("refl") if r.kind == "refl"] == ["rfl"]
    assert [r.fix for r in find_relics("existsi z") if r.kind == "existsi"] == ["use"]
    assert len([r for r in find_relics("refl <;> refl") if r.kind == "refl"]) == 1
    # The finding is the trailing comma, not the Mathlib3 lemma name.
    assert find_relics("apply supr_le,") == [
        Relic(kind="trailing-comma", text="apply supr_le,", fix="apply supr_le", line=0)]
