"""Offline contract for scripts/fleet/{run_fleet,fleet_status,run_shards,fleet_teardown}.py.

No AWS: every client is a stub factory and no subprocess is ever launched.
"""

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


fleet, status, shards, teardown = (
    _load(s) for s in ("run_fleet", "fleet_status", "run_shards", "fleet_teardown"))

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
    assert {k for k, lane in fleet.LANES.items() if lane.tier == tier} == set(members)
    assert fleet.TIER_INSTANCE_TYPES[tier] == types


def test_lane_env_and_commands():
    env = fleet.lane_env(fleet.LANES["gemma-4-e2b"], "induction",
                         base_env={**_CREDS, "IRRELEVANT": "dropped"})
    assert fleet.TIER_REGIONS["D"] == "us-east-1,us-east-2,us-west-2"
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


def test_shard_state_files_stay_out_of_the_fleet_teardown_glob():
    """run_shards owns its state files; teardown's glob must not claim them."""
    import fnmatch

    args = _shard_args(shards.build_parser())
    name = shards.state_file_for(args, 2).name
    assert name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    assert not fnmatch.fnmatch(name, teardown.STATE_FILE_GLOB)
    # ...while a real fleet lane's file is exactly what that glob is for.
    assert fnmatch.fnmatch(fleet.LANES["glm-4.7"].state_file, teardown.STATE_FILE_GLOB)


def test_regions_and_tag_prefix_are_declared_once():
    """14-15: fleet_status/run_shards/run_fleet read one _config, not three literals."""
    config = status._config
    assert config is shards._config is fleet._config   # one object, not three copies
    assert status.SCALING_TAG_PREFIX == config.SCALING_TAG_PREFIX == "scaling-"
    assert status.STATUS_REGIONS == config.REGION_TUPLE
    assert config.REGION_TUPLE == tuple(config.DEFAULT_REGIONS.split(","))


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

    assert fleet.TIER_REQUIRE_GPU == {
        "A": "L40S:1", "B": "L40S:4", "C": ":8", "D": "B200:8"}
    for tier, types in fleet.TIER_INSTANCE_TYPES.items():
        hunt = types.split(",")
        # One GPU count per tier is what the pin encodes...
        assert len({ec2._INSTANCE_GPU_COUNTS[t] for t in hunt}) == 1, tier
        # ...and the property that buys: every lane in the tier derives the
        # SAME tp on every type it could land on.
        for key, lane in fleet.LANES.items():
            if lane.tier != tier:
                continue
            tps = {ec2.derive_tp(key, t, ec2.EC2_DEPLOY_SPECS[key]) for t in hunt}
            assert len(tps) == 1, (key, tier, tps)
    # Tier C's pin is count-only: p5 (H100) and p5e (H200) are different
    # silicon the study accepts at the same GPU count, so the name substring is
    # empty and only the count is enforced.
    assert fleet.TIER_REQUIRE_GPU["C"].startswith(":")
    for lane in fleet.LANES.values():
        env = fleet.lane_env(lane, "induction", base_env={})
        assert env["EC2_REQUIRE_GPU"] == fleet.TIER_REQUIRE_GPU[lane.tier]


def test_every_lane_override_key_is_a_roster_key_and_reaches_lane_env():
    """14-10: both override tables are .get() lookups no test covered.

    The reviewer typo'd all five keys and the suite still passed, so a lane
    silently losing its image pin or its timeout was invisible.
    """
    for table in (fleet.LANE_IMAGE_OVERRIDES, fleet.LANE_REQUEST_TIMEOUT_OVERRIDES):
        assert table, "an empty override table would make this test vacuous"
        assert set(table) <= set(fleet.LANES), sorted(set(table) - set(fleet.LANES))
    for key, image in fleet.LANE_IMAGE_OVERRIDES.items():
        assert fleet.lane_env(fleet.LANES[key], "induction", base_env={})[
            "EC2_VLLM_IMAGE"] == image
    for key, timeout in fleet.LANE_REQUEST_TIMEOUT_OVERRIDES.items():
        assert fleet.lane_env(fleet.LANES[key], "induction", base_env={})[
            "EC2_REQUEST_TIMEOUT_SECONDS"] == timeout
    # Every other lane takes the fleet default, recomputed for one request in
    # flight: the two 10800s entries are gone (see LANE_REQUEST_TIMEOUT_OVERRIDES).
    assert set(fleet.LANE_REQUEST_TIMEOUT_OVERRIDES) == {"deepseek-v4-pro"}
    others = {fleet.lane_env(lane, "induction", base_env={})["EC2_REQUEST_TIMEOUT_SECONDS"]
              for key, lane in fleet.LANES.items()
              if key not in fleet.LANE_REQUEST_TIMEOUT_OVERRIDES}
    assert others == {fleet.REQUEST_TIMEOUT_SECONDS} == {"3600"}
    # ...and the client fan-out that invalidated the old arithmetic is pinned.
    assert all(fleet.lane_env(lane, "induction", base_env={})["EC2_MAX_PARALLEL_REQUESTS"] == "1"
               for lane in fleet.LANES.values())


def test_fleet_image_is_ec2s_own_value_with_a_three_step_precedence():
    """14-12: FLEET_IMAGE was a byte-identical COPY of ec2's default digest."""
    from smolbench.evals.providers import ec2

    assert fleet.FLEET_IMAGE is ec2.EC2_VLLM_IMAGE
    plain, pinned = fleet.LANES["gemma-4-e2b"], fleet.LANES["deepseek-v4-pro"]
    # lowest: no key at all -> the lane's own ec2.py resolves the image.
    assert "EC2_VLLM_IMAGE" not in fleet.lane_env(plain, "induction", base_env={})
    # middle: an operator export is carried through PASSTHROUGH_ENV...
    assert "EC2_VLLM_IMAGE" in fleet.PASSTHROUGH_ENV
    assert fleet.lane_env(plain, "induction", base_env={"EC2_VLLM_IMAGE": "op/img"})[
        "EC2_VLLM_IMAGE"] == "op/img"
    # highest: ...but a lane's own pin still wins over it.
    assert fleet.lane_env(pinned, "induction", base_env={"EC2_VLLM_IMAGE": "op/img"})[
        "EC2_VLLM_IMAGE"] == fleet.LANE_IMAGE_OVERRIDES["deepseek-v4-pro"]
