"""Test render() and is_trivial_rung() in smolbench.deduction.lean.context.
Goldens below were checked by hand, not copied from output.
"""

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus
import smolbench.deduction.lean.premises as premises
from tests._paths import LEAN_MINI as FIXTURE


@pytest.fixture
def thms(monkeypatch, tmp_path):
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    # Empty HOME: no ~/.cache/lean_dojo traced repo, so `premises._traced_root`
    # returns None and `body_with_proof` falls back to the fixture's own code --
    # the CI configuration, and what keeps the hint-rung goldens deterministic
    # on a developer box that HAS a traced mathlib4.
    monkeypatch.setenv("HOME", str(tmp_path))
    corpus.reset_caches()
    by_name = {t.full_name: t for t in corpus.load_split("random", "val")}
    yield by_name
    corpus.reset_caches()


def _cl100k_count(text: str) -> int:
    tiktoken = pytest.importorskip("tiktoken")
    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def _noise_cases(thms):
    """Every (theorem, k, level) noise rung renderable on the fixture."""
    for name in sorted(thms):
        t = thms[name]
        for k in range(len(t.traced_tactics)):
            for level in (1, 2, 3):
                yield name, t, k, level


def test_state_parsing():
    """split_state/extract_goal_only separate hypotheses from goals."""
    hyps, goals = context.split_state("n : ℕ\nh : P n\n⊢ Q n")
    assert hyps == "n : ℕ\nh : P n"
    assert goals == "⊢ Q n"
    assert context.split_state("⊢ 1 + 1 = 2") == ("", "⊢ 1 + 1 = 2")
    assert context.extract_goal_only("n : ℕ\nh : P n\n⊢ Q n") == "⊢ Q n"


@pytest.mark.parametrize("chain,level,required,forbidden", [
    ("stepk", 0, ["## Current goal", "⊢ R n"],
     ["## Full tactic state", "## Proof so far", "## Theorem", "## Premises"]),
    ("stepk", 1, ["## Current goal", "## Full tactic state", "n : ℕ", "h : P n"],
     ["## Theorem"]),
    ("stepk", 2, ["## Proof so far (2 tactics)", "intro h", "simp", "## Theorem",
                  "Mini.theoremA", "Mini/A.lean"], ["## Premises"]),
    ("hint", 0, ["## Theorem", "## Premises used in the next tactic",
                 "- `Mini.premiseA`", "- `Mini.premiseB`"], ["## Premise signatures"]),
    ("hint", 1, ["## Premise signatures", "theorem Mini.premiseA {n : ℕ} (h : P n) : R n",
                 "def Mini.premiseB (n : ℕ) : ℕ"], []),
])
def test_render_ladder(thms, chain, level, required, forbidden):
    """Each rung adds its own sections and nothing from higher rungs."""
    r = context.render(thms["Mini.theoremA"], 2, chain, level)
    assert r.label == f"{chain}:{level}"
    assert all(m in r.text for m in required)
    assert not any(m in r.text for m in forbidden)


def test_is_trivial_rung_branches(thms):
    """stepk:1 is trivial only without hypotheses; hint rungs need premises."""
    a = thms["Mini.theoremA"]
    b = thms["Mini.theoremB"]
    assert premises._traced_root() is None, "fixture HOME must have no traced repo"
    assert context.is_trivial_rung(a, 0, "stepk", 0) is False
    assert context.is_trivial_rung(a, 0, "stepk", 1) is False
    assert context.is_trivial_rung(b, 0, "stepk", 1) is True
    assert context.is_trivial_rung(a, 2, "stepk", 2) is False
    assert context.is_trivial_rung(a, 0, "hint", 0) is True
    assert context.is_trivial_rung(a, 2, "hint", 0) is False
    assert context.is_trivial_rung(a, 2, "hint", 1) is False
    # hint:2 -- premiseA's stored code carries a proof body its signature lacks.
    assert context.is_trivial_rung(a, 2, "hint", 2) is False
    # hint:3 -- neither premise's body names another corpus premise, so the
    # 1-hop closure is empty. Exercises the `_traced_root() is None` path too:
    # the closure reads bodies through `body_with_proof`.
    assert context.is_trivial_rung(a, 2, "hint", 3) is True
    assert context.is_trivial_rung(a, 2, "noise", 0) is True
    assert context.is_trivial_rung(a, 2, "noise", 2) is False
    # noise:3 inherits hint:3's triviality.
    assert context.is_trivial_rung(a, 2, "noise", 3) is True


def test_noise_arm_invariants(thms):
    """noise:N == hint:(N-1) plus whitespace, at EXACTLY hint:N's token count."""
    pytest.importorskip("tiktoken")
    checked = padded_seen = 0
    for name, t, k, level in _noise_cases(thms):
        noise_text = context.render(t, k, "noise", level).text
        hint_text = context.render(t, k, "hint", level).text
        base_text = context.render(t, k, "hint", level - 1).text
        n_noise, n_hint = _cl100k_count(noise_text), _cl100k_count(hint_text)
        assert n_noise == n_hint, (
            f"{name} k={k} noise:{level} -> {n_noise} tokens but "
            f"hint:{level} -> {n_hint} tokens (must be exactly equal)"
        )
        assert noise_text.startswith(base_text), (
            f"{name} k={k} noise:{level} does not start with its hint:{level-1} baseline"
        )
        pad = noise_text[len(base_text):]
        assert pad.strip() == "", (
            f"{name} k={k} noise:{level} pad is not whitespace-only: {pad[:120]!r}"
        )
        assert "Lorem ipsum" not in noise_text
        assert "lorem" not in noise_text.lower()
        assert "Filler" not in noise_text
        assert context.render(t, k, "noise", level).text == noise_text, (
            f"{name} k={k} noise:{level} render is not deterministic"
        )
        checked += 1
        padded_seen += bool(pad)
    assert checked >= 6, f"only {checked} noise rungs exercised"
    assert padded_seen >= 2, f"only {padded_seen} noise rungs actually padded"


def test_noise_rejects_impossible_targets(thms, monkeypatch):
    """A baseline longer than its target, and noise:0, must both raise."""
    pytest.importorskip("tiktoken")
    t = thms["Mini.theoremA"]
    with pytest.raises(ValueError):
        context.render(t, 2, "noise", 0)
    def fake_hint_parts(theorem, k, level):
        return ["X " * 400] if level == 1 else ["short"]
    monkeypatch.setattr(context, "_render_hint_parts", fake_hint_parts)
    with pytest.raises(ValueError):
        context.render(t, 2, "noise", 2)
