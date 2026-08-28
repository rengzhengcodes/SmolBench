"""Test the pure logic of ``scripts/results/provision_results_bucket.py``.

No AWS, no network. The script is a human-run runbook against ADMIN
credentials, and nothing here ever executes it against AWS. Every
client is a fake. The real bucket now exists and must not be touched,
which makes the fakes a safety property, not just a speed one.

Scope note: this script is PROVISION-ONLY. It used to also seed the
bucket from local result trees, and those tests are gone with that
feature. The bucket is deliberately empty, and results reach it only
by being written through ``smolbench.evals.results_store`` in the
append-only log layout.
"""

import json
import sys

import pytest

from tests._paths import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.results import provision_results_bucket as p  # noqa: E402  (needs the path insert)
from smolbench.evals import _aws  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeAwsClient:
    """One fake standing in for both the S3 and IAM clients.

    Records every call as ``(operation, kwargs)`` so a test can assert the
    provisioning steps ran with the right arguments.
    """

    def __init__(self):
        self.calls: list = []

    def _record(self, op, **kwargs):
        self.calls.append((op, kwargs))

    # -- S3 ------------------------------------------------------------------
    def create_bucket(self, **kwargs):
        self._record("create_bucket", **kwargs)

    def put_public_access_block(self, **kwargs):
        self._record("put_public_access_block", **kwargs)

    def put_bucket_versioning(self, **kwargs):
        self._record("put_bucket_versioning", **kwargs)

    # -- IAM / STS -----------------------------------------------------------
    def create_policy(self, **kwargs):
        self._record("create_policy", **kwargs)
        return {
            "Policy": {"Arn": f"arn:aws:iam::414266451290:policy/{kwargs['PolicyName']}"}
        }

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
    if hasattr(p, "fresh_client"):
        monkeypatch.setattr(p, "fresh_client", _fresh_client)
    return client


# ---------------------------------------------------------------------------
# The seeding machinery must be GONE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "removed",
    [
        "SEED_TREES",
        "seed_tree",
        "s3_sync_command",
        "dest_prefix",
        "count_local_files",
        "count_s3_objects",
        "format_table",
        "TreeCount",
    ],
)
def test_seeding_machinery_is_removed(removed):
    """The bucket is deliberately empty and is never bulk-seeded.

    This is pinned by name, because a leftover helper is an invitation
    to re-enable the old repo-mirroring upload path, which would write
    objects in a layout nothing reads any more.
    """
    assert not hasattr(p, removed), f"{removed} should have been removed with seeding"


def test_no_seeding_flags_remain():
    for flag in ("--seed", "--from", "--dest"):
        with pytest.raises(SystemExit):
            p.parse_args([flag])


# ---------------------------------------------------------------------------
# Constants and pure helpers
# ---------------------------------------------------------------------------


def test_bucket_and_region_are_the_fixed_decision():
    assert p.BUCKET == "smolbench-results-414266451290"
    assert p.REGION == "us-west-2"


def test_policy_document_grants_list_on_bucket_and_rw_on_contents():
    doc = p.policy_document("some-bucket")
    assert doc["Version"] == "2012-10-17"
    assert doc["Statement"] == [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::some-bucket",
        },
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
            "Resource": "arn:aws:s3:::some-bucket/*",
        },
    ]
    json.dumps(doc)  # must be serializable as-is


def test_access_denied_message_names_the_operation_and_the_credential_cause():
    msg = p.access_denied_message("s3:CreateBucket")
    assert "s3:CreateBucket" in msg
    lowered = msg.lower()
    assert "admin" in lowered
    assert "expired" in lowered or "scoped" in lowered


def test_parse_args_takes_no_arguments():
    args = p.parse_args([])
    assert vars(args) == {} or all(v in (None, False) for v in vars(args).values())


# ---------------------------------------------------------------------------
# Provisioning steps against the fake client
# ---------------------------------------------------------------------------


def test_ensure_bucket_passes_the_location_constraint(fake_aws):
    """us-west-2 is not the grandfathered us-east-1 default.

    So the constraint is required, or the bucket lands in the wrong region.
    """
    p.ensure_bucket(fake_aws)
    op, kwargs = next(c for c in fake_aws.calls if c[0] == "create_bucket")
    assert kwargs["Bucket"] == p.BUCKET
    assert kwargs["CreateBucketConfiguration"] == {"LocationConstraint": p.REGION}


def test_ensure_bucket_tolerates_already_owned(fake_aws, monkeypatch):
    """This test checks idempotency.

    The bucket already exists live, so a re-run must not fail on its own bucket.
    """
    from botocore.exceptions import ClientError

    def _already(**kwargs):
        raise ClientError(
            {"Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "yours"}},
            "CreateBucket",
        )

    monkeypatch.setattr(fake_aws, "create_bucket", _already)
    p.ensure_bucket(fake_aws)  # must not raise


def test_put_public_access_block_sets_all_four_flags(fake_aws):
    p.put_public_access_block(fake_aws)
    op, kwargs = next(c for c in fake_aws.calls if c[0] == "put_public_access_block")
    assert kwargs["PublicAccessBlockConfiguration"] == {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    }


def test_enable_versioning(fake_aws):
    p.enable_versioning(fake_aws)
    op, kwargs = next(c for c in fake_aws.calls if c[0] == "put_bucket_versioning")
    assert kwargs["VersioningConfiguration"] == {"Status": "Enabled"}


def test_ensure_policy_creates_the_named_policy_and_returns_its_arn(fake_aws):
    arn = p.ensure_policy(fake_aws)
    op, kwargs = next(c for c in fake_aws.calls if c[0] == "create_policy")
    assert kwargs["PolicyName"] == "SmolbenchResultsBucketRW"
    assert json.loads(kwargs["PolicyDocument"]) == p.policy_document(p.BUCKET)
    assert arn.endswith("policy/SmolbenchResultsBucketRW")


def test_ensure_policy_reuses_an_existing_policy_without_new_versions(
    fake_aws, monkeypatch
):
    """Create-or-reuse, never create-a-new-VERSION.

    A managed policy holds at most 5 versions, and this policy already
    exists live, so every re-run would burn one.
    """
    from botocore.exceptions import ClientError

    existing = "arn:aws:iam::414266451290:policy/SmolbenchResultsBucketRW"

    def _exists(**kwargs):
        raise ClientError(
            {"Error": {"Code": "EntityAlreadyExists", "Message": "exists"}},
            "CreatePolicy",
        )

    monkeypatch.setattr(fake_aws, "create_policy", _exists)
    monkeypatch.setattr(
        fake_aws,
        "list_policies",
        lambda **kw: {
            "Policies": [{"PolicyName": "SmolbenchResultsBucketRW", "Arn": existing}]
        },
    )
    assert p.ensure_policy(fake_aws) == existing
    assert not any(c[0] == "create_policy_version" for c in fake_aws.calls)


def test_attach_policy_to_group_targets_the_operator_group(fake_aws):
    p.attach_policy_to_group(fake_aws, "arn:aws:iam::414266451290:policy/X")
    op, kwargs = next(c for c in fake_aws.calls if c[0] == "attach_group_policy")
    assert kwargs["GroupName"] == "smolbench-ec2-operators"
    assert kwargs["PolicyArn"] == "arn:aws:iam::414266451290:policy/X"


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def test_main_runs_every_provisioning_step_and_returns_zero(fake_aws, capsys):
    assert p.main([]) == 0
    ops = [c[0] for c in fake_aws.calls]
    for expected in (
        "create_bucket",
        "put_public_access_block",
        "put_bucket_versioning",
        "create_policy",
        "attach_group_policy",
    ):
        assert expected in ops


def test_main_returns_nonzero_and_explains_on_access_denied(
    fake_aws, monkeypatch, capsys
):
    """The scoped EC2-only operator key cannot manage S3.

    That must produce the actionable message, not a raw traceback.
    """
    from botocore.exceptions import ClientError

    def _denied(**kwargs):
        raise ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "CreateBucket"
        )

    monkeypatch.setattr(fake_aws, "create_bucket", _denied)
    code = p.main([])
    out = capsys.readouterr().out

    assert code != 0
    assert "ACCESS DENIED" in out.upper()
    assert "admin" in out.lower()
