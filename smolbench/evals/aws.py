"""
Interfacing with AWS-hosted models through an OpenAI-compatible endpoint.

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
from typing import Any, Optional, Dict, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Answer, QnA, Quiz, Mark, Marks

AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
# Long-lived Bedrock API key (AWS's own env-var name). For SageMaker, override
# with AWS_INFERENCE_API_KEY (a minted, time-limited bearer token).
AWS_BEARER_TOKEN_BEDROCK: str = os.getenv("AWS_BEARER_TOKEN_BEDROCK", None)
AWS_INFERENCE_API_KEY: str = os.getenv("AWS_INFERENCE_API_KEY") or AWS_BEARER_TOKEN_BEDROCK
# Full base URL up to (but excluding) "/chat/completions". Defaults to the
# bedrock-mantle endpoint -- AWS's OpenAI-compatible surface fronting the broad
# model catalog (Anthropic, Qwen, Mistral, DeepSeek, Gemma, gpt-oss, GLM, Kimi,
# Nemotron, MiniMax, ...; call list_models()). Verified live in us-east-1.
# Override AWS_INFERENCE_BASE_URL for:
#   - bedrock-runtime's OpenAI surface (serves only the OpenAI gpt-oss models;
#     Anthropic/Nova there are reached via Converse/Messages, not this API):
#       https://bedrock-runtime.{region}.amazonaws.com/openai/v1
#   - a SageMaker endpoint:
#       https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{ep}/openai/v1
AWS_INFERENCE_BASE_URL: str = os.getenv(
    "AWS_INFERENCE_BASE_URL",
    f"https://bedrock-mantle.{AWS_REGION}.api.aws/v1",
).rstrip("/")
URL: str = f"{AWS_INFERENCE_BASE_URL}/chat/completions"
MODELS_URL: str = f"{AWS_INFERENCE_BASE_URL}/models"
# Override for the OpenAI ``model`` field in the request body. SageMaker routes
# by endpoint URL, so AWS's docs say this field "can be empty or set to match the
# model name your container expects": the vLLM/SGLang DLCs accept "", but a
# *custom* container may reject "" and require its served model id (a 400). By
# default ``_body_model`` auto-resolves that id per endpoint from ``list_models``;
# set this env var to force ONE value across all endpoints instead.
AWS_INFERENCE_BODY_MODEL: Optional[str] = os.getenv("AWS_INFERENCE_BODY_MODEL")
# Cache of each SageMaker endpoint's served model id (resolved lazily; see
# ``_body_model``). Keyed by endpoint name.
_SERVED_MODELS: Dict[str, str] = {}


def _resolve_base(model: str) -> str:
    """Fills the ``{model}`` placeholder in the base URL with the endpoint name.

    SageMaker serves one model per endpoint, so set
    ``AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/{model}/openai/v1``
    and the ``{model}`` placeholder is filled with the (endpoint) name per call.
    With no placeholder (Bedrock-mantle, which selects the model via the request
    body) the static base URL is returned unchanged.
    """
    return (
        AWS_INFERENCE_BASE_URL.replace("{model}", model)
        if "{model}" in AWS_INFERENCE_BASE_URL
        else AWS_INFERENCE_BASE_URL
    )


def _chat_url(model: str) -> str:
    """Returns the chat-completions endpoint for ``model``."""
    return f"{_resolve_base(model)}/chat/completions"


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
    if AWS_INFERENCE_BODY_MODEL is not None:
        return AWS_INFERENCE_BODY_MODEL
    if "{model}" not in AWS_INFERENCE_BASE_URL:
        return model
    if model not in _SERVED_MODELS:
        try:
            served = list_models(model)
            _SERVED_MODELS[model] = served[0] if served else ""
        except requests.exceptions.RequestException:
            _SERVED_MODELS[model] = ""
    return _SERVED_MODELS[model]

AWS_BEDROCK_INFO: bool = bool(int(os.getenv("AWS_BEDROCK_INFO", "0")))
AWS_BEDROCK_INFO_RESPONSE: bool = bool(int(os.getenv("AWS_BEDROCK_INFO_RESPONSE", "0")))
AWS_BEDROCK_MAX_PARALLEL_REQUESTS: int = int(
    os.getenv("AWS_BEDROCK_MAX_PARALLEL_REQUESTS", "8")
)
AWS_BEDROCK_RETRY_BACKOFF_SECONDS: int = 60
# Bedrock's OpenAI-compatible /models listing does not report context windows,
# so context length is a configurable default (optionally refined per model via
# the static map below). It is only used as a soft post-hoc token guard.
AWS_BEDROCK_CONTEXT_LENGTH: int = int(os.getenv("AWS_BEDROCK_CONTEXT_LENGTH", "200000"))
_CONTEXT_LENGTHS: Dict[str, int] = {}


def _is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """
    Returns whether an AWS request error should be retried.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True

        return response.status_code == 429 or 500 <= response.status_code < 600

    return True


def get_model_context_length(model: str) -> int:
    """Returns the configured context window for a model.

    AWS's OpenAI-compatible endpoints expose model ids but not context windows,
    so this returns a per-model override from ``_CONTEXT_LENGTHS`` when known and
    otherwise the ``AWS_BEDROCK_CONTEXT_LENGTH`` default.
    """
    return _CONTEXT_LENGTHS.get(model, AWS_BEDROCK_CONTEXT_LENGTH)


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
        headers={"Authorization": f"Bearer {AWS_INFERENCE_API_KEY}"},
        timeout=120,
    )
    response.raise_for_status()
    return [m["id"] for m in response.json().get("data", [])]


def query(
    prompt: str,
    model: str,
    seed: int,
    context_length: int = 0,
    extra_args: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Queries a model hosted on AWS (Bedrock by default).

    Parameters
    ----------
    prompt:
        The content posed to the LLM we expect an answer from.
    model:
        The model to evaluate (a Bedrock inference-profile id, or the model your
        SageMaker endpoint serves).
    seed:
        Seed for LLM output.
    context_length:
        Context length of LLM model.
    extra_args:
        Extra args for `json=<slug>` of requests to get certain LLM behavior.

    Returns
    -------
    The model's output.
    """
    attempt: int = 0
    # Keep attempting to get a result until one is provisioned.
    while True:
        attempt += 1
        # Tries to get a non-error code response from AWS.
        try:
            response = requests.post(
                url=_chat_url(model),
                headers={
                    "Authorization": f"Bearer {AWS_INFERENCE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=(
                    {
                        "model": _body_model(model),
                        "messages": [{"role": "user", "content": prompt}],
                        "seed": seed,
                    }
                    | (extra_args if extra_args else {})
                ),
                timeout=120,
            )

            if not response.ok:
                logging.info(response.text)

            response.raise_for_status()
            body = response.json()
            if AWS_BEDROCK_INFO and AWS_BEDROCK_INFO_RESPONSE:
                logging.info(body)

            msg = body["choices"][0]["message"]
            if msg["content"] is None:
                logging.warning("Body returned none value: \n" f"{body}")
                return "", None
            # Bedrock/SageMaker surface reasoning as reasoning_content (or
            # reasoning) when a model emits a separate chain-of-thought channel.
            reasoning = msg.get("reasoning_content") or msg.get("reasoning")
            # Usage may be omitted by some SageMaker containers; only guard when
            # the provider reports a token count.
            usage = body.get("usage") or {}
            tokens = usage.get("total_tokens")
            if tokens is not None and tokens > context_length:
                raise ValueError(f"Response:\n{body}\n was {tokens} > {context_length}")
            if AWS_BEDROCK_INFO:
                logging.info(f"Response:\n{body}\n was {tokens} <= {context_length}")
            return msg["content"], reasoning

        # Attempts to retry exceptions if possible.
        except requests.exceptions.RequestException as err:
            if not _is_retryable_request_error(err):
                raise
            logging.info(
                f"AWS request failed on attempt {attempt}: {err}. "
                f"Retrying in {AWS_BEDROCK_RETRY_BACKOFF_SECONDS} seconds."
            )
            time.sleep(AWS_BEDROCK_RETRY_BACKOFF_SECONDS)


def evaluate(
    quiz: Quiz, model: str, seed: int, extra_args: Optional[Dict[str, Any]] = None
) -> Marks:
    """Evaluates a model given a sequence of quizzes."""
    ctx_len: int = get_model_context_length(model)
    max_workers: int = max(1, min(len(quiz), AWS_BEDROCK_MAX_PARALLEL_REQUESTS))
    responses: list[Tuple[str, Optional[str]]] = Parallel(n_jobs=max_workers, prefer="threads")(
        delayed(query)(q.prompt, model, seed, ctx_len, extra_args=extra_args)
        for q in quiz
    )

    mark_list: list[Mark] = []
    q: QnA
    raw: str
    reasoning: Optional[str]
    for q, (raw, reasoning) in zip(quiz, responses):
        try:
            conditioned: Answer = q.condition(raw)
        except ValueError as e:
            if AWS_BEDROCK_INFO:
                logging.info(e)
            mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=None))
            continue

        part_correct, _ = q.score(conditioned)
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=part_correct))

    return Marks(model=model, marks=tuple(mark_list))


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
    f"763104351884.dkr.ecr.{AWS_REGION}.amazonaws.com/vllm:0.11.1-gpu-py312-cu129-ubuntu22.04-sagemaker",
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
    return (
        prov == "sagemaker"
        or "sagemaker" in AWS_INFERENCE_BASE_URL
        or "{model}" in AWS_INFERENCE_BASE_URL
    )


def _sagemaker_client():
    import boto3  # lazy: keep the inference path boto3-free

    return boto3.client("sagemaker", region_name=AWS_REGION)


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
    SigV4QueryAuth(creds, "sagemaker", AWS_REGION, expires=expires).add_auth(req)
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
    global AWS_INFERENCE_API_KEY

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

        # Refresh the bearer token (a long deploy may have outlived an earlier one)
        # and point this module's inference path at it.
        token = mint_sagemaker_token()
        os.environ["AWS_INFERENCE_API_KEY"] = token
        AWS_INFERENCE_API_KEY = token

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
