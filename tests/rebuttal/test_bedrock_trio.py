"""Offline tests for ``rebuttal/bedrock_trio.py`` against the shared OpenAI stub."""

import json
import os
import re
import time
from dataclasses import replace
from datetime import datetime, timezone
from types import MappingProxyType, SimpleNamespace

import pytest
import yaml
from botocore.exceptions import ClientError

from smolbench.deduction.horn import repro as horn_repro
from smolbench.deduction.horn import stats
from smolbench.deduction.horn.checker import designed_proof
from smolbench.deduction.horn.render import ALL_ARMS
from smolbench.deduction.horn.theory import Theory
from smolbench.evals import _aws
from smolbench.evals.results_store import ReplicateAddress, S3ResultsStore
from smolbench.induction import repro as induction_repro
from tests._paths import REPO_ROOT, load_by_path
from conftest import StubTokenizer, chat_completion

bt = load_by_path(REPO_ROOT / "rebuttal" / "bedrock_trio.py", "bedrock_trio_under_test")
# The in-memory S3 client the results-store tests use; loaded by path (tests/ has no packages).
FakeS3Client = load_by_path(
    REPO_ROOT / "tests" / "evals" / "test_results_store.py", "results_store_tests_for_bedrock_trio"
).FakeS3Client

GEMMA = bt.TRIO["gemma-4-31b"]
NEMO = bt.TRIO["nemotron-3-super-120b-a12b"]
DSV31 = replace(bt.TRIO["deepseek-v3.1"], bedrock_id="deepseek.v3-v1:0")
ROUTED_ENV = (
    "INFERENCE_PROVIDER",
    "AWS_INFERENCE_BASE_URL",
    "AWS_INFERENCE_BODY_MODEL",
    "AWS_BEDROCK_STREAM_COMPLETIONS",
    "HORN_STREAM_COMPLETIONS",
)


def _final(content, reasoning=None, finish_reason="stop"):
    body = chat_completion(content, reasoning_content=reasoning)
    body["choices"][0]["finish_reason"] = finish_reason
    return body


@pytest.fixture
def mantle(stub_server, monkeypatch):
    """Point every mantle URL at the stub, keeping the per-model path."""
    host = stub_server.base_url.removesuffix("/v1")
    monkeypatch.setattr(bt, "MANTLE_URL", host + "{path}")
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "tok")
    for k in ROUTED_ENV:
        monkeypatch.delenv(k, raising=False)
    return stub_server


@pytest.mark.parametrize(
    "model, path", [(GEMMA, "/openai/v1/chat/completions"), (NEMO, "/v1/chat/completions")]
)
def test_probe_routes_per_model_and_sends_seed_and_reasoning(mantle, model, path):
    mantle.queue_response(_final("391", reasoning="17*23 = 391"))
    result = bt.probe(model, "us-east-1", {"reasoning_effort": "high"}, seed=5)
    assert result["ok"] and result["reasoned"], result
    req = mantle.requests[-1]
    assert req["path"] == path
    assert req["headers"]["Authorization"] == "Bearer tok"
    body = req["body"]
    assert body["model"] == model.bedrock_id
    assert body["seed"] == 5
    assert body["reasoning_effort"] == "high"
    assert body["max_completion_tokens"] == bt.PROBE_MAX_TOKENS
    assert body["stream"] is True
    assert not any(k in os.environ for k in ROUTED_ENV), "use_model must restore the env"


def test_reasoned_accepts_think_split_and_rejects_bare_answer(mantle):
    mantle.queue_response(_final("<think>17*20+17*3</think>391"))
    assert bt.probe(NEMO, "us-east-1", {})["reasoned"]
    mantle.queue_response(_final("391"))
    assert not bt.probe(NEMO, "us-east-1", {})["reasoned"]
    assert not bt.reasoned("  ") and bt.reasoned("x")


def test_pick_reasoning_args_falls_through_then_refuses(mantle):
    mantle.queue_response(_final("391"))
    mantle.queue_response(_final("391", reasoning="thought"))
    args, tried = bt.pick_reasoning_args(GEMMA, "us-east-1")
    assert args == GEMMA.reasoning_candidates[1] and len(tried) == 2
    assert mantle.requests[-1]["body"]["chat_template_kwargs"] == {"enable_thinking": True}
    mantle.queue_response(_final("391"))
    with pytest.raises(RuntimeError, match="no reasoning candidate"):
        bt.pick_reasoning_args(NEMO, "us-east-1")


def test_resolve_ids_fills_deepseek_v31_and_checks_known_ids():
    listing = ["google.gemma-4-31b", "nvidia.nemotron-super-3-120b", "deepseek.v3.2", "deepseek.v3-v1:0"]
    out = bt.resolve_ids(listing)
    assert out["deepseek-v3.1"].bedrock_id == "deepseek.v3-v1:0"
    # A known id missing from the listing is left for the probe to check.
    assert bt.resolve_ids(listing[1:])["gemma-4-31b"].bedrock_id == "google.gemma-4-31b"
    with pytest.raises(LookupError, match="deepseek"):
        bt.resolve_ids(listing[:3])


def test_induction_writes_released_layout_and_resumes(mantle, tmp_path, monkeypatch):
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    harness = bt.induction_harness([DSV31], seeds=[0], results_dir=tmp_path)
    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"}, max_parallel=4)
    assert len(mantle.requests) == 27
    assert {r["body"]["model"] for r in mantle.requests} == {"deepseek.v3-v1:0"}
    assert all("temperature" not in r["body"] for r in mantle.requests)

    cells = induction_repro.load_cells(tmp_path / "induction")
    assert set(cells) == {("deepseek-v3.1", arm) for arm in bt.INDUCTION_ARMS}
    run = next((tmp_path / "induction" / "induction" / "deepseek-v3.1" / "seed=0").glob("extens--*.yaml"))
    data = yaml.safe_load(run.read_text())
    # The ICLR budget: the context limit less the longest prompt and the template reserve.
    budget = bt.induction_budget("deepseek-v3.1")
    assert rs.MIN_VIABLE_BUDGET <= budget < rs.CONTEXT_LIMIT - rs.TEMPLATE_RESERVE
    assert data["server_config"]["extra_args"] == {"max_completion_tokens": budget, "reasoning_effort": "high"}
    report = bt.induction_reasoning_report(tmp_path)
    assert all(v["unreasoned"] == 0 and v["marks"] == 9 for v in report.values())

    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"})
    assert len(mantle.requests) == 27, "a finished replicate must not be re-billed"


def test_horn_rows_score_and_load_through_stats(mantle, tmp_path):
    rung = bt.render_horn_rung(2, [100], rungs_dir=tmp_path / "rungs")
    theory = Theory.from_json((rung / "s0100" / "theory.json").read_text())
    mantle.default_response = _final("\n".join(designed_proof(theory)), reasoning="plan: a ∧ b → c")
    out = tmp_path / "rows.jsonl"
    rows = bt.run_horn(NEMO, "us-east-1", {"reasoning_effort": "high"}, rung, [100], reps=1, out=out)
    assert sorted(r["arm"] for r in rows) == sorted(bt.HORN_ARMS)
    assert {r["verdict"] for r in rows} == {"success"}
    body = mantle.requests[-1]["body"]
    assert body["temperature"] == 0.7 and body["seed"] == 0 and body["reasoning_effort"] == "high"
    assert body["stream"] is True and all(r["reasoning"] == "plan: a ∧ b → c" for r in rows)
    assert mantle.requests[-1]["path"] == "/v1/chat/completions"
    # The ICLR budget: the protocol's cap, cut so that prompt and output fit its context.
    sent = {r["max_tokens_sent"] for r in rows}
    assert body["max_tokens"] in sent and all(100_000 < s < bt.HORN_MAX_TOKENS for s in sent)
    assert (bt.HORN_MAX_TOKENS, bt.HORN_CONTEXT_LENGTH) == (131072, 131072)
    sampling = json.loads((REPO_ROOT / "smolbench/deduction/horn/iclr.json").read_text())["sampling"]
    assert (sampling["max_tokens"], sampling["context_length"]) == (bt.HORN_MAX_TOKENS, bt.HORN_CONTEXT_LENGTH)
    capped = bt.run_horn(NEMO, "us-east-1", {}, rung, [100], reps=1, out=tmp_path / "capped.jsonl",
                         arms=("lem",), max_tokens=4096)
    assert [r["max_tokens_sent"] for r in capped] == [4096]

    cells, dropped = stats.load_rows([out])
    assert not dropped and set(cells) == {("nemotron-3-super-120b-a12b", "m2")}
    assert bt.horn_breakdown([out])[("nemotron-3-super-120b-a12b", "lem")]["unreasoned"] == 0
    assert all(json.loads(l)["provider"] == "bedrock-mantle:us-east-1" for l in out.read_text().splitlines())

    assert bt.run_horn(NEMO, "us-east-1", {}, rung, [100], reps=1, out=out) == []


# ------------------------------------------------------------------------ S3 store

URI = bt.RESULTS_S3
PREFIX = "bedrock-trio"
NEMO_HORN = f"{PREFIX}/deduction/horn/nemotron-3-super-120b-a12b/"
FIXED_NOW = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)


class AppendOnlyS3(FakeS3Client):
    """The shared fake, but a write to an existing key fails the test."""

    def put_object(self, Bucket, Key, Body):
        assert Key not in self.objects, f"overwrote s3://{Bucket}/{Key}"
        super().put_object(Bucket=Bucket, Key=Key, Body=Body)


@pytest.fixture
def fake_s3(monkeypatch):
    """Route ``_aws.fresh_client`` to an in-memory, append-only bucket."""
    client = AppendOnlyS3()
    monkeypatch.setattr(_aws, "fresh_client", client._fresh)
    return client


def _parts(fake_s3):
    return sorted(k for k in fake_s3.objects if k.startswith(NEMO_HORN))


def _horn_run(model, rung, out, **kw):
    kw.setdefault("reps", 1)
    return bt.run_horn(model, "us-east-1", {"reasoning_effort": "high"}, rung, [100], out=out, **kw)


def test_induction_s3_writes_expected_keys_resumes_and_pulls_a_readable_tree(
    mantle, fake_s3, tmp_path, monkeypatch
):
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    harness = bt.induction_harness([DSV31], seeds=[0], results_dir=tmp_path / "a", s3_uri=URI)
    assert isinstance(harness.store, S3ResultsStore) and harness.store.describe() == URI + "/induction"
    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"}, max_parallel=4)
    assert len(mantle.requests) == 27
    pattern = re.compile(rf"{PREFIX}/induction/deepseek-v3\.1/seed=0/(\w+)--\d{{8}}T\d{{6}}\.\d{{6}}Z\.yaml")
    assert sorted(m.group(1) for m in map(pattern.fullmatch, fake_s3.objects) if m) == sorted(bt.INDUCTION_ARMS)
    assert len(fake_s3.objects) == 3 and not (tmp_path / "a").exists(), "S3 is the only copy written"
    assert set(fake_s3.requested) == {("s3", "us-west-2")}

    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"})
    assert len(mantle.requests) == 27, "a finished replicate must not be re-billed"
    assert len(fake_s3.objects) == 3

    # Objects the reader cannot handle are not mirrored; a supersession marker is.
    fake_s3.objects[f"{PREFIX}/induction/README.txt"] = b"x"
    fake_s3.objects[f"{PREFIX}/induction/deepseek-v3.1/seed=abc/extens--1.yaml"] = b"x"
    mirror = tmp_path / "mirror"
    assert bt.pull_induction(URI, mirror) == 3
    assert bt.pull_induction(URI, mirror) == 0, "same-size files are kept"
    cells = induction_repro.load_cells(mirror / "induction")
    assert set(cells) == {("deepseek-v3.1", arm) for arm in bt.INDUCTION_ARMS}
    assert (mirror / "induction" / "induction" / "deepseek-v3.1" / "seed=0").is_dir()
    assert not list(mirror.rglob("*.part")) and not list(mirror.rglob("README.txt"))
    # The attention replay reads the same mirror, from the same root as the report.
    ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_for_bedrock_trio")
    runs = ar.find_runs(mirror / "induction", "deepseek-v3.1")
    assert sorted(run.path.name.split("--")[0] for run in runs) == sorted(bt.INDUCTION_ARMS)

    stamp = harness.store.list_runs(_addr("noise_intens"))[0]
    harness.store.supersede(_addr("noise_intens"), stamp, "test")
    assert bt.pull_induction(URI, mirror) == 1
    assert set(induction_repro.load_cells(mirror / "induction")) == {
        ("deepseek-v3.1", arm) for arm in ("intens", "extens")
    }


def _addr(info):
    return ReplicateAddress(tag="ds_v31", info=info, seed=0, model="deepseek-v3.1")


def test_horn_s3_uploads_parts_and_a_fresh_machine_resumes_with_no_requests(mantle, fake_s3, tmp_path):
    rung = bt.render_horn_rung(2, [100], rungs_dir=tmp_path / "rungs")
    theory = Theory.from_json((rung / "s0100" / "theory.json").read_text())
    mantle.default_response = _final("\n".join(designed_proof(theory)), reasoning="plan")
    first = tmp_path / "a" / "rows.jsonl"
    rows = _horn_run(NEMO, rung, first, s3_uri=URI, push_every=3)
    assert len(rows) == 8 == len(mantle.requests)
    # 8 new rows with a push every 3: parts of 3 and 3, then the remaining 2 in the finally.
    parts = _parts(fake_s3)
    assert len(parts) == 3 and all(re.fullmatch(r"rows--\d{8}T\d{6}\.\d{6}Z\.jsonl", p[len(NEMO_HORN) :]) for p in parts)
    in_bucket = [l for p in parts for l in fake_s3.objects[p].decode().splitlines()]
    assert sorted(in_bucket) == sorted(first.read_text().splitlines()) and len(set(in_bucket)) == 8
    assert all(json.loads(l)["provider"] == "bedrock-mantle:us-east-1" for l in in_bucket)
    assert set(fake_s3.requested) == {("s3", "us-west-2")}

    # A machine with an empty local tree resumes from the bucket alone.
    objects = dict(fake_s3.objects)
    second = tmp_path / "b" / "rows.jsonl"
    assert _horn_run(NEMO, rung, second, s3_uri=URI) == []
    assert len(mantle.requests) == 8, "rows collected elsewhere must not be re-billed"
    assert sorted(second.read_text().splitlines()) == sorted(in_bucket)
    assert fake_s3.objects == objects, "nothing new to push"
    cells, dropped = stats.load_rows([second])
    assert not dropped and len(cells[("nemotron-3-super-120b-a12b", "m2")]) == 8


def test_push_and_pull_horn_rows_are_append_only_and_exact(fake_s3, tmp_path, monkeypatch):
    monkeypatch.setattr(bt, "utcnow", lambda: FIXED_NOW)
    out = tmp_path / "rows.jsonl"
    key = "nemotron-3-super-120b-a12b"
    assert bt.push_horn_rows(key, URI, out=out) is None, "no file, nothing to push"
    out.write_text('{"n": 1}\n{"n": 2}\n{"n": 2}\n')
    first = bt.push_horn_rows(key, URI, out=out)
    assert first == f"{NEMO_HORN}rows--20260810T193000.000000Z.jsonl"
    assert fake_s3.objects[first] == b'{"n": 1}\n{"n": 2}\n', "each missing line once"
    assert bt.push_horn_rows(key, URI, out=out) is None and len(fake_s3.objects) == 1
    # Same instant, new line: the next free stamp, one second later; the first part stays.
    with out.open("a") as fh:
        fh.write('{"n": 3}\n')
    second = bt.push_horn_rows(key, URI, out=out)
    assert second == f"{NEMO_HORN}rows--20260810T193001.000000Z.jsonl"
    assert fake_s3.objects[second] == b'{"n": 3}\n' and fake_s3.objects[first] == b'{"n": 1}\n{"n": 2}\n'

    # Pull appends only what the file lacks, parts in key order, behind a torn last line.
    other = tmp_path / "other.jsonl"
    other.write_text('{"n": 2}\n{"n"')
    assert bt.pull_horn_rows(key, URI, out=other) == 2
    assert other.read_text() == '{"n": 2}\n{"n"\n{"n": 1}\n{"n": 3}\n'
    assert bt.pull_horn_rows(key, URI, out=other) == 0
    assert bt.pull_horn_rows(key, URI, results_dir=tmp_path / "fresh") == 3
    assert (tmp_path / "fresh" / "horn" / f"{key}.jsonl").read_text() == '{"n": 1}\n{"n": 2}\n{"n": 3}\n'
    assert bt.pull_horn_rows("deepseek-v3.1", URI, out=tmp_path / "none.jsonl") == 0
    assert not (tmp_path / "none.jsonl").exists()


def test_render_horn_rung_leaves_all_eight_arms_and_keeps_paper_arms_identical(mantle, tmp_path):
    assert bt.HORN_ARMS == tuple(ALL_ARMS) and bt.HORN_ARMS[:4] == bt.HORN_PAPER_ARMS and len(bt.HORN_ARMS) == 8
    rungs = tmp_path / "rungs"
    # A rung rendered with the paper arms only (an earlier version of this module) gains the rest.
    rung = bt.render_horn_rung(2, [100], rungs_dir=rungs, arms=bt.HORN_PAPER_ARMS)
    assert not (rung / "s0100" / "fwd").exists()
    paper = {a: (rung / "s0100" / a / "prompt.md").read_bytes() for a in bt.HORN_PAPER_ARMS}
    assert bt.render_horn_rung(2, [100], rungs_dir=rungs) == rung
    assert {a for a in ALL_ARMS if (rung / "s0100" / a / "prompt.md").is_file()} == set(ALL_ARMS)
    assert paper == {a: (rung / "s0100" / a / "prompt.md").read_bytes() for a in bt.HORN_PAPER_ARMS}
    assert horn_repro.verify_rung(rung, 2, [100]) == []
    with pytest.raises(ValueError, match="bad arm"):
        bt.render_horn_rung(2, [100], rungs_dir=rungs, arms=("nope",))

    theory = Theory.from_json((rung / "s0100" / "theory.json").read_text())
    mantle.default_response = _final("\n".join(designed_proof(theory)), reasoning="plan")
    rows = _horn_run(NEMO, rung, tmp_path / "rows.jsonl")
    assert sorted(r["arm"] for r in rows) == sorted(ALL_ARMS) and {r["verdict"] for r in rows} == {"success"}
    only = _horn_run(NEMO, rung, tmp_path / "paper.jsonl", arms=bt.HORN_PAPER_ARMS)
    assert sorted(r["arm"] for r in only) == sorted(bt.HORN_PAPER_ARMS)


def test_push_file_refuses_an_existing_key_and_check_bucket_reports_failures(fake_s3, tmp_path):
    probe = tmp_path / "probes.json"
    probe.write_text("{}\n")
    key = bt.push_file(probe, URI, "probes/probes--1.json")
    assert key == f"{PREFIX}/probes/probes--1.json" and fake_s3.objects[key] == b"{}\n"
    probe.write_text("changed")
    with pytest.raises(FileExistsError, match="append-only"):
        bt.push_file(probe, URI, "probes/probes--1.json")
    assert fake_s3.objects[key] == b"{}\n"

    bt.check_bucket(URI)
    assert fake_s3.probes[-1] == (f"{PREFIX}/", 1)

    def denied(**_):
        raise ClientError({"Error": {"Code": "AccessDenied", "Message": "no"}}, "ListObjectsV2")

    fake_s3.list_objects_v2 = denied
    with pytest.raises(RuntimeError, match="cannot list s3://.*AccessDenied"):
        bt.check_bucket(URI)


# ----------------------------------------------------------------- prompt fidelity


@pytest.fixture
def prompts(monkeypatch):
    """This branch's prompts of seed 0, and the released ones: the same quizzes under the
    earlier ``extens`` definition, which carried the listing only."""
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())

    def arms(quizzes):
        return {a: [SimpleNamespace(prompt=q.prompt) for q in quizzes[a]] for a in bt.INDUCTION_ARMS}

    mine = arms(rs.make_quizzes(0, "deepseek-v3.1"))
    listing_only = replace(rs.CONDITIONS["extens"], context=lambda c: c.extensional)
    monkeypatch.setattr(rs, "CONDITIONS", MappingProxyType(dict(rs.CONDITIONS) | {"extens": listing_only}))
    released = {a: [q.prompt for q in qs] for a, qs in arms(rs.make_quizzes(0, "deepseek-v3.1")).items()}
    return mine, released


def test_check_induction_prompts_accepts_the_consistent_case(prompts):
    mine, released = prompts
    assert mine["extens"][0].prompt != released["extens"][0], "the two definitions must differ"
    assert mine["intens"][0].prompt == released["intens"][0]
    assert mine["noise_intens"][0].prompt != released["noise_intens"][0], "noise is padded to the new extens"
    bt.check_induction_prompts(mine, released, StubTokenizer())


def _edited(mine, arm, i, fn):
    out = {a: list(qs) for a, qs in mine.items()}
    out[arm][i] = SimpleNamespace(prompt=fn(out[arm][i].prompt))
    return out


def test_check_induction_prompts_names_the_arm_and_index_of_a_mismatch(prompts):
    mine, released = prompts
    tok = StubTokenizer()
    with pytest.raises(AssertionError, match=r"intens\[3\]"):
        bt.check_induction_prompts(_edited(mine, "intens", 3, lambda p: p + " "), released, tok)
    # A rules block that is not the intens prompt's (the first label changed in extens only) ...
    with pytest.raises(AssertionError, match=r"extens\[2\].*rules block"):
        bt.check_induction_prompts(_edited(mine, "extens", 2, lambda p: p.replace("write ", "write Z", 1)), released, tok)
    # ... or cut short: the last rule dropped, which is still a prefix of the intens rules.
    last_rule = re.findall(r"Every \d+ positions write \w+\.\n", mine["intens"][5].prompt)[-1]
    with pytest.raises(AssertionError, match=r"extens\[5\].*rules block"):
        bt.check_induction_prompts(_edited(mine, "extens", 5, lambda p: p.replace(last_rule, "", 1)), released, tok)
    # No rules block at all (the earlier definition) is refused, not matched.
    with pytest.raises(AssertionError, match=r"extens\[0\].*rules block"):
        bt.check_induction_prompts(_edited(mine, "extens", 0, lambda _p: released["extens"][0]), released, tok)
    # A listing that differs from the released one.
    with pytest.raises(AssertionError, match=r"extens\[1\]"):
        bt.check_induction_prompts(_edited(mine, "extens", 1, lambda p: p.replace("Position 2:", "Position 2 :")), released, tok)
    with pytest.raises(AssertionError, match=r"noise_intens\[4\]"):
        bt.check_induction_prompts(_edited(mine, "noise_intens", 4, lambda p: p + "\n\nextra words"), released, tok)
    with pytest.raises(AssertionError, match="extens: the released file has no prompts"):
        bt.check_induction_prompts(mine, {"intens": released["intens"]}, tok)


# ------------------------------------------------------------ interrupted and failing runs
def _proof_response(mantle, tmp_path, **kw):
    rung = bt.render_horn_rung(2, [100], rungs_dir=tmp_path / "rungs")
    theory = Theory.from_json((rung / "s0100" / "theory.json").read_text())
    mantle.default_response = _final("\n".join(designed_proof(theory)), **kw)
    return rung


def test_horn_interrupt_keeps_every_started_cell_and_bills_no_queued_one(mantle, fake_s3, tmp_path, monkeypatch):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    sweep, out = bt.load_sweep(), tmp_path / "rows.jsonl"
    run_cell, dump_row, dumps = sweep.run_cell, bt._dump_row, []

    def slow_cell(*args):
        time.sleep(0.2)  # keeps most of the queue unstarted when the interrupt lands
        return run_cell(*args)

    def interrupting_dump(row):
        dumps.append(row)
        if len(dumps) == 2:
            raise KeyboardInterrupt
        return dump_row(row)

    monkeypatch.setattr(sweep, "run_cell", slow_cell)
    monkeypatch.setattr(bt, "_dump_row", interrupting_dump)
    with pytest.raises(KeyboardInterrupt):
        _horn_run(NEMO, rung, out, s3_uri=URI, concurrency=2)
    started = len(mantle.requests)
    local = out.read_text().splitlines()
    assert 2 <= started < 8, "the queue behind the interrupt is cancelled"
    assert len(local) == started == len(set(local)), "a cell that was sent leaves its row"
    assert sorted(l for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines()) == sorted(local)

    monkeypatch.setattr(bt, "_dump_row", dump_row)
    assert len(_horn_run(NEMO, rung, out, s3_uri=URI)) == 8 - started
    assert len(mantle.requests) == 8, "the rerun sends only the cells the interrupt dropped"


def test_horn_periodic_push_failure_is_survived_and_the_final_one_is_raised(mantle, fake_s3, tmp_path, monkeypatch):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    put, failures = fake_s3.put_object, [2]

    def flaky_put(**kw):
        if failures[0]:
            failures[0] -= 1
            raise ClientError({"Error": {"Code": "ExpiredToken", "Message": "expired"}}, "PutObject")
        put(**kw)

    monkeypatch.setattr(fake_s3, "put_object", flaky_put)
    out = tmp_path / "a.jsonl"
    assert len(_horn_run(NEMO, rung, out, s3_uri=URI, push_every=3)) == 8
    in_bucket = [l for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines()]
    assert sorted(in_bucket) == sorted(out.read_text().splitlines()) and len(in_bucket) == 8

    # A failing final push raises, with every row already on disk for the next run to push.
    fake_s3.objects.clear()
    failures[0] = 99
    other = tmp_path / "b.jsonl"
    other.write_text(out.read_text())
    with pytest.raises(ClientError):
        _horn_run(NEMO, rung, other, s3_uri=URI, reps=2, push_every=99)
    assert len(other.read_text().splitlines()) == 16 and not fake_s3.objects
    failures[0] = 0
    assert bt.push_horn_rows(NEMO.key, URI, out=other) and len(mantle.requests) == 16


def test_horn_rows_with_unicode_line_separators_stay_one_line_and_resume(mantle, tmp_path):
    rung = _proof_response(mantle, tmp_path, reasoning="step one step two then\x85done")
    out = tmp_path / "rows.jsonl"
    rows = _horn_run(NEMO, rung, out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8 and [json.loads(l) for l in lines] == rows
    assert all(" " in r["reasoning"] and "\x85" in r["reasoning"] for r in rows)
    assert _horn_run(NEMO, rung, out) == [] and len(mantle.requests) == 8
    cells, dropped = stats.load_rows([out])
    assert not dropped and len(cells[(NEMO.key, "m2")]) == 8


def test_a_torn_last_line_is_neither_pushed_nor_counted(fake_s3, tmp_path):
    out = tmp_path / "rows.jsonl"
    out.write_text('{"spec_key": "k", "arm": "lem", "verdict": "success", "reasoning": "r"}\n{"spec_k')
    key = bt.push_horn_rows(NEMO.key, URI, out=out)
    assert fake_s3.objects[key].decode().count("\n") == 1 and '{"spec_k\n' not in fake_s3.objects[key].decode()
    with out.open("a") as fh:
        fh.write('ey": "k", "arm": "pad", "verdict": "wrong", "reasoning": ""}\n')
    second = bt.push_horn_rows(NEMO.key, URI, out=out)
    assert json.loads(fake_s3.objects[second])["arm"] == "pad", "the completed line goes up whole"
    out.write_text(out.read_text() + '{"torn')
    breakdown = bt.horn_breakdown([out])
    assert sum(c["rows"] for c in breakdown.values()) == 2


def test_horn_reference_gives_published_rates_and_output_lengths(tmp_path):
    deep, nemo = DSV31.key, NEMO.key
    cells = tmp_path / "cells.csv"
    cells.write_text(
        "model,model_id,m,arm,seed,rep,verdict,route,steps,finish_reason,completion_tokens,batch\n"
        f"{deep},x,64,lem,100,0,success,short,1,stop,8192,2026-09\n"
        f"{deep},x,64,lem,100,1,success,short,1,stop,8193,2026-09\n"
        f"{deep},x,64,lem,101,0,invalid_step,short,1,stop,90000,2026-09\n"
        f"{deep},x,64,lem,101,1,invalid_step,short,1,stop,10,2026-09\n"
        "glm-4.7,x,48,lem,100,0,success,short,1,stop,10,2026-09\n",
        encoding="utf-8",
    )
    ref = bt.horn_reference([deep, GEMMA.key], cells)
    assert ref == {
        (deep, "lem"): {"cells": 4, "m": 64, "pass": 50.0, "tokens_median": 8193, "tokens_max": 90000}
    }

    # The committed cells: the paper table's rates, with outputs far above the 8K and 32K
    # caps of the model cards and within the budget sent here.
    real = bt.horn_reference(list(bt.TRIO))
    assert {k for k, _ in real} == {deep, nemo}
    assert {arm for _, arm in real} == {"lem", "pad", "disc", "both", "rep", "tjunk"}
    assert all(v["cells"] == 300 for v in real.values())
    assert round(real[(deep, "lem")]["pass"], 1) == 64.0
    assert round(real[(nemo, "rep")]["pass"], 1) == 61.3
    assert real[(deep, "lem")]["tokens_median"] > 8192
    assert all(v["tokens_max"] <= bt.HORN_MAX_TOKENS for v in real.values())
