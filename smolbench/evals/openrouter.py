"""
Interfacing directly with the OpenRouter API.
"""

import logging
import os
import time
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from joblib import Parallel, delayed

from smolbench.evals import Answer, QnA, Quiz, Marks

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", None)
URL: str = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEBUG: bool = bool(int(os.getenv("OPENROUTER_DEBUG", "0")))
OPENROUTER_DEBUG_RESPONSE: bool = bool(int(os.getenv("OPENROUTER_DEBUG_RESPONSE", "0")))
OPENROUTER_MAX_PARALLEL_REQUESTS: int = int(
    os.getenv("OPENROUTER_MAX_PARALLEL_REQUESTS", "8")
)
OPENROUTER_RETRY_BACKOFF_SECONDS: int = 60


def _is_retryable_request_error(err: requests.exceptions.RequestException) -> bool:
    """
    Returns whether an OpenRouter request error should be retried.
    """
    if isinstance(err, requests.exceptions.HTTPError):
        response = err.response
        if response is None:
            return True

        return response.status_code == 429 or 500 <= response.status_code < 600

    return True


def query(
    prompt: str, model: str, seed: int, extra_args: Optional[Dict[str, Any]] = {}
) -> str:
    """
    Queries a model using openrouter.

    Parameters
    ----------
    prompt:
        The content posed to the LLM we expect an answer from.
    model:
        The model to evaluate on OpenRouter.

    Returns
    -------
    The model's output.
    """
    attempt: int = 0
    # Keep attempting to get a result until one is provisioned.
    while True:
        attempt += 1
        # Tries to get a non-error code response from OpenRouter.
        try:
            response = requests.post(
                url=URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "seed": seed
                } | extra_args,
                timeout=120,
            )

            if not response.ok:
                logging.info(response.text)

            response.raise_for_status()
            body = response.json()
            if OPENROUTER_DEBUG and OPENROUTER_DEBUG_RESPONSE:
                logging.debug(body)

            if body["choices"][0]["message"]["content"] is None:
                logging.warning("Body returned none value: \n" f"{body}")
                return ""
            else:
                return body["choices"][0]["message"]["content"]

        # Attempts to retry exceptions if possible.
        except requests.exceptions.RequestException as err:
            if not _is_retryable_request_error(err):
                raise
            logging.info(
                f"OpenRouter request failed on attempt {attempt}: {err}. "
                f"Retrying in {OPENROUTER_RETRY_BACKOFF_SECONDS} seconds."
            )
            time.sleep(OPENROUTER_RETRY_BACKOFF_SECONDS)


def evaluate(
    quiz: Quiz, model: str, seed: int, extra_args: Optional[Dict[str, Any]] = {}
) -> Marks:
    """
    Evaluates a model given a sequence of quizzes.

    Postconditions
    --------------

    """
    # Quiz response marking bookkeeping.
    correct: int = 0
    incorrect: int = 0
    invalid: int = 0

    # Batches the requests across workers.
    max_workers: int = max(1, min(len(quiz), OPENROUTER_MAX_PARALLEL_REQUESTS))
    responses: list[str] = Parallel(n_jobs=max_workers, prefer="threads")(
        delayed(query)(q.prompt, model, seed, extra_args) for q in quiz
    )

    # Marks the responses after all requests complete.
    q: QnA
    response: str
    for q, response in zip(quiz, responses):
        if OPENROUTER_DEBUG:
            logging.debug(correct, incorrect, invalid)
        # Tracks if the response given is "nonsensical."
        try:
            response: Answer = q.condition(response)
        except ValueError as e:
            invalid += 1
            if OPENROUTER_DEBUG:
                logging.debug(e)
            continue

        # Marks any sensical answers and updates scoring.
        part_correct, part_incorrect = q.score(response)
        correct += part_correct
        incorrect += part_incorrect

    return Marks(
        quiz=quiz, model=model, correct=correct, incorrect=incorrect, invalid=invalid
    )
