"""
Share AWS provisioning primitives between the SageMaker and EC2 providers.

Used by :mod:`smolbench.evals.providers.aws` and
:mod:`smolbench.evals.providers.ec2`: fresh-Session clients, ``Error.Code``
extraction, trust policies, IAM role/instance-profile creation, a poll loop and
a teardown sweep. There is deliberately NO shared provision -> poll -> teardown
framework: ``aws.provision_endpoint`` is a per-model ``@contextmanager`` that
ALWAYS tears down (a SageMaker endpoint bills hourly until deleted), while
``ec2`` provisions one instance per experiment and tears down NOTHING on exit
(an on-box idle watchdog plus a max-lifetime shutdown cover abandonment, since
the instance outlives any one section).

Import boto3/botocore LAZILY inside each function that needs them: no inference
path needs AWS credentials or the SDK, and importing this module must not force
that dependency.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypedDict, TypeVar

#: Generic success-value type for `poll_until` -- whatever `check` returns.
T = TypeVar("T")


def fresh_client(service: str, region: Optional[str] = None):
    """Build a boto3 client from a brand-new :class:`boto3.session.Session`.

    Deliberately NOT ``boto3.client(...)``, which caches credentials in the
    process-wide default session; clients are never reused either. A fresh
    Session per call picks up a rotated ``~/.aws/credentials`` (this repo's IdP
    sessions last ~12h) on the very next call, instead of raising
    ``RequestExpired``/``ExpiredToken`` until the process restarts.

    Parameters
    ----------
    region : str, optional
        None defers to boto3's own resolution order; callers pass None for IAM,
        a global service.
    """
    import boto3  # lazy: keep the inference paths boto3-free

    return boto3.session.Session().client(service, region_name=region)


def error_code(err: Exception) -> str:
    """Return ``err.response["Error"]["Code"]``, or ``""`` if absent.

    Accepts any exception, not just ``ClientError``: a missing, ``None`` or
    non-mapping ``.response``/``Error`` degrades to ``""`` rather than raising
    -- callers use this inside ``except`` blocks, where a second exception
    would replace the real failure.
    """
    response = getattr(err, "response", None)
    error = response.get("Error") if isinstance(response, dict) else None
    return error.get("Code", "") if isinstance(error, dict) else ""


def assume_role_trust_policy(service: str) -> Dict[str, Any]:
    """Build an IAM trust policy allowing ``sts:AssumeRole`` by one service.

    Key order is fixed (``Version`` -> ``Statement`` ->
    ``Effect``/``Principal``/``Action``); callers pin the exact
    ``AssumeRolePolicyDocument`` JSON string.

    Parameters
    ----------
    service : str
        Service principal: ``"ec2.amazonaws.com"`` for ec2.py's instance-profile
        role, ``"sagemaker.amazonaws.com"`` for aws.py's execution role.
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

    Attaches ``AmazonSageMakerFullAccess`` on the create path, then sleeps 10s
    for IAM eventual consistency before SageMaker assumes the role; the
    already-exists path skips the sleep. Raises ``ClientError`` for any IAM
    failure other than the role already existing.
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
    """Return the EC2 instance-profile name for the S3 model cache, creating it if absent.

    The role grants exactly S3 list on ``bucket`` plus get/put on its objects,
    and ``AmazonSSMManagedInstanceCore`` (break-glass shell for a box launched
    with no SSH key); ``put_role_policy`` overwrites idempotently, so the grant
    re-targets ``bucket`` even for a pre-existing role.

    Parameters
    ----------
    role_name : str
        Names BOTH the IAM role and the instance profile; returned as-is.
    propagation_sleep_s : int
        Slept before returning ONLY when the role or profile was freshly
        created, so ``RunInstances`` cannot reference an IAM object that is not
        yet visible.

    Raises
    ------
    botocore.exceptions.ClientError
        Any IAM failure other than the tolerated ones: ``EntityAlreadyExists``
        on ``create_role``/``create_instance_profile``, ``LimitExceeded`` on
        ``add_role_to_instance_profile`` (AWS's code for "role already
        attached"; a profile holds at most one role), and ``AccessDenied`` on
        ``create_role`` (scoped credentials -- returns ``role_name``
        optimistically, see the comment there).
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
            # Scoped credentials (the EC2-only operator key) cannot manage IAM
            # at all, and create_role is the first IAM call, so this fails even
            # when the role/profile already exist from a prior
            # admin-credentialed run (the common case: the name is fixed).
            # Proceed optimistically -- if the profile genuinely does not
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
    """Poll ``check`` until it succeeds, with a fixed, load-bearing ordering.

    Parameters
    ----------
    check : callable
        One attempt: non-``None`` = success (returned), ``None`` = keep
        waiting, a raise aborts the loop unchanged (e.g. a spot instance
        reclaimed mid-wait). All I/O lives here; this function does none.
    timeout_s : float
        Deadline, measured from entry.
    on_timeout : callable
        Must RETURN (not raise) the exception this function then raises;
        deferred so it can close over state from the last ``check()`` -- ec2.py
        embeds the last polled status in its ``TimeoutError``.

    Notes
    -----
    The ordering is a contract: a non-``None`` ``check()`` result returns
    IMMEDIATELY without consulting the deadline, so a success at or just past
    the deadline still wins over ``on_timeout()``.
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

    Callers invoke this from a ``finally`` block, where a raise would mask the
    ``with`` body's own exception. Every step therefore runs regardless of
    earlier failures, each exception logged at INFO -- a failed step leaves its
    resource behind for manual or next-run cleanup.

    Parameters
    ----------
    steps : sequence of (str, callable)
        Label and deferred zero-argument call, attempted in order.
    log_prefix : str
        Prefixes each log line (typically the caller's function name), keeping
        interleaved teardown sites attributable.
    """
    for label, call in steps:
        try:
            call()
            logging.info(f"{log_prefix}: torn down {label}")
        except Exception as exc:  # noqa: BLE001 -- teardown must never mask the caller's exception
            logging.info(f"{log_prefix}: teardown skip {label}: {type(exc).__name__}: {exc}")


class _DeploySpecRequired(TypedDict):
    """Hold the one field every deploy spec must have; see `DeploySpec`."""

    #: HuggingFace repo id to deploy/serve, e.g. ``"Qwen/Qwen2.5-1.5B-Instruct"``.
    #: SageMaker puts it in the container's ``HF_MODEL_ID`` env var
    #: (``aws.provision_endpoint``); EC2/vLLM passes it as the control agent's
    #: ``hf_model_id`` payload field, i.e. vLLM's ``--model`` flag
    #: (``ec2.serve_model`` / ``_serve`` in ``payloads/agent.py.txt``).
    hf_model_id: str


class DeploySpec(_DeploySpecRequired, total=False):
    """Hold one model's deployment parameters, in a shape shared by both backends.

    ``hf_model_id`` (see `_DeploySpecRequired`) is the only required field;
    everything else is backend-specific and optional. `SAGEMAKER_SPEC_KEYS` /
    `EC2_SPEC_KEYS` enumerate which optional fields each backend reads, each
    with a documented default.
    """

    #: Tensor-parallel degree, ``spec.get("tp", 1)`` in both backends:
    #: SageMaker's ``SM_VLLM_TENSOR_PARALLEL_SIZE`` env var, EC2/vLLM's ``tp``
    #: payload field (vLLM's ``--tensor-parallel-size``).
    tp: int
    #: SageMaker ONLY: ``InstanceType`` for the endpoint's production variant
    #: (e.g. ``"ml.p5.48xlarge"``); read via ``spec["instance_type"]``, so
    #: SageMaker specs require it. EC2 picks its instance type once at
    #: ``provision_spot_instance`` time, not per model.
    instance_type: str
    #: SageMaker ONLY: extra container environment variables merged into the
    #: DLC's base ``Environment`` dict (e.g. ``{"HF_TOKEN": "hf_..."}`` for a
    #: gated repo); read via ``spec.get("env", {})``.
    env: Dict[str, str]
    #: SageMaker ONLY: override for the default vLLM DLC image URI; read via
    #: ``spec.get("image", SAGEMAKER_VLLM_DLC)``.
    image: str
    #: EC2/vLLM ONLY: context window vLLM launches with (``--max-model-len``),
    #: doubling as ``get_model_context_length``'s soft token guard. Read via
    #: ``spec.get("max_model_len", EC2_CONTEXT_LENGTH)``.
    max_model_len: int
    #: EC2/vLLM ONLY: extra CLI flags appended verbatim to the ``docker run``
    #: vLLM command (e.g. ``["--trust-remote-code"]``, ``["--reasoning-parser",
    #: "qwen3"]``); read via ``spec.get("vllm_args", [])``.
    vllm_args: List[str]
    #: EC2/vLLM ONLY: a system prompt the provider layer injects ahead of every
    #: user prompt for this model (e.g. Nemotron-Ultra's "detailed thinking on"
    #: CoT toggle); read via ``spec.get("system_prompt")``. Uniquely, it has no
    #: non-None default: absence means "no provider-injected system prompt".
    system_prompt: str
    #: EC2/vLLM ONLY: repo id to load this model's TOKENIZER from when that
    #: differs from ``hf_model_id``; ``tokenization.for_model`` reads it via
    #: ``spec.get("tokenizer_hf_id")``, falling back to ``hf_model_id``. Exists
    #: because a quantized redistribution occasionally ships weights with no
    #: ``tokenizer.json`` while its unquantized base repo has one; the
    #: tokenizer is identical either way, so pointing at the base repo keeps
    #: token-matched prompts (the induction noise arm) buildable.
    tokenizer_hf_id: str
    #: EC2/vLLM ONLY: LoRA adapters to stage from S3 and register with vLLM,
    #: as ``[{"name": ..., "s3": "<prefix>/<base_key>[/<sub>]", "region": ...}]``.
    #: ``ec2.serve_model`` consumes this field and passes the staging plan to
    #: the on-box agent. Base-only studies never set it.
    adapters: list


#: Keys `aws.SAGEMAKER_DEPLOY_SPECS` entries may use. Verified against the dict
#: literal and every place a spec is read (``provision_endpoint``).
#: ``hf_model_id``/``instance_type`` are read unconditionally (``spec["..."]``),
#: so any entry actually deployed needs them; the rest via ``.get(...)``.
SAGEMAKER_SPEC_KEYS: frozenset = frozenset(
    {"hf_model_id", "tp", "instance_type", "env", "image"}
)
#: Keys `ec2.EC2_DEPLOY_SPECS` entries may use. Verified against the dict
#: literal and every place a spec is read (``get_model_context_length``,
#: ``serve_model``, ``_system_prompt``, plus ``tokenizer_hf_id`` one module
#: over in ``tokenization.for_model``). Only ``hf_model_id`` is read
#: unconditionally; the rest via ``.get(...)``.
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
