"""Test smolbench.deduction.lean.runner.

The Lean verifier is faked (FakeVerifier), so the whole sweep runs with no
lean_dojo. Generation goes to two local OpenAI-compatible stub servers, one
per provider. Verification is driven by a marker string in the model's reply.
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
from conftest import StubServer, chat_completion
from tests._paths import LEAN_MINI as FIXTURE

# Session-unique model ids so provider get_model_context_length lru_caches
# don't bleed a stale ctx-length in from another test module.
M1 = "mini/pi-model-a"       # provider: primeintellect
M2 = "mini/or-model-b"       # provider: openrouter

# A candidate proof "verifies" (FakeVerifier) iff it contains this marker.
MARKER = "QED"


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
    """Stands in for smolbench.deduction.lean.verify without lean_dojo."""

    ProofResult = FakeProofResult

    def replay_ground_truth(self, bt, timeout=600):
        n = len(bt.traced_tactics)
        return FakeReplayResult(bt.full_name, "success", n, n)

    @contextmanager
    def open_at_step(self, bt, k, timeout=600):
        yield ("fake-dojo", f"state@k={k}")

    def try_tail(self, dojo, state_at_k, tail, theorem_name):
        ok = MARKER in tail
        return FakeProofResult(theorem_name, "success" if ok else "lean_error", tail,
                               error=None if ok else "marker absent")

    def verify_proof_tail(self, bt, k, tail, timeout=600):
        ok = MARKER in tail
        return FakeProofResult(bt.full_name, "success" if ok else "lean_error", tail,
                               error=None if ok else "marker absent")


class SpyVerifier(FakeVerifier):
    """Counts/records calls, to pin sweep()'s one-Dojo-per-(theorem, k) contract."""

    def __init__(self):
        self.open_count = 0
        self.tail_tokens: list[tuple[str, str]] = []
        self.replay_calls: list[str] = []

    def replay_ground_truth(self, bt, timeout=600):
        self.replay_calls.append(bt.full_name)
        return super().replay_ground_truth(bt, timeout=timeout)

    @contextmanager
    def open_at_step(self, bt, k, timeout=600):
        self.open_count += 1
        yield (f"dojo-{self.open_count}-{bt.full_name}-k{k}", f"state@k={k}")

    def try_tail(self, dojo, state_at_k, tail, theorem_name):
        self.tail_tokens.append((theorem_name, dojo))
        return super().try_tail(dojo, state_at_k, tail, theorem_name)


class ConfigurableSanityVerifier(FakeVerifier):
    """FakeVerifier whose sanity-gate verdict is configurable per theorem."""

    def __init__(self, verdict_by_theorem: dict[str, str]):
        self.verdict_by_theorem = verdict_by_theorem
        self.replay_calls: list[str] = []

    def replay_ground_truth(self, bt, timeout=600):
        self.replay_calls.append(bt.full_name)
        n = len(bt.traced_tactics)
        verdict = self.verdict_by_theorem.get(bt.full_name, "success")
        return FakeReplayResult(
            bt.full_name, verdict, n if verdict == "success" else 0, n,
            error=None if verdict == "success" else "synthetic sanity failure")


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


def _make_config(concurrent=False, **overrides):
    """Base sweep config; `overrides` replace top-level keys wholesale."""
    cfg = {
        "run_name": "mini",
        "theorems": {"source": "explicit", "kind": "random", "split": "val",
                     "full_names": ["Mini.theoremA", "Mini.theoremB"]},
        "k": {"strategy": "last"},
        "rungs": ["stepk:0", "stepk:1"],
        "skip_trivial": False,        # deterministic cell count, no skips
        "n_replicates": 2,
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
    cfg.update(overrides)
    return cfg


# BASE config only: theorems(2) x rungs(2) x models(2) x replicates(2).
EXPECTED_CELLS = 16

REQUIRED_ROW_KEYS = {
    "kind", "theorem_id", "file_path", "k", "n_total_tactics", "chain",
    "level", "rung", "replicate_idx", "model", "api_model", "provider", "seed",
    "temperature", "context_chars", "ground_truth_remaining", "prompt_tokens",
    "completion_tokens", "cache_read_tokens", "cache_creation_tokens",
    "gen_ms", "verify_ms", "candidate_proof", "raw_response",
    "reasoning_content", "verdict", "lean_error", "final_state_pp",
    "finish_reason",
}


def _rows(run_dir, kind):
    rows = [json.loads(l) for l in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    return [r for r in rows if r.get("kind") == kind]


def _key(r):
    return (r["model"], r["theorem_id"], r["k"], r["rung"], r["replicate_idx"])


def _chat_posts(stub):
    """POST /chat/completions requests only (GET ctx-length lookups have body=None)."""
    return [req for req in stub.requests
            if req.get("body") is not None and req["path"].endswith("/chat/completions")]


def _theorem(name="Mini.theoremA"):
    return {t.full_name: t for t in corpus.load_split("random", "val")}[name]


def _run_cell(theorem, **kw):
    return list(runner.run_cell(**{
        "theorem": theorem, "provider": "primeintellect", "model": M1, "k": 2,
        "chain": "stepk", "level": 0, "n_replicates": 1, "seed": 1000,
        "request_timeout": 30, "max_retries": 2, "verifier": FakeVerifier(), **kw}))


def _force_exception(run_dir, theorem=None):
    """Make one cell's ONLY recorded verdict "exception" (appending can't); return key."""
    path = run_dir / "all_rows.jsonl"
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        r = json.loads(line)
        if r.get("kind") == "cell" and theorem in (None, r["theorem_id"]):
            key = _key(r)
            r["verdict"] = "exception"
            lines[i] = json.dumps(r, ensure_ascii=False)
            path.write_text("\n".join(lines) + "\n")
            return key
    raise AssertionError("no cell row to fail")


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_schema_and_dispatch(sweep_ctx, concurrent):
    """Row schema, seed threading, per-model dispatch, outputs, and artifacts."""
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(_make_config(concurrent), run_dir, verifier=FakeVerifier())
    assert n_written == EXPECTED_CELLS
    cells = _rows(run_dir, "cell")
    assert len(cells) == EXPECTED_CELLS
    for r in cells:
        assert REQUIRED_ROW_KEYS <= set(r), REQUIRED_ROW_KEYS - set(r)
        assert r["seed"] == 1000 + r["replicate_idx"]
        assert r["verdict"] == "success"      # marker present in every reply
        assert r["temperature"] == 0.5
    pi_posts = _chat_posts(sweep_ctx.pi)
    or_posts = _chat_posts(sweep_ctx.orr)
    assert len(pi_posts) == len(or_posts) == EXPECTED_CELLS // 2
    assert {p["body"]["model"] for p in pi_posts} == {M1}
    assert {p["body"]["model"] for p in or_posts} == {M2}
    for p in pi_posts + or_posts:
        body = p["body"]
        assert body["seed"] in (1000, 1001)
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 256
        assert body["messages"][0] == {"role": "system", "content": prompt.SYSTEM}
        assert body["messages"][1]["role"] == "user"
        assert body["messages"][1]["content"].endswith(prompt.INSTRUCTION)
    assert {p["body"]["seed"] for p in pi_posts} == {1000, 1001}
    # extra_params rides through only for the model that declared it.
    assert all(p["body"].get("reasoning_effort") == "high" for p in pi_posts)
    assert all("reasoning_effort" not in p["body"] for p in or_posts)
    all_keys = {_key(r) for r in cells}
    assert len(all_keys) == EXPECTED_CELLS
    out_keys = {_key(json.loads(line))
                for jl in (run_dir / "theorems").rglob("outputs/*.jsonl")
                for line in jl.read_text().splitlines()}
    assert out_keys == all_keys
    assert {r["theorem_id"] for r in _rows(run_dir, "sanity")} == {"Mini.theoremA",
                                                                  "Mini.theoremB"}
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["counts"]["written"] == EXPECTED_CELLS
    assert (run_dir / "analysis.txt").read_text().strip()


def test_sweep_resume_and_exception_rerun(sweep_ctx):
    """A clean resume re-runs nothing; a cell recorded only as exception re-runs."""
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == EXPECTED_CELLS
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == 0
    assert len(_rows(run_dir, "sanity")) == 2
    target = _force_exception(run_dir)
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == 1
    assert [r for r in _rows(run_dir, "cell")
            if _key(r) == target and r["verdict"] != "exception"]


def test_existing_keys_reruns_only_cells_that_never_reached_the_model(tmp_path):
    """`prompt_tokens > 0` is the line between lost data and real data."""
    def cell(theorem, verdict, proof="", error="", prompt_tokens=0):
        return {"kind": "cell", "model": "m", "theorem_id": theorem, "k": 1,
                "rung": "stepk:1", "replicate_idx": 0, "verdict": verdict,
                "candidate_proof": proof, "lean_error": error,
                "prompt_tokens": prompt_tokens, "completion_tokens": 0}

    path = tmp_path / "all_rows.jsonl"
    rows = [
        # (1) LOST: every attempt died before the model saw the prompt.
        cell("lost.never_asked", "exception",
             error="RuntimeError: spot instance terminated", prompt_tokens=0),
        cell("lost.never_asked", "unverified", proof="", prompt_tokens=0),
        # (2) DATA: a later attempt ran and answered emptily -> resampling.
        cell("data.answered_empty_after_infra", "exception",
             error="RuntimeError: spot instance terminated", prompt_tokens=0),
        cell("data.answered_empty_after_infra", "unverified", proof="",
             prompt_tokens=398),
        # (3) DATA: asked, answered nothing, nothing ever failed.
        cell("data.plain_empty", "unverified", proof="", prompt_tokens=398),
        # (4) DONE: has a proof.
        cell("done.has_proof", "unverified", proof="exact foo", prompt_tokens=398),
        # (5) RE-RUN: only record is an exception, so the proof was never checked.
        cell("rerun.only_an_exception", "exception", proof="exact bar",
             error="RuntimeError: dojo", prompt_tokens=398),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    skip = runner._existing_keys(path)

    def key(theorem):
        return runner._row_key("m", theorem, 1, "stepk:1", 0)

    assert key("lost.never_asked") not in skip, "infra loss must still be recoverable"
    assert key("data.answered_empty_after_infra") in skip, (
        "re-running a cell the model already answered is resampling")
    assert key("data.plain_empty") in skip
    assert key("done.has_proof") in skip
    assert key("rerun.only_an_exception") not in skip


def test_run_cell_prompt_is_byte_identical_to_build_user_prompt(sweep_ctx):
    """run_cell's request body matches prompt.build_user_prompt(context.render(...))."""
    theorem = _theorem()
    k, chain, level = 2, "stepk", 1
    expected_user = prompt.build_user_prompt(context.render(theorem, k, chain, level))
    rows = _run_cell(theorem, k=k, chain=chain, level=level, n_replicates=2)
    assert len(rows) == 2
    for i, r in enumerate(rows):
        assert r["seed"] == 1000 + i
        assert r["provider"] == "primeintellect"
        assert r["model"] == M1
        assert r["verdict"] == "success"
    pi_posts = _chat_posts(sweep_ctx.pi)
    assert len(pi_posts) == 2
    assert {p["body"]["seed"] for p in pi_posts} == {1000, 1001}
    for p in pi_posts:
        assert p["body"]["messages"][0] == {"role": "system", "content": prompt.SYSTEM}
        assert p["body"]["messages"][1]["content"] == expected_user


def test_reasoning_only_cap_hit_is_never_graded_as_a_proof(sweep_ctx):
    """Retained reasoning text stays out of the candidate; finish_reason is verbatim."""
    sweep_ctx.pi.default_response = {
        "choices": [{"message": {"content": None,
                                 "reasoning_content": f"I will now write {MARKER}"},
                     "finish_reason": "length"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 32768, "total_tokens": 40},
    }
    row = _run_cell(_theorem())[0]
    assert row["verdict"] != "success"          # the marker did NOT become a proof
    assert row["candidate_proof"] == ""
    assert row["raw_response"] == ""
    assert MARKER in row["reasoning_content"]   # but the reasoning IS preserved
    assert row["finish_reason"] == "length"
    assert row["completion_tokens"] == 32768


def test_cli_help_subprocess():
    result = subprocess.run([sys.executable, "-m", "smolbench.deduction.lean.cli",
                             "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage" in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("concurrent", [False, True])
def test_complete_receives_max_retries_request_timeout_system_seed(
        sweep_ctx, monkeypatch, concurrent):
    """Every generation call forwards retries/timeout/system/ctx-length and its seed."""
    import smolbench.evals.providers.openrouter as orr
    import smolbench.evals.providers.primeintellect as pi
    calls: list[dict] = []

    def _spy(real):
        def _wrapped(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return real(*args, **kwargs)
        return _wrapped

    # Patch the module ATTRIBUTE: every call site does `mod.complete(...)`.
    monkeypatch.setattr(pi, "complete", _spy(pi.complete))
    monkeypatch.setattr(orr, "complete", _spy(orr.complete))
    cfg = _make_config(concurrent, request_timeout=33, max_retries=2)
    run_dir = sweep_ctx.tmp / "run"
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == EXPECTED_CELLS
    assert len(calls) == EXPECTED_CELLS
    seeds_seen: list[int] = []
    for call in calls:
        kwargs = call["kwargs"]
        assert kwargs["max_retries"] == 2
        assert kwargs["request_timeout"] == 33
        assert kwargs["system"] == prompt.SYSTEM
        assert kwargs["context_length"] == 100000  # stub's fixed GET response
        seeds_seen.append(call["args"][2])         # complete(prompt, model, seed, ...)
    assert set(seeds_seen) == {1000, 1001}
    assert seeds_seen.count(1000) == seeds_seen.count(1001) == EXPECTED_CELLS // 2


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_shares_one_dojo_session_per_theorem_k(sweep_ctx, concurrent):
    """One open_at_step per (theorem, k), shared across rungs/models/replicates."""
    run_dir = sweep_ctx.tmp / "run"
    verifier = SpyVerifier()
    n_written = runner.sweep(_make_config(concurrent), run_dir, verifier=verifier)
    assert n_written == EXPECTED_CELLS
    # k.strategy "last" -> exactly one k per theorem -> 2 theorems == 2 opens.
    assert verifier.open_count == 2
    by_theorem: dict[str, set] = {}
    for name, token in verifier.tail_tokens:
        by_theorem.setdefault(name, set()).add(token)
    assert set(by_theorem) == {"Mini.theoremA", "Mini.theoremB"}
    for name, tokens in by_theorem.items():
        assert len(tokens) == 1, f"{name} used more than one Dojo token: {tokens}"
    assert len({t for tokens in by_theorem.values() for t in tokens}) == 2
    assert len(verifier.tail_tokens) == EXPECTED_CELLS
    assert verifier.replay_calls == ["Mini.theoremA", "Mini.theoremB"]


def test_sweep_skips_trivial_rungs(sweep_ctx):
    """skip_trivial=True drops exactly the cells `is_trivial_rung` calls trivial."""
    theorems = {t.full_name: t for t in corpus.load_split("random", "val")}
    rungs = ["stepk:0", "stepk:1"]
    trivial_pairs = set()
    for name, t in theorems.items():
        k = runner._k_indices(t, "first")[0]
        for rung in rungs:
            chain, level = rung.split(":", 1)
            if context.is_trivial_rung(t, k, chain, int(level)):
                trivial_pairs.add((name, rung))
    assert trivial_pairs, (
        "fixture no longer produces any trivial rung under k=first -- "
        "update this test's config/fixture expectations")
    cfg = _make_config(run_name="trivial", k={"strategy": "first"}, skip_trivial=True,
                       models=[{"provider": "primeintellect", "model": M1},
                               {"provider": "openrouter", "model": M2}])
    run_dir = sweep_ctx.tmp / "run"
    runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    cells = _rows(run_dir, "cell")
    all_pairs = {(name, rung) for name in theorems for rung in rungs}
    assert {(r["theorem_id"], r["rung"]) for r in cells} == all_pairs - trivial_pairs
    assert len(cells) == ((len(all_pairs) - len(trivial_pairs))
                          * len(cfg["models"]) * cfg["n_replicates"])


def test_sanity_gate_fail_and_resume_exclusion(sweep_ctx):
    """A recorded sanity FAILURE keeps its theorem excluded on resume."""
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"
    first_verifier = ConfigurableSanityVerifier({"Mini.theoremA": "lean_error"})
    n_written = runner.sweep(cfg, run_dir, verifier=first_verifier)
    sanity_rows = {r["theorem_id"]: r for r in _rows(run_dir, "sanity")}
    assert sanity_rows["Mini.theoremA"]["verdict"] == "lean_error"
    assert sanity_rows["Mini.theoremB"]["verdict"] == "success"
    cells = _rows(run_dir, "cell")
    assert not any(r["theorem_id"] == "Mini.theoremA" for r in cells)
    assert len(cells) == n_written == EXPECTED_CELLS // 2
    assert first_verifier.replay_calls == ["Mini.theoremA", "Mini.theoremB"]
    # Resume with a verifier that WOULD now report success for A.
    second_verifier = ConfigurableSanityVerifier({})
    assert runner.sweep(cfg, run_dir, verifier=second_verifier) == 0
    assert second_verifier.replay_calls == []  # neither theorem's gate re-ran
    assert len(_rows(run_dir, "sanity")) == 2  # no duplicate/new sanity rows
    cells_after = _rows(run_dir, "cell")
    assert len(cells_after) == EXPECTED_CELLS // 2
    assert not any(r["theorem_id"] == "Mini.theoremA" for r in cells_after)


def test_select_theorems_shards_partition_the_unsharded_selection(sweep_ctx):
    """Seeded selection is deterministic; `shard: "i/n"` slices it after sampling."""
    base = {"source": "with_proof", "kind": "random", "split": "val",
            "limit": 0, "seed": 0}
    whole = [t.full_name for t in runner._select_theorems(base)]
    assert whole == [t.full_name for t in runner._select_theorems(base)]
    assert len(whole) >= 2  # fixture must give the slices something to split
    seen: list[str] = []
    for i in range(3):
        names = [t.full_name
                 for t in runner._select_theorems({**base, "shard": f"{i}/3"})]
        assert names == whole[i::3]
        seen.extend(names)
    assert sorted(seen) == sorted(whole)
    assert len(seen) == len(set(seen))  # pairwise disjoint
    # A malformed shard must raise, never silently return the FULL pool.
    for bad in ("3/3", "-1/3", "0", "0of3", "a/b", "1/0"):
        with pytest.raises(ValueError):
            runner._select_theorems({**base, "shard": bad})


def test_load_cell_whitelist_parses_and_dedupes(tmp_path):
    """Valid entries parse into `_row_key`-shaped tuples; duplicates collapse."""
    path = tmp_path / "wl.json"
    path.write_text(json.dumps([["m", "T", 1, "stepk:1", 0],
                                ["m", "T", 1, "stepk:1", 0],
                                ["m", "U", 2, "hint:2", 1]]))
    assert runner.load_cell_whitelist(str(path)) == frozenset(
        {("m", "T", 1, "stepk:1", 0), ("m", "U", 2, "hint:2", 1)})


@pytest.mark.parametrize("content", [
    None,                                    # missing file
    "{not valid json",
    json.dumps({"not": "a list"}),
    json.dumps([["too", "few", "elements"]]),
])
def test_load_cell_whitelist_rejects_bad_input(tmp_path, content):
    path = tmp_path / "wl.json"
    if content is not None:
        path.write_text(content)
    with pytest.raises(ValueError):
        runner.load_cell_whitelist(str(path))


def test_hash_cell_keys_is_order_and_type_independent():
    """The digest depends only on the SET of keys, not on-disk order or type."""
    keys_a = [("m", "T", 1, "stepk:1", 0), ("m", "U", 2, "hint:2", 1)]
    keys_b = [["m", "U", 2, "hint:2", 1], ["m", "T", 1, "stepk:1", 0]]
    assert runner.hash_cell_keys(keys_a) == runner.hash_cell_keys(keys_b)
    assert (runner.hash_cell_keys([("m", "T", 1, "stepk:1", 0)])
            != runner.hash_cell_keys([("m", "T", 1, "stepk:1", 1)]))


@pytest.mark.parametrize("concurrent", [False, True])
def test_cell_whitelist_restricts_sweep_to_exactly_the_listed_cells(
        sweep_ctx, monkeypatch, concurrent):
    """LEAN_CELL_WHITELIST=<path> runs ONLY the whitelisted cells."""
    cfg = _make_config(concurrent)
    baseline_dir = sweep_ctx.tmp / "baseline"
    runner.sweep(cfg, baseline_dir, verifier=FakeVerifier())
    all_keys = sorted(_key(r) for r in _rows(baseline_dir, "cell"))
    assert len(all_keys) == EXPECTED_CELLS
    # A strict subset of theoremA's cells; theoremB owns none, so its sanity
    # gate must never run (theorem-level pre-filter).
    theorem_a_keys = [k for k in all_keys if k[1] == "Mini.theoremA"]
    assert len(theorem_a_keys) >= 3
    whitelist_keys = theorem_a_keys[:3]
    whitelist_path = sweep_ctx.tmp / "whitelist.json"
    whitelist_path.write_text(json.dumps([list(k) for k in whitelist_keys]))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(whitelist_path))
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert n_written == len(whitelist_keys)
    assert sorted(_key(r) for r in _rows(run_dir, "cell")) == sorted(whitelist_keys)
    assert {r["theorem_id"] for r in _rows(run_dir, "sanity")} == {"Mini.theoremA"}


@pytest.mark.parametrize("content", [
    None,                                             # missing file
    "{not valid json",
    json.dumps([["only", "four", "elements", 0]]),    # malformed shape
])
def test_cell_whitelist_bad_file_raises_and_writes_nothing(sweep_ctx, monkeypatch,
                                                           content):
    """A bad LEAN_CELL_WHITELIST aborts at sweep start, never a full unfiltered run."""
    path = sweep_ctx.tmp / "bad_whitelist.json"
    if content is not None:
        path.write_text(content)
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(path))
    run_dir = sweep_ctx.tmp / "run"
    with pytest.raises(ValueError):
        runner.sweep(_make_config(concurrent=False), run_dir, verifier=FakeVerifier())
    assert not (run_dir / "all_rows.jsonl").exists()


def test_sweep_frozen_ordering_and_artifacts(sweep_ctx, monkeypatch):
    """A SERIAL sweep writes rows in loop-nest order and emits every artifact.

    Concurrent sweeps write in `as_completed()` order, non-deterministic by design.
    """
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"
    runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    expected: list[tuple] = []
    for t in runner._select_theorems(cfg["theorems"]):
        for _k in runner._k_indices(t, cfg["k"]["strategy"]):
            for rung in cfg["rungs"]:
                for mc in cfg["models"]:
                    for replicate_idx in range(cfg["n_replicates"]):
                        expected.append((t.full_name, rung,
                                         mc.get("display_name", mc["model"]),
                                         replicate_idx))
    assert [(r["theorem_id"], r["rung"], r["model"], r["replicate_idx"])
            for r in _rows(run_dir, "cell")] == expected
    latest = run_dir.parent / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == run_dir.resolve()
    for name in ("Mini.theoremA", "Mini.theoremB"):
        tdir = run_dir / "theorems" / runner.slug_theorem(name)
        assert (tdir / "summary.md").exists()
        assert (tdir / "meta.json").exists()
    # results_root() is repo-anchored, never cwd-relative, when the env is unset.
    monkeypatch.delenv("SMOLBENCH_LEAN_RESULTS", raising=False)
    root = runner.results_root()
    assert root.is_absolute()
    assert root.parts[-3:] == ("notebooks", "deduction", "results")


@pytest.mark.parametrize("concurrent", [False, True])
def test_display_name_aliasing_and_per_model_semaphore(sweep_ctx, concurrent):
    """Two model configs sharing one `model` id stay distinct rows via display_name."""
    cfg = _make_config(
        concurrent, run_name="alias", rungs=["stepk:0"], n_replicates=1,
        theorems={"source": "explicit", "kind": "random", "split": "val",
                  "full_names": ["Mini.theoremA"]},
        models=[{"provider": "primeintellect", "model": M1, "display_name": "alias-one"},
                {"provider": "primeintellect", "model": M1, "display_name": "alias-two",
                 "max_concurrency": 1}])
    run_dir = sweep_ctx.tmp / "run"
    n_written = runner.sweep(cfg, run_dir, verifier=FakeVerifier())
    assert n_written == 2  # 1 theorem x 1 rung x 2 aliases x 1 replicate
    by_alias = {r["model"]: r for r in _rows(run_dir, "cell")}
    assert set(by_alias) == {"alias-one", "alias-two"}
    for r in by_alias.values():
        assert r["api_model"] == M1  # shared underlying provider-facing id
    # Resume is keyed by display_name: the two aliases never collide.
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == 0
    assert len(_rows(run_dir, "cell")) == 2


def test_ctx_len_for_falls_back_to_huge_value_on_lookup_failure():
    """A catalog lookup failure widens the token guard instead of aborting the sweep."""
    class _BrokenModule:
        def get_model_context_length(self, model):
            raise RuntimeError("catalog unreachable")

    assert runner._ctx_len_for({"model": "some-model", "provider": "primeintellect"},
                               _BrokenModule()) == 10**9


def _l3_row(*, model="m", rung="stepk:0", verdict, candidate_proof) -> dict:
    """One synthetic `kind: "cell"` row with only the fields write_run_analysis reads."""
    return {"kind": "cell", "rung": rung, "model": model,
            "verdict": verdict, "candidate_proof": candidate_proof}


def _write_all_rows(run_dir: Path, rows: list[dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "all_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _l3_data_row(analysis_text: str) -> list[str]:
    """Whitespace-split fields of the single (rung, model) data row."""
    lines = analysis_text.splitlines()
    sep_idx = next(i for i, line in enumerate(lines) if line.startswith("---"))
    (row,) = ([lines[sep_idx + 1]] if not lines[sep_idx + 1].startswith("#")
              else [lines[sep_idx + 2]])
    return row.split()


def _header_l3_index(analysis_text: str) -> int:
    header = next(line for line in analysis_text.splitlines()
                  if "l3" in line and "exc" in line)
    return header.split().index("l3")


@pytest.mark.parametrize("align,proofs,expected_verified,expected_l3", [
    # Parse-level relics (existsi, trailing comma); `rfl` is clean Lean 4.
    (None, [("lean_error", "existsi z"), ("lean_error", "intros f,"),
            ("success", "rfl")], "1/3", "2"),
    # A comma-free mathlib3 name is only catchable with an align map.
    ({"supr_le": "iSup_le"}, [("lean_error", "apply supr_le")], "0/1", "1"),
])
def test_l3_counts_relics(tmp_path, monkeypatch, align, proofs, expected_verified,
                          expected_l3):
    """The `l3` column counts relic-bearing cells; the align asset widens detection."""
    # AlignMap.load() resolves the asset at data_root().parent == tmp_path.
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "data"))
    if align is not None:
        with gzip.open(tmp_path / lean3.ALIGN_ASSET_NAME, "wt", encoding="utf-8") as f:
            json.dump({"lean3_to_lean4": align}, f)
    run_dir = tmp_path / "run"
    _write_all_rows(run_dir, [_l3_row(verdict=v, candidate_proof=p) for v, p in proofs])
    runner.write_run_analysis(run_dir)
    text = (run_dir / "analysis.txt").read_text()
    marker = "# l3 = parse-level only (lean3_align.json.gz not built)"
    assert (marker in text) is ("not built" in text) is (align is None)
    fields = _l3_data_row(text)
    assert fields[0] == "stepk:0" and fields[1] == "m"
    assert fields[2] == expected_verified
    assert fields[_header_l3_index(text)] == expected_l3
    assert f"l3={expected_l3}" in text.splitlines()[-1]  # per-model totals line


def _nullverifier():
    from smolbench.deduction.lean.nullverify import NullVerifier

    return NullVerifier()


def test_nullverify_imports_without_verify_module_subprocess():
    """`nullverify` must import WITHOUT dragging in `verify` (and lean_dojo)."""
    code = (
        "import sys\n"
        "from smolbench.deduction.lean.nullverify import NullVerifier\n"
        "assert 'smolbench.deduction.lean.verify' not in sys.modules, "
        "'nullverify pulled in verify'\n"
        "v = NullVerifier()\n"
        "assert hasattr(v, 'replay_ground_truth') and hasattr(v, 'open_at_step')\n"
        "assert hasattr(v, 'try_tail')\n"
        "print('OK')\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


@pytest.mark.parametrize("concurrent", [False, True])
def test_nullverify_sweep_generates_all_theorems(sweep_ctx, concurrent):
    """A NullVerifier sweep generates the FULL cell grid, verifying nothing."""
    cfg = _make_config(concurrent)
    run_dir = sweep_ctx.tmp / "run"
    assert runner.sweep(cfg, run_dir, verifier=_nullverifier()) == EXPECTED_CELLS
    sanity_rows = _rows(run_dir, "sanity")
    assert {r["theorem_id"] for r in sanity_rows} == {"Mini.theoremA", "Mini.theoremB"}
    assert all(r["verdict"] == "skipped" for r in sanity_rows), sanity_rows
    cells = _rows(run_dir, "cell")
    assert len(cells) == EXPECTED_CELLS
    assert {r["theorem_id"] for r in cells} == {"Mini.theoremA", "Mini.theoremB"}
    assert all(r["verdict"] == "unverified" for r in cells), (
        sorted({r["verdict"] for r in cells}))
    assert all(r["seed"] == cfg["seed"] + r["replicate_idx"] for r in cells)
    assert (len(_chat_posts(sweep_ctx.pi)) + len(_chat_posts(sweep_ctx.orr))
            == EXPECTED_CELLS)


@pytest.mark.parametrize("verdict", ["lean_error", "incomplete", "given_up",
                                     "exception", "replay_failed"])
def test_sanity_gate_still_excludes_on_explicit_failure_verdicts(sweep_ctx, verdict):
    """Every explicit FAILURE verdict still gates its theorem out of generation."""
    run_dir = sweep_ctx.tmp / "run"
    v = ConfigurableSanityVerifier({"Mini.theoremA": verdict})
    n_written = runner.sweep(_make_config(concurrent=False), run_dir, verifier=v)
    cells = _rows(run_dir, "cell")
    assert not any(r["theorem_id"] == "Mini.theoremA" for r in cells), verdict
    assert n_written == EXPECTED_CELLS // 2


def test_sanity_gate_passes_through_non_failure_verdict_on_fresh_and_resume(sweep_ctx):
    """A "skipped" sanity verdict generates cells on the fresh AND the resume path."""
    cfg = _make_config(concurrent=False)
    run_dir = sweep_ctx.tmp / "run"
    v = ConfigurableSanityVerifier({"Mini.theoremA": "skipped"})
    assert runner.sweep(cfg, run_dir, verifier=v) == EXPECTED_CELLS
    assert {r["theorem_id"] for r in _rows(run_dir, "cell")} == {"Mini.theoremA",
                                                                "Mini.theoremB"}
    # Resume: drop A's cell rows, keep its recorded "skipped" sanity row.
    all_rows_path = run_dir / "all_rows.jsonl"
    kept = [line for line in all_rows_path.read_text().splitlines()
            if not (json.loads(line).get("kind") == "cell"
                    and json.loads(line)["theorem_id"] == "Mini.theoremA")]
    all_rows_path.write_text("\n".join(kept) + "\n")
    second = runner.sweep(cfg, run_dir, verifier=ConfigurableSanityVerifier({}))
    assert second == EXPECTED_CELLS // 2, "resume excluded the 'skipped' theorem"
    assert len(_rows(run_dir, "sanity")) == 2  # gate did not re-replay
    # Exception-rerun is unchanged for a theorem recorded as "skipped": only
    # that one cell re-runs.
    target = _force_exception(run_dir, theorem="Mini.theoremA")
    assert runner.sweep(cfg, run_dir, verifier=ConfigurableSanityVerifier({})) == 1
    assert [r for r in _rows(run_dir, "cell")
            if _key(r) == target and r["verdict"] != "exception"]
