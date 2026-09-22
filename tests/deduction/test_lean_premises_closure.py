"""Derivation edges: trace-first, namespace-aware text fallback.

Covers ``premises.referenced_premises`` and its helpers. The ``lean_mini``
fixture traces two theorems whose tactics name ``Mini.premiseA`` and
``Mini.premiseB``; the premises themselves are untraced, so they exercise the
text path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

from smolbench.deduction.lean import corpus, premises
from tests._paths import LEAN_MINI as FIXTURE

_FIXTURE_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"


@pytest.fixture
def mini(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Point the loaders at the fixture with an empty HOME (no traced repo)."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("HOME", str(tmp_path))
    corpus.reset_caches()
    yield tmp_path
    corpus.reset_caches()


# --- index -----------------------------------------------------------------


def test_build_derivation_index_records_first_use_order_without_self(mini: Path) -> None:
    idx = premises.build_derivation_index()
    assert idx == {
        "Mini.theoremA": ["Mini.premiseA", "Mini.premiseB"],
        "Mini.theoremB": ["Mini.premiseA"],
    }


def test_derivation_index_is_built_in_memory_when_the_sidecar_is_absent(
    mini: Path,
) -> None:
    """The fixture directory is read-only from the loader's point of view."""
    sidecar = premises.derivation_index_path()
    assert sidecar == FIXTURE / "derivation_index.json"
    assert not sidecar.exists()
    assert premises._derivation_index()["Mini.theoremB"] == ["Mini.premiseA"]
    assert not sidecar.exists(), "loading must not write into the corpus"


def test_derivation_index_prefers_the_sidecar(
    mini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sidecar = mini / "derivation_index.json"
    sidecar.write_text(json.dumps({"Mini.theoremB": ["Mini.premiseB"]}))
    monkeypatch.setattr(premises, "derivation_index_path", lambda: sidecar)
    corpus.reset_caches()
    assert premises._derivation_index() == {"Mini.theoremB": ["Mini.premiseB"]}


def test_write_derivation_index_writes_the_sidecar_and_refreshes(
    mini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sidecar = mini / "derivation_index.json"
    monkeypatch.setattr(premises, "derivation_index_path", lambda: sidecar)
    premises._derivation_index.cache_clear()
    assert premises.write_derivation_index() == sidecar
    assert json.loads(sidecar.read_text())["Mini.theoremA"] == [
        "Mini.premiseA",
        "Mini.premiseB",
    ]
    assert premises._derivation_index()["Mini.theoremA"] == [
        "Mini.premiseA",
        "Mini.premiseB",
    ]


def test_dep_source_reports_trace_text_or_none(mini: Path) -> None:
    assert premises.dep_source("Mini.theoremA") == "trace"
    assert premises.dep_source("Mini.premiseA") == "text"
    assert premises.dep_source("Mini.nothing") == "none"


# --- referenced_premises -------------------------------------------------


def test_referenced_premises_uses_the_trace_when_present(mini: Path) -> None:
    got = [p.full_name for p in premises.referenced_premises("Mini.theoremA")]
    assert got == ["Mini.premiseA", "Mini.premiseB"]
    got = [p.full_name for p in premises.referenced_premises("Mini.theoremB")]
    assert got == ["Mini.premiseA"]


def test_referenced_premises_falls_back_to_text_for_untraced_decls(mini: Path) -> None:
    """premiseA's corpus signature names nothing else; premiseB likewise."""
    assert premises.referenced_premises("Mini.premiseA") == ()
    assert premises.referenced_premises("Mini.premiseB") == ()
    assert premises.referenced_premises("Mini.nothing") == ()


def test_text_fallback_resolves_short_names_through_the_file_context(
    mini: Path,
) -> None:
    """A traced repo with ``namespace Mini`` lets ``premiseB`` (bare) resolve."""
    repo = (
        mini
        / ".cache"
        / "lean_dojo"
        / f"leanprover-community-mathlib4-{_FIXTURE_COMMIT}"
        / "mathlib4"
    )
    (repo / "Mini").mkdir(parents=True)
    lines = ["namespace Mini", "", "section", "open Nat", ""]
    lines += [f"-- filler {i}" for i in range(len(lines) + 1, 10)]
    lines += [
        "theorem premiseA {n : ℕ} (h : P n) : R n := by",
        "  exact absurd (premiseB n) h",
        "",
        "",
        "",
        "def premiseB (n : ℕ) : ℕ := n + 1",
        "",
        "end",
        "end Mini",
    ]
    (repo / "Mini" / "Prem.lean").write_text("\n".join(lines) + "\n")
    corpus.reset_caches()
    assert premises._traced_root() is not None
    assert premises._file_context("Mini/Prem.lean", 10) == ("Mini", ("Nat",))
    assert premises._file_context("Mini/Prem.lean", 1) == ("", ())
    got = [p.full_name for p in premises.referenced_premises("Mini.premiseA")]
    assert got == ["Mini.premiseB"]


# --- _resolve_name ---------------------------------------------------------

_IDX = {
    "Nat.add_comm": 1,
    "Int.add_comm": 2,
    "Nat.succ_le": 3,
    "Foo.Bar.baz": 4,
    "Foo.qux": 5,
    "unique_name": 6,
}


def _short(idx: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for full in idx:
        out.setdefault(full.rsplit(".", 1)[-1], []).append(full)
    return out


_SHORT = _short(_IDX)


def _resolve(tok: str, ns: str = "", opens: tuple[str, ...] = ()) -> str | None:
    return premises._resolve_name(tok, ns, opens, _IDX, _SHORT)


def test_resolve_exact_and_root_prefix() -> None:
    assert _resolve("Nat.add_comm") == "Nat.add_comm"
    assert _resolve("_root_.Nat.add_comm", ns="Int") == "Nat.add_comm"


def test_resolve_under_current_namespace_and_ancestors() -> None:
    assert _resolve("baz", ns="Foo.Bar") == "Foo.Bar.baz"
    assert _resolve("qux", ns="Foo.Bar") == "Foo.qux"
    assert _resolve("Bar.baz", ns="Foo") == "Foo.Bar.baz"


def test_resolve_through_open_and_open_relative_to_namespace() -> None:
    assert _resolve("add_comm", opens=("Nat",)) == "Nat.add_comm"
    assert _resolve("baz", ns="Foo", opens=("Bar",)) == "Foo.Bar.baz"


def test_resolve_ambiguity_is_none() -> None:
    assert _resolve("add_comm", opens=("Nat", "Int")) is None
    assert _resolve("add_comm") is None, "two globals share the short name"
    assert _resolve("unique_name") == "unique_name"


def test_resolve_dot_notation_suffix_only_under_context() -> None:
    assert _resolve("h.succ_le", ns="Nat") == "Nat.succ_le"
    assert _resolve("h.add_comm", ns="Nat") == "Nat.add_comm"
    assert _resolve("h.unique_name") is None, "never by global uniqueness"


def test_file_context_handles_open_forms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "X.lean"
    src.write_text(
        "\n".join(
            [
                "open Nat in",
                "open scoped BigOperators",
                "open Finset (sum prod)",
                "open List hiding map",
                "namespace A.B",
                "section",
                "end",
                "end A.B",
                "namespace C",
                "theorem t : True := trivial",
            ]
        )
    )
    monkeypatch.setattr(premises, "_resolve_source", lambda _p: src)
    premises._source_lines.cache_clear()
    premises._file_context.cache_clear()
    assert premises._file_context("X.lean", 10) == ("C", ("Nat", "Finset", "List"))
    assert premises._file_context("X.lean", 7) == ("A.B", ("Nat", "Finset", "List"))
    premises._source_lines.cache_clear()
    premises._file_context.cache_clear()


def test_ident_re_accepts_unicode_lean_names() -> None:
    """Mathlib names carry subscripts and Greek letters; an ASCII class split them."""
    text = "(forall₂_congr fun _ _ => by exact eq_comm).trans ext_iff.symm; hε ▸ Nat.succ_le'"
    toks = premises._IDENT_RE.findall(text)
    for want in ("forall₂_congr", "eq_comm", "ext_iff.symm", "hε", "Nat.succ_le'"):
        assert want in toks, toks
    assert "forall" not in toks and "_congr" not in toks, toks
    assert not any(t[0].isdigit() for t in premises._IDENT_RE.findall("2 * x₁ + 3")), "numerals are not names"


def test_resolve_dotted_prefix_before_dot_notation() -> None:
    """`ext_iff.symm` is the constant `ext_iff` under the namespace, then `.symm`."""
    idx = {"Foo.ext_iff": 1, "Foo.Bar.trans": 2, "Nat.succ_le": 3}
    short = _short(idx)
    assert premises._resolve_name("ext_iff.symm", "Foo", (), idx, short) == "Foo.ext_iff"
    assert premises._resolve_name("ext_iff.symm.trans", "Foo", (), idx, short) == "Foo.ext_iff"
    assert premises._resolve_name("Bar.trans", "Foo", (), idx, short) == "Foo.Bar.trans"
    assert premises._resolve_name("h.succ_le", "Nat", (), idx, short) == "Nat.succ_le"


def test_trace_covers_proof_only_for_top_level_tactic_blocks() -> None:
    assert premises._trace_covers_proof("theorem t : P := by\n  simp")
    assert premises._trace_covers_proof("theorem t : P :=by simp")
    assert not premises._trace_covers_proof(
        "theorem t : P :=\n  (foo fun _ => by exact bar).trans baz"
    )
    assert not premises._trace_covers_proof("def d : ℕ := 3")


def test_partial_trace_is_unioned_with_text_references(
    mini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A term-mode proof with a nested `by` traces only that block; the term-level names must survive."""
    repo = (
        mini
        / ".cache"
        / "lean_dojo"
        / f"leanprover-community-mathlib4-{_FIXTURE_COMMIT}"
        / "mathlib4"
    )
    (repo / "Mini").mkdir(parents=True)
    lines = ["namespace Mini"]
    lines += [f"-- filler {i}" for i in range(2, 10)]
    lines += [
        "theorem premiseA {n : ℕ} (h : P n) : R n :=",
        "  (premiseB n).elim (by exact h)",
        "",
        "",
        "",
        "def premiseB (n : ℕ) : ℕ := n + 1",
        "",
        "end Mini",
    ]
    (repo / "Mini" / "Prem.lean").write_text("\n".join(lines) + "\n")
    corpus.reset_caches()
    # theoremA's corpus record is `:= by ...`: the trace covers it.
    assert premises.dep_source("Mini.theoremA") == "trace"
    # premiseA is untraced: plain text path.
    assert premises.dep_source("Mini.premiseA") == "text"
    got = [p.full_name for p in premises.referenced_premises("Mini.premiseA")]
    assert got == ["Mini.premiseB"]

    # With a partial trace for premiseA, both sources contribute, trace first.
    idx = dict(premises.build_derivation_index())
    idx["Mini.premiseA"] = ["Mini.theoremB"]
    monkeypatch.setattr(premises, "_derivation_index", lambda: idx)
    premises.referenced_premises.cache_clear()
    try:
        assert premises.dep_source("Mini.premiseA") == "trace+text"
        got = [p.full_name for p in premises.referenced_premises("Mini.premiseA")]
        assert got == ["Mini.theoremB", "Mini.premiseB"]
    finally:
        monkeypatch.undo()
        corpus.reset_caches()


def test_projection_after_a_term_is_not_a_global_short_name(
    mini: Path,
) -> None:
    """`(x).premiseB` must not resolve `premiseB` by global uniqueness; only the file context may."""
    repo = (
        mini
        / ".cache"
        / "lean_dojo"
        / f"leanprover-community-mathlib4-{_FIXTURE_COMMIT}"
        / "mathlib4"
    )
    (repo / "Mini").mkdir(parents=True)
    lines = [f"-- filler {i}" for i in range(1, 10)]  # no namespace, no open
    lines += [
        "theorem Mini.premiseA {n : ℕ} (h : P n) : R n :=",
        "  (h).premiseB",
        "", "", "",
        "def Mini.premiseB (n : ℕ) : ℕ := n + 1",
    ]
    (repo / "Mini" / "Prem.lean").write_text("\n".join(lines) + "\n")
    corpus.reset_caches()
    assert premises.referenced_premises("Mini.premiseA") == ()
    # Under `namespace Mini` the projection head resolves through the context.
    (repo / "Mini" / "Prem.lean").write_text(
        "namespace Mini\n" + "\n".join(lines[1:]) + "\nend Mini\n"
    )
    corpus.reset_caches()
    got = [p.full_name for p in premises.referenced_premises("Mini.premiseA")]
    assert got == ["Mini.premiseB"]
