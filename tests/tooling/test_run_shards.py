"""Test scripts/run_shards.py, the direct-shard babysitter."""

from __future__ import annotations

import argparse
import importlib.util
import sys

from tests._paths import REPO_ROOT as REPO

_spec = importlib.util.spec_from_file_location("run_shards", REPO / "scripts" / "run_shards.py")
run_shards = importlib.util.module_from_spec(_spec)
sys.modules["run_shards"] = run_shards
_spec.loader.exec_module(run_shards)


def _args(**overrides):
    base = dict(model="gemma-4-12b", count=3, force_rerun="1",
                types="g7.12xlarge", regions="us-east-2,us-west-2",
                request_timeout=10800, tag="scaling", no_shard=False,
                state_file="")
    base.update(overrides)
    return argparse.Namespace(**base)


def test_shard_env_mirrors_the_hand_launch_recipe(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIATEST")
    env = run_shards.shard_env(_args(), 1)
    assert env["INDUCTION_MODELS"] == "gemma-4-12b"
    assert env["INDUCTION_SHARD"] == "1/3"
    assert env["INDUCTION_FORCE_RERUN"] == "1"
    assert env["EC2_EXPERIMENT_TAG"] == "scaling"
    assert env["EC2_INSTANCE_TYPES"] == "g7.12xlarge"
    assert env["EC2_REQUEST_TIMEOUT_SECONDS"] == "10800"
    # Base environment (credentials) passes through to the child.
    assert env["AWS_ACCESS_KEY_ID"] == "AKIATEST"


def test_shard_env_no_shard_omits_the_selector():
    args = _args(no_shard=True, count=1, state_file=".ec2_state_x.json",
                 force_rerun="0-11")
    env = run_shards.shard_env(args, 0)
    assert "INDUCTION_SHARD" not in env
    assert env["INDUCTION_STATE_FILE"] == ".ec2_state_x.json"
    assert env["INDUCTION_FORCE_RERUN"] == "0-11"


def test_state_file_matches_the_driver_lane_suffix():
    # Must agree with run_study's _LANE derivation or box termination and
    # reattach both silently break.
    path = run_shards.state_file_for(_args(), 2)
    assert path.name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    unsharded = run_shards.state_file_for(
        _args(no_shard=True, count=1, state_file=".ec2_state_v4flash.json"), 0)
    assert unsharded.name == ".ec2_state_v4flash.json"


def test_find_adoptable_returns_none_for_unknown_group():
    assert run_shards.find_adoptable("no-such-model", "0/99") is None
