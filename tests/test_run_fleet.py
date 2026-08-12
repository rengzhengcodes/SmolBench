"""Offline contract tests for the 21-lane scaling-study fleet supervisor.

``scripts/run_fleet.py`` launches one subprocess per study model, each of
which provisions its own EC2 spot instance. Nothing here touches AWS: every
boto3 seam is either injected (``client_factory``) or unreached, and the
lane-environment builder is a PURE function precisely so it can be pinned
here rather than discovered on a live fleet.

The four failure modes these tests exist to catch:

* **Lane drift.** ``LANES`` is derived from a hand-written tier table; if a
  rung is added to ``EC2_DEPLOY_SPECS`` and not to a tier, that model
  silently never runs and the study quietly ships 20 of 21 ladders.
* **Env bleed.** Building a lane's environment by mutating ``os.environ``
  (the obvious implementation) makes lane N+1 inherit lane N's experiment
  tag and state file -- which means two lanes reattach to ONE instance and
  swap the served checkpoint out from under each other. The builder must be
  pure and its output exact.
* **Region pins.** ``p5e.48xlarge`` exists only in us-east-2 (a/b/c) and
  us-west-2c, so the three tier-D models must not be offered us-east-1.
* **Restart misclassification.** A spot reclaim deserves unlimited retries;
  a crash loop deserves 2 and then a halt. Getting the classifier backwards
  either abandons a study lane on a routine interruption or burns money
  relaunching a lane that will always crash.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.ec2 import EC2_DEPLOY_SPECS

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_FLEET_PATH = REPO_ROOT / "scripts" / "run_fleet.py"
FLEET_STATUS_PATH = REPO_ROOT / "scripts" / "fleet_status.py"

STUDY_KEYS = sorted(set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"})

EXPECTED_TIERS = {
    "A": {"nemotron-3-nano-4b", "gemma-4-e2b", "ministral-3-3b"},
    "B": {
        "qwen3.5-27b", "nemotron-3-nano-30b-a3b", "gemma-4-12b", "gemma-4-31b",
        "glm-4.7-flash", "ministral-3-8b", "ministral-3-14b", "exaone-4.0-32b",
        "exaone-4.5-33b",
    },
    "C": {
        "qwen3.5-122b-a10b", "qwen3.5-397b-a17b", "nemotron-3-super-120b-a12b",
        "glm-4.5-air", "k-exaone-236b-a23b", "deepseek-v4-flash",
    },
    "D": {"glm-4.7", "deepseek-v3.1", "deepseek-v4-pro"},
}


def _load(path: Path, name: str):
    """Imports a script by PATH under a private module name, env restored.

    ``run_fleet`` imports the induction driver, which calls
    ``load_dotenv(keys.env)`` at import time (it must -- ``ec2.py`` freezes
    its ``EC2_*`` constants at import). That would leak the study's real
    ``SMOLBENCH_RESULTS_S3`` into the pytest process and through into every
    later test, so the import is bracketed by a snapshot/restore of
    ``os.environ``. Loading by path (rather than putting ``scripts/`` on
    ``sys.path``) also keeps these module names from colliding with anything
    else in the repo.
    """
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
    return _load(RUN_FLEET_PATH, "_scaling_run_fleet")


@pytest.fixture(scope="module")
def status():
    return _load(FLEET_STATUS_PATH, "_scaling_fleet_status")


# ---------------------------------------------------------------------------
# Lane table <-> deploy-spec drift guard
# ---------------------------------------------------------------------------


def test_lanes_cover_exactly_the_study_specs(fleet):
    assert sorted(fleet.LANES) == STUDY_KEYS


def test_tier_membership_partitions_the_roster(fleet):
    seen: set[str] = set()
    for tier, expected in EXPECTED_TIERS.items():
        members = {key for key, lane in fleet.LANES.items() if lane.tier == tier}
        assert members == expected, tier
        assert not (members & seen), f"{tier} overlaps an earlier tier"
        seen |= members
    assert seen == set(STUDY_KEYS)


def test_lane_tags_come_from_the_study_driver(fleet):
    """The fleet must not re-declare the analysis tags -- run_study.py is the
    single source of truth, so a tag rename there propagates here."""
    assert {key: lane.tag for key, lane in fleet.LANES.items()} == dict(
        fleet.run_study.MODELS
    )


@pytest.mark.parametrize(
    "tier,types",
    [
        ("A", "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge"),
        ("B", "g6e.12xlarge,g6e.24xlarge"),
        ("C", "p5.48xlarge,p5e.48xlarge"),
        ("D", "p5e.48xlarge,p5en.48xlarge"),
    ],
)
def test_tier_instance_types(fleet, tier, types):
    assert fleet.TIER_INSTANCE_TYPES[tier] == types


# ---------------------------------------------------------------------------
# lane_env: pure, exact, no os.environ mutation
# ---------------------------------------------------------------------------


def test_lane_env_is_exact_for_an_induction_lane(fleet):
    env = fleet.lane_env(
        fleet.LANES["gemma-4-e2b"],
        "induction",
        base_env={"AWS_PROFILE": "rengz", "IRRELEVANT": "dropped"},
    )
    assert env == {
        "AWS_PROFILE": "rengz",
        "INFERENCE_PROVIDER": "ec2",
        "EC2_EXPERIMENT_TAG": "scaling-gemma-4-e2b",
        "INDUCTION_STATE_FILE": ".ec2_state_scaling_gemma-4-e2b.json",
        "INDUCTION_MODELS": "gemma-4-e2b",
        "EC2_INSTANCE_TYPES": "g6e.4xlarge,g6e.8xlarge,g6e.12xlarge",
        "EC2_REGIONS": "us-east-1,us-east-2,us-west-2",
        "EC2_VLLM_IMAGE": "vllm/vllm-openai:nightly",
        "EC2_MAX_LIFETIME_MIN": "2160",
        "EC2_REQUEST_TIMEOUT_SECONDS": "3600",
    }


def test_lane_env_tier_d_overrides_the_regions(fleet):
    """p5e exists ONLY in us-east-2 a/b/c and us-west-2c -- offering
    us-east-1 to a tier-D lane wastes a whole capacity hunt."""
    for key in EXPECTED_TIERS["D"]:
        env = fleet.lane_env(fleet.LANES[key], "induction", base_env={})
        assert env["EC2_REGIONS"] == "us-east-2,us-west-2"
        assert env["EC2_INSTANCE_TYPES"] == "p5e.48xlarge,p5en.48xlarge"


def test_lane_env_non_tier_d_uses_the_default_regions(fleet):
    for key in EXPECTED_TIERS["A"] | EXPECTED_TIERS["B"] | EXPECTED_TIERS["C"]:
        env = fleet.lane_env(fleet.LANES[key], "induction", base_env={})
        assert env["EC2_REGIONS"] == "us-east-1,us-east-2,us-west-2"


def test_lane_env_deduction_phase_adds_the_lean_variables(fleet):
    env = fleet.lane_env(fleet.LANES["glm-4.7"], "deduction", base_env={})
    assert env["LEAN_MODEL"] == "glm-4.7"
    assert env["LEAN_STATE_FILE"] == ".ec2_state_scaling_glm-4.7.json"
    # Same instance, same state file: the deduction driver reattaches to the
    # box the induction phase already provisioned rather than launching a
    # second one.
    assert env["INDUCTION_STATE_FILE"] == env["LEAN_STATE_FILE"]
    assert env["EC2_EXPERIMENT_TAG"] == "scaling-glm-4.7"


def test_lane_env_induction_phase_sets_no_lean_variables(fleet):
    env = fleet.lane_env(fleet.LANES["glm-4.7"], "induction", base_env={})
    assert not [k for k in env if k.startswith("LEAN_")]


def test_lane_env_never_mutates_the_parent_environment(fleet):
    before = dict(os.environ)
    result = fleet.lane_env(fleet.LANES["deepseek-v4-pro"], "induction")
    assert dict(os.environ) == before
    assert result is not os.environ
    # Mutating the returned dict must not reach back into os.environ either.
    result["EC2_EXPERIMENT_TAG"] = "tampered"
    assert os.environ.get("EC2_EXPERIMENT_TAG") != "tampered"


def test_lane_env_passes_through_credentials_and_results_store(fleet):
    base = {
        "AWS_PROFILE": "operator",
        "AWS_ACCESS_KEY_ID": "AKIA-test",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "AWS_SESSION_TOKEN": "token",
        "SMOLBENCH_RESULTS_S3": "s3://bucket",
        "SMOLBENCH_RESULTS_S3_REGION": "us-west-2",
    }
    env = fleet.lane_env(fleet.LANES["qwen3.5-27b"], "induction", base_env=base)
    for key, value in base.items():
        assert env[key] == value


def test_every_lane_gets_a_distinct_tag_and_state_file(fleet):
    tags = {fleet.lane_env(lane, "induction", base_env={})["EC2_EXPERIMENT_TAG"]
            for lane in fleet.LANES.values()}
    states = {fleet.lane_env(lane, "induction", base_env={})["INDUCTION_STATE_FILE"]
              for lane in fleet.LANES.values()}
    assert len(tags) == len(states) == 21
    assert all(t.startswith("scaling-") for t in tags)
    assert all(s.startswith(".ec2_state_scaling_") and s.endswith(".json") for s in states)


# ---------------------------------------------------------------------------
# Lane commands
# ---------------------------------------------------------------------------


def test_lane_command_induction(fleet):
    cmd = fleet.lane_command(fleet.LANES["gemma-4-12b"], "induction")
    assert cmd == [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        str(REPO_ROOT / "notebooks" / "induction" / "run_study.py"),
    ]


def test_lane_command_deduction(fleet):
    cmd = fleet.lane_command(fleet.LANES["gemma-4-12b"], "deduction")
    assert cmd == [
        str(REPO_ROOT / ".venv" / "bin" / "python"),
        str(REPO_ROOT / "notebooks" / "deduction" / "run_study.py"),
    ]


def test_lane_command_shutdown_calls_the_provider_teardown(fleet):
    cmd = fleet.lane_command(fleet.LANES["gemma-4-12b"], "shutdown")
    assert cmd[0] == str(REPO_ROOT / ".venv" / "bin" / "python")
    assert cmd[1] == "-c"
    assert "shutdown_instance" in cmd[2]


# ---------------------------------------------------------------------------
# Restart-policy classifier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tail,instance_present,expected",
    [
        # Instance gone under a live lane == the spot-reclaim signature.
        ("nothing interesting here\n", False, "reclaim"),
        # Capacity words, instance still visible (reclaim in progress).
        ("botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n", True, "reclaim"),
        ("us-east-2: spot quota exhausted for p5.48xlarge; skipping region\n", True, "reclaim"),
        ("RuntimeError: endpoint unreachable after 10 connection failures\n", True, "reclaim"),
        # A real crash: instance alive, traceback in the tail.
        ("Traceback (most recent call last):\n  KeyError: 'gemma-4-12b'\n", True, "crash"),
        ("SystemExit: INDUCTION_MODELS: unknown key(s)\n", True, "crash"),
        ("", True, "crash"),
    ],
)
def test_classify_exit(fleet, tail, instance_present, expected):
    assert fleet.classify_exit(tail, instance_present) == expected


def test_crash_relaunch_budget_is_two(fleet):
    assert fleet.MAX_CRASH_RELAUNCHES == 2


def test_tier_budget_hours(fleet):
    assert fleet.TIER_BUDGET_HOURS == {"A": 9, "B": 9, "C": 10, "D": 14}


def test_family_gate_is_the_three_cheap_tier_a_models(fleet):
    assert set(fleet.GATE_MODELS) == {
        "gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b"
    }
    assert all(fleet.LANES[k].tier == "A" for k in fleet.GATE_MODELS)


def test_serve_healthy_marker_matches_the_provider_log_line(fleet):
    """``ec2.serve_model`` logs ``serve_model: 'x' is up at http://...`` when
    the model is live; the gate watches lane logs for exactly that."""
    line = "INFO:root:serve_model: 'gemma-4-e2b' is up at http://1.2.3.4:8000/v1"
    assert fleet.is_serve_healthy(line)
    assert not fleet.is_serve_healthy("INFO:root:serve_model: requesting 'gemma-4-e2b' ...")


# ---------------------------------------------------------------------------
# CoT-ON assertion (marks carry a reasoning channel -- Mark.reasoning)
# ---------------------------------------------------------------------------


class _FakeStore:
    """Minimal ``ResultsStore`` stand-in keyed on (tag, info, seed)."""

    def __init__(self, marks_by_info):
        self._marks = marks_by_info

    def exists(self, addr) -> bool:
        return addr.info in self._marks

    def load_marks(self, addr):
        return self._marks[addr.info]


def _marks(reasonings):
    return Marks(
        model="gemma-4-e2b",
        marks=tuple(
            Mark(query="q", answer=1, response="1", score=1, reasoning=r)
            for r in reasonings
        ),
    )


def test_reasoning_fraction_returns_none_before_anything_lands(fleet):
    assert fleet.reasoning_fraction(_FakeStore({}), "gemma-4-e2b", "gemma4_e2b") is None


def test_reasoning_fraction_all_thinking(fleet):
    store = _FakeStore({"intens": _marks(["let me count...", "thinking"])})
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == 1.0


def test_reasoning_fraction_counts_empty_and_none_as_not_thinking(fleet):
    store = _FakeStore({"intens": _marks(["thought", None, "", "thought"])})
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == 0.5


def test_reasoning_fraction_pools_across_info_arms(fleet):
    store = _FakeStore(
        {"intens": _marks(["a", "b"]), "extens": _marks([None, None])}
    )
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == 0.5


def test_cot_threshold_separates_dead_toggle_from_variable_protocol(fleet):
    assert fleet.COT_MIN_FRACTION == 0.5


def test_reasoning_fraction_counts_long_content_as_reasoning(fleet):
    """A reasoning chain carried in ``response`` (soft-protocol models that
    reason without their think markup -- the live Ministral/EXAONE incident,
    2026-08-11) counts as thinking; a compliant bare integer does not."""
    chain = "Alright, let's tackle this problem step by step. " * 10  # >200 chars
    store = _FakeStore(
        {
            "intens": Marks(
                model="gemma-4-e2b",
                marks=(
                    Mark(query="q", answer=1, response=chain, score=1, reasoning=None),
                    Mark(query="q", answer=1, response="1260", score=1, reasoning=None),
                ),
            )
        }
    )
    assert fleet.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == 0.5


def test_content_reasoning_threshold_value(fleet):
    assert fleet.COT_CONTENT_REASONING_MIN_CHARS == 200


# ---------------------------------------------------------------------------
# fleet_status: read-only describe, boto3 injected
# ---------------------------------------------------------------------------


class _FakeEc2Client:
    """Returns one canned ``describe_instances`` page per region."""

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
        client = _FakeEc2Client([{"Instances": [_instance("i-1", "scaling-glm-4.7")]}])
        clients[region] = client
        return client

    rows = status.fleet_rows(
        regions=("us-east-1", "us-east-2", "us-west-2"), client_factory=factory
    )
    assert sorted(clients) == ["us-east-1", "us-east-2", "us-west-2"]
    assert len(rows) == 3
    assert {r["lane"] for r in rows} == {"glm-4.7"}
    assert {r["instance_id"] for r in rows} == {"i-1"}
    assert rows[0]["age_hours"] == pytest.approx(2.0, abs=0.05)
    # Read-only: the tag filter is server-side and no mutating call is made.
    call = clients["us-east-1"].calls[0]
    assert any(
        f["Name"] == "tag:smolbench:experiment" and f["Values"] == ["scaling-*"]
        for f in call["Filters"]
    )
    assert any(
        f["Name"] == "instance-state-name"
        and sorted(f["Values"]) == ["pending", "running"]
        for f in call["Filters"]
    )


def test_fleet_rows_ignores_instances_from_other_experiments(status):
    def factory(region):
        return _FakeEc2Client(
            [
                {
                    "Instances": [
                        _instance("i-mine", "scaling-ds-pro"),
                        _instance("i-theirs", "periodic-induction"),
                    ]
                }
            ]
        )

    rows = status.fleet_rows(regions=("us-west-2",), client_factory=factory)
    assert [r["instance_id"] for r in rows] == ["i-mine"]


def test_format_fleet_table_renders_without_boto3(status):
    rows = [
        {
            "lane": "glm-4.7",
            "region": "us-east-2",
            "instance_id": "i-abc",
            "instance_type": "p5e.48xlarge",
            "availability_zone": "us-east-2b",
            "state": "running",
            "age_hours": 3.5,
        }
    ]
    text = status.format_fleet_table(rows)
    assert "glm-4.7" in text and "i-abc" in text and "p5e.48xlarge" in text


def test_format_fleet_table_handles_an_empty_fleet(status):
    assert status.format_fleet_table([]).strip() != ""
