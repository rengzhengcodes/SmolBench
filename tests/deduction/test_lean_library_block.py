"""Unflagged library block: ``sig``/``proof`` chains and their length controls."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from smolbench.deduction.lean import context, corpus, premises, prompt
from tests._paths import LEAN_MINI as FIXTURE


@pytest.fixture
def thms(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[dict]:
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("HOME", str(tmp_path))
    corpus.reset_caches()
    yield {t.full_name: t for t in corpus.load_split("random", "val")}
    corpus.reset_caches()


def _count(text: str) -> int:
    tiktoken = pytest.importorskip("tiktoken")
    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def test_library_order_follows_imports_then_lines(thms: dict) -> None:
    """Prem.lean is imported by A.lean and B.lean, so it ranks first; within a file, by line."""
    rank = premises._file_rank()
    assert rank["Mini/Prem.lean"] < rank["Mini/A.lean"] < rank["Mini/B.lean"]
    ps = [premises.lookup(n) for n in ("Mini.theoremB", "Mini.premiseB", "Mini.premiseA", "Mini.theoremA")]
    assert [p.full_name for p in premises.library_order(ps)] == [
        "Mini.premiseA",
        "Mini.premiseB",
        "Mini.theoremA",
        "Mini.theoremB",
    ]


def test_sig_block_is_unflagged_and_in_library_order(thms: dict) -> None:
    a = thms["Mini.theoremA"]
    text = context.render(a, 2, "sig", 0).text
    assert "## Library context" in text
    assert "Premises used" not in text and "Premise signatures" not in text
    heads = [l for l in text.splitlines() if l.startswith("### ")]
    assert [h.split("`")[1] for h in heads] == ["Mini.premiseA", "Mini.premiseB"]
    # Signatures only: premiseA's proof body must be absent.
    assert "exact absurd h" not in text
    assert "theorem Mini.premiseA {n : ℕ} (h : P n) : R n" in text
    # The stepk:2 base is intact.
    for h in ("## Current goal", "## Full tactic state", "## Proof so far", "## Theorem"):
        assert h in text


def test_proof_block_carries_bodies(thms: dict) -> None:
    a = thms["Mini.theoremA"]
    text = context.render(a, 2, "proof", 0).text
    assert "exact absurd h" in text
    assert text.count("### ") == 2


def test_empty_mpi_renders_no_block_and_is_trivial(thms: dict) -> None:
    a = thms["Mini.theoremA"]
    assert "## Library context" not in context.render(a, 0, "sig", 0).text
    assert context.is_trivial_rung(a, 0, "sig", 0) is True
    assert context.is_trivial_rung(a, 0, "proof", 1) is True


def test_triviality_of_hops_and_forms(thms: dict) -> None:
    a = thms["Mini.theoremA"]
    assert context.is_trivial_rung(a, 2, "sig", 0) is False
    # The fixture premises reference nothing, so the 1-hop closure adds nothing.
    assert context.is_trivial_rung(a, 2, "sig", 1) is True
    assert context.is_trivial_rung(a, 2, "signoise", 1) is True
    assert context.is_trivial_rung(a, 2, "signoise", 0) is True
    # premiseA's stored code has a proof its signature lacks.
    assert context.is_trivial_rung(a, 2, "proof", 0) is False
    assert context.is_trivial_rung(a, 2, "proofnoise", 0) is False


def test_proofnoise_matches_proof_prompt_tokens_exactly(thms: dict) -> None:
    a = thms["Mini.theoremA"]
    pn = context.render(a, 2, "proofnoise", 0)
    pf = context.render(a, 2, "proof", 0)
    sg = context.render(a, 2, "sig", 0).text
    assert pn.text.startswith(sg)
    assert pn.text[len(sg) :].strip() == ""
    assert _count(prompt.build_user_prompt(pn)) == _count(prompt.build_user_prompt(pf))


def test_validate_accepts_new_chains_and_rejects_bad_levels() -> None:
    for chain in ("sig", "proof", "signoise", "proofnoise"):
        context.validate(chain, 0)
        context.validate(chain, 9)
        with pytest.raises(ValueError):
            context.validate(chain, 10)
