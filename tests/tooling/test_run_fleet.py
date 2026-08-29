"""Offline contract for the 21-lane scaling-study fleet supervisor.

Covers scripts/fleet/{run_fleet,fleet_status,run_shards}.py; no AWS is reached.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from smolbench.evals import Mark, Marks
from tests._paths import NOTEBOOKS, REPO_ROOT, SCRIPTS


def _load(path: Path, name: str):
    """Imports a script by path under a private module name, os.environ restored."""
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


@pytest.fixture(scope="module")
def fleet():
    return _load(SCRIPTS / "fleet" / "run_fleet.py", "_scaling_run_fleet")


@pytest.fixture(scope="module")
def status():
    return _load(SCRIPTS / "fleet" / "fleet_status.py", "_scaling_fleet_status")


@pytest.fixture(scope="module")
def shards():
    return _load(SCRIPTS / "fleet" / "run_shards.py", "_scaling_run_shards")


@pytest.mark.parametrize(
    "tier,members,types",
    [
        ("A", {"nemotron-3-nano-4b", "gemma-4-e2b", "ministral-3-3b"},
         "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge"),
        ("B", {"qwen3.5-27b", "nemotron-3-nano-30b-a3b", "gemma-4-12b", "gemma-4-31b",
               "glm-4.7-flash", "ministral-3-8b", "ministral-3-14b", "exaone-4.0-32b",
               "exaone-4.5-33b"},
         "g6e.12xlarge,g6e.24xlarge"),
        ("C", {"qwen3.5-122b-a10b", "qwen3.5-397b-a17b", "nemotron-3-super-120b-a12b",
               "glm-4.5-air", "k-exaone-236b-a23b"},
         "p5.48xlarge,p5e.48xlarge"),
        ("D", {"glm-4.7", "deepseek-v3.1", "deepseek-v4-pro", "deepseek-v4-flash"},
         "p6-b200.48xlarge"),
    ],
)
def test_tier_table(fleet, tier, members, types):
    assert {k for k, lane in fleet.LANES.items() if lane.tier == tier} == members
    assert fleet.TIER_INSTANCE_TYPES[tier] == types
    if tier == "D":
        assert fleet.TIER_REGIONS["D"] == "us-east-1,us-east-2,us-west-2"


_CREDS = {
    "AWS_PROFILE": "rengz",
    "AWS_ACCESS_KEY_ID": "AKIA-test",
    "AWS_SECRET_ACCESS_KEY": "secret",
    "AWS_SESSION_TOKEN": "token",
    "SMOLBENCH_RESULTS_S3": "s3://bucket",
    "SMOLBENCH_RESULTS_S3_REGION": "us-west-2",
}


def test_lane_env_is_exact(fleet):
    env = fleet.lane_env(fleet.LANES["gemma-4-e2b"], "induction",
                         base_env={**_CREDS, "IRRELEVANT": "dropped"})
    assert env == {
        **_CREDS,
        "INFERENCE_PROVIDER": "ec2",
        "EC2_EXPERIMENT_TAG": "scaling-gemma-4-e2b",
        "INDUCTION_STATE_FILE": ".ec2_state_scaling_gemma-4-e2b.json",
        "INDUCTION_MODELS": "gemma-4-e2b",
        "EC2_INSTANCE_TYPES": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge",
        "EC2_REGIONS": "us-east-1,us-east-2,us-west-2",
        "EC2_VLLM_IMAGE": "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7",
        "EC2_MAX_LIFETIME_MIN": "2160",
        "EC2_REQUEST_TIMEOUT_SECONDS": "3600",
    }


def test_lane_env_deduction_reattaches_to_the_induction_box(fleet):
    env = fleet.lane_env(fleet.LANES["glm-4.7"], "deduction", base_env={})
    assert env["LEAN_MODEL"] == "glm-4.7"
    assert env["LEAN_STATE_FILE"] == ".ec2_state_scaling_glm-4.7.json"
    assert env["INDUCTION_STATE_FILE"] == env["LEAN_STATE_FILE"]
    assert env["EC2_EXPERIMENT_TAG"] == "scaling-glm-4.7"


def test_lane_env_never_mutates_the_parent_environment(fleet):
    before = dict(os.environ)
    result = fleet.lane_env(fleet.LANES["deepseek-v4-pro"], "induction")
    assert dict(os.environ) == before
    assert result is not os.environ
    result["EC2_EXPERIMENT_TAG"] = "tampered"
    assert os.environ.get("EC2_EXPERIMENT_TAG") != "tampered"


def test_every_lane_gets_a_distinct_tag_and_state_file(fleet):
    tags = {fleet.lane_env(lane, "induction", base_env={})["EC2_EXPERIMENT_TAG"]
            for lane in fleet.LANES.values()}
    states = {fleet.lane_env(lane, "induction", base_env={})["INDUCTION_STATE_FILE"]
              for lane in fleet.LANES.values()}
    assert {k: l.tag for k, l in fleet.LANES.items()} == dict(fleet.run_study.MODELS)
    assert len(tags) == len(states) == 21
    assert all(t.startswith("scaling-") for t in tags)
    assert all(s.startswith(".ec2_state_scaling_") and s.endswith(".json") for s in states)


def test_lane_command(fleet):
    lane = fleet.LANES["gemma-4-12b"]
    python = str(REPO_ROOT / ".venv" / "bin" / "python")
    assert fleet.lane_command(lane, "induction") == [
        python, str(NOTEBOOKS / "induction" / "run_study.py")]
    assert fleet.lane_command(lane, "deduction") == [
        python, str(NOTEBOOKS / "deduction" / "run_study.py")]
    shutdown = fleet.lane_command(lane, "shutdown")
    assert shutdown[1] == "-c" and "shutdown_instance" in shutdown[2]


@pytest.mark.parametrize(
    "tail,instance_present,expected",
    [
        ("nothing interesting here\n", False, "reclaim"),
        ("botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n", True, "reclaim"),
        ("RuntimeError: endpoint unreachable after 10 connection failures\n", True, "reclaim"),
        ("Traceback (most recent call last):\n  KeyError: 'gemma-4-12b'\n", True, "crash"),
        ("", True, "crash"),
    ],
)
def test_classify_exit(fleet, tail, instance_present, expected):
    assert fleet.classify_exit(tail, instance_present) == expected


def test_is_serve_healthy(fleet):
    assert fleet.is_serve_healthy(
        "INFO:root:serve_model: 'gemma-4-e2b' is up at http://1.2.3.4:8000/v1")
    assert not fleet.is_serve_healthy("INFO:root:serve_model: requesting 'gemma-4-e2b' ...")


class _FakeStore:
    """Minimal ResultsStore stand-in keyed on info arm."""

    def __init__(self, marks_by_info):
        self._marks = marks_by_info

    def exists(self, addr) -> bool:
        return addr.info in self._marks

    def load_marks(self, addr):
        return self._marks[addr.info]


def _marks(pairs):
    return Marks(
        model="gemma-4-e2b",
        marks=tuple(
            Mark(query="q", answer=1, response=response, score=1, reasoning=reasoning)
            for reasoning, response in pairs
        ),
    )


_CHAIN = "Alright, let's tackle this problem step by step. " * 10


@pytest.mark.parametrize(
    "contents,expected",
    [
        ({}, None),
        ({"intens": [("let me count...", "1"), ("thinking", "1")]}, 1.0),
        ({"intens": [("thought", "1"), (None, "1"), ("", "1"), ("thought", "1")]}, 0.5),
        ({"intens": [("a", "1"), ("b", "1")], "extens": [(None, "1"), (None, "1")]}, 0.5),
        ({"intens": [(None, _CHAIN), (None, "1260")]}, 0.5),
    ],
)
def test_reasoning_fraction(fleet, contents, expected):
    store = _FakeStore({info: _marks(pairs) for info, pairs in contents.items()})
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == expected


class _FakeEc2Client:
    """Returns one canned describe_instances page per region."""

    def __init__(self, reservations):
        self._reservations = reservations
        self.calls: list = []

    def describe_instances(self, **kwargs):
        self.calls.append(kwargs)
        return {"Reservations": self._reservations}


def _instance(instance_id, tag, launched_hours_ago=2.0):
    return {
        "InstanceId": instance_id,
        "InstanceType": "p5e.48xlarge",
        "State": {"Name": "running"},
        "Placement": {"AvailabilityZone": "us-east-2b"},
        "LaunchTime": datetime.now(timezone.utc) - timedelta(hours=launched_hours_ago),
        "Tags": [{"Key": "smolbench:experiment", "Value": tag}],
    }


def test_fleet_rows_reads_every_region_and_filters_on_the_scaling_prefix(status):
    clients = {}

    def factory(region):
        client = _FakeEc2Client([{"Instances": [
            _instance("i-1", "scaling-glm-4.7"),
            _instance("i-theirs", "periodic-induction"),
        ]}])
        clients[region] = client
        return client

    rows = status.fleet_rows(
        regions=("us-east-1", "us-east-2", "us-west-2"), client_factory=factory)
    assert sorted(clients) == ["us-east-1", "us-east-2", "us-west-2"]
    assert len(rows) == 3
    assert {r["lane"] for r in rows} == {"glm-4.7"}
    assert {r["instance_id"] for r in rows} == {"i-1"}
    assert rows[0]["age_hours"] == pytest.approx(2.0, abs=0.05)
    call = clients["us-east-1"].calls[0]
    assert any(f["Name"] == "tag:smolbench:experiment" and f["Values"] == ["scaling-*"]
               for f in call["Filters"])
    assert any(f["Name"] == "instance-state-name"
               and sorted(f["Values"]) == ["pending", "running"]
               for f in call["Filters"])


def test_format_fleet_table(status):
    text = status.format_fleet_table([{
        "lane": "glm-4.7",
        "region": "us-east-2",
        "instance_id": "i-abc",
        "instance_type": "p5e.48xlarge",
        "availability_zone": "us-east-2b",
        "state": "running",
        "age_hours": 3.5,
    }])
    assert "glm-4.7" in text and "i-abc" in text and "p5e.48xlarge" in text
    assert status.format_fleet_table([]).strip() != ""


def _args(**overrides):
    base = dict(model="gemma-4-12b", count=3, force_rerun="1",
                types="g7.12xlarge", regions="us-east-2,us-west-2",
                request_timeout=10800, tag="scaling", no_shard=False,
                state_file="")
    base.update(overrides)
    return argparse.Namespace(**base)


def test_shard_env(shards, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIATEST")
    env = shards.shard_env(_args(), 1)
    assert env["INDUCTION_MODELS"] == "gemma-4-12b"
    assert env["INDUCTION_SHARD"] == "1/3"
    assert env["INDUCTION_FORCE_RERUN"] == "1"
    assert env["EC2_EXPERIMENT_TAG"] == "scaling"
    assert env["EC2_INSTANCE_TYPES"] == "g7.12xlarge"
    assert env["EC2_REQUEST_TIMEOUT_SECONDS"] == "10800"
    assert env["AWS_ACCESS_KEY_ID"] == "AKIATEST"

    no_shard = shards.shard_env(
        _args(no_shard=True, count=1, state_file=".ec2_state_x.json",
              force_rerun="0-11"), 0)
    assert "INDUCTION_SHARD" not in no_shard
    assert no_shard["INDUCTION_STATE_FILE"] == ".ec2_state_x.json"
    assert no_shard["INDUCTION_FORCE_RERUN"] == "0-11"


def test_state_file_for(shards):
    assert shards.state_file_for(_args(), 2).name == (
        ".ec2_state_induction-gemma-4-12b-s2of3.json")
    assert shards.state_file_for(
        _args(no_shard=True, count=1, state_file=".ec2_state_v4flash.json"), 0
    ).name == ".ec2_state_v4flash.json"
