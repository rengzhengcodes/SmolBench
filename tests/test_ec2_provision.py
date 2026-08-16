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
        user_data="#!/bin/bash\necho hi\n",
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
        "UserData": "#!/bin/bash\necho hi\n",
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
