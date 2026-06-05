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

Enabling Bedrock model access, deploying a SageMaker endpoint, and minting a
SageMaker token are out-of-band steps; this module stays dependency-free and
only speaks HTTP (no boto3 / sagemaker SDK import). The ``model`` argument is a
model id from the configured endpoint's catalog -- on the default bedrock-mantle
endpoint, e.g. ``anthropic.claude-haiku-4-5``, ``qwen.qwen3-32b``, or
``openai.gpt-oss-120b``; call ``list_models()`` to enumerate them.
"""

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


def list_models() -> list[str]:
    """Lists model ids available on the configured AWS endpoint.

    Works on the default bedrock-mantle endpoint and on SageMaker endpoints. The
    bedrock-runtime OpenAI surface does not implement ``GET /models`` (it 404s);
    there, discover ids with ``aws bedrock list-foundation-models`` instead.
    """
    response = requests.get(
        url=MODELS_URL,
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
                url=URL,
                headers={
                    "Authorization": f"Bearer {AWS_INFERENCE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=(
                    {
                        "model": model,
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
