"""
Interface with AWS-hosted models through an OpenAI-compatible endpoint.

A configuration over :mod:`smolbench.evals.openai_compat` (the shared
retry/parsing/evaluation core), adding AWS endpoint/auth resolution plus
optional SageMaker provisioning. The default is Bedrock's bedrock-mantle Chat
Completions endpoint (broad catalog; call ``list_models()``): Anthropic models
are NOT reachable there (Bedrock serves them over the Messages API), and the
bedrock-*runtime* OpenAI surface (an override, see ``_base_url_template``)
serves only gpt-oss. A self-deployed SageMaker endpoint speaks the same schema.

Setup -- Bedrock (default), then SageMaker (same client, your own endpoint):

    AWS_REGION=us-east-1                  # region hosting the models
    AWS_BEARER_TOKEN_BEDROCK=<api key>    # long-lived Bedrock API key
    INFERENCE_PROVIDER=aws                # routes smolbench.evals.provider here
    AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/<endpoint>/openai/v1
    AWS_INFERENCE_API_KEY=<minted bearer token>   # SageMaker only; lasts <= 12h

Optional: ``AWS_BEDROCK_MAX_PARALLEL_REQUESTS`` (evaluate's fan-out, default
8), ``AWS_BEDROCK_INFO`` / ``AWS_BEDROCK_INFO_RESPONSE`` (verbose logging),
``AWS_BEDROCK_CONTEXT_LENGTH`` (the token guard) and
``AWS_INFERENCE_BODY_MODEL`` (see ``_body_model``).

All INFERENCE-path env config is read at CALL time, so refreshing
AWS_INFERENCE_API_KEY takes effect on the next request. The PROVISIONING knobs
``SAGEMAKER_VLLM_DLC``/``SAGEMAKER_EXEC_ROLE_NAME`` are captured at IMPORT
time, so ``load_dotenv()`` must run BEFORE importing this module. Provisioning
builds on :mod:`smolbench.evals._aws` with lazy boto3 imports, keeping this
module dependency-free: inference is pure HTTP.
"""

import contextlib
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from smolbench.evals import _aws
from smolbench.evals._aws import DeploySpec
from smolbench.evals.openai_compat import ChatClient, metadata_get

AWS_BEDROCK_RETRY_BACKOFF_SECONDS: int = 60
# Default bedrock-mantle base URL, a format template so ``region`` resolves at
# CALL time (``_region()``), per the inference path's call-time env policy.
AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE: str = "https://bedrock-mantle.{region}.api.aws/v1"
# Fallback context window (tokens) when ``AWS_BEDROCK_CONTEXT_LENGTH`` is
# unset. Bedrock's OpenAI-compatible endpoints don't expose per-model context
# windows, so this is a conservative soft default.
AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH: int = 200000
# Cache of each SageMaker endpoint's served model id, keyed by endpoint name
# (resolved lazily; see ``_body_model``).
_SERVED_MODELS: Dict[str, str] = {}


def _region() -> str:
    """Return ``AWS_REGION`` (the region hosting the models), else ``"us-east-1"``."""
    return os.getenv("AWS_REGION", "us-east-1")


def _base_url_template() -> str:
    """Return the base URL, up to (but excluding) ``/chat/completions``.

    ``AWS_INFERENCE_BASE_URL`` if set (bedrock-runtime's OpenAI surface
    ``https://bedrock-runtime.{region}.amazonaws.com/openai/v1``, gpt-oss only,
    or a SageMaker endpoint -- see the module docstring), else the
    bedrock-mantle default templated with ``_region()``. Never has a trailing
    slash.
    """
    return os.getenv(
        "AWS_INFERENCE_BASE_URL",
        AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE.format(region=_region()),
    ).rstrip("/")


def _api_key() -> str:
    """Return the bearer token, resolved at call time.

    ``AWS_INFERENCE_API_KEY`` (a minted, time-limited SageMaker token) wins
    over ``AWS_BEARER_TOKEN_BEDROCK`` (long-lived); ``""`` when neither is set.
    """
    return os.getenv("AWS_INFERENCE_API_KEY") or os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")


def _resolve_base(model: str) -> str:
    """Fill the ``{model}`` placeholder in the base URL with the endpoint name.

    SageMaker serves one model per endpoint, so its base URL carries the
    placeholder; with none (bedrock-mantle selects in the body) the base URL is
    returned unchanged.
    """
    base = _base_url_template()
    return base.replace("{model}", model) if "{model}" in base else base


def _connection(model: str) -> Tuple[str, str]:
    """Return ``(chat-completions URL, bearer token)`` for ``model``."""
    return f"{_resolve_base(model)}/chat/completions", _api_key()


def _body_model(model: str) -> str:
    """Return the OpenAI ``model`` field to put in the request body.

    ``AWS_INFERENCE_BODY_MODEL`` wins everywhere; otherwise Bedrock (no
    ``{model}`` placeholder) sends the model id as-is. A SageMaker endpoint
    routes by URL, so the field is nominally free -- but a custom container may
    400 on ``""``, so its served id is resolved once via ``list_models``
    (cached in ``_SERVED_MODELS``), falling back to ``""``. A FAILED lookup is
    NOT cached, and neither is an empty listing: a transient error -- or a
    warming endpoint answering 200 with no models yet -- would otherwise pin
    ``""`` for the rest of the process.
    """
    body_model_override = os.getenv("AWS_INFERENCE_BODY_MODEL")
    if body_model_override is not None:
        return body_model_override
    if "{model}" not in _base_url_template():
        return model
    if model not in _SERVED_MODELS:
        try:
            served = list_models(model)
        except requests.exceptions.RequestException:
            return ""  # not cached; retried on the next request
        if not served:
            return ""  # not cached either; the endpoint may still be warming
        _SERVED_MODELS[model] = served[0]
    return _SERVED_MODELS[model]


def get_model_context_length(model: str) -> int:
    """Return the context window (tokens) to guard ``usage.total_tokens`` against.

    AWS's OpenAI-compatible endpoints expose model ids but not context windows,
    so ``model`` is UNUSED (present for parity with the other providers'
    ``Callable[[str], int]``) and there is no per-model override. Reads
    ``AWS_BEDROCK_CONTEXT_LENGTH`` at CALL time, else
    ``AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH``; one endpoint-wide value suffices
    because callers use it only as a soft post-hoc guard.
    """
    return int(os.getenv("AWS_BEDROCK_CONTEXT_LENGTH", str(AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH)))


def list_models(model: str = "") -> list[str]:
    """List model ids from the configured endpoint's ``GET /models`` response.

    Works on bedrock-mantle and on SageMaker endpoints. bedrock-runtime's
    OpenAI surface does NOT implement ``GET /models`` (it 404s); discover ids
    there with ``aws bedrock list-foundation-models``.

    Parameters
    ----------
    model : str, optional
        Endpoint name filling the ``{model}`` placeholder of a templated
        SageMaker base URL -- required there, else the request hits a literal
        ``{model}`` path and fails. The default ``""`` suits bedrock-mantle.
    """
    response = metadata_get(f"{_resolve_base(model)}/models", _api_key(), check_status=True)
    return [m["id"] for m in response.get("data", [])]


_CLIENT = ChatClient(
    name="AWS",
    env_prefix="AWS_BEDROCK",
    connection=_connection,
    context_length=get_model_context_length,
    body_model=_body_model,
    retry_backoff_s=AWS_BEDROCK_RETRY_BACKOFF_SECONDS,
)

# The provider-facing API; see ChatClient.query/complete/evaluate.
query = _CLIENT.query
complete = _CLIENT.complete
evaluate = _CLIENT.evaluate


# ---------------------------------------------------------------------------
# Optional SageMaker endpoint provisioning (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# boto3/botocore imports stay *inside* the functions below (see the module
# docstring). The endpoint NAME must equal the model id passed to
# query()/evaluate() -- the provider builds .../endpoints/<name>/openai/v1
# from it.

# SageMaker vLLM Deep Learning Container (override via env). AWS's vLLM and
# SGLang DLCs serve the OpenAI-compatible /openai/v1 route.
SAGEMAKER_VLLM_DLC: str = os.getenv(
    "SAGEMAKER_VLLM_DLC",
    f"763104351884.dkr.ecr.{_region()}.amazonaws.com/vllm:0.11.1-gpu-py312-cu129-ubuntu22.04-sagemaker",
)
SAGEMAKER_EXEC_ROLE_NAME: str = os.getenv("SAGEMAKER_EXEC_ROLE_NAME", "smolbench-sm-exec-role")
# Per-endpoint deployment spec. The small entry runs within the default ml.g5
# quota; the big models need a Service Quota increase for their instance type
# (multi-GPU endpoint quotas default to 0) plus likely quantization/multi-node
# tuning, so treat their specs as editable templates. Add {"env": {"HF_TOKEN":
# "hf_..."}} for gated models, {"image": "..."} to override the container.
SAGEMAKER_DEPLOY_SPECS: Dict[str, DeploySpec] = {
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct",                    "instance_type": "ml.g5.2xlarge",  "tp": 1},
    "llama-31-405b":       {"hf_model_id": "meta-llama/Llama-3.1-405B-Instruct",            "instance_type": "ml.p5.48xlarge", "tp": 8},
    "nemotron-ultra-253b": {"hf_model_id": "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1",       "instance_type": "ml.p5.48xlarge", "tp": 8},
    "llama4-maverick":     {"hf_model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct", "instance_type": "ml.p5.48xlarge", "tp": 8},
}


def _is_sagemaker_provider() -> bool:
    """Return whether the active provider targets a SageMaker endpoint (vs. serverless Bedrock)."""
    prov = os.getenv("INFERENCE_PROVIDER", "").lower()
    if prov not in ("aws", "bedrock", "sagemaker"):
        return False
    base = _base_url_template()
    return prov == "sagemaker" or "sagemaker" in base or "{model}" in base


def _sagemaker_client():
    """Return a SageMaker client from a fresh boto3 Session.

    Fresh per call, so a just-rotated credentials file is picked up on the next
    call (see ``_aws.fresh_client``). Locally named so
    ``tests/evals/test_aws_provision.py`` can monkeypatch this one name.
    """
    return _aws.fresh_client("sagemaker", _region())


def mint_sagemaker_token(expires: int = 43200) -> str:
    """Mint a short-lived SageMaker bearer token from local AWS credentials.

    A base64-encoded SigV4 pre-signed ``CallWithBearerToken`` URL prefixed
    ``sagemaker-api-key-``: the SageMaker SDK's ``generate_token`` scheme,
    reimplemented on botocore so no extra SDK is needed.

    Parameters
    ----------
    expires : int
        Token lifetime in seconds; SageMaker caps it at 12h (the default).

    Raises
    ------
    RuntimeError
        No local AWS credentials found.
    """
    import base64
    from botocore.auth import SigV4QueryAuth
    from botocore.awsrequest import AWSRequest
    from botocore.session import Session as BotocoreSession

    creds = BotocoreSession().get_credentials()
    if creds is None:
        raise RuntimeError("No AWS credentials found.")
    req = AWSRequest(
        method="POST",
        url="https://sagemaker.amazonaws.com/",
        headers={"host": "sagemaker.amazonaws.com"},
        params={"Action": "CallWithBearerToken"},
    )
    SigV4QueryAuth(creds, "sagemaker", _region(), expires=expires).add_auth(req)
    presigned = req.url.replace("https://", "") + "&Version=1"
    return "sagemaker-api-key-" + base64.b64encode(presigned.encode()).decode()


def _ensure_exec_role() -> str:
    """Return the ``SAGEMAKER_EXEC_ROLE_NAME`` role ARN, creating it idempotently if absent.

    Locally named so tests can monkeypatch this name instead of ``_aws``.
    """
    return _aws.ensure_sagemaker_execution_role(SAGEMAKER_EXEC_ROLE_NAME)


# Pure kwargs builders -- no AWS I/O, no boto3 import, so
# tests/evals/test_aws_provision.py can pin a payload by calling one directly,
# with no SageMaker client or provision_endpoint context.


def _create_model_kwargs(model: str, spec: DeploySpec, role_arn: str) -> Dict[str, Any]:
    """Build the pure ``CreateModel`` kwargs for one SageMaker deploy spec.

    Parameters
    ----------
    model : str
        Endpoint name; the SageMaker *model* resource is ``f"{model}-model"``.
    spec : DeploySpec
        Requires ``hf_model_id`` (else ``KeyError``); ``image``/``tp``/``env``
        are optional, with the defaults `_aws.DeploySpec` documents.
        ``spec["env"]`` merges SECOND into ``Environment``, so its keys
        override colliding base ones.
    """
    return {
        "ModelName": f"{model}-model",
        "ExecutionRoleArn": role_arn,
        "PrimaryContainer": {
            "Image": spec.get("image", SAGEMAKER_VLLM_DLC),
            "Environment": {
                "HF_MODEL_ID": spec["hf_model_id"],
                "SM_VLLM_TENSOR_PARALLEL_SIZE": str(spec.get("tp", 1)),
                "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
            }
            | spec.get("env", {}),
        },
    }


def _create_endpoint_config_kwargs(model: str, spec: DeploySpec) -> Dict[str, Any]:
    """Build the pure ``CreateEndpointConfig`` kwargs for one SageMaker deploy spec.

    One production variant, 1 instance, with a fixed 1800s container-startup
    health-check timeout: large multi-GPU DLC images are slow to pull and load.

    Parameters
    ----------
    model : str
        Endpoint name; the config is ``f"{model}-config"``, referencing
        ``f"{model}-model"``.
    spec : DeploySpec
        Must have ``instance_type`` (else ``KeyError``).
    """
    return {
        "EndpointConfigName": f"{model}-config",
        "ProductionVariants": [
            {
                "VariantName": "variant1",
                "ModelName": f"{model}-model",
                "InitialInstanceCount": 1,
                "InstanceType": spec["instance_type"],
                "ContainerStartupHealthCheckTimeoutInSeconds": 1800,
            }
        ],
    }


def _create_endpoint_kwargs(model: str) -> Dict[str, Any]:
    """Build the pure ``CreateEndpoint`` kwargs referencing ``f"{model}-config"``.

    ``model`` becomes ``EndpointName`` verbatim: the same string
    ``query()``/``evaluate()`` are later called with, and what fills
    ``AWS_INFERENCE_BASE_URL``'s ``{model}`` placeholder.
    """
    return {"EndpointName": model, "EndpointConfigName": f"{model}-config"}


def _teardown_steps(sm: Any, model: str) -> List[Tuple[str, Callable[[], Any]]]:
    """Build the ordered ``(label, callable)`` teardown steps for one endpoint.

    Parameters
    ----------
    sm : Any
        A SageMaker client (``Any``: boto3 clients are dynamically generated).
    model : str
        Endpoint name; its config and model resources are ``f"{model}-config"``
        / ``f"{model}-model"``.

    Returns
    -------
    list
        Exactly three pairs in DEPENDENCY-SAFE order: ``"endpoint"`` (whose
        deletion stops the billed instance), ``"endpoint-config"``, ``"model"``.
        The calls are deferred, so building the list has no side effects.
        Labels are bare (not ``f"endpoint {model}"``): ``provision_endpoint``
        formats the model name into its own logs.
    """
    mdl, cfg = f"{model}-model", f"{model}-config"
    return [
        ("endpoint", lambda: sm.delete_endpoint(EndpointName=model)),
        ("endpoint-config", lambda: sm.delete_endpoint_config(EndpointConfigName=cfg)),
        ("model", lambda: sm.delete_model(ModelName=mdl)),
    ]


@contextlib.contextmanager
def provision_endpoint(model: str, timeout_min: int = 40):
    """Provision the SageMaker endpoint named ``model`` for the body of a ``with``.

    Deploys from ``SAGEMAKER_DEPLOY_SPECS[model]``, waits for ``InService``,
    refreshes ``AWS_INFERENCE_API_KEY``, and yields ``model`` unchanged.
    Teardown (endpoint + endpoint-config + model, which stops the billed
    instance) is GUARANTEED on exit: success, exception, or KeyboardInterrupt.
    A no-op that still yields ``model`` for serverless Bedrock and non-AWS
    providers, so wrapping an experiment is always safe.

    Parameters
    ----------
    timeout_min : int
        Minutes to wait for ``InService``; large multi-GPU DLC images are slow
        to pull and load.

    Raises
    ------
    KeyError
        The provider is SageMaker but ``model`` has no
        ``SAGEMAKER_DEPLOY_SPECS`` entry; checked before any AWS call, so a
        typo fails fast.
    RuntimeError
        The endpoint reached ``Failed``/``OutOfService``.
    TimeoutError
        Not ``InService`` within ``timeout_min``.
    """
    if not _is_sagemaker_provider():
        logging.info("provision_endpoint: serverless/non-SageMaker provider; nothing to provision.")
        yield model
        return

    spec = SAGEMAKER_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(
            f"No SAGEMAKER_DEPLOY_SPECS entry for endpoint {model!r}; "
            "add one with hf_model_id / instance_type / tp."
        )

    role = _ensure_exec_role()
    try:
        logging.info(
            f"provision_endpoint: deploying {model!r} ({spec['hf_model_id']} on {spec['instance_type']}) ..."
        )
        # A fresh `_sagemaker_client()` per create call, not one reused across
        # all three, so each picks up a just-rotated credentials file -- the
        # long-running-notebook-cell case.
        _sagemaker_client().create_model(**_create_model_kwargs(model, spec, role))
        _sagemaker_client().create_endpoint_config(**_create_endpoint_config_kwargs(model, spec))
        _sagemaker_client().create_endpoint(**_create_endpoint_kwargs(model))

        # `_aws.poll_until` (shared with ec2.py's wait loops), not a hand-rolled
        # `while True`. `last_status` is threaded through via `nonlocal`
        # because `on_timeout()` needs the most recently polled status, while
        # `poll_until`'s `check` contract is otherwise stateless.
        last_status: Optional[str] = None

        def check() -> Optional[bool]:
            nonlocal last_status
            # Fresh client each poll, to pick up a refreshed credential file.
            desc = _sagemaker_client().describe_endpoint(EndpointName=model)
            status = desc["EndpointStatus"]
            last_status = status
            if status == "InService":
                logging.info(f"provision_endpoint: {model!r} is InService.")
                return True
            if status in ("Failed", "OutOfService"):
                raise RuntimeError(f"endpoint {model} {status}: {desc.get('FailureReason', '?')}")
            return None

        def on_timeout() -> TimeoutError:
            return TimeoutError(
                f"endpoint {model} not InService after {timeout_min} min (status={last_status})."
            )

        _aws.poll_until(check, timeout_s=timeout_min * 60, interval_s=30, on_timeout=on_timeout)

        # Refresh the bearer token: a long deploy may have outlived an earlier
        # one. The inference path reads AWS_INFERENCE_API_KEY at call time, so
        # setting the env var suffices; no module global to mutate.
        os.environ["AWS_INFERENCE_API_KEY"] = mint_sagemaker_token()

        yield model
    finally:
        # The model name rides in the log prefix, so _teardown_steps' labels
        # stay bare and every teardown line is attributable to this endpoint.
        _aws.best_effort_teardown(
            _teardown_steps(_sagemaker_client(), model),
            log_prefix=f"provision_endpoint {model}",
        )
