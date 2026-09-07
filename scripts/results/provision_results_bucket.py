"""Provision the S3-backed replicate results bucket (needs ADMIN credentials).

Provisions the bucket named by ``SMOLBENCH_RESULTS_S3`` (or
``DEFAULT_RESULTS_BUCKET``): public access blocked, versioning enabled, the
managed read/write policy attached to the day-to-day operator IAM group. Every
step is idempotent; nothing runs at import time. Exits 1 when a call is
denied, since day-to-day credentials are EC2-only. The bucket is not seeded:
any historical import must go through ``S3ResultsStore`` instead.

    .venv/bin/python scripts/results/provision_results_bucket.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import Any

from smolbench.evals.results_store import resolve_results_location

REGION = "us-west-2"
POLICY_NAME = "SmolbenchResultsBucketRW"
GROUP_NAME = "smolbench-ec2-operators"

#: `ClientError` codes `_run_step` treats uniformly as access denied.
_ACCESS_DENIED_CODES = frozenset(
    {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation"}
)


# ---------------------------------------------------------------------------
# Pure functions (no AWS, no I/O)
# ---------------------------------------------------------------------------
def policy_document(bucket: str) -> dict:
    """Build the IAM policy document granting read/write on ``bucket``.

    ``s3:ListBucket`` needs the bucket ARN with no trailing ``/*``; object
    actions need the ``/*`` wildcard. Key order is pinned: a reviewer diffs
    the rendered ``json.dumps`` against this shape.

    Parameters
    ----------
    bucket : str
        bucket whose ARN the policy grants access to.

    Returns
    -------
    dict
        IAM policy document granting read/write on ``bucket``.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:ListBucket"],
                "Resource": f"arn:aws:s3:::{bucket}",
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                "Resource": f"arn:aws:s3:::{bucket}/*",
            },
        ],
    }


def access_denied_message(operation: str) -> str:
    """Build the AccessDenied message for ``operation`` (e.g. ``"s3:CreateBucket"``)."""
    return (
        f"ACCESS DENIED on {operation}.\n"
        "The credentials in use are expired, or deliberately scoped-out: "
        f"the {GROUP_NAME!r} operator key used for day-to-day eval runs is "
        "EC2-only and cannot manage S3 or IAM. This script requires ADMIN "
        "credentials -- authenticate with an admin-scoped profile and re-run."
    )


# ---------------------------------------------------------------------------
# AWS steps. Each takes an already-built client, so each is testable against a
# fake with no AWS SDK installed.
# ---------------------------------------------------------------------------
def ensure_bucket(s3: Any, bucket: str, region: str = REGION) -> None:
    """Create ``bucket`` in ``region``, tolerating "already provisioned".

    ``CreateBucketConfiguration`` is required: without it ``create_bucket``
    always targets ``us-east-1`` regardless of the client's region binding.

    Parameters
    ----------
    s3 : Any
        S3 client that creates the bucket.
    bucket : str
        bucket to create.
    region : str, optional
        region for the bucket's location constraint.
    """
    from botocore.exceptions import ClientError

    from smolbench.evals._aws import error_code

    try:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
    except ClientError as err:
        if error_code(err) not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise


def put_public_access_block(s3: Any, bucket: str) -> None:
    """Block all public access on ``bucket``, setting all four flags to True.

    A PUT (replace), so re-running is idempotent with no error-code handling.

    Parameters
    ----------
    s3 : Any
        S3 client that sets the access block.
    bucket : str
        bucket whose public access is blocked.
    """
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )


def enable_versioning(s3: Any, bucket: str) -> None:
    """Enable S3 versioning on ``bucket`` (an idempotent call).

    Replicates are written exactly once and never mutated, so versions cost
    almost nothing while making a racing overwrite or a destructive
    ``aws s3 sync --delete`` recoverable.

    Parameters
    ----------
    s3 : Any
        S3 client that enables versioning.
    bucket : str
        bucket on which to enable versioning.
    """
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})


def ensure_policy(iam: Any, bucket: str, name: str = POLICY_NAME) -> str:
    """Create the managed policy granting read/write on ``bucket``, or reuse it.

    Create-or-reuse, not create-or-update: refreshing on every run would burn
    IAM's 5-version budget per managed policy, so a real change is a
    deliberate manual ``aws iam create-policy-version``.

    Parameters
    ----------
    iam : Any
        IAM client that creates or lists policies.
    bucket : str
        bucket the policy grants access to.
    name : str, optional
        managed policy name.

    Returns
    -------
    str
        ARN of the created or existing managed policy.
    """
    from botocore.exceptions import ClientError

    from smolbench.evals._aws import error_code

    try:
        response = iam.create_policy(
            PolicyName=name,
            PolicyDocument=json.dumps(policy_document(bucket)),
        )
        return response["Policy"]["Arn"]
    except ClientError as err:
        if error_code(err) != "EntityAlreadyExists":
            raise

    marker: str | None = None
    while True:
        kwargs = {"Scope": "Local"}
        if marker:
            kwargs["Marker"] = marker
        response = iam.list_policies(**kwargs)
        for policy in response.get("Policies", []):
            if policy["PolicyName"] == name:
                return policy["Arn"]
        if not response.get("IsTruncated"):
            break
        marker = response["Marker"]

    raise RuntimeError(
        f"IAM reported EntityAlreadyExists for policy {name!r}, but it is not "
        f"present in list_policies(Scope='Local')"
    )


def attach_policy_to_group(iam: Any, policy_arn: str, group: str = GROUP_NAME) -> None:
    """Attach ``policy_arn`` (from `ensure_policy`) to IAM group ``group``.

    No "already attached" handling needed: ``attach_group_policy`` is
    idempotent server-side.

    Parameters
    ----------
    iam : Any
        IAM client that attaches the policy.
    policy_arn : str
        ARN of the managed policy to attach.
    group : str, optional
        IAM group that receives the policy.
    """
    iam.attach_group_policy(GroupName=group, PolicyArn=policy_arn)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
class _ProvisionAccessDenied(Exception):
    """Raised by `_run_step` on a denied call, so `main` exits 1 with no traceback."""


def _run_step(label: str, operation: str, call: Callable[[], Any]) -> Any:
    """Run one provisioning step with a progress line and AccessDenied handling.

    other exceptions propagate.

    Parameters
    ----------
    label : str
        progress label to print.
    operation : str
        AWS operation named in an access-denied message.
    call : Callable[[], Any]
        provisioning operation to invoke.

    Returns
    -------
    Any
        value returned by `call`.

    Raises
    ------
    _ProvisionAccessDenied
        after printing the denial if `call` raises a ``ClientError`` in
        `_ACCESS_DENIED_CODES`.
    """
    from botocore.exceptions import ClientError

    from smolbench.evals._aws import error_code

    print(f"-> {label}")
    try:
        return call()
    except ClientError as err:
        if error_code(err) in _ACCESS_DENIED_CODES:
            print(access_denied_message(operation))
            raise _ProvisionAccessDenied(operation) from err
        raise


def main(argv: list[str] | None = None) -> int:
    """Provision the results bucket. Returns 1 when an AWS call was denied, else 0."""
    argparse.ArgumentParser(
        description=(
            "Idempotently provision the S3-backed replicate results bucket "
            "(smolbench.evals.results_store)."
        ),
    ).parse_args(argv)

    # Resolved at call time, or this script could provision one bucket while
    # the store writes to another.
    bucket, _base_prefix = resolve_results_location()

    # Lazy so offline tests can monkeypatch fresh_client before main looks it up.
    from smolbench.evals._aws import fresh_client

    print(f"Provisioning {bucket!r} in {REGION}...")
    s3 = fresh_client("s3", REGION)
    iam = fresh_client("iam")

    try:
        _run_step("ensure bucket", "s3:CreateBucket", lambda: ensure_bucket(s3, bucket, REGION))
        _run_step(
            "block public access",
            "s3:PutPublicAccessBlock",
            lambda: put_public_access_block(s3, bucket),
        )
        _run_step(
            "enable versioning", "s3:PutBucketVersioning", lambda: enable_versioning(s3, bucket)
        )
        policy_arn = _run_step(
            "ensure IAM policy", "iam:CreatePolicy", lambda: ensure_policy(iam, bucket, POLICY_NAME)
        )
        _run_step(
            "attach policy to group",
            "iam:AttachGroupPolicy",
            lambda: attach_policy_to_group(iam, policy_arn, GROUP_NAME),
        )
    except _ProvisionAccessDenied:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
