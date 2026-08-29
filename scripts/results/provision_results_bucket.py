"""Provision the S3-backed replicate results bucket.

This is the ADMIN-credentialed runbook counterpart to
``smolbench.evals.results_store`` (the S3ResultsStore/LocalResultsStore
read/write layer). It provisions the bucket the results store writes to when
``SMOLBENCH_RESULTS_S3`` is configured (see ``smolbench/evals/README.md``,
"Results store" section).

What it provisions
------------------
- The bucket itself (``BUCKET``, region ``REGION``), if it does not already
  exist.
- A public-access block with all four flags on (the bucket holds nothing
  that should ever be world-readable).
- Versioning (protects against an accidental overwrite or a destructive
  ``aws s3 sync --delete``; see ``enable_versioning``'s docstring for why
  this is cheap for a write-once workload).
- A managed IAM policy (``POLICY_NAME``) granting ``s3:ListBucket`` on the
  bucket and ``s3:GetObject``/``s3:PutObject``/``s3:DeleteObject`` on its
  contents, attached to the IAM group ``GROUP_NAME``.

Every step above is IDEMPOTENT and safe to re-run. A re-run of this
script against an already-provisioned bucket does nothing destructive,
and leaves the bucket in the same state. See each function's docstring
for exactly which "already exists" conditions count as success, and
which propagate as genuine errors.

Credentials
-----------
This script needs ADMIN credentials. The scoped ``smolbench-ec2-operators``
operator key used day-to-day by the eval drivers is deliberately EC2-only
(see ``smolbench/evals/_aws.py`` / ``ec2.py``). It cannot create buckets,
manage bucket policy, or touch IAM. Every AWS call this script makes will
come back ``AccessDenied`` under that key. Authenticate with an
admin-scoped profile before running it.

Runbook
-------
::

    .venv/bin/python scripts/results/provision_results_bucket.py

This script is never imported for its side effects. Nothing above runs at
import time.

Exit status
-----------
- ``0``: the bucket/policy/versioning/public-access-block steps all
  succeeded (or were already in place).
- Nonzero (``1``): an AWS call was denied (see Credentials above).

Not seeded
----------
This bucket is a clean, append-only EXPERIMENT LOG. The eval harness
writes to it through ``smolbench.evals.results_store`` (``S3ResultsStore``)
as it runs, never through this script. It is deliberately NOT seeded. IF
historical results are ever imported into this bucket, they MUST be
written THROUGH the store, not bulk-synced directly, so they land in the
CURRENT log layout::

    <experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml

never in the old repo-mirroring layout (a results directory's repo-relative
path used verbatim as its S3 key prefix), which nothing reads any more.
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
    """Parse this script's command line.

    Parameters
    ----------
    argv : list of str, optional
        Argument vector to parse. ``None`` (the default) parses
        ``sys.argv[1:]``, matching :meth:`argparse.ArgumentParser.parse_args`.

    Returns
    -------
    argparse.Namespace
        Empty. This is a provision-only script with no flags or
        positional arguments. The values that vary run-to-run are the
        module-level `BUCKET`/`REGION`/`POLICY_NAME`/`GROUP_NAME`
        constants, not anything read from ``argv``.

    Notes
    -----
    This function still runs the parse, rather than letting `main` skip
    straight to its body. That way, ``--help`` and an unrecognized/stray
    argument both behave the way every other script's ``ArgumentParser``
    does: printing usage and exiting, instead of this one script silently
    ignoring them.
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

    Parameters
    ----------
    bucket : str
        S3 bucket name the policy is scoped to.

    Returns
    -------
    dict
        An IAM policy document: ``s3:ListBucket`` on the bucket itself
        (this needs the bucket ARN, with no trailing ``/*``, to list
        keys), and ``s3:GetObject``/``s3:PutObject``/``s3:DeleteObject``
        on its contents (this needs the ``/*`` object-ARN wildcard). Key
        order is exactly ``Version`` -> ``Statement`` -> (``Effect``,
        ``Action``, ``Resource``) per statement. This is pinned
        deliberately, since a reviewer diffs the rendered ``json.dumps``
        output against this literal shape.
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
    """Build the message printed when ``operation`` comes back AccessDenied.

    Parameters
    ----------
    operation : str
        A short, human-identifiable label for the denied call, e.g.
        ``"s3:CreateBucket"`` or ``"iam:AttachGroupPolicy"``.

    Returns
    -------
    str
        A message naming ``operation``. It explains that the credentials
        in use are expired or deliberately scoped-out (the ``GROUP_NAME``
        operator key is EC2-only and cannot manage S3 or IAM). It also
        states that this script requires admin credentials.
    """
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

    Parameters
    ----------
    s3 : Any
        A boto3 S3 client (built by the caller, e.g. via
        ``smolbench.evals._aws.fresh_client("s3", REGION)``).
    bucket : str, optional
        Bucket name. Defaults to `BUCKET`.
    region : str, optional
        Region for ``CreateBucketConfiguration``. Defaults to `REGION`.

    Returns
    -------
    None

    Raises
    ------
    botocore.exceptions.ClientError
        Any S3 failure other than the two "already exists" codes
        tolerated below (see Notes). Most notably ``AccessDenied``, left
        for the caller (`main`, via `_run_step`) to catch and report.

    Notes
    -----
    ``us-west-2`` is not the grandfathered ``us-east-1`` default region,
    so ``CreateBucketConfiguration={"LocationConstraint": region}`` is
    REQUIRED on every call. ``create_bucket`` without it always targets
    ``us-east-1``, regardless of the client's own region binding.

    Two error codes are tolerated as idempotent success:

    - ``BucketAlreadyOwnedByYou``: the documented "you already created
      this" code.
    - ``BucketAlreadyExists``: ordinarily this means a DIFFERENT AWS
      account owns the name (bucket names are globally unique). For most
      bucket names, that would be a real conflict worth propagating. This
      code is tolerated here specifically because `BUCKET` embeds THIS
      account's id as a suffix (``smolbench-results-414266451290``). That
      naming convention was chosen precisely so this exact string cannot
      already be taken by anyone except this account. That makes
      "already exists" and "already exists, owned by you" the same
      event, in practice, for this one name.
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
    """Block all public access on ``bucket``.

    Parameters
    ----------
    s3 : Any
        A boto3 S3 client.
    bucket : str, optional
        Bucket name. Defaults to `BUCKET`.

    Returns
    -------
    None

    Raises
    ------
    botocore.exceptions.ClientError
        Any S3 failure, most notably ``AccessDenied``.

    Notes
    -----
    This function sets all four flags to ``True``. This bucket holds
    nothing that should ever be reachable by an unauthenticated request,
    so there is no partial setting worth exposing.
    ``put_public_access_block`` is a PUT (replace), so re-running this is
    idempotent, with no error-code handling needed.
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

    Parameters
    ----------
    s3 : Any
        A boto3 S3 client.
    bucket : str, optional
        Bucket name. Defaults to `BUCKET`.

    Returns
    -------
    None

    Raises
    ------
    botocore.exceptions.ClientError
        Any S3 failure, most notably ``AccessDenied``.

    Notes
    -----
    This is worth turning on specifically because of this bucket's access
    pattern: an eval driver writes a replicate ``rep_*.yaml`` exactly
    once, and never mutates it afterward (see
    ``smolbench.evals.replicates``). Under a write-once workload, keeping
    every version costs almost nothing, since ordinary operation never
    produces a second version of any key. But it turns an accidental
    overwrite (e.g. two drivers racing on the same replicate number), or a
    destructive ``aws s3 sync --delete``, from an unrecoverable loss into
    a fully recoverable one. Recovery uses ``list-object-versions`` plus
    a version-scoped ``get-object``. ``put_bucket_versioning`` is itself
    idempotent, so re-running this needs no error-code handling.
    """
    s3.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})


def ensure_policy(iam: Any, bucket: str = BUCKET, name: str = POLICY_NAME) -> str:
    """Create the managed policy granting read/write on ``bucket``, or reuse it.

    Parameters
    ----------
    iam : Any
        A boto3 IAM client (global service; built without a region binding).
    bucket : str, optional
        Bucket the policy is scoped to. Defaults to `BUCKET`.
    name : str, optional
        Policy name. Defaults to `POLICY_NAME`.

    Returns
    -------
    str
        The policy's ARN -- freshly created, or the existing policy's ARN
        when one by this name already exists.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than ``EntityAlreadyExists`` on
        ``create_policy`` -- most notably ``AccessDenied``.
    RuntimeError
        IAM reported ``EntityAlreadyExists`` for ``name``, but no policy by
        that name turned up in ``list_policies(Scope="Local")``. This
        surfaces a should-be-impossible race (e.g. the policy was deleted
        between the two calls) as a clear error, rather than letting a
        ``None`` ARN propagate silently into `attach_policy_to_group`.

    Notes
    -----
    On ``EntityAlreadyExists``, this function does NOT call
    ``create_policy_version`` to refresh the document to the current
    ``policy_document(bucket)``. IAM keeps only 5 versions of a managed
    policy. A new version on every run of an idempotent,
    expected-to-be-re-run script would silently burn that budget, until
    an old version could no longer be deleted to make room. This
    function's contract is create-or-reuse, not create-or-update. A
    genuine change to the policy document is a deliberate, manual
    ``aws iam create-policy-version`` operation, out of scope here.

    This function finds the existing policy's ARN via
    ``list_policies(Scope="Local")``, rather than constructing it from
    ``sts:GetCallerIdentity``'s account id. (``arn:aws:iam::{account}:policy/{name}``
    is a pure function of account id plus name, so that route would also
    work.) Building it from STS would need a SECOND client type threaded
    into this function, purely to learn the account id. That would also
    mean any test double for this function needs to fake TWO AWS
    services, instead of one. ``list_policies`` keeps everything on the
    single ``iam`` client this function already takes. It paginates
    manually via ``Marker``/``IsTruncated``, not ``iam.get_paginator``,
    again so a fake client only needs to implement the one plain method,
    not the paginator protocol.
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
    """Attach ``policy_arn`` to ``group``.

    Parameters
    ----------
    iam : Any
        A boto3 IAM client.
    policy_arn : str
        ARN of the policy to attach (the return value of `ensure_policy`).
    group : str, optional
        IAM group name. Defaults to `GROUP_NAME`.

    Returns
    -------
    None

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure, most notably ``AccessDenied``, or the group not
        existing.

    Notes
    -----
    No try/except is needed for "already attached".
    ``attach_group_policy`` is idempotent server-side. If the policy ARN
    is already attached to the group, the call succeeds silently, rather
    than raising. (Contrast ``_aws.ensure_instance_profile``'s
    ``add_role_to_instance_profile``, which DOES raise ``LimitExceeded``
    for an already-attached role. That is a different API, with a
    different idempotency contract, not a pattern this call shares.)
    """
    iam.attach_group_policy(GroupName=group, PolicyArn=policy_arn)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
class _ProvisionAccessDenied(Exception):
    """Signal an AccessDenied AWS call inside `main`'s step sequence.

    `_run_step` raises this. `main` catches it exactly once, at the
    bottom, so it can print nothing further and return a nonzero exit
    status, instead of letting the underlying `ClientError` traceback
    surface (see `access_denied_message`).
    """


def _run_step(label: str, operation: str, call):
    """Run one provisioning step with a progress line and AccessDenied handling.

    Parameters
    ----------
    label : str
        One-line, human-readable description printed before ``call`` runs,
        e.g. ``"ensure bucket"``.
    operation : str
        Short operation identifier passed to `access_denied_message` if
        ``call`` raises an AccessDenied-coded ``ClientError``, e.g.
        ``"s3:CreateBucket"``.
    call : Callable[[], Any]
        Zero-argument callable performing the actual AWS call.

    Returns
    -------
    Any
        Whatever ``call()`` returned.

    Raises
    ------
    _ProvisionAccessDenied
        ``call`` raised a ``botocore.exceptions.ClientError`` whose code is
        in `_ACCESS_DENIED_CODES`. The denial message has already been
        printed by the time this is raised.
    Exception
        Any other exception ``call`` raises, propagated unchanged.

    Notes
    -----
    This function imports ``botocore.exceptions.ClientError`` lazily
    (inside the function body). This matches this module's and
    ``_aws.py``'s house rule: nothing reachable at import time requires
    the AWS SDK to be installed.
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
    """Provision the results bucket.

    Parameters
    ----------
    argv : list of str, optional
        Argument vector; forwarded to `parse_args`. ``None`` parses
        ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit status; see the module docstring's "Exit status" section.
        ``0`` on success (the bucket/policy/versioning/public-access-block
        steps all succeeded, or were already in place). ``1`` if any AWS
        call was denied.

    Notes
    -----
    This function builds exactly two clients, both fresh (via
    ``smolbench.evals._aws.fresh_client``, never a cached/default-session
    client; see that function's docstring for why): one S3 client bound to
    `REGION`, and one IAM client (global service, no region). It imports
    both boto3 and botocore only inside this function and the functions
    it calls. Nothing at this module's import time requires either.
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
