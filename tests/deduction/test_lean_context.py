"""Test render() and is_trivial_rung() in smolbench.deduction.lean.context.
Goldens below were checked by hand, not copied from output.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus
import smolbench.deduction.lean.premises as premises
import smolbench.deduction.lean.prompt as prompt
from tests._paths import LEAN_MINI as FIXTURE


@pytest.fixture
def thms(monkeypatch: pytest.MonkeyPatch,
         tmp_path: Path) -> Iterator[dict[str, corpus.BenchmarkTheorem]]:
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


def _noise_cases(
        thms: dict[str, corpus.BenchmarkTheorem],
) -> Iterator[tuple[str, corpus.BenchmarkTheorem, int, int]]:
    """Every (theorem, k, level) noise rung renderable on the fixture."""
    for name in sorted(thms):
        t = thms[name]
        for k in range(len(t.traced_tactics)):
            for level in (1, 2, 3):
                yield name, t, k, level


def test_state_parsing() -> None:
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


def test_extract_goal_only_drops_hypotheses_from_EVERY_goal() -> None:
    """stepk:0 must withhold hypotheses from every goal, not just the first (extract_goal_only used to delegate to split_state, which stops at the first ⊢ and leaked the rest)."""
    got = context.extract_goal_only(_TWO_GOALS)
    for keep in ("case inl", "case inr", "⊢ Q n", "⊢ R m"):
        assert keep in got, f"{keep!r} missing from {got!r}"
    for leak in ("h : P n", "hm : S m", "n : ℕ", "m : ℕ"):
        assert leak not in got, f"{leak!r} leaked into stepk:0: {got!r}"


def test_extract_goal_only_passes_through_a_state_with_no_goal_line() -> None:
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
def test_render_ladder(thms: dict[str, corpus.BenchmarkTheorem], chain: str, level: int,
                       required: list[str], forbidden: list[str]) -> None:
    """Each rung adds its own sections and nothing from higher rungs."""
    r = context.render(thms["Mini.theoremA"], 2, chain, level)
    assert r.label == f"{chain}:{level}"
    assert all(m in r.text for m in required)
    assert not any(m in r.text for m in forbidden)


def test_is_trivial_rung_branches(thms: dict[str, corpus.BenchmarkTheorem]) -> None:
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
    # hint:3 -- neither premise's body names another premise, so the 1-hop closure
    # is empty; also exercises the _traced_root() is None path via body_with_proof.
    assert context.is_trivial_rung(a, 2, "hint", 3) is True
    assert context.is_trivial_rung(a, 2, "noise", 0) is True
    assert context.is_trivial_rung(a, 2, "noise", 2) is False
    # noise:3 inherits hint:3's triviality.
    assert context.is_trivial_rung(a, 2, "noise", 3) is True


def test_noise_arm_invariants(thms: dict[str, corpus.BenchmarkTheorem]) -> None:
    """noise:N == hint:(N-1) plus whitespace, at exactly hint:N's PROMPT token count -- checked on the full prompt because the instruction suffix's own token cost depends on what precedes it."""
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


def test_noise_rejects_impossible_targets(
        thms: dict[str, corpus.BenchmarkTheorem], monkeypatch: pytest.MonkeyPatch) -> None:
    """A baseline longer than its target, and noise:0, must both raise."""
    pytest.importorskip("tiktoken")
    t = thms["Mini.theoremA"]
    with pytest.raises(ValueError):
        context.render(t, 2, "noise", 0)
    def fake_hint_parts(theorem: corpus.BenchmarkTheorem, k: int,
                        level: int) -> list[str]:
        return ["X " * 400] if level == 1 else ["short"]
    monkeypatch.setattr(context, "_render_hint_parts", fake_hint_parts)
    with pytest.raises(ValueError):
        context.render(t, 2, "noise", 2)


# The pad is matched on the PROMPT, not on the context.


def test_noise_pad_is_matched_on_the_full_prompt(
        thms: dict[str, corpus.BenchmarkTheorem], monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructed case (the fixture corpus never produces one) where matching on CONTEXT and matching on PROMPT disagree: context-matching stops at r=2 (15 tokens, exact) but ships a 42-token prompt against the hint arm's 43; matching on PROMPT takes r=3 and lands on 43."""
    pytest.importorskip("tiktoken")
    base = "## Current goal\n```\n⊢ Q n\n```"
    target = base + " Q m"
    assert _cl100k_count(base) == 13 and _cl100k_count(target) == 15, (
        "the constructed baseline drifted; recompute the table in this docstring"
    )

    def fake_hint_parts(theorem: corpus.BenchmarkTheorem, k: int,
                        level: int) -> list[str]:
        return [target] if level == 2 else [base]

    monkeypatch.setattr(context, "_render_hint_parts", fake_hint_parts)
    t = thms["Mini.theoremA"]
    noise = context.render(t, 2, "noise", 2)
    hint = context.render(t, 2, "hint", 2)

    n_noise = _cl100k_count(prompt.build_user_prompt(noise))
    n_hint = _cl100k_count(prompt.build_user_prompt(hint))
    assert n_noise == n_hint == 43, (n_noise, n_hint)
    # Still a pure whitespace pad -- the fix changes what's measured, not the arm itself.
    assert noise.text.startswith(base)
    assert noise.text[len(base):].strip() == ""


def test_noise_path_uses_a_real_tokenizer_with_no_char_fallback() -> None:
    """The pad search counts with TiktokenTokenizer, never a char-count fallback -- an approximate count can't satisfy an exact length control; `_count_tokens` keeps its fallback for callers where a rough count is fine (is_trivial_rung's non-noise branches, cli.py, test_s3_archive.py)."""
    source = (
        __import__("pathlib").Path(context.__file__).read_text()
    )
    assert "class _TokenCounter" not in source
    assert "TiktokenTokenizer" in source
    assert "def _count_tokens" in source, "the tolerant budget counter must survive"
    assert "len(s) // 4" in source, "_count_tokens keeps its graceful degrade"
    # The instruction suffix must come from prompt.build_user_prompt, never be copied here.
    assert prompt.INSTRUCTION not in source


# The hint:2 header must describe what it actually rendered.

_FULL_SOURCE_HEADING = "## Premise full source (with proof)"

#: Traced-repo commit key that premises._traced_root resolves, from the corpus's own
#: from_repo.commit.
_FIXTURE_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"


def test_hint2_header_says_signature_when_no_traced_source(
        thms: dict[str, corpus.BenchmarkTheorem]) -> None:
    """Without a traced repo, body_with_proof falls back to the corpus's stored signature; the header must say so instead of claiming full source with proof."""
    assert premises._traced_root() is None, "fixture HOME must have no traced repo"
    text = context.render(thms["Mini.theoremA"], 2, "hint", 2).text
    assert _FULL_SOURCE_HEADING not in text, text[:400]
    assert "## Premise signature" in text, text[:400]


def test_hint2_header_says_full_source_when_the_traced_repo_is_present(
        thms: dict[str, corpus.BenchmarkTheorem], monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    """The other direction: with a real traced slice available, the header must say full source rather than always defaulting to signature."""
    repo = (tmp_path / "traced" / ".cache" / "lean_dojo"
            / f"leanprover-community-mathlib4-{_FIXTURE_COMMIT}" / "mathlib4")
    (repo / "Mini").mkdir(parents=True)
    # premiseA is recorded at lines 10-11, premiseB at 15; pad so the slice lands on
    # real text, not past EOF.
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


# The premise-reference stoplist has no unreachable entries.


def test_lean_noise_stoplist_has_no_dead_entries() -> None:
    """Every _LEAN_NOISE entry must be reachable: dead if it's a single char (pre-empted by the length guard) or doesn't match _IDENT_RE (e.g. "trivial!", since ! is outside the class)."""
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


def test_noise_pad_search_comes_from_the_public_evals_home(tmp_path: Path) -> None:
    """Noise-rung rendering must not reach into smolbench.induction._common (another study's private module); run in a subprocess because a sys.meta_path blocker only bites pre-import, and this module may already be imported in-process by an induction test."""
    import subprocess
    import sys as _sys

    from tests._paths import LEAN_MINI, REPO_ROOT

    script = tmp_path / "blocked_render.py"
    script.write_text(
        "import sys\n"
        "BANNED = 'smolbench.induction._common'\n"
        "class _Blocker:\n"
        "    def find_module(self, name, path=None):\n"
        "        return None\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == BANNED:\n"
        "            raise ImportError(f'{name} is banned by this test')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _Blocker())\n"
        "from smolbench.deduction.lean import context, corpus\n"
        "t = {x.full_name: x for x in corpus.load_split('random', 'val')}['Mini.theoremA']\n"
        "rendered = context.render(t, 2, 'noise', 1)\n"
        "assert BANNED not in sys.modules, 'the private induction module was imported'\n"
        "assert rendered.text.strip(), 'noise rung rendered empty'\n"
        "print('OK')\n"
    )
    proc = subprocess.run(
        [_sys.executable, str(script)],
        capture_output=True, text=True, timeout=300, cwd=str(REPO_ROOT),
        env={"PATH": "/usr/bin:/bin", "SMOLBENCH_LEAN_DATA": str(LEAN_MINI),
             "PYTHONPATH": str(REPO_ROOT)},
    )
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert "OK" in proc.stdout
