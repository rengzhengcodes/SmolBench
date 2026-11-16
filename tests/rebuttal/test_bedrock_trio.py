"""Offline tests for ``rebuttal/bedrock_trio.py`` against the shared OpenAI stub."""

import collections
import json
import os
import re
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
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
    assert len(mantle.requests) == 36, "four arms x 9 questions"
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
    assert all(v["empty_response"] == 0 for v in report.values())
    assert set(report) == {("deepseek-v3.1", arm) for arm in bt.INDUCTION_ARMS}
    seed_dir = tmp_path / "induction" / "induction" / "deepseek-v3.1" / "seed=0"
    assert sorted(p.name.split("--")[0] for p in seed_dir.glob("*.yaml")) == sorted(bt.INDUCTION_ARMS)

    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"})
    assert len(mantle.requests) == 36, "a finished replicate must not be re-billed"


def test_an_answer_left_in_the_reasoning_channel_is_counted(mantle, tmp_path, monkeypatch):
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    # What Bedrock sometimes returns: the bare answer as reasoning and no content.
    mantle.default_response = _final("", reasoning="280")
    harness = bt.induction_harness([DSV31], seeds=[0], results_dir=tmp_path)
    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"}, max_parallel=4)
    report = bt.induction_reasoning_report(tmp_path)
    assert all(v["empty_response"] == 9 == v["null_score"] and v["unreasoned"] == 0 for v in report.values())


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
    iclr = json.loads((REPO_ROOT / "smolbench/deduction/horn/iclr.json").read_text())
    assert {r["scoring"] for r in rows} == {iclr["scoring"]} == {bt.HORN_SCORING}
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
    assert len(mantle.requests) == 36
    pattern = re.compile(rf"{PREFIX}/induction/deepseek-v3\.1/seed=0/(\w+)--\d{{8}}T\d{{6}}\.\d{{6}}Z\.yaml")
    assert sorted(m.group(1) for m in map(pattern.fullmatch, fake_s3.objects) if m) == sorted(bt.INDUCTION_ARMS)
    assert len(fake_s3.objects) == 4 and not (tmp_path / "a").exists(), "S3 is the only copy written"
    assert set(fake_s3.requested) == {("s3", "us-west-2")}

    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"})
    assert len(mantle.requests) == 36, "a finished replicate must not be re-billed"
    assert len(fake_s3.objects) == 4

    # Objects the reader cannot handle are not mirrored; a supersession marker is.
    fake_s3.objects[f"{PREFIX}/induction/README.txt"] = b"x"
    fake_s3.objects[f"{PREFIX}/induction/deepseek-v3.1/seed=abc/extens--1.yaml"] = b"x"
    mirror = tmp_path / "mirror"
    assert bt.pull_induction(URI, mirror) == 4
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
        ("deepseek-v3.1", arm) for arm in ("intens", "extens", "related_intens")
    }


def test_arm_names_and_quiz_factory():
    from smolbench.induction.periodic import REVIEW_CONDITIONS

    assert bt.INDUCTION_PAPER_ARMS == ("intens", "noise_intens", "extens")
    assert bt.INDUCTION_ARMS == bt.INDUCTION_PAPER_ARMS + tuple(REVIEW_CONDITIONS)
    assert bt.INDUCTION_ARMS[-1] == "related_intens"


def test_a_bucket_holding_the_three_paper_arms_gets_only_the_review_arm(
    mantle, fake_s3, tmp_path, monkeypatch
):
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    # The bucket as the earlier runner left it: the three paper arms of seed 0.
    with monkeypatch.context() as m:
        m.setattr(bt, "INDUCTION_ARMS", bt.INDUCTION_PAPER_ARMS)
        old = bt.induction_harness([DSV31], seeds=[0], results_dir=tmp_path, s3_uri=URI)
        bt.run_induction(old, DSV31, "us-east-1", {"reasoning_effort": "high"}, max_parallel=4)
    assert len(mantle.requests) == 27
    before = dict(fake_s3.objects)
    assert len(before) == 3

    # A tree without the review arm: the mirror and both reports work.
    mirror = tmp_path / "mirror"
    assert bt.pull_induction(URI, mirror) == 3
    assert set(induction_repro.load_cells(mirror / "induction")) == {
        ("deepseek-v3.1", a) for a in bt.INDUCTION_PAPER_ARMS
    }
    assert set(bt.induction_reasoning_report(mirror)) == {("deepseek-v3.1", a) for a in bt.INDUCTION_PAPER_ARMS}
    text = induction_repro.report(mirror / "induction")
    assert "noise_intens-extens" in text and "related_intens" not in text

    harness = bt.induction_harness([DSV31], seeds=[0], results_dir=tmp_path, s3_uri=URI)
    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"}, max_parallel=4)
    assert len(mantle.requests) == 36, "only the review arm's 9 questions are sent"
    sent = [r["body"]["messages"][-1]["content"] for r in mantle.requests[27:]]
    assert all(re.search(r"write [a-z]+\.\n\s*\nQuestion:", p) for p in sent)
    new = sorted(set(fake_s3.objects) - set(before))
    assert len(new) == 1 and re.fullmatch(
        rf"{PREFIX}/induction/deepseek-v3\.1/seed=0/related_intens--\d{{8}}T\d{{6}}\.\d{{6}}Z\.yaml", new[0]
    ), new
    assert all(fake_s3.objects[k] == v for k, v in before.items()), "paper-arm objects untouched"

    # A tree with the review arm.
    assert bt.pull_induction(URI, mirror) == 1
    cells = induction_repro.load_cells(mirror / "induction")
    assert set(cells) == {("deepseek-v3.1", a) for a in bt.INDUCTION_ARMS}
    ind = bt.induction_reasoning_report(mirror)
    assert ind[("deepseek-v3.1", "related_intens")]["marks"] == 9
    assert ind[("deepseek-v3.1", "related_intens")]["unreasoned"] == 0
    text = induction_repro.report(mirror / "induction")
    assert any(l.split()[:1] == ["related_intens"] for l in text.splitlines())
    assert any(l.split()[:1] == ["related_intens-extens"] for l in text.splitlines())


def test_a_local_tree_holding_the_paper_arms_gets_only_the_review_arm(mantle, tmp_path, monkeypatch):
    rs = bt.load_run_study()
    monkeypatch.setattr(rs, "for_model", lambda _model: StubTokenizer())
    mantle.default_response = _final("280", reasoning="2520 / 9")
    with monkeypatch.context() as m:
        m.setattr(bt, "INDUCTION_ARMS", bt.INDUCTION_PAPER_ARMS)
        bt.run_induction(bt.induction_harness([DSV31], [0], results_dir=tmp_path), DSV31, "us-east-1", {})
    assert len(mantle.requests) == 27
    bt.run_induction(bt.induction_harness([DSV31], [0], results_dir=tmp_path), DSV31, "us-east-1", {})
    assert len(mantle.requests) == 36
    seed_dir = tmp_path / "induction" / "induction" / "deepseek-v3.1" / "seed=0"
    names = sorted(p.name.split("--")[0] for p in seed_dir.glob("*.yaml"))
    assert names == sorted(bt.INDUCTION_ARMS)


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

    def arms(quizzes, names):
        return {a: [SimpleNamespace(prompt=q.prompt) for q in quizzes[a]] for a in names}

    mine = arms(bt.induction_quizzes(0, "deepseek-v3.1"), bt.INDUCTION_ARMS)
    listing_only = replace(rs.CONDITIONS["extens"], context=lambda c: c.extensional)
    monkeypatch.setattr(rs, "CONDITIONS", MappingProxyType(dict(rs.CONDITIONS) | {"extens": listing_only}))
    released = {
        a: [q.prompt for q in qs]
        for a, qs in arms(rs.make_quizzes(0, "deepseek-v3.1"), bt.INDUCTION_PAPER_ARMS).items()
    }
    return mine, released


def test_check_induction_prompts_accepts_the_consistent_case(prompts):
    mine, released = prompts
    assert mine["extens"][0].prompt != released["extens"][0], "the two definitions must differ"
    assert mine["intens"][0].prompt == released["intens"][0]
    assert mine["noise_intens"][0].prompt != released["noise_intens"][0], "noise is padded to the new extens"
    assert "related_intens" not in released, "the review arm has no released counterpart"
    report = bt.check_induction_prompts(mine, released, StubTokenizer())
    assert report == bt.check_related_prompts(mine["intens"], mine["extens"], mine["related_intens"], StubTokenizer())
    assert len(report) == 9
    for row, q in zip(report, mine["related_intens"]):
        assert row["added_lines"] == len(re.findall(r"Every \d+ positions write [a-z]+\.\n", q.prompt)) - 9
        assert row["added_lines"] > 100 and row["pad_tokens"] >= 0


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


_RULE = re.compile(r"Every (\d+) positions write ([a-z]+)\.\n")


def _added(mine, i):
    """The added rule lines of related_intens[i] (the real rules are its first 9)."""
    return _RULE.findall(mine["related_intens"][i].prompt)[9:]


def _check(mine, released):
    return bt.check_induction_prompts(mine, released, StubTokenizer())


def test_related_self_check_names_the_problem(prompts):
    mine, released = prompts
    k0, lab0 = _added(mine, 3)[0]
    first = f"Every {k0} positions write {lab0}.\n"
    k1, lab1 = _added(mine, 3)[1]
    second = f"Every {k1} positions write {lab1}.\n"
    real_label = _RULE.findall(mine["intens"][0].prompt)[0][1]

    def tampered(fn, i=3):
        return _edited(mine, "related_intens", i, fn)

    with pytest.raises(AssertionError, match=r"related_intens: no prompts"):
        _check({a: v for a, v in mine.items() if a != "related_intens"}, released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*question"):
        _check(tampered(lambda p: p.replace("How many", "How  many")), released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*period"):
        _check(tampered(lambda p: p.replace(first, f"Every 97 positions write {lab0}.\n", 1)), released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*label"):
        _check(tampered(lambda p: p.replace(first, f"Every {k0} positions write {real_label}.\n", 1)), released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*label"):
        _check(tampered(lambda p: p.replace(first, f"Every {k0} positions write {real_label}q.\n", 1)), released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*repeat"):
        _check(tampered(lambda p: p.replace(first + second, first + first, 1)), released)
    # The stream reference is the first question with the most added lines; 3 is not it.
    counts = [len(_added(mine, i)) for i in range(9)]
    assert counts.index(max(counts)) != 3
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*prefix"):
        _check(tampered(lambda p: p.replace(first + second, second + first, 1)), released)
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*token count"):
        _check(tampered(lambda p: p.replace("\nQuestion:", "\x0b\x0b\x0b\nQuestion:")), released)
    # The whitespace-only control (noise_intens) has the right count but no related text.
    with pytest.raises(AssertionError, match=r"related_intens\[3\].*leftover"):
        _check(tampered(lambda _p: mine["noise_intens"][3].prompt), released)
    with pytest.raises(AssertionError, match=r"related_intens\[0\].*rules"):
        _check(tampered(lambda p: p.replace("write ", "write z", 1), i=0), released)


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


def _reject_with_400(mantle, monkeypatch, rejects=lambda n: True):
    """Answer request number ``n`` (from 0) with an HTTP 400 when ``rejects(n)``, as the stub otherwise would.

    A 400 is a permanent error to the client, so the cell becomes an ``exception`` row at once
    (the stub alone always answers 200, and a retryable error would wait out the client's backoff).
    """
    handler = mantle.RequestHandlerClass
    do_post = handler.do_POST

    def post(self):
        n = len(mantle.requests)
        if not rejects(n):
            return do_post(self)
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0") or "0")) or b"{}")
        mantle.requests.append({"path": self.path, "body": payload, "headers": dict(self.headers)})
        return self._reply({"error": {"message": "ExpiredTokenException"}}, 400)

    monkeypatch.setattr(handler, "do_POST", post)


def _local_and_bucket(fake_s3, out):
    local = out.read_text().splitlines() if out.exists() else []
    return local, [l for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines()]


def test_horn_deadline_in_the_past_starts_no_cell_and_writes_no_row(mantle, fake_s3, tmp_path, capsys):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    out = tmp_path / "rows.jsonl"
    assert _horn_run(NEMO, rung, out, s3_uri=URI, deadline=FIXED_NOW) == []
    assert mantle.requests == [] and _local_and_bucket(fake_s3, out) == ([], [])
    assert "8 of 8 cells left unstarted" in capsys.readouterr().out


def test_horn_deadline_passing_mid_run_keeps_started_cells_and_a_rerun_sends_the_rest(
    mantle, fake_s3, tmp_path, monkeypatch, capsys
):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    sweep, out = bt.load_sweep(), tmp_path / "rows.jsonl"
    run_cell = sweep.run_cell

    def slow_cell(*args):
        time.sleep(1.0)  # the deadline passes while the first cells run; the queue is not started
        return run_cell(*args)

    monkeypatch.setattr(sweep, "run_cell", slow_cell)
    deadline = bt.utcnow() + timedelta(seconds=0.5)
    rows = _horn_run(NEMO, rung, out, s3_uri=URI, concurrency=2, deadline=deadline)
    started = len(mantle.requests)
    assert 0 < started < 8 and len(rows) == started, "a cell started before the deadline finishes and keeps its row"
    local, bucket = _local_and_bucket(fake_s3, out)
    assert len(local) == started and sorted(bucket) == sorted(local)
    assert f"{8 - started} of 8 cells left unstarted" in capsys.readouterr().out

    monkeypatch.setattr(sweep, "run_cell", run_cell)
    assert len(_horn_run(NEMO, rung, out, s3_uri=URI)) == 8 - started
    assert len(mantle.requests) == 8, "the rerun sends exactly the cells the deadline left"


def test_horn_stops_after_consecutive_failures_pushes_and_a_later_run_completes(
    mantle, fake_s3, tmp_path, monkeypatch
):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    rejecting = [True]
    _reject_with_400(mantle, monkeypatch, lambda _n: rejecting[0])
    out = tmp_path / "rows.jsonl"
    with pytest.raises(bt.HornRunStopped, match=r"2 consecutive.*last error: HTTPError: 400") as stopped:
        _horn_run(NEMO, rung, out, s3_uri=URI, concurrency=1, max_consecutive_failures=2)
    assert isinstance(stopped.value, RuntimeError)
    sent = len(mantle.requests)
    assert 2 <= sent < 8, "the cells behind the failures are not started"
    local, bucket = _local_and_bucket(fake_s3, out)
    assert len(local) == sent and sorted(bucket) == sorted(local), "the final push still happened"
    assert {json.loads(l)["verdict"] for l in local} == {"exception"}

    # Exception rows are not done: the rerun repeats those cells and sends the never-started ones.
    rejecting[0] = False
    rows = _horn_run(NEMO, rung, out, s3_uri=URI)
    assert len(rows) == 8 and {r["verdict"] for r in rows} == {"success"}
    assert len(mantle.requests) == sent + 8


def test_horn_failure_count_resets_on_a_success_and_zero_disables_the_limit(mantle, tmp_path, monkeypatch):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    # With one worker the rows come back in request order: two failures, a success, and so on.
    _reject_with_400(mantle, monkeypatch, lambda n: n % 3 != 2)
    rows = _horn_run(NEMO, rung, tmp_path / "a.jsonl", concurrency=1, max_consecutive_failures=3)
    assert [r["verdict"] == "exception" for r in rows] == [True, True, False, True, True, False, True, True]

    _reject_with_400(mantle, monkeypatch)
    rows = _horn_run(NEMO, rung, tmp_path / "b.jsonl", concurrency=1, max_consecutive_failures=0)
    assert len(rows) == 8 and {r["verdict"] for r in rows} == {"exception"}


def test_horn_refuses_a_naive_deadline_and_a_negative_failure_limit(mantle, tmp_path):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    with pytest.raises(ValueError, match="timezone-aware"):
        _horn_run(NEMO, rung, tmp_path / "a.jsonl", deadline=datetime(2026, 11, 16, 10, 30))
    with pytest.raises(ValueError, match="max_consecutive_failures"):
        _horn_run(NEMO, rung, tmp_path / "a.jsonl", max_consecutive_failures=-1)
    assert mantle.requests == []


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


# ------------------------------------------------- replicate filter, second process, ramp
def _store_rows(fake_s3):
    """Every row line in the bucket, parsed, in part order."""
    return [json.loads(l) for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines()]


def _cell_counts(rows):
    return collections.Counter((r["arm"], r["seed"], r["rep"]) for r in rows)


def test_horn_rep_indices_run_only_those_replicates_and_a_later_call_sends_the_rest(mantle, tmp_path, capsys):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    out = tmp_path / "rows.jsonl"
    rows = _horn_run(NEMO, rung, out, reps=3, rep_indices=[1])
    assert len(rows) == 8 == len(mantle.requests)
    assert {r["rep"] for r in rows} == {1} and {r["body"]["seed"] for r in mantle.requests} == {1}
    assert "0 of 8 cells of this call are already done" in capsys.readouterr().out

    # The decoding seed is still the replicate index, and what the filter left is what remains.
    assert len(_horn_run(NEMO, rung, out, reps=3)) == 16 == len(mantle.requests) - 8
    assert {r["body"]["seed"] for r in mantle.requests[8:]} == {0, 2}
    assert _horn_run(NEMO, rung, out, reps=3, rep_indices=[0, 1, 2]) == []
    assert len(mantle.requests) == 24
    assert _horn_run(NEMO, rung, tmp_path / "none.jsonl", reps=3, rep_indices=[]) == []
    assert len(mantle.requests) == 24, "an empty filter runs nothing"
    printed = capsys.readouterr().out
    assert "8 of 24 cells of this call are already done" in printed and "24 of 24 cells of this call" in printed


@pytest.mark.parametrize("bad", [[3], [0, -1], [1, 7]])
def test_horn_refuses_replicate_indices_outside_the_protocol(mantle, tmp_path, bad):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    with pytest.raises(ValueError, match="rep_indices"):
        _horn_run(NEMO, rung, tmp_path / "a.jsonl", reps=3, rep_indices=bad)
    assert mantle.requests == [] and not (tmp_path / "a.jsonl").exists()


def test_horn_rows_path_labels_a_working_copy_and_refuses_odd_labels(tmp_path):
    key = NEMO.key
    assert bt.horn_rows_path(key, tmp_path) == tmp_path / "horn" / f"{key}.jsonl"
    assert bt.horn_rows_path(key, tmp_path, "east-2.v1_x") == tmp_path / "horn" / f"{key}--east-2.v1_x.jsonl"
    for bad in ("", "a/b", "a b", "é", "../x"):
        with pytest.raises(ValueError, match="label"):
            bt.horn_rows_path(key, tmp_path, bad)


def _two_regions(mantle, rung, fake_s3, tmp_path, **kw):
    """Run replicates 0 and 2 from us-east-1 and replicate 1 from us-east-2, one local file each."""
    runs = {}
    for label, region, reps in (("east-1", "us-east-1", [0, 2]), ("east-2", "us-east-2", [1])):
        out = bt.horn_rows_path(NEMO.key, tmp_path, label)
        runs[label] = (out, bt.run_horn(
            NEMO, region, {"reasoning_effort": "high"}, rung, [100], reps=3, out=out, s3_uri=URI,
            rep_indices=reps, **kw))
    return runs


def test_two_processes_of_one_model_fill_the_store_once_and_every_file_after_a_pull(
    mantle, fake_s3, tmp_path, monkeypatch, capsys
):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    monkeypatch.setattr(bt, "utcnow", lambda: FIXED_NOW)  # both pushes pick the same stamp
    runs = _two_regions(mantle, rung, fake_s3, tmp_path)
    (out1, rows1), (out2, rows2) = runs["east-1"], runs["east-2"]
    assert (len(rows1), len(rows2)) == (16, 8) and len(mantle.requests) == 24

    # The store holds every cell once; the same-instant pushes took distinct, free stamps.
    store = _store_rows(fake_s3)
    assert len(store) == 24 and set(_cell_counts(store).values()) == {1} and len(_cell_counts(store)) == 24
    assert len(_parts(fake_s3)) == 2
    assert {r["provider"] for r in store if r["rep"] == 1} == {"bedrock-mantle:us-east-2"}
    assert {r["provider"] for r in store if r["rep"] != 1} == {"bedrock-mantle:us-east-1"}
    out = capsys.readouterr().out
    assert "0 of 16 cells of this call are already done" in out and "0 of 8 cells of this call are already done" in out
    assert "0 of 16 rows written by this call duplicate" in out and "0 of 8 rows written by this call duplicate" in out

    # The second process saw the first one's rows only by pulling them: its file held 16 + 8.
    assert len(out2.read_text().splitlines()) == 24 and len(out1.read_text().splitlines()) == 16
    assert bt.pull_horn_rows(NEMO.key, URI, out=out1) == 8
    assert bt.pull_horn_rows(NEMO.key, URI, out=out2) == 0
    lines = sorted(l for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines())
    assert sorted(out1.read_text().splitlines()) == lines == sorted(out2.read_text().splitlines())

    # The reports read the main file: the existing pull fills it with every row.
    main = bt.horn_rows_path(NEMO.key, tmp_path)
    assert not main.exists() and bt.pull_horn_rows(NEMO.key, URI, results_dir=tmp_path) == 24
    assert sorted(main.read_text().splitlines()) == lines
    cells, dropped = stats.load_rows([main])
    assert not dropped and len(cells[(NEMO.key, "m2")]) == 8, "eight arms"
    assert {len(reps) for per_seed in cells[(NEMO.key, "m2")].values() for reps in per_seed.values()} == {3}

    # Nothing is left to run for either process.
    before = len(mantle.requests)
    assert _two_regions(mantle, rung, fake_s3, tmp_path) and len(mantle.requests) == before
    assert len(_store_rows(fake_s3)) == 24


def test_a_second_process_started_while_the_first_pushes_sees_the_rows_pushed_so_far(
    mantle, fake_s3, tmp_path, monkeypatch
):
    monkeypatch.setenv("HORN_STREAM_COMPLETIONS", "1")  # two overlapping runs share the process environment
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    sweep, run_cell = bt.load_sweep(), bt.load_sweep().run_cell

    def slow_cell(*args):
        time.sleep(0.1)
        return run_cell(*args)

    monkeypatch.setattr(sweep, "run_cell", slow_cell)
    out1, out2 = (bt.horn_rows_path(NEMO.key, tmp_path, name) for name in ("east-1", "east-2"))
    result = {}

    def first():
        try:
            result["rows"] = bt.run_horn(NEMO, "us-east-1", {}, rung, [100], reps=3, out=out1, s3_uri=URI,
                                         concurrency=2, push_every=2, rep_indices=[0, 2])
        except Exception as err:  # pylint: disable=broad-exception-caught
            result["error"] = err

    thread = threading.Thread(target=first)
    thread.start()
    deadline = time.monotonic() + 30
    while not _parts(fake_s3) and time.monotonic() < deadline:
        time.sleep(0.02)
    pushed = set(l for p in _parts(fake_s3) for l in fake_s3.objects[p].decode().splitlines())
    assert pushed, "the first process must have pushed before the second starts"
    rows2 = bt.run_horn(NEMO, "us-east-2", {}, rung, [100], reps=3, out=out2, s3_uri=URI, concurrency=2,
                        rep_indices=[1])
    thread.join(30)
    assert "error" not in result and len(result["rows"]) == 16 and len(rows2) == 8
    assert pushed <= set(out2.read_text().splitlines()), "the second process pulled what the first had pushed"
    store = _store_rows(fake_s3)
    assert len(store) == 24 and set(_cell_counts(store).values()) == {1}
    assert len(mantle.requests) == 24


def test_overlapping_processes_report_the_duplicate_rows(mantle, fake_s3, tmp_path, monkeypatch, capsys):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    out_a, out_b = (bt.horn_rows_path(NEMO.key, tmp_path, name) for name in ("a", "b"))
    # Process A keeps its rows local for now: replicate 1.
    rows_a = bt.run_horn(NEMO, "us-east-1", {}, rung, [100], reps=3, out=out_a, rep_indices=[1])
    capsys.readouterr()

    # Process B (replicates 1 and 2) starts with an empty bucket, so it cannot see A's rows;
    # A's rows reach the bucket while B runs.
    sweep, run_cell, pushed = bt.load_sweep(), bt.load_sweep().run_cell, []

    def push_a_then_run(*args):
        if not pushed:
            pushed.append(bt.push_horn_rows(NEMO.key, URI, out=out_a))
        return run_cell(*args)

    monkeypatch.setattr(sweep, "run_cell", push_a_then_run)
    rows_b = bt.run_horn(NEMO, "us-east-2", {}, rung, [100], reps=3, out=out_b, s3_uri=URI, concurrency=1,
                         rep_indices=[1, 2])
    out = capsys.readouterr().out
    assert "0 of 16 cells of this call are already done" in out
    assert "8 of 16 rows written by this call duplicate" in out
    assert len(_store_rows(fake_s3)) == 24 and sorted(_cell_counts(_store_rows(fake_s3)).values()) == [1] * 8 + [2] * 8
    assert bt.count_horn_duplicates(NEMO.key, URI, rows_a) == 8
    assert bt.count_horn_duplicates(NEMO.key, URI, rows_b) == 8

    # A process that starts now finds replicate 1 done and says so.
    capsys.readouterr()
    assert _horn_run(NEMO, rung, tmp_path / "c.jsonl", reps=3, rep_indices=[1], s3_uri=URI) == []
    assert "8 of 8 cells of this call are already done" in capsys.readouterr().out


def test_an_exception_row_does_not_make_a_retry_a_duplicate(fake_s3, tmp_path):
    cell = {"model": "m", "rung": "r", "arm": "lem", "seed": 100, "rep": 0, "provider": "p"}
    failed, retried = cell | {"verdict": "exception"}, cell | {"verdict": "success", "t": 1}
    out = tmp_path / "rows.jsonl"
    out.write_text(bt._dump_row(failed) + "\n" + bt._dump_row(retried) + "\n")
    assert bt.push_horn_rows(NEMO.key, URI, out=out)
    assert bt.count_horn_duplicates(NEMO.key, URI, [failed, retried]) == 1, "only the failed row has a covering row"
    assert bt.count_horn_duplicates(NEMO.key, URI, [retried]) == 0


def _ramp_run(mantle, tmp_path, monkeypatch, sleep, reps=1, **kw):
    """Run the 8 cells of one theory per replicate with each cell holding for ``sleep`` seconds.

    Returns the rows, the (cells in flight, seconds since the ramp started) seen as each cell
    began, and the elapsed seconds of the whole run.
    """
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    sweep, run_cell = bt.load_sweep(), bt.load_sweep().run_cell
    clock, started, lock, inflight, seen = bt._ramp_clock, [], threading.Lock(), [0], []

    def watched_clock():
        now = clock()
        started.append(now)
        return now

    def slow_cell(*args):
        with lock:
            inflight[0] += 1
            seen.append((inflight[0], clock() - started[0] if started else 0.0))  # no ramp, no start time
        try:
            time.sleep(sleep)
            return run_cell(*args)
        finally:
            with lock:
                inflight[0] -= 1

    monkeypatch.setattr(sweep, "run_cell", slow_cell)
    monkeypatch.setattr(bt, "_ramp_clock", watched_clock)
    begun = time.monotonic()
    rows = _horn_run(NEMO, rung, tmp_path / "rows.jsonl", reps=reps, **kw)
    return rows, seen, time.monotonic() - begun


def test_horn_ramp_never_exceeds_the_current_limit_and_reaches_the_concurrency(mantle, tmp_path, monkeypatch):
    interval = 0.01 * 60  # ramp_minutes=0.01
    rows, seen, _ = _ramp_run(mantle, tmp_path, monkeypatch, sleep=0.25, reps=4, concurrency=8, ramp_start=2,
                              ramp_minutes=0.01)
    assert len(rows) == 32 == len(mantle.requests)
    for flying, elapsed in seen:
        assert flying <= min(8, 2 * 2 ** int(elapsed // interval)), (flying, elapsed)
    assert max(flying for flying, _ in seen) == 8, "the limit reaches the concurrency"
    assert max(flying for flying, elapsed in seen if elapsed < interval) == 2, "and starts at ramp_start"


def test_horn_without_a_ramp_starts_all_workers_at_once(mantle, tmp_path, monkeypatch):
    rows, seen, _ = _ramp_run(mantle, tmp_path, monkeypatch, sleep=0.25, concurrency=8)
    assert len(rows) == 8 and max(flying for flying, _ in seen) == 8


def test_horn_deadline_passing_while_cells_wait_for_the_ramp_leaves_them_unstarted(
    mantle, tmp_path, monkeypatch, capsys
):
    deadline = bt.utcnow() + timedelta(seconds=0.4)
    rows, seen, took = _ramp_run(mantle, tmp_path, monkeypatch, sleep=1.0, concurrency=4, ramp_start=1,
                                 ramp_minutes=30, deadline=deadline)
    assert len(rows) == 1 == len(mantle.requests) == len(seen), "only the cell that held the single slot ran"
    assert "7 of 8 cells left unstarted (deadline passed)" in capsys.readouterr().out
    assert took < 10, "the waiting cells gave up at the deadline, not at the next doubling in 30 minutes"


def test_horn_stop_flag_releases_cells_that_wait_for_the_ramp(mantle, tmp_path, monkeypatch):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    _reject_with_400(mantle, monkeypatch)
    begun = time.monotonic()
    with pytest.raises(bt.HornRunStopped, match="2 consecutive"):
        _horn_run(NEMO, rung, tmp_path / "rows.jsonl", concurrency=4, ramp_start=1, ramp_minutes=30,
                  max_consecutive_failures=2)
    assert 2 <= len(mantle.requests) <= 3, "one slot: a third cell may start before the stop flag is set"
    assert time.monotonic() - begun < 20, "the waiting cells did not wait out the 30-minute ramp"


@pytest.mark.parametrize("kw", [{"ramp_start": 9}, {"ramp_start": 0}, {"ramp_start": -1},
                                {"ramp_start": 2, "ramp_minutes": 0}, {"ramp_start": 2, "ramp_minutes": -1.0},
                                {"ramp_start": 2, "ramp_minutes": float("inf")}])
def test_horn_refuses_a_ramp_outside_one_to_the_concurrency(mantle, tmp_path, kw):
    rung = _proof_response(mantle, tmp_path, reasoning="plan")
    with pytest.raises(ValueError, match="ramp_"):
        _horn_run(NEMO, rung, tmp_path / "a.jsonl", concurrency=8, **kw)
    assert mantle.requests == [] and not (tmp_path / "a.jsonl").exists()


def test_horn_ramp_start_equal_to_the_concurrency_limits_nothing(mantle, tmp_path, monkeypatch):
    rows, seen, _ = _ramp_run(mantle, tmp_path, monkeypatch, sleep=0.2, concurrency=4, ramp_start=4,
                              ramp_minutes=30)
    assert len(rows) == 8 and max(flying for flying, _ in seen) == 4


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
