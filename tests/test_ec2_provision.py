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
