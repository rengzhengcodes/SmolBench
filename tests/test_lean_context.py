"""Test render() and is_trivial_rung() in smolbench.deduction.lean.context.

The golden values below come from running render() on the fixture and
checking the output by hand. They do not copy what the code emits now.
"""

from pathlib import Path

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus

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


# ---------------------------------------------------------------------------
# noise:N invariants: WHITESPACE padding at EXACT token equality.
#
# This is a user directive. A `noise:N` rendering must equal its
# `hint:(N-1)` baseline plus pure WHITESPACE padding. The padding must make
# the token count match the paired `hint:N` rendering EXACTLY, not
# approximately, and never with prose filler.
#
# These tests count tokens with an INDEPENDENT tiktoken cl100k_base encoder,
# not with `context`'s own counter. This way the tests check the contract
# itself, not just what the current implementation happens to measure.
# ---------------------------------------------------------------------------


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


def test_noise_token_count_exactly_equals_paired_hint(thms):
    """`noise:N` matches `hint:N` EXACTLY in tokens, for every fixture rung.

    Exactness is the whole point of the control arm: an approximate match
    silently reintroduces prompt length as a confound between the two arms
    being compared.
    """
    pytest.importorskip("tiktoken")
    checked = 0
    for name, t, k, level in _noise_cases(thms):
        noise = context.render(t, k, "noise", level)
        hint = context.render(t, k, "hint", level)
        n_noise = _cl100k_count(noise.text)
        n_hint = _cl100k_count(hint.text)
        assert n_noise == n_hint, (
            f"{name} k={k} noise:{level} -> {n_noise} tokens but "
            f"hint:{level} -> {n_hint} tokens (must be exactly equal)"
        )
        checked += 1
    # Guard against a vacuous pass if the fixture ever stops producing rungs.
    assert checked >= 6, f"only {checked} noise rungs exercised"


def test_noise_padding_is_whitespace_only_and_not_lorem(thms):
    """The pad is the `hint:(N-1)` baseline plus WHITESPACE, and nothing else.

    This also confirms removal of the old lorem-ipsum filler. Prose padding
    adds information the paired hint rung does not have. The old
    `## Filler ...` header was itself unmatched content.
    """
    pytest.importorskip("tiktoken")
    padded_seen = 0
    for name, t, k, level in _noise_cases(thms):
        noise_text = context.render(t, k, "noise", level).text
        base_text = context.render(t, k, "hint", level - 1).text

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
        if pad:
            padded_seen += 1
    # At least some rungs must actually need padding, or the whitespace
    # assertion above is trivially satisfied by empty pads everywhere.
    assert padded_seen >= 2, f"only {padded_seen} noise rungs actually padded"


def test_noise_render_is_deterministic(thms):
    """Whitespace padding consumes no RNG: identical inputs, identical text."""
    pytest.importorskip("tiktoken")
    for name, t, k, level in _noise_cases(thms):
        a = context.render(t, k, "noise", level).text
        b = context.render(t, k, "noise", level).text
        assert a == b, f"{name} k={k} noise:{level} render is not deterministic"


def test_noise_raises_when_baseline_exceeds_target(thms, monkeypatch):
    """A baseline LONGER than its target must fail loudly, not under-pad.

    You cannot shrink a rendering by appending whitespace. So if `hint:(N-1)` renders
    longer than `hint:N`, the exact-match contract cannot hold. The renderer must raise
    instead of silently emitting a short "length control", which would bring back the
    length confound this arm removes.
    """
    pytest.importorskip("tiktoken")
    t = thms["Mini.theoremA"]

    def fake_hint_parts(theorem, k, level):
        # level 1 (the noise:2 baseline) renders far longer than level 2.
        return ["X " * 400] if level == 1 else ["short"]

    monkeypatch.setattr(context, "_render_hint_parts", fake_hint_parts)
    with pytest.raises(ValueError):
        context.render(t, 2, "noise", 2)


def test_noise_level_zero_still_rejected(thms):
    """`noise:0` has no `hint:-1` baseline to pad; it stays a ValueError."""
    with pytest.raises(ValueError):
        context.render(thms["Mini.theoremA"], 2, "noise", 0)


def test_is_trivial_hint_branches(thms):
    a = thms["Mini.theoremA"]
    # No premises recorded at this step -> the whole hint chain is trivial.
    assert context.is_trivial_rung(a, 0, "hint", 0) is True
    # Premises recorded -> hint:0 non-trivial.
    assert context.is_trivial_rung(a, 2, "hint", 0) is False
    # Premises resolve in the corpus -> hint:1 (signatures) non-trivial.
    assert context.is_trivial_rung(a, 2, "hint", 1) is False
