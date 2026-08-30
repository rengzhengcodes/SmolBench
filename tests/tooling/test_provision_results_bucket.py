"""Pure-logic tests for scripts/results/provision_results_bucket.py.

No AWS, no network: every client is a fake, so the live bucket is never touched.
"""

import json

import pytest
from botocore.exceptions import ClientError

from scripts.results import provision_results_bucket as p
from smolbench.evals import _aws


class FakeAwsClient:
    """One fake standing in for both the S3 and IAM clients."""

    def __init__(self):
        self.calls: list = []

    def _record(self, op, **kwargs):
        self.calls.append((op, kwargs))

    def create_bucket(self, **kwargs):
        self._record("create_bucket", **kwargs)

    def put_public_access_block(self, **kwargs):
        self._record("put_public_access_block", **kwargs)

    def put_bucket_versioning(self, **kwargs):
        self._record("put_bucket_versioning", **kwargs)

    def create_policy(self, **kwargs):
        self._record("create_policy", **kwargs)
        return {"Policy": {"Arn": f"arn:aws:iam::414266451290:policy/{kwargs['PolicyName']}"}}

    def attach_group_policy(self, **kwargs):
        self._record("attach_group_policy", **kwargs)

    def list_policies(self, **kwargs):
        self._record("list_policies", **kwargs)
        return {"Policies": []}

    def get_caller_identity(self, **kwargs):
        self._record("get_caller_identity", **kwargs)
        return {"Account": "414266451290"}


@pytest.fixture
def fake_aws(monkeypatch):
    """Routes every client construction to one FakeAwsClient."""
    client = FakeAwsClient()

    def _fresh_client(service, region=None):
        client.calls.append(("fresh_client", {"service": service, "region": region}))
        return client

    monkeypatch.setattr(_aws, "fresh_client", _fresh_client)
    return client


def _raiser(code, operation):
    def _fail(**kwargs):
        raise ClientError({"Error": {"Code": code, "Message": code}}, operation)

    return _fail


def test_policy_document_grants_list_on_bucket_and_rw_on_contents():
    doc = p.policy_document("some-bucket")
    assert doc["Version"] == "2012-10-17"
    assert doc["Statement"] == [
        {"Effect": "Allow", "Action": ["s3:ListBucket"],
         "Resource": "arn:aws:s3:::some-bucket"},
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::some-bucket/*"},
    ]


def test_main_provisions_bucket_policy_and_group_attachment(fake_aws):
    assert p.main([]) == 0
    by_op = {op: kwargs for op, kwargs in fake_aws.calls}
    assert by_op["create_bucket"]["Bucket"] == "smolbench-results-414266451290"
    assert by_op["create_bucket"]["CreateBucketConfiguration"] == {
        "LocationConstraint": "us-west-2"}
    assert by_op["put_public_access_block"]["PublicAccessBlockConfiguration"] == {
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True}
    assert by_op["put_bucket_versioning"]["VersioningConfiguration"] == {"Status": "Enabled"}
    assert by_op["create_policy"]["PolicyName"] == "SmolbenchResultsBucketRW"
    assert json.loads(by_op["create_policy"]["PolicyDocument"]) == p.policy_document(p.BUCKET)
    assert by_op["attach_group_policy"]["GroupName"] == "smolbench-ec2-operators"
    assert by_op["attach_group_policy"]["PolicyArn"].endswith("policy/SmolbenchResultsBucketRW")


def test_ensure_bucket_tolerates_already_owned(fake_aws, monkeypatch):
    """A re-run must not fail on the bucket it already owns."""
    monkeypatch.setattr(fake_aws, "create_bucket",
                        _raiser("BucketAlreadyOwnedByYou", "CreateBucket"))
    p.ensure_bucket(fake_aws)


def test_ensure_policy_reuses_an_existing_policy_without_new_versions(fake_aws, monkeypatch):
    """Create-or-reuse, never create-a-new-VERSION (5-version cap)."""
    existing = "arn:aws:iam::414266451290:policy/SmolbenchResultsBucketRW"
    monkeypatch.setattr(fake_aws, "create_policy",
                        _raiser("EntityAlreadyExists", "CreatePolicy"))
    monkeypatch.setattr(fake_aws, "list_policies", lambda **kw: {
        "Policies": [{"PolicyName": "SmolbenchResultsBucketRW", "Arn": existing}]})
    assert p.ensure_policy(fake_aws) == existing
    assert not any(c[0] == "create_policy_version" for c in fake_aws.calls)


def test_main_returns_nonzero_and_explains_on_access_denied(fake_aws, monkeypatch, capsys):
    """A scoped EC2-only key must produce the actionable message, not a traceback."""
    monkeypatch.setattr(fake_aws, "create_bucket", _raiser("AccessDenied", "CreateBucket"))
    code = p.main([])
    out = capsys.readouterr().out
    assert code != 0
    assert "ACCESS DENIED" in out.upper()
    assert "admin" in out.lower()
