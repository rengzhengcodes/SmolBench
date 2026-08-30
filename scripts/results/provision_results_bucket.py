"""Provision the S3-backed replicate results bucket (needs ADMIN credentials).

The runbook counterpart to ``smolbench.evals.results_store``, which writes here
when ``SMOLBENCH_RESULTS_S3`` is configured. Provisions `BUCKET` in `REGION`, a
public-access block with all four flags on, versioning, and a managed IAM policy
(`POLICY_NAME`) granting ``s3:ListBucket`` on the bucket plus
``s3:GetObject``/``s3:PutObject``/``s3:DeleteObject`` on its contents, attached
to IAM group `GROUP_NAME`. Every step is IDEMPOTENT; nothing runs at import
time::

    .venv/bin/python scripts/results/provision_results_bucket.py

The scoped ``smolbench-ec2-operators`` key the eval drivers use day-to-day is
deliberately EC2-only, so every AWS call here returns ``AccessDenied`` under it.
Exit status is ``0`` when every step succeeded or was already in place, ``1``
when a call was denied.

The bucket is a clean, append-only EXPERIMENT LOG written by the harness through
``S3ResultsStore``, and deliberately NOT seeded. Any historical import MUST go
THROUGH the store, so it lands in the CURRENT layout
``<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml`` and never in the old
repo-mirroring layout, which nothing reads any more.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BUCKET = "smolbench-results-414266451290"
REGION = "us-west-2"
POLICY_NAME = "SmolbenchResultsBucketRW"
GROUP_NAME = "smolbench-ec2-operators"

#: `ClientError` codes meaning "the caller's credentials are not allowed
#: to do this". `_run_step` handles these uniformly; see its docstring.
_ACCESS_DENIED_CODES = frozenset(
    {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation"}
)


# ---------------------------------------------------------------------------
# Pure functions (no AWS, no I/O)
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse this script's command line (``None`` parses ``sys.argv[1:]``).

    Returns an empty namespace: there are no flags, and what varies run-to-run
    is the module-level `BUCKET`/`REGION`/`POLICY_NAME`/`GROUP_NAME`. The parse
    still runs so ``--help`` and a stray argument behave as elsewhere.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Idempotently provision the S3-backed replicate results bucket "
            "(smolbench.evals.results_store)."
        ),
    )
    return parser.parse_args(argv)


def policy_document(bucket: str) -> dict:
    """Build the IAM policy document granting read/write on ``bucket``.

    ``s3:ListBucket`` is scoped to the bucket ARN (no trailing ``/*``, which is
    what listing keys requires); the object actions to the ``/*`` object-ARN
    wildcard. Key order is pinned deliberately: a reviewer diffs the rendered
    ``json.dumps`` output against this literal shape.
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
# AWS steps. Each one takes an already-built client as its first
# parameter, so each is testable against a fake client with no AWS SDK
# installed. None of these build a client themselves, and none is called
# at import time.
# ---------------------------------------------------------------------------
def ensure_bucket(s3: Any, bucket: str = BUCKET, region: str = REGION) -> None:
    """Create ``bucket`` in ``region``, tolerating "already provisioned".

    ``CreateBucketConfiguration={"LocationConstraint": region}`` is REQUIRED on
    every call: without it ``create_bucket`` always targets ``us-east-1``,
    whatever the client's own region binding. ``BucketAlreadyOwnedByYou`` and
    ``BucketAlreadyExists`` both count as idempotent success; the latter
    ordinarily means a DIFFERENT account owns the globally-unique name, but
    `BUCKET` embeds this account's id as a suffix precisely so that cannot
    happen here.

    Raises
    ------
    botocore.exceptions.ClientError
        Any other S3 failure -- notably ``AccessDenied``, which `main` reports
        via `_run_step`.
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


def put_public_access_block(s3: Any, bucket: str = BUCKET) -> None:
    """Block all public access on ``bucket``, setting all four flags to True.

    A PUT (replace), so re-running is idempotent with no error-code handling.

    Raises
    ------
    botocore.exceptions.ClientError
        Any S3 failure, most notably ``AccessDenied``.
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


def enable_versioning(s3: Any, bucket: str = BUCKET) -> None:
    """Enable S3 versioning on ``bucket``.

    A replicate ``rep_*.yaml`` is written exactly once and never mutated (see
    ``smolbench.evals.replicates``), so keeping every version costs almost
    nothing while making an accidental overwrite (two drivers racing on one
    replicate number) or a destructive ``aws s3 sync --delete`` recoverable.
    ``put_bucket_versioning`` is itself idempotent.

    Raises
    ------
    botocore.exceptions.ClientError
        Any S3 failure, most notably ``AccessDenied``.
    """
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})


def ensure_policy(iam: Any, bucket: str = BUCKET, name: str = POLICY_NAME) -> str:
    """Create the managed policy granting read/write on ``bucket``, or reuse it.

    Create-or-REUSE, not create-or-update: refreshing the document via
    ``create_policy_version`` on every run of a re-runnable script would
    silently burn IAM's budget of 5 versions per managed policy, so a genuine
    change is a deliberate manual ``aws iam create-policy-version``. The
    existing ARN comes from ``list_policies(Scope="Local")``, paginated by hand
    via ``Marker``/``IsTruncated``, so everything stays on the one ``iam``
    client (a global service, built without a region).

    Returns
    -------
    str
        ARN of the created or already-existing policy.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than ``EntityAlreadyExists`` on
        ``create_policy`` -- most notably ``AccessDenied``.
    RuntimeError
        IAM reported ``EntityAlreadyExists`` but no policy by that name turned
        up in ``list_policies`` -- rather than let a ``None`` ARN propagate into
        `attach_policy_to_group`.
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

    No "already attached" handling is needed: ``attach_group_policy`` is
    idempotent server-side and succeeds silently (unlike
    ``_aws.ensure_instance_profile``'s ``add_role_to_instance_profile``, which
    DOES raise ``LimitExceeded``).

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure, most notably ``AccessDenied`` or a missing group.
    """
    iam.attach_group_policy(GroupName=group, PolicyArn=policy_arn)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
class _ProvisionAccessDenied(Exception):
    """Signal an AccessDenied AWS call inside `main`'s step sequence.

    `_run_step` prints the denial and raises this; `main` catches it once, so it
    returns a nonzero exit status instead of a `ClientError` traceback.
    """


def _run_step(label: str, operation: str, call):
    """Run one provisioning step with a progress line and AccessDenied handling.

    ``ClientError`` is imported lazily, per this module's and ``_aws.py``'s
    house rule that nothing reachable at import time requires the AWS SDK.

    Parameters
    ----------
    label : str
        Printed before ``call`` runs.
    operation : str
        Identifier named in `access_denied_message`, e.g. ``"s3:CreateBucket"``.
    call : callable
        Zero-argument; its return value is passed through.

    Raises
    ------
    _ProvisionAccessDenied
        ``call`` raised a ``ClientError`` whose code is in
        `_ACCESS_DENIED_CODES`, after printing the denial; any other exception
        propagates unchanged.
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
    """Provision the results bucket and return an exit status.

    ``0`` when every step succeeded or was already in place, ``1`` when an AWS
    call was denied. Builds exactly two clients via
    ``smolbench.evals._aws.fresh_client`` (never a cached/default-session one):
    S3 bound to `REGION`, and IAM (global).
    """
    parse_args(argv)

    from smolbench.evals._aws import fresh_client

    print(f"Provisioning {BUCKET!r} in {REGION}...")
    s3 = fresh_client("s3", REGION)
    iam = fresh_client("iam")

    try:
        _run_step("ensure bucket", "s3:CreateBucket", lambda: ensure_bucket(s3, BUCKET, REGION))
        _run_step(
            "block public access",
            "s3:PutPublicAccessBlock",
            lambda: put_public_access_block(s3, BUCKET),
        )
        _run_step(
            "enable versioning", "s3:PutBucketVersioning", lambda: enable_versioning(s3, BUCKET)
        )
        policy_arn = _run_step(
            "ensure IAM policy", "iam:CreatePolicy", lambda: ensure_policy(iam, BUCKET, POLICY_NAME)
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
