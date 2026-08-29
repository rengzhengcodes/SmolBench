"""
Share AWS provisioning primitives between the SageMaker and EC2 providers.

Used by :mod:`smolbench.evals.providers.aws` (SageMaker) and
:mod:`smolbench.evals.providers.ec2` (self-provisioned EC2 Spot). Both provider
modules talk to IAM, EC2, SageMaker, and S3 to stand up an
inference endpoint. This module holds the shared primitives: a fresh-Session
client constructor, an ``Error.Code`` extractor, an assume-role trust-policy
dict, a poll-until-ready loop, and a best-effort teardown sweep. Each
provider wires its own model- or endpoint-specific logic on top.

The two providers' endpoint lifecycles use DELIBERATELY different shapes.
They do not diverge by accident:

=====================  =====================================================
aws.py (SageMaker)     ec2.py (EC2 Spot)
=====================  =====================================================
``provision_endpoint``  ``provision_spot_instance`` / ``serve_model``
is a PER-MODEL          are split: one instance is provisioned ONCE per
``@contextmanager``     experiment (idempotent, reattach-or-launch), and
that deploys, waits,    ``serve_model`` only ever SWAPS which model that
yields, and ALWAYS      shared instance serves. ``serve_model`` deliberately
tears down (success,    tears down NOTHING on exit -- an on-instance idle
error, or Ctrl-C) --    watchdog and an absolute max-lifetime ``shutdown``
because a SageMaker     backstop cover abandonment instead, since the
endpoint bills per       instance (unlike a SageMaker endpoint) is meant to
hour until deleted.      outlive any single archetype section.
=====================  =====================================================

This module has no shared ``provision -> poll -> yield -> teardown``
framework. It offers only the smaller pieces (``poll_until``,
``best_effort_teardown``, and so on). Each lifecycle shape above has exactly
ONE consumer. A framework built for a single call site is pure indirection:
it would need enough hooks to reproduce both shapes anyway, and at that
point it is just this module's functions with extra ceremony. This module
shares only the small, genuinely-repeated pieces instead: client
construction, error-code parsing, the poll loop, the trust policy, the
teardown sweep. That gives the deduplication benefit without inventing a
lifecycle abstraction that neither caller asked for.

Both call sites share one convention: import boto3 and botocore LAZILY,
inside each function that needs them, never at module scope. Neither
provider's pure-inference path (querying an already-running endpoint) needs
AWS credentials or the SDK installed. This module must not force that
dependency on a caller merely by being imported.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypedDict, TypeVar

#: Generic success-value type for `poll_until` -- whatever `check` returns.
T = TypeVar("T")


def fresh_client(service: str, region: Optional[str] = None):
    """Build a boto3 client from a brand-new :class:`boto3.session.Session`.

    This is deliberately NOT ``boto3.client(service, ...)``, which resolves
    against the process-wide DEFAULT session and caches credentials at first
    resolve. It also does not reuse a client across calls. A fresh
    ``Session`` per call picks up a rotated ``~/.aws/credentials`` file (this
    repo's IdP-issued sessions last around 12h) on the very next call. Without
    this, calls raise ``RequestExpired``/``ExpiredToken`` until the process
    (or kernel) restarts. Both provider modules' original per-call
    ``boto3.session.Session().client(...)`` constructions had already
    independently arrived at this same fix. This function is that fix,
    shared.

    Parameters
    ----------
    service : str
        A boto3 service name, e.g. ``"ec2"``, ``"iam"``, ``"s3"``, ``"ssm"``.
    region : str, optional
        AWS region to bind the client to. ``None`` (the default) lets boto3
        fall back to its own resolution order (``AWS_REGION``/``AWS_DEFAULT_
        REGION``/the shared config file). Callers use this for IAM, a global
        (non-regional) service.

    Returns
    -------
    Any
        A boto3 client for ``service``, bound to a Session constructed fresh
        for this call.

    Notes
    -----
    Imports ``boto3`` lazily (see the module docstring). A call to this
    function is itself the opt-in that requires boto3 to be installed and
    credentials to be resolvable. Nothing at import time of this module
    requires either.
    """
    import boto3  # lazy: keep the inference paths boto3-free

    return boto3.session.Session().client(service, region_name=region)


def error_code(err: Exception) -> str:
    """Extract the ``Error.Code`` from a boto3/botocore exception.

    Parameters
    ----------
    err : Exception
        Typically a ``botocore.exceptions.ClientError``, but this function
        accepts any exception. One that lacks a ``.response`` dict (e.g. a
        plain ``Exception`` raised by test doubles, or a non-ClientError
        failure) degrades to ``""`` rather than raising. Every call site
        uses this return value purely as a string to compare against a
        known error code.

    Returns
    -------
    str
        The value at ``err.response["Error"]["Code"]``, or ``""`` when
        ``err`` has no ``.response`` attribute, or that attribute is missing
        the expected nested keys.
    """
    return getattr(err, "response", {}).get("Error", {}).get("Code", "")


def assume_role_trust_policy(service: str) -> Dict[str, Any]:
    """Build an EC2-style AssumeRole trust policy for one AWS service principal.

    Both callers need this document: one for
    ``"sagemaker.amazonaws.com"`` (aws.py's SageMaker execution role), and
    one for ``"ec2.amazonaws.com"`` (ec2.py's instance-profile role). The two
    documents differ only in the ``Principal.Service`` value, so this
    function takes that value as a parameter instead of duplicating the
    document.

    Parameters
    ----------
    service : str
        The AWS service principal allowed to assume the role, e.g.
        ``"ec2.amazonaws.com"`` or ``"sagemaker.amazonaws.com"``.

    Returns
    -------
    Dict[str, Any]
        An IAM trust-policy document permitting ``sts:AssumeRole`` for
        ``service``, with a fixed key order (``Version`` -> ``Statement`` ->
        ``Effect``/``Principal``/``Action`` within each statement).
        Callers pin the exact ``AssumeRolePolicyDocument`` JSON string, so
        the key order is stable.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": service},
                "Action": "sts:AssumeRole",
            }
        ],
    }


def ensure_sagemaker_execution_role(role_name: str) -> str:
    """Return the SageMaker execution role ARN, creating it if absent.

    This function is parametrized on the role name so
    both a SageMaker deployment path and any future caller can name their
    own role. The IAM client comes from ``fresh_client("iam")`` (a brand-new
    boto3 Session per call), so a rotated
    ``~/.aws/credentials`` file is actually picked up instead of silently
    signing with stale, expired credentials (see ``fresh_client``'s
    docstring for the full rationale).

    Parameters
    ----------
    role_name : str
        IAM role name to create-or-fetch, e.g. ``SAGEMAKER_EXEC_ROLE_NAME``.

    Returns
    -------
    str
        The role's ARN: freshly created, or the existing role's ARN when
        one by this name already exists.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than the role already existing (e.g. missing
        ``iam:CreateRole``/``iam:AttachRolePolicy`` permission).

    Notes
    -----
    On the CREATE path this sleeps 10 seconds (``time.sleep(10)``) after
    ``attach_role_policy`` and before
    returning. The sleep lets IAM's eventual consistency catch up before
    SageMaker tries to assume the role. The already-exists path skips the
    sleep, since that role has presumably already propagated.
    """
    import json

    iam = fresh_client("iam")
    trust = assume_role_trust_policy("sagemaker.amazonaws.com")
    try:
        arn = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust),
        )["Role"]["Arn"]
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
        )
        time.sleep(10)  # let the new role propagate before SageMaker assumes it
        return arn
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName=role_name)["Role"]["Arn"]


def ensure_instance_profile(role_name: str, bucket: str, propagation_sleep_s: int) -> str:
    """Return the EC2 instance-profile name for the S3 model cache.

    Creates the role and profile if they are absent. ``EC2_INSTANCE_ROLE_NAME``
    and ``_IAM_PROPAGATION_SLEEP_S`` are threaded through as parameters, so
    this function carries no ec2.py-specific global state. The role grants
    two things: (a) read/write scoped to ``bucket``, and (b) SSM core, which
    doubles as the break-glass shell for a box launched with no SSH key.

    Parameters
    ----------
    role_name : str
        IAM role AND instance-profile name (one name for
        both), e.g. ``EC2_INSTANCE_ROLE_NAME``.
    bucket : str
        S3 bucket name the role's inline policy is scoped to (list + get/put
        object, nothing else, nothing broader).
    propagation_sleep_s : int
        Seconds to sleep after creating the role/profile, to let IAM's
        eventual consistency settle before ``RunInstances`` references the
        profile. This function sleeps only when it actually freshly created
        something (see the ``created`` flag below); an already-existing
        role/profile is presumed already propagated.

    Returns
    -------
    str
        ``role_name`` itself, returned for call-site convenience.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than the specific "already exists"/"limit
        exceeded" conditions this function is designed to tolerate (see
        Notes).

    Notes
    -----
    This function swallows four ``ClientError`` codes, each at the exact
    call that can raise it, because each means "this resource already
    exists in the shape we want" rather than a genuine failure:

    - ``create_role`` -> ``EntityAlreadyExists`` (role already created by an
      earlier run).
    - ``create_instance_profile`` -> ``EntityAlreadyExists`` (ditto, for the
      profile).
    - ``add_role_to_instance_profile`` -> ``LimitExceeded`` (AWS's error code
      for "this role is already attached to this profile" -- a profile may
      only ever hold one role, so re-attaching the same one is a no-op, not
      a genuine limit).

    ``put_role_policy`` is NOT wrapped in a try/except: it overwrites
    idempotently (no "already exists" failure mode). This is exactly why the
    grant tracks ``bucket`` even when the role predates this call with a
    different bucket.

    The ``created`` flag is set to True when EITHER the role or the profile
    is freshly made, not just one specific one. This function spends
    ``propagation_sleep_s`` if anything at all was new, since either
    omission could leave an IAM object that ``RunInstances`` is about to
    reference not yet visible.
    """
    import json as _json

    from botocore.exceptions import ClientError

    iam = fresh_client("iam")
    name = role_name
    trust = assume_role_trust_policy("ec2.amazonaws.com")
    created = False
    try:
        iam.create_role(RoleName=name, AssumeRolePolicyDocument=_json.dumps(trust))
        created = True
    except ClientError as err:
        if error_code(err) == "AccessDenied":
            # Scoped credentials (e.g. the EC2-only operator key) cannot
            # manage IAM at all. create_role is the first IAM call, so it
            # fails here even when the role/profile already exist from a
            # prior admin-credentialed run (the common case: the name is
            # fixed). Proceed optimistically. If the profile genuinely does
            # not exist, RunInstances fails cleanly when it references it.
            logging.info(
                f"ensure_instance_profile: iam:CreateRole denied for scoped "
                f"credentials; assuming role/profile {name!r} already exists"
            )
            return name
        if error_code(err) != "EntityAlreadyExists":
            raise
    # put_role_policy overwrites idempotently, so the grant tracks the bucket.
    iam.put_role_policy(
        RoleName=name,
        PolicyName="smolbench-s3-model-cache",
        PolicyDocument=_json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket"],
                        "Resource": f"arn:aws:s3:::{bucket}",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["s3:GetObject", "s3:PutObject"],
                        "Resource": f"arn:aws:s3:::{bucket}/*",
                    },
                ],
            }
        ),
    )
    iam.attach_role_policy(
        RoleName=name,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    )
    try:
        iam.create_instance_profile(InstanceProfileName=name)
        created = True
    except ClientError as err:
        if error_code(err) != "EntityAlreadyExists":
            raise
    try:
        iam.add_role_to_instance_profile(InstanceProfileName=name, RoleName=name)
    except ClientError as err:
        if error_code(err) != "LimitExceeded":  # role already attached
            raise
    if created:
        time.sleep(propagation_sleep_s)  # let IAM propagate before RunInstances references it
    return name


def poll_until(
    check: Callable[[], Optional[T]],
    *,
    timeout_s: float,
    interval_s: float,
    on_timeout: Callable[[], Exception],
) -> T:
    """Poll in a loop, with a fixed, load-bearing ordering.

    Callers wait for a public IP, a control agent, a
    healthy model, or an ``InService`` SageMaker endpoint. ``check`` does one
    poll attempt and returns either a non-None success value or ``None`` to
    keep waiting. ``check``
    may itself raise, to abort the loop early for an unrecoverable
    condition (e.g. "the instance is terminated, waiting further is
    pointless").

    Parameters
    ----------
    check : Callable[[], Optional[T]]
        Called with no arguments once per iteration. A non-``None`` return
        ends the loop successfully with that value. ``check`` may raise any
        exception to abort the loop immediately; the exception propagates to
        ``poll_until``'s caller unchanged. Every migrated loop uses this to
        fail fast on a condition no amount of further waiting would fix,
        e.g. a spot instance reclaimed mid-wait.
    timeout_s : float
        Overall deadline, in seconds, measured from the first call to this
        function (NOT from the first ``check()`` call, though in practice
        the two are microseconds apart).
    interval_s : float
        Seconds slept between poll attempts, via ``time.sleep``.
    on_timeout : Callable[[], Exception]
        Called with no arguments once the deadline has passed with no
        successful ``check()``. It must RETURN (not raise) an ``Exception``
        instance, which ``poll_until`` then raises. This is deferred, rather
        than a fixed message, so the exception can carry state gathered
        during the loop's last ``check()`` call. For example, ``ec2.py``'s
        model-readiness wait closes over the last polled status to describe
        the container's state in its ``TimeoutError``.

    Returns
    -------
    T
        Whatever ``check()`` returned as its non-``None`` success value.

    Raises
    ------
    Exception
        Whatever ``check()`` itself raised, propagated verbatim; or whatever
        ``on_timeout()`` returns, once the deadline has passed.

    Notes
    -----
    This function has a load-bearing ordering contract. Every wait loop
    built on it must match it exactly:

    1. Call ``check()``.
    2. If it returned non-``None``, return that value immediately. The
       deadline is NEVER consulted on a successful attempt, so a check that
       happens to succeed exactly when time.time() equals (or has just
       passed) the deadline still returns normally rather than raising.
    3. If it raised, the exception propagates immediately (no sleep, no
       deadline check).
    4. Otherwise (``None``, no exception): check the deadline. If
       ``time.time() > deadline``, raise ``on_timeout()``.
    5. Otherwise, ``time.sleep(interval_s)`` and loop back to step 1.

    This function performs no I/O of its own beyond ``time.time()``/``time.
    sleep()``. All actual polling (HTTP requests, ``DescribeInstances``
    calls, etc.) lives in the caller-supplied ``check``.
    """
    deadline = time.time() + timeout_s
    while True:
        result = check()
        if result is not None:
            return result
        if time.time() > deadline:
            raise on_timeout()
        time.sleep(interval_s)


def best_effort_teardown(
    steps: Sequence[Tuple[str, Callable[[], Any]]], *, log_prefix: str
) -> None:
    """Run every teardown step, logging (never raising) each one's outcome.

    This function takes an arbitrary
    sequence of (label, callable) steps, so any teardown sequence (e.g. a
    SageMaker endpoint/endpoint-config/model triple, in a fixed order) can
    reuse the same "never let cleanup mask the real error" behavior.

    Parameters
    ----------
    steps : Sequence[Tuple[str, Callable[[], Any]]]
        ``(label, call)`` pairs, in the order to attempt them. Every step
        runs regardless of whether an earlier one succeeded or failed; this
        function never short-circuits.
    log_prefix : str
        Prefix for each log line, e.g. the caller's function name, so
        interleaved logs from multiple teardown sites stay attributable.

    Returns
    -------
    None

    Notes
    -----
    Callers typically call this function from a ``finally`` block guarding a
    ``yield`` (a ``@contextlib.contextmanager`` body). Teardown running
    there must NEVER raise and mask whatever exception (or successful
    completion) the ``with`` body produced. Accordingly, this function
    catches every step's exception with a bare ``except Exception`` and logs
    it at INFO level, rather than re-raising or escalating it. A step that
    fails leaves its resource behind for manual/next-run cleanup, rather
    than aborting the remaining steps or the caller's own exception
    propagation.
    """
    for label, call in steps:
        try:
            call()
            logging.info(f"{log_prefix}: torn down {label}")
        except Exception as exc:  # noqa: BLE001 -- teardown must never mask the caller's exception
            logging.info(f"{log_prefix}: teardown skip {label}: {type(exc).__name__}: {exc}")


class _DeploySpecRequired(TypedDict):
    """Hold the one field every deploy spec must have; see `DeploySpec`."""

    #: HuggingFace repo id to deploy/serve, e.g.
    #: ``"Qwen/Qwen2.5-1.5B-Instruct"``. Both backends consume it: SageMaker
    #: puts it in the container's ``HF_MODEL_ID`` env var
    #: (``aws.provision_endpoint``); EC2/vLLM passes it as the control
    #: agent's ``hf_model_id`` payload field, which becomes vLLM's
    #: ``--model`` flag (``ec2.serve_model`` / the control agent's ``_serve``
    #: in ``payloads/agent.py.txt``).
    hf_model_id: str


class DeploySpec(_DeploySpecRequired, total=False):
    """Hold one model's deployment parameters, in a shape shared by both backends.

    ``hf_model_id`` (see `_DeploySpecRequired`) is the only field every spec
    must supply. Everything else is backend-specific and optional.
    `SAGEMAKER_SPEC_KEYS` / `EC2_SPEC_KEYS` enumerate which optional fields
    each backend actually reads via ``.get(...)``, with a documented default
    for every one it does not require. This class is modeled as two classes
    (a ``total=True`` base carrying the required field, subclassed
    ``total=False`` for the rest) rather than a single class with
    ``typing.Required``/``NotRequired`` annotations. That split is already
    the idiomatic pattern for "one required field, many optional ones"
    TypedDicts.
    """

    #: Tensor-parallel degree. SageMaker reads it as the
    #: ``SM_VLLM_TENSOR_PARALLEL_SIZE`` env var (``spec.get("tp", 1)``).
    #: EC2/vLLM reads it as the control agent's ``tp`` payload field, which
    #: becomes vLLM's ``--tensor-parallel-size`` (``spec.get("tp", 1)``).
    tp: int
    #: SageMaker ONLY: the ``InstanceType`` for the endpoint's production
    #: variant (e.g. ``"ml.p5.48xlarge"``); read via ``spec["instance_type"]``.
    #: SageMaker specs require this field, though it is not required across
    #: both backends: EC2 specs have no use for it, since the shared
    #: instance type is chosen once at ``provision_spot_instance`` time, not
    #: per model.
    instance_type: str
    #: SageMaker ONLY: extra container environment variables merged into the
    #: DLC's base ``Environment`` dict (e.g. ``{"HF_TOKEN": "hf_..."}`` for a
    #: gated repo); read via ``spec.get("env", {})``.
    env: Dict[str, str]
    #: SageMaker ONLY: override for the default vLLM DLC image URI; read via
    #: ``spec.get("image", SAGEMAKER_VLLM_DLC)``.
    image: str
    #: EC2/vLLM ONLY: context window vLLM launches with (``--max-model-
    #: len``); also doubles as ``get_model_context_length``'s soft token
    #: guard. Read via ``spec.get("max_model_len", EC2_CONTEXT_LENGTH)``.
    max_model_len: int
    #: EC2/vLLM ONLY: extra CLI flags appended verbatim to the ``docker run``
    #: vLLM command (e.g. ``["--trust-remote-code"]``,
    #: ``["--reasoning-parser", "qwen3"]``); read via ``spec.get("vllm_args",
    #: [])``.
    vllm_args: List[str]
    #: EC2/vLLM ONLY: a system prompt the provider layer injects ahead of
    #: every user prompt for this model (e.g. Nemotron-Ultra's "detailed
    #: thinking on" CoT toggle); read via ``spec.get("system_prompt")``. This
    #: field, uniquely, has no non-None default: absence means "no
    #: provider-injected system prompt".
    system_prompt: str
    #: EC2/vLLM ONLY: repo id to load this model's TOKENIZER from, when that
    #: differs from ``hf_model_id``. ``smolbench.evals.tokenization.for_model``
    #: reads it via ``spec.get("tokenizer_hf_id")`` and falls back to
    #: ``hf_model_id`` when absent (the normal case). This field exists
    #: because a quantized redistribution occasionally ships weights without
    #: a ``tokenizer.json``, while its unquantized base repo has one. The
    #: tokenizer is identical either way, so pointing at the base repo costs
    #: nothing and keeps token-matched prompts (the induction noise arm)
    #: buildable for that checkpoint.
    tokenizer_hf_id: str
    #: EC2/vLLM ONLY: LoRA adapters to stage from S3 and register with vLLM,
    #: as ``[{"name": ..., "s3": "<prefix>/<base_key>[/<sub>]", "region": ...}]``.
    #: ``ec2.serve_model`` consumes this field and passes the staging plan to
    #: the on-box agent. Base-only studies never set it.
    adapters: list


#: Keys `aws.SAGEMAKER_DEPLOY_SPECS` entries may use. Verified against the
#: dict literal (aws.py's ``SAGEMAKER_DEPLOY_SPECS``) and every place a spec
#: is read (``provision_endpoint``). ``hf_model_id``/``instance_type`` are
#: read unconditionally (``spec["..."]``), so they are effectively required
#: by any entry actually deployed. ``tp``/``env``/``image`` are read via
#: ``.get(...)`` with documented defaults.
SAGEMAKER_SPEC_KEYS: frozenset = frozenset(
    {"hf_model_id", "tp", "instance_type", "env", "image"}
)
#: Keys `ec2.EC2_DEPLOY_SPECS` entries may use. Verified against the dict
#: literal (ec2.py's ``EC2_DEPLOY_SPECS``) and every place a spec is read
#: (``get_model_context_length``, ``serve_model``, ``_system_prompt``).
#: ``hf_model_id`` is read unconditionally (``spec["hf_model_id"]``).
#: ``tp``/``max_model_len``/``vllm_args``/``system_prompt`` are all read via
#: ``.get(...)`` with documented defaults. ``tokenization.for_model``, one
#: module over, reads ``tokenizer_hf_id`` the same way.
EC2_SPEC_KEYS: frozenset = frozenset(
    {
        "hf_model_id",
        "tp",
        "max_model_len",
        "vllm_args",
        "system_prompt",
        "adapters",
        "tokenizer_hf_id",
    }
)
