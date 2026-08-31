import gzip
import json
import random

import pytest

from smolbench.deduction.lean.lean3 import (
    ALIGN_ASSET_NAME, AlignMap, Relic, build_repair_user, corrupt_tail,
    find_relics, has_relics, synth_error,
)

FIXTURE_ALIGN = AlignMap.from_pairs({
    "supr_le": "iSup_le", "category_theory.iso.inv_comp_eq": "Iso.inv_comp_eq",
    "finset.mem_univ": "Finset.mem_univ", "filter.prod_bot": "Filter.prod_bot",
    "linear_map.is_compl_of_proj": "LinearMap.isCompl_of_proj",
})


_UNKNOWN_TACTIC = "<stdin>:1:1: unknown tactic"
_UNEXPECTED_COMMA = "<stdin>:1:1: unexpected token ','; expected command"
_COORDINATION = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)
_GOLDEN = "USER TURN\n\n## Previous attempt\n```lean\nATTEMPT LINE\n```\n"


def _write_align(path, mapping):
    path.write_bytes(gzip.compress(json.dumps({"lean3_to_lean4": mapping}).encode()))


@pytest.mark.parametrize("text, expected_kinds", [
    pytest.param("exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩", set(), id="nested-comma-in-anglebrackets"),
    pytest.param("exact fun s hs ↦ x c ⟨s, hs⟩", set(), id="arrow-before-nested-comma"),
    pytest.param("rw [CategoryTheory.Limits.prod.leftUnitor_inv_naturality]", set(), id="lean4-name-snake-suffix"),
    pytest.param("simp [Iso.inv_comp_eq]", set(), id="already-lean4-name"),
    pytest.param("simp [inv_comp_eq]", set(), id="lean4-suffix-resolving-via-align-map"),
    pytest.param("exact le_refl x", set(), id="refl-not-in-head-position"),
    pytest.param("refine ⟨foo,\n  bar⟩", set(), id="trailing-comma-inside-open-bracket"),
    pytest.param("simp only [stdBasis_eq_pi_diag]", set(), id="snake-ish-with-no-align-hit"),
    pytest.param("λ _ s, x _ s", {"binder-comma"}, id="bare-lambda-comma-binder"),
    pytest.param("exact funext (λ i, eval_f i (finset.mem_univ _))", {"binder-comma", "lean3-name"}, id="lambda-comma-plus-lean3-name"),
    pytest.param("apply supr_le,", {"lean3-name", "trailing-comma"}, id="lean3-name-plus-trailing-comma"),
    pytest.param("existsi z", {"existsi"}, id="existsi-anywhere"),
    pytest.param("refl", {"refl"}, id="bare-refl-whole-line"),
    pytest.param("rw [x] <;> refl", {"refl"}, id="refl-after-semicolon-combinator"),
    pytest.param("rw [iso.inv_comp_eq]", {"lean3-name"}, id="lean3-name-via-unique-suffix"),
    pytest.param("intros f,", {"trailing-comma"}, id="trailing-comma-only"),
    pytest.param("begin\n  simp\nend", {"begin-end"}, id="begin-end-block"),
])
def test_find_relics(text, expected_kinds):
    assert {r.kind for r in find_relics(text, FIXTURE_ALIGN)} == expected_kinds
    assert has_relics(text, FIXTURE_ALIGN) is bool(expected_kinds)


def test_relic_fixes_dedup_and_no_align_map():
    assert [r.fix for r in find_relics("refl", FIXTURE_ALIGN) if r.kind == "refl"] == ["rfl"]
    assert [r.fix for r in find_relics("existsi z", FIXTURE_ALIGN) if r.kind == "existsi"] == ["use"]
    (name_relic,) = find_relics("rw [iso.inv_comp_eq]", FIXTURE_ALIGN)
    assert (name_relic.text, name_relic.fix) == ("iso.inv_comp_eq", "Iso.inv_comp_eq")
    assert len([r for r in find_relics("refl <;> refl", FIXTURE_ALIGN) if r.kind == "refl"]) == 1
    assert find_relics("apply supr_le,", None) == [
        Relic(kind="trailing-comma", text="apply supr_le,", fix="apply supr_le", line=0)]


@pytest.mark.parametrize(
    "tail", ["exact ⟨z, sq z⟩", "simp [iSup_le]\nrfl", "use z\nrfl", "exact rfl", "rfl"]
)
def test_corrupt_tail_invariants(tail):
    seen = set()
    for align in (None, FIXTURE_ALIGN):
        for seed in range(20):
            if (result := corrupt_tail(tail, random.Random(seed), align)) is None:
                continue
            corrupted, injected = result
            kinds = {r.kind for r in injected}
            detected = {r.kind for r in find_relics(corrupted, align)}
            assert detected and kinds <= detected
            seen |= kinds
            if tail == "rfl" and "refl" in kinds:
                assert corrupted.startswith("refl")
    if tail == "exact rfl":
        assert "refl" not in seen, "term-position rfl must not be rewritten"
    if tail == "rfl":
        assert "refl" in seen, "tactic-head rfl must still be reachable"
    fixed = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    assert fixed is not None and fixed == corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)


def test_corrupt_tail_single_seed_cases():
    assert [corrupt_tail("", random.Random(1776), a) for a in (None, FIXTURE_ALIGN)] == [None, None]
    corrupted, injected = corrupt_tail("norm_num", random.Random(1776), None)
    assert corrupted == "norm_num," and {r.kind for r in injected} == {"trailing-comma"}
    corrupted, injected = corrupt_tail("rw [Iso.inv_comp_eq]", random.Random(1776), FIXTURE_ALIGN)
    assert any(r.kind == "lean3-name" for r in injected)
    assert "iso.inv_comp_eq" in corrupted and "category_theory.iso.inv_comp_eq" not in corrupted


@pytest.mark.parametrize("pairs, tail, seeds, forbidden", [
    ({"inv_inv": "inv_inv", "supr_le": "iSup_le"}, "rw [inv_inv]", 20, None),
    ({"div_mul_cancel'": "div_mul_cancel"}, "rw [div_mul_cancel₀ _ hd]", 10, "div_mul_cancel'"),
])
def test_rename_never_injects_unmapped_names(pairs, tail, seeds, forbidden):
    align = AlignMap.from_pairs(pairs)
    if forbidden is not None:
        assert [r for r in find_relics(tail, align) if r.kind == "lean3-name"] == []
    for seed in range(seeds):
        if (result := corrupt_tail(tail, random.Random(seed), align)) is None:
            continue
        corrupted, injected = result
        assert all(r.kind != "lean3-name" for r in injected)
        assert {r.kind for r in injected} <= {r.kind for r in find_relics(corrupted, align)}
        if forbidden is not None:
            assert forbidden not in corrupted


@pytest.mark.parametrize("relic, expected", [
    (Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0), "unknown identifier 'supr_le'"),
    (Relic(kind="refl", text="refl", fix="rfl", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="existsi", text="existsi", fix="use", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="begin-end", text="begin", fix=None, line=0), _UNKNOWN_TACTIC),
    (Relic(kind="binder-comma", text="λ x,", fix=None, line=0), _UNEXPECTED_COMMA),
    (Relic(kind="trailing-comma", text="apply foo,", fix="apply foo", line=0), _UNEXPECTED_COMMA),
])
def test_synth_error_per_kind(relic, expected):
    assert synth_error([relic]) == expected


def test_synth_error_first_relic_only_and_empty_raises():
    relics = [Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0),
              Relic(kind="refl", text="refl", fix="rfl", line=1)]
    assert synth_error(relics) == "unknown identifier 'supr_le'"
    with pytest.raises(ValueError):
        synth_error([])


def test_build_repair_user_golden():
    assert build_repair_user("USER TURN", "ATTEMPT LINE") == _GOLDEN + _COORDINATION
    assert build_repair_user("USER TURN", "ATTEMPT LINE", error="unknown identifier 'supr_le'") == (
        _GOLDEN + "Lean reported:\n```\nunknown identifier 'supr_le'\n```\n\n" + _COORDINATION)


def test_align_map_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "leandojo_benchmark_4"))
    assert AlignMap.load() is None
    _write_align(tmp_path / ALIGN_ASSET_NAME,
                 {"supr_le": "iSup_le", "finset.mem_univ": "Finset.mem_univ"})
    loaded = AlignMap.load()
    assert loaded is not None
    for tok, want in [("supr_le", "iSup_le"), ("finset.mem_univ", "Finset.mem_univ"),
                      ("mem_univ", "Finset.mem_univ")]:
        assert loaded.lookup_lean3(tok) == want
    assert loaded.is_lean4_name("Finset.mem_univ") is loaded.is_lean4_name("mem_univ") is True
    assert loaded.reverse_unique == {"iSup_le": "supr_le", "Finset.mem_univ": "finset.mem_univ"}
    explicit = tmp_path / "custom_name.json.gz"
    _write_align(explicit, {"filter.prod_bot": "Filter.prod_bot"})
    assert AlignMap.load(explicit).lookup_lean3("filter.prod_bot") == "Filter.prod_bot"
