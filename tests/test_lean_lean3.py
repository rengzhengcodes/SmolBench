"""Offline tests for smolbench.deduction.lean.lean3 (detector + corrupter).

Structured in five parts, mirroring the module's own sections:

1. Detection (`find_relics` / `has_relics`) -- CLEAN and FLAGGED cases lifted
   verbatim from real pilot-eval outputs (see spec_a1_lean3_module.md), plus
   a dedup check.
2. Corruption (`corrupt_tail`) -- the shared-vocabulary post-condition
   (everything injected is independently detectable), determinism given a
   fixed seed, the "no applicable transform" contract, and the `rename`
   truncation rule.
3. `synth_error` -- one case per relic-kind message bucket, plus the
   empty-input error.
4. `build_repair_user` -- golden-string checks for the with-error and
   no-error coordination template.
5. `AlignMap.load` -- missing-asset -> None, and a round trip through a
   temp gzip JSON asset via the default `SMOLBENCH_LEAN_DATA`-relative path.

No LeanDojo dataset fixture is needed here (unlike test_lean_corpus.py /
test_lean_sft.py / test_lean_decontam.py) -- this module only touches
`corpus.data_root()` indirectly, inside `AlignMap.load`'s default-path
branch, so `SMOLBENCH_LEAN_DATA` is only set where that branch is exercised.
"""

from __future__ import annotations

import gzip
import json
import random
from pathlib import Path

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

#: Fixture align map used throughout, per spec_a1_lean3_module.md's exact
#: pairs (a mix of single-, double-, and triple-component lean3 names).
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
    pytest.param(
        "exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩",
        id="tuple-of-binders-comma-nested-in-anglebrackets",
    ),
    pytest.param(
        "exact fun s hs ↦ x c ⟨s, hs⟩",
        id="arrow-before-nested-comma",
    ),
    pytest.param(
        "rw [CategoryTheory.Limits.prod.leftUnitor_inv_naturality]",
        id="mixed-case-lean4-name-snake-suffix-does-not-resolve",
    ),
    pytest.param(
        "simp [Iso.inv_comp_eq]",
        id="already-lean4-name-is_lean4_name-guard",
    ),
    pytest.param(
        "exact le_refl x",
        id="refl-not-in-tactic-head-position",
    ),
    pytest.param(
        "refine ⟨foo,\n  bar⟩",
        id="multiline-trailing-comma-inside-open-bracket",
    ),
    pytest.param(
        "simp only [stdBasis_eq_pi_diag]",
        id="snake-ish-identifier-with-no-align-hit",
    ),
]


@pytest.mark.parametrize("text", CLEAN_CASES)
def test_find_relics_clean_cases_produce_zero_relics(text):
    assert find_relics(text, FIXTURE_ALIGN) == []
    assert has_relics(text, FIXTURE_ALIGN) is False


FLAGGED_CASES = [
    pytest.param("λ _ s, x _ s", {"binder-comma"}, id="bare-lambda-comma-binder"),
    pytest.param(
        "exact funext (λ i, eval_f i (finset.mem_univ _))",
        {"binder-comma", "lean3-name"},
        id="nested-lambda-comma-plus-lean3-name",
    ),
    pytest.param(
        "apply supr_le,",
        {"lean3-name", "trailing-comma"},
        id="lean3-name-plus-trailing-comma-same-line",
    ),
    pytest.param("existsi z", {"existsi"}, id="existsi-anywhere"),
    pytest.param("refl", {"refl"}, id="bare-refl-whole-line"),
    pytest.param("rw [x] <;> refl", {"refl"}, id="refl-after-semicolon-combinator"),
    pytest.param(
        "rw [iso.inv_comp_eq]",
        {"lean3-name"},
        id="lean3-name-via-unique-2component-suffix",
    ),
    pytest.param(
        "intros f,",
        {"trailing-comma"},
        id="trailing-comma-only-intros-is-valid-lean4",
    ),
    pytest.param("begin\n  simp\nend", {"begin-end"}, id="begin-end-block"),
]


@pytest.mark.parametrize("text, expected_kinds", FLAGGED_CASES)
def test_find_relics_flagged_cases(text, expected_kinds):
    relics = find_relics(text, FIXTURE_ALIGN)
    assert {r.kind for r in relics} == expected_kinds
    assert has_relics(text, FIXTURE_ALIGN) is True


def test_refl_fix_is_rfl():
    relics = find_relics("refl", FIXTURE_ALIGN)
    assert [r.fix for r in relics if r.kind == "refl"] == ["rfl"]


def test_existsi_fix_is_use():
    relics = find_relics("existsi z", FIXTURE_ALIGN)
    assert [r.fix for r in relics if r.kind == "existsi"] == ["use"]


def test_lean3_name_fix_resolves_via_unique_suffix():
    relics = find_relics("rw [iso.inv_comp_eq]", FIXTURE_ALIGN)
    (relic,) = relics
    assert relic.text == "iso.inv_comp_eq"
    assert relic.fix == "Iso.inv_comp_eq"


def test_lean3_name_disabled_without_align_map():
    # Rule 6 is skipped entirely when align=None -- graceful degradation to
    # parse-level-only detection (see the module docstring).
    assert find_relics("apply supr_le,", None) == [
        Relic(kind="trailing-comma", text="apply supr_le,", fix="apply supr_le", line=0)
    ]


def test_dedup_collapses_same_kind_text_line():
    # Two `refl` occurrences on the SAME line collapse to one Relic, per
    # the "one Relic per (kind, text, line)" dedup rule.
    relics = find_relics("refl <;> refl", FIXTURE_ALIGN)
    refl_relics = [r for r in relics if r.kind == "refl"]
    assert len(refl_relics) == 1


# ---------------------------------------------------------------------------
# 2. Corruption
# ---------------------------------------------------------------------------

CORRUPTION_TAILS = [
    "exact ⟨z, sq z⟩",
    "simp [iSup_le]\nrfl",
    "use z\nrfl",
]


@pytest.mark.parametrize("tail", CORRUPTION_TAILS)
def test_corrupt_tail_shared_vocabulary_invariant(tail):
    """corrupt_tail's output must always be independently re-detectable.

    Checks the three load-bearing properties in one pass: the corruption
    actually changed the text, the detector catches something in the
    result, and every kind `corrupt_tail` claims to have injected is a
    subset of what an independent `find_relics` call finds -- the
    "shared-vocabulary invariant" the module docstring is built around.
    """
    result = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    assert result is not None
    corrupted, injected = result

    assert corrupted != tail
    detected = find_relics(corrupted, FIXTURE_ALIGN)
    assert detected != []

    injected_kinds = {r.kind for r in injected}
    detected_kinds = {r.kind for r in detected}
    assert injected_kinds <= detected_kinds


@pytest.mark.parametrize("tail", CORRUPTION_TAILS)
def test_corrupt_tail_deterministic_given_seed(tail):
    result1 = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    result2 = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    assert result1 == result2


def test_corrupt_tail_no_applicable_transform_returns_none():
    # An empty tail has no rfl/fun-λ/use-prefix/renamable-token/eligible
    # line -- genuinely zero applicable transforms under all five rules.
    assert corrupt_tail("", random.Random(1776), None) is None
    assert corrupt_tail("", random.Random(1776), FIXTURE_ALIGN) is None


def test_corrupt_tail_trailing_is_broadly_applicable_norm_num():
    """Documents a deliberate reading of the `trailing` transform's scope.

    NOTE (design decision / spec deviation): spec_a1_lean3_module.md's
    "no applicable transform" example names `tail="norm_num"` with
    `align=None`. Under the `trailing` transform's literal definition
    ("append `,` to a seeded non-empty subset of depth-0 line ends"),
    `norm_num` is a single non-comma-ending depth-0 line and so IS
    eligible: `trailing` corrupts it to `norm_num,`, which `find_relics`
    correctly flags as `trailing-comma`. `trailing`'s applicability is
    therefore intentionally NOT gated on any of the other four transforms
    also being available -- gating it that way isn't stated anywhere in
    the corruption-transform rules and would make `trailing` inconsistent
    with the OTHER required property (`exact ⟨z, sq z⟩` above has no rfl,
    no fun/λ, no `use ` line, and -- with the fixture align map -- no
    renamable token either; `trailing` is its ONLY possible mechanism, and
    it MUST succeed for that case per the spec's corruption-properties
    test). `tail=""` (see the test above) is used as the genuinely
    zero-applicable-transforms case instead; this test pins the resulting,
    intentionally-broader `trailing` behavior so the deviation is explicit
    and verified rather than silently diverging from the written example.
    """
    result = corrupt_tail("norm_num", random.Random(1776), None)
    assert result is not None
    corrupted, injected = result
    assert corrupted == "norm_num,"
    assert {r.kind for r in injected} == {"trailing-comma"}
    assert find_relics(corrupted, None) != []


def test_rename_truncates_to_token_component_count():
    """rename must truncate the lean3 replacement to the token's own arity.

    `Iso.inv_comp_eq` (2 dotted components) resolves via
    `reverse_unique` to the FULL 3-component lean3 name
    `category_theory.iso.inv_comp_eq`; the injected text must be truncated
    to the last 2 components (`iso.inv_comp_eq`), never the full name.
    """
    tail = "rw [Iso.inv_comp_eq]"
    result = corrupt_tail(tail, random.Random(1776), FIXTURE_ALIGN)
    assert result is not None
    corrupted, injected = result
    assert any(r.kind == "lean3-name" for r in injected)
    assert "iso.inv_comp_eq" in corrupted
    assert "category_theory.iso.inv_comp_eq" not in corrupted


def test_rename_applicability_requires_align():
    # `rename` needs `align.reverse_unique`; without an align map it can
    # never be the chosen transform (`_rename_applicable` always False),
    # regardless of how many potentially-renamable tokens are present.
    # `trailing` remains applicable to this tail either way (see
    # test_corrupt_tail_trailing_is_broadly_applicable_norm_num), so
    # corrupt_tail still succeeds -- but never via a `lean3-name` injection.
    tail = "exact Iso.inv_comp_eq"
    for seed in range(1776, 1776 + 20):
        result = corrupt_tail(tail, random.Random(seed), None)
        assert result is None or all(r.kind != "lean3-name" for r in result[1])


def test_rfl_transform_never_targets_term_position_rfl():
    """Regression: 2026-07-12 review finding (adversarially confirmed 2-0).

    `exact rfl` holds `rfl` in TERM position; rewriting it to `refl` would
    produce `exact refl`, which `find_relics` rule 2 deliberately does NOT
    flag (only tactic-head `refl` is a relic). The unrestricted rewrite
    therefore injected a phantom `refl` relic the detector could never
    corroborate -- mis-classing `synth_error` for the repair dataset. The
    transform is now gated on the same head-position predicate as rule 2,
    and `corrupt_tail`'s post-condition corroborates every claimed kind, so
    across any seed and either align setting no result may claim `refl`
    here, and the subset invariant must hold unconditionally.
    """
    for align in (None, FIXTURE_ALIGN):
        for seed in range(0, 20):
            result = corrupt_tail("exact rfl", random.Random(seed), align)
            if result is None:
                continue
            corrupted, injected = result
            assert all(r.kind != "refl" for r in injected)
            detected_kinds = {r.kind for r in find_relics(corrupted, align)}
            assert {r.kind for r in injected} <= detected_kinds


def test_rfl_transform_still_targets_tactic_head_rfl():
    """The head-position gate must not disable the transform where it IS
    detectable: a bare `rfl` line is tactic-head, so some seeds corrupt it
    to `refl` and the detector re-reports the injected relic."""
    saw_refl = False
    for seed in range(0, 20):
        result = corrupt_tail("rfl", random.Random(seed), None)
        assert result is not None  # rfl_to_refl and trailing both applicable
        corrupted, injected = result
        kinds = {r.kind for r in injected}
        assert kinds <= {r.kind for r in find_relics(corrupted, None)}
        if "refl" in kinds:
            saw_refl = True
            assert corrupted.startswith("refl")
    assert saw_refl


def test_rename_skips_identity_align_pairs():
    """Regression: 2026-07-12 review finding (adversarially confirmed 2-0).

    mathlib4 carries ~8k identity `#align` pairs (``#align inv_inv
    inv_inv``) whose "rename" is a byte-level no-op; the transform used to
    claim a `lean3-name` relic for them anyway, which downstream
    `synth_error` turned into a false ``unknown identifier 'inv_inv'``
    about a perfectly valid Lean 4 name (109/1600 rows of the first real
    dataset build). `_rename_candidates` now drops identity pairs (and any
    replacement rule 6 would not re-flag), so no seed may claim a
    `lean3-name` injection for this tail.
    """
    align = AlignMap.from_pairs({"inv_inv": "inv_inv", "supr_le": "iSup_le"})
    for seed in range(0, 20):
        result = corrupt_tail("rw [inv_inv]", random.Random(seed), align)
        if result is None:
            continue
        corrupted, injected = result
        assert all(r.kind != "lean3-name" for r in injected)
        assert {r.kind for r in injected} <= {r.kind for r in find_relics(corrupted, align)}


# ---------------------------------------------------------------------------
# 3. synth_error
# ---------------------------------------------------------------------------

SYNTH_ERROR_CASES = [
    pytest.param(
        Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0),
        "unknown identifier 'supr_le'",
        id="lean3-name",
    ),
    pytest.param(
        Relic(kind="refl", text="refl", fix="rfl", line=0),
        "<stdin>:1:1: unknown tactic",
        id="refl",
    ),
    pytest.param(
        Relic(kind="existsi", text="existsi", fix="use", line=0),
        "<stdin>:1:1: unknown tactic",
        id="existsi",
    ),
    pytest.param(
        Relic(kind="begin-end", text="begin", fix=None, line=0),
        "<stdin>:1:1: unknown tactic",
        id="begin-end",
    ),
    pytest.param(
        Relic(kind="binder-comma", text="λ x,", fix=None, line=0),
        "<stdin>:1:1: unexpected token ','; expected command",
        id="binder-comma",
    ),
    pytest.param(
        Relic(kind="trailing-comma", text="apply foo,", fix="apply foo", line=0),
        "<stdin>:1:1: unexpected token ','; expected command",
        id="trailing-comma",
    ),
]


@pytest.mark.parametrize("relic, expected", SYNTH_ERROR_CASES)
def test_synth_error_per_kind(relic, expected):
    assert synth_error([relic]) == expected


def test_synth_error_uses_only_first_relic():
    relics = [
        Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0),
        Relic(kind="refl", text="refl", fix="rfl", line=1),
    ]
    assert synth_error(relics) == "unknown identifier 'supr_le'"


def test_synth_error_raises_on_empty_list():
    with pytest.raises(ValueError):
        synth_error([])


# ---------------------------------------------------------------------------
# 4. build_repair_user
# ---------------------------------------------------------------------------


def test_build_repair_user_no_error_golden_string():
    got = build_repair_user("USER TURN", "ATTEMPT LINE")
    expected = (
        "USER TURN\n"
        "\n"
        "## Previous attempt\n"
        "```lean\n"
        "ATTEMPT LINE\n"
        "```\n"
        "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
        "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
        "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
    )
    assert got == expected


def test_build_repair_user_with_error_golden_string():
    got = build_repair_user("USER TURN", "ATTEMPT LINE", error="unknown identifier 'supr_le'")
    expected = (
        "USER TURN\n"
        "\n"
        "## Previous attempt\n"
        "```lean\n"
        "ATTEMPT LINE\n"
        "```\n"
        "Lean reported:\n"
        "```\n"
        "unknown identifier 'supr_le'\n"
        "```\n"
        "\n"
        "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
        "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
        "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
    )
    assert got == expected


# ---------------------------------------------------------------------------
# 5. AlignMap.load
# ---------------------------------------------------------------------------


def test_align_map_load_returns_none_when_asset_missing(tmp_path, monkeypatch):
    # The default path is data_root().parent / ALIGN_ASSET_NAME (the
    # committed-sidecar layout), so point the data root at a SUBDIR of the
    # empty tmp dir -- load() then resolves to tmp_path itself, which holds
    # no asset.
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "leandojo_benchmark_4"))
    assert AlignMap.load() is None


def test_align_map_load_round_trips_and_resolves_lookups(tmp_path, monkeypatch):
    # Mirror the real layout: SMOLBENCH_LEAN_DATA names the benchmark dir,
    # the asset sits BESIDE it (data_root().parent -- see AlignMap.load).
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "leandojo_benchmark_4"))
    asset_path = tmp_path / ALIGN_ASSET_NAME
    with gzip.open(asset_path, "wt", encoding="utf-8") as f:
        json.dump({"lean3_to_lean4": {"supr_le": "iSup_le", "finset.mem_univ": "Finset.mem_univ"}}, f)

    loaded = AlignMap.load()
    assert loaded is not None
    assert loaded.lookup_lean3("supr_le") == "iSup_le"
    assert loaded.lookup_lean3("finset.mem_univ") == "Finset.mem_univ"
    assert loaded.lookup_lean3("mem_univ") == "Finset.mem_univ"  # unique 1-component suffix
    assert loaded.is_lean4_name("Finset.mem_univ") is True
    assert loaded.is_lean4_name("mem_univ") is True  # component-boundary suffix
    assert loaded.reverse_unique == {"iSup_le": "supr_le", "Finset.mem_univ": "finset.mem_univ"}


def test_align_map_load_explicit_path(tmp_path):
    asset_path = tmp_path / "custom_name.json.gz"
    with gzip.open(asset_path, "wt", encoding="utf-8") as f:
        json.dump({"lean3_to_lean4": {"filter.prod_bot": "Filter.prod_bot"}}, f)

    loaded = AlignMap.load(asset_path)
    assert loaded is not None
    assert loaded.lookup_lean3("filter.prod_bot") == "Filter.prod_bot"


def test_align_map_from_pairs_is_independent_of_caller_dict():
    pairs = {"supr_le": "iSup_le"}
    align = AlignMap.from_pairs(pairs)
    pairs["supr_le"] = "MUTATED"
    assert align.lean3_to_lean4["supr_le"] == "iSup_le"


def test_candidate_tokens_keep_subscript_digits_whole():
    """Regression: identifiers ending in subscript digits (`div_mul_cancel₀`)
    must tokenize WHOLE. Before ₀-₉ (U+2080-2089) joined `_CANDIDATE_RE`,
    the tokenizer cut at the subscript, so `rename` could rewrite the
    alphabetic stem of a longer identifier and strand the subscript --
    producing a token that was neither the Lean3 nor the Lean4 spelling of
    anything (observed in the first real dataset build as
    `div_mul_cancel'₀`). With the whole token visible, an align map that
    has no entry for it yields no rename candidate at all."""
    align = AlignMap.from_pairs({"div_mul_cancel'": "div_mul_cancel"})
    tail = "rw [div_mul_cancel₀ _ hd]"
    # Detection: the whole token `div_mul_cancel₀` has no align entry, and
    # its stem must NOT be matched piecewise.
    assert [r for r in find_relics(tail, align) if r.kind == "lean3-name"] == []
    # Corruption: rename must find no candidate in this tail (any corruption
    # that does occur must come from other transforms and stay corroborated).
    for seed in range(0, 10):
        result = corrupt_tail(tail, random.Random(seed), align)
        if result is None:
            continue
        corrupted, injected = result
        assert all(r.kind != "lean3-name" for r in injected)
        assert "div_mul_cancel'" not in corrupted
