"""Test render() and is_trivial_rung() in smolbench.deduction.lean.context.
Goldens below were checked by hand, not copied from output.
"""

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus
import smolbench.deduction.lean.premises as premises
import smolbench.deduction.lean.prompt as prompt
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


#: A post-`cases`/`constructor` state -- the NORMAL shape once a proof branches.
_TWO_GOALS = (
    "case inl\n"
    "n : ℕ\n"
    "h : P n\n"
    "⊢ Q n\n"
    "\n"
    "case inr\n"
    "m : ℕ\n"
    "hm : S m\n"
    "⊢ R m"
)


def test_extract_goal_only_drops_hypotheses_from_EVERY_goal():
    """13-10: `stepk:0` is "goal only" for all goals, not just the first.

    `extract_goal_only` used to delegate to `split_state`, which stops at the
    FIRST `⊢`; everything after it -- including every later goal's
    hypotheses -- was returned verbatim under the "## Current goal" heading.
    At `stepk:1+` that only duplicates what the full tactic state already
    shows, but `stepk:0` is DEFINED as the rung that withholds hypotheses, so
    there it was a pure leak of exactly the information the rung exists to
    remove.

    Case headers and goal lines are kept (they are what makes a branched state
    readable and carry no hypothesis content); hypothesis lines are not.
    """
    got = context.extract_goal_only(_TWO_GOALS)
    for keep in ("case inl", "case inr", "⊢ Q n", "⊢ R m"):
        assert keep in got, f"{keep!r} missing from {got!r}"
    for leak in ("h : P n", "hm : S m", "n : ℕ", "m : ℕ"):
        assert leak not in got, f"{leak!r} leaked into stepk:0: {got!r}"


def test_extract_goal_only_passes_through_a_state_with_no_goal_line():
    """No `⊢` anywhere: return the state unchanged rather than an empty rung."""
    assert context.extract_goal_only("weird state") == "weird state"


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
    """noise:N == hint:(N-1) plus whitespace, at EXACTLY hint:N's PROMPT token count.

    13-11: this used to compare the CONTEXT texts. The model never sees a bare
    context -- it receives `prompt.build_user_prompt(rendered)`, i.e. the
    context plus a fixed instruction suffix -- and the suffix's token cost is
    NOT constant: it depends on what precedes it. Measured with cl100k, the
    suffix costs 28 tokens after most pads and 27 after a two-unit one, so a
    context-matched noise arm could be one token short of its hint twin in the
    only text that matters. The invariant is therefore asserted on the FULL
    PROMPT; `test_noise_pad_is_matched_on_the_full_prompt` is the case that
    proves the distinction is not academic.
    """
    pytest.importorskip("tiktoken")
    checked = padded_seen = 0
    for name, t, k, level in _noise_cases(thms):
        noise_rc = context.render(t, k, "noise", level)
        hint_rc = context.render(t, k, "hint", level)
        noise_text, hint_text = noise_rc.text, hint_rc.text
        base_text = context.render(t, k, "hint", level - 1).text
        n_noise = _cl100k_count(prompt.build_user_prompt(noise_rc))
        n_hint = _cl100k_count(prompt.build_user_prompt(hint_rc))
        assert n_noise == n_hint, (
            f"{name} k={k} noise:{level} -> {n_noise} PROMPT tokens but "
            f"hint:{level} -> {n_hint} (must be exactly equal)"
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


# ---------------------------------------------------------------------------
# 13-11: the pad is matched on the PROMPT, not on the context
# ---------------------------------------------------------------------------


def test_noise_pad_is_matched_on_the_full_prompt(thms, monkeypatch):
    """The one pad length where context-matching and prompt-matching disagree.

    Constructed, not sampled, because the discrepancy needs an exact pad
    length and the fixture corpus does not happen to produce one. With
    cl100k_base and the pad unit `choose_whitespace_unit` picks (``" \t"``,
    1 token), for this baseline:

        pad reps r:        0    1    2    3    4
        context tokens:   13   14   15   15   16
        prompt tokens:    41   42   42   43   44

    The hint:2 target is 15 context tokens / 43 prompt tokens. Matching on the
    CONTEXT stops at r=2 -- 15 == 15, exact, no complaint -- and ships a
    prompt of 42 against the hint arm's 43. That single token is a residual
    length confound inside the arm whose entire purpose is to remove the
    length confound. Matching on the PROMPT takes r=3 and lands on 43.

    Note r=2 and r=3 give the same CONTEXT count, which is why the old
    exactness re-check could not catch this: both spellings were "exact" on
    the quantity being measured. Only the quantity was wrong.
    """
    pytest.importorskip("tiktoken")
    base = "## Current goal\n```\n⊢ Q n\n```"
    target = base + " Q m"
    assert _cl100k_count(base) == 13 and _cl100k_count(target) == 15, (
        "the constructed baseline drifted; recompute the table in this docstring"
    )

    def fake_hint_parts(theorem, k, level):
        return [target] if level == 2 else [base]

    monkeypatch.setattr(context, "_render_hint_parts", fake_hint_parts)
    t = thms["Mini.theoremA"]
    noise = context.render(t, 2, "noise", 2)
    hint = context.render(t, 2, "hint", 2)

    n_noise = _cl100k_count(prompt.build_user_prompt(noise))
    n_hint = _cl100k_count(prompt.build_user_prompt(hint))
    assert n_noise == n_hint == 43, (n_noise, n_hint)
    # Still a pure whitespace pad appended to the baseline -- the fix changes
    # WHAT is measured, not what the arm is made of.
    assert noise.text.startswith(base)
    assert noise.text[len(base):].strip() == ""


def test_noise_path_uses_a_real_tokenizer_with_no_char_fallback():
    """13-21: the pad search counts with TiktokenTokenizer, never `len(s) // 4`.

    `_TokenCounter` re-implemented `smolbench.evals.tokenization.TiktokenTokenizer`
    with a bare-except char-count fallback, in a module whose own comment said
    it must not depend on `smolbench.evals` -- while already importing it
    lazily via the shared pad search. `tokenization.py`'s rule is NO SILENT
    FALLBACKS, and an approximate count cannot satisfy an EXACT length control.

    `_count_tokens` deliberately survives WITH its fallback, for the callers
    where a rough count is fine and raising would be scope creep:
    `is_trivial_rung`'s non-noise branches, plus `cli.py` and
    `tests/deduction/test_s3_archive.py`. (`_render_hint_parts`'s hint:3+ 50k
    budget applies the same tiktoken-or-`len(s) // 4` policy through its own
    inline `tok()`, not by calling this function -- a pre-existing duplicate
    that 13-21 deliberately left alone.)
    """
    source = (
        __import__("pathlib").Path(context.__file__).read_text()
    )
    assert "class _TokenCounter" not in source
    assert "TiktokenTokenizer" in source
    assert "def _count_tokens" in source, "the tolerant budget counter must survive"
    assert "len(s) // 4" in source, "_count_tokens keeps its graceful degrade"
    # The instruction suffix must be obtained from prompt.build_user_prompt,
    # never copied into this module -- a copy is the drift 13-11 closes.
    assert prompt.INSTRUCTION not in source


# ---------------------------------------------------------------------------
# 13-09: the hint:2 header must describe what it actually rendered
# ---------------------------------------------------------------------------

_FULL_SOURCE_HEADING = "## Premise full source (with proof)"

#: The traced-repo layout `premises._traced_root` resolves, keyed on the
#: corpus's own `from_repo.commit`.
_FIXTURE_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"


def test_hint2_header_says_signature_when_no_traced_source(thms):
    """13-09: without the traced repo, hint:2 renders SIGNATURES; say so.

    `premises.body_with_proof` falls back to the corpus's stored `Premise.code`
    -- a signature, usually with no proof body -- whenever `slice_full_decl`
    returns "" because `_traced_root()` is None. That is the CI/analysis-box
    configuration (this fixture's `HOME` has no `~/.cache/lean_dojo`), and the
    section was still headed "Premise full source (with proof)". The heading is
    part of the prompt, so it was telling the model it had been given proofs it
    had not been given.
    """
    assert premises._traced_root() is None, "fixture HOME must have no traced repo"
    text = context.render(thms["Mini.theoremA"], 2, "hint", 2).text
    assert _FULL_SOURCE_HEADING not in text, text[:400]
    assert "## Premise signature" in text, text[:400]


def test_hint2_header_says_full_source_when_the_traced_repo_is_present(
        thms, monkeypatch, tmp_path):
    """13-09, the other direction: a real slice still gets the full-source heading.

    Without this the fix could be "always say signature", which would be just
    as wrong in the configuration the study actually runs in. Builds the
    traced-repo layout `premises._traced_root` resolves -- keyed on the
    corpus's own `from_repo.commit` -- and puts a real proof body at the line
    range the corpus records for `Mini.premiseA`.
    """
    repo = (tmp_path / "traced" / ".cache" / "lean_dojo"
            / f"leanprover-community-mathlib4-{_FIXTURE_COMMIT}" / "mathlib4")
    (repo / "Mini").mkdir(parents=True)
    # premiseA is recorded at lines 10-11, premiseB at 15; pad so the slice
    # lands on real text rather than off the end of the file.
    lines = [f"-- filler {i}" for i in range(1, 10)]
    lines += ["theorem Mini.premiseA {n : ℕ} (h : P n) : R n := by",
              "  exact absurd h  -- REAL PROOF BODY FROM THE TRACED REPO"]
    lines += [f"-- filler {i}" for i in range(12, 15)]
    lines += ["def Mini.premiseB (n : ℕ) : ℕ := n + 1"]
    (repo / "Mini" / "Prem.lean").write_text("\n".join(lines) + "\n")

    monkeypatch.setenv("HOME", str(tmp_path / "traced"))
    corpus.reset_caches()
    try:
        assert premises._traced_root() is not None, "the fake traced repo was not found"
        text = context.render(thms["Mini.theoremA"], 2, "hint", 2).text
        assert _FULL_SOURCE_HEADING in text, text[:400]
        assert "REAL PROOF BODY FROM THE TRACED REPO" in text
    finally:
        corpus.reset_caches()


# ---------------------------------------------------------------------------
# 13-30: the premise-reference stoplist has no unreachable entries
# ---------------------------------------------------------------------------


def test_lean_noise_stoplist_has_no_dead_entries():
    """13-30: every stoplist entry must be able to fire.

    `referenced_premises` filters with ``if tok in _LEAN_NOISE or len(tok) <= 1``
    over tokens from ``_IDENT_RE.findall(text)``, so an entry is DEAD if it is a
    single character (pre-empted by the length guard) or is not an `_IDENT_RE`
    token at all (``"trivial!"`` -- ``!`` is outside the character class). 23 of
    the original 120 entries were dead, which is 23 lines of documentation
    asserting a filter that never ran.

    Deleting them is behaviour-preserving BY CONSTRUCTION, which is why this
    test states the property rather than pinning a count: a future entry that
    cannot fire fails here regardless of how many there are.
    """
    dead_short = sorted(t for t in premises._LEAN_NOISE if len(t) <= 1)
    assert not dead_short, f"pre-empted by the len(tok) <= 1 guard: {dead_short}"
    unmatchable = sorted(
        t for t in premises._LEAN_NOISE if not premises._IDENT_RE.fullmatch(t)
    )
    assert not unmatchable, f"never produced by _IDENT_RE.findall: {unmatchable}"
    assert len(premises._LEAN_NOISE) == 97, (
        "120 entries minus the 23 verified-dead ones; a change here needs a "
        "reason in the commit message"
    )
