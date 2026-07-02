"""
Interfacing with AWS-hosted models through an OpenAI-compatible endpoint.

A configuration over :mod:`smolbench.evals.openai_compat` (the shared retry/
parsing/evaluation core); what lives here is AWS-specific endpoint and auth
resolution plus the optional SageMaker endpoint provisioning helpers.

Defaults to Amazon Bedrock's OpenAI-compatible Chat Completions API on the
bedrock-mantle endpoint, which fronts a broad catalog of chat models behind a
single base URL (Qwen, Mistral, DeepSeek, Gemma, OpenAI gpt-oss, GLM, Kimi,
Nemotron, MiniMax, ...). Note: Anthropic models on Bedrock are served via the
Anthropic Messages API, not this OpenAI Chat Completions API, and so are not
reachable through this provider. The same module also targets a self-deployed
Amazon SageMaker endpoint, since SageMaker serves the same OpenAI-compatible
schema; only the base URL and token differ.

Setup
-----
Bedrock (default):
    AWS_REGION=us-east-1                  # region hosting the models
    AWS_BEARER_TOKEN_BEDROCK=<api key>    # long-lived Bedrock API key
    INFERENCE_PROVIDER=aws                # to route smolbench.evals.provider here

SageMaker (point the same client at your deployed endpoint):
    AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/<endpoint>/openai/v1
    AWS_INFERENCE_API_KEY=<minted bearer token>   # SageMaker tokens last <= 12h

All env config is read at CALL time, never import time: setting or refreshing
AWS_INFERENCE_API_KEY (e.g. after ``mint_sagemaker_token``) takes effect on
the next request with no re-import, and no module global needs mutating.

Enabling Bedrock model access and minting a SageMaker token are out-of-band
steps; the inference path stays dependency-free and only speaks HTTP. The
optional ``provision_endpoint`` helper can deploy and tear down a SageMaker
endpoint for the duration of an experiment; it imports boto3/botocore lazily, so
importing this module (and the query path) requires neither. The ``model`` argument is a
model id from the configured endpoint's catalog -- on the default bedrock-mantle
endpoint, e.g. ``anthropic.claude-haiku-4-5``, ``qwen.qwen3-32b``, or
``openai.gpt-oss-120b``; call ``list_models()`` to enumerate them.
"""

import contextlib
import logging
import os
import time
from typing import Any, Dict, Tuple

import requests

from smolbench.evals.openai_compat import ChatClient

AWS_BEDROCK_RETRY_BACKOFF_SECONDS: int = 60
# Cache of each SageMaker endpoint's served model id (resolved lazily; see
# ``_body_model``). Keyed by endpoint name.
_SERVED_MODELS: Dict[str, str] = {}
# Per-model context-window overrides for get_model_context_length.
_CONTEXT_LENGTHS: Dict[str, int] = {}


def _region() -> str:
    return os.getenv("AWS_REGION", "us-east-1")


def _base_url_template() -> str:
    """Full base URL up to (but excluding) ``/chat/completions``.

    Defaults to the bedrock-mantle endpoint -- AWS's OpenAI-compatible surface
    fronting the broad model catalog (Anthropic, Qwen, Mistral, DeepSeek,
    Gemma, gpt-oss, GLM, Kimi, Nemotron, MiniMax, ...; call list_models()).
    Verified live in us-east-1. Override AWS_INFERENCE_BASE_URL for:
      - bedrock-runtime's OpenAI surface (serves only the OpenAI gpt-oss
        models; Anthropic/Nova there are reached via Converse/Messages, not
        this API):
          https://bedrock-runtime.{region}.amazonaws.com/openai/v1
      - a SageMaker endpoint:
          https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{ep}/openai/v1
    """
    return os.getenv(
        "AWS_INFERENCE_BASE_URL",
        f"https://bedrock-mantle.{_region()}.api.aws/v1",
    ).rstrip("/")


def _api_key() -> str:
    """Bearer token, resolved at call time.

    ``AWS_INFERENCE_API_KEY`` (a minted, time-limited SageMaker token) wins;
    otherwise ``AWS_BEARER_TOKEN_BEDROCK`` (AWS's own env-var name for the
    long-lived Bedrock API key).
    """
    return os.getenv("AWS_INFERENCE_API_KEY") or os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")


def _resolve_base(model: str) -> str:
    """Fills the ``{model}`` placeholder in the base URL with the endpoint name.

    SageMaker serves one model per endpoint, so set
    ``AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/{model}/openai/v1``
    and the ``{model}`` placeholder is filled with the (endpoint) name per call.
    With no placeholder (Bedrock-mantle, which selects the model via the request
    body) the static base URL is returned unchanged.
    """
    base = _base_url_template()
    return base.replace("{model}", model) if "{model}" in base else base


def _connection(model: str) -> Tuple[str, str]:
    """Returns the chat-completions URL and bearer token for ``model``."""
    return f"{_resolve_base(model)}/chat/completions", _api_key()


def _body_model(model: str) -> str:
    """The OpenAI ``model`` field to put in the request body.

    Precedence: an explicit ``AWS_INFERENCE_BODY_MODEL`` wins (one value for all
    endpoints). Otherwise, for Bedrock (no ``{model}`` placeholder) the model id
    selects the model and is sent as-is. For a SageMaker single-model endpoint
    (templated base URL) AWS routes by the URL, so the field is nominally free --
    the vLLM/SGLang DLCs accept ``""`` -- but a *custom* container may reject
    ``""`` and require its served id (a 400). We therefore resolve each endpoint's
    served id once via ``list_models`` (cached per endpoint) and fall back to
    ``""`` if the listing is unavailable, so every endpoint -- including the
    notebook's three distinct SageMaker endpoints -- gets the name its own
    container expects.
    """
    body_model_override = os.getenv("AWS_INFERENCE_BODY_MODEL")
    if body_model_override is not None:
        return body_model_override
    if "{model}" not in _base_url_template():
        return model
    if model not in _SERVED_MODELS:
        try:
            served = list_models(model)
            _SERVED_MODELS[model] = served[0] if served else ""
        except requests.exceptions.RequestException:
            _SERVED_MODELS[model] = ""
    return _SERVED_MODELS[model]


def get_model_context_length(model: str) -> int:
    """Returns the configured context window for a model.

    AWS's OpenAI-compatible endpoints expose model ids but not context windows,
    so this returns a per-model override from ``_CONTEXT_LENGTHS`` when known and
    otherwise the ``AWS_BEDROCK_CONTEXT_LENGTH`` default (env var, default
    200000). It is only used as a soft post-hoc token guard.
    """
    return _CONTEXT_LENGTHS.get(
        model, int(os.getenv("AWS_BEDROCK_CONTEXT_LENGTH", "200000"))
    )


def list_models(model: str = "") -> list[str]:
    """Lists model ids available on the configured AWS endpoint.

    Works on the default bedrock-mantle endpoint and on SageMaker endpoints. For a
    templated SageMaker base URL (``.../endpoints/{model}/openai/v1``) pass the
    endpoint name as ``model`` to fill the ``{model}`` placeholder; otherwise the
    request hits a literal ``{model}`` path and fails. The bedrock-runtime OpenAI
    surface does not implement ``GET /models`` (it 404s); there, discover ids with
    ``aws bedrock list-foundation-models`` instead.
    """
    response = requests.get(
        url=f"{_resolve_base(model)}/models",
        headers={"Authorization": f"Bearer {_api_key()}"},
        timeout=120,
    )
    response.raise_for_status()
    return [m["id"] for m in response.json().get("data", [])]


_CLIENT = ChatClient(
    name="AWS",
    env_prefix="AWS_BEDROCK",
    connection=_connection,
    context_length=get_model_context_length,
    body_model=_body_model,
    retry_backoff_s=AWS_BEDROCK_RETRY_BACKOFF_SECONDS,
)

# The provider-facing API (dispatched via smolbench.evals.provider); full
# parameter docs live on ChatClient.query / ChatClient.evaluate.
query = _CLIENT.query
evaluate = _CLIENT.evaluate


# ---------------------------------------------------------------------------
# Optional SageMaker endpoint provisioning (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# Deploying/tearing down a SageMaker endpoint needs boto3/botocore; the inference
# path does not, so those imports stay *inside* the functions below to keep
# importing this module dependency-free (see module docstring). The endpoint NAME
# must equal the model id passed to query()/evaluate() -- the provider builds
# .../endpoints/<name>/openai/v1 from it.

# SageMaker vLLM Deep Learning Container (override via env). The OpenAI-compatible
# /openai/v1 route is served by AWS's vLLM and SGLang DLCs.
SAGEMAKER_VLLM_DLC: str = os.getenv(
    "SAGEMAKER_VLLM_DLC",
    f"763104351884.dkr.ecr.{_region()}.amazonaws.com/vllm:0.11.1-gpu-py312-cu129-ubuntu22.04-sagemaker",
)
SAGEMAKER_EXEC_ROLE_NAME: str = os.getenv("SAGEMAKER_EXEC_ROLE_NAME", "smolbench-sm-exec-role")
# Per-endpoint deployment spec. The small entry runs within the default ml.g5
# quota; the big models need a Service Quota increase for their instance type
# (multi-GPU endpoint quotas default to 0) plus likely quantization/multi-node
# tuning -- treat their specs as editable templates. Add {"env": {"HF_TOKEN":
# "hf_..."}} for gated models, or {"image": "..."} to override the container.
SAGEMAKER_DEPLOY_SPECS: Dict[str, Dict[str, Any]] = {
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct",                    "instance_type": "ml.g5.2xlarge",  "tp": 1},
    "llama-31-405b":       {"hf_model_id": "meta-llama/Llama-3.1-405B-Instruct",            "instance_type": "ml.p5.48xlarge", "tp": 8},
    "nemotron-ultra-253b": {"hf_model_id": "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1",       "instance_type": "ml.p5.48xlarge", "tp": 8},
    "llama4-maverick":     {"hf_model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct", "instance_type": "ml.p5.48xlarge", "tp": 8},
}


def _is_sagemaker_provider() -> bool:
    """Whether the active provider targets a SageMaker endpoint (vs serverless Bedrock)."""
    prov = os.getenv("INFERENCE_PROVIDER", "").lower()
    if prov not in ("aws", "bedrock", "sagemaker"):
        return False
    base = _base_url_template()
    return prov == "sagemaker" or "sagemaker" in base or "{model}" in base


def _sagemaker_client():
    import boto3  # lazy: keep the inference path boto3-free

    return boto3.client("sagemaker", region_name=_region())


def mint_sagemaker_token(expires: int = 43200) -> str:
    """Mints a short-lived (<=12h) SageMaker bearer token from local AWS creds.

    The token is a base64-encoded SigV4 pre-signed ``CallWithBearerToken`` URL --
    the same scheme the SageMaker SDK's ``generate_token`` produces, implemented
    here with botocore so the module needs no extra SDK.
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
    """Returns the SageMaker execution role ARN, creating it (idempotently) if absent."""
    import json

    import boto3

    iam = boto3.client("iam")
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        arn = iam.create_role(
            RoleName=SAGEMAKER_EXEC_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
        )["Role"]["Arn"]
        iam.attach_role_policy(
            RoleName=SAGEMAKER_EXEC_ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
        )
        time.sleep(10)  # let the new role propagate before SageMaker assumes it
        return arn
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName=SAGEMAKER_EXEC_ROLE_NAME)["Role"]["Arn"]


@contextlib.contextmanager
def provision_endpoint(model: str, timeout_min: int = 40):
    """Provision the SageMaker endpoint named ``model`` for the body of a ``with``.

    Deploys the endpoint from ``SAGEMAKER_DEPLOY_SPECS[model]``, waits until it is
    InService, refreshes the bearer token, yields, and GUARANTEES teardown (delete
    endpoint + endpoint-config + model, which stops the billed instance) on exit --
    success, exception, or KeyboardInterrupt. A no-op for serverless Bedrock and
    non-AWS providers, so wrapping an experiment with it is always safe::

        with provision_endpoint(DENSE_MODEL):
            decode_intens_eval = evaluate(intens_quiz, DENSE_MODEL, SEED)
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

    mdl, cfg = f"{model}-model", f"{model}-config"
    role = _ensure_exec_role()
    try:
        logging.info(
            f"provision_endpoint: deploying {model!r} ({spec['hf_model_id']} on {spec['instance_type']}) ..."
        )
        _sagemaker_client().create_model(
            ModelName=mdl,
            ExecutionRoleArn=role,
            PrimaryContainer={
                "Image": spec.get("image", SAGEMAKER_VLLM_DLC),
                "Environment": {
                    "HF_MODEL_ID": spec["hf_model_id"],
                    "SM_VLLM_TENSOR_PARALLEL_SIZE": str(spec.get("tp", 1)),
                    "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
                }
                | spec.get("env", {}),
            },
        )
        _sagemaker_client().create_endpoint_config(
            EndpointConfigName=cfg,
            ProductionVariants=[
                {
                    "VariantName": "variant1",
                    "ModelName": mdl,
                    "InitialInstanceCount": 1,
                    "InstanceType": spec["instance_type"],
                    "ContainerStartupHealthCheckTimeoutInSeconds": 1800,
                }
            ],
        )
        _sagemaker_client().create_endpoint(EndpointName=model, EndpointConfigName=cfg)

        deadline = time.time() + timeout_min * 60
        while True:
            # Fresh client each poll so a rotated/refreshed credential file is picked up.
            desc = _sagemaker_client().describe_endpoint(EndpointName=model)
            status = desc["EndpointStatus"]
            if status == "InService":
                logging.info(f"provision_endpoint: {model!r} is InService.")
                break
            if status in ("Failed", "OutOfService"):
                raise RuntimeError(f"endpoint {model} {status}: {desc.get('FailureReason', '?')}")
            if time.time() > deadline:
                raise TimeoutError(
                    f"endpoint {model} not InService after {timeout_min} min (status={status})."
                )
            time.sleep(30)

        # Refresh the bearer token (a long deploy may have outlived an earlier
        # one). The inference path reads AWS_INFERENCE_API_KEY from the
        # environment at call time, so setting it here is sufficient -- no
        # module global to mutate.
        os.environ["AWS_INFERENCE_API_KEY"] = mint_sagemaker_token()

        yield model
    finally:
        # Guaranteed teardown -- runs on success, error, or interrupt.
        sm = _sagemaker_client()
        for label, call in (
            ("endpoint", lambda: sm.delete_endpoint(EndpointName=model)),
            ("endpoint-config", lambda: sm.delete_endpoint_config(EndpointConfigName=cfg)),
            ("model", lambda: sm.delete_model(ModelName=mdl)),
        ):
            try:
                call()
                logging.info(f"provision_endpoint: torn down {label} {model}")
            except Exception as exc:  # teardown must not mask the body's exception
                logging.info(f"provision_endpoint: teardown skip {label}: {type(exc).__name__}: {exc}")
