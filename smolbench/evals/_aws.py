"""
Shared AWS provisioning primitives for :mod:`smolbench.evals.aws` (SageMaker)
and :mod:`smolbench.evals.ec2` (self-provisioned EC2 Spot).

Both provider modules need to talk to IAM/EC2/SageMaker/S3 to stand up an
inference endpoint, and until this module existed they each carried their own
copy of the same handful of primitives (a fresh-Session client constructor, an
``Error.Code`` extractor, an assume-role trust-policy dict, a poll-until-ready
loop, a best-effort teardown sweep). This module is the single copy; each
provider wires its own model/endpoint-specific logic on top.

Lifecycle correspondence -- the two providers' endpoint lifecycles are
DELIBERATELY different shapes, not accidentally divergent:

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

Why there is no shared ``provision -> poll -> yield -> teardown`` framework
here, only the smaller pieces (``poll_until``, ``best_effort_teardown``,
etc.): each lifecycle shape above has exactly ONE consumer. A framework
generalized over a single call site is pure indirection -- it would need
enough hooks to reproduce both shapes anyway, at which point it is just this
module's functions with extra ceremony. Sharing the small, genuinely-repeated
pieces (client construction, error-code parsing, the poll loop, the trust
policy, the teardown sweep) gets the deduplication benefit without inventing
a lifecycle abstraction neither caller asked for.

Convention preserved from both call sites: boto3/botocore are imported
LAZILY, inside each function that needs them, never at module scope. Neither
provider's pure-inference path (querying an already-running endpoint) needs
AWS credentials or the SDK installed, and this module must not force that
dependency on them merely by being imported.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypedDict, TypeVar

#: Generic success-value type for `poll_until` -- whatever `check` returns.
T = TypeVar("T")


def fresh_client(service: str, region: Optional[str] = None):
    """Builds a boto3 client from a brand-new :class:`boto3.session.Session`.

    Deliberately NOT ``boto3.client(service, ...)`` (which resolves against
    the process-wide DEFAULT session, caching credentials at first resolve)
    and not a client reused across calls. A fresh ``Session`` per call means a
    rotated ``~/.aws/credentials`` file (this repo's IdP-issued sessions last
    on the order of 12h) is picked up on the very next call instead of
    raising ``RequestExpired``/``ExpiredToken`` until the process (or kernel)
    restarts -- both provider modules' original per-call ``boto3.session.
    Session().client(...)`` constructions had already independently arrived
    at this same fix; this function is that fix, shared.

    Parameters
    ----------
    service : str
        A boto3 service name, e.g. ``"ec2"``, ``"iam"``, ``"s3"``, ``"ssm"``.
    region : str, optional
        AWS region to bind the client to. ``None`` (the default) lets boto3
        fall back to its own resolution order (``AWS_REGION``/``AWS_DEFAULT_
        REGION``/the shared config file) -- used for IAM, which is a global
        (non-regional) service.

    Returns
    -------
    Any
        A boto3 client for ``service``, bound to a Session constructed fresh
        for this call.

    Notes
    -----
    Imports ``boto3`` lazily (see the module docstring) -- calling this is
    itself the opt-in that requires boto3 to be installed and credentials to
    be resolvable; nothing at import time of this module requires either.
    """
    import boto3  # lazy: keep the inference paths boto3-free

    return boto3.session.Session().client(service, region_name=region)


def error_code(err: Exception) -> str:
    """Extracts the ``Error.Code`` from a boto3/botocore exception.

    Parameters
    ----------
    err : Exception
        Typically a ``botocore.exceptions.ClientError``, but any exception is
        accepted -- one that lacks a ``.response`` dict (e.g. a plain
        ``Exception`` raised by test doubles, or a non-ClientError failure)
        degrades to ``""`` rather than raising, since every call site uses
        this purely as a string to compare against a known error code.

    Returns
    -------
    str
        The value at ``err.response["Error"]["Code"]``, or ``""`` when
        ``err`` has no ``.response`` attribute, or that attribute is missing
        the expected nested keys.
    """
    return getattr(err, "response", {}).get("Error", {}).get("Code", "")


def assume_role_trust_policy(service: str) -> Dict[str, Any]:
    """Builds an EC2-style AssumeRole trust policy for one AWS service principal.

    Both provider modules independently built this exact document -- for
    ``"sagemaker.amazonaws.com"`` (aws.py's SageMaker execution role) and for
    ``"ec2.amazonaws.com"`` (ec2.py's instance-profile role) -- differing
    only in the ``Principal.Service`` value, so it is parameterized here on
    that value instead of duplicated.

    Parameters
    ----------
    service : str
        The AWS service principal allowed to assume the role, e.g.
        ``"ec2.amazonaws.com"`` or ``"sagemaker.amazonaws.com"``.

    Returns
    -------
    Dict[str, Any]
        An IAM trust-policy document permitting ``sts:AssumeRole`` for
        ``service``. The dict's key order (``Version`` -> ``Statement`` ->
        ``Effect``/``Principal``/``Action`` within each statement) matches
        the inline dicts this was extracted from byte-for-byte under
        ``json.dumps`` -- callers that pin the exact ``AssumeRolePolicyDocument``
        JSON string sent to IAM rely on that ordering being stable.
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
    """Returns the SageMaker execution role ARN, creating it if absent.

    Transcribed from ``aws.py``'s original ``_ensure_exec_role`` (pre-refactor),
    parametrized on the role name so both a SageMaker deployment path and any
    future caller can name their own role. The one intentional behavioral
    delta from the original: the IAM client comes from ``fresh_client("iam")``
    (a brand-new boto3 Session per call) rather than the original's
    process-wide-default-session ``boto3.client("iam")``. This delta is
    payload-invariant (identical IAM API calls, identical request bodies) --
    it only changes which credentials snapshot signs the request, so a
    rotated ``~/.aws/credentials`` file is actually picked up instead of
    silently signing with stale, expired credentials (see ``fresh_client``'s
    docstring for the full rationale).

    Parameters
    ----------
    role_name : str
        IAM role name to create-or-fetch, e.g. ``SAGEMAKER_EXEC_ROLE_NAME``.

    Returns
    -------
    str
        The role's ARN -- freshly created, or the existing role's ARN when
        one by this name already exists.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than the role already existing (e.g. missing
        ``iam:CreateRole``/``iam:AttachRolePolicy`` permission).

    Notes
    -----
    On the CREATE path this sleeps 10 seconds (``time.sleep(10)``, preserved
    exactly from the original) after ``attach_role_policy`` and before
    returning, to let IAM's eventual consistency catch up before SageMaker
    attempts to assume the role -- omitted entirely on the already-exists
    path, since that role has presumably already propagated.
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
    """Returns the EC2 instance-profile name for the S3 model cache, creating it if absent.

    Transcribed verbatim (behaviorally) from ``ec2.py``'s original
    ``_ensure_instance_profile``, with the two things that were module
    constants there (``EC2_INSTANCE_ROLE_NAME``, ``_IAM_PROPAGATION_SLEEP_S``)
    threaded through as parameters instead, so this function carries no
    ec2.py-specific global state. The role grants (a) read/write scoped to
    ``bucket`` and (b) SSM core, which doubles as the break-glass shell for a
    box launched with no SSH key.

    Parameters
    ----------
    role_name : str
        IAM role AND instance-profile name (the original uses one name for
        both), e.g. ``EC2_INSTANCE_ROLE_NAME``.
    bucket : str
        S3 bucket name the role's inline policy is scoped to (list + get/put
        object, nothing else, nothing broader).
    propagation_sleep_s : int
        Seconds to sleep after creating the role/profile, to let IAM's
        eventual consistency settle before ``RunInstances`` references the
        profile. Only slept when something was actually freshly created (see
        the ``created`` flag below) -- an already-existing role/profile is
        presumed already propagated.

    Returns
    -------
    str
        ``role_name`` itself (returned for call-site convenience, mirroring
        the original, which returns the same string it was passed in as
        ``EC2_INSTANCE_ROLE_NAME``).

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than the specific "already exists"/"limit
        exceeded" conditions this function is designed to tolerate (see
        Notes).

    Notes
    -----
    Four ``ClientError`` codes are swallowed, each at the exact call that can
    raise it, because each means "this resource already exists in the shape
    we want" rather than a genuine failure:

    - ``create_role`` -> ``EntityAlreadyExists`` (role already created by an
      earlier run).
    - ``create_instance_profile`` -> ``EntityAlreadyExists`` (ditto, for the
      profile).
    - ``add_role_to_instance_profile`` -> ``LimitExceeded`` (AWS's error code
      for "this role is already attached to this profile" -- a profile may
      only ever hold one role, so re-attaching the same one is a no-op, not
      a genuine limit).

    ``put_role_policy`` is NOT wrapped in a try/except: it overwrites
    idempotently (no "already exists" failure mode), which is exactly why the
    grant tracks ``bucket`` even when the role predates this call with a
    different bucket.

    The ``created`` flag is set to True by EITHER the role or the profile
    being freshly made (not just one specific one) -- ``propagation_sleep_s``
    is spent if anything at all was new, since either omission could leave an
    IAM object RunInstances is about to reference not-yet-visible.
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
            # manage IAM at all -- create_role is the first IAM call, so it
            # fails here even when the role/profile already exist from prior
            # admin-credentialed runs (the common case: the name is fixed).
            # Proceed optimistically; if the profile genuinely doesn't
            # exist, RunInstances fails cleanly when it references it.
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
    """Generic poll loop, matching the exact ordering of every wait loop it replaces.

    Both provider modules independently grew several structurally-identical
    ``while True: ... check ... if time.time() > deadline: raise ... time.
    sleep(...)`` loops (waiting for a public IP, a control agent, a healthy
    model, an ``InService`` SageMaker endpoint). This function is that shape,
    generalized: ``check`` does one poll attempt and returns either a
    non-None success value or ``None`` to keep waiting, and may itself raise
    to abort the loop early for an unrecoverable condition (e.g. "the
    instance is terminated, waiting further is pointless").

    Parameters
    ----------
    check : Callable[[], Optional[T]]
        Called with no arguments once per iteration. A non-``None`` return
        ends the loop successfully with that value. May raise any exception
        to abort the loop immediately -- the exception propagates to
        ``poll_until``'s caller unchanged (used by every migrated loop to
        fail fast on a condition no amount of further waiting would fix,
        e.g. a spot instance reclaimed mid-wait).
    timeout_s : float
        Overall deadline, in seconds, measured from the first call to this
        function (NOT from the first ``check()`` call, though in practice
        the two are microseconds apart).
    interval_s : float
        Seconds slept between poll attempts, via ``time.sleep``.
    on_timeout : Callable[[], Exception]
        Called with no arguments once the deadline has passed with no
        successful ``check()``; must RETURN (not raise) an ``Exception``
        instance, which ``poll_until`` then raises. Deferred like this
        (rather than a fixed message) so the exception can incorporate state
        gathered during the loop's last ``check()`` call -- e.g. ``ec2.py``'s
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
    Ordering contract (this is the load-bearing part -- it must match every
    wait loop being migrated onto this function, byte-for-byte in behavior):

    1. Call ``check()``.
    2. If it returned non-``None``, return that value immediately -- the
       deadline is NEVER consulted on a successful attempt, so a check that
       happens to succeed exactly when time.time() equals (or has just
       passed) the deadline still returns normally rather than raising.
    3. If it raised, the exception propagates immediately (no sleep, no
       deadline check).
    4. Otherwise (``None``, no exception): check the deadline. If
       ``time.time() > deadline``, raise ``on_timeout()``.
    5. Otherwise, ``time.sleep(interval_s)`` and loop back to step 1.

    This function performs no I/O of its own beyond ``time.time()``/``time.
    sleep()`` -- all actual polling (HTTP requests, ``DescribeInstances``
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
    """Runs every teardown step, logging (never raising) each one's outcome.

    Generalized from ``aws.py``'s original ``provision_endpoint`` ``finally``
    block, which tore down a SageMaker endpoint/endpoint-config/model in a
    fixed 3-tuple loop with the same try/log-success/except-log-failure
    shape. Generalized here to an arbitrary sequence of (label, callable)
    steps so other teardown sequences (e.g. a different resource ordering)
    can reuse the same "never let cleanup mask the real error" behavior.

    Parameters
    ----------
    steps : Sequence[Tuple[str, Callable[[], Any]]]
        ``(label, call)`` pairs, in the order they should be attempted. Every
        step runs regardless of whether an earlier one succeeded or failed --
        this function never short-circuits.
    log_prefix : str
        Prefix for each log line, e.g. the caller's function name, so
        interleaved logs from multiple teardown sites stay attributable.

    Returns
    -------
    None

    Notes
    -----
    This function is typically called from a ``finally`` block guarding a
    ``yield`` (a ``@contextlib.contextmanager`` body) -- teardown running
    there must NEVER raise and mask whatever exception (or successful
    completion) the ``with`` body produced. Accordingly, every step's
    exception is caught with a bare ``except Exception`` and logged at INFO
    level rather than re-raised or escalated; a step that fails leaves its
    resource behind for manual/next-run cleanup rather than aborting the
    remaining steps or the caller's own exception propagation.
    """
    for label, call in steps:
        try:
            call()
            logging.info(f"{log_prefix}: torn down {label}")
        except Exception as exc:  # noqa: BLE001 -- teardown must never mask the caller's exception
            logging.info(f"{log_prefix}: teardown skip {label}: {type(exc).__name__}: {exc}")


class _DeploySpecRequired(TypedDict):
    """The one field every deploy spec must have; see `DeploySpec`."""

    #: HuggingFace repo id to deploy/serve, e.g.
    #: ``"Qwen/Qwen2.5-1.5B-Instruct"``. Consumed by BOTH backends: SageMaker
    #: puts it in the container's ``HF_MODEL_ID`` env var
    #: (``aws.provision_endpoint``); EC2/vLLM passes it as the control
    #: agent's ``hf_model_id`` payload field, which becomes vLLM's
    #: ``--model`` flag (``ec2.serve_model`` / the control agent's ``_serve``
    #: in ``payloads/agent.py.txt``).
    hf_model_id: str


class DeploySpec(_DeploySpecRequired, total=False):
    """One model's deployment parameters, shared shape for both backends.

    ``hf_model_id`` (see `_DeploySpecRequired`) is the only field every spec
    must supply; everything else is backend-specific and optional --
    `SAGEMAKER_SPEC_KEYS` / `EC2_SPEC_KEYS` enumerate which optional fields
    each backend actually reads via ``.get(...)``, with a documented default
    for every one it does not require. Modeled as two classes (a
    ``total=True`` base carrying the required field, subclassed
    ``total=False`` for the rest) rather than a single class with
    ``typing.Required``/``NotRequired`` annotations, since that is the
    pattern already idiomatic for "one required field, many optional ones"
    TypedDicts.
    """

    #: Tensor-parallel degree. SageMaker: ``SM_VLLM_TENSOR_PARALLEL_SIZE`` env
    #: var (``spec.get("tp", 1)``). EC2/vLLM: the control agent's ``tp``
    #: payload field -> vLLM's ``--tensor-parallel-size`` (``spec.get("tp",
    #: 1)``).
    tp: int
    #: SageMaker ONLY: the ``InstanceType`` for the endpoint's production
    #: variant (e.g. ``"ml.p5.48xlarge"``); read via ``spec["instance_type"]``
    #: (required by SageMaker specs specifically, though not globally
    #: required across both backends -- EC2 specs have no use for it, since
    #: the shared instance type is chosen once at ``provision_spot_instance``
    #: time, not per model).
    instance_type: str
    #: SageMaker ONLY: extra container environment variables merged into the
    #: DLC's base ``Environment`` dict (e.g. ``{"HF_TOKEN": "hf_..."}`` for a
    #: gated repo); read via ``spec.get("env", {})``.
    env: Dict[str, str]
    #: SageMaker ONLY: override for the default vLLM DLC image URI; read via
    #: ``spec.get("image", SAGEMAKER_VLLM_DLC)``.
    image: str
    #: EC2/vLLM ONLY: context window vLLM is launched with (``--max-model-
    #: len``); also doubles as ``get_model_context_length``'s soft token
    #: guard. Read via ``spec.get("max_model_len", EC2_CONTEXT_LENGTH)``.
    max_model_len: int
    #: EC2/vLLM ONLY: extra CLI flags appended verbatim to the ``docker run``
    #: vLLM command (e.g. ``["--trust-remote-code"]``,
    #: ``["--enable-prefix-caching"]``); read via ``spec.get("vllm_args",
    #: [])``.
    vllm_args: List[str]
    #: EC2/vLLM ONLY: a system prompt the provider layer injects ahead of
    #: every user prompt for this model (e.g. Nemotron-Ultra's "detailed
    #: thinking on" CoT toggle); read via ``spec.get("system_prompt")`` (this
    #: one, uniquely, has no non-None default -- absence means "no
    #: provider-injected system prompt").
    system_prompt: str


#: Keys `aws.SAGEMAKER_DEPLOY_SPECS` entries may use -- verified against the
#: dict literal (aws.py's ``SAGEMAKER_DEPLOY_SPECS``) and every place a spec
#: is read (``provision_endpoint``): ``hf_model_id``/``instance_type`` are
#: read unconditionally (``spec["..."]``, i.e. effectively required by any
#: entry actually deployed); ``tp``/``env``/``image`` are read via
#: ``.get(...)`` with documented defaults.
SAGEMAKER_SPEC_KEYS: frozenset = frozenset(
    {"hf_model_id", "tp", "instance_type", "env", "image"}
)
#: Keys `ec2.EC2_DEPLOY_SPECS` entries may use -- verified against the dict
#: literal (ec2.py's ``EC2_DEPLOY_SPECS``) and every place a spec is read
#: (``get_model_context_length``, ``serve_model``, ``_system_prompt``):
#: ``hf_model_id`` is read unconditionally (``spec["hf_model_id"]``);
#: ``tp``/``max_model_len``/``vllm_args``/``system_prompt`` are all read via
#: ``.get(...)`` with documented defaults.
EC2_SPEC_KEYS: frozenset = frozenset(
    {"hf_model_id", "tp", "max_model_len", "vllm_args", "system_prompt", "adapters"}
)
