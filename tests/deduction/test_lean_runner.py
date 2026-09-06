"""Test smolbench.deduction.lean.runner with a faked verifier (no lean_dojo) and
two local OpenAI-compatible stub servers; a proof verifies iff it holds MARKER.
"""

import json
import re
import shutil
import subprocess
import sys
import threading
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import smolbench.deduction.lean.context as context
import smolbench.deduction.lean.corpus as corpus
import smolbench.deduction.lean.prompt as prompt
import smolbench.deduction.lean.runner as runner
from conftest import StubServer, chat_completion
from tests._paths import LEAN_MINI as FIXTURE, LEAN_MINI_POSTCUTOFF as POSTCUTOFF

M1 = "mini/pi-model-a"       # provider: primeintellect
M2 = "mini/or-model-b"       # provider: openrouter
MARKER = "QED"


def _proof(theorem, verdict, tail_tried, error=None, final_state_pp=None):
    return SimpleNamespace(theorem=theorem, verdict=verdict, tail_tried=tail_tried,
                           error=error, final_state_pp=final_state_pp)


def _graded(theorem, tail):
    ok = MARKER in tail
    return _proof(theorem, "success" if ok else "lean_error", tail,
                  error=None if ok else "marker absent")


class FakeVerifier:
    """Stands in for ...lean.verify: records calls, sanity verdicts configurable."""

    ProofResult = staticmethod(_proof)

    def __init__(self, sanity=None):
        self.sanity = sanity or {}
        self.replay_calls: list[str] = []
        self.tail_tokens: list[tuple[str, str]] = []
        self.open_count = 0

    def replay_ground_truth(self, bt, timeout=600):
        self.replay_calls.append(bt.full_name)
        n = len(bt.traced_tactics)
        verdict = self.sanity.get(bt.full_name, "success")
        ok = verdict == "success"
        return SimpleNamespace(theorem=bt.full_name, verdict=verdict, tactics_total=n,
                               tactics_applied=n if ok else 0, final_state_pp=None,
                               error=None if ok else "synthetic sanity failure")

    @contextmanager
    def open_at_step(self, bt, k, timeout=600):
        self.open_count += 1
        yield (f"dojo-{self.open_count}-{bt.full_name}-k{k}", f"state@k={k}")

    def try_tail(self, dojo, state_at_k, tail, theorem_name):
        self.tail_tokens.append((theorem_name, dojo))
        return _graded(theorem_name, tail)

    def verify_proof_tail(self, bt, k, tail, timeout=600):
        return _graded(bt.full_name, tail)


@pytest.fixture
def sweep_ctx(monkeypatch, tmp_path):
    """Two stub servers, one per provider; dataset repointed at the fixture."""
    stubs, threads = [StubServer(), StubServer()], []
    for s in stubs:
        s.default_response = chat_completion(MARKER)
        threads.append(threading.Thread(target=s.serve_forever, daemon=True))
        threads[-1].start()
    for name, value in {"PRIME_INTELLECT_BASE_URL": stubs[0].base_url,
                        "OPENROUTER_BASE_URL": stubs[1].base_url,
                        "PRIME_INTELLECT_API_KEY": "stub-key",
                        "OPENROUTER_API_KEY": "stub-key",
                        "SMOLBENCH_LEAN_DATA": str(FIXTURE),
                        "SMOLBENCH_LEAN_RESULTS": str(tmp_path)}.items():
        monkeypatch.setenv(name, value)
    corpus.reset_caches()
    yield SimpleNamespace(pi=stubs[0], orr=stubs[1], tmp=tmp_path)
    corpus.reset_caches()
    for s in stubs:
        s.shutdown()
    for t in threads:
        t.join(timeout=5)


def _make_config(concurrent=False, **overrides):
    cfg = {
        "run_name": "mini", "k": {"strategy": "last"},
        "theorems": {"source": "explicit", "kind": "random", "split": "val",
                     "full_names": ["Mini.theoremA", "Mini.theoremB"]},
        "rungs": ["stepk:0", "stepk:1"],
        "skip_trivial": False,
        "n_replicates": 2, "temperature": 0.5, "max_tokens": 256, "seed": 1000,
        "request_timeout": 33, "max_retries": 2,
        "concurrent_gen": concurrent, "max_concurrency": 4,
        "models": [{"provider": "primeintellect", "model": M1,
                    "extra_params": {"reasoning_effort": "high"}},
                   {"provider": "openrouter", "model": M2}],
    }
    cfg.update(overrides)
    return cfg


EXPECTED_CELLS = 16  # theorems(2) x rungs(2) x models(2) x replicates(2)

REQUIRED_ROW_KEYS = set("""
kind theorem_id file_path k n_total_tactics chain level rung replicate_idx model
api_model provider seed temperature context_chars ground_truth_remaining
prompt_tokens completion_tokens cache_read_tokens cache_creation_tokens gen_ms
verify_ms candidate_proof raw_response reasoning_content verdict lean_error
final_state_pp finish_reason""".split())


def _rows(run_dir, kind=None):
    rows = [json.loads(l) for l in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    return [r for r in rows if kind is None or r.get("kind") == kind]


def _write_rows(run_dir, rows):
    (run_dir / "all_rows.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def _key(r):
    return (r["model"], r["theorem_id"], r["k"], r["rung"], r["replicate_idx"])


def _chat_posts(stub):
    """POST /chat/completions only (GET ctx-length lookups have body=None)."""
    return [req for req in stub.requests
            if req.get("body") is not None and req["path"].endswith("/chat/completions")]


def _theorem(name="Mini.theoremA"):
    return {t.full_name: t for t in corpus.load_split("random", "val")}[name]


def _run_cell(theorem, **kw):
    return list(runner.run_cell(**{
        "theorem": theorem, "provider": "primeintellect", "model": M1, "k": 2,
        "chain": "stepk", "level": 0, "n_replicates": 1, "seed": 1000,
        "request_timeout": 30, "max_retries": 2, "verifier": FakeVerifier(), **kw}))


def _sweep(ctx, cfg=None, name="run", verifier=None):
    run_dir = ctx.tmp / name
    return runner.sweep(cfg or _make_config(), run_dir,
                        verifier=verifier or FakeVerifier()), run_dir


def _force_exception(run_dir, theorem=None):
    """Make one cell's ONLY recorded verdict "exception" (appending can't); return key."""
    rows = _rows(run_dir)
    target = next(r for r in rows
                  if r.get("kind") == "cell" and theorem in (None, r["theorem_id"]))
    target["verdict"] = "exception"
    _write_rows(run_dir, rows)
    return _key(target)


@pytest.mark.parametrize("concurrent", [False, True])
def test_sweep_end_to_end(sweep_ctx, monkeypatch, concurrent):
    """Schema, seeds, dispatch, request kwargs, Dojo sharing, order, artifacts."""
    import smolbench.evals.providers.openrouter as orr
    import smolbench.evals.providers.primeintellect as pi
    calls: list[dict] = []

    def _spy(real):
        def _wrapped(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return real(*args, **kwargs)
        return _wrapped

    monkeypatch.setattr(pi, "complete", _spy(pi.complete))
    monkeypatch.setattr(orr, "complete", _spy(orr.complete))
    cfg = _make_config(concurrent)
    verifier = FakeVerifier()
    written, run_dir = _sweep(sweep_ctx, cfg, verifier=verifier)
    assert written == EXPECTED_CELLS
    cells = _rows(run_dir, "cell")
    assert len(cells) == EXPECTED_CELLS
    assert all(REQUIRED_ROW_KEYS <= set(r) for r in cells), set(cells[0])
    assert all(r["seed"] == 1000 + r["replicate_idx"] for r in cells)
    assert all(r["verdict"] == "success" for r in cells)
    assert all(r["temperature"] == 0.5 for r in cells)
    pi_posts, or_posts = _chat_posts(sweep_ctx.pi), _chat_posts(sweep_ctx.orr)
    assert len(pi_posts) == len(or_posts) == EXPECTED_CELLS // 2
    assert {p["body"]["model"] for p in pi_posts} == {M1}
    assert {p["body"]["model"] for p in or_posts} == {M2}
    for body in [p["body"] for p in pi_posts + or_posts]:
        assert body["seed"] in (1000, 1001)
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 256
        assert body["messages"][0] == {"role": "system", "content": prompt.SYSTEM}
        assert body["messages"][1]["role"] == "user"
        assert body["messages"][1]["content"].endswith(prompt.INSTRUCTION)
    assert {p["body"]["seed"] for p in pi_posts} == {1000, 1001}
    assert all(p["body"].get("reasoning_effort") == "high" for p in pi_posts)
    assert all("reasoning_effort" not in p["body"] for p in or_posts)
    all_keys = {_key(r) for r in cells}
    assert len(all_keys) == EXPECTED_CELLS
    assert all_keys == {_key(json.loads(line))
                        for jl in (run_dir / "theorems").rglob("outputs/*.jsonl")
                        for line in jl.read_text().splitlines()}
    assert {r["theorem_id"] for r in _rows(run_dir, "sanity")} == {"Mini.theoremA",
                                                                  "Mini.theoremB"}
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["counts"]["written"] == EXPECTED_CELLS
    assert (run_dir / "analysis.txt").read_text().strip()
    assert len(calls) == EXPECTED_CELLS
    for kwargs in [c["kwargs"] for c in calls]:
        assert kwargs["max_retries"] == 2
        assert kwargs["request_timeout"] == 33
        assert kwargs["context_length"] == 100000  # stub's fixed GET response
    seeds = [c["args"][2] for c in calls]  # complete(prompt, model, seed, ...)
    assert seeds.count(1000) == seeds.count(1001) == EXPECTED_CELLS // 2
    assert verifier.open_count == 2  # one per (theorem, k); k "last" -> one k each
    tokens_by_theorem = {name: {tok for n, tok in verifier.tail_tokens if n == name}
                         for name in ("Mini.theoremA", "Mini.theoremB")}
    assert all(len(t) == 1 for t in tokens_by_theorem.values()), tokens_by_theorem
    assert verifier.replay_calls == ["Mini.theoremA", "Mini.theoremB"]
    latest = run_dir.parent / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == run_dir.resolve()
    for name in ("Mini.theoremA", "Mini.theoremB"):
        tdir = run_dir / "theorems" / runner.slug_theorem(name)
        assert (tdir / "summary.md").exists()
        assert (tdir / "meta.json").exists()
    if not concurrent:
        assert [(r["theorem_id"], r["rung"], r["model"], r["replicate_idx"])
                for r in cells] == [
            (t.full_name, rung, mc.get("display_name", mc["model"]), replicate_idx)
            for t in runner._select_theorems(cfg["theorems"])
            for _k in runner._k_indices(t, cfg["k"]["strategy"])
            for rung in cfg["rungs"] for mc in cfg["models"]
            for replicate_idx in range(cfg["n_replicates"])]
    monkeypatch.delenv("SMOLBENCH_LEAN_RESULTS", raising=False)
    root = runner.results_root()
    assert root.is_absolute()
    assert root.parts[-3:] == ("notebooks", "deduction", "results")


@pytest.mark.parametrize("concurrent", [False, True])
def test_fully_resumed_sweep_opens_no_dojo_session(sweep_ctx, concurrent):
    """With every cell already recorded, neither path pays a Dojo session to skip them."""
    cfg = _make_config(concurrent)
    assert _sweep(sweep_ctx, cfg)[0] == EXPECTED_CELLS
    verifier = FakeVerifier()
    written, run_dir = _sweep(sweep_ctx, cfg, verifier=verifier)
    assert (written, verifier.open_count) == (0, 0)
    assert json.loads((run_dir / "manifest.json").read_text())["counts"]["skipped"] == \
        EXPECTED_CELLS


@pytest.mark.parametrize("concurrent", [False, True])
def test_generation_exception_rows_carry_the_full_cell_schema(sweep_ctx, monkeypatch,
                                                              concurrent):
    """A raising provider still writes a complete cell row (reasoning_content None)."""
    import smolbench.evals.providers.primeintellect as pi

    def _boom(*args, **kwargs):
        raise RuntimeError("upstream died")

    monkeypatch.setattr(pi, "complete", _boom)
    cfg = _make_config(concurrent, run_name="boom", rungs=["stepk:0"], n_replicates=1,
                       theorems={"source": "explicit", "kind": "random", "split": "val",
                                 "full_names": ["Mini.theoremA"]},
                       models=[{"provider": "primeintellect", "model": M1}])
    written, run_dir = _sweep(sweep_ctx, cfg, name="boom")
    (row,) = _rows(run_dir, "cell")
    assert written == 1 and row["verdict"] == "exception"
    assert REQUIRED_ROW_KEYS <= set(row), REQUIRED_ROW_KEYS - set(row)
    assert row["reasoning_content"] is None and row["finish_reason"] is None
    assert "RuntimeError: upstream died" in row["lean_error"]


def test_existing_keys_reruns_only_cells_that_never_reached_the_model(tmp_path):
    """`prompt_tokens > 0` is the line between lost data and real data."""
    records = {
        "lost.never_asked": [("exception", "", 0), ("unverified", "", 0)],
        "data.answered_empty_after_infra": [("exception", "", 0),
                                            ("unverified", "", 398)],
        "data.plain_empty": [("unverified", "", 398)],
        "done.has_proof": [("unverified", "exact foo", 398)],
        "rerun.only_an_exception": [("exception", "exact bar", 398)],
    }
    path = tmp_path / "all_rows.jsonl"
    path.write_text("".join(json.dumps(
        {"kind": "cell", "model": "m", "theorem_id": t, "k": 1, "rung": "stepk:1",
         "replicate_idx": 0, "verdict": v, "candidate_proof": proof, "lean_error": "",
         "prompt_tokens": tokens, "completion_tokens": 0}) + "\n"
        for t, rows in records.items() for v, proof, tokens in rows))
    skip = runner._existing_keys(path)
    assert {t for t in records
            if runner._row_key("m", t, 1, "stepk:1", 0) not in skip} == {
        "lost.never_asked", "rerun.only_an_exception"}


def test_run_cell_prompt_bytes_seeds_and_reasoning_only_cap_hit(sweep_ctx):
    """The body matches build_user_prompt(render(...)); a cap-hit is never a proof."""
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
    sweep_ctx.pi.default_response = {
        "choices": [{"message": {"content": None,
                                 "reasoning_content": f"I will now write {MARKER}"},
                     "finish_reason": "length"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 32768, "total_tokens": 40},
    }
    row = _run_cell(theorem)[0]
    assert row["verdict"] != "success"          # the marker did NOT become a proof
    assert row["candidate_proof"] == ""
    assert row["raw_response"] == ""
    assert MARKER in row["reasoning_content"]   # but the reasoning IS preserved
    assert row["finish_reason"] == "length"
    assert row["completion_tokens"] == 32768


def test_cli_help_and_nullverify_import_subprocesses():
    """`--help` works, and `nullverify` imports WITHOUT `verify` (and lean_dojo)."""
    help_run = subprocess.run([sys.executable, "-m", "smolbench.deduction.lean.cli",
                               "--help"], capture_output=True, text=True)
    assert help_run.returncode == 0, help_run.stderr
    assert "usage" in (help_run.stdout + help_run.stderr).lower()
    import_run = subprocess.run([sys.executable, "-c", (
        "import sys\n"
        "from smolbench.deduction.lean.nullverify import NullVerifier\n"
        "assert 'smolbench.deduction.lean.verify' not in sys.modules\n"
        "v = NullVerifier()\n"
        "assert v.replay_ground_truth and v.open_at_step and v.try_tail\n"
    )], capture_output=True, text=True)
    assert import_run.returncode == 0, import_run.stderr


def test_sweep_skips_trivial_rungs(sweep_ctx):
    theorems = {t.full_name: t for t in corpus.load_split("random", "val")}
    rungs = ["stepk:0", "stepk:1"]
    trivial_pairs = {
        (name, rung) for name, t in theorems.items() for rung in rungs
        if context.is_trivial_rung(t, runner._k_indices(t, "first")[0],
                                   rung.split(":")[0], int(rung.split(":")[1]))}
    assert trivial_pairs, (
        "fixture no longer produces any trivial rung under k=first -- "
        "update this test's config/fixture expectations")
    cfg = _make_config(run_name="trivial", k={"strategy": "first"}, skip_trivial=True,
                       models=[{"provider": "primeintellect", "model": M1},
                               {"provider": "openrouter", "model": M2}])
    cells = _rows(_sweep(sweep_ctx, cfg)[1], "cell")
    all_pairs = {(name, rung) for name in theorems for rung in rungs}
    assert {(r["theorem_id"], r["rung"]) for r in cells} == all_pairs - trivial_pairs
    assert len(cells) == ((len(all_pairs) - len(trivial_pairs))
                          * len(cfg["models"]) * cfg["n_replicates"])


@pytest.mark.parametrize("verdict", ["lean_error", "incomplete", "given_up",
                                     "exception", "replay_failed", "skipped"])
def test_sanity_gate_excludes_on_failure_and_is_sticky_on_resume(sweep_ctx, verdict):
    """Failure verdicts gate a theorem out; "skipped" AND "exception" pass through.

    13-03 moved ``"exception"`` out of `SANITY_FAILURE_VERDICTS`, so this test
    now pins it in the pass-through group beside ``"skipped"``: a Python
    exception during the ground-truth replay (an unset SMOLBENCH_MATHLIB_ROOT,
    a REPL start race) is a statement about the INFRASTRUCTURE, not a positive
    finding that the recorded ground truth is unreplayable, and gating on it
    dropped the theorem from every later resume with no escape short of
    ``--force-rerun`` on the whole lane. It previously sat in the excluded
    group.

    The recorded gate stays authoritative on resume for the four verdicts that
    remain, and -- for the two pass-through verdicts -- the resume path still
    performs NO second replay: the ``len(_rows(run_dir, "sanity")) == 2``
    assertions below are what pins that, and they matter because a duplicate
    sanity row would break `merge_lean_shards.py`'s ``--expect-sanity`` count.
    """
    cfg = _make_config(concurrent=False)
    excluded = verdict not in ("skipped", "exception")
    expected = EXPECTED_CELLS // 2 if excluded else EXPECTED_CELLS
    first = FakeVerifier(sanity={"Mini.theoremA": verdict})
    written, run_dir = _sweep(sweep_ctx, cfg, verifier=first)
    assert written == expected
    assert first.replay_calls == ["Mini.theoremA", "Mini.theoremB"]
    assert {r["theorem_id"]: r["verdict"] for r in _rows(run_dir, "sanity")} == {
        "Mini.theoremA": verdict, "Mini.theoremB": "success"}
    cells = _rows(run_dir, "cell")
    assert len(cells) == expected
    assert any(r["theorem_id"] == "Mini.theoremA" for r in cells) == (not excluded)
    second = FakeVerifier()  # this one WOULD now report success for A
    assert _sweep(sweep_ctx, cfg, verifier=second)[0] == 0
    assert second.replay_calls == []
    assert len(_rows(run_dir, "sanity")) == 2
    after = _rows(run_dir, "cell")
    assert len(after) == expected
    assert any(r["theorem_id"] == "Mini.theoremA" for r in after) == (not excluded)
    if excluded:
        return
    _write_rows(run_dir, [r for r in _rows(run_dir) if not (
        r["kind"] == "cell" and r["theorem_id"] == "Mini.theoremA")])
    assert _sweep(sweep_ctx, cfg)[0] == EXPECTED_CELLS // 2
    assert len(_rows(run_dir, "sanity")) == 2
    target = _force_exception(run_dir, theorem="Mini.theoremA")
    assert _sweep(sweep_ctx, cfg)[0] == 1
    assert [r for r in _rows(run_dir, "cell")
            if _key(r) == target and r["verdict"] != "exception"]


def test_select_theorems_shards_partition_the_unsharded_selection(sweep_ctx):
    """Seeded selection is deterministic; `shard: "i/n"` slices it after sampling."""
    base = {"source": "with_proof", "kind": "random", "split": "val",
            "limit": 0, "seed": 0}
    whole = [t.full_name for t in runner._select_theorems(base)]
    assert whole == [t.full_name for t in runner._select_theorems(base)]
    assert len(whole) >= 2
    seen: list[str] = []
    for i in range(3):
        names = [t.full_name
                 for t in runner._select_theorems({**base, "shard": f"{i}/3"})]
        assert names == whole[i::3]
        seen.extend(names)
    assert sorted(seen) == sorted(whole)
    assert len(seen) == len(set(seen))  # pairwise disjoint
    for bad in ("3/3", "-1/3", "0", "0of3", "a/b", "1/0"):
        with pytest.raises(ValueError):
            runner._select_theorems({**base, "shard": bad})


def test_load_cell_whitelist_parses_dedupes_hashes_and_rejects_bad_input(tmp_path):
    path = tmp_path / "wl.json"
    path.write_text(json.dumps([["m", "T", 1, "stepk:1", 0],
                                ["m", "T", 1, "stepk:1", 0],
                                ["m", "U", 2, "hint:2", 1]]))
    keys = [("m", "T", 1, "stepk:1", 0), ("m", "U", 2, "hint:2", 1)]
    assert runner.load_cell_whitelist(str(path)) == frozenset(keys)
    assert runner.hash_cell_keys(keys) == runner.hash_cell_keys(
        [["m", "U", 2, "hint:2", 1], ["m", "T", 1, "stepk:1", 0]])
    assert (runner.hash_cell_keys([("m", "T", 1, "stepk:1", 0)])
            != runner.hash_cell_keys([("m", "T", 1, "stepk:1", 1)]))
    for bad in ("{not valid json", json.dumps({"not": "a list"}),
                json.dumps([["too", "few", "elements"]])):
        path.write_text(bad)
        with pytest.raises(ValueError):
            runner.load_cell_whitelist(str(path))


@pytest.mark.parametrize("concurrent", [False, True])
def test_cell_whitelist_restricts_sweep_to_exactly_the_listed_cells(
        sweep_ctx, monkeypatch, concurrent):
    cfg = _make_config(concurrent)
    all_keys = sorted(_key(r)
                      for r in _rows(_sweep(sweep_ctx, cfg, name="baseline")[1], "cell"))
    assert len(all_keys) == EXPECTED_CELLS
    whitelist_keys = [k for k in all_keys if k[1] == "Mini.theoremA"][:3]
    assert len(whitelist_keys) == 3
    whitelist_path = sweep_ctx.tmp / "whitelist.json"
    whitelist_path.write_text(json.dumps([list(k) for k in whitelist_keys]))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(whitelist_path))
    written, run_dir = _sweep(sweep_ctx, cfg)
    assert written == len(whitelist_keys)
    assert sorted(_key(r) for r in _rows(run_dir, "cell")) == sorted(whitelist_keys)
    assert {r["theorem_id"] for r in _rows(run_dir, "sanity")} == {"Mini.theoremA"}


def test_cell_whitelist_bad_file_raises_and_writes_nothing(sweep_ctx, monkeypatch):
    """A bad LEAN_CELL_WHITELIST aborts at sweep start, never a full unfiltered run."""
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(sweep_ctx.tmp / "missing.json"))
    with pytest.raises(ValueError):
        _sweep(sweep_ctx)
    assert not (sweep_ctx.tmp / "run" / "all_rows.jsonl").exists()


@pytest.mark.parametrize("concurrent", [False, True])
def test_display_name_aliasing_and_per_model_semaphore(sweep_ctx, concurrent):
    cfg = _make_config(
        concurrent=concurrent, run_name="alias", rungs=["stepk:0"], n_replicates=1,
        theorems={"source": "explicit", "kind": "random", "split": "val",
                  "full_names": ["Mini.theoremA"]},
        models=[{"provider": "primeintellect", "model": M1, "display_name": "alias-one"},
                {"provider": "primeintellect", "model": M1, "display_name": "alias-two",
                 "max_concurrency": 1}])
    written, run_dir = _sweep(sweep_ctx, cfg)
    assert written == 2  # 1 theorem x 1 rung x 2 aliases x 1 replicate
    by_alias = {r["model"]: r for r in _rows(run_dir, "cell")}
    assert set(by_alias) == {"alias-one", "alias-two"}
    assert all(r["api_model"] == M1 for r in by_alias.values())
    assert _sweep(sweep_ctx, cfg)[0] == 0
    assert len(_rows(run_dir, "cell")) == 2


def test_ctx_len_for_falls_back_to_huge_value_on_lookup_failure():
    """A catalog lookup failure widens the token guard instead of aborting the sweep."""
    class _BrokenModule:
        def get_model_context_length(self, model):
            raise RuntimeError("catalog unreachable")

    assert runner._ctx_len_for({"model": "some-model", "provider": "primeintellect"},
                               _BrokenModule()) == 10**9


def test_l3_column_counts_parse_level_relics_and_names_its_scope(tmp_path, monkeypatch):
    """The `l3` column counts parse-level-relic cells and SAYS it is parse-level.

    Name-level (mathlib3 renamed-lemma) detection was removed from `lean3`
    together with the declaration-name-map asset that was never built in this
    tree, so the column now means the same thing on every machine and the old
    graceful-degradation marker line is gone. Three things are pinned here:

    * a comma-free mathlib3 lemma name (``apply supr_le``) is NOT counted --
      the negative control for that removal. It used to be counted, but only on
      a machine that happened to carry the asset;
    * no ``parse-level only`` marker line survives, since the header now carries
      that fact;
    * the header cell is the single whitespace-delimited token
      ``l3(parse-level)``. It carries no internal space on purpose: this test
      locates the column by ``header.index(...)`` after ``line.split()`` and
      asserts every data row yields as many tokens as the header, so a header
      cell containing a space would silently break that width invariant.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "data"))
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    # Distinct theorem_id per row: `write_run_analysis` now deduplicates on the
    # full `runner._row_key` (13-04), so rows sharing an identity collapse to
    # one cell. Production rows always carry these fields; this fixture did not,
    # and three identity-less rows would fold into a single 1/1 cell.
    proofs = [("lean_error", "existsi z"),      # parse-level relic
              ("lean_error", "intros f,"),      # parse-level relic
              ("lean_error", "apply supr_le"),  # mathlib3 NAME only -> not a relic
              ("success", "rfl")]               # clean Lean 4
    _write_rows(run_dir, [{"kind": "cell", "rung": "stepk:0", "model": "m",
                           "theorem_id": f"T{i}", "k": 1, "replicate_idx": 0,
                           "verdict": v, "candidate_proof": p}
                          for i, (v, p) in enumerate(proofs)])
    runner.write_run_analysis(run_dir)
    text = (run_dir / "analysis.txt").read_text()
    assert "parse-level only" not in text, "the degradation marker line must be gone"
    lines = text.splitlines()
    sep = next(i for i, line in enumerate(lines) if line.startswith("---"))
    header = next(line for line in lines
                  if "l3(parse-level)" in line and "exc" in line).split()
    row = lines[sep + 1].split()
    assert len(row) == len(header), f"header/row width mismatch\n{header}\n{row}"
    assert row[0] == "stepk:0" and row[1] == "m"
    assert row[2] == "1/4"
    assert row[header.index("l3(parse-level)")] == "2"
    assert "l3(parse-level)=2" in lines[-1]  # per-model totals line


def test_nullverify_sweep_generates_all_theorems(sweep_ctx):
    from smolbench.deduction.lean.nullverify import NullVerifier

    cfg = _make_config()
    written, run_dir = _sweep(sweep_ctx, cfg, verifier=NullVerifier())
    assert written == EXPECTED_CELLS
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


# ---------------------------------------------------------------------------
# theorems.require_postcutoff (A2): the corpus gate inside `_select_theorems`
# ---------------------------------------------------------------------------

#: Selects the fixture's whole 2-theorem pool, in file order, with no sampling.
PC_BASE = {"source": "with_proof", "kind": "random", "split": "val", "limit": 0, "seed": 0}


def _repoint(monkeypatch, root):
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(root))
    corpus.reset_caches()


def _demote_one_row(tmp_path, name="Mini.theoremB"):
    """Copy the post-cutoff fixture, flipping one row back to ``postcutoff: false``."""
    root = tmp_path / "mixed_corpus"
    shutil.copytree(POSTCUTOFF, root)
    path = root / "random" / "val.json"
    rows = json.loads(path.read_text())
    hit = [r for r in rows if r["full_name"] == name]
    assert hit, f"{name} not in the fixture"
    hit[0]["postcutoff"] = False
    path.write_text(json.dumps(rows, indent=1))
    return root


def test_require_postcutoff_accepts_a_postcutoff_corpus(monkeypatch, tmp_path):
    _repoint(monkeypatch, POSTCUTOFF)
    names = [t.full_name
             for t in runner._select_theorems({**PC_BASE, "require_postcutoff": True})]
    assert names == ["Mini.theoremA", "Mini.theoremB"]
    corpus.reset_caches()


def test_require_postcutoff_rejects_the_old_corpus_naming_it(monkeypatch):
    """The 2024-03-24 benchmark has no post-cutoff tail; the refusal names the corpus."""
    _repoint(monkeypatch, FIXTURE)
    with pytest.raises(ValueError, match=re.escape(str(FIXTURE))):
        runner._select_theorems({**PC_BASE, "require_postcutoff": True})
    corpus.reset_caches()


def test_require_postcutoff_is_opt_in(monkeypatch):
    """Absent or False, the gate never fires -- the old corpus still selects."""
    _repoint(monkeypatch, FIXTURE)
    assert len(runner._select_theorems(PC_BASE)) == 2
    assert len(runner._select_theorems({**PC_BASE, "require_postcutoff": False})) == 2
    corpus.reset_caches()


def test_require_postcutoff_rejects_a_pre_cutoff_row(monkeypatch, tmp_path):
    """Corpus-level metadata is not enough: every selected row must carry the flag."""
    _repoint(monkeypatch, _demote_one_row(tmp_path))
    assert corpus.is_postcutoff_corpus() is True
    with pytest.raises(ValueError, match="Mini.theoremB"):
        runner._select_theorems({**PC_BASE, "require_postcutoff": True})
    corpus.reset_caches()


def test_require_postcutoff_checks_the_pool_before_sampling(monkeypatch, tmp_path):
    """`shard: "0/2"` drops the offending row, so only a PRE-sample check catches it."""
    _repoint(monkeypatch, _demote_one_row(tmp_path))
    sharded = {**PC_BASE, "shard": "0/2"}
    assert [t.full_name for t in runner._select_theorems(sharded)] == ["Mini.theoremA"]
    with pytest.raises(ValueError, match="Mini.theoremB"):
        runner._select_theorems({**sharded, "require_postcutoff": True})
    corpus.reset_caches()


# ---------------------------------------------------------------------------
# 13-01 / 13-03: the verdict vocabulary itself
# ---------------------------------------------------------------------------


def test_sanity_failure_verdicts_is_exactly_the_positively_broken_set():
    """Pin `SANITY_FAILURE_VERDICTS` membership by value, in both directions.

    Two fixes edit this frozenset in opposite directions and must not undo one
    another: 13-03 REMOVES ``"exception"`` (infrastructure, not a broken ground
    truth), and 13-01 adds the ``"no_answer"`` verdict, which must NOT be added
    here -- `replay_ground_truth` has no candidate tail, so `no_answer` is
    unreachable as a sanity verdict and its presence would be meaningless.
    An equality assertion, not two membership checks, so any future addition
    has to come here and argue for itself.
    """
    assert runner.SANITY_FAILURE_VERDICTS == frozenset(
        {"lean_error", "incomplete", "given_up", "replay_failed"}
    )
    assert "exception" not in runner.SANITY_FAILURE_VERDICTS
    assert "no_answer" not in runner.SANITY_FAILURE_VERDICTS
    assert "skipped" not in runner.SANITY_FAILURE_VERDICTS


def test_no_answer_has_its_own_glyph():
    """13-01: `no_answer` is renderable and does not collide with another verdict.

    `_glyph` falls back to ``"?"`` for an unknown verdict -- which is
    `given_up`'s glyph -- so an unregistered verdict would render as a
    DIFFERENT real verdict rather than as something obviously wrong.
    """
    assert "no_answer" in runner._VERDICT_GLYPH
    assert runner._glyph("no_answer") != runner._glyph("__not_a_verdict__")
    glyphs = list(runner._VERDICT_GLYPH.values())
    assert len(glyphs) == len(set(glyphs)), f"duplicate glyph: {glyphs}"


def test_write_run_analysis_counts_no_answer_in_its_own_column(tmp_path, monkeypatch):
    """13-01: `noans` is a real column, counted separately from `lerr`.

    Before the fix an empty candidate landed in `lean_error`, so a lane of
    truncated reasoning traces read as a lane of wrong Lean proofs. Asserts
    the split by value on a mixed run: one of each, in different columns.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "data"))
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    # Distinct theorem_id per row -- see `test_l3_counts_relics`: the analysis
    # deduplicates on the full row key (13-04).
    _write_rows(run_dir, [
        {"kind": "cell", "rung": "stepk:0", "model": "m", "theorem_id": f"T{i}",
         "k": 1, "replicate_idx": 0, "verdict": v, "candidate_proof": p}
        for i, (v, p) in enumerate(
            [("no_answer", ""), ("lean_error", "bogus"), ("success", "rfl")])
    ])
    runner.write_run_analysis(run_dir)
    lines = (run_dir / "analysis.txt").read_text().splitlines()
    header = next(line for line in lines if "noans" in line and "exc" in line).split()
    sep = next(i for i, line in enumerate(lines) if line.startswith("---"))
    row = (lines[sep + 2] if lines[sep + 1].startswith("#") else lines[sep + 1]).split()
    assert len(row) == len(header), f"header/row width mismatch\n{header}\n{row}"
    assert row[header.index("noans")] == "1"
    assert row[header.index("lerr")] == "1"
    assert row[2] == "1/3"


def test_write_run_analysis_collapses_an_exception_then_retry_duplicate(
        tmp_path, monkeypatch):
    """13-04: analysis.txt counts CELLS, not rows, for a resumed lane.

    `_existing_keys` re-runs an exception-only cell and the sweep appends the
    retry, so one key legitimately owns two rows. Counting rows made the
    retried cell read as 1/2 = 50%. Earliest SURVIVING attempt wins, matching
    `power_analysis.grade_verdicts`; the superseded exception row stays in
    all_rows.jsonl and is simply not counted twice.

    The second cell pins the other direction: with no surviving row the first
    row stands in, so a never-measured cell is counted once under `exc` rather
    than disappearing from the denominator.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(tmp_path / "data"))
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    base = {"kind": "cell", "rung": "stepk:0", "model": "m", "k": 1,
            "candidate_proof": "rfl"}
    _write_rows(run_dir, [
        {**base, "theorem_id": "T1", "replicate_idx": 0, "verdict": "exception"},
        {**base, "theorem_id": "T1", "replicate_idx": 0, "verdict": "success"},
        {**base, "theorem_id": "T2", "replicate_idx": 0, "verdict": "exception"},
        {**base, "theorem_id": "T2", "replicate_idx": 0, "verdict": "exception"},
    ])
    runner.write_run_analysis(run_dir)
    lines = (run_dir / "analysis.txt").read_text().splitlines()
    assert lines[0].startswith("# 2 cells;"), lines[0]
    header = next(line for line in lines if "noans" in line and "exc" in line).split()
    sep = next(i for i, line in enumerate(lines) if line.startswith("---"))
    row = (lines[sep + 2] if lines[sep + 1].startswith("#") else lines[sep + 1]).split()
    assert row[2] == "1/2", row
    assert row[header.index("exc")] == "1", row


def test_dedupe_cell_rows_keys_on_the_full_row_key():
    """13-04: replicates are a real axis; only the SAME key collapses.

    `replicate_idx` is part of `runner._row_key`, so genuine replicates survive
    deduplication. A helper keyed on (model, theorem, k, rung) alone would
    silently collapse the replication axis the sweep is built around.
    """
    def row(rep, verdict):
        return {"kind": "cell", "model": "m", "theorem_id": "T", "k": 1,
                "rung": "stepk:0", "replicate_idx": rep, "verdict": verdict}

    kept = runner.dedupe_cell_rows([row(0, "exception"), row(0, "success"),
                                    row(1, "lean_error")])
    assert [(r["replicate_idx"], r["verdict"]) for r in kept] == [
        (0, "success"), (1, "lean_error")]
    # Order of the surviving rows follows the input, not the key ordering.
    kept = runner.dedupe_cell_rows([row(1, "success"), row(0, "success")])
    assert [r["replicate_idx"] for r in kept] == [1, 0]


# ---------------------------------------------------------------------------
# 13-12 / 13-09 / 13-17 / 13-18: sweep reconciliation, provenance, constants
# ---------------------------------------------------------------------------


def _manifest(run_dir):
    return json.loads((run_dir / "manifest.json").read_text())


def test_unreachable_whitelist_keys_are_reported_and_fatal(sweep_ctx, monkeypatch):
    """13-12: a requested cell the sweep cannot reach must not exit 0.

    Membership was only ever tested in the direction "is this GENERATED cell
    wanted", so a requested key naming a theorem/rung the sweep never produces
    was skipped, counted in the same `n_skipped` as resumed cells, and the
    sweep returned normally -- while `run_study` stamped the whitelist's
    sha256 into manifest.json as a claim that this exact set of cells was
    collected. Exit 0 made that claim false.

    The ORDERING assertions are the load-bearing half: manifest.json must
    record `whitelist_missed` and analysis.txt must exist BEFORE the raise, or
    the only record of what went wrong dies with the exception.
    """
    cfg = _make_config()
    reachable = sorted(_key(r)
                       for r in _rows(_sweep(sweep_ctx, cfg, name="baseline")[1], "cell"))
    wanted = [list(reachable[0]), ["m", "Mini.ghostTheorem", 0, "stepk:0", 0]]
    path = sweep_ctx.tmp / "whitelist.json"
    path.write_text(json.dumps(wanted))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(path))

    run_dir = sweep_ctx.tmp / "missed"
    with pytest.raises(RuntimeError, match="(?i)whitelist"):
        runner.sweep(cfg, run_dir, verifier=FakeVerifier())

    manifest = _manifest(run_dir)
    assert manifest["whitelist_missed"] == [["m", "Mini.ghostTheorem", 0, "stepk:0", 0]]
    assert (run_dir / "analysis.txt").exists(), (
        "the analysis must be written before the raise, not lost with it"
    )


def test_a_fully_reachable_whitelist_records_an_empty_missed_list(sweep_ctx, monkeypatch):
    """13-12: "reconciled, nothing missed" and "this run predates the check" differ.

    An absent key and an empty list must not be confusable, so the key is
    written whenever a whitelist is active -- otherwise a reader of an
    archived manifest cannot tell a clean reconciliation from no
    reconciliation at all.
    """
    cfg = _make_config()
    reachable = sorted(_key(r)
                       for r in _rows(_sweep(sweep_ctx, cfg, name="baseline")[1], "cell"))
    path = sweep_ctx.tmp / "whitelist.json"
    path.write_text(json.dumps([list(k) for k in reachable[:2]]))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(path))
    run_dir = sweep_ctx.tmp / "clean"
    assert runner.sweep(cfg, run_dir, verifier=FakeVerifier()) == 2
    assert _manifest(run_dir)["whitelist_missed"] == []


def test_no_whitelist_leaves_the_manifest_key_absent(sweep_ctx):
    """13-12: the reconciliation record only exists when a whitelist was in effect."""
    _, run_dir = _sweep(sweep_ctx, name="nowl")
    assert "whitelist_missed" not in _manifest(run_dir)


def test_manifest_records_whether_the_traced_repo_was_present(sweep_ctx):
    """13-09: which cells a run produces depends on a directory outside results/.

    `premises.body_with_proof` falls back to the corpus's stored signature when
    `premises._traced_root()` is None, and under `skip_trivial` that can make
    `is_trivial_rung` judge hint:2/hint:3/noise:3 trivial -- so the SET OF
    CELLS a lane produces differs between a box with the traced mathlib4
    checkout and one without. `traced_root_present` is provenance about the
    BOX, recorded unconditionally so an archived run can be read years later
    without re-deriving which regime it came from.
    """
    _, run_dir = _sweep(sweep_ctx, name="prov")
    assert isinstance(_manifest(run_dir)["traced_root_present"], bool)


def test_dojo_timeout_has_one_default_across_all_three_entry_points():
    """13-17: `dojo_timeout` had three defaults (600 / 600 / 300) and no owner.

    Unified on 600, deliberately NOT on 300: `notebooks/deduction/run_study.py`
    passes 300 explicitly, so the production sweep is unaffected either way,
    while unifying downward would TIGHTEN `run_cell` and `cli --timeout` -- and
    a REPL request that times out is recorded as an `"exception"` verdict, so
    tightening silently converts slow theorems into infrastructure failures.

    Checked through the actual signature/parser defaults, not by grepping for
    the number, so a stray literal that bypasses the constant fails here.
    """
    import inspect

    assert runner.DEFAULT_DOJO_TIMEOUT == 600
    assert (inspect.signature(runner.run_cell).parameters["dojo_timeout"].default
            == runner.DEFAULT_DOJO_TIMEOUT)

    from smolbench.deduction.lean import cli

    # `--timeout` is defined on the SUBparsers, not the top-level parser, so
    # scanning `parser._actions` finds nothing and would make this check pass
    # vacuously (it only failed loudly here because `.get` returned None).
    # Walk into the subcommand instead.
    parser = cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "cmd")
    for name in ("run-cell", "replay"):
        timeout = next(a for a in sub.choices[name]._actions if a.dest == "timeout")
        assert timeout.default == runner.DEFAULT_DOJO_TIMEOUT, (name, timeout.default)
    # `filter`'s --timeout is deliberately NOT this constant: it is documented
    # separately at its own call site. Pinned so a future "tidy-up" that folds
    # it in has to change this line and argue for it.
    filt = next(a for a in sub.choices["filter"]._actions if a.dest == "timeout")
    assert filt.default != runner.DEFAULT_DOJO_TIMEOUT


def test_sweep_seed_default_is_zero(sweep_ctx):
    """13-18: an omitted `seed` must not silently disagree with the driver.

    `theorems.seed` (which theorems are measured) defaulted to 0 while
    `cfg.seed` (the decode seed on the wire) defaulted to 1776, so a sweep
    config omitting `seed` decoded at a seed no driver ever chose.
    `run_cell`'s own 1776 default is a different entry point and is
    deliberately unchanged.
    """
    cfg = _make_config(run_name="seedless", rungs=["stepk:0"], n_replicates=1,
                       theorems={"source": "explicit", "kind": "random",
                                 "split": "val", "full_names": ["Mini.theoremA"]})
    del cfg["seed"]
    _, run_dir = _sweep(sweep_ctx, cfg, name="seedless")
    assert {r["seed"] for r in _rows(run_dir, "cell")} == {0}


def test_resume_truncates_a_torn_final_line_before_appending(sweep_ctx):
    """13-07: a torn FINAL line must not become a corrupt MIDDLE line.

    `all_rows.jsonl` is opened in APPEND mode on resume, and `_existing_keys`
    merely SKIPS an unparseable line -- so a row half-written when a box was
    SIGKILLed stayed in the file and the resumed writer appended onto its torn
    prefix, welding two records into one line:

        {"kind": "cel{"kind": "cell", "n": 3}

    A torn FINAL line is recoverable (both merge_lean_shards.py and
    split_lean_run_into_shards.py drop it with a warning, and the driver's own
    docstring promises it "regenerates on resume"); a corrupt MIDDLE line is
    not -- both scripts hard-abort on one. So the damage is done by the
    APPEND, and the fix is to truncate before appending.
    """
    cfg = _make_config(run_name="torn", rungs=["stepk:0"], n_replicates=1,
                       theorems={"source": "explicit", "kind": "random",
                                 "split": "val", "full_names": ["Mini.theoremA"]})
    written, run_dir = _sweep(sweep_ctx, cfg, name="torn")
    assert written > 0
    path = run_dir / "all_rows.jsonl"
    good = _rows(run_dir)

    # SIGKILL mid-write: a partial record with no trailing newline.
    with path.open("a") as f:
        f.write('{"kind": "cell", "theorem_id": "Mini.theo')

    # Resume. The truncated cell must be regenerated, not appended onto.
    _write_rows(run_dir, good[:-1])
    with path.open("a") as f:
        f.write('{"kind": "cell", "theorem_id": "Mini.theo')
    runner.sweep(cfg, run_dir, verifier=FakeVerifier())

    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        json.loads(line)  # every line must parse -- a torn weld raises here
    assert lines, "the file must not have been emptied"
    assert not any('{"kind": "cel' in line and line.count('"kind"') > 1
                   for line in lines), "two records welded into one line"
