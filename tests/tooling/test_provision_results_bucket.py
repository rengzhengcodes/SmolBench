"""Offline tests for ``provision_results_bucket.py``.

The fake records unknown calls so absence assertions remain falsifiable.
"""

import json
from collections.abc import Callable
from typing import Any

import pytest
from botocore.exceptions import ClientError

from scripts.results import provision_results_bucket as p
from smolbench.evals import _aws


class FakeAwsClient:
    """One fake standing in for both the S3 and IAM clients.

    Preserve ordered duplicate calls; an operation-keyed mapping would hide
    a second ``create_bucket``.
    """

    def __init__(self) -> None:
        self.calls: list = []

    def _record(self, op: str, **kwargs: Any) -> None:
        self.calls.append((op, kwargs))

    def __getattr__(self, name: str) -> Any:
        """Record any operation this fake doesn't implement, and return ``{}``.

        Refuse dunder lookups so introspection sees a normal object.
        """
        if name.startswith("__"):
            raise AttributeError(name)

        def _unknown(**kwargs: Any) -> dict[Any, Any]:
            self._record(name, **kwargs)
            return {}

        return _unknown

    def create_policy(self, **kwargs: Any) -> dict[str, dict[str, str]]:
        self._record("create_policy", **kwargs)
        return {"Policy": {"Arn": f"arn:aws:iam::414266451290:policy/{kwargs['PolicyName']}"}}

    def list_policies(self, **kwargs: Any) -> dict[str, list[Any]]:
        self._record("list_policies", **kwargs)
        return {"Policies": []}

    def get_caller_identity(self, **kwargs: Any) -> dict[str, str]:
        self._record("get_caller_identity", **kwargs)
        return {"Account": "414266451290"}


@pytest.fixture
def fake_aws(monkeypatch: pytest.MonkeyPatch) -> FakeAwsClient:
    """Routes every client construction to one FakeAwsClient.

    Clear ``SMOLBENCH_RESULTS_S3`` to isolate default-bucket tests.
    """
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    client = FakeAwsClient()

    def _fresh_client(service: str, region: str | None = None) -> FakeAwsClient:
        client.calls.append(("fresh_client", {"service": service, "region": region}))
        return client

    monkeypatch.setattr(_aws, "fresh_client", _fresh_client)
    return client


def _kwargs_for(calls: list[tuple[str, dict[str, Any]]], op: str) -> list[dict[str, Any]]:
    """Return every recorded kwargs mapping for `op`, in call order."""
    return [kwargs for name, kwargs in calls if name == op]


def _raiser(code: str, operation: str) -> Callable[..., None]:
    def _fail(**kwargs: Any) -> None:
        raise ClientError({"Error": {"Code": code, "Message": code}}, operation)

    return _fail


def test_policy_document_grants_list_on_bucket_and_rw_on_contents() -> None:
    doc = p.policy_document("some-bucket")
    assert doc["Version"] == "2012-10-17"
    assert doc["Statement"] == [
        {"Effect": "Allow", "Action": ["s3:ListBucket"],
         "Resource": "arn:aws:s3:::some-bucket"},
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::some-bucket/*"},
    ]


def test_unknown_calls_are_recorded(fake_aws: FakeAwsClient) -> None:
    """Positive control for `FakeAwsClient.__getattr__` (see the module docstring)."""
    assert fake_aws.create_policy_version(PolicyArn="arn:x", PolicyDocument="{}") == {}
    assert ("create_policy_version",
            {"PolicyArn": "arn:x", "PolicyDocument": "{}"}) in fake_aws.calls


def test_main_provisions_bucket_policy_and_group_attachment(fake_aws: FakeAwsClient) -> None:
    assert p.main([]) == 0
    calls = fake_aws.calls

    # S3 uses the bucket region; IAM is global.
    assert [kw for name, kw in calls if name == "fresh_client"] == [
        {"service": "s3", "region": "us-west-2"},
        {"service": "iam", "region": None},
    ]

    # Lists expose duplicate mutating calls.
    assert [name for name, _kw in calls].count("create_bucket") == 1
    assert _kwargs_for(calls, "create_bucket") == [{
        "Bucket": "smolbench-results-414266451290",
        "CreateBucketConfiguration": {"LocationConstraint": "us-west-2"},
    }]
    assert _kwargs_for(calls, "put_public_access_block")[0][
        "PublicAccessBlockConfiguration"] == {
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True}
    assert _kwargs_for(calls, "put_bucket_versioning")[0][
        "VersioningConfiguration"] == {"Status": "Enabled"}
    create_policy = _kwargs_for(calls, "create_policy")[0]
    assert create_policy["PolicyName"] == "SmolbenchResultsBucketRW"
    assert json.loads(create_policy["PolicyDocument"]) == p.policy_document(
        "smolbench-results-414266451290")
    attach = _kwargs_for(calls, "attach_group_policy")[0]
    assert attach["GroupName"] == "smolbench-ec2-operators"
    assert attach["PolicyArn"].endswith("policy/SmolbenchResultsBucketRW")


def test_main_provisions_the_bucket_smolbench_results_s3_names(
    fake_aws: FakeAwsClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The provisioner targets the configured store, not a stale literal."""
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://redirected-bucket/analysis/2026-08-16")
    assert p.main([]) == 0
    assert _kwargs_for(fake_aws.calls, "create_bucket")[0]["Bucket"] == "redirected-bucket"
    assert json.loads(
        _kwargs_for(fake_aws.calls, "create_policy")[0]["PolicyDocument"]
    ) == p.policy_document("redirected-bucket")


def test_ensure_bucket_tolerates_already_owned(
    fake_aws: FakeAwsClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A re-run must not fail on the bucket it already owns."""
    monkeypatch.setattr(fake_aws, "create_bucket",
                        _raiser("BucketAlreadyOwnedByYou", "CreateBucket"))
    p.ensure_bucket(fake_aws, "any-bucket")


def test_ensure_policy_reuses_an_existing_policy_without_new_versions(
    fake_aws: FakeAwsClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Create-or-reuse, never create a new version (the 5-version cap)."""
    existing = "arn:aws:iam::414266451290:policy/SmolbenchResultsBucketRW"
    monkeypatch.setattr(fake_aws, "create_policy",
                        _raiser("EntityAlreadyExists", "CreatePolicy"))
    monkeypatch.setattr(fake_aws, "list_policies", lambda **kw: {
        "Policies": [{"PolicyName": "SmolbenchResultsBucketRW", "Arn": existing}]})
    assert p.ensure_policy(fake_aws, "any-bucket") == existing
    assert not any(c[0] == "create_policy_version" for c in fake_aws.calls)


def test_main_returns_nonzero_and_explains_on_access_denied(
    fake_aws: FakeAwsClient, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """A scoped EC2-only key must produce the actionable message, not a traceback."""
    monkeypatch.setattr(fake_aws, "create_bucket", _raiser("AccessDenied", "CreateBucket"))
    code = p.main([])
    out = capsys.readouterr().out
    assert code != 0
    assert "ACCESS DENIED" in out.upper()
    assert "admin" in out.lower()
