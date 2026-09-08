"""Offline contract for scripts/fleet/{run_fleet,fleet_status,run_shards,fleet_teardown}.py.

No AWS: every client is a stub factory and no subprocess is ever launched.
"""

import argparse
import json
import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT
from tests._paths import NOTEBOOKS, REPO_ROOT, SCRIPTS, load_by_path


def _load(stem: str) -> ModuleType:
    return load_by_path(
        f"_scaling_{stem}", SCRIPTS / "fleet" / f"{stem}.py", snapshot_env=True)


fleet, status, shards, teardown = (
    _load(s) for s in ("run_fleet", "fleet_status", "run_shards", "fleet_teardown"))
# Reached through their consumers, never re-`_load`ed: a fresh `_load` call
# builds a new module object, which could never be the object the entry
# points actually share -- half of what these tests check.
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
def test_tier_table(tier: str) -> None:
    types, *members = TIERS[tier].split()
    assert {k for k, lane in laneenv.LANES.items() if lane.tier == tier} == set(members)
    assert laneenv.TIER_INSTANCE_TYPES[tier] == types


def test_lane_env_and_commands() -> None:
    env = laneenv.lane_env(laneenv.LANES["gemma-4-e2b"], "induction",
                         base_env={**_CREDS, "IRRELEVANT": "dropped"})
    assert laneenv.TIER_REGIONS["D"] == "us-east-1,us-east-2,us-west-2"
    # EXACT equality: any key lane_env adds must show up here. EC2_VLLM_IMAGE
    # is absent by design -- ec2.py resolves it itself so a digest bump there
    # can't be shadowed by a stale copy here.
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
    # itself, so the fleet doesn't need a second variable for it (pinned
    # against the driver in test_the_fleet_no_longer_manages_per_lane_state_files).
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
def test_classify_exit(tail: str, present: bool, expected: str) -> None:
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
def test_reasoning_fraction(
    contents: dict[str, list[tuple[str | None, str]]],
    expected: float | None,
) -> None:
    landed = {info: Marks(model="gemma-4-e2b", marks=tuple(
        Mark(query="q", answer=1, response=resp, score=1, reasoning=trace, compliance=COMPLIANT)
        for trace, resp in pairs)) for info, pairs in contents.items()}
    store = SimpleNamespace(exists=lambda addr: addr.info in landed,
                            load_marks=lambda addr: landed[addr.info])
    assert sup.reasoning_fraction(store, "gemma-4-e2b", "gemma4_e2b") == expected


def test_fleet_rows_reads_every_region_and_filters_on_the_scaling_prefix() -> None:
    calls = {}

    base = {"InstanceType": "p5e.48xlarge", "State": {"Name": "running"},
            "Placement": {"AvailabilityZone": "us-east-2b"},
            "LaunchTime": datetime.now(timezone.utc) - timedelta(hours=2.0)}
    page = {"Reservations": [{"Instances": [
        {**base, "InstanceId": i, "Tags": [{"Key": "smolbench:experiment", "Value": t}]}
        for i, t in [("i-1", "scaling-glm-4.7"), ("i-theirs", "periodic-induction")]]}]}

    def factory(region: str) -> Any:
        def describe_instances(**kwargs: Any) -> dict[str, Any]:
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


def test_shard_env_and_state_file(monkeypatch: pytest.MonkeyPatch) -> None:
    def _args(**overrides: Any) -> argparse.Namespace:
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
    name = shards.state_file_for(_args(), 2).name
    assert name == ".ec2_state_induction-gemma-4-12b-s2of3.json"
    assert name != laneenv.LANES["gemma-4-12b"].state_file
    assert not name.startswith(".ec2_state_scaling_")
    assert shards.state_file_for(solo, 0).name == ".ec2_state_x.json"



# ---------------------------------------------------------------------------
# the shard supervisor's tag namespace
# ---------------------------------------------------------------------------
def _shard_args(parser: argparse.ArgumentParser, *extra: str) -> argparse.Namespace:
    return parser.parse_args(
        ["--model", "gemma-4-12b", "--count", "3", "--types", "g6e.12xlarge",
         "--regions", "us-east-2", *extra])


def test_shard_tag_defaults_outside_the_fleet_teardown_blast_radius() -> None:
    """--tag "scaling" put shard boxes inside fleet_teardown's blast radius."""
    from smolbench.evals.study_config import load_study_config

    parser = shards.build_parser()
    args = _shard_args(parser)
    assert args.tag == laneenv._config.STANDALONE_TAG
    assert args.tag == load_study_config().fleet.standalone_tag == "induction-scaling"
    # The DERIVED per-shard tag, not the bare one, is what lands on the box.
    assert not f"{args.tag}-gemma-4-12b-s0of3".startswith(status._config.SCALING_TAG_PREFIX)
    shards.refuse_fleet_prefix_tag(parser, args)  # accepted: no raise

    # The old default is refused even though "scaling" itself isn't prefixed --
    # the suffixed form is what matters.
    assert "scaling-gemma-4-12b-s0of3".startswith(status._config.SCALING_TAG_PREFIX)
    for bad in ("scaling", "scaling-gemma"):
        with pytest.raises(SystemExit):
            shards.refuse_fleet_prefix_tag(parser, _shard_args(parser, "--tag", bad))
        # ...and the escape hatch is explicit, not implicit.
        shards.refuse_fleet_prefix_tag(
            parser, _shard_args(parser, "--tag", bad, "--allow-fleet-prefix"))
    # A tag that merely shares a prefix-free stem is not over-matched.
    shards.refuse_fleet_prefix_tag(parser, _shard_args(parser, "--tag", "scalingful"))


def test_regions_and_tag_prefix_are_declared_once() -> None:
    """fleet_status/run_shards/run_fleet read one _config, not three literals."""
    config = status._config
    assert config is shards._config is laneenv._config  # one object, not three copies
    assert config.SCALING_TAG_PREFIX == "scaling-"
    assert config.REGION_TUPLE == tuple(config.DEFAULT_REGIONS.split(","))


# ---------------------------------------------------------------------------
# _config is a VIEW on the committed study config, not a second copy
# ---------------------------------------------------------------------------
def test_fleet_config_is_read_from_the_committed_study_config() -> None:
    """The fleet vocabulary is study_config.toml's, not a copy in _config.py."""
    from smolbench.evals.study_config import load_study_config, roster_keys

    study = load_study_config()
    cfg = study.fleet
    config = laneenv._config
    assert config.REGION_TUPLE == cfg.regions
    assert config.SCALING_TAG_PREFIX == cfg.tag_prefix
    assert config.STANDALONE_TAG == cfg.standalone_tag
    # DEFAULT_REGIONS is the comma-joined rendering of the tuple (the shape an
    # EC2_REGIONS env value takes), derived rather than declared beside it.
    assert config.DEFAULT_REGIONS == ",".join(cfg.regions)
    # The roster reaches the fleet from the same file...
    assert config.ROSTER_KEYS == roster_keys()
    assert config.ROSTER_TAGS is study.roster.tags
    # ...and the lane table is built from it, so a rung added to the TOML
    # can't be missing here.
    assert set(laneenv.LANES) == set(config.ROSTER_KEYS)
    assert {key: lane.tag for key, lane in laneenv.LANES.items()} == dict(config.ROSTER_TAGS)


# ---------------------------------------------------------------------------
# the per-lane environment is what makes a lane reproducible
# ---------------------------------------------------------------------------
def test_a_tier_hunt_list_cannot_change_derived_tp_mid_lane() -> None:
    """A capacity reclaim onto a fallback type must not change a lane's tp."""
    from smolbench.evals.providers import ec2

    assert laneenv.TIER_REQUIRE_GPU == {
        "A": "L40S:1", "B": "L40S:4", "C": ":8", "D": "B200:8"}
    for tier, types in laneenv.TIER_INSTANCE_TYPES.items():
        hunt = types.split(",")
        # One GPU count per tier is what the pin encodes...
        assert len({ec2._INSTANCE_GPU_COUNTS[t] for t in hunt}) == 1, tier
        # ...and the property it buys: every lane in the tier derives the
        # same tp on every type it could land on.
        for key, lane in laneenv.LANES.items():
            if lane.tier != tier:
                continue
            tps = {ec2.derive_tp(key, t, ec2.EC2_DEPLOY_SPECS[key]) for t in hunt}
            assert len(tps) == 1, (key, tier, tps)
    # Tier C's pin is count-only: p5 (H100) and p5e (H200) are different
    # silicon the study accepts at the same GPU count, so only the count is
    # enforced.
    assert laneenv.TIER_REQUIRE_GPU["C"].startswith(":")
    for lane in laneenv.LANES.values():
        env = laneenv.lane_env(lane, "induction", base_env={})
        assert env["EC2_REQUIRE_GPU"] == laneenv.TIER_REQUIRE_GPU[lane.tier]


def test_every_lane_override_key_is_a_roster_key_and_reaches_lane_env() -> None:
    """Both override tables are .get() lookups: a typo'd key drops silently."""
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


def test_lane_image_has_a_three_step_precedence() -> None:
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
# the restart, gate and spool policies
#
# A tripwire found the old suite pinned only leaf predicates: disabling the
# CoT halt, raising MAX_CRASH_RELAUNCHES to 999, or deleting the tier B/C
# launch all still passed. These drive the policy functions directly, with
# fake processes -- no subprocess, no AWS.
# ---------------------------------------------------------------------------
class _FakeProc:
    """subprocess.Popen stand-in: a fixed return code and a terminate() flag."""

    def __init__(self, rc: int | None) -> None:
        self.returncode = rc
        self.terminated = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True


def _lane_run(key: str, phases: tuple[str, ...] = ("induction",), rc: int | None = 1) -> Any:
    run = sup._LaneRun(lane=laneenv.LANES[key], phases=phases)
    run.proc = _FakeProc(rc)
    return run


def _recording_start_phase(
    launches: list[str],
    rc: int | None = 1,
    log_text: str | None = None,
) -> Callable[[Any, Path], None]:
    def _start(run: Any, log_dir: Path) -> None:
        launches.append(run.lane.key)
        run.proc = _FakeProc(rc)
        if log_text is not None:
            (log_dir / f"{run.lane.key}.log").write_text(log_text)
    return _start


def _bounded_tick(counter: dict[str, int]) -> Callable[[Any, Path, int, Any], None]:
    """Build a monitor tick that fails if a fleet loop does not terminate.

    The bound turns a supervisor regression into a fast assertion instead of
    hanging the test process.

    Parameters
    ----------
    counter : dict[str, int]
        Mutable call count shared with the invoking test.

    Returns
    -------
    Callable[[Any, Path, int, Any], None]
        Monitor callback enforcing the test suite's 200-tick limit.

    Raises
    ------
    AssertionError
        Raised by the callback after 200 monitor ticks.
    """
    def _tick(runs: Any, log_dir: Path, tick: int, presence: Any) -> None:
        counter["n"] += 1
        if counter["n"] > 200:
            raise AssertionError("_run_fleet did not terminate")

    return _tick


def test_presence_reads_an_empty_first_sweep_as_unknown_not_as_gone() -> None:
    """An empty sweep must read as "unknown," not "gone", or classify_exit short-circuits every lane to "reclaim"."""
    presence = sup._Presence()
    assert presence.lanes is None and presence.ever_seen is False
    presence.observe(set())
    assert presence.lanes is None, "an empty sweep before any lane was seen is UNKNOWN"
    presence.observe({"glm-4.7"})
    assert presence.lanes == {"glm-4.7"} and presence.ever_seen is True
    presence.observe(set())
    assert presence.lanes == set(), "once a lane has been seen, empty means empty"


def test_an_empty_sweep_no_longer_turns_a_crash_into_an_endless_reclaim(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The simulated failure: 60 ticks of empty sweeps gave 60 relaunches, 0 crashes."""
    launches = []
    tail = "Traceback (most recent call last):\n  KeyError: 'gemma-4-e2b'\n"
    (tmp_path / "gemma-4-e2b.log").write_text(tail)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase(launches, log_text=tail))
    runs = {"gemma-4-e2b": _lane_run("gemma-4-e2b")}
    presence = sup._Presence()
    presence.observe(set())  # an empty sweep, nothing ever seen

    for _ in range(policy.MAX_CRASH_RELAUNCHES + 1):
        sup._apply_restart_policy(runs, tmp_path, presence)

    run = runs["gemma-4-e2b"]
    assert run.reclaim_relaunches == 0, "an unknown sweep must not read as a reclaim"
    assert run.halted and "MAX_CRASH_RELAUNCHES" in run.halt_reason
    assert len(launches) == policy.MAX_CRASH_RELAUNCHES == 2


def test_a_reclaim_backs_off_and_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Reclaims had unlimited retries and no backoff at all."""
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


def test_the_budget_alert_uses_a_clock_a_relaunch_cannot_reset(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The 2x-budget alert uses the lane clock, which relaunches never reset."""
    run = _lane_run("gemma-4-e2b", rc=None)
    run.lane_started_at = sup.time.monotonic() - 3600 * 2 * laneenv.LANES[
        "gemma-4-e2b"].budget_hours - 60
    (tmp_path / "gemma-4-e2b.log").write_text("still going\n")
    sup._monitor_tick({"gemma-4-e2b": run}, tmp_path, 2, sup._Presence())
    assert "exceeds 2x budget" in capsys.readouterr().out


def test_tail_log_finds_a_reclaim_marker_in_a_large_log(tmp_path: Path) -> None:
    """_tail_log used to read the whole file every tick; under-reading isn't neutral either -- a match outside the window becomes a false CRASH."""
    log = tmp_path / "k.log"
    log.write_text(("x" * 200 + "\n") * 5000
                   + "botocore ... InsufficientInstanceCapacity for p5e.48xlarge\n")
    assert log.stat().st_size > 1_000_000
    tail = sup._tail_log(tmp_path, "k")
    assert policy.classify_exit(tail, True) == "reclaim"
    assert len(tail.splitlines()) <= 40
    assert len(tail) < log.stat().st_size // 4, "the whole file is still being read"
    assert sup._tail_log(tmp_path, "does-not-exist") == ""


def test_the_gate_scan_is_incremental_sticky_and_survives_truncation(tmp_path: Path) -> None:
    """The gate line appears once, early, then scrolls away, so the scan can't be a bounded tail."""
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


def test_a_failed_family_gate_halts_the_never_launched_lanes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A gate failure used to leave tier B/C at proc=None, so _all_terminal never became true."""
    import logging

    monkeypatch.setattr(sup, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(sup, "LAUNCH_STAGGER_SECONDS", 0)
    launches = []
    crash = "Traceback (most recent call last):\n  KeyError: 'boom'\n"
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase(launches, log_text=crash))
    monkeypatch.setattr(sup, "_check_cot", lambda runs, *a, **k: None)

    # Bounded: without the fix _run_fleet never becomes all-terminal, and an
    # unbounded loop would hang the suite instead of failing it.
    ticks = {"n": 0}

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick(ticks))

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


def test_a_spool_failure_reaches_the_closing_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """spool_to_s3's failure must surface, not be logged and forgotten, right before the box shuts down."""
    import logging
    from types import SimpleNamespace as NS

    monkeypatch.setattr(sup, "MONITOR_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(sup, "LAUNCH_STAGGER_SECONDS", 0)
    spool_ticks = {"n": 0}

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick(spool_ticks))
    monkeypatch.setattr(sup, "_check_cot", lambda runs, *a, **k: None)
    monkeypatch.setattr(sup, "_start_phase", _recording_start_phase([], rc=0))
    # The lane exits 0, so _advance_finished would otherwise really shell out.
    shutdowns = []
    monkeypatch.setattr(sup, "subprocess",
                        NS(run=lambda cmd, **kw: shutdowns.append(cmd), Popen=None))

    def _boom(run_dir: Path, key: str) -> None:
        # Not an Exception: an `except Exception` here would swallow this and
        # kill the fleet.
        raise SystemExit(f"EC2_EXPERIMENT_TAG mismatch for {key}")

    monkeypatch.setattr(sup, "_deduction_driver", lambda: NS(spool_to_s3=_boom))

    lanes = {"glm-4.7": laneenv.LANES["glm-4.7"]}
    with caplog.at_level(logging.ERROR):
        sup._run_fleet(lanes, ("deduction",), gate=False, log_dir=tmp_path,
                         phase_name="deduction")

    assert "glm-4.7" in caplog.text and "spool" in caplog.text.lower()
    assert "SystemExit" in caplog.text
    assert shutdowns, "the lane still completes and its box is still shut down"


def test_no_fleet_script_names_the_results_bucket() -> None:
    """The bucket is study_config's to name, not a fleet script's."""
    banned = ("smolbench-results-414266451290",)
    for source in (SCRIPTS / "fleet").glob("*.py"):
        text = source.read_text()
        assert not [b for b in banned if b in text], source.name


def test_a_store_outage_leaves_the_lane_unchecked_instead_of_halting_it() -> None:
    """A store that cannot be built says nothing about the lane's CoT fraction."""
    calls = []

    def _boom() -> None:
        calls.append(1)
        raise RuntimeError("no credentials")

    runs = {"gemma-4-e2b": _lane_run("gemma-4-e2b")}
    sup._check_cot(runs, store_factory=_boom)
    run = runs["gemma-4-e2b"]
    assert calls and not run.halted and not run.cot_checked


# ---------------------------------------------------------------------------
# one restart vocabulary, one Shard, thin entry points
# ---------------------------------------------------------------------------
def test_both_supervisors_share_one_policy_module() -> None:
    """The same spot reclaim must not get two different answers."""
    assert sup._policy is shards._policy is policy   # one object, not two copies


def test_the_shared_patterns_cover_the_marker_they_replaced() -> None:
    """Deleting CAPACITY_MARKER only holds if RECLAIM_PATTERNS still catches the line, pinned against the producer, not the deleted literal."""
    # The phrase alone, not the trailing newline in the raise -- this pins the
    # wording ec2.py produces, not how the source spells the line break after it.
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
def test_decide_relaunch_is_the_one_capped_backed_off_answer(
    verdict: str,
    attempt: int,
    action: str,
) -> None:
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


def test_the_reclaim_backoff_is_exponential_and_capped() -> None:
    """60, 120, 240, 480, 960, then 1800s forever -- the schedule run_fleet documents."""
    seq = [policy.reclaim_backoff_seconds(n)
           for n in range(1, policy.MAX_RECLAIM_RELAUNCHES + 1)]
    assert seq[:5] == [60, 120, 240, 480, 960]
    assert set(seq[5:]) == {policy.RECLAIM_BACKOFF_CAP_SECONDS} == {1800}
    assert seq == sorted(seq), "backoff must never shrink"


def test_a_shard_reclaim_is_capped_and_backed_off_like_a_fleet_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A capacity-exhausted hunt used to retry forever on a flat 300s sleep."""
    slept, launches = [], []
    monkeypatch.setattr(shards.time, "sleep", slept.append)
    monkeypatch.setattr(shards, "terminate_shard_box", lambda shard: None)

    log = tmp_path / "s0.log"
    log.write_text("ERROR:root:No spot capacity for any (instance type, region)\n")
    shard = shard_mod.Shard(
        index=0, selector="0/1", log=log, env={}, state_file=tmp_path / ".st.json",
        python=Path("/py"), driver=Path("/drv.py"), cwd=tmp_path)

    def _fake_launch() -> None:
        launches.append(len(launches))
        shard.proc = _FakeProc(1)
        shard.status = "running"

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


def test_a_completed_shard_still_terminates_its_own_box(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
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


def test_run_fleet_is_a_thin_entry_point_over_the_split_modules() -> None:
    """run_fleet.py was 1,600+ lines of tables, lane env and supervisor loop; this pins ownership, not a line count."""
    assert fleet._lane_env is laneenv and fleet._supervisor is sup
    # The tables and the lane environment belong to lane_env.py...
    for name in ("LANES", "Lane", "TIER_MEMBERS", "TIER_INSTANCE_TYPES",
                 "TIER_REQUIRE_GPU", "TIER_BUDGET_HOURS", "PASSTHROUGH_ENV",
                 "lane_env", "lane_command"):
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


def test_the_dry_run_plan_still_renders_every_lane_and_phase(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI is thin, but --dry-run must still render the same plan end-to-end."""
    assert fleet.main(["--dry-run", "--phase", "both", "--lanes", "glm-4.7"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "glm-4.7 (tier D" in out
    assert "EC2_EXPERIMENT_TAG=scaling-glm-4.7" in out
    assert "[induction] command:" in out and "[deduction] command:" in out
    assert "[shutdown] command" in out
    # ...and it launched nothing and asked AWS nothing to do it.
    assert "WIRING preview only" in out


# ---------------------------------------------------------------------------
# one restartable supervisor state, and teardown by tag
# ---------------------------------------------------------------------------
def _persisted_runs() -> dict[str, Any]:
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


def test_the_supervisor_state_file_lives_under_the_log_dir(tmp_path: Path) -> None:
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
    # prefix off smolbench:experiment, so a describe sweep and this file agree.
    for key in state["lanes"]:
        tag = laneenv.LANES[key].experiment_tag
        assert tag[len(status._config.SCALING_TAG_PREFIX):] == key


def test_a_resumed_supervisor_continues_with_the_persisted_counters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Counters lived only in memory; the reload runs under a SHIFTED time.monotonic since a fresh process's epoch is arbitrary."""
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
    # A process handle can't be persisted, so a resumed lane holds none; the
    # driver's own resume-skip stops landed work being re-billed.
    assert lane.proc is None and halted.proc is None


def test_a_lane_absent_from_the_state_file_starts_clean(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
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


def test_no_state_file_at_all_is_a_first_run_not_an_error(tmp_path: Path) -> None:
    assert sup.load_fleet_state({"glm-4.7": _persisted_runs()["glm-4.7"]}, tmp_path) == 0


def test_a_corrupt_state_file_is_refused_loudly(tmp_path: Path) -> None:
    """Silently starting from zero would re-bill 21 boxes' worth of relaunch budget."""
    (tmp_path / "fleet_state.json").write_text("{not json")
    runs = {"glm-4.7": sup._LaneRun(lane=laneenv.LANES["glm-4.7"], phases=("induction",))}
    with pytest.raises(ValueError) as excinfo:
        sup.load_fleet_state(runs, tmp_path)
    assert "fleet_state.json" in str(excinfo.value)


def test_the_state_file_is_rewritten_every_tick(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
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

    monkeypatch.setattr(sup, "_monitor_tick", _bounded_tick(ticks))
    sup._run_fleet({"glm-4.7": laneenv.LANES["glm-4.7"]}, ("induction",),
                   gate=False, log_dir=tmp_path, phase_name="induction")
    assert saves, "the supervisor state was never written"
    assert (tmp_path / "fleet_state.json").is_file()
    assert json.loads((tmp_path / "fleet_state.json").read_text())["lanes"]["glm-4.7"]["done"]


def test_the_fleet_no_longer_manages_per_lane_state_files() -> None:
    """Each lane gets one state file, not two: the deduction phase no longer gets its own spelling."""
    deduction = laneenv.lane_env(laneenv.LANES["glm-4.7"], "deduction", base_env={})
    assert "LEAN_STATE_FILE" not in deduction
    # ...because the driver derives the identical path itself; if the two ever
    # diverge, deduction silently provisions a second box per lane.
    driver = load_by_path(
        "_deduction_driver_probe", NOTEBOOKS / "deduction" / "run_study.py",
        snapshot_env=True)
    derived = driver.lane_env_defaults("glm-4.7", repo_root=Path("/anchor"))["EC2_STATE_FILE"]
    assert Path(derived).name == deduction["INDUCTION_STATE_FILE"]
    assert Path(derived).name == laneenv.LANES["glm-4.7"].state_file

def test_teardown_terminates_by_tag_and_deletes_nothing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Termination is decided by the smolbench:experiment tag, and only by it."""
    calls = []
    rows = [
        {"region": "us-east-2", "instance_id": "i-ours", "lane": "glm-4.7",
         "experiment_tag": "scaling-glm-4.7"},
        {"region": "us-east-1", "instance_id": "i-theirs", "lane": "x",
         "experiment_tag": "induction-scaling-gemma-4-12b-s0of3"},
    ]

    def factory(region: str) -> Any:
        return SimpleNamespace(
            terminate_instances=lambda InstanceIds: calls.append((region, InstanceIds)))

    terminated = teardown.terminate_fleet(rows, client_factory=factory)
    assert [r["instance_id"] for r in terminated] == ["i-ours"]
    assert calls == [("us-east-2", ["i-ours"])]

    monkeypatch.setattr(teardown, "_fleet_status", lambda: SimpleNamespace(
        fleet_rows=lambda: rows[:1],
        format_fleet_table=lambda r: "TABLE\n"))
    monkeypatch.setattr(teardown, "terminate_fleet",
                        lambda r, **kw: r)
    assert teardown.main(["--terminate", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "Terminated 1 instance(s)" in out
