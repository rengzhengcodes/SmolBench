"""Offline unit tests for provision_spot_instance's pure-function helpers.

``_run_instances_kwargs`` and ``_instance_state`` do no AWS I/O of their own
(no boto3 client construction, no network) -- ``_run_instances_kwargs`` is a
plain dict builder, and ``_instance_state`` is exercised here with
``_describe_instance`` monkeypatched out, so neither test needs credentials
or a live instance. Compare tests/test_ec2_state.py (state-file round trips)
and tests/test_ec2_payloads.py (on-instance payload scripts) -- together the
three files cover ec2.py's offline-testable surface; the live AWS lifecycle
(actually calling provision_spot_instance/RunInstances) is exercised outside
this offline suite.
"""

import pytest

from smolbench.evals import ec2


# ---------------------------------------------------------------------------
# _run_instances_kwargs: pins the exact RunInstances kwargs dict
# ---------------------------------------------------------------------------
# Transcribed directly from the inline dict this helper was extracted from
# (provision_spot_instance's fresh-launch branch, pre-refactor) -- any
# accidental structural drift introduced by the extraction (a dropped key, a
# typo'd literal, wrong nesting) fails one of these tests. The two fields
# that are themselves env-configurable module constants (root-volume
# throughput/IOPS, the experiment tag) are asserted via ``ec2.EC2_*`` rather
# than hardcoded literals, so the pin stays valid under a non-default env
# (e.g. a CI run with EC2_EXPERIMENT_TAG overridden) while everything that is
# NOT env-configurable is still pinned as a literal.


def _base_kwargs(**overrides):
    """Builds _run_instances_kwargs with a fixed set of representative
    inputs, overridable per test so each test only states what it varies."""
    kwargs = dict(
        ami="ami-0123456789abcdef0",
        instance_type="p5e.48xlarge",
        subnet_id="subnet-abc123",
        group_id="sg-def456",
        root_device="/dev/sda1",
        volume_gb=300,
        user_data=b"#!/bin/bash\necho hi\n",
        key_name="",
        iam_profile=None,
    )
    kwargs.update(overrides)
    return ec2._run_instances_kwargs(**kwargs)


def test_run_instances_kwargs_matches_pinned_shape():
    kwargs = _base_kwargs()
    assert kwargs == {
        "ImageId": "ami-0123456789abcdef0",
        "InstanceType": "p5e.48xlarge",
        "MinCount": 1,
        "MaxCount": 1,
        "InstanceMarketOptions": {
            "MarketType": "spot",
            "SpotOptions": {
                "SpotInstanceType": "one-time",
                "InstanceInterruptionBehavior": "terminate",
            },
        },
        "InstanceInitiatedShutdownBehavior": "terminate",
        "NetworkInterfaces": [
            {
                "DeviceIndex": 0,
                "SubnetId": "subnet-abc123",
                "Groups": ["sg-def456"],
                "AssociatePublicIpAddress": True,
                "DeleteOnTermination": True,
            }
        ],
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 300,
                    "VolumeType": "gp3",
                    "Throughput": ec2.EC2_ROOT_VOLUME_THROUGHPUT,
                    "Iops": ec2.EC2_ROOT_VOLUME_IOPS,
                    "DeleteOnTermination": True,
                },
            }
        ],
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "smolbench:experiment", "Value": ec2.EC2_EXPERIMENT_TAG},
                    {"Key": "Name", "Value": f"smolbench-{ec2.EC2_EXPERIMENT_TAG}"},
                ],
            }
        ],
        "UserData": b"#!/bin/bash\necho hi\n",
    }


def test_run_instances_kwargs_omits_key_name_and_iam_profile_when_unset():
    """key_name="" and iam_profile=None (or "") must NOT add KeyName /
    IamInstanceProfile keys at all -- RunInstances rejects an empty KeyName,
    and a present-but-empty IamInstanceProfile would be a confusing no-op."""
    kwargs = _base_kwargs(key_name="", iam_profile=None)
    assert "KeyName" not in kwargs
    assert "IamInstanceProfile" not in kwargs

    kwargs = _base_kwargs(key_name="", iam_profile="")
    assert "KeyName" not in kwargs
    assert "IamInstanceProfile" not in kwargs


def test_run_instances_kwargs_includes_key_name_and_iam_profile_when_set():
    kwargs = _base_kwargs(key_name="my-debug-key", iam_profile="smolbench-ec2-role")
    assert kwargs["KeyName"] == "my-debug-key"
    assert kwargs["IamInstanceProfile"] == {"Name": "smolbench-ec2-role"}


def test_run_instances_kwargs_is_pure():
    """Same inputs -> equal (and independently-mutable) dicts, with no AWS
    calls -- guards against the helper picking up hidden global state."""
    first = _base_kwargs()
    second = _base_kwargs()
    assert first == second
    first["InstanceType"] = "mutated"
    assert second["InstanceType"] == "p5e.48xlarge"  # no shared mutable state


# ---------------------------------------------------------------------------
# _decode_user_data: gzip-or-plain-text decode, the read-side counterpart of
# payloads.pack_user_data. Pure (no AWS calls), so it is tested directly
# rather than through _recover_state_from_instance's DescribeInstanceAttribute
# call.
# ---------------------------------------------------------------------------
# User-data ships gzip-compressed since the 2026-08-18 determinism change
# (see payloads.pack_user_data), but a live instance launched before that
# change can outlive the code that provisioned it -- _recover_state_from_
# instance is exactly the best-effort "state file was lost, rebuild it from
# whatever is still running" path, so it must tolerate both formats rather
# than assume every live instance was launched by the current code.


def test_decode_user_data_gunzips_pack_user_data_output():
    """The normal, post-2026-08-18 case: gzip-compressed bytes decode back
    to the exact rendered script, matching pack_user_data's own round-trip
    contract (tests/test_ec2_payloads.py exercises that contract from the
    write side; this is the read side)."""
    from smolbench.evals.payloads import pack_user_data

    rendered = "#!/bin/bash\necho hi\n"
    assert ec2._decode_user_data(pack_user_data(rendered)) == rendered


def test_decode_user_data_falls_back_to_plain_text():
    """Backward compatibility: an instance launched before the determinism
    change shipped its user-data uncompressed. gzip.decompress raises
    BadGzipFile on non-gzip bytes (no gzip magic number), which must fall
    back to plain UTF-8 decoding rather than propagate."""
    rendered = "#!/bin/bash\necho hi\n"
    assert ec2._decode_user_data(rendered.encode()) == rendered


def test_decode_user_data_neither_format_raises():
    """Genuinely corrupt/foreign bytes (not gzip, not valid UTF-8) must
    raise rather than silently return garbage -- the caller,
    _recover_state_from_instance, nets this with its own best-effort
    ``except Exception`` and returns None (refuse reuse) instead of
    fabricating a state dict from noise."""
    with pytest.raises(UnicodeDecodeError):
        ec2._decode_user_data(b"\xff\xfe\x00\x01not-gzip-not-utf8")


# ---------------------------------------------------------------------------
# _instance_state: "absent" normalization over _describe_instance's Optional
# ---------------------------------------------------------------------------
# _describe_instance itself makes a real DescribeInstances call, so it is
# monkeypatched out here to keep this suite AWS-free; these tests exercise
# only _instance_state's own (instance or {}).get(...) extraction logic.


def test_instance_state_absent_when_describe_returns_none(monkeypatch):
    monkeypatch.setattr(ec2, "_describe_instance", lambda region, instance_id: None)
    assert ec2._instance_state("us-east-1", "i-doesnotmatter") == "absent"


def test_instance_state_absent_when_describe_returns_empty_dict(monkeypatch):
    """An empty (but non-None) describe result -- e.g. a reservation with no
    State key yet -- must fall back to "absent" too, not raise a KeyError."""
    monkeypatch.setattr(ec2, "_describe_instance", lambda region, instance_id: {})
    assert ec2._instance_state("us-east-1", "i-doesnotmatter") == "absent"


def test_instance_state_returns_name_when_present(monkeypatch):
    monkeypatch.setattr(
        ec2,
        "_describe_instance",
        lambda region, instance_id: {"State": {"Name": "running"}},
    )
    assert ec2._instance_state("us-east-1", "i-0123456789abcdef0") == "running"


def test_instance_state_passes_region_and_instance_id_through(monkeypatch):
    """The helper must forward its arguments to _describe_instance unchanged
    (not e.g. swap them) -- caught by asserting on the captured call args."""
    captured = {}

    def fake_describe(region, instance_id):
        captured["region"] = region
        captured["instance_id"] = instance_id
        return {"State": {"Name": "terminated"}}

    monkeypatch.setattr(ec2, "_describe_instance", fake_describe)
    result = ec2._instance_state("eu-west-1", "i-abc")
    assert result == "terminated"
    assert captured == {"region": "eu-west-1", "instance_id": "i-abc"}


# ---------------------------------------------------------------------------
# _ensure_bucket -- 403 disambiguation. HEAD -> 403 usually means the name is
# squatted in another account, but scoped credentials (the EC2-only operator
# key, which has no s3:*) get the same 403 on our own bucket. The account-id
# suffix in the bucket name is the tie-breaker, proven via sts (policy-free).
# ---------------------------------------------------------------------------


def _client_error(code):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": ""}}, "HeadBucket")


class _FakeS3:
    def __init__(self, head_error=None):
        self.head_error = head_error
        self.created = []

    def head_bucket(self, Bucket):
        if self.head_error is not None:
            raise self.head_error

    def create_bucket(self, **kwargs):
        self.created.append(kwargs)


class _FakeSts:
    def __init__(self, account):
        self.account = account

    def get_caller_identity(self):
        return {"Account": self.account}


def _patch_clients(monkeypatch, s3, sts):
    def fake_fresh_client(service, region):
        return {"s3": s3, "sts": sts}[service]

    monkeypatch.setattr(ec2._aws, "fresh_client", fake_fresh_client)


def test_ensure_bucket_403_with_account_suffix_proceeds(monkeypatch):
    s3 = _FakeS3(head_error=_client_error("403"))
    _patch_clients(monkeypatch, s3, _FakeSts("414266451290"))
    ec2._ensure_bucket("smolbench-model-cache-414266451290", "us-west-2")
    assert s3.created == []  # exists; never tries to create


def test_ensure_bucket_403_foreign_name_still_raises(monkeypatch):
    s3 = _FakeS3(head_error=_client_error("403"))
    _patch_clients(monkeypatch, s3, _FakeSts("999999999999"))
    with pytest.raises(RuntimeError, match="not accessible"):
        ec2._ensure_bucket("smolbench-model-cache-414266451290", "us-west-2")


def test_ensure_bucket_404_creates(monkeypatch):
    s3 = _FakeS3(head_error=_client_error("404"))
    _patch_clients(monkeypatch, s3, _FakeSts("414266451290"))
    ec2._ensure_bucket("some-new-bucket", "us-west-2")
    assert s3.created == [
        {
            "Bucket": "some-new-bucket",
            "CreateBucketConfiguration": {"LocationConstraint": "us-west-2"},
        }
    ]


# ---------------------------------------------------------------------------
# _run_instances_kwargs -- capacity-block launches. A purchased Capacity
# Block replaces the Spot market options (the API mandates MarketType=
# "capacity-block") and pins the instance to the reservation.
# ---------------------------------------------------------------------------


def test_run_instances_kwargs_capacity_block_swaps_market_and_pins_reservation():
    kwargs = _base_kwargs(capacity_reservation_id="cr-0123456789abcdef0")
    assert kwargs["InstanceMarketOptions"] == {"MarketType": "capacity-block"}
    assert kwargs["CapacityReservationSpecification"] == {
        "CapacityReservationTarget": {
            "CapacityReservationId": "cr-0123456789abcdef0"
        }
    }
    # everything else keeps the pinned spot-launch shape
    assert kwargs["InstanceInitiatedShutdownBehavior"] == "terminate"
    assert kwargs["MinCount"] == 1 and kwargs["MaxCount"] == 1


def test_run_instances_kwargs_no_reservation_keeps_spot_shape():
    kwargs = _base_kwargs()
    assert kwargs["InstanceMarketOptions"]["MarketType"] == "spot"
    assert "CapacityReservationSpecification" not in kwargs


# ---------------------------------------------------------------------------
# provision_spot_instance -- reservation authority over live instances. When
# EC2_CAPACITY_RESERVATION is set, a live box outside the block (e.g. a Spot
# instance from an earlier hunt) must be terminated and relaunched inside the
# block, never reused: the block is already paid for and the Spot box bills
# on top of it. All AWS-touching helpers are monkeypatched out.
# ---------------------------------------------------------------------------


def _patch_provision(monkeypatch, reattach=None, recover=None):
    calls = {"shutdown": 0, "launch_fresh": 0}
    monkeypatch.setattr(ec2, "_my_public_ip", lambda: "203.0.113.7")
    monkeypatch.setattr(ec2, "_reattach_existing_instance", lambda my_ip: reattach)
    monkeypatch.setattr(ec2, "_recover_tagged_instance", lambda my_ip: recover)

    def fake_shutdown(wait=True):
        calls["shutdown"] += 1
        # The guard must not block on full termination: p5-class teardown can
        # outlast botocore's 10-min instance_terminated waiter, and the block
        # launch does not depend on the dying box.
        assert wait is False

    def fake_launch_fresh(*args, **kwargs):
        calls["launch_fresh"] += 1
        return {"instance_id": "i-fresh", "capacity_reservation_id": "cr-block1"}

    monkeypatch.setattr(ec2, "shutdown_instance", fake_shutdown)
    monkeypatch.setattr(ec2, "_launch_fresh", fake_launch_fresh)
    return calls


_SPOT_STATE = {"instance_id": "i-spot", "region": "us-west-2"}
_BLOCK_STATE = {"instance_id": "i-block", "capacity_reservation_id": "cr-block1"}


def test_provision_no_reservation_env_reuses_live_instance(monkeypatch):
    monkeypatch.delenv("EC2_CAPACITY_RESERVATION", raising=False)
    calls = _patch_provision(monkeypatch, reattach=_SPOT_STATE)
    assert ec2.provision_spot_instance() is _SPOT_STATE
    assert calls == {"shutdown": 0, "launch_fresh": 0}


def test_provision_reservation_env_reuses_instance_already_in_block(monkeypatch):
    monkeypatch.setenv("EC2_CAPACITY_RESERVATION", "cr-block1")
    calls = _patch_provision(monkeypatch, reattach=_BLOCK_STATE)
    assert ec2.provision_spot_instance() is _BLOCK_STATE
    assert calls == {"shutdown": 0, "launch_fresh": 0}


def test_provision_reservation_env_terminates_off_block_instance(monkeypatch):
    monkeypatch.setenv("EC2_CAPACITY_RESERVATION", "cr-block1")
    calls = _patch_provision(monkeypatch, reattach=_SPOT_STATE)
    state = ec2.provision_spot_instance()
    assert calls == {"shutdown": 1, "launch_fresh": 1}
    assert state["capacity_reservation_id"] == "cr-block1"


def test_provision_reservation_env_terminates_off_block_recovered_instance(monkeypatch):
    """The tag-recovery branch (state file lost) is subject to the same
    authority: a recovered off-block box is torn down, not reused."""
    monkeypatch.setenv("EC2_CAPACITY_RESERVATION", "cr-block1")
    calls = _patch_provision(monkeypatch, reattach=None, recover=_SPOT_STATE)
    state = ec2.provision_spot_instance()
    assert calls == {"shutdown": 1, "launch_fresh": 1}
    assert state["instance_id"] == "i-fresh"


# ---------------------------------------------------------------------------
# shutdown_instance -- the instance_terminated waiter expiring is NOT a
# failure. TerminateInstances has already succeeded by then, so the box is
# dying regardless; p5-class teardown routinely outlasts botocore's 10-min
# waiter (seen live 2026-07-18, twice), and crashing stranded callers AFTER
# the only action that matters had been taken.
# ---------------------------------------------------------------------------


def test_shutdown_instance_survives_waiter_timeout(monkeypatch):
    from botocore.exceptions import WaiterError

    class _FakeWaiter:
        def wait(self, **kwargs):
            raise WaiterError("InstanceTerminated", "Max attempts exceeded", {})

    class _FakeEc2:
        def __init__(self):
            self.terminated = []

        def terminate_instances(self, InstanceIds):
            self.terminated.append(InstanceIds)

        def get_waiter(self, name):
            return _FakeWaiter()

    fake = _FakeEc2()
    cleared = []
    monkeypatch.setattr(
        ec2, "_load_state", lambda: {"instance_id": "i-slow", "region": "us-west-2"}
    )
    monkeypatch.setattr(ec2, "_agent", lambda *a, **k: {})
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: fake)
    # Records the argument, not just the call: shutdown must clear state as
    # the OWNER of a specific instance, so a concurrent run's freshly-written
    # state for a different box is not deleted out from under it (see
    # tests/test_ec2_state.py's ownership tests).
    monkeypatch.setattr(ec2, "_clear_state", lambda instance_id=None: cleared.append(instance_id))

    ec2.shutdown_instance(wait=True)  # must not raise

    assert fake.terminated == [["i-slow"]]
    # State is still cleared despite the expired waiter (the original point of
    # this test), and is cleared as the OWNER of i-slow rather than blindly.
    assert cleared == ["i-slow"]


# ---------------------------------------------------------------------------
# max_price / _spot_price_map (2026-08-13 audit: price-aware capacity hunt)
# ---------------------------------------------------------------------------


def test_run_instances_kwargs_max_price_sets_the_spot_ceiling():
    kwargs = _base_kwargs(max_price="25.1900")
    assert kwargs["InstanceMarketOptions"]["SpotOptions"]["MaxPrice"] == "25.1900"


def test_run_instances_kwargs_no_max_price_keeps_the_default_ceiling():
    kwargs = _base_kwargs()
    assert "MaxPrice" not in kwargs["InstanceMarketOptions"]["SpotOptions"]


def test_run_instances_kwargs_capacity_block_ignores_max_price():
    # A block launch replaces InstanceMarketOptions wholesale; a stray
    # MaxPrice would be an invalid combination.
    kwargs = _base_kwargs(capacity_reservation_id="cr-0abc", max_price="25.1900")
    assert kwargs["InstanceMarketOptions"] == {"MarketType": "capacity-block"}


def test_spot_price_map_newest_observation_wins(monkeypatch):
    class FakeClient:
        def describe_spot_price_history(self, **kwargs):
            # describe_spot_price_history returns rows newest-first.
            return {
                "SpotPriceHistory": [
                    {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1a", "SpotPrice": "20.00"},
                    {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1a", "SpotPrice": "99.00"},
                    {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1b", "SpotPrice": "21.50"},
                ]
            }

    monkeypatch.setattr(ec2, "_ec2_client", lambda region: FakeClient())
    prices = ec2._spot_price_map("us-east-1", ["p5.48xlarge"])
    assert prices == {
        ("p5.48xlarge", "us-east-1a"): 20.00,
        ("p5.48xlarge", "us-east-1b"): 21.50,
    }


def test_spot_price_map_failure_degrades_to_price_blind(monkeypatch):
    def boom(region):
        raise RuntimeError("no credentials")

    monkeypatch.setattr(ec2, "_ec2_client", boom)
    assert ec2._spot_price_map("us-east-1", ["p5.48xlarge"]) == {}


# _wait_public_ip absent-streak tolerance: DescribeInstances is eventually
# consistent, so a just-launched instance can be invisible for a few polls
# (observed live 2026-08-14 during a quota-race relaunch -- the driver
# declared a healthy box "absent" and crash-looped). Only a SUSTAINED absent
# streak may abort; positively-observed death states abort immediately.

def _no_sleep_ip(monkeypatch):
    monkeypatch.setattr(ec2._aws.time, "sleep", lambda s: None)


def test_wait_public_ip_tolerates_transient_absent_then_succeeds(monkeypatch):
    _no_sleep_ip(monkeypatch)
    polls = iter(
        [None] * (ec2._ABSENT_STREAK_LIMIT - 1)
        + [{"State": {"Name": "running"}, "PublicIpAddress": "1.2.3.4"}]
    )
    monkeypatch.setattr(ec2, "_describe_instance", lambda region, iid: next(polls))
    assert ec2._wait_public_ip("us-east-2", "i-abc") == "1.2.3.4"


def test_wait_public_ip_sustained_absent_still_aborts(monkeypatch):
    _no_sleep_ip(monkeypatch)
    calls = {"n": 0}

    def describe(region, iid):
        calls["n"] += 1
        return None

    monkeypatch.setattr(ec2, "_describe_instance", describe)
    with pytest.raises(RuntimeError, match="went absent right after launch"):
        ec2._wait_public_ip("us-east-2", "i-abc")
    assert calls["n"] == ec2._ABSENT_STREAK_LIMIT


def test_wait_public_ip_observed_terminated_aborts_immediately(monkeypatch):
    _no_sleep_ip(monkeypatch)
    monkeypatch.setattr(
        ec2, "_describe_instance", lambda region, iid: {"State": {"Name": "terminated"}}
    )
    with pytest.raises(RuntimeError, match="went terminated right after launch"):
        ec2._wait_public_ip("us-east-2", "i-abc")


# ec2.server_config: the provenance snapshot stamped onto stored results.

def test_server_config_snapshot_from_state(monkeypatch):
    monkeypatch.setattr(ec2, "_load_state", lambda: {
        "instance_type": "g7.24xlarge", "region": "us-east-2",
        "availability_zone": "us-east-2c", "instance_id": "i-abc123",
    })
    cfg = ec2.server_config("ministral-3-14b")
    assert cfg["instance_type"] == "g7.24xlarge"
    assert cfg["gpu"] == "4x RTX PRO 4500 32GB"
    assert cfg["tp"] == 4  # derived from the landed box, not the spec pin
    assert cfg["availability_zone"] == "us-east-2c"
    assert cfg["instance_id"] == "i-abc123"
    assert cfg["vllm_image"] == ec2.EC2_VLLM_IMAGE
    assert cfg["hf_model_id"] == ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["hf_model_id"]


def test_server_config_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("corrupt state")

    monkeypatch.setattr(ec2, "_load_state", boom)
    assert ec2.server_config("ministral-3-14b") is None
    # Absent state degrades to a schema-complete dict of Nones, not a crash.
    monkeypatch.setattr(ec2, "_load_state", lambda: None)
    cfg = ec2.server_config("gemma-4-12b")
    assert cfg["instance_type"] is None and cfg["gpu"] is None


# ---------------------------------------------------------------------------
# ec2.server_config §5 extension (DETERMINISM_PLAN_2026-08-16.md section 5):
# vllm_args/max_model_len/served_at (from state["last_serve"]), vllm_version/
# vllm_cache_config/agent_fingerprint/vllm_image_digest (live probes),
# max_parallel_requests/stream (client-side env config). The live-probe
# helpers (_fetch_vllm_version/_fetch_vllm_cache_config/_fetch_agent_
# fingerprint) are monkeypatched directly here -- server_config's OWN job is
# composing their results with last_serve/model-match gating, which is what
# these tests exercise; the helpers' own request-building is covered by the
# _FakeResponse-based unit tests further below.
# ---------------------------------------------------------------------------

_S5_STATE = {
    "instance_type": "g7.24xlarge",
    "region": "us-east-2",
    "availability_zone": "us-east-2c",
    "instance_id": "i-abc123",
    "public_ip": "203.0.113.10",
    "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret",
    "last_serve": {
        "model": "ministral-3-14b",
        "hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512",
        "tp": 4,
        "max_model_len": 131072,
        "vllm_args": ["--seed", "0"],
        "image": "vllm/vllm-openai@sha256:deadbeef",
        "served_at": "2026-08-18T00:00:00+00:00",
    },
}


def _patch_s5_fetches(monkeypatch, *, vllm_version="0.27.2rc1.dev122+g8efa13b70",
                       vllm_cache_config=None, agent_fp=None):
    """Stands in for the three live-probe helpers server_config() calls.

    Records the (ip, key) / state each was called with so a test can assert
    server_config only attempts a probe when it has enough state to reach the
    box (the "box absent" test below relies on this to prove no doomed call
    was made, not just that the result degraded to None).
    """
    calls = {"version": [], "cache": [], "agent": []}
    if vllm_cache_config is None:
        vllm_cache_config = ["vllm:cache_config_info{num_gpu_blocks=\"12345\"} 1.0"]
    if agent_fp is None:
        agent_fp = {
            "image_repo_digests": ["vllm/vllm-openai@sha256:cec2df507519abc"],
            "nvidia_smi": "H100 80GB HBM3, gpu-uuid-1, 550.90.07, 81559 MiB, Disabled",
            "hf_snapshots": ["51f9210f3cd20f3452a80d5819d15dc61cc50630"],
            "weights_digest": "abc123def456",
        }

    def fake_version(ip, key):
        calls["version"].append((ip, key))
        return vllm_version

    def fake_cache(ip, key):
        calls["cache"].append((ip, key))
        return vllm_cache_config

    def fake_agent_fp(state):
        calls["agent"].append(state)
        return agent_fp

    monkeypatch.setattr(ec2, "_fetch_vllm_version", fake_version)
    monkeypatch.setattr(ec2, "_fetch_vllm_cache_config", fake_cache)
    monkeypatch.setattr(ec2, "_fetch_agent_fingerprint", fake_agent_fp)
    return calls


def test_server_config_s5_happy_path_all_new_fields_populated(monkeypatch):
    """Box up, last_serve names the queried model, all probes succeed."""
    monkeypatch.setattr(ec2, "_load_state", lambda: dict(_S5_STATE))
    calls = _patch_s5_fetches(monkeypatch)
    monkeypatch.setenv("EC2_MAX_PARALLEL_REQUESTS", "3")
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")

    cfg = ec2.server_config("ministral-3-14b")

    # last_serve-derived (model matches).
    assert cfg["vllm_args"] == ["--seed", "0"]
    assert cfg["max_model_len"] == 131072
    assert cfg["served_at"] == "2026-08-18T00:00:00+00:00"
    # Live-probe-derived.
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"
    assert cfg["vllm_cache_config"] == ["vllm:cache_config_info{num_gpu_blocks=\"12345\"} 1.0"]
    assert cfg["agent_fingerprint"]["nvidia_smi"].startswith("H100")
    assert cfg["vllm_image_digest"] == "vllm/vllm-openai@sha256:cec2df507519abc"
    # Client-side config, read at call time.
    assert cfg["max_parallel_requests"] == 3
    assert cfg["stream"] is True
    # The probes were actually reached with the box's ip/key, not skipped.
    assert calls["version"] == [("203.0.113.10", "vk-stub-secret")]
    assert calls["cache"] == [("203.0.113.10", "vk-stub-secret")]
    assert len(calls["agent"]) == 1
    # The original 8 fields are untouched by the extension.
    assert cfg["instance_type"] == "g7.24xlarge"
    assert cfg["tp"] == 4


def test_server_config_s5_box_absent_degrades_to_none_without_probing(monkeypatch):
    """No state file at all: every box/network-derived §5 field is None, and
    the live-probe helpers are never even called (nothing to reach)."""
    monkeypatch.setattr(ec2, "_load_state", lambda: None)
    calls = _patch_s5_fetches(monkeypatch)

    cfg = ec2.server_config("gemma-4-12b")

    assert cfg["vllm_args"] is None
    assert cfg["max_model_len"] is None
    assert cfg["served_at"] is None
    assert cfg["vllm_version"] is None
    assert cfg["vllm_cache_config"] is None
    assert cfg["agent_fingerprint"] is None
    assert cfg["vllm_image_digest"] is None
    assert calls == {"version": [], "cache": [], "agent": []}
    # Client-side config is NOT box-dependent (env reads only) -- unlike the
    # box/network fields above, "no box" must not blank these, matching the
    # existing precedent that vllm_image/hf_model_id also survive no box.
    assert cfg["max_parallel_requests"] == 8  # ChatClient's own default
    assert cfg["stream"] is False
    # server_config must still return a dict, never None, on this path.
    assert cfg is not None


def test_server_config_s5_last_serve_model_mismatch_yields_none(monkeypatch):
    """last_serve names a DIFFERENT model than the one being queried (the box
    was swapped since): the launched-argv fields must not be misattributed to
    the model asked about, even though the box is reachable and the live
    probes (which describe whatever IS currently running) still succeed."""
    state = dict(_S5_STATE, last_serve=dict(_S5_STATE["last_serve"], model="gemma-4-12b"))
    monkeypatch.setattr(ec2, "_load_state", lambda: state)
    _patch_s5_fetches(monkeypatch)

    cfg = ec2.server_config("ministral-3-14b")

    assert cfg["vllm_args"] is None
    assert cfg["max_model_len"] is None
    assert cfg["served_at"] is None
    # Live probes are independent of the model-name match -- they describe
    # whatever the box is actually running right now, not the query's name.
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"
    assert cfg["agent_fingerprint"] is not None


def test_server_config_s5_malformed_env_blanks_only_its_own_field(monkeypatch):
    """EC2_STREAM_COMPLETIONS="true" (not "1") makes ChatClient._flag's
    ``bool(int(...))`` raise ValueError. That must degrade ONLY the "stream"
    field to None, not escape to server_config's outer except and blank
    every other already-computed field over one malformed env var."""
    monkeypatch.setattr(ec2, "_load_state", lambda: dict(_S5_STATE))
    _patch_s5_fetches(monkeypatch)
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "true")

    cfg = ec2.server_config("ministral-3-14b")

    assert cfg is not None
    assert cfg["stream"] is None
    assert cfg["vllm_args"] == ["--seed", "0"]  # untouched by the bad env var
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"


class _FakeResponse:
    """Minimal stand-in for requests.Response, as used by _Resp in
    test_openai_compat.py: only the attributes the code under test reads."""

    def __init__(self, *, ok=True, json_body=None, text="", status_code=200):
        self.ok = ok
        self._json_body = json_body
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._json_body


def test_fetch_vllm_version_returns_the_version_string(monkeypatch):
    monkeypatch.setattr(
        ec2.requests, "get",
        lambda url, headers, timeout: _FakeResponse(json_body={"version": "0.27.2rc1.dev122+g8efa13b70"}),
    )
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") == "0.27.2rc1.dev122+g8efa13b70"


def test_fetch_vllm_version_none_on_non_ok_and_on_exception(monkeypatch):
    monkeypatch.setattr(ec2.requests, "get", lambda url, headers, timeout: _FakeResponse(ok=False))
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") is None

    def boom(url, headers, timeout):
        raise ec2.requests.exceptions.ConnectionError("dead box")

    monkeypatch.setattr(ec2.requests, "get", boom)
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") is None


def test_fetch_vllm_cache_config_filters_to_cache_config_info_lines(monkeypatch):
    body = (
        "# HELP vllm:cache_config_info info\n"
        "# TYPE vllm:cache_config_info gauge\n"
        'vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0\n'
        'vllm:num_requests_running{} 0.0\n'
    )
    monkeypatch.setattr(
        ec2.requests, "get", lambda url, headers, timeout: _FakeResponse(text=body)
    )
    lines = ec2._fetch_vllm_cache_config("203.0.113.10", "vk")
    assert lines == ['vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0']


def test_fetch_vllm_cache_config_none_when_no_matching_lines(monkeypatch):
    monkeypatch.setattr(
        ec2.requests, "get",
        lambda url, headers, timeout: _FakeResponse(text="vllm:num_requests_running{} 0.0\n"),
    )
    assert ec2._fetch_vllm_cache_config("203.0.113.10", "vk") is None


def test_fetch_agent_fingerprint_extracts_the_fingerprint_key(monkeypatch):
    monkeypatch.setattr(
        ec2, "_agent",
        lambda state, method, path, timeout=None, connect_retries=None: {
            "healthy": True, "fingerprint": {"nvidia_smi": "stub"},
        },
    )
    assert ec2._fetch_agent_fingerprint(_S5_STATE) == {"nvidia_smi": "stub"}


def test_fetch_agent_fingerprint_none_on_failure(monkeypatch):
    def boom(state, method, path, timeout=None, connect_retries=None):
        raise RuntimeError("agent unreachable")

    monkeypatch.setattr(ec2, "_agent", boom)
    assert ec2._fetch_agent_fingerprint(_S5_STATE) is None


# ---------------------------------------------------------------------------
# ec2.serve_model: the "last_serve" stash (Change B of the §5 plan) -- the
# launched argv server_config() later reads back. Everything on the network
# boundary (_agent, _wait_model_ready, list_models) is monkeypatched out;
# this test's only job is proving the state mutation, not the swap protocol.
# ---------------------------------------------------------------------------


def test_serve_model_stashes_last_serve_with_the_actual_launched_argv(monkeypatch):
    state = {
        "instance_type": "g7.24xlarge",
        "region": "us-east-2",
        "availability_zone": "us-east-2c",
        "instance_id": "i-abc123",
        "public_ip": "203.0.113.10",
        "vllm_api_key": "vk-stub-secret",
        "control_token": "ct-stub-secret",
    }
    monkeypatch.delenv("EC2_REQUIRE_GPU", raising=False)
    monkeypatch.setattr(ec2, "_require_state", lambda: state)

    agent_calls = []

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        agent_calls.append((method, path, payload))
        if method == "GET" and path == "/status":
            # First call is the "already serving?" probe (before): report NOT
            # already serving so serve_model takes the real-swap path.
            return {"healthy": False}
        if method == "POST" and path == "/serve":
            return {"ok": True, "launching": payload["served_model_name"]}
        raise AssertionError(f"unexpected agent call: {method} {path}")

    saved = {}
    monkeypatch.setattr(ec2, "_agent", fake_agent)
    monkeypatch.setattr(ec2, "_wait_model_ready", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "list_models", lambda: ["ministral-3-14b"])
    monkeypatch.setattr(ec2, "_save_state", lambda s: saved.update(s))

    with ec2.serve_model("ministral-3-14b") as served:
        assert served == "ministral-3-14b"

    assert saved["last_serve"]["model"] == "ministral-3-14b"
    assert saved["last_serve"]["hf_model_id"] == "mistralai/Ministral-3-14B-Reasoning-2512"
    assert saved["last_serve"]["tp"] == 4  # derived from g7.24xlarge, not the spec's static pin
    assert saved["last_serve"]["max_model_len"] == 131072
    assert saved["last_serve"]["vllm_args"] == ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"]
    assert saved["last_serve"]["image"] == ec2.EC2_VLLM_IMAGE
    # served_at is a UTC ISO-8601 timestamp -- round-trips through fromisoformat.
    from datetime import datetime as _dt

    _dt.fromisoformat(saved["last_serve"]["served_at"])
    # "serving" (the pre-existing fast-path key) and "last_serve" are distinct
    # dicts with different key names -- serve_model must not conflate them.
    assert saved["serving"]["served_model_name"] == "ministral-3-14b"
    assert "served_model_name" not in saved["last_serve"]
    # The real swap actually happened (POST /serve), not the skip path.
    assert ("POST", "/serve") in [(m, p) for m, p, _ in agent_calls]


def test_on_demand_market_drops_instance_market_options(monkeypatch):
    """EC2_MARKET=on-demand launches by OMITTING InstanceMarketOptions.

    There is no MarketType="on-demand" -- absence is how the API expresses it,
    so a launch that merely renamed the MarketType would be rejected. Every
    other kwarg must be byte-identical to the spot shape, because the whole
    point of this path is buying the SAME silicon a different way: it exists
    for a lane (deepseek-v3.1, 2026-08-15) whose p5e.48xlarge had no spot
    capacity in any AZ and whose hardware could not be substituted without
    contaminating the study.

    The bid ceiling must go too: an on-demand launch has no MaxPrice, and
    leaving one attached would be rejected.
    """
    monkeypatch.setattr(ec2, "EC2_MARKET", "on-demand")
    kwargs = _base_kwargs(max_price="12.34")
    assert "InstanceMarketOptions" not in kwargs

    monkeypatch.setattr(ec2, "EC2_MARKET", "spot")
    spot = _base_kwargs(max_price="12.34")
    assert spot["InstanceMarketOptions"]["SpotOptions"]["MaxPrice"] == "12.34"

    # Same box, different till: everything except the market differs not at all.
    assert {k: v for k, v in spot.items() if k != "InstanceMarketOptions"} == kwargs
    # The cost backstop survives -- an abandoned on-demand p5e bills forever.
    assert kwargs["InstanceInitiatedShutdownBehavior"] == "terminate"


def test_capacity_block_still_wins_over_on_demand(monkeypatch):
    """A purchased block is targeted even when EC2_MARKET says on-demand."""
    monkeypatch.setattr(ec2, "EC2_MARKET", "on-demand")
    kwargs = _base_kwargs(capacity_reservation_id="cr-123")
    assert kwargs["InstanceMarketOptions"] == {"MarketType": "capacity-block"}
    assert kwargs["CapacityReservationSpecification"] == {
        "CapacityReservationTarget": {"CapacityReservationId": "cr-123"}
    }


def test_spot_bid_multiplier_scales_the_cap_and_zero_means_uncapped(monkeypatch):
    """EC2_SPOT_BID_MULTIPLIER scales the bid; <= 0 sends no MaxPrice at all.

    Sending no MaxPrice defaults the ceiling to the ON-DEMAND price, which is
    the highest bid EC2 accepts -- there is no way to bid above it, and the spot
    price never exceeds it.

    Raising the multiplier only helps when an AZ's price genuinely exceeds the
    cap; within spot, InsufficientInstanceCapacity is about physical hosts, not
    money. It does NOT follow that on-demand is better at acquiring capacity --
    that claim was made here and was wrong. deepseek-v3.1 failed 2,079 ON-DEMAND
    attempts across 13 AZs with InsufficientInstanceCapacity and then landed on
    SPOT within one attempt (2026-08-16). On-demand's priority concerns
    interruption, not which pool has free hosts.
    """
    assert ec2.EC2_SPOT_BID_MULTIPLIER == 1.25, "default headroom over median"

    # A cap is passed through verbatim to SpotOptions.MaxPrice.
    kwargs = _base_kwargs(max_price="9.9900")
    assert kwargs["InstanceMarketOptions"]["SpotOptions"]["MaxPrice"] == "9.9900"

    # No cap -> the key is absent, i.e. EC2's default on-demand ceiling.
    kwargs = _base_kwargs(max_price=None)
    assert "MaxPrice" not in kwargs["InstanceMarketOptions"]["SpotOptions"]
    assert kwargs["InstanceMarketOptions"]["MarketType"] == "spot"


def test_launch_fresh_wraps_user_data_in_pack_user_data():
    """gzip is LOAD-BEARING, not an optimization: the raw render is 57 bytes
    over EC2's 16 KB user-data cap under the digest-pinned image, so a
    regression that drops the ``pack_user_data`` call would fail only at the
    live ``RunInstances`` call, with zero local signal. Source-text pin (the
    same env-independent pattern as
    test_deploy_specs.test_ec2_vllm_image_default_is_digest_pinned).
    """
    import re
    from pathlib import Path

    src = Path(ec2.__file__.replace(".pyc", ".py")).read_text()
    assert re.search(r"pack_user_data\(\s*render_user_data\(", src), (
        "ec2.py must build user-data as pack_user_data(render_user_data(...)) "
        "-- raw user-data no longer fits EC2's 16 KB cap"
    )
