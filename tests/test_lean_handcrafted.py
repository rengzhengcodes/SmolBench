"""Offline tests for ``scripts/verify_handcrafted_lean.py`` -- the
hand-crafted "unrelated" Lean4 instance verifier.

No Lean toolchain is exercised here: everything below the compile gate is
covered by the live gold-instance run instead. These tests pin the pure
logic -- the banned-head token scan (including the launderings a naive
line-head split would miss), comment stripping, ``#print axioms`` parsing,
schema gating, the SFT projection round-trip through
`prompt.extract_tactic_block`, and behavioral parity of the vendored QC
gate with its source of truth in ``scripts/annotate_lean_cot.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import verify_handcrafted_lean as vh  # noqa: E402
from smolbench.deduction.lean.prompt import extract_tactic_block  # noqa: E402


# ---------------------------------------------------------------------------
# Ban scan
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "src, expected",
    [
        ("induction n <;> simp", ["simp"]),
        ("refine ⟨?_, by exact h⟩", ["exact"]),
        ("all_goals rw [foo]", ["rw"]),
        ("cases h; rwa [bar] at hx", ["rwa"]),
        ("simp_all only [foo]", ["simp_all"]),
        ("exact?", ["exact"]),
        ("have h := foo\nsimpa using h", ["simpa"]),
        ("erw [foo]", ["erw"]),
        ("norm_num [two_mul]", []),
        ("constructor", []),
        ("omega", []),
        ("refine Eq.refl _", []),          # refl is not rfl
        ("have h : P := Iff.rfl.mp hq", []),  # dotted .rfl does not fire
        ("linarith [sq_nonneg x]", []),
        ("-- we deliberately avoid simp here\nomega", []),  # comments stripped
        ("/- rw [foo] -/\ndecide", []),
        ("gcongr", []),
        ("apply foo", ["apply"]),
        # longest alternative wins: the token IS exact_mod_cast, not exact
        ("exact_mod_cast h", ["exact_mod_cast"]),
    ],
)
def test_ban_scan(src: str, expected: list[str]) -> None:
    assert vh.ban_scan(src) == sorted(expected)


def test_ban_scan_identifier_boundaries() -> None:
    # banned words inside identifiers must not fire
    assert vh.ban_scan("have simple : P := foo simple_lemma") == []
    assert vh.ban_scan("have applyx := f applyx") == []
    # bare rfl term IS banned by design
    assert vh.ban_scan("exact rfl") == ["exact", "rfl"]


def test_strip_comments_nested() -> None:
    src = "a /- outer /- inner -/ still -/ b -- tail\nc"
    assert vh.strip_comments(src) == "a  b \nc"


# ---------------------------------------------------------------------------
# tactic_heads (informational)
# ---------------------------------------------------------------------------


def test_tactic_heads_segments_and_bullets() -> None:
    proof = "  intro h\n  induction n <;> omega\n  · constructor\n  case succ ih => omega"
    assert vh.tactic_heads(proof) == [
        "intro", "induction", "omega", "constructor", "omega",
    ]


# ---------------------------------------------------------------------------
# #print axioms parsing
# ---------------------------------------------------------------------------


def test_parse_axioms_both_forms() -> None:
    out = (
        "'U001.t' depends on axioms: [U001.G, U001.op_e, propext]\n"
        "'U014.andcomm' does not depend on any axioms\n"
    )
    parsed = vh.parse_axioms(out)
    assert parsed["U001.t"] == ["U001.G", "U001.op_e", "propext"]
    assert parsed["U014.andcomm"] == []


def test_parse_axioms_ignores_diagnostics() -> None:
    out = (
        "<stdin>:2:8: warning: declaration uses 'sorry'\n"
        "'U002.t' depends on axioms: [sorryAx]\n"
    )
    assert vh.parse_axioms(out)["U002.t"] == ["sorryAx"]


# ---------------------------------------------------------------------------
# Schema gate (no Lean needed: failures short-circuit before compiling)
# ---------------------------------------------------------------------------


def _row(**over) -> dict:
    base = {
        "id": "U000",
        "category": "prop_logic",
        "provision_style": "hypothesis",
        "ns": "U000",
        "thm_name": "u000_chain",
        "provided_src": "",
        "theorem_src": "theorem u000_chain (P Q : Prop) (hpq : P → Q) (hp : P) : Q := by",
        "proof": "  have hq := hpq hp\n  assumption",
        "reasoning_chain": "hpq turns a proof of P into a proof of Q; applying it to hp gives Q.",
        "negative_control_src": "theorem u000_chain (P Q : Prop) (hp : P) : Q := by",
    }
    base.update(over)
    return base


def test_schema_rejects_bad_rows() -> None:
    assert vh._schema_check(_row(id="X1")) == "schema:bad_id_or_ns"
    assert vh._schema_check(_row(category="nope")) == "schema:unknown_category"
    assert vh._schema_check(_row(theorem_src="theorem other : True := by")) == (
        "schema:theorem_src_name_mismatch"
    )
    assert vh._schema_check(_row(theorem_src="theorem u000_chain : True := trivial")) == (
        "schema:theorem_src_must_end_with_by"
    )
    assert vh._schema_check(_row(negative_control_src="")) == (
        "schema:missing_negative_control_src"
    )
    assert vh._schema_check(_row()) is None


def test_verify_row_banned_head_fails_before_compile() -> None:
    row = vh.verify_row(_row(proof="  exact hpq hp"), timeout=0.001)
    assert row["verify"].startswith("fail:banned_heads:exact")


def test_verify_row_forbidden_construct() -> None:
    row = vh.verify_row(_row(proof="  sorry"), timeout=0.001)
    assert row["verify"].startswith("fail:forbidden_construct")


# ---------------------------------------------------------------------------
# SFT projection
# ---------------------------------------------------------------------------


def test_sft_round_trip_through_extract_tactic_block() -> None:
    row = _row()
    row["tactic_heads"] = vh.tactic_heads(row["proof"])
    sft = vh.build_sft_row(row)
    assert sft["assistant"].startswith("<think>\n")
    # the training-time extractor must recover exactly the tactic block
    assert extract_tactic_block(sft["assistant"]) == row["proof"].strip()
    assert "## Theorem to prove" in sft["user"]
    assert sft["meta"]["cot_style"] == "think"


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------


def test_dedupe_jaccard_name_insensitive() -> None:
    a = vh._statement_shingles("theorem u001_foo (n : Nat) (h : n < 3) : n * n < 9 := by")
    b = vh._statement_shingles("theorem u099_bar (n : Nat) (h : n < 3) : n * n < 9 := by")
    assert vh._jaccard(a, b) == 1.0
    c = vh._statement_shingles(
        "theorem u050_other (xs : List Nat) : xs.reverse.reverse = xs := by"
    )
    assert vh._jaccard(a, c) < 0.2


# ---------------------------------------------------------------------------
# Vendored QC gate: behavioral parity with scripts/annotate_lean_cot.py
# ---------------------------------------------------------------------------

_QC_CASES = [
    ("", "tac", "empty_rationale"),
    ("uses ``` fence", "tac", "forbidden_markup"),
    ("x" * 3000, "tac", "too_long"),
    ("intro h\nomega", "intro h\nomega", "restatement"),
    ("this is probably fine", "tac", "hedging"),
    ("The hypothesis h closes the goal directly.", "tac", None),
]


@pytest.mark.parametrize("rationale, tail, expected", _QC_CASES)
def test_vendored_qc_gate(rationale: str, tail: str, expected: str | None) -> None:
    assert vh._qc_gate(rationale, tail, max_rationale_chars=2500) == expected


def test_vendored_qc_gate_parity_with_source_of_truth() -> None:
    ac = pytest.importorskip("scripts.annotate_lean_cot")
    for rationale, tail, expected in _QC_CASES:
        assert (
            ac._qc_gate(rationale, tail, max_rationale_chars=2500)
            == vh._qc_gate(rationale, tail, max_rationale_chars=2500)
            == expected
        )
