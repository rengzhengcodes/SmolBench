"""
Interface with AWS-hosted models through an OpenAI-compatible endpoint.

This module is a configuration over :mod:`smolbench.evals.openai_compat`
(the shared retry/parsing/evaluation core). It adds AWS-specific endpoint
and auth resolution, plus the optional SageMaker endpoint provisioning
helpers.

It defaults to Amazon Bedrock's OpenAI-compatible Chat Completions API on
the bedrock-mantle endpoint, which fronts a broad catalog of chat models
behind a single base URL (Qwen, Mistral, DeepSeek, Gemma, OpenAI gpt-oss,
GLM, Kimi, Nemotron, MiniMax, ...). Note: Bedrock serves Anthropic models
via the Anthropic Messages API, not this OpenAI Chat Completions API, so
this provider cannot reach them. The separate bedrock-*runtime* OpenAI
surface (an override, not the default; see ``_base_url_template``) serves
only the OpenAI gpt-oss models, and reaches Anthropic and Nova only
through the Converse/Messages API, not this one. The same module also
targets a self-deployed Amazon SageMaker endpoint, since SageMaker serves
the same OpenAI-compatible schema; only the base URL and token differ.

Setup
-----
Bedrock (default):
    AWS_REGION=us-east-1                  # region hosting the models
    AWS_BEARER_TOKEN_BEDROCK=<api key>    # long-lived Bedrock API key
    INFERENCE_PROVIDER=aws                # to route smolbench.evals.provider here

SageMaker (point the same client at your deployed endpoint):
    AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/<endpoint>/openai/v1
    AWS_INFERENCE_API_KEY=<minted bearer token>   # SageMaker tokens last <= 12h

This module reads all env config on the INFERENCE path (base URL, bearer
token, body-model override, context-length override) at CALL time, never
import time. If you set or refresh AWS_INFERENCE_API_KEY (e.g. after
``mint_sagemaker_token``), it takes effect on the next request. This needs
no re-import, and no module global needs mutating. The optional SageMaker
PROVISIONING knobs (``SAGEMAKER_VLLM_DLC``, ``SAGEMAKER_EXEC_ROLE_NAME``,
below) are the exception: this module captures them from the environment
once, at IMPORT time, as module-level constants. To override them, call
``load_dotenv()`` (or otherwise set the environment) BEFORE importing this
module. If you import first and then set the env var, the override will
not take effect, unlike everywhere else in this module.

You enable Bedrock model access and mint a SageMaker token as out-of-band
steps. The inference path stays dependency-free and only speaks HTTP. The
optional ``provision_endpoint`` helper can deploy and tear down a SageMaker
endpoint for the duration of an experiment. It imports boto3/botocore
lazily, so importing this module (and the query path) requires neither. The
``model`` argument is a model id from the configured endpoint's catalog --
on the default bedrock-mantle endpoint, e.g. ``qwen.qwen3-32b`` or
``openai.gpt-oss-120b``; call ``list_models()`` to enumerate them.

This module builds provisioning on :mod:`smolbench.evals._aws`, the primitives shared
with ``ec2.py``'s EC2 Spot provisioning (fresh-Session client construction,
IAM execution-role creation, the generic ``poll_until`` wait loop, the
``DeploySpec`` shape). See that module's docstring for the full lifecycle-
correspondence table between the two providers. ``provision_endpoint`` here
is a per-model, always-tears-down ``@contextmanager``, deliberately a
different shape from ec2.py's provision-once/``serve_model``-swaps split.
This module's own call-time resolvers (``_base_url_template``/``_api_key``/
``_connection``) correspond 1:1 to ec2.py's (``_base_url``/``_api_key``/
``_connection``): same job (build a chat-completions URL and bearer token
per call), but deliberately NOT merged into one shared resolver. Each reads
different env vars and different state -- a static Bedrock/SageMaker bearer
token here vs. EC2's per-instance state file there. A shared function would
need as many branches as there are call sites today, buying nothing over
two small independent implementations.
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
# Default bedrock-mantle base URL, as a format template. This keeps
# ``region`` resolved at CALL time (via ``_region()``) instead of baked in
# here at import time, consistent with the module's call-time
# env-resolution policy for the inference path (see the module docstring).
AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE: str = "https://bedrock-mantle.{region}.api.aws/v1"
# Fallback context window (tokens) for ``get_model_context_length`` when no
# ``AWS_BEDROCK_CONTEXT_LENGTH`` override is set. Bedrock's OpenAI-compatible
# endpoints don't expose per-model context windows, so this is a conservative
# soft default -- see ``get_model_context_length``.
AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH: int = 200000
# Cache of each SageMaker endpoint's served model id (resolved lazily; see
# ``_body_model``). Keyed by endpoint name.
_SERVED_MODELS: Dict[str, str] = {}


def _region() -> str:
    """Return the AWS region hosting the models, read from ``AWS_REGION``.

    Returns
    -------
    str
        ``AWS_REGION`` if set, else ``"us-east-1"``.
    """
    return os.getenv("AWS_REGION", "us-east-1")


def _base_url_template() -> str:
    """Return the full base URL, up to (but excluding) ``/chat/completions``.

    This function defaults to the bedrock-mantle endpoint, AWS's
    OpenAI-compatible surface fronting a broad model catalog (Qwen,
    Mistral, DeepSeek, Gemma, gpt-oss, GLM, Kimi, Nemotron, MiniMax, ...;
    no Anthropic -- see the module docstring; call ``list_models()`` to
    list them).

    Override ``AWS_INFERENCE_BASE_URL`` to reach a different surface:

    - bedrock-runtime's OpenAI surface serves only the OpenAI gpt-oss
      models; it reaches Anthropic and Nova only through Converse/Messages,
      not this API::

          https://bedrock-runtime.{region}.amazonaws.com/openai/v1

    - a SageMaker endpoint::

          https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{ep}/openai/v1

    Returns
    -------
    str
        The ``AWS_INFERENCE_BASE_URL`` env value if set, else the
        bedrock-mantle default templated with ``_region()``. Either way,
        the result has no trailing slash.
    """
    return os.getenv(
        "AWS_INFERENCE_BASE_URL",
        AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE.format(region=_region()),
    ).rstrip("/")


def _api_key() -> str:
    """Return the bearer token, resolved at call time.

    Returns
    -------
    str
        ``AWS_INFERENCE_API_KEY`` (a minted, time-limited SageMaker token)
        if set; otherwise ``AWS_BEARER_TOKEN_BEDROCK`` (AWS's own env-var
        name for the long-lived Bedrock API key), or ``""`` if neither is
        set.
    """
    return os.getenv("AWS_INFERENCE_API_KEY") or os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")


def _resolve_base(model: str) -> str:
    """Fill the ``{model}`` placeholder in the base URL with the endpoint name.

    SageMaker serves one model per endpoint. Set
    ``AWS_INFERENCE_BASE_URL=https://runtime.sagemaker.<region>.amazonaws.com/endpoints/{model}/openai/v1``
    to use it; this function fills the ``{model}`` placeholder with the
    endpoint name on every call.

    Parameters
    ----------
    model : str
        The endpoint name to fill into the ``{model}`` placeholder, when the
        base URL has one.

    Returns
    -------
    str
        The base URL with ``{model}`` replaced by ``model``. With no
        placeholder (bedrock-mantle, which selects the model through the
        request body instead) this function returns the static base URL
        unchanged.
    """
    base = _base_url_template()
    return base.replace("{model}", model) if "{model}" in base else base


def _connection(model: str) -> Tuple[str, str]:
    """Return the chat-completions URL and bearer token for ``model``.

    Parameters
    ----------
    model : str
        Provider-specific model id, forwarded to ``_resolve_base``.

    Returns
    -------
    Tuple[str, str]
        ``(url, token)``: the full chat-completions URL, and the bearer
        token from ``_api_key()``.
    """
    return f"{_resolve_base(model)}/chat/completions", _api_key()


def _body_model(model: str) -> str:
    """Return the OpenAI ``model`` field to put in the request body.

    An explicit ``AWS_INFERENCE_BODY_MODEL`` wins over everything else, and
    applies as one value across all endpoints. Otherwise, for Bedrock (no
    ``{model}`` placeholder) the model id selects the model and this
    function sends it as-is. For a SageMaker single-model endpoint
    (templated base URL) AWS routes by the URL, so the field is nominally
    free -- the vLLM/SGLang DLCs accept ``""``. A *custom* container may
    reject ``""`` and require its served id instead, with a 400 error. This
    function therefore resolves each endpoint's served id once via
    ``list_models`` (cached per endpoint) and falls back to ``""`` if the
    listing is unavailable. This way every endpoint gets the name its own
    container expects.

    Parameters
    ----------
    model : str
        Provider-specific model id (the caller-facing endpoint name).

    Returns
    -------
    str
        The value to send as the request body's ``model`` field.
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
    """Return the configured context window for a model.

    AWS's OpenAI-compatible endpoints expose model ids but not context
    windows. This function returns the ``AWS_BEDROCK_CONTEXT_LENGTH`` env
    override when set, and otherwise ``AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH``.
    It reads the override at CALL time, so a changed or exported env var
    takes effect on the next call with no re-import. Callers use this value
    only as a soft post-hoc token guard, so one value shared across every
    model on the endpoint is an acceptable approximation. There is
    currently no per-model override.

    Parameters
    ----------
    model : str
        Provider-specific model id. This function accepts it for interface
        parity with the other providers' ``get_model_context_length`` (and
        because ``ChatClient.context_length`` calls it as
        ``Callable[[str], int]``). It is unused, since AWS exposes no
        per-model context-window catalog.

    Returns
    -------
    int
        The context window, in tokens, to guard ``usage.total_tokens``
        against.
    """
    return int(os.getenv("AWS_BEDROCK_CONTEXT_LENGTH", str(AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH)))


def list_models(model: str = "") -> list[str]:
    """List model ids available on the configured AWS endpoint.

    This function works on the default bedrock-mantle endpoint and on
    SageMaker endpoints. For a templated SageMaker base URL
    (``.../endpoints/{model}/openai/v1``), pass the endpoint name as
    ``model`` to fill the ``{model}`` placeholder; otherwise the request
    hits a literal ``{model}`` path and fails. The bedrock-runtime OpenAI
    surface does not implement ``GET /models`` (it 404s); there, discover
    ids with ``aws bedrock list-foundation-models`` instead.

    Parameters
    ----------
    model : str, optional
        Endpoint name to fill the ``{model}`` placeholder in the base URL,
        for a templated SageMaker base URL. Default ``""``, correct for the
        default bedrock-mantle endpoint (no placeholder).

    Returns
    -------
    list[str]
        Model ids from the endpoint's ``GET /models`` response ``data``
        list.
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

# The provider-facing API, dispatched via smolbench.evals.provider. Full
# parameter docs live on ChatClient.query / ChatClient.complete / ChatClient.evaluate.
query = _CLIENT.query
complete = _CLIENT.complete  # ChatResult-returning superset of query (usage, model, finish_reason)
evaluate = _CLIENT.evaluate


# ---------------------------------------------------------------------------
# Optional SageMaker endpoint provisioning (lazy boto3; opt-in)
# ---------------------------------------------------------------------------
# A SageMaker endpoint's deploy and teardown need boto3/botocore. The
# inference path does not, so those imports stay *inside* the functions
# below to keep importing this module dependency-free (see module
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
# Per-endpoint deployment spec. The small entry runs within the default
# ml.g5 quota. The big models need a Service Quota increase for their
# instance type (multi-GPU endpoint quotas default to 0), plus likely
# quantization/multi-node tuning -- treat their specs as editable templates.
# Add {"env": {"HF_TOKEN": "hf_..."}} for gated models, or {"image": "..."}
# to override the container.
SAGEMAKER_DEPLOY_SPECS: Dict[str, DeploySpec] = {
    "qwen2.5-1.5b":        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct",                    "instance_type": "ml.g5.2xlarge",  "tp": 1},
    "llama-31-405b":       {"hf_model_id": "meta-llama/Llama-3.1-405B-Instruct",            "instance_type": "ml.p5.48xlarge", "tp": 8},
    "nemotron-ultra-253b": {"hf_model_id": "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1",       "instance_type": "ml.p5.48xlarge", "tp": 8},
    "llama4-maverick":     {"hf_model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct", "instance_type": "ml.p5.48xlarge", "tp": 8},
}


def _is_sagemaker_provider() -> bool:
    """Return whether the active provider targets a SageMaker endpoint.

    Returns
    -------
    bool
        True when the provider targets a SageMaker endpoint, rather than
        serverless Bedrock.
    """
    prov = os.getenv("INFERENCE_PROVIDER", "").lower()
    if prov not in ("aws", "bedrock", "sagemaker"):
        return False
    base = _base_url_template()
    return prov == "sagemaker" or "sagemaker" in base or "{model}" in base


def _sagemaker_client():
    """Return a thin wrapper over ``_aws.fresh_client("sagemaker", _region())``.

    This function stays a locally-named one-liner, rather than calling
    ``_aws.fresh_client`` directly at every call site, so
    ``tests/evals/test_aws_provision.py`` can monkeypatch this one name to
    substitute a recording fake. This exactly mirrors ec2.py's own
    ``_ec2_client`` wrapper.

    Returns
    -------
    Any
        A boto3 SageMaker client from a fresh session (see
        ``_aws.fresh_client``).
    """
    return _aws.fresh_client("sagemaker", _region())


def mint_sagemaker_token(expires: int = 43200) -> str:
    """Mint a short-lived (<=12h) SageMaker bearer token from local AWS creds.

    The token is a base64-encoded SigV4 pre-signed ``CallWithBearerToken``
    URL, the same scheme the SageMaker SDK's ``generate_token`` produces.
    This function implements the scheme with botocore, so the module needs
    no extra SDK.

    Parameters
    ----------
    expires : int, optional
        Token lifetime in seconds. Default 43200 (12h).

    Returns
    -------
    str
        The bearer token, prefixed ``sagemaker-api-key-``.

    Raises
    ------
    RuntimeError
        No local AWS credentials are found.
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
    """Return the SageMaker execution role ARN, creating it (idempotently) if absent.

    This function is a thin wrapper over
    ``_aws.ensure_sagemaker_execution_role(SAGEMAKER_EXEC_ROLE_NAME)``. It
    stays a locally-named one-liner, rather than calling
    ``_aws.ensure_sagemaker_execution_role`` directly from
    ``provision_endpoint``, so tests can monkeypatch this one name. This
    matches the convention ``_sagemaker_client`` and ec2.py's own thin
    wrappers (``_ec2_client``, ``_ensure_instance_profile``) already use.

    Returns
    -------
    str
        The role's ARN.
    """
    return _aws.ensure_sagemaker_execution_role(SAGEMAKER_EXEC_ROLE_NAME)


# Pure kwargs builders -- no AWS I/O, no boto3 import. tests/evals/
# test_aws_provision.py pins each payload by dict equality, with no
# SageMaker client or provision_endpoint context.


def _create_model_kwargs(model: str, spec: DeploySpec, role_arn: str) -> Dict[str, Any]:
    """Build the ``CreateModel`` kwargs for one SageMaker deploy spec.

    Parameters
    ----------
    model : str
        The endpoint name (== the model id passed to ``provision_endpoint``/
        ``query``/``evaluate``). The SageMaker *model* resource created from
        this is named ``f"{model}-model"``, distinct from the endpoint name
        itself, since SageMaker's model/endpoint-config/endpoint are three
        separate named resources.
    spec : DeploySpec
        The deploy spec for ``model`` (typically ``SAGEMAKER_DEPLOY_
        SPECS[model]``). Must have ``spec["hf_model_id"]``; optionally reads
        ``spec.get("image", SAGEMAKER_VLLM_DLC)``, ``spec.get("tp", 1)``, and
        ``spec.get("env", {})``.
    role_arn : str
        The SageMaker execution role ARN (from ``_ensure_exec_role`` /
        ``_aws.ensure_sagemaker_execution_role``) the model assumes at
        runtime.

    Returns
    -------
    Dict[str, Any]
        Kwargs for ``boto3``'s SageMaker ``create_model``. ``Environment``
        merges a fixed base dict (``HF_MODEL_ID``, ``SM_VLLM_TENSOR_
        PARALLEL_SIZE`` as a str, ``SAGEMAKER_ENABLE_LOAD_AWARE``) with
        ``spec.get("env", {})`` via ``|``. The spec dict comes SECOND in
        that merge, so a spec ``env`` key with the same name as a base key
        (e.g. a spec overriding ``SAGEMAKER_ENABLE_LOAD_AWARE``) WINS over
        the base value; an unrelated spec env key is simply added alongside
        the base keys.

    Raises
    ------
    KeyError
        If ``spec`` has no ``"hf_model_id"`` key.

    Notes
    -----
    This function is pure: no AWS I/O, no boto3 import, no side effects.
    Every call with the same arguments returns an equal (independently-
    mutable) dict.
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
    """Build the ``CreateEndpointConfig`` kwargs for one SageMaker deploy spec.

    Parameters
    ----------
    model : str
        The endpoint name. The endpoint config is named ``f"{model}-config"``
        and its single production variant references the model resource
        named ``f"{model}-model"`` (see ``_create_model_kwargs``).
    spec : DeploySpec
        Must have ``spec["instance_type"]`` (the production variant's
        ``InstanceType``, e.g. ``"ml.p5.48xlarge"``).

    Returns
    -------
    Dict[str, Any]
        Kwargs for ``boto3``'s SageMaker ``create_endpoint_config``, with a
        single production variant (``"variant1"``, 1 initial instance, a
        fixed 1800s container-startup health-check timeout). Large
        multi-GPU DLC images can take a while to pull and load.

    Raises
    ------
    KeyError
        If ``spec`` has no ``"instance_type"`` key.

    Notes
    -----
    This function is pure: no AWS I/O, no boto3 import, no side effects.
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
    """Build the ``CreateEndpoint`` kwargs for one SageMaker deploy spec.

    Parameters
    ----------
    model : str
        The endpoint name. This becomes ``EndpointName`` verbatim: the same
        string ``query()``/``evaluate()`` are later called with, and what
        fills the ``{model}`` placeholder in ``AWS_INFERENCE_BASE_URL``.

    Returns
    -------
    Dict[str, Any]
        Kwargs for ``boto3``'s SageMaker ``create_endpoint``, referencing the
        endpoint config named ``f"{model}-config"`` (see
        ``_create_endpoint_config_kwargs``).

    Notes
    -----
    This function is pure: no AWS I/O, no boto3 import, no side effects.
    """
    return {"EndpointName": model, "EndpointConfigName": f"{model}-config"}


def _teardown_steps(sm: Any, model: str) -> List[Tuple[str, Callable[[], Any]]]:
    """Build the ordered ``(label, callable)`` teardown steps for one endpoint.

    Parameters
    ----------
    sm : Any
        A SageMaker client (as returned by ``_sagemaker_client()``) exposing
        ``delete_endpoint``/``delete_endpoint_config``/``delete_model``. This
        parameter is not type-hinted more narrowly than ``Any``, since boto3
        clients are dynamically generated (no static type is available
        without an optional stub-generation dependency). This is consistent
        with the rest of this module's boto3-adjacent code.
    model : str
        The endpoint name. The associated endpoint-config and model
        resources are named ``f"{model}-config"`` / ``f"{model}-model"``
        (see ``_create_endpoint_config_kwargs`` / ``_create_model_kwargs``).

    Returns
    -------
    List[Tuple[str, Callable[[], Any]]]
        Exactly three ``(label, call)`` pairs, in DEPENDENCY-SAFE order:
        ``"endpoint"`` (deletes the endpoint itself, which stops the billed
        instance), then ``"endpoint-config"``, then ``"model"``. Each
        ``call`` is a zero-argument closure over ``sm``/``model`` that
        performs exactly one ``delete_*`` call when invoked. None of the
        three calls run until the caller actually invokes them; building
        this list has no side effects.

    Notes
    -----
    This function returns bare labels (``"endpoint"``, not
    ``f"endpoint {model}"``); ``tests/evals/test_aws_provision.py``'s
    ``test_provision_endpoint_happy_path_full_lifecycle`` pins that shape, and
    ``provision_endpoint``'s ``finally`` block formats the model name into
    its own log lines.
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

    This function deploys the endpoint from ``SAGEMAKER_DEPLOY_SPECS[model]``,
    waits until it is InService, refreshes the bearer token, and yields. It
    GUARANTEES teardown (delete endpoint + endpoint-config + model, which
    stops the billed instance) on exit: on success, on an exception, or on
    KeyboardInterrupt. This function is a no-op for serverless Bedrock and
    non-AWS providers, so wrapping an experiment with it is always safe::

        with provision_endpoint(DENSE_MODEL):
            decode_intens_eval = evaluate(intens_quiz, DENSE_MODEL, SEED)

    Parameters
    ----------
    model : str
        Endpoint name; must be a key of ``SAGEMAKER_DEPLOY_SPECS`` once
        ``_is_sagemaker_provider()`` is true. This function checks that
        eagerly, before any AWS call, so a typo'd model name fails fast.
    timeout_min : int, optional
        Minutes to wait for the endpoint to reach ``InService`` before
        raising ``TimeoutError``. Default 40 (large multi-GPU DLC images can
        take a while to provision, pull, and load).

    Yields
    ------
    str
        ``model``, unchanged. This gives symmetry with the no-op path, so
        ``with provision_endpoint(m) as name:`` gives the same ``name``
        whether or not anything was actually provisioned.

    Raises
    ------
    KeyError
        If ``_is_sagemaker_provider()`` is true and ``model`` has no
        ``SAGEMAKER_DEPLOY_SPECS`` entry.
    RuntimeError
        If the endpoint reaches ``Failed``/``OutOfService`` while waiting for
        ``InService``.
    TimeoutError
        If the endpoint has not reached ``InService`` within ``timeout_min``.

    Notes
    -----
    This function builds its three ``CreateX`` request payloads via
    ``_create_model_kwargs``/``_create_endpoint_config_kwargs``/
    ``_create_endpoint_kwargs`` (pure, offline-pinnable; see
    ``tests/evals/test_aws_provision.py``), and its teardown steps via
    ``_teardown_steps``. It builds on ``_aws.poll_until``'s caller-facing
    `on_timeout`/`check` machinery. See the ``check``/``on_timeout``
    closures below for the wait loop's semantics (deadline consulted only
    after a failed check, the last-seen status embedded in the timeout
    message). Similarly, the
    ``finally`` block does NOT delegate to ``_aws.best_effort_teardown``;
    see that block's own comment for why.
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
        # Design: use one fresh `_sagemaker_client()` per create call, not a
        # single client reused across all three. Each call independently
        # benefits from picking up a just-rotated credentials file (see
        # `_sagemaker_client`'s docstring), and a long-running notebook cell
        # is exactly the case where that matters most.
        _sagemaker_client().create_model(**_create_model_kwargs(model, spec, role))
        _sagemaker_client().create_endpoint_config(**_create_endpoint_config_kwargs(model, spec))
        _sagemaker_client().create_endpoint(**_create_endpoint_kwargs(model))

        # Design: this builds on `_aws.poll_until` (shared with ec2.py's
        # wait loops) rather than a hand-rolled `while True`. `last_status`
        # is threaded through via `nonlocal`, because `on_timeout()` -- called
        # AFTER `check()` returns None and the deadline has passed -- needs
        # the MOST RECENTLY POLLED status to build the TimeoutError message.
        # `poll_until`'s `check` contract is otherwise
        # stateless (it only distinguishes success/None/raise).
        last_status: Optional[str] = None

        def check() -> Optional[bool]:
            nonlocal last_status
            # Use a fresh client each poll, to pick up a rotated/refreshed
            # credential file.
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

        # Refresh the bearer token: a long deploy may have outlived an
        # earlier one. The inference path reads AWS_INFERENCE_API_KEY from
        # the environment at call time, so setting it here is sufficient.
        # No module global needs mutating.
        os.environ["AWS_INFERENCE_API_KEY"] = mint_sagemaker_token()

        yield model
    finally:
        # Guaranteed teardown -- runs on success, error, or interrupt.
        # Hand-rolled rather than delegated to _aws.best_effort_teardown:
        # the success line names the model and the skip line does not, and
        # test_aws_provision.py pins the bare (label, call) shape from
        # _teardown_steps.
        for label, call in _teardown_steps(_sagemaker_client(), model):
            try:
                call()
                logging.info(f"provision_endpoint: torn down {label} {model}")
            except Exception as exc:  # teardown must not mask the body's exception
                logging.info(f"provision_endpoint: teardown skip {label}: {type(exc).__name__}: {exc}")
