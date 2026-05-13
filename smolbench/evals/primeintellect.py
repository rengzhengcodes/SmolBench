"""
Interfacing directly with the Prime Intellect inference API.
"""

import logging
import os
import time
from typing import Any, Optional, Dict, Tuple

import requests
from joblib import Parallel, delayed

from smolbench.evals import Answer, QnA, Quiz, Mark, Marks

PRIME_INTELLECT_API_KEY: str = os.getenv("PRIME_INTELLECT_API_KEY", None)
URL: str = "https://api.pinference.ai/api/v1/chat/completions"
PRIME_INTELLECT_INFO: bool = bool(int(os.getenv("PRIME_INTELLECT_INFO", "0")))
PRIME_INTELLECT_INFO_RESPONSE: bool = bool(
    int(os.getenv("PRIME_INTELLECT_INFO_RESPONSE", "0"))
)
PRIME_INTELLECT_MAX_PARALLEL_REQUESTS: int = int(
    os.getenv("PRIME_INTELLECT_MAX_PARALLEL_REQUESTS", "8")
)
PRIME_INTELLECT_RETRY_BACKOFF_SECONDS: int = 60


def _is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True

        return response.status_code == 429 or 500 <= response.status_code < 600

    return True


def get_model_context_length(model: str) -> int:
    """Fetches the model context window from Prime Intellect."""
    response: Dict[str, Any] = requests.get(
        url=f"https://api.pinference.ai/api/v1/models/{model}",
        headers={
            "Authorization": f"Bearer {PRIME_INTELLECT_API_KEY}",
        },
        timeout=120,
    ).json()

    ctx: int = response["context_length"]
    return ctx


def query(
    prompt: str,
    model: str,
    seed: int,
    context_length: int = 0,
    extra_args: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Queries a model using Prime Intellect.

    Parameters
    ----------
    prompt:
        The content posed to the LLM we expect an answer from.
    model:
        The model to evaluate on Prime Intellect.
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
    while True:
        attempt += 1
        try:
            response = requests.post(
                url=URL,
                headers={
                    "Authorization": f"Bearer {PRIME_INTELLECT_API_KEY}",
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
            if PRIME_INTELLECT_INFO and PRIME_INTELLECT_INFO_RESPONSE:
                logging.info(body)

            msg = body["choices"][0]["message"]
            if msg["content"] is None:
                logging.warning("Body returned none value: \n" f"{body}")
                return "", None
            if (tokens := body["usage"]["total_tokens"]) > context_length:
                raise ValueError(f"Response:\n{body}\n was {tokens} > {context_length}")
            if PRIME_INTELLECT_INFO:
                logging.info(f"Response:\n{body}\n was {tokens} <= {context_length}")
            return msg["content"], msg.get("reasoning")

        except requests.exceptions.RequestException as err:
            if not _is_retryable_request_error(err):
                raise
            logging.info(
                f"Prime Intellect request failed on attempt {attempt}: {err}. "
                f"Retrying in {PRIME_INTELLECT_RETRY_BACKOFF_SECONDS} seconds."
            )
            time.sleep(PRIME_INTELLECT_RETRY_BACKOFF_SECONDS)


def evaluate(
    quiz: Quiz, model: str, seed: int, extra_args: Optional[Dict[str, Any]] = None
) -> Marks:
    """Evaluates a model given a sequence of quizzes."""
    ctx_len: int = get_model_context_length(model)
    max_workers: int = max(1, min(len(quiz), PRIME_INTELLECT_MAX_PARALLEL_REQUESTS))
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
            if PRIME_INTELLECT_INFO:
                logging.info(e)
            mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=None))
            continue

        part_correct, _ = q.score(conditioned)
        mark_list.append(Mark(query=q.prompt, answer=q.answer, response=raw, reasoning=reasoning, score=part_correct))

    return Marks(model=model, marks=tuple(mark_list))
