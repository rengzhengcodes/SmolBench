"""Provision the S3-backed replicate results bucket with ADMIN credentials.

Use the configured bucket, block public access, enable versioning, and attach
the operator policy; every step is idempotent and nothing runs at import time.
Versioning makes deletes recoverable; denied calls exit 1 because keys are EC2-only.
The bucket is not seeded: historical imports must go through ``S3ResultsStore`` instead.
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

#: Access-denied `ClientError` codes.
_ACCESS_DENIED_CODES = frozenset(
    {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation"}
)


def policy_document(bucket: str) -> dict:
    """Build the IAM policy document granting read/write on ``bucket``.

    ListBucket needs the bucket ARN; object actions need ``/*``. Key order is
    pinned because reviewers diff the rendered ``json.dumps`` against this shape.

    Parameters
    ----------
    bucket : str
        Bucket receiving access.

    Returns
    -------
    dict
        Read/write IAM policy.
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


def ensure_bucket(s3: Any, bucket: str, region: str = REGION) -> None:
    """Create ``bucket`` in ``region``, tolerating "already provisioned".

    Supply the location constraint because create_bucket otherwise targets us-east-1.

    Parameters
    ----------
    s3 : Any
        S3 client.
    bucket : str
        Bucket name.
    region : str, optional
        Location-constraint region.
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

    This is a PUT replacement, so re-running is idempotent without error-code handling.

    Parameters
    ----------
    s3 : Any
        S3 client.
    bucket : str
        Bucket name.
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

    Versioning makes accidental overwrites and deletes recoverable.

    Parameters
    ----------
    s3 : Any
        S3 client.
    bucket : str
        Bucket name.
    """
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})


def ensure_policy(iam: Any, bucket: str, name: str = POLICY_NAME) -> str:
    """Create the managed policy granting read/write on ``bucket``, or reuse it.

    Reuse rather than update to preserve IAM's five-version policy budget.

    Parameters
    ----------
    iam : Any
        IAM client.
    bucket : str
        Bucket receiving access.
    name : str, optional
        Policy name.

    Returns
    -------
    str
        Created or existing policy ARN.
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

    No "already attached" handling is needed because ``attach_group_policy`` is idempotent.

    Parameters
    ----------
    iam : Any
        IAM client.
    policy_arn : str
        Managed policy ARN.
    group : str, optional
        Receiving IAM group.
    """
    iam.attach_group_policy(GroupName=group, PolicyArn=policy_arn)


class _ProvisionAccessDenied(Exception):
    """Raised by `_run_step` on a denied call, so `main` exits 1 with no traceback."""


def _run_step(label: str, operation: str, call: Callable[[], Any]) -> Any:
    """Run one provisioning step with a progress line and AccessDenied handling.

    Parameters
    ----------
    label : str
        Progress label.
    operation : str
        AWS operation for denial output.
    call : Callable[[], Any]
        Provisioning operation.

    Returns
    -------
    Any
        `call` result.

    Raises
    ------
    _ProvisionAccessDenied
        A denied `ClientError` from `call`.
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

    # Resolve at call time so provisioning matches the store destination.
    bucket, _base_prefix = resolve_results_location()

    # Delay AWS import so offline tests can patch fresh_client.
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
