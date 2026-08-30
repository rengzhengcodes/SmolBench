"""Offline contract for scripts/fleet/{run_fleet,fleet_status,run_shards}.py; no AWS."""

import argparse
import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from smolbench.evals import Mark, Marks
from tests._paths import NOTEBOOKS, REPO_ROOT, SCRIPTS


def _load(stem):
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(
            f"_scaling_{stem}", SCRIPTS / "fleet" / f"{stem}.py")
        sys.modules[spec.name] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


fleet, status, shards = (_load(s) for s in ("run_fleet", "fleet_status", "run_shards"))

TIERS = {  # tier -> instance types, then that tier's lane keys
    "A": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge nemotron-3-nano-4b gemma-4-e2b ministral-3-3b",
    "B": "g6e.12xlarge,g6e.24xlarge qwen3.5-27b nemotron-3-nano-30b-a3b gemma-4-12b gemma-4-31b"
         " glm-4.7-flash ministral-3-8b ministral-3-14b exaone-4.0-32b exaone-4.5-33b",
    "C": "p5.48xlarge,p5e.48xlarge qwen3.5-122b-a10b qwen3.5-397b-a17b"
         " nemotron-3-super-120b-a12b glm-4.5-air k-exaone-236b-a23b",
    "D": "p6-b200.48xlarge glm-4.7 deepseek-v3.1 deepseek-v4-pro deepseek-v4-flash",
}
_CREDS = {"AWS_PROFILE": "rengz", "AWS_ACCESS_KEY_ID": "AKIA-test",
          "AWS_SECRET_ACCESS_KEY": "secret", "AWS_SESSION_TOKEN": "token",
          "SMOLBENCH_RESULTS_S3": "s3://bucket",
          "SMOLBENCH_RESULTS_S3_REGION": "us-west-2"}


@pytest.mark.parametrize("tier", TIERS)
def test_tier_table(tier):
    types, *members = TIERS[tier].split()
    assert {k for k, lane in fleet.LANES.items() if lane.tier == tier} == set(members)
    assert fleet.TIER_INSTANCE_TYPES[tier] == types


def test_lane_env_and_commands():
    env = fleet.lane_env(fleet.LANES["gemma-4-e2b"], "induction",
                         base_env={**_CREDS, "IRRELEVANT": "dropped"})
    assert fleet.TIER_REGIONS["D"] == "us-east-1,us-east-2,us-west-2"
    assert env == {
        **_CREDS, "INFERENCE_PROVIDER": "ec2", "EC2_EXPERIMENT_TAG": "scaling-gemma-4-e2b",
        "INDUCTION_STATE_FILE": ".ec2_state_scaling_gemma-4-e2b.json",
        "INDUCTION_MODELS": "gemma-4-e2b", "EC2_REGIONS": "us-east-1,us-east-2,us-west-2",
        "EC2_INSTANCE_TYPES": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge",
        "EC2_VLLM_IMAGE": "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7",
        "EC2_MAX_LIFETIME_MIN": "2160", "EC2_REQUEST_TIMEOUT_SECONDS": "3600"}
    ded = fleet.lane_env(fleet.LANES["glm-4.7"], "deduction", base_env={})
    assert ded["LEAN_MODEL"] == "glm-4.7"
    assert ded["LEAN_STATE_FILE"] == ".ec2_state_scaling_glm-4.7.json"
    assert ded["INDUCTION_STATE_FILE"] == ded["LEAN_STATE_FILE"]
    assert ded["EC2_EXPERIMENT_TAG"] == "scaling-glm-4.7"
    before = dict(os.environ)
    result = fleet.lane_env(fleet.LANES["deepseek-v4-pro"], "induction")
    assert dict(os.environ) == before
    assert result is not os.environ
    result["EC2_EXPERIMENT_TAG"] = "tampered"
    assert os.environ.get("EC2_EXPERIMENT_TAG") != "tampered"
    envs = [fleet.lane_env(lane, "induction", base_env={}) for lane in fleet.LANES.values()]
    tags = {e["EC2_EXPERIMENT_TAG"] for e in envs}
    states = {e["INDUCTION_STATE_FILE"] for e in envs}
    assert {k: l.tag for k, l in fleet.LANES.items()} == dict(fleet.run_study.MODELS)
    assert len(tags) == len(states) == 21
    assert all(t.startswith("scaling-") for t in tags)
    assert all(s.startswith(".ec2_state_scaling_") and s.endswith(".json") for s in states)
    lane = fleet.LANES["gemma-4-12b"]
    python = str(REPO_ROOT / ".venv" / "bin" / "python")
    assert fleet.lane_command(lane, "induction") == [
        python, str(NOTEBOOKS / "induction" / "run_study.py")]
    assert fleet.lane_command(lane, "deduction") == [
        python, str(NOTEBOOKS / "deduction" / "run_study.py")]
    shutdown = fleet.lane_command(lane, "shutdown")
    assert shutdown[1] == "-c" and "shutdown_instance" in shutdown[2]
    assert fleet.is_serve_healthy(
        "INFO:root:serve_model: 'gemma-4-e2b' is up at http://1.2.3.4:8000/v1")
    assert not fleet.is_serve_healthy("INFO:root:serve_model: requesting 'gemma-4-e2b' ...")


@pytest.mark.parametrize(
    "tail,present,expected",
    [("nothing interesting here\n", False, "reclaim"),
     ("botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n", True, "reclaim"),
     ("RuntimeError: endpoint unreachable after 10 connection failures\n", True, "reclaim"),
     ("Traceback (most recent call last):\n  KeyError: 'gemma-4-12b'\n", True, "crash"),
     ("", True, "crash")],
)
def test_classify_exit(tail, present, expected):
    assert fleet.classify_exit(tail, present) == expected


@pytest.mark.parametrize(
    "contents,expected",
    [({}, None),
     ({"intens": [("let me count...", "1"), ("thinking", "1")]}, 1.0),
     ({"intens": [("thought", "1"), (None, "1"), ("", "1"), ("thought", "1")]}, 0.5),
     ({"intens": [("a", "1"), ("b", "1")], "extens": [(None, "1"), (None, "1")]}, 0.5),
     ({"intens": [(None, "Alright, let's tackle this step by step. " * 12),
                  (None, "1260")]}, 0.5)],
)
def test_reasoning_fraction(contents, expected):
    landed = {info: Marks(model="gemma-4-e2b", marks=tuple(
        Mark(query="q", answer=1, response=resp, score=1, reasoning=trace)
        for trace, resp in pairs)) for info, pairs in contents.items()}
    store = SimpleNamespace(exists=lambda addr: addr.info in landed,
                            load_marks=lambda addr: landed[addr.info])
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == expected


def test_fleet_rows_reads_every_region_and_filters_on_the_scaling_prefix():
    calls = {}

    base = {"InstanceType": "p5e.48xlarge", "State": {"Name": "running"},
            "Placement": {"AvailabilityZone": "us-east-2b"},
            "LaunchTime": datetime.now(timezone.utc) - timedelta(hours=2.0)}
    page = {"Reservations": [{"Instances": [
        {**base, "InstanceId": i, "Tags": [{"Key": "smolbench:experiment", "Value": t}]}
        for i, t in [("i-1", "scaling-glm-4.7"), ("i-theirs", "periodic-induction")]]}]}

    def factory(region):
        def describe_instances(**kwargs):
            calls[region] = kwargs
            return page
        return SimpleNamespace(describe_instances=describe_instances)

    rows = status.fleet_rows(
        regions=("us-east-1", "us-east-2", "us-west-2"), client_factory=factory)
    assert sorted(calls) == ["us-east-1", "us-east-2", "us-west-2"]
    assert len(rows) == 3
    assert {r["lane"] for r in rows} == {"glm-4.7"}
    assert {r["instance_id"] for r in rows} == {"i-1"}
    assert rows[0]["age_hours"] == pytest.approx(2.0, abs=0.05)
    filters = calls["us-east-1"]["Filters"]
    assert any(f["Name"] == "tag:smolbench:experiment" and f["Values"] == ["scaling-*"]
               for f in filters)
    assert any(f["Name"] == "instance-state-name"
               and sorted(f["Values"]) == ["pending", "running"] for f in filters)
    text = status.format_fleet_table([{
        "lane": "glm-4.7", "region": "us-east-2", "instance_id": "i-abc", "state": "running",
        "instance_type": "p5e.48xlarge", "availability_zone": "us-east-2b", "age_hours": 3.5}])
    assert "glm-4.7" in text and "i-abc" in text and "p5e.48xlarge" in text
    assert status.format_fleet_table([]).strip() != ""


def test_shard_env_and_state_file(monkeypatch):
    def _args(**overrides):
        return argparse.Namespace(**{
            "model": "gemma-4-12b", "count": 3, "force_rerun": "1", "types": "g7.12xlarge",
            "regions": "us-east-2,us-west-2", "request_timeout": 10800, "tag": "scaling",
            "no_shard": False, "state_file": "", **overrides})

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIATEST")
    assert shards.shard_env(_args(), 1).items() >= {
        "INDUCTION_MODELS": "gemma-4-12b", "INDUCTION_SHARD": "1/3",
        "INDUCTION_FORCE_RERUN": "1", "EC2_EXPERIMENT_TAG": "scaling",
        "EC2_INSTANCE_TYPES": "g7.12xlarge", "EC2_REQUEST_TIMEOUT_SECONDS": "10800",
        "AWS_ACCESS_KEY_ID": "AKIATEST"}.items()
    solo = _args(no_shard=True, count=1, state_file=".ec2_state_x.json", force_rerun="0-11")
    no_shard = shards.shard_env(solo, 0)
    assert "INDUCTION_SHARD" not in no_shard
    assert no_shard["INDUCTION_STATE_FILE"] == ".ec2_state_x.json"
    assert no_shard["INDUCTION_FORCE_RERUN"] == "0-11"
    assert shards.state_file_for(_args(), 2).name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    assert shards.state_file_for(solo, 0).name == ".ec2_state_x.json"


def test_sync_deduction_spool_writes_under_the_new_prefix(monkeypatch, tmp_path):
    """The published pre-cutoff study lives under `deduction/runs`; never write there."""
    src = tmp_path / "notebooks" / "deduction" / "results" / "runs" / "scaling_glm-4.7"
    src.mkdir(parents=True)
    (src / "manifest.json").write_text("{}")
    (src / "all_rows.jsonl").write_text('{"kind": "cell"}\n')
    monkeypatch.setattr(fleet, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)
    uploads = []
    client = SimpleNamespace(upload_file=lambda f, b, k: uploads.append((b, k)))
    assert fleet.sync_deduction_spool(SimpleNamespace(key="glm-4.7"), client=client) == 2
    assert {k for _b, k in uploads} == {
        "deduction_postcutoff/runs/scaling_glm-4.7/manifest.json",
        "deduction_postcutoff/runs/scaling_glm-4.7/all_rows.jsonl"}
    assert all(b == fleet.SPOOL_BUCKET for b, _k in uploads)
