"""Test smolbench.deduction.lean.lean3, whose detection is now PARSE-LEVEL only.

The module used to carry a second, name-level rule (mathlib3 lemma names the
mathlib4 port renamed) resolved through a Lean 3 <-> Lean 4 declaration-name map,
plus a matching corrupter transform. That map's on-disk asset was never built
anywhere in this tree, so the rule was inert on every machine; both were removed
and the tests that existed only for them went with them. What remains here is
the surviving contract:

* the five parse-level relic kinds `find_relics` reports, with the mathlib3-name
  cases kept as NEGATIVE controls (a lemma name alone must now be reported as
  clean, not merely undetected by accident);
* `corrupt_tail`'s shared-vocabulary invariant and its determinism;
* `synth_error` and `build_repair_user`'s frozen byte-level output.
"""

import random

import pytest

from smolbench.deduction.lean.lean3 import (
    Relic, build_repair_user, corrupt_tail, find_relics, has_relics, synth_error,
)

_UNKNOWN_TACTIC = "<stdin>:1:1: unknown tactic"
_UNEXPECTED_COMMA = "<stdin>:1:1: unexpected token ','; expected command"
_COORDINATION = (
    "The attempt above may use Lean 3 syntax or lemma names that Lean 4 / Mathlib 4\n"
    "rejects. If it is already valid Lean 4, output it unchanged; otherwise output the\n"
    "corrected Lean 4 tactics. Output only the tactic lines, nothing else."
)
_GOLDEN = "USER TURN\n\n## Previous attempt\n```lean\nATTEMPT LINE\n```\n"


@pytest.mark.parametrize("text, expected_kinds", [
    pytest.param("exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩", set(), id="nested-comma-in-anglebrackets"),
    pytest.param("exact fun s hs ↦ x c ⟨s, hs⟩", set(), id="arrow-before-nested-comma"),
    pytest.param("rw [CategoryTheory.Limits.prod.leftUnitor_inv_naturality]", set(), id="lean4-name-snake-suffix"),
    pytest.param("simp [Iso.inv_comp_eq]", set(), id="already-lean4-name"),
    pytest.param("simp [inv_comp_eq]", set(), id="bare-lean4-suffix"),
    pytest.param("exact le_refl x", set(), id="refl-not-in-head-position"),
    pytest.param("refine ⟨foo,\n  bar⟩", set(), id="trailing-comma-inside-open-bracket"),
    pytest.param("simp only [stdBasis_eq_pi_diag]", set(), id="snake-ish-identifier"),
    # Negative controls for the REMOVED name-level rule: a mathlib3 lemma name
    # carries no parse-level relic, so a syntactically clean line holding one is
    # now reported clean. Were that rule ever reintroduced, these flip and this
    # file says so at the point of the change.
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
def test_find_relics(text, expected_kinds):
    assert {r.kind for r in find_relics(text)} == expected_kinds
    assert has_relics(text) is bool(expected_kinds)


def test_relic_fixes_and_dedup():
    assert [r.fix for r in find_relics("refl") if r.kind == "refl"] == ["rfl"]
    assert [r.fix for r in find_relics("existsi z") if r.kind == "existsi"] == ["use"]
    # One relic per line, not one per occurrence.
    assert len([r for r in find_relics("refl <;> refl") if r.kind == "refl"]) == 1
    # A mathlib3 lemma name contributes nothing of its own: the whole finding is
    # the trailing comma.
    assert find_relics("apply supr_le,") == [
        Relic(kind="trailing-comma", text="apply supr_le,", fix="apply supr_le", line=0)]


@pytest.mark.parametrize(
    "tail", ["exact ⟨z, sq z⟩", "simp [iSup_le]\nrfl", "use z\nrfl", "exact rfl", "rfl"]
)
def test_corrupt_tail_invariants(tail):
    """The shared-vocabulary invariant: every injected kind is re-detected."""
    seen = set()
    for seed in range(20):
        if (result := corrupt_tail(tail, random.Random(seed))) is None:
            continue
        corrupted, injected = result
        kinds = {r.kind for r in injected}
        detected = {r.kind for r in find_relics(corrupted)}
        assert detected and kinds <= detected
        seen |= kinds
        if tail == "rfl" and "refl" in kinds:
            assert corrupted.startswith("refl")
    if tail == "exact rfl":
        assert "refl" not in seen, "term-position rfl must not be rewritten"
    if tail == "rfl":
        assert "refl" in seen, "tactic-head rfl must still be reachable"
    # Determinism: `rng` is the only randomness source.
    fixed = corrupt_tail(tail, random.Random(1776))
    assert fixed is not None and fixed == corrupt_tail(tail, random.Random(1776))


def test_corrupt_tail_single_seed_cases():
    """Seed pins.

    These are implementation artifacts of the seeded transform draw, kept as a
    regression tripwire: an unannounced change to `_TRANSFORMS`' membership or
    order silently re-shuffles every repair dataset built from this module.
    """
    assert corrupt_tail("", random.Random(1776)) is None
    corrupted, injected = corrupt_tail("norm_num", random.Random(1776))
    assert corrupted == "norm_num," and {r.kind for r in injected} == {"trailing-comma"}


@pytest.mark.parametrize("relic, expected", [
    (Relic(kind="refl", text="refl", fix="rfl", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="existsi", text="existsi", fix="use", line=0), _UNKNOWN_TACTIC),
    (Relic(kind="begin-end", text="begin", fix=None, line=0), _UNKNOWN_TACTIC),
    (Relic(kind="binder-comma", text="λ x,", fix=None, line=0), _UNEXPECTED_COMMA),
    (Relic(kind="trailing-comma", text="apply foo,", fix="apply foo", line=0), _UNEXPECTED_COMMA),
])
def test_synth_error_per_kind(relic, expected):
    assert synth_error([relic]) == expected


def test_synth_error_first_relic_only_empty_and_unknown_kind_raise():
    relics = [Relic(kind="binder-comma", text="λ x,", fix=None, line=0),
              Relic(kind="refl", text="refl", fix="rfl", line=1)]
    assert synth_error(relics) == _UNEXPECTED_COMMA
    with pytest.raises(ValueError):
        synth_error([])
    # The removed name-level kind is no longer a kind this module knows: passing
    # it in must raise rather than fall through to a stale message.
    with pytest.raises(ValueError, match="lean3-name"):
        synth_error([Relic(kind="lean3-name", text="supr_le", fix="iSup_le", line=0)])


def test_build_repair_user_golden():
    assert build_repair_user("USER TURN", "ATTEMPT LINE") == _GOLDEN + _COORDINATION
    assert build_repair_user("USER TURN", "ATTEMPT LINE", error="unknown identifier 'supr_le'") == (
        _GOLDEN + "Lean reported:\n```\nunknown identifier 'supr_le'\n```\n\n" + _COORDINATION)
