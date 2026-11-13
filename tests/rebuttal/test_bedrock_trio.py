"""Offline tests for ``rebuttal/bedrock_trio.py`` against the shared OpenAI stub."""

import json
import os
from dataclasses import replace

import pytest
import yaml

from smolbench.deduction.horn import stats
from smolbench.deduction.horn.checker import designed_proof
from smolbench.deduction.horn.theory import Theory
from smolbench.induction import repro as induction_repro
from tests._paths import REPO_ROOT, load_by_path
from conftest import StubTokenizer, chat_completion

bt = load_by_path(REPO_ROOT / "rebuttal" / "bedrock_trio.py", "bedrock_trio_under_test")

GEMMA = bt.TRIO["gemma-4-31b"]
NEMO = bt.TRIO["nemotron-3-super-120b-a12b"]
DSV31 = replace(bt.TRIO["deepseek-v3.1"], bedrock_id="deepseek.v3-v1:0")
ROUTED_ENV = ("INFERENCE_PROVIDER", "AWS_INFERENCE_BASE_URL", "AWS_INFERENCE_BODY_MODEL")


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
    assert body["max_completion_tokens"] == min(model.max_tokens, 4096)
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
    with pytest.raises(LookupError, match="gemma"):
        bt.resolve_ids(listing[1:])
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
    assert data["server_config"]["extra_args"] == {"max_completion_tokens": 8192, "reasoning_effort": "high"}
    report = bt.induction_reasoning_report(tmp_path)
    assert all(v["unreasoned"] == 0 and v["marks"] == 9 for v in report.values())

    bt.run_induction(harness, DSV31, "us-east-1", {"reasoning_effort": "high"})
    assert len(mantle.requests) == 27, "a finished replicate must not be re-billed"


def test_horn_rows_score_and_load_through_stats(mantle, tmp_path):
    rung = bt.render_horn_rung(2, [100], rungs_dir=tmp_path / "rungs")
    theory = Theory.from_json((rung / "s0100" / "theory.json").read_text())
    mantle.default_response = _final("\n".join(designed_proof(theory)), reasoning="plan")
    out = tmp_path / "rows.jsonl"
    rows = bt.run_horn(NEMO, "us-east-1", {"reasoning_effort": "high"}, rung, [100], reps=1, out=out)
    assert sorted(r["arm"] for r in rows) == sorted(bt.HORN_ARMS)
    assert {r["verdict"] for r in rows} == {"success"}
    body = mantle.requests[-1]["body"]
    assert body["temperature"] == 0.7 and body["seed"] == 0 and body["reasoning_effort"] == "high"
    assert mantle.requests[-1]["path"] == "/v1/chat/completions"

    cells, dropped = stats.load_rows([out])
    assert not dropped and set(cells) == {("nemotron-3-super-120b-a12b", "m2")}
    assert bt.horn_breakdown([out])[("nemotron-3-super-120b-a12b", "lem")]["unreasoned"] == 0
    assert all(json.loads(l)["provider"] == "bedrock-mantle:us-east-1" for l in out.read_text().splitlines())

    assert bt.run_horn(NEMO, "us-east-1", {}, rung, [100], reps=1, out=out) == []
