"""Checked-signature sidecar: declarations the corpus export omits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

from smolbench.deduction.lean import context, corpus, premises
from tests._paths import LEAN_MINI as FIXTURE

_PRINT_OUTPUT = """\
theorem add_comm.{u_1} : ∀ {G : Type u_1} [inst : AddCommMagma G] (a b : G), a + b = b + a :=
fun {G} [AddCommMagma G] => AddCommMagma.add_comm
constructor Or.inr : ∀ {a b : Prop}, b → a ∨ b
def HSub.hSub.{u, v, w} : {α : Type u} → {β : Type v} → {γ : outParam (Type w)} → [self : HSub α β γ] → α → β → γ :=
fun α β {γ} [self : HSub α β γ] => self.1
/tmp/x.lean:7:8: error: unknown identifier 'nonexistent_name_xyz'
@[reducible] def Foo.bar.{u} : Type u →
  Type u :=
fun x => x
"""


def test_parse_print_output_records_kind_type_and_body() -> None:
    got = premises.parse_print_output(_PRINT_OUTPUT)
    assert set(got) == {"add_comm", "Or.inr", "HSub.hSub", "Foo.bar"}
    assert got["add_comm"]["kind"] == "theorem"
    assert got["add_comm"]["type"].startswith("∀ {G : Type u_1} [inst : AddCommMagma G]")
    assert got["add_comm"]["body"] == "fun {G} [AddCommMagma G] => AddCommMagma.add_comm"
    assert got["Or.inr"] == {"kind": "constructor", "type": "∀ {a b : Prop}, b → a ∨ b", "body": ""}
    assert got["Foo.bar"]["type"] == "Type u → Type u", "multi-line types join with a space"
    assert got["Foo.bar"]["body"] == "fun x => x"


def test_module_of_maps_paths_to_modules() -> None:
    assert premises.module_of("Mathlib/Algebra/Group/Defs.lean") == "Mathlib.Algebra.Group.Defs"
    assert premises.module_of(".lake/packages/lean4/src/lean/Init/Prelude.lean") == "Init.Prelude"
    assert premises.module_of(".lake/packages/std/Std/Data/List/Basic.lean") == "Std.Data.List.Basic"
    assert premises.module_of("Mathlib/Foo.txt") is None


@pytest.fixture
def mini(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("HOME", str(tmp_path))
    corpus.reset_caches()
    yield tmp_path
    corpus.reset_caches()


def test_missing_trace_premises_is_empty_when_the_corpus_has_everything(mini: Path) -> None:
    assert premises.missing_trace_premises("random", ("val",)) == {}


def test_lookup_falls_back_to_the_sidecar_and_never_slices_source(
    mini: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sidecar = mini / "checked_signatures.json"
    sidecar.write_text(
        json.dumps(
            {
                "add_comm": {
                    "kind": "theorem",
                    "type": "∀ {G : Type u_1} [inst : AddCommMagma G] (a b : G), a + b = b + a",
                    "body": "fun {G} [AddCommMagma G] => AddCommMagma.add_comm",
                    "def_path": "Mini/Prem.lean",
                    "def_pos": [10, 1],
                }
            }
        )
    )
    monkeypatch.setattr(premises, "checked_signatures_path", lambda: sidecar)
    premises._checked.cache_clear()
    p = premises.lookup("add_comm")
    assert p is not None and premises.is_checked(p)
    assert p.kind == "theorem" and p.file_path == "Mini/Prem.lean"
    assert premises.signature(p) == "theorem add_comm : ∀ {G : Type u_1} [inst : AddCommMagma G] (a b : G), a + b = b + a"
    assert premises.body_with_proof(p).endswith(":=\nfun {G} [AddCommMagma G] => AddCommMagma.add_comm")
    assert premises.has_full_source(p) is False
    # Corpus records still win, and unknown names still miss.
    assert not premises.is_checked(premises.lookup("Mini.premiseA"))
    assert premises.lookup("nothing.here") is None
    premises._checked.cache_clear()


def test_checked_lemma_enters_the_library_block(mini: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import dataclasses

    sidecar = mini / "checked_signatures.json"
    sidecar.write_text(
        json.dumps({"Or.inr": {"kind": "constructor", "type": "∀ {a b : Prop}, b → a ∨ b", "body": "",
                                "def_path": "Mini/Prem.lean", "def_pos": [1, 1]}})
    )
    monkeypatch.setattr(premises, "checked_signatures_path", lambda: sidecar)
    premises._checked.cache_clear()
    by = {t.full_name: t for t in corpus.load_split("random", "val")}
    a = by["Mini.theoremA"]
    tt = a.traced_tactics[2]
    extra = {"full_name": "Or.inr", "def_path": "Mini/Prem.lean", "def_pos": [1, 1], "def_end_pos": [1, 5]}
    a2 = dataclasses.replace(a, traced_tactics=a.traced_tactics[:2] + [dataclasses.replace(tt, premises=tt.premises + [extra])])
    text = context.render(a2, 2, "sig", 0).text
    assert "### `Or.inr` at `Mini/Prem.lean`" in text
    assert "constructor Or.inr : ∀ {a b : Prop}, b → a ∨ b" in text
    premises._checked.cache_clear()


def test_lookup_unmangles_private_names(mini: Path) -> None:
    p = premises.lookup("_private.Mini.Prem.0.Mini.premiseA")
    assert p is not None and p.full_name == "Mini.premiseA"
    assert premises.lookup("_private.Mini.Prem.0.Mini.nothing") is None
