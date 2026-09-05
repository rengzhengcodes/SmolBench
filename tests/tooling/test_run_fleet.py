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
    run = fleet._LaneRun(lane=fleet.LANES[key], phases=phases)
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
    presence = fleet._Presence()
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
    monkeypatch.setattr(fleet, "_start_phase", _recording_start_phase(launches, log_text=tail))
    runs = {"gemma-4-e2b": _lane_run("gemma-4-e2b")}
    presence = fleet._Presence()
    presence.observe(set())  # an empty sweep, nothing ever seen

    for _ in range(60):
        fleet._apply_restart_policy(runs, tmp_path, presence)

    run = runs["gemma-4-e2b"]
    assert run.reclaim_relaunches == 0, "an unknown sweep must not read as a reclaim"
    assert run.halted and "MAX_CRASH_RELAUNCHES" in run.halt_reason
    assert len(launches) == fleet.MAX_CRASH_RELAUNCHES == 2


def test_a_reclaim_backs_off_and_is_bounded(monkeypatch, tmp_path):
    """14-02: reclaims had unlimited retries and no backoff at all."""
    import time as _time

    launches, delays = [], []
    tail = "botocore ... InsufficientInstanceCapacity for p6-b200.48xlarge\n"
    (tmp_path / "glm-4.7.log").write_text(tail)
    monkeypatch.setattr(fleet, "_start_phase", _recording_start_phase(launches, log_text=tail))
    runs = {"glm-4.7": _lane_run("glm-4.7")}
    run = runs["glm-4.7"]
    presence = fleet._Presence()
    presence.observe({"glm-4.7"})  # present: the verdict comes from the log tail

    for expected in range(1, fleet.MAX_RECLAIM_RELAUNCHES + 2):
        fleet._apply_restart_policy(runs, tmp_path, presence)
        if run.halted:
            break
        assert run.reclaim_relaunches == expected
        assert run.pending_relaunch_at is not None
        delays.append(run.pending_relaunch_at - _time.monotonic())
        # A lane inside its backoff window is not relaunched...
        before = len(launches)
        fleet._apply_restart_policy(runs, tmp_path, presence)
        assert len(launches) == before, "relaunched before the backoff elapsed"
        # ...and is relaunched once the deadline passes.
        run.pending_relaunch_at = _time.monotonic() - 1
        fleet._apply_restart_policy(runs, tmp_path, presence)
        assert len(launches) == before + 1 and run.pending_relaunch_at is None

    assert run.halted and str(fleet.MAX_RECLAIM_RELAUNCHES) in run.halt_reason
    assert len(launches) == fleet.MAX_RECLAIM_RELAUNCHES
    # Exponential, capped: 60, 120, 240, ... 1800, 1800, ...
    assert delays[0] == pytest.approx(fleet.RECLAIM_BACKOFF_BASE_SECONDS, abs=2)
    assert delays[1] == pytest.approx(2 * fleet.RECLAIM_BACKOFF_BASE_SECONDS, abs=2)
    assert max(delays) == pytest.approx(fleet.RECLAIM_BACKOFF_CAP_SECONDS, abs=2)


def test_the_budget_alert_uses_a_clock_a_relaunch_cannot_reset(tmp_path, capsys):
    """14-02: _start_phase resets started_at, so the 2x-budget alert never fired."""
    run = _lane_run("gemma-4-e2b", rc=None)
    run.lane_started_at = fleet.time.monotonic() - 3600 * 2 * fleet.LANES[
        "gemma-4-e2b"].budget_hours - 60
    run.started_at = fleet.time.monotonic()  # as a fresh relaunch would leave it
    (tmp_path / "gemma-4-e2b.log").write_text("still going\n")
    fleet._monitor_tick({"gemma-4-e2b": run}, tmp_path, 2, fleet._Presence())
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
    tail = fleet._tail_log(tmp_path, "k")
    assert fleet.classify_exit(tail, True) == "reclaim"
    assert len(tail.splitlines()) <= 40
    assert len(tail) < log.stat().st_size // 4, "the whole file is still being read"
    assert fleet._tail_log(tmp_path, "does-not-exist") == ""


def test_the_gate_scan_is_incremental_sticky_and_survives_truncation(tmp_path):
    """14-03: the gate line appears ONCE, early, then scrolls away.

    So the scan cannot simply become a bounded tail: it reads only what is new,
    latches when it finds the line, and rescans from 0 if the file shrinks.
    """
    run = fleet._LaneRun(lane=fleet.LANES["gemma-4-e2b"], phases=("induction",))
    log = tmp_path / "gemma-4-e2b.log"
    log.write_text("provisioning\n")
    assert fleet._lane_gate_passed(run, tmp_path) is False

    # The healthy-serve line arrives split across two reads.
    with log.open("a") as fh:
        fh.write("INFO:root:serve_model: 'gemma-4-e2b' is up at ")
    assert fleet._lane_gate_passed(run, tmp_path) is False, "a partial line must not match"
    with log.open("a") as fh:
        fh.write("http://1.2.3.4:8000/v1\n")
    assert fleet._lane_gate_passed(run, tmp_path) is True
    assert run.gate_passed is True

    # Sticky: the line may scroll away entirely.
    log.write_text("gigabytes of later chatter\n")
    assert fleet._lane_gate_passed(run, tmp_path) is True

    # Truncation before passing: the offset resets instead of reading nothing forever.
    other = fleet._LaneRun(lane=fleet.LANES["ministral-3-3b"], phases=("induction",))
    olog = tmp_path / "ministral-3-3b.log"
    olog.write_text("A" * 5000 + "\n")
    assert fleet._lane_gate_passed(other, tmp_path) is False
    assert other.gate_scan_offset > 0
    olog.write_text("INFO:root:serve_model: 'ministral-3-3b' is up at http://1.2.3.4:8000/v1\n")
    assert fleet._lane_gate_passed(other, tmp_path) is True


def test_a_failed_family_gate_halts_the_never_launched_lanes(monkeypatch, tmp_path, caplog, capsys):
    """14-03: gate failure left tier B/C at proc=None, so _all_terminal never became true.

    The supervisor then ticked forever with the tier-D boxes billing, never
    printing the closing report or the teardown reminder.
    """
    import logging

    monkeypatch.setattr(fleet, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(fleet, "LAUNCH_STAGGER_SECONDS", 0)
    launches = []
    crash = "Traceback (most recent call last):\n  KeyError: 'boom'\n"
    monkeypatch.setattr(fleet, "_start_phase", _recording_start_phase(launches, log_text=crash))
    monkeypatch.setattr(fleet, "_check_cot", lambda runs, *a, **k: None)

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

    monkeypatch.setattr(fleet, "_monitor_tick", _bounded_tick)

    lanes = {k: fleet.LANES[k] for k in
             ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b",  # the gate lanes
              "qwen3.5-27b",                                            # tier B
              "glm-4.7")}                                               # tier D
    with caplog.at_level(logging.ERROR):
        fleet._run_fleet(lanes, ("induction",), gate=True, log_dir=tmp_path,
                         phase_name="induction")  # must TERMINATE, not spin

    assert "qwen3.5-27b" not in launches, "tier B must not launch behind a failed gate"
    assert set(launches) >= set(fleet.GATE_MODELS) | {"glm-4.7"}
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

    monkeypatch.setattr(fleet, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(fleet, "LAUNCH_STAGGER_SECONDS", 0)
    spool_ticks = {"n": 0}

    def _bounded_tick(runs, log_dir, tick, presence):
        spool_ticks["n"] += 1
        if spool_ticks["n"] > 200:
            raise AssertionError("_run_fleet did not terminate")

    monkeypatch.setattr(fleet, "_monitor_tick", _bounded_tick)
    monkeypatch.setattr(fleet, "_check_cot", lambda runs, *a, **k: None)
    monkeypatch.setattr(fleet, "_start_phase", _recording_start_phase([], rc=0))
    # The lane exits 0, so _advance_finished would otherwise really shell out.
    shutdowns = []
    monkeypatch.setattr(fleet, "subprocess",
                        NS(run=lambda cmd, **kw: shutdowns.append(cmd), Popen=None))

    def _boom(run_dir, key):
        # The deduction driver's module-scope guard raises SystemExit, which is
        # NOT an Exception -- an `except Exception` here would kill the fleet.
        raise SystemExit(f"EC2_EXPERIMENT_TAG mismatch for {key}")

    monkeypatch.setattr(fleet, "_deduction_driver", lambda: NS(spool_to_s3=_boom))

    lanes = {"glm-4.7": fleet.LANES["glm-4.7"]}
    with caplog.at_level(logging.ERROR):
        fleet._run_fleet(lanes, ("deduction",), gate=False, log_dir=tmp_path,
                         phase_name="deduction")

    assert "glm-4.7" in caplog.text and "spool" in caplog.text.lower()
    assert "SystemExit" in caplog.text
    assert shutdowns, "the lane still completes and its box is still shut down"


def test_the_unverified_spool_copy_is_gone():
    """14-11: sync_deduction_spool duplicated the driver without its verification."""
    assert not hasattr(fleet, "sync_deduction_spool")
    assert not hasattr(fleet, "SPOOL_BUCKET") and not hasattr(fleet, "SPOOL_REGION")
    source = (SCRIPTS / "fleet" / "run_fleet.py").read_text()
    assert "smolbench-results-414266451290" not in source
