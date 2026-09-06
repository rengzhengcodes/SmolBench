"""Pure-logic tests for scripts/results/provision_results_bucket.py.

No AWS, no network: every client is a fake, so the live bucket is never touched.

The fake records EVERY call, including operations it does not implement (see
`FakeAwsClient.__getattr__`). That matters for the 5-version-cap guarantee:
the assertion "``create_policy_version`` was never called" is only meaningful
if that name COULD have been recorded, and the earlier fake, which implemented
exactly seven methods and nothing else, made it unfalsifiable -- a regression
would have surfaced as an ``AttributeError`` raised by the fake, not as that
assertion failing. `test_unknown_calls_are_recorded` is its positive control.
"""

import json

import pytest
from botocore.exceptions import ClientError

from scripts.results import provision_results_bucket as p
from smolbench.evals import _aws


class FakeAwsClient:
    """One fake standing in for both the S3 and IAM clients.

    Records every call as ``(operation, kwargs)`` onto `calls`, in ORDER and
    with duplicates kept -- collapsing them into an operation-keyed dict would
    hide a second ``create_bucket`` behind the first.
    """

    def __init__(self):
        self.calls: list = []

    def _record(self, op, **kwargs):
        self.calls.append((op, kwargs))

    def __getattr__(self, name):
        """Record any operation this fake does not implement, and return ``{}``.

        Only reached for attributes not found normally, so the explicit methods
        below keep their own return values. Dunder lookups are refused, so copy,
        pickle and pytest introspection still see a normal object rather than a
        callable for every conceivable name.
        """
        if name.startswith("__"):
            raise AttributeError(name)

        def _unknown(**kwargs):
            self._record(name, **kwargs)
            return {}

        return _unknown

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
    """Routes every client construction to one FakeAwsClient.

    Also clears ``SMOLBENCH_RESULTS_S3``, so the default-bucket tests below
    describe the documented fallback deliberately instead of inheriting
    whatever a developer's shell exports.
    """
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    client = FakeAwsClient()

    def _fresh_client(service, region=None):
        client.calls.append(("fresh_client", {"service": service, "region": region}))
        return client

    monkeypatch.setattr(_aws, "fresh_client", _fresh_client)
    return client


def _kwargs_for(calls, op):
    """Return every recorded kwargs mapping for `op`, in call order."""
    return [kwargs for name, kwargs in calls if name == op]


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


def test_unknown_calls_are_recorded(fake_aws):
    """Positive control for `FakeAwsClient.__getattr__` (see the module docstring)."""
    assert fake_aws.create_policy_version(PolicyArn="arn:x", PolicyDocument="{}") == {}
    assert ("create_policy_version",
            {"PolicyArn": "arn:x", "PolicyDocument": "{}"}) in fake_aws.calls


def test_main_provisions_bucket_policy_and_group_attachment(fake_aws):
    assert p.main([]) == 0
    calls = fake_aws.calls

    # The clients: S3 pinned to the bucket's region, IAM global (region None).
    assert [kw for name, kw in calls if name == "fresh_client"] == [
        {"service": "s3", "region": "us-west-2"},
        {"service": "iam", "region": None},
    ]

    # Each mutating step runs EXACTLY once (kept as a list, so a duplicate
    # cannot hide behind the last call of the same name).
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


def test_main_provisions_the_bucket_smolbench_results_s3_names(fake_aws, monkeypatch):
    """The provisioner targets the CONFIGURED store, not a stale literal (14-15).

    Otherwise it provisions one bucket while ``S3ResultsStore`` writes to
    another. The base prefix in the URI is deliberately ignored here:
    everything this script provisions is bucket-level.
    """
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://redirected-bucket/analysis/2026-08-16")
    assert p.main([]) == 0
    assert _kwargs_for(fake_aws.calls, "create_bucket")[0]["Bucket"] == "redirected-bucket"
    assert json.loads(
        _kwargs_for(fake_aws.calls, "create_policy")[0]["PolicyDocument"]
    ) == p.policy_document("redirected-bucket")


def test_ensure_bucket_tolerates_already_owned(fake_aws, monkeypatch):
    """A re-run must not fail on the bucket it already owns."""
    monkeypatch.setattr(fake_aws, "create_bucket",
                        _raiser("BucketAlreadyOwnedByYou", "CreateBucket"))
    p.ensure_bucket(fake_aws)


def test_ensure_policy_reuses_an_existing_policy_without_new_versions(fake_aws, monkeypatch):
    """Create-or-reuse, never create-a-new-VERSION (5-version cap).

    The negative assertion has teeth only because the fake records unknown
    operations -- see `test_unknown_calls_are_recorded`.
    """
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
