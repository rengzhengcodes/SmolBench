"""Offline contract for scripts/fleet/{run_fleet,fleet_status,run_shards,fleet_teardown}.py.

No AWS: every client is a stub factory and no subprocess is ever launched.
"""

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


fleet, status, shards, teardown = (
    _load(s) for s in ("run_fleet", "fleet_status", "run_shards", "fleet_teardown"))
# The modules run_fleet.py was split into. Reached THROUGH their consumers,
# never re-`_load`ed: `_load` builds a fresh module object every call, so an
# independently loaded copy could never be the object the entry points actually
# share -- which is half of what these tests check. Same idiom as
# `status._config is shards._config is fleet._config` below.
laneenv = fleet._lane_env
sup = fleet._supervisor
policy = sup._policy
shard_mod = shards._shards

TIERS = {  # tier -> instance types, then that tier's lane keys
    "A": "g6e.4xlarge,g6e.8xlarge nemotron-3-nano-4b gemma-4-e2b ministral-3-3b",
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
    assert {k for k, lane in laneenv.LANES.items() if lane.tier == tier} == set(members)
    assert laneenv.TIER_INSTANCE_TYPES[tier] == types


def test_lane_env_and_commands():
    env = laneenv.lane_env(laneenv.LANES["gemma-4-e2b"], "induction",
                         base_env={**_CREDS, "IRRELEVANT": "dropped"})
    assert laneenv.TIER_REGIONS["D"] == "us-east-1,us-east-2,us-west-2"
    # EXACT equality, so a key added to lane_env has to be accounted for here.
    # Note what is NOT present: EC2_VLLM_IMAGE, which lane_env no longer sets
    # for a lane with no LANE_IMAGE_OVERRIDES entry (14-12) -- the lane's own
    # ec2.py resolves it, so a digest bump there cannot be overridden by a
    # stale copy in run_fleet.
    assert env == {
        **_CREDS, "INFERENCE_PROVIDER": "ec2", "EC2_EXPERIMENT_TAG": "scaling-gemma-4-e2b",
        "INDUCTION_STATE_FILE": ".ec2_state_scaling_gemma-4-e2b.json",
        "INDUCTION_MODELS": "gemma-4-e2b", "EC2_REGIONS": "us-east-1,us-east-2,us-west-2",
        "EC2_INSTANCE_TYPES": "g6e.4xlarge,g6e.8xlarge",
        "EC2_REQUIRE_GPU": "L40S:1", "EC2_MAX_PARALLEL_REQUESTS": "1",
        "EC2_MAX_LIFETIME_MIN": "2160", "EC2_REQUEST_TIMEOUT_SECONDS": "3600"}
    ded = laneenv.lane_env(laneenv.LANES["glm-4.7"], "deduction", base_env={})
    assert ded["LEAN_MODEL"] == "glm-4.7"
    # LEAN_STATE_FILE is gone: the deduction driver derives the identical path
    # itself, so the fleet no longer spells a second variable for it. The
    # equality is pinned against that driver in
    # `test_the_fleet_no_longer_manages_per_lane_state_files`.
    assert "LEAN_STATE_FILE" not in ded
    assert ded["INDUCTION_STATE_FILE"] == ".ec2_state_scaling_glm-4.7.json"
    assert ded["EC2_EXPERIMENT_TAG"] == "scaling-glm-4.7"
    before = dict(os.environ)
    result = laneenv.lane_env(laneenv.LANES["deepseek-v4-pro"], "induction")
    assert dict(os.environ) == before
    assert result is not os.environ
    result["EC2_EXPERIMENT_TAG"] = "tampered"
    assert os.environ.get("EC2_EXPERIMENT_TAG") != "tampered"
    envs = [laneenv.lane_env(lane, "induction", base_env={}) for lane in laneenv.LANES.values()]
    tags = {e["EC2_EXPERIMENT_TAG"] for e in envs}
    states = {e["INDUCTION_STATE_FILE"] for e in envs}
    assert {k: l.tag for k, l in laneenv.LANES.items()} == dict(laneenv.run_study.MODELS)
    assert len(tags) == len(states) == 21
    assert all(t.startswith("scaling-") for t in tags)
    assert all(s.startswith(".ec2_state_scaling_") and s.endswith(".json") for s in states)
    lane = laneenv.LANES["gemma-4-12b"]
    python = str(REPO_ROOT / ".venv" / "bin" / "python")
    assert laneenv.lane_command(lane, "induction") == [
        python, str(NOTEBOOKS / "induction" / "run_study.py")]
    assert laneenv.lane_command(lane, "deduction") == [
        python, str(NOTEBOOKS / "deduction" / "run_study.py")]
    shutdown = laneenv.lane_command(lane, "shutdown")
    assert shutdown[1] == "-c" and "shutdown_instance" in shutdown[2]
    assert sup.is_serve_healthy(
        "INFO:root:serve_model: 'gemma-4-e2b' is up at http://1.2.3.4:8000/v1")
    assert not sup.is_serve_healthy("INFO:root:serve_model: requesting 'gemma-4-e2b' ...")


@pytest.mark.parametrize(
    "tail,present,expected",
    [("nothing interesting here\n", False, "reclaim"),
     ("botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n", True, "reclaim"),
     ("RuntimeError: endpoint unreachable after 10 connection failures\n", True, "reclaim"),
     ("Traceback (most recent call last):\n  KeyError: 'gemma-4-12b'\n", True, "crash"),
     ("", True, "crash")],
)
def test_classify_exit(tail, present, expected):
    assert policy.classify_exit(tail, present) == expected


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
    assert sup.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == expected


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
            "regions": "us-east-2,us-west-2", "request_timeout": 10800,
            "tag": "induction-scaling", "allow_fleet_prefix": False,
            "no_shard": False, "state_file": "", **overrides})

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIATEST")
    assert shards.shard_env(_args(), 1).items() >= {
        "INDUCTION_MODELS": "gemma-4-12b", "INDUCTION_SHARD": "1/3",
        "INDUCTION_FORCE_RERUN": "1", "EC2_EXPERIMENT_TAG": "induction-scaling",
        "EC2_INSTANCE_TYPES": "g7.12xlarge", "EC2_REQUEST_TIMEOUT_SECONDS": "10800",
        "AWS_ACCESS_KEY_ID": "AKIATEST"}.items()
    solo = _args(no_shard=True, count=1, state_file=".ec2_state_x.json", force_rerun="0-11")
    no_shard = shards.shard_env(solo, 0)
    assert "INDUCTION_SHARD" not in no_shard
    assert no_shard["INDUCTION_STATE_FILE"] == ".ec2_state_x.json"
    assert no_shard["INDUCTION_FORCE_RERUN"] == "0-11"
    assert shards.state_file_for(_args(), 2).name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    assert shards.state_file_for(solo, 0).name == ".ec2_state_x.json"



# ---------------------------------------------------------------------------
# 14-07: the shard supervisor's tag namespace
# ---------------------------------------------------------------------------
def _shard_args(parser, *extra):
    return parser.parse_args(
        ["--model", "gemma-4-12b", "--count", "3", "--types", "g6e.12xlarge",
         "--regions", "us-east-2", *extra])


def test_shard_tag_defaults_outside_the_fleet_teardown_blast_radius():
    """--tag defaulted to "scaling", putting shard boxes inside fleet_teardown.

    The driver appends "-<model>-s<i>of<n>", so the tag that actually landed on
    the instance was "scaling-gemma-4-12b-s0of3": inside fleet_status's
    server-side "scaling-*" filter and therefore inside `fleet_teardown
    --terminate`'s only safety re-check, which would have killed live,
    hand-launched shard boxes.
    """
    parser = shards.build_parser()
    args = _shard_args(parser)
    assert args.tag == "induction-scaling"
    # The DERIVED per-shard tag, not the bare one, is what lands on the box.
    assert not f"{args.tag}-gemma-4-12b-s0of3".startswith(status.SCALING_TAG_PREFIX)
    shards.refuse_fleet_prefix_tag(parser, args)  # accepted: no raise

    # The old default is refused even though "scaling" does not itself start
    # with "scaling-" -- it is the suffixed form that matters.
    assert "scaling-gemma-4-12b-s0of3".startswith(status.SCALING_TAG_PREFIX)
    for bad in ("scaling", "scaling-gemma"):
        with pytest.raises(SystemExit):
            shards.refuse_fleet_prefix_tag(parser, _shard_args(parser, "--tag", bad))
        # ...and the escape hatch is explicit, not implicit.
        shards.refuse_fleet_prefix_tag(
            parser, _shard_args(parser, "--tag", bad, "--allow-fleet-prefix"))
    # A tag that merely shares a prefix-free stem is not over-matched.
    shards.refuse_fleet_prefix_tag(parser, _shard_args(parser, "--tag", "scalingful"))


def test_shard_state_files_are_named_apart_from_the_fleets():
    """run_shards owns its own state files, under a distinct naming scheme.

    Teardown no longer has a state-file glob to keep them out of -- it
    terminates by tag and deletes nothing (see
    `test_the_fleet_no_longer_manages_per_lane_state_files`) -- but the two
    schemes must still be distinct, so an operator reading a repo root can
    tell a shard box's record from a fleet lane's.
    """
    args = _shard_args(shards.build_parser())
    name = shards.state_file_for(args, 2).name
    assert name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    assert name != laneenv.LANES["gemma-4-12b"].state_file
    assert not name.startswith(".ec2_state_scaling_")


def test_regions_and_tag_prefix_are_declared_once():
    """14-15: fleet_status/run_shards/run_fleet read one _config, not three literals."""
    config = status._config
    assert config is shards._config is laneenv._config  # one object, not three copies
    assert status.SCALING_TAG_PREFIX == config.SCALING_TAG_PREFIX == "scaling-"
    assert status.STATUS_REGIONS == config.REGION_TUPLE
    assert config.REGION_TUPLE == tuple(config.DEFAULT_REGIONS.split(","))


# ---------------------------------------------------------------------------
# #46: _config is a VIEW on the committed study config, not a second copy
# ---------------------------------------------------------------------------
def test_fleet_config_is_read_from_the_committed_study_config():
    """The fleet vocabulary is study_config.toml's, not a literal in _config.py.

    Before #46 the tag prefix, the region list and the standalone tag were
    each typed out twice -- once in ``smolbench/evals/study_config.toml`` (read
    by ``providers/ec2.py`` and ``notebooks/induction/run_study.py``) and once
    in ``scripts/fleet/_config.py`` -- with nothing keeping the two spellings
    equal. Editing the TOML now moves the fleet with it.
    """
    from smolbench.evals.study_config import load_study_config, roster_keys, tag_for

    cfg = load_study_config().fleet
    config = laneenv._config
    assert config.REGION_TUPLE == cfg.regions
    assert config.SCALING_TAG_PREFIX == cfg.tag_prefix
    assert config.STANDALONE_TAG == cfg.standalone_tag
    # DEFAULT_REGIONS is the comma-joined RENDERING of the tuple (the shape an
    # EC2_REGIONS environment value takes), derived from it rather than
    # declared beside it.
    assert config.DEFAULT_REGIONS == ",".join(cfg.regions)
    # The roster reaches the fleet from the same file...
    assert config.ROSTER_KEYS == roster_keys()
    assert config.ROSTER_TAGS == {key: tag_for(key) for key in roster_keys()}
    # ...and is what the lane table is actually built from, so a rung added to
    # the TOML cannot be missing here.
    assert set(laneenv.LANES) == set(config.ROSTER_KEYS)
    assert {key: lane.tag for key, lane in laneenv.LANES.items()} == dict(config.ROSTER_TAGS)


def test_the_shard_tag_default_is_the_configs_standalone_tag():
    """run_shards' --tag default was a literal that had to agree with the config.

    ``notebooks/induction/run_study.py`` already defaults a standalone run's
    ``EC2_EXPERIMENT_TAG`` to ``[fleet].standalone_tag``; run_shards spelled
    the same string again, so the two could drift and a shard box would carry
    a tag no other tool expected.
    """
    from smolbench.evals.study_config import load_study_config

    default = shards.build_parser().get_default("tag")
    assert default == laneenv._config.STANDALONE_TAG
    assert default == load_study_config().fleet.standalone_tag
    # It must stay outside the fleet's blast radius -- that is WHY it is a
    # separate config key rather than a derivation of the tag prefix.
    assert not f"{default}-".startswith(laneenv._config.SCALING_TAG_PREFIX)


# ---------------------------------------------------------------------------
# 14-06 / 14-10 / 14-12: the per-lane environment is what makes a lane reproducible
# ---------------------------------------------------------------------------
def test_a_tier_hunt_list_cannot_change_derived_tp_mid_lane():
    """14-06: the pin is a DETERMINISM specifier, so assert the mechanism.

    tier A used to hunt g6e.4xlarge,g6e.8xlarge,g6e.12xlarge -- 1, 1 and 4
    GPUs -- and ec2.derive_tp is gcd(attention heads, landed GPU count), so a
    capacity reclaim onto the fallback changed a lane's tp from 1 to 4 partway
    through, making rows before and after incomparable.
    """
    from smolbench.evals.providers import ec2

    assert laneenv.TIER_REQUIRE_GPU == {
        "A": "L40S:1", "B": "L40S:4", "C": ":8", "D": "B200:8"}
    for tier, types in laneenv.TIER_INSTANCE_TYPES.items():
        hunt = types.split(",")
        # One GPU count per tier is what the pin encodes...
        assert len({ec2._INSTANCE_GPU_COUNTS[t] for t in hunt}) == 1, tier
        # ...and the property that buys: every lane in the tier derives the
        # SAME tp on every type it could land on.
        for key, lane in laneenv.LANES.items():
            if lane.tier != tier:
                continue
            tps = {ec2.derive_tp(key, t, ec2.EC2_DEPLOY_SPECS[key]) for t in hunt}
            assert len(tps) == 1, (key, tier, tps)
    # Tier C's pin is count-only: p5 (H100) and p5e (H200) are different
    # silicon the study accepts at the same GPU count, so the name substring is
    # empty and only the count is enforced.
    assert laneenv.TIER_REQUIRE_GPU["C"].startswith(":")
    for lane in laneenv.LANES.values():
        env = laneenv.lane_env(lane, "induction", base_env={})
        assert env["EC2_REQUIRE_GPU"] == laneenv.TIER_REQUIRE_GPU[lane.tier]


def test_every_lane_override_key_is_a_roster_key_and_reaches_lane_env():
    """14-10: both override tables are .get() lookups no test covered.

    The reviewer typo'd all five keys and the suite still passed, so a lane
    silently losing its image pin or its timeout was invisible.
    """
    for table in (laneenv.LANE_IMAGE_OVERRIDES, laneenv.LANE_REQUEST_TIMEOUT_OVERRIDES):
        assert table, "an empty override table would make this test vacuous"
        assert set(table) <= set(laneenv.LANES), sorted(set(table) - set(laneenv.LANES))
    for key, image in laneenv.LANE_IMAGE_OVERRIDES.items():
        assert laneenv.lane_env(laneenv.LANES[key], "induction", base_env={})[
            "EC2_VLLM_IMAGE"] == image
    for key, timeout in laneenv.LANE_REQUEST_TIMEOUT_OVERRIDES.items():
        assert laneenv.lane_env(laneenv.LANES[key], "induction", base_env={})[
            "EC2_REQUEST_TIMEOUT_SECONDS"] == timeout
    # Every other lane takes the fleet default, recomputed for one request in
    # flight: the two 10800s entries are gone (see LANE_REQUEST_TIMEOUT_OVERRIDES).
    assert set(laneenv.LANE_REQUEST_TIMEOUT_OVERRIDES) == {"deepseek-v4-pro"}
    others = {laneenv.lane_env(lane, "induction", base_env={})["EC2_REQUEST_TIMEOUT_SECONDS"]
              for key, lane in laneenv.LANES.items()
              if key not in laneenv.LANE_REQUEST_TIMEOUT_OVERRIDES}
    assert others == {laneenv.REQUEST_TIMEOUT_SECONDS} == {"3600"}
    # ...and the client fan-out that invalidated the old arithmetic is pinned.
    assert all(laneenv.lane_env(lane, "induction", base_env={})["EC2_MAX_PARALLEL_REQUESTS"] == "1"
               for lane in laneenv.LANES.values())


def test_fleet_image_is_ec2s_own_value_with_a_three_step_precedence():
    """14-12: FLEET_IMAGE was a byte-identical COPY of ec2's default digest."""
    from smolbench.evals.providers import ec2

    assert laneenv.FLEET_IMAGE is ec2.EC2_VLLM_IMAGE
    plain, pinned = laneenv.LANES["gemma-4-e2b"], laneenv.LANES["deepseek-v4-pro"]
    # lowest: no key at all -> the lane's own ec2.py resolves the image.
    assert "EC2_VLLM_IMAGE" not in laneenv.lane_env(plain, "induction", base_env={})
    # middle: an operator export is carried through PASSTHROUGH_ENV...
    assert "EC2_VLLM_IMAGE" in laneenv.PASSTHROUGH_ENV
    assert laneenv.lane_env(plain, "induction", base_env={"EC2_VLLM_IMAGE": "op/img"})[
        "EC2_VLLM_IMAGE"] == "op/img"
    # highest: ...but a lane's own pin still wins over it.
    assert laneenv.lane_env(pinned, "induction", base_env={"EC2_VLLM_IMAGE": "op/img"})[
        "EC2_VLLM_IMAGE"] == laneenv.LANE_IMAGE_OVERRIDES["deepseek-v4-pro"]


# ---------------------------------------------------------------------------
# 14-02 / 14-03 / 14-11: the restart, gate and spool policies
#
# The reviewer's tripwire: disabling the CoT halt, setting MAX_CRASH_RELAUNCHES
# to 999 and deleting the tier B/C launch each left all 99 tooling tests green,
# because the file pinned only leaf predicates. These drive the policy
# functions themselves, with fake processes -- no subprocess, no AWS.
# ---------------------------------------------------------------------------
class _FakeProc:
    """subprocess.Popen stand-in: a fixed return code and a terminate() flag."""

    def __init__(self, rc):
        self.returncode = rc
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True


def _lane_run(key, phases=("induction",), rc=1):
    run = sup._LaneRun(lane=laneenv.LANES[key], phases=phases)
    run.proc = _FakeProc(rc)
    return run


def _recording_start_phase(launches, rc=1, log_text=None):
    def _start(run, log_dir):
        launches.append(run.lane.key)
        run.proc = _FakeProc(rc)
        if log_text is not None:
            (log_dir / f"{run.lane.key}.log").write_text(log_text)
    return _start


def test_presence_reads_an_empty_first_sweep_as_unknown_not_as_gone():
    """14-02: fleet_rows returns [] for an empty fleet AND for an all-region failure.

    Reading that as "every instance is gone" made classify_exit short-circuit
    to "reclaim" for every lane before RECLAIM_PATTERNS was ever consulted.
    """
    presence = sup._Presence()
    assert presence.lanes is None and presence.ever_seen is False
    presence.observe(set())
    assert presence.lanes is None, "an empty sweep before any lane was seen is UNKNOWN"
    presence.observe({"glm-4.7"})
    assert presence.lanes == {"glm-4.7"} and presence.ever_seen is True
    presence.observe(set())
    assert presence.lanes == set(), "once a lane has been seen, empty means empty"


def test_an_empty_sweep_no_longer_turns_a_crash_into_an_endless_reclaim(monkeypatch, tmp_path):
    """The simulated failure: 60 ticks of empty sweeps gave 60 relaunches, 0 crashes."""
    launches = []
    tail = "Traceback (most recent call last):\n  KeyError: 'gemma-4-e2b'\n"
    (tmp_path / "gemma-4-e2b.log").write_text(tail)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase(launches, log_text=tail))
    runs = {"gemma-4-e2b": _lane_run("gemma-4-e2b")}
    presence = sup._Presence()
    presence.observe(set())  # an empty sweep, nothing ever seen

    for _ in range(60):
        sup._apply_restart_policy(runs, tmp_path, presence)

    run = runs["gemma-4-e2b"]
    assert run.reclaim_relaunches == 0, "an unknown sweep must not read as a reclaim"
    assert run.halted and "MAX_CRASH_RELAUNCHES" in run.halt_reason
    assert len(launches) == policy.MAX_CRASH_RELAUNCHES == 2


def test_a_reclaim_backs_off_and_is_bounded(monkeypatch, tmp_path):
    """14-02: reclaims had unlimited retries and no backoff at all."""
    import time as _time

    launches, delays = [], []
    tail = "botocore ... InsufficientInstanceCapacity for p6-b200.48xlarge\n"
    (tmp_path / "glm-4.7.log").write_text(tail)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase(launches, log_text=tail))
    runs = {"glm-4.7": _lane_run("glm-4.7")}
    run = runs["glm-4.7"]
    presence = sup._Presence()
    presence.observe({"glm-4.7"})  # present: the verdict comes from the log tail

    for expected in range(1, policy.MAX_RECLAIM_RELAUNCHES + 2):
        sup._apply_restart_policy(runs, tmp_path, presence)
        if run.halted:
            break
        assert run.reclaim_relaunches == expected
        assert run.pending_relaunch_at is not None
        delays.append(run.pending_relaunch_at - _time.monotonic())
        # A lane inside its backoff window is not relaunched...
        before = len(launches)
        sup._apply_restart_policy(runs, tmp_path, presence)
        assert len(launches) == before, "relaunched before the backoff elapsed"
        # ...and is relaunched once the deadline passes.
        run.pending_relaunch_at = _time.monotonic() - 1
        sup._apply_restart_policy(runs, tmp_path, presence)
        assert len(launches) == before + 1 and run.pending_relaunch_at is None

    assert run.halted and str(policy.MAX_RECLAIM_RELAUNCHES) in run.halt_reason
    assert len(launches) == policy.MAX_RECLAIM_RELAUNCHES
    # Exponential, capped: 60, 120, 240, ... 1800, 1800, ...
    assert delays[0] == pytest.approx(policy.RECLAIM_BACKOFF_BASE_SECONDS, abs=2)
    assert delays[1] == pytest.approx(2 * policy.RECLAIM_BACKOFF_BASE_SECONDS, abs=2)
    assert max(delays) == pytest.approx(policy.RECLAIM_BACKOFF_CAP_SECONDS, abs=2)


def test_the_budget_alert_uses_a_clock_a_relaunch_cannot_reset(tmp_path, capsys):
    """14-02: _start_phase resets started_at, so the 2x-budget alert never fired."""
    run = _lane_run("gemma-4-e2b", rc=None)
    run.lane_started_at = sup.time.monotonic() - 3600 * 2 * laneenv.LANES[
        "gemma-4-e2b"].budget_hours - 60
    run.started_at = sup.time.monotonic()  # as a fresh relaunch would leave it
    (tmp_path / "gemma-4-e2b.log").write_text("still going\n")
    sup._monitor_tick({"gemma-4-e2b": run}, tmp_path, 2, sup._Presence())
    assert "exceeds 2x budget" in capsys.readouterr().out


def test_tail_log_finds_a_reclaim_marker_in_a_large_log(tmp_path):
    """14-03: _tail_log read the WHOLE file every tick, per lane.

    Under-reading is not neutral either: a RECLAIM_PATTERNS match outside the
    window silently becomes a CRASH, halting a lane that should have retried.
    """
    log = tmp_path / "k.log"
    log.write_text(("x" * 200 + "\n") * 5000
                   + "botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n")
    assert log.stat().st_size > 1_000_000
    tail = sup._tail_log(tmp_path, "k")
    assert policy.classify_exit(tail, True) == "reclaim"
    assert len(tail.splitlines()) <= 40
    assert len(tail) < log.stat().st_size // 4, "the whole file is still being read"
    assert sup._tail_log(tmp_path, "does-not-exist") == ""


def test_the_gate_scan_is_incremental_sticky_and_survives_truncation(tmp_path):
    """14-03: the gate line appears ONCE, early, then scrolls away.

    So the scan cannot simply become a bounded tail: it reads only what is new,
    latches when it finds the line, and rescans from 0 if the file shrinks.
    """
    run = sup._LaneRun(lane=laneenv.LANES["gemma-4-e2b"], phases=("induction",))
    log = tmp_path / "gemma-4-e2b.log"
    log.write_text("provisioning\n")
    assert sup._lane_gate_passed(run, tmp_path) is False

    # The healthy-serve line arrives split across two reads.
    with log.open("a") as fh:
        fh.write("INFO:root:serve_model: 'gemma-4-e2b' is up at ")
    assert sup._lane_gate_passed(run, tmp_path) is False, "a partial line must not match"
    with log.open("a") as fh:
        fh.write("http://1.2.3.4:8000/v1\n")
    assert sup._lane_gate_passed(run, tmp_path) is True
    assert run.gate_passed is True

    # Sticky: the line may scroll away entirely.
    log.write_text("gigabytes of later chatter\n")
    assert sup._lane_gate_passed(run, tmp_path) is True

    # Truncation before passing: the offset resets instead of reading nothing forever.
    other = sup._LaneRun(lane=laneenv.LANES["ministral-3-3b"], phases=("induction",))
    olog = tmp_path / "ministral-3-3b.log"
    olog.write_text("A" * 5000 + "\n")
    assert sup._lane_gate_passed(other, tmp_path) is False
    assert other.gate_scan_offset > 0
    olog.write_text("INFO:root:serve_model: 'ministral-3-3b' is up at http://1.2.3.4:8000/v1\n")
    assert sup._lane_gate_passed(other, tmp_path) is True


def test_a_failed_family_gate_halts_the_never_launched_lanes(monkeypatch, tmp_path, caplog, capsys):
    """14-03: gate failure left tier B/C at proc=None, so _all_terminal never became true.

    The supervisor then ticked forever with the tier-D boxes billing, never
    printing the closing report or the teardown reminder.
    """
    import logging

    monkeypatch.setattr(sup, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(sup, "LAUNCH_STAGGER_SECONDS", 0)
    launches = []
    crash = "Traceback (most recent call last):\n  KeyError: 'boom'\n"
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase(launches, log_text=crash))
    monkeypatch.setattr(sup, "_check_cot", lambda runs, *a, **k: None)

    # A bounded stub: without the fix _run_fleet never becomes all-terminal, and
    # an unbounded loop would HANG the suite rather than fail it. 200 ticks is
    # far more than the handful this scenario needs.
    ticks = {"n": 0}

    def _bounded_tick(runs, log_dir, tick, presence):
        ticks["n"] += 1
        if ticks["n"] > 200:
            raise AssertionError(
                "_run_fleet did not terminate: the never-launched lanes were "
                "left un-halted, so _all_terminal can never be true")

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick)

    lanes = {k: laneenv.LANES[k] for k in
             ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b",  # the gate lanes
              "qwen3.5-27b",                                            # tier B
              "glm-4.7")}                                               # tier D
    with caplog.at_level(logging.ERROR):
        sup._run_fleet(lanes, ("induction",), gate=True, log_dir=tmp_path,
                         phase_name="induction")  # must TERMINATE, not spin

    assert "qwen3.5-27b" not in launches, "tier B must not launch behind a failed gate"
    assert set(launches) >= set(sup.GATE_MODELS) | {"glm-4.7"}
    text = caplog.text
    assert "FAMILY GATE FAILED" in text
    assert "qwen3.5-27b" in text and "never launched" in text
    assert "fleet finished with" in text
    assert "fleet_teardown.py --terminate" in capsys.readouterr().out


def test_a_spool_failure_reaches_the_closing_report(monkeypatch, tmp_path, caplog):
    """14-11: the deleted copy uploaded without verification, then unlinked the rows.

    The driver's own spool_to_s3 verifies each upload with head_object before
    pruning; a failure must surface rather than being logged and forgotten,
    because this runs immediately before the supervisor shuts the box down.
    """
    import logging
    from types import SimpleNamespace as NS

    monkeypatch.setattr(sup, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(sup, "LAUNCH_STAGGER_SECONDS", 0)
    spool_ticks = {"n": 0}

    def _bounded_tick(runs, log_dir, tick, presence):
        spool_ticks["n"] += 1
        if spool_ticks["n"] > 200:
            raise AssertionError("_run_fleet did not terminate")

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick)
    monkeypatch.setattr(sup, "_check_cot", lambda runs, *a, **k: None)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase([], rc=0))
    # The lane exits 0, so _advance_finished would otherwise really shell out.
    shutdowns = []
    monkeypatch.setattr(sup, "subprocess",
                        NS(run=lambda cmd, **kw: shutdowns.append(cmd), Popen=None))

    def _boom(run_dir, key):
        # The deduction driver's module-scope guard raises SystemExit, which is
        # NOT an Exception -- an `except Exception` here would kill the fleet.
        raise SystemExit(f"EC2_EXPERIMENT_TAG mismatch for {key}")

    monkeypatch.setattr(sup, "_deduction_driver", lambda: NS(spool_to_s3=_boom))

    lanes = {"glm-4.7": laneenv.LANES["glm-4.7"]}
    with caplog.at_level(logging.ERROR):
        sup._run_fleet(lanes, ("deduction",), gate=False, log_dir=tmp_path,
                         phase_name="deduction")

    assert "glm-4.7" in caplog.text and "spool" in caplog.text.lower()
    assert "SystemExit" in caplog.text
    assert shutdowns, "the lane still completes and its box is still shut down"


def test_the_unverified_spool_copy_is_gone():
    """14-11: sync_deduction_spool duplicated the driver without its verification."""
    for module in (fleet, sup, laneenv):
        assert not hasattr(module, "sync_deduction_spool")
        assert not hasattr(module, "SPOOL_BUCKET") and not hasattr(module, "SPOOL_REGION")
    # Scanned across the WHOLE fleet family, not just run_fleet.py: the spool
    # code moved into supervisor.py when run_fleet.py was split, and a check
    # pinned to one filename would have gone quietly vacuous at that moment.
    for source in (SCRIPTS / "fleet").glob("*.py"):
        assert "smolbench-results-414266451290" not in source.read_text(), source.name


# ---------------------------------------------------------------------------
# 14-14 / #49: ONE restart vocabulary, ONE Shard, thin entry points
# ---------------------------------------------------------------------------
def test_both_supervisors_share_one_policy_module():
    """The same spot reclaim must not get two different answers.

    run_shards used to carry its own restart vocabulary -- a single
    ``CAPACITY_MARKER`` substring, ``FAST_CRASH_SECONDS``/``MAX_FAST_CRASHES``,
    and unlimited flat-backoff capacity retries -- beside run_fleet's eight
    ``RECLAIM_PATTERNS`` and capped exponential backoff. Both now read one
    module object, so there is nothing left to drift.
    """
    assert sup._policy is shards._policy is policy   # one object, not two copies
    for gone in ("CAPACITY_MARKER", "CAPACITY_BACKOFF_SECONDS",
                 "FAST_CRASH_SECONDS", "MAX_FAST_CRASHES", "RELAUNCH_BACKOFF_SECONDS"):
        assert not hasattr(shards, gone), gone
    for gone in ("RECLAIM_PATTERNS", "classify_exit", "MAX_CRASH_RELAUNCHES",
                 "MAX_RECLAIM_RELAUNCHES", "RECLAIM_BACKOFF_BASE_SECONDS",
                 "RECLAIM_BACKOFF_CAP_SECONDS"):
        assert not hasattr(fleet, gone), f"run_fleet still declares {gone}"
        assert hasattr(policy, gone), f"policy is missing {gone}"


def test_the_shared_patterns_cover_the_marker_they_replaced():
    """Deleting CAPACITY_MARKER only holds if RECLAIM_PATTERNS catches that line.

    Pinned against the line's PRODUCER (``providers/ec2.py``), not against the
    deleted literal, so this cannot pass by comparing the substitution to
    itself.
    """
    # The phrase alone, not the escaped newline that follows it in the raise:
    # this is a pin on the WORDING ec2.py produces, and how a source file spells
    # the line break after it is not part of that wording.
    produced = "No spot capacity for any (instance type, region) combination:"
    assert produced in (REPO_ROOT / "smolbench" / "evals" / "providers" / "ec2.py").read_text()
    rendered = f"ERROR:root:{produced}\n  g6e.12xlarge in us-east-2 -- no capacity"
    assert policy.classify_exit(rendered, True) == "reclaim"
    # ...and it is not a blanket "everything is a reclaim" verdict.
    assert policy.classify_exit("Traceback:\n  KeyError: 'x'\n", True) == "crash"


@pytest.mark.parametrize("verdict,attempt,action", [
    ("reclaim", 1, "relaunch"),
    ("reclaim", policy.MAX_RECLAIM_RELAUNCHES, "relaunch"),
    ("reclaim", policy.MAX_RECLAIM_RELAUNCHES + 1, "halt"),
    ("crash", 1, "relaunch"),
    ("crash", policy.MAX_CRASH_RELAUNCHES, "relaunch"),
    ("crash", policy.MAX_CRASH_RELAUNCHES + 1, "halt"),
])
def test_decide_relaunch_is_the_one_capped_backed_off_answer(verdict, attempt, action):
    """One decision function, so neither supervisor can answer differently."""
    decision = policy.decide_relaunch(verdict, attempt=attempt, rc=1)
    assert decision.action == action
    assert decision.reason.strip()
    if action == "halt":
        cap = ("MAX_RECLAIM_RELAUNCHES" if verdict == "reclaim"
               else "MAX_CRASH_RELAUNCHES")
        assert cap in decision.reason
    elif verdict == "crash":
        assert decision.delay_seconds == 0, "a crash relaunches immediately"
    else:
        assert decision.delay_seconds == policy.reclaim_backoff_seconds(attempt)


def test_the_reclaim_backoff_is_exponential_and_capped():
    """60, 120, 240, 480, 960, then 1800s forever -- the schedule run_fleet documents."""
    seq = [policy.reclaim_backoff_seconds(n)
           for n in range(1, policy.MAX_RECLAIM_RELAUNCHES + 1)]
    assert seq[:5] == [60, 120, 240, 480, 960]
    assert set(seq[5:]) == {policy.RECLAIM_BACKOFF_CAP_SECONDS} == {1800}
    assert seq == sorted(seq), "backoff must never shrink"


def test_shard_is_a_module_level_class_with_an_explicit_constructor():
    """14-14: `class Shard` lived inside main(), closing over `args`.

    Every field it read off that closure is now a constructor parameter, so a
    Shard can be built (and driven) without an argparse Namespace.
    """
    assert not hasattr(shards, "Shard"), "run_shards must import Shard, not redefine it"
    src = (SCRIPTS / "fleet" / "run_shards.py").read_text()
    assert "class Shard" not in src
    shard = shard_mod.Shard(
        index=2, selector="2/3", log=Path("/tmp/nowhere/gemma-4-12b-s2of3.log"),
        env={"INDUCTION_SHARD": "2/3"}, state_file=Path("/tmp/nowhere/.state.json"),
        python=Path("/py"), driver=Path("/drv.py"), cwd=Path("/repo"))
    assert (shard.index, shard.selector, shard.status) == (2, "2/3", "pending")
    assert shard.proc is None and shard.adopted_pid is None
    assert shard.launched_at == 0.0
    assert shard.crash_relaunches == 0 and shard.reclaim_relaunches == 0
    assert shard.env["INDUCTION_SHARD"] == "2/3"


def test_a_shard_reclaim_is_capped_and_backed_off_like_a_fleet_lane(monkeypatch, tmp_path):
    """A capacity-exhausted hunt used to retry FOREVER on a flat 300s sleep.

    It now takes the same bounded, exponentially backed-off path a fleet lane
    does, so a permanently dry pool stops costing relaunches instead of
    retrying for the whole run.
    """
    slept, launches = [], []
    monkeypatch.setattr(shards.time, "sleep", slept.append)
    monkeypatch.setattr(shards, "terminate_shard_box", lambda shard: None)

    log = tmp_path / "s0.log"
    log.write_text("ERROR:root:No spot capacity for any (instance type, region)\n")
    shard = shard_mod.Shard(
        index=0, selector="0/1", log=log, env={}, state_file=tmp_path / ".st.json",
        python=Path("/py"), driver=Path("/drv.py"), cwd=tmp_path)

    def _fake_launch():
        launches.append(len(launches))
        shard.proc = _FakeProc(1)
        shard.status = "running"
        shard.launched_at = 0.0

    monkeypatch.setattr(shard, "launch", _fake_launch)
    shard.proc = _FakeProc(1)
    shard.status = "running"

    assert shards.supervise([shard]) == 1
    assert shard.status == "halted"
    assert shard.reclaim_relaunches == policy.MAX_RECLAIM_RELAUNCHES + 1
    assert len(launches) == policy.MAX_RECLAIM_RELAUNCHES
    backoffs = [s for s in slept if s in
                {policy.reclaim_backoff_seconds(n)
                 for n in range(1, policy.MAX_RECLAIM_RELAUNCHES + 1)}]
    assert backoffs == [policy.reclaim_backoff_seconds(n)
                        for n in range(1, policy.MAX_RECLAIM_RELAUNCHES + 1)]


def test_a_completed_shard_still_terminates_its_own_box(monkeypatch, tmp_path):
    """The clean-exit path is what reclaims a direct run's box; keep it wired."""
    terminated = []
    monkeypatch.setattr(shards.time, "sleep", lambda _s: None)
    monkeypatch.setattr(shards, "terminate_shard_box", terminated.append)
    log = tmp_path / "s0.log"
    log.write_text("INDUCTION STUDY RUN COMPLETE\n")
    shard = shard_mod.Shard(
        index=0, selector=None, log=log, env={}, state_file=tmp_path / ".st.json",
        python=Path("/py"), driver=Path("/drv.py"), cwd=tmp_path)
    shard.proc = _FakeProc(0)
    shard.status = "running"

    assert shards.supervise([shard]) == 0
    assert shard.status == "done"
    assert terminated == [shard]


def test_run_fleet_is_a_thin_entry_point_over_the_split_modules():
    """14-14: run_fleet.py was 1,600+ lines of tables, lane env and supervisor loop.

    The split is only real if the entry point stops OWNING those things: it
    parses a command line, resolves the lane selection, and hands off. This
    pins the ownership, not a line count -- a symbol re-exported from
    run_fleet would let a future edit drift a second definition back in.
    """
    assert fleet._lane_env is laneenv and fleet._supervisor is sup
    # The tables and the lane environment belong to lane_env.py...
    for name in ("LANES", "Lane", "TIER_MEMBERS", "TIER_INSTANCE_TYPES",
                 "TIER_REQUIRE_GPU", "TIER_BUDGET_HOURS", "PASSTHROUGH_ENV",
                 "lane_env", "lane_command", "FLEET_IMAGE"):
        assert hasattr(laneenv, name), name
        assert not hasattr(fleet, name), f"run_fleet still owns {name}"
    # ...the loop and its policy hooks to supervisor.py...
    for name in ("_LaneRun", "_Presence", "_run_fleet", "_monitor_tick",
                 "_apply_restart_policy", "_advance_finished", "_check_cot",
                 "_start_phase", "_tail_log", "_lane_gate_passed", "GATE_MODELS",
                 "LOG_DIR", "reasoning_fraction", "preflight"):
        assert hasattr(sup, name), name
        assert not hasattr(fleet, name), f"run_fleet still owns {name}"
    # ...and run_fleet.py keeps only the command line.
    for name in ("main", "_build_arg_parser", "_selected_lanes", "_print_dry_run_plan"):
        assert hasattr(fleet, name), name
    body = (SCRIPTS / "fleet" / "run_fleet.py").read_text()
    assert len(body.splitlines()) < 300, "run_fleet.py is not a thin entry point"


def test_the_dry_run_plan_still_renders_every_lane_and_phase(capsys):
    """The CLI is thin, but it must still be the same CLI.

    --dry-run is the only offline path an operator can check the wiring with,
    so it is the one end-to-end assertion that survives the split.
    """
    assert fleet.main(["--dry-run", "--phase", "both", "--lanes", "glm-4.7"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "glm-4.7 (tier D" in out
    assert "EC2_EXPERIMENT_TAG=scaling-glm-4.7" in out
    assert "[induction] command:" in out and "[deduction] command:" in out
    assert "[shutdown] command" in out
    # ...and it launched nothing and asked AWS nothing to do it.
    assert "WIRING preview only" in out


# ---------------------------------------------------------------------------
# 14-13 / #48: one restartable supervisor state, and teardown by tag
# ---------------------------------------------------------------------------
def _persisted_runs():
    """Two lanes mid-flight: one backing off a reclaim, one already halted."""
    backing_off = sup._LaneRun(lane=laneenv.LANES["glm-4.7"], phases=("induction", "deduction"))
    backing_off.phase_index = 1
    backing_off.crash_relaunches = 1
    backing_off.reclaim_relaunches = 4
    backing_off.cot_checked = True
    backing_off.gate_passed = True
    backing_off.gate_scan_offset = 4096
    backing_off.lane_started_at = sup.time.monotonic() - 7200      # 2h ago
    backing_off.pending_relaunch_at = sup.time.monotonic() + 600   # 10m out
    halted = sup._LaneRun(lane=laneenv.LANES["gemma-4-e2b"], phases=("induction",))
    halted.halted = True
    halted.halt_reason = "crashed 3 time(s) (last rc=1); exceeded MAX_CRASH_RELAUNCHES=2"
    return {"glm-4.7": backing_off, "gemma-4-e2b": halted}


def test_the_supervisor_state_file_lives_under_the_log_dir(tmp_path):
    """One file, named once, beside the lane logs it describes."""
    runs = _persisted_runs()
    sup.save_fleet_state(runs, tmp_path)
    path = tmp_path / "fleet_state.json"
    assert path.is_file()
    assert sup.fleet_state_path(tmp_path) == path
    # Atomic rewrite: no temporary left behind for a reader to trip over.
    assert sorted(p.name for p in tmp_path.iterdir()) == ["fleet_state.json"]
    state = json.loads(path.read_text())
    assert sorted(state["lanes"]) == ["gemma-4-e2b", "glm-4.7"]
    # Lane identity is the tag's: fleet_status derives `lane` by stripping the
    # prefix off smolbench:experiment, and that is the key used here, so a
    # describe sweep and this file name the same lanes.
    for key in state["lanes"]:
        tag = laneenv.LANES[key].experiment_tag
        assert tag[len(status.SCALING_TAG_PREFIX):] == key


def test_a_resumed_supervisor_continues_with_the_persisted_counters(tmp_path, monkeypatch):
    """THE regression: every counter lived in memory, so a dead supervisor lost them.

    21 boxes kept billing with nobody advancing phases, and a replacement
    supervisor restarted every lane's crash and reclaim budget from zero.

    The reload runs under a SHIFTED ``time.monotonic``, because that is what a
    genuinely new process gets: monotonic's epoch is arbitrary per process, so
    a persisted monotonic deadline is meaningless on the other side of a
    restart. Only wall-clock survives, and the assertions below are on the
    lane's AGE and its REMAINING backoff -- both of which a naive
    monotonic-in, monotonic-out implementation gets wrong by exactly the shift.
    """
    sup.save_fleet_state(_persisted_runs(), tmp_path)

    real_monotonic = sup.time.monotonic
    shift = 10_000.0  # a fresh process's arbitrary monotonic origin
    monkeypatch.setattr(sup.time, "monotonic", lambda: real_monotonic() + shift)

    resumed = {key: sup._LaneRun(lane=laneenv.LANES[key], phases=phases)
               for key, phases in (("glm-4.7", ("induction", "deduction")),
                                   ("gemma-4-e2b", ("induction",)))}
    assert sup.load_fleet_state(resumed, tmp_path) == 2

    lane = resumed["glm-4.7"]
    assert lane.phase_index == 1 and lane.current_phase == "deduction"
    assert (lane.crash_relaunches, lane.reclaim_relaunches) == (1, 4)
    assert lane.cot_checked is True and lane.gate_passed is True
    assert lane.gate_scan_offset == 4096
    now = sup.time.monotonic()
    assert now - lane.lane_started_at == pytest.approx(7200, abs=5), \
        "the lane's AGE must survive the restart, so the 2x-budget alert still fires"
    assert lane.pending_relaunch_at - now == pytest.approx(600, abs=5), \
        "the REMAINING backoff must survive, not the raw monotonic deadline"

    halted = resumed["gemma-4-e2b"]
    assert halted.halted is True and "MAX_CRASH_RELAUNCHES" in halted.halt_reason
    # A process handle cannot be persisted, so a resumed lane holds none; the
    # driver's own resume-skip is what stops landed work being re-billed.
    assert lane.proc is None and halted.proc is None


def test_a_lane_absent_from_the_state_file_starts_clean(tmp_path, caplog):
    """A --lanes subset, or a lane added since the last run, must not fail the load."""
    import logging

    sup.save_fleet_state({"glm-4.7": _persisted_runs()["glm-4.7"]}, tmp_path)
    resumed = {key: sup._LaneRun(lane=laneenv.LANES[key], phases=("induction",))
               for key in ("glm-4.7", "qwen3.5-27b")}
    with caplog.at_level(logging.INFO):
        assert sup.load_fleet_state(resumed, tmp_path) == 1
    assert resumed["qwen3.5-27b"].reclaim_relaunches == 0
    assert resumed["qwen3.5-27b"].lane_started_at == 0.0
    assert "qwen3.5-27b" in caplog.text, "a lane starting clean must be reported"


def test_no_state_file_at_all_is_a_first_run_not_an_error(tmp_path):
    assert sup.load_fleet_state({"glm-4.7": _persisted_runs()["glm-4.7"]}, tmp_path) == 0


def test_a_corrupt_state_file_is_refused_loudly(tmp_path):
    """Silently starting from zero would re-bill 21 boxes' worth of relaunch budget."""
    (tmp_path / "fleet_state.json").write_text("{not json")
    runs = {"glm-4.7": sup._LaneRun(lane=laneenv.LANES["glm-4.7"], phases=("induction",))}
    with pytest.raises(ValueError) as excinfo:
        sup.load_fleet_state(runs, tmp_path)
    assert "fleet_state.json" in str(excinfo.value)


def test_the_state_file_is_rewritten_every_tick(monkeypatch, tmp_path):
    """A supervisor that only saved at exit would lose everything to the crash."""
    monkeypatch.setattr(sup, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(sup, "LAUNCH_STAGGER_SECONDS", 0)
    monkeypatch.setattr(sup, "_check_cot", lambda runs, *a, **k: None)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase([], rc=0))
    monkeypatch.setattr(sup, "subprocess", SimpleNamespace(run=lambda cmd, **kw: None, Popen=None))
    saves = []
    real_save = sup.save_fleet_state
    monkeypatch.setattr(sup, "save_fleet_state",
                        lambda runs, log_dir: (saves.append(sorted(runs)), real_save(runs, log_dir))[1])

    ticks = {"n": 0}

    def _bounded_tick(runs, log_dir, tick, presence):
        ticks["n"] += 1
        if ticks["n"] > 200:
            raise AssertionError("_run_fleet did not terminate")

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick)
    sup._run_fleet({"glm-4.7": laneenv.LANES["glm-4.7"]}, ("induction",),
                   gate=False, log_dir=tmp_path, phase_name="induction")
    assert saves, "the supervisor state was never written"
    assert (tmp_path / "fleet_state.json").is_file()
    assert json.loads((tmp_path / "fleet_state.json").read_text())["lanes"]["glm-4.7"]["done"]


def test_the_fleet_no_longer_manages_per_lane_state_files():
    """14-13: three state-file naming schemes coexisted and teardown globbed one.

    ec2's provisioning state file stays -- ec2 needs it, and the induction
    driver's own default is SHARED across lanes, so the supervisor still has to
    hand each lane a private one. What goes is the FLEET managing them:
    teardown no longer globs or deletes anything, and the deduction phase no
    longer gets a second, independently spelled state-file variable.
    """
    for gone in ("STATE_FILE_GLOB", "state_file_path", "delete_state_files"):
        assert not hasattr(teardown, gone), gone
    deduction = laneenv.lane_env(laneenv.LANES["glm-4.7"], "deduction", base_env={})
    assert "LEAN_STATE_FILE" not in deduction
    # ...because the deduction driver derives the IDENTICAL path itself. If
    # these two ever diverge the deduction phase provisions a SECOND box per
    # lane, silently and expensively, so pin it against the driver.
    driver = _deduction_driver_module()
    derived = driver.lane_env_defaults("glm-4.7", repo_root=Path("/anchor"))["EC2_STATE_FILE"]
    assert Path(derived).name == deduction["INDUCTION_STATE_FILE"]
    assert Path(derived).name == laneenv.LANES["glm-4.7"].state_file


def _deduction_driver_module():
    """Load notebooks/deduction/run_study.py under an environment snapshot.

    It calls ``load_dotenv`` and sets ``EC2_*`` defaults at module scope, which
    would otherwise leak into every later test in the session.
    """
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(
            "_deduction_driver_probe", NOTEBOOKS / "deduction" / "run_study.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


def test_teardown_terminates_by_tag_and_deletes_nothing(tmp_path, monkeypatch, capsys):
    """Termination is decided by the smolbench:experiment tag, and only by it."""
    calls = []
    rows = [
        {"region": "us-east-2", "instance_id": "i-ours", "lane": "glm-4.7",
         "experiment_tag": "scaling-glm-4.7"},
        {"region": "us-east-1", "instance_id": "i-theirs", "lane": "x",
         "experiment_tag": "induction-scaling-gemma-4-12b-s0of3"},
    ]

    def factory(region):
        return SimpleNamespace(
            terminate_instances=lambda InstanceIds: calls.append((region, InstanceIds)))

    terminated = teardown.terminate_fleet(rows, client_factory=factory)
    assert [r["instance_id"] for r in terminated] == ["i-ours"]
    assert calls == [("us-east-2", ["i-ours"])]

    monkeypatch.setattr(teardown, "_fleet_status", lambda: SimpleNamespace(
        fleet_rows=lambda: rows[:1],
        format_fleet_table=lambda r: "TABLE\n",
        SCALING_TAG_PREFIX=status.SCALING_TAG_PREFIX))
    monkeypatch.setattr(teardown, "terminate_fleet",
                        lambda r, **kw: r)
    assert teardown.main(["--terminate", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "Terminated 1 instance(s)" in out
    assert "state file" not in out, "the fleet no longer deletes state files"
