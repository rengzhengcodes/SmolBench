"""Offline tests for smolbench.deduction.lean.runner (and cli import-cleanliness).

The Lean verifier is faked (FakeVerifier below) so the whole sweep runs with
no lean_dojo and no Lean process: generation goes to two local OpenAI-compatible
stub servers (one per provider), verification is a pure-Python stand-in driven
off a marker string in the model's reply. This exercises the runner's dispatch,
seed threading, row schema, resume, and artifact writing on ANY interpreter.
"""

import gzip
import json
import subprocess
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus
import smolbench.deduction.lean.lean3 as lean3
import smolbench.deduction.lean.prompt as prompt
import smolbench.deduction.lean.runner as runner
from tests.conftest import StubServer, chat_completion

FIXTURE = Path(__file__).parent / "fixtures" / "lean_mini"

# Session-unique model ids so provider get_model_context_length lru_caches
# don't bleed a stale ctx-length in from another test module.
M1 = "mini/pi-model-a"       # provider: primeintellect
M2 = "mini/or-model-b"       # provider: openrouter

# A candidate proof "verifies" (FakeVerifier) iff it contains this marker.
MARKER = "QED"


# ---------------------------------------------------------------------------
# Fake verifier: stands in for smolbench.deduction.lean.verify without lean_dojo.
# Field names mirror the real ProofResult / ReplayResult so the runner's
# attribute access (verdict/error/final_state_pp, verdict/tactics_applied/
# tactics_total/error) works unchanged.
# ---------------------------------------------------------------------------


@dataclass
class FakeProofResult:
    theorem: str
    verdict: str
    tail_tried: str
    error: Optional[str] = None
    final_state_pp: Optional[str] = None


@dataclass
class FakeReplayResult:
    theorem: str
    verdict: str
    tactics_applied: int
    tactics_total: int
    error: Optional[str] = None
    final_state_pp: Optional[str] = None


class FakeVerifier:
    ProofResult = FakeProofResult

    def replay_ground_truth(self, bt, timeout=600):
        n = len(bt.traced_tactics)
        return FakeReplayResult(bt.full_name, "success", n, n)

    @contextmanager
    def open_at_step(self, bt, k, timeout=600):
        yield ("fake-dojo", f"state@k={k}")

    def try_tail(self, dojo, state_at_k, tail, theorem_name):
        ok = MARKER in tail
        return FakeProofResult(
            theorem_name, "success" if ok else "lean_error", tail,
            error=None if ok else "marker absent",
        )

    def verify_proof_tail(self, bt, k, tail, timeout=600):
        ok = MARKER in tail
        return FakeProofResult(
            bt.full_name, "success" if ok else "lean_error", tail,
            error=None if ok else "marker absent",
        )


# ---------------------------------------------------------------------------
# Additional fake verifiers: spy / configurable-gate variants for the tests
# below that pin sweep()'s Dojo-session-sharing and sanity-gate-resume
# contracts specifically (as opposed to FakeVerifier above, which only
# needs to stand in for a working verifier's happy-path behavior).
# ---------------------------------------------------------------------------


class SpyVerifier(FakeVerifier):
    """FakeVerifier variant that counts/records calls instead of just faking
    verdicts, to pin sweep()'s "one shared Dojo session per (theorem, k)"
    contract: every rung/model/rollout branching off the same (theorem, k)
    must reuse the SAME `open_at_step` context (never open a fresh one), and
    each theorem gets exactly one `replay_ground_truth` sanity replay.
    """

    def __init__(self):
        self.open_count = 0
        # (theorem_name, dojo_token) per try_tail call, in call order.
        self.tail_tokens: list[tuple[str, str]] = []
        self.replay_calls: list[str] = []

    def replay_ground_truth(self, bt, timeout=600):
        self.replay_calls.append(bt.full_name)
        return super().replay_ground_truth(bt, timeout=timeout)

    @contextmanager
    def open_at_step(self, bt, k, timeout=600):
        # A unique token per open (never reused across opens) so any
        # cross-(theorem, k) session reuse would show up as a shared token
        # in `tail_tokens` where none is expected.
        self.open_count += 1
        token = f"dojo-{self.open_count}-{bt.full_name}-k{k}"
        yield (token, f"state@k={k}")

    def try_tail(self, dojo, state_at_k, tail, theorem_name):
        self.tail_tokens.append((theorem_name, dojo))
        return super().try_tail(dojo, state_at_k, tail, theorem_name)


class ConfigurableSanityVerifier(FakeVerifier):
    """FakeVerifier variant whose sanity-gate verdict is configurable per
    theorem, to pin the resume-exclusion fix in `_sanity_done` /
    `_process_one_theorem`: a theorem whose ground-truth replay was
    recorded as non-success must stay excluded from cell generation on
    resume, even if a LATER verifier instance passed to a resumed `sweep()`
    call would now report success for it. `_sanity_done` returns a
    `dict[str, str]` of verdicts (not just a set of "done" names)
    specifically so this resume-time re-exclusion is possible.
    """

    def __init__(self, verdict_by_theorem: dict[str, str]):
        # Theorems absent from this mapping default to "success" -- only
        # the theorems under test need an explicit non-success verdict.
        self.verdict_by_theorem = verdict_by_theorem
        self.replay_calls: list[str] = []

    def replay_ground_truth(self, bt, timeout=600):
        self.replay_calls.append(bt.full_name)
        n = len(bt.traced_tactics)
        verdict = self.verdict_by_theorem.get(bt.full_name, "success")
        applied = n if verdict == "success" else 0
        return FakeReplayResult(
            bt.full_name, verdict, applied, n,
            error=None if verdict == "success" else "synthetic sanity failure",
        )


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def two_stubs():
    """Two independent OpenAI-compatible stub servers (distinct endpoints)."""
    servers, threads = [], []
    for _ in range(2):
        s = StubServer()
        t = threading.Thread(target=s.serve_forever, daemon=True)
        t.start()
        servers.append(s)
        threads.append(t)
    yield servers
    for s in servers:
        s.shutdown()
    for t in threads:
        t.join(timeout=5)


@pytest.fixture
def sweep_ctx(two_stubs, monkeypatch, tmp_path):
    """Wire both providers at their stubs, repoint the dataset at the fixture."""
    pi_stub, or_stub = two_stubs
    monkeypatch.setenv("PRIME_INTELLECT_BASE_URL", pi_stub.base_url)
    monkeypatch.setenv("PRIME_INTELLECT_API_KEY", "stub-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", or_stub.base_url)
    monkeypatch.setenv("OPENROUTER_API_KEY", "stub-key")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("SMOLBENCH_LEAN_RESULTS", str(tmp_path))
    pi_stub.default_response = chat_completion(MARKER)
    or_stub.default_response = chat_completion(MARKER)
    corpus.reset_caches()
    yield SimpleNamespace(pi=pi_stub, orr=or_stub, tmp=tmp_path)
    corpus.reset_caches()


def _make_config(concurrent):
    return {
        "run_name": "mini",
        "theorems": {
            "source": "explicit",
            "full_names": ["Mini.theoremA", "Mini.theoremB"],
            "kind": "random",
            "split": "val",
        },
        "k": {"strategy": "last"},
        "rungs": ["stepk:0", "stepk:1"],
        "skip_trivial": False,        # deterministic cell count, no skips
        "n_rollouts": 2,
        "temperature": 0.5,
        "max_tokens": 256,
        "seed": 1000,
        "request_timeout": 30,
        "max_retries": 2,
        "concurrent_gen": concurrent,
        "max_concurrency": 4,
        "models": [
            {"provider": "primeintellect", "model": M1,
             "extra_params": {"reasoning_effort": "high"}},
            {"provider": "openrouter", "model": M2},
        ],
    }


# theorems(2) x rungs(2) x models(2) x rollouts(2), no trivial skips.
EXPECTED_CELLS = 16

REQUIRED_ROW_KEYS = {
    "kind", "theorem_id", "file_path", "k", "n_total_tactics", "chain",
    "level", "rung", "rollout_idx", "model", "api_model", "provider", "seed",
    "temperature", "context_chars", "ground_truth_remaining", "prompt_tokens",
    "completion_tokens", "cache_read_tokens", "cache_creation_tokens",
    "gen_ms", "verify_ms", "candidate_proof", "raw_response",
    "reasoning_content", "verdict", "lean_error", "final_state_pp",
}


def _rows(run_dir, kind):
    out = []
    for line in (run_dir / "all_rows.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") == kind:
            out.append(r)
    return out


def _chat_posts(stub):
    """POST /chat/completions requests only (GET ctx-length lookups have body=None)."""
    return [
        req for req in stub.requests
        if req.get("body") is not None and req["path"].endswith("/chat/completions")
    ]


# ---------------------------------------------------------------------------
# (a) row count + schema + seed threading   (b) per-model dispatch
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_schema_and_dispatch(sweep_ctx, concurrent):
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(_make_config(concurrent), run_dir, verifier=FakeVerifier())
    assert n_written == EXPECTED_CELLS

    cells = _rows(run_dir, "cell")
    assert len(cells) == EXPECTED_CELLS

    # (a) full schema on every row; seed = base_seed(1000) + rollout_idx.
    for r in cells:
        assert REQUIRED_ROW_KEYS <= set(r), REQUIRED_ROW_KEYS - set(r)
        assert r["seed"] == 1000 + r["rollout_idx"]
        assert r["verdict"] == "success"      # marker present in every reply
        assert r["temperature"] == 0.5

    # (b) per-model dispatch: each provider's stub only ever saw its own model.
    pi_posts = _chat_posts(sweep_ctx.pi)
    or_posts = _chat_posts(sweep_ctx.orr)
    assert len(pi_posts) == EXPECTED_CELLS // 2
    assert len(or_posts) == EXPECTED_CELLS // 2
    assert {p["body"]["model"] for p in pi_posts} == {M1}
    assert {p["body"]["model"] for p in or_posts} == {M2}

    # request bodies carry seed / temperature / max_tokens and [system, user].
    for p in pi_posts + or_posts:
        body = p["body"]
        assert body["seed"] in (1000, 1001)
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 256
        assert body["messages"][0] == {"role": "system", "content": prompt.SYSTEM}
        assert body["messages"][1]["role"] == "user"
        assert body["messages"][1]["content"].endswith(prompt.INSTRUCTION)
    # both rollout seeds are exercised.
    assert {p["body"]["seed"] for p in pi_posts} == {1000, 1001}

    # extra_params rides through only for the model that declared it.
    assert all(p["body"].get("reasoning_effort") == "high" for p in pi_posts)
    assert all("reasoning_effort" not in p["body"] for p in or_posts)


# ---------------------------------------------------------------------------
# (d) all_rows vs per-theorem outputs consistency + manifest + analysis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_outputs_and_artifacts(sweep_ctx, concurrent):
    run_dir = sweep_ctx.tmp / "run"
    runner.sweep(_make_config(concurrent), run_dir, verifier=FakeVerifier())

    def key(r):
        return (r["theorem_id"], r["rung"], r["model"], r["rollout_idx"])

    all_keys = {key(r) for r in _rows(run_dir, "cell")}
    assert len(all_keys) == EXPECTED_CELLS

    out_keys = set()
    for jl in (run_dir / "theorems").rglob("outputs/*.jsonl"):
        for line in jl.read_text().splitlines():
            out_keys.add(key(json.loads(line)))
    assert out_keys == all_keys

    # one sanity row per theorem.
    assert {r["theorem_id"] for r in _rows(run_dir, "sanity")} == {
        "Mini.theoremA", "Mini.theoremB"
    }

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["counts"]["written"] == EXPECTED_CELLS
    assert (run_dir / "analysis.txt").read_text().strip()


# ---------------------------------------------------------------------------
# (c) resume: nothing re-run on a clean resume; an exception cell IS re-run
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_resume_and_exception_rerun(sweep_ctx, concurrent):
    cfg = _make_config(concurrent)
    run_dir = sweep_ctx.tmp / "run"

    first = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert first == EXPECTED_CELLS

    # Clean resume: every cell key already present -> 0 new rows, sanity intact.
    second = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert second == 0
    assert len(_rows(run_dir, "sanity")) == 2

    # Rewrite ONE cell's verdict to "exception" (append can't force a rerun:
    # _existing_keys still sees the original success row for that key, so the
    # faithful way to model a transient failure is to make the cell's only
    # recorded verdict be exception). Every other row is preserved verbatim.
    all_rows_path = run_dir / "all_rows.jsonl"
    lines = all_rows_path.read_text().splitlines()
    target = None
    for i, line in enumerate(lines):
        r = json.loads(line)
        if r.get("kind") == "cell":
            target = (r["model"], r["theorem_id"], r["k"], r["rung"], r["rollout_idx"])
            r["verdict"] = "exception"
            lines[i] = json.dumps(r, ensure_ascii=False)
            break
    assert target is not None
    all_rows_path.write_text("\n".join(lines) + "\n")

    third = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert third == 1  # exactly the one exception cell re-runs

    # And the re-run produced a fresh non-exception row for that exact key.
    reran = [
        r for r in _rows(run_dir, "cell")
        if (r["model"], r["theorem_id"], r["k"], r["rung"], r["rollout_idx"]) == target
        and r["verdict"] != "exception"
    ]
    assert reran


# ---------------------------------------------------------------------------
# (f) determinism: identical key sets across two fresh sweeps
# ---------------------------------------------------------------------------


def test_sweep_determinism(sweep_ctx):
    cfg = _make_config(concurrent=True)

    def keyset(run_dir):
        return {
            (r["model"], r["theorem_id"], r["k"], r["rung"], r["rollout_idx"], r["seed"])
            for r in _rows(run_dir, "cell")
        }

    runner.sweep(cfg, sweep_ctx.tmp / "run_a", verifier=FakeVerifier())
    runner.sweep(cfg, sweep_ctx.tmp / "run_b", verifier=FakeVerifier())
    ka = keyset(sweep_ctx.tmp / "run_a")
    kb = keyset(sweep_ctx.tmp / "run_b")
    assert ka == kb
    assert len(ka) == EXPECTED_CELLS


# ---------------------------------------------------------------------------
# (e) run_cell path: provider string + verifier.verify_proof_tail
# ---------------------------------------------------------------------------


def test_run_cell_path(sweep_ctx):
    theorem = {t.full_name: t for t in corpus.load_split("random", "val")}["Mini.theoremA"]
    rows = list(runner.run_cell(
        provider="primeintellect",
        model=M1,
        theorem=theorem,
        k=2,
        chain="stepk",
        level=0,
        n_rollouts=2,
        seed=1000,
        request_timeout=30,
        max_retries=2,
        verifier=FakeVerifier(),
    ))
    assert len(rows) == 2
    for i, r in enumerate(rows):
        assert r["seed"] == 1000 + i
        assert r["provider"] == "primeintellect"
        assert r["model"] == M1
        assert r["verdict"] == "success"

    pi_posts = _chat_posts(sweep_ctx.pi)
    assert len(pi_posts) == 2
    assert {p["body"]["model"] for p in pi_posts} == {M1}
    assert {p["body"]["seed"] for p in pi_posts} == {1000, 1001}


# ---------------------------------------------------------------------------
# 3.14-venv guarantee: runner + cli import with NO lean_dojo installed.
# ---------------------------------------------------------------------------


def test_runner_and_cli_import_without_lean_dojo():
    # This module already imports runner at top level; on the main .venv
    # (Python 3.14, no lean_dojo) that import succeeding at collection time is
    # itself the guarantee. Confirm both modules and their public surface.
    import smolbench.deduction.lean.cli as cli
    import smolbench.deduction.lean.runner as rnr

    assert callable(rnr.sweep)
    assert callable(rnr.run_cell)
    assert callable(rnr.results_root)
    assert callable(cli.main)


def test_cli_help_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "smolbench.deduction.lean.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "usage" in (result.stdout + result.stderr).lower()


# ---------------------------------------------------------------------------
# (g) plumbing spy: max_retries/request_timeout/system/seed reach complete()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("concurrent", [False, True])
def test_complete_receives_max_retries_request_timeout_system_seed(
    sweep_ctx, monkeypatch, concurrent
):
    """Wraps the REAL provider `complete` in a recording spy -- patched on
    the module OBJECT the runner resolves via `provider_module`, exactly
    the attribute `mod.complete(...)` looks up at call time (see the
    runner module docstring's "Generation dispatch" note) -- and asserts
    EVERY call the sweep makes forwards `max_retries`, `request_timeout`,
    `system`, the resolved `context_length`, and a correctly-threaded
    `seed`. This is the test that fails if any generation code path
    silently drops one of these kwargs: an unbounded retry loop against a
    wedged endpoint, a truncated-CoT timeout, or (worst) an unseeded,
    non-reproducible generation would all be invisible to the
    response-shape assertions in `test_sweep_schema_and_dispatch` above,
    which only inspect what came BACK, never what was actually sent.
    """
    import smolbench.evals.openrouter as orr
    import smolbench.evals.primeintellect as pi

    calls: list[dict] = []

    def _spy(real):
        def _wrapped(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return real(*args, **kwargs)
        return _wrapped

    # Design: patch the MODULE ATTRIBUTE, not a locally-bound reference --
    # `_provider_and_ctx_for` caches the module object itself and every call
    # site does `mod.complete(...)`, a fresh attribute lookup each time, so
    # patching the attribute is sufficient regardless of when the module
    # was resolved/cached relative to this patch.
    monkeypatch.setattr(pi, "complete", _spy(pi.complete))
    monkeypatch.setattr(orr, "complete", _spy(orr.complete))

    cfg = _make_config(concurrent)
    cfg["request_timeout"] = 33
    cfg["max_retries"] = 2
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert n_written == EXPECTED_CELLS
    assert len(calls) == EXPECTED_CELLS

    seeds_seen: list[int] = []
    for call in calls:
        kwargs = call["kwargs"]
        assert kwargs["max_retries"] == 2
        assert kwargs["request_timeout"] == 33
        assert kwargs["system"] == prompt.SYSTEM
        assert kwargs["context_length"] == 100000  # stub's fixed GET response
        # complete(prompt, model, seed, ...) -- seed is the 3rd positional.
        seeds_seen.append(call["args"][2])

    # Seed threading: every call's seed is base_seed(1000) + rollout_idx in
    # {0, 1} (rollouts are the seed-varying replicate axis; see `sweep`'s
    # docstring), and both rollout seeds are exercised in equal numbers (one
    # per rung x model combination: 2 rungs x 2 models = 4 calls each).
    assert set(seeds_seen) == {1000, 1001}
    assert seeds_seen.count(1000) == seeds_seen.count(1001) == EXPECTED_CELLS // 2


# ---------------------------------------------------------------------------
# (h) one-shared-Dojo contract: one open_at_step per (theorem, k); every
# try_tail/replay_ground_truth call is scoped to the right theorem.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_shares_one_dojo_session_per_theorem_k(sweep_ctx, concurrent):
    """Pins the "open once per (theorem, k), share across all
    rungs/models/rollouts" contract documented in `sweep`'s docstring and
    implemented by the single `with verifier.open_at_step(...)` in both
    `_run_cells_at_step` and `_run_cells_at_step_concurrent`. A regression
    that opened a fresh Dojo session per cell instead would still pass the
    schema/dispatch tests (the fake verdicts don't depend on which token
    was used) but would be catastrophically slower/wrong against the real
    Lean verifier, which this test would catch via the open-count and
    per-theorem token assertions below.
    """
    cfg = _make_config(concurrent)
    run_dir = sweep_ctx.tmp / "run"
    verifier = SpyVerifier()
    n_written = runner.sweep(cfg, run_dir, verifier=verifier)
    assert n_written == EXPECTED_CELLS

    # k.strategy "last" -> exactly one k per theorem -> 2 theorems == 2 opens.
    assert verifier.open_count == 2

    # Every try_tail call for a given theorem must have used THAT theorem's
    # own token, and tokens must never cross theorems.
    by_theorem: dict[str, set] = {}
    for name, token in verifier.tail_tokens:
        by_theorem.setdefault(name, set()).add(token)
    assert set(by_theorem) == {"Mini.theoremA", "Mini.theoremB"}
    for name, tokens in by_theorem.items():
        assert len(tokens) == 1, f"{name} used more than one Dojo token: {tokens}"
    all_tokens = {t for tokens in by_theorem.values() for t in tokens}
    assert len(all_tokens) == 2  # theorems never share a token

    assert len(verifier.tail_tokens) == EXPECTED_CELLS
    # Exactly one sanity replay per theorem.
    assert verifier.replay_calls == ["Mini.theoremA", "Mini.theoremB"]


# ---------------------------------------------------------------------------
# (i) trivial-skip path: skip_trivial=True drops exactly the rungs
# `is_trivial_rung` calls trivial, no more and no less.
# ---------------------------------------------------------------------------


def _make_trivial_config(concurrent: bool = False) -> dict:
    return {
        "run_name": "trivial",
        "theorems": {
            "source": "explicit",
            "full_names": ["Mini.theoremA", "Mini.theoremB"],
            "kind": "random",
            "split": "val",
        },
        # k.strategy "first" (unlike _make_config's "last"): under this
        # fixture, Mini.theoremB's k=0 tactic state has NO hypotheses, so
        # stepk:1 is trivial there (verified via is_trivial_rung directly
        # in the test below, not hardcoded) -- k.strategy "last" produces
        # no trivial rungs in this fixture at all, per `_make_config`'s own
        # "no deterministic skips" comment.
        "k": {"strategy": "first"},
        "rungs": ["stepk:0", "stepk:1"],
        "skip_trivial": True,
        "n_rollouts": 2,
        "temperature": 0.5,
        "max_tokens": 256,
        "seed": 1000,
        "request_timeout": 30,
        "max_retries": 2,
        "concurrent_gen": concurrent,
        "max_concurrency": 4,
        "models": [
            {"provider": "primeintellect", "model": M1},
            {"provider": "openrouter", "model": M2},
        ],
    }


def test_sweep_skips_trivial_rungs(sweep_ctx):
    """skip_trivial=True must drop exactly the (theorem, rung) cells
    `is_trivial_rung` calls trivial -- no more, no less. The expected set is
    derived by PROBING `is_trivial_rung` directly against the fixture in
    this test (not hardcoded as a magic cell count), so the test fails
    loudly instead of silently passing/drifting if the fixture data or
    `is_trivial_rung`'s rules ever change.
    """
    theorems = {t.full_name: t for t in corpus.load_split("random", "val")}
    k_strategy = "first"
    rungs = ["stepk:0", "stepk:1"]
    k_by_theorem = {
        name: runner._k_indices(t, k_strategy)[0] for name, t in theorems.items()
    }

    trivial_pairs = set()
    for name, t in theorems.items():
        k = k_by_theorem[name]
        for rung in rungs:
            chain, level = rung.split(":", 1)
            if context.is_trivial_rung(t, k, chain, int(level)):
                trivial_pairs.add((name, rung))
    # Guard against vacuous-pass drift: this test only exercises the
    # trivial-skip path if the fixture actually produces >=1 trivial rung.
    assert trivial_pairs, (
        "fixture no longer produces any trivial rung under k=first -- "
        "update this test's config/fixture expectations"
    )

    cfg = _make_trivial_config()
    run_dir = sweep_ctx.tmp / "run"
    runner.sweep(cfg, run_dir, verifier=FakeVerifier())

    cells = _rows(run_dir, "cell")
    seen_pairs = {(r["theorem_id"], r["rung"]) for r in cells}
    all_pairs = {(name, rung) for name in theorems for rung in rungs}
    assert seen_pairs == all_pairs - trivial_pairs

    n_models = len(cfg["models"])
    n_rollouts = cfg["n_rollouts"]
    expected_n_cells = (len(all_pairs) - len(trivial_pairs)) * n_models * n_rollouts
    assert len(cells) == expected_n_cells


# ---------------------------------------------------------------------------
# (j) sanity-gate fail + resume exclusion -- pins the _sanity_done
# dict[str, str] fix (a recorded failure must stay excluded on resume).
# ---------------------------------------------------------------------------


def test_sanity_gate_fail_and_resume_exclusion(sweep_ctx):
    """Pins the resume-exclusion behavior of `_sanity_done` /
    `_process_one_theorem`: a theorem whose ground-truth replay was
    recorded as failed must STAY excluded from cell generation on resume,
    even when a FRESH verifier instance passed to the resumed `sweep()`
    call would now report success for it. Before `_sanity_done` returned
    verdicts (just names), a resumed sweep could only tell "a sanity row
    exists", not "what it said" -- silently starting to generate cells for
    a theorem the first pass explicitly refused to run.
    """
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"

    first_verifier = ConfigurableSanityVerifier({"Mini.theoremA": "lean_error"})
    n_written = runner.sweep(cfg, run_dir, verifier=first_verifier)

    sanity_rows = {r["theorem_id"]: r for r in _rows(run_dir, "sanity")}
    assert sanity_rows["Mini.theoremA"]["verdict"] == "lean_error"
    assert sanity_rows["Mini.theoremB"]["verdict"] == "success"

    cells = _rows(run_dir, "cell")
    assert not any(r["theorem_id"] == "Mini.theoremA" for r in cells)
    b_cells = [r for r in cells if r["theorem_id"] == "Mini.theoremB"]
    assert len(b_cells) == EXPECTED_CELLS // 2  # B's full cell count, untouched
    assert n_written == EXPECTED_CELLS // 2
    assert first_verifier.replay_calls == ["Mini.theoremA", "Mini.theoremB"]

    # Resume with a verifier that WOULD now report success for A: the
    # recorded "lean_error" sanity row must still gate it out. B's cells
    # are already recorded and must be skipped as done, not regenerated,
    # and neither theorem's sanity gate should re-run at all (A stays
    # excluded via the recorded verdict; B's recorded "success" short-
    # circuits straight past the replay -- see `_process_one_theorem`).
    second_verifier = ConfigurableSanityVerifier({})  # empty -> "success" for all
    second_written = runner.sweep(cfg, run_dir, verifier=second_verifier)

    assert second_written == 0
    assert second_verifier.replay_calls == []  # neither theorem's gate re-ran

    sanity_rows_after = _rows(run_dir, "sanity")
    assert len(sanity_rows_after) == 2  # no duplicate/new sanity rows

    cells_after = _rows(run_dir, "cell")
    assert len(cells_after) == EXPECTED_CELLS // 2  # still just B's; A never ran
    assert not any(r["theorem_id"] == "Mini.theoremA" for r in cells_after)


# ---------------------------------------------------------------------------
# (k) determinism of seeded theorem selection
# ---------------------------------------------------------------------------


def test_select_theorems_seeded_selection_is_deterministic(sweep_ctx):
    """`_select_theorems`'s `limit` + `seed` sampling (`random.Random(seed).
    sample(...)`) must be a pure function of its inputs: calling it twice
    with the IDENTICAL spec must return the IDENTICAL theorem, in the same
    order. A sweep resumed later, or run a second time against the same
    config, must draw the same sub-sample rather than a fresh random draw
    each call -- otherwise `resume` semantics (keyed by theorem full_name)
    would be meaningless across separate sweep() invocations of one config.

    (The end-to-end version of this guarantee -- two FRESH sweeps drawing
    identical (model, theorem, k, rung, rollout, seed) key sets, including
    per-row seed values -- is already covered by `test_sweep_determinism`
    above; its key tuple already includes `seed`, so it already fails if a
    differing seed ever leaked in.)
    """
    spec = {"source": "with_proof", "kind": "random", "split": "val", "limit": 1, "seed": 5}
    first = runner._select_theorems(spec)
    second = runner._select_theorems(spec)
    assert len(first) == 1
    assert [t.full_name for t in first] == [t.full_name for t in second]


# ---------------------------------------------------------------------------
# (l) frozen ordering + artifacts (SERIAL sweep only -- see docstring)
# ---------------------------------------------------------------------------


def test_sweep_frozen_ordering_and_artifacts(sweep_ctx, monkeypatch):
    """Pins two invariants not covered by the schema/dispatch tests above:

    1. A SERIAL sweep (`concurrent_gen=False`) writes cell rows to
       `all_rows.jsonl` in the EXACT loop-nest order the module docstring
       promises -- theorem -> k -> rung -> model -> rollout, theorems in
       `_select_theorems` order, rungs/models in config order. A consumer
       that streams `all_rows.jsonl` incrementally (e.g. a live dashboard)
       depends on this ordering, not just on the eventual row SET being
       correct.
    2. Every artifact `sweep()` promises actually exists: the `latest`
       symlink next to `run_dir`, and each theorem's `summary.md` /
       `meta.json`. Also checks `results_root()`'s documented fallback when
       `SMOLBENCH_LEAN_RESULTS` is unset.

    Concurrent sweeps are explicitly OUT of scope for the ordering check:
    `_run_cells_at_step_concurrent` writes rows in `as_completed()` arrival
    order, which is non-deterministic BY DESIGN (gen is fanned out over a
    thread pool) -- frozen ordering is a serial-path-only guarantee.
    """
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"
    runner.sweep(cfg, run_dir, verifier=FakeVerifier())

    # Expected order, derived the same way sweep() itself derives it.
    theorems_ordered = runner._select_theorems(cfg["theorems"])
    expected: list[tuple] = []
    for t in theorems_ordered:
        for k in runner._k_indices(t, cfg["k"]["strategy"]):
            for rung in cfg["rungs"]:
                for mc in cfg["models"]:
                    model_disp = mc.get("display_name", mc["model"])
                    for rollout_idx in range(cfg["n_rollouts"]):
                        expected.append((t.full_name, rung, model_disp, rollout_idx))

    actual: list[tuple] = []
    for line in (run_dir / "all_rows.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") == "cell":
            actual.append((r["theorem_id"], r["rung"], r["model"], r["rollout_idx"]))
    assert actual == expected

    # `latest` symlink lives next to run_dir and resolves to it.
    latest = run_dir.parent / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == run_dir.resolve()

    # Per-theorem artifacts.
    for name in ("Mini.theoremA", "Mini.theoremB"):
        tdir = run_dir / "theorems" / runner.slug_theorem(name)
        assert (tdir / "summary.md").exists()
        assert (tdir / "meta.json").exists()

    # results_root() falls back to notebooks/lean/results when the env
    # override is unset (repo-anchored, never cwd-relative -- see that
    # function's docstring).
    monkeypatch.delenv("SMOLBENCH_LEAN_RESULTS", raising=False)
    root = runner.results_root()
    assert root.parts[-3:] == ("notebooks", "lean", "results")


# ---------------------------------------------------------------------------
# (m) prompt byte-identity: the request body's user message must match
# prompt.build_user_prompt(context.render(...)) EXACTLY, not approximately.
# ---------------------------------------------------------------------------


def test_run_cell_prompt_is_byte_identical_to_build_user_prompt(sweep_ctx):
    """The request body's user-message content must be BYTE-IDENTICAL to
    `prompt.build_user_prompt(context.render(theorem, k, chain, level))`
    computed independently right here in the test, and the system message
    must be `prompt.SYSTEM` exactly. Pins the prompt-assembly contract
    end-to-end: a refactor that trimmed whitespace, changed the
    text-join separator, or reordered system/user construction in
    `run_cell` would still pass the looser
    `body["messages"][1]["content"].endswith(prompt.INSTRUCTION)` check in
    `test_sweep_schema_and_dispatch`, but would fail this exact-equality one.
    """
    theorem = {t.full_name: t for t in corpus.load_split("random", "val")}["Mini.theoremA"]
    k, chain, level = 2, "stepk", 1
    expected_user = prompt.build_user_prompt(context.render(theorem, k, chain, level))

    list(runner.run_cell(
        provider="primeintellect", model=M1, theorem=theorem, k=k, chain=chain,
        level=level, n_rollouts=1, seed=1000, request_timeout=30, max_retries=2,
        verifier=FakeVerifier(),
    ))
    body = _chat_posts(sweep_ctx.pi)[-1]["body"]
    assert body["messages"][0] == {"role": "system", "content": prompt.SYSTEM}
    assert body["messages"][1]["content"] == expected_user


# ---------------------------------------------------------------------------
# (n) display_name aliasing (two model configs, one underlying model id) +
# per-model max_concurrency config is accepted without crashing the sweep.
# ---------------------------------------------------------------------------


def _make_alias_config(concurrent: bool) -> dict:
    return {
        "run_name": "alias",
        "theorems": {
            "source": "explicit", "full_names": ["Mini.theoremA"],
            "kind": "random", "split": "val",
        },
        "k": {"strategy": "last"},
        "rungs": ["stepk:0"],
        "skip_trivial": False,
        "n_rollouts": 1,
        "temperature": 0.5,
        "max_tokens": 256,
        "seed": 1000,
        "request_timeout": 30,
        "max_retries": 2,
        "concurrent_gen": concurrent,
        "max_concurrency": 4,
        "models": [
            {"provider": "primeintellect", "model": M1, "display_name": "alias-one"},
            {"provider": "primeintellect", "model": M1, "display_name": "alias-two",
             "max_concurrency": 1},
        ],
    }


@pytest.mark.parametrize("concurrent", [False, True])
def test_display_name_aliasing_and_per_model_semaphore(sweep_ctx, concurrent):
    """Two model-config entries can share the SAME underlying `model` id
    while being tracked as distinct rows via `display_name` -- rows are
    keyed (written AND resumed) by display_name, not the raw provider model
    id, so a sweep can run one model under two configurations (e.g. one
    `max_concurrency`-capped, one not) without their rows colliding into a
    single key. Also confirms a `max_concurrency` entry doesn't crash sweep
    construction (`model_semaphores`) or, under `concurrent_gen=True`, the
    semaphore-gated `_gated_complete` call path.
    """
    cfg = _make_alias_config(concurrent)
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert n_written == 2  # 1 theorem x 1 rung x 2 aliases x 1 rollout

    cells = _rows(run_dir, "cell")
    by_alias = {r["model"]: r for r in cells}
    assert set(by_alias) == {"alias-one", "alias-two"}
    for r in by_alias.values():
        assert r["api_model"] == M1  # shared underlying provider-facing id

    # Resume respects display_name: both aliases' single cell is already
    # recorded, so a second sweep must skip everything -- 0 new rows, and
    # the two aliases must never collide into one resume key.
    second_written = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert second_written == 0
    assert len(_rows(run_dir, "cell")) == 2


# ---------------------------------------------------------------------------
# (o) _ctx_len_for's best-effort fallback: a lookup failure must not abort
# the sweep, just widen the token-usage guard to a no-op.
# ---------------------------------------------------------------------------


def test_ctx_len_for_falls_back_to_huge_value_on_lookup_failure():
    """`_ctx_len_for`'s best-effort guard: a context-length catalog lookup
    failure (a flaky metadata endpoint, an unlisted model id) must not
    abort the whole sweep. It falls back to `10**9` so `complete()`'s
    token-usage guard simply never fires for this model; a GENUINE
    overflow then surfaces later as the `ValueError` that guard raises,
    which the per-cell exception handling already resumes from (see the
    module docstring's `_ctx_len_for` note) -- trading a hard abort for a
    soft, retryable failure mode instead of silently hiding real problems.
    """
    class _BrokenModule:
        def get_model_context_length(self, model):
            raise RuntimeError("catalog unreachable")

    mc = {"model": "some-model", "provider": "primeintellect"}
    assert runner._ctx_len_for(mc, _BrokenModule()) == 10**9


# ---------------------------------------------------------------------------
# (p) `write_run_analysis`'s `l3` leak-rate column (WP-B2).
#
# Design: `write_run_analysis` is pure JSONL aggregation over an
# `all_rows.jsonl` it can be handed directly (no Dojo session, no sweep) --
# so, mirroring `tests/test_lean_analyze_passn.py`'s approach for the
# separate `cli.cmd_analyze` table (NOT this function; the two share a
# near-identical column layout by convention but are independent
# implementations, and this WP only touches `write_run_analysis`), these
# tests hand-write a small `all_rows.jsonl` straight into a tmp run dir and
# call `write_run_analysis` directly rather than driving a full
# `FakeVerifier` sweep, which would be unable to control `candidate_proof`
# content precisely enough to target specific relic kinds.
# ---------------------------------------------------------------------------


def _l3_row(*, model: str = "m", rung: str = "stepk:0", verdict: str, candidate_proof: str) -> dict:
    """Build one synthetic ``kind: "cell"`` row for the `l3`-column tests.

    Only the fields `write_run_analysis` actually reads are populated;
    token/timing fields are omitted deliberately (the function's own
    ``r.get(..., 0)`` defaults cover their absence) to keep each fixture
    row focused on the one thing each test varies: `candidate_proof`.
    """
    return {
        "kind": "cell", "rung": rung, "model": model,
        "verdict": verdict, "candidate_proof": candidate_proof,
    }


def _write_all_rows(run_dir: Path, rows: list[dict]) -> None:
    """Write `rows` as ``run_dir/all_rows.jsonl``, creating `run_dir` first."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "all_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _l3_data_row(analysis_text: str) -> list[str]:
    """Whitespace-split fields of the single (rung, model) data row.

    `write_run_analysis` emits exactly one table (unlike `cli.cmd_analyze`'s
    three), so the data row directly follows the ``"-" * len(header)``
    separator line; every field is whitespace-delimited with no internal
    spaces (see the header's fixed-width format strings in `runner.py`), so
    a plain `str.split()` per row is unambiguous.
    """
    lines = analysis_text.splitlines()
    sep_idx = next(i for i, line in enumerate(lines) if line.startswith("---"))
    (row,) = [lines[sep_idx + 1]] if not lines[sep_idx + 1].startswith("#") else [lines[sep_idx + 2]]
    return row.split()


def _header_l3_index(analysis_text: str) -> int:
    """Column index of ``l3`` in the (whitespace-split) table header."""
    header = next(line for line in analysis_text.splitlines() if "l3" in line and "exc" in line)
    return header.split().index("l3")


def test_l3_counts_parse_level_relics_and_excludes_clean(tmp_path, monkeypatch):
    """`existsi z` and `intros f,` are parse-level relics (no align map
    needed -- see `lean3.find_relics`'s `existsi` and `trailing-comma`
    rules); `rfl` is clean Lean 4. Chosen so this test is env-independent:
    with no align map, `l3` must count exactly 2 of the 3 cells, not 3, and
    the "align asset not built" marker line must appear."""
    # Point SMOLBENCH_LEAN_DATA at a tmp subdir so `AlignMap.load()` (which
    # resolves the asset BESIDE the data root, at data_root().parent --
    # i.e. tmp_path here, which holds no asset) deterministically returns
    # `None` regardless of whether a real `lean3_align.json.gz` has been
    # built elsewhere in this checkout.
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "data"))
    run_dir = tmp_path / "run"
    _write_all_rows(run_dir, [
        _l3_row(verdict="lean_error", candidate_proof="existsi z"),
        _l3_row(verdict="lean_error", candidate_proof="intros f,"),
        _l3_row(verdict="success", candidate_proof="rfl"),
    ])

    runner.write_run_analysis(run_dir)
    text = (run_dir / "analysis.txt").read_text()

    assert "# l3 = parse-level only (lean3_align.json.gz not built)" in text
    fields = _l3_data_row(text)
    assert fields[0] == "stepk:0" and fields[1] == "m"
    assert fields[2] == "1/3"  # only the clean `rfl` row verified.
    l3_idx = _header_l3_index(text)
    assert fields[l3_idx] == "2"  # existsi + trailing-comma, NOT the clean rfl.
    assert "l3=2" in text.splitlines()[-1]  # per-model totals line.


def test_l3_counts_name_level_relic_when_align_map_present(tmp_path, monkeypatch):
    """With a `lean3_align.json.gz` present, a comma-free mathlib3 lemma
    name (`supr_le`, uncatchable at parse level alone) is now counted, and
    the "not built" marker line disappears."""
    data_dir = tmp_path / "data"
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(data_dir))
    data_dir.mkdir(parents=True)
    # The asset lives BESIDE the benchmark dir (data_root().parent -- see
    # lean3.AlignMap.load), i.e. at tmp_path here, not inside data_dir.
    with gzip.open(tmp_path / lean3.ALIGN_ASSET_NAME, "wt", encoding="utf-8") as f:
        json.dump({"lean3_to_lean4": {"supr_le": "iSup_le"}}, f)

    run_dir = tmp_path / "run"
    _write_all_rows(run_dir, [
        _l3_row(verdict="lean_error", candidate_proof="apply supr_le"),
    ])

    runner.write_run_analysis(run_dir)
    text = (run_dir / "analysis.txt").read_text()

    assert "not built" not in text
    fields = _l3_data_row(text)
    l3_idx = _header_l3_index(text)
    assert fields[l3_idx] == "1"
