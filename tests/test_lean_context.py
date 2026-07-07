"""Offline tests for smolbench.lean.context render + trivial-rung logic.

Golden expectations below were derived by RUNNING render() on the fixture and
hand-verifying the output, not by copying whatever the code currently emits.
"""

from pathlib import Path

import pytest

import smolbench.lean.context as context
import smolbench.lean.corpus as corpus

FIXTURE = Path(__file__).parent / "fixtures" / "lean_mini"


@pytest.fixture
def thms(monkeypatch):
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    by_name = {t.full_name: t for t in corpus.load_split("random", "val")}
    yield by_name
    corpus.reset_caches()


# ---------------------------------------------------------------------------
# Goal-state parsing
# ---------------------------------------------------------------------------


def test_split_state_with_hypotheses():
    hyps, goals = context.split_state("n : ℕ\nh : P n\n⊢ Q n")
    assert hyps == "n : ℕ\nh : P n"
    assert goals == "⊢ Q n"


def test_split_state_bare_goal():
    hyps, goals = context.split_state("⊢ 1 + 1 = 2")
    assert hyps == ""
    assert goals == "⊢ 1 + 1 = 2"


def test_extract_goal_only_drops_hypotheses():
    assert context.extract_goal_only("n : ℕ\nh : P n\n⊢ Q n") == "⊢ Q n"


# ---------------------------------------------------------------------------
# render() golden checks at (Mini.theoremA, k=2)
# ---------------------------------------------------------------------------


def test_render_stepk0_goal_only(thms):
    r = context.render(thms["Mini.theoremA"], 2, "stepk", 0)
    assert r.label == "stepk:0"
    assert "## Current goal" in r.text
    assert "⊢ R n" in r.text
    # stepk:0 is answer-agnostic goal only: none of the richer sections yet.
    assert "## Full tactic state" not in r.text
    assert "## Proof so far" not in r.text
    assert "## Theorem" not in r.text
    assert "## Premises" not in r.text


def test_render_stepk1_adds_full_state(thms):
    r = context.render(thms["Mini.theoremA"], 2, "stepk", 1)
    assert "## Current goal" in r.text
    assert "## Full tactic state" in r.text
    assert "n : ℕ" in r.text
    assert "h : P n" in r.text
    assert "## Theorem" not in r.text


def test_render_stepk2_adds_tactics_and_theorem(thms):
    r = context.render(thms["Mini.theoremA"], 2, "stepk", 2)
    assert "## Proof so far (2 tactics)" in r.text
    assert "intro h" in r.text
    assert "simp" in r.text
    assert "## Theorem" in r.text
    assert "Mini.theoremA" in r.text
    assert "Mini/A.lean" in r.text
    assert "## Premises" not in r.text


def test_render_hint0_lists_premise_names(thms):
    r = context.render(thms["Mini.theoremA"], 2, "hint", 0)
    # hint:N always includes the stepk:2 baseline.
    assert "## Theorem" in r.text
    assert "## Premises used in the next tactic" in r.text
    assert "- `Mini.premiseA`" in r.text
    assert "- `Mini.premiseB`" in r.text
    assert "## Premise signatures" not in r.text


def test_render_hint1_includes_signatures(thms):
    r = context.render(thms["Mini.theoremA"], 2, "hint", 1)
    assert "## Premise signatures" in r.text
    # signature() = code prefix before the first top-level `:=`.
    assert "theorem Mini.premiseA {n : ℕ} (h : P n) : R n" in r.text
    assert "def Mini.premiseB (n : ℕ) : ℕ" in r.text


# ---------------------------------------------------------------------------
# is_trivial_rung branch coverage
# ---------------------------------------------------------------------------


def test_is_trivial_stepk_branches(thms):
    a = thms["Mini.theoremA"]
    b = thms["Mini.theoremB"]
    # stepk:0 is never trivial.
    assert context.is_trivial_rung(a, 0, "stepk", 0) is False
    # stepk:1 trivial iff the state has no hypotheses.
    assert context.is_trivial_rung(a, 0, "stepk", 1) is False  # tt[0] has hyps
    assert context.is_trivial_rung(b, 0, "stepk", 1) is True   # bare goal, no hyps
    # stepk:2 adds theorem identity even at k=0 -> never trivial.
    assert context.is_trivial_rung(a, 2, "stepk", 2) is False


def test_is_trivial_hint_branches(thms):
    a = thms["Mini.theoremA"]
    # No premises recorded at this step -> the whole hint chain is trivial.
    assert context.is_trivial_rung(a, 0, "hint", 0) is True
    # Premises recorded -> hint:0 non-trivial.
    assert context.is_trivial_rung(a, 2, "hint", 0) is False
    # Premises resolve in the corpus -> hint:1 (signatures) non-trivial.
    assert context.is_trivial_rung(a, 2, "hint", 1) is False
