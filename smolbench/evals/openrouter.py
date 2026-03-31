"""
Interfacing directly with the OpenRouter API.
"""

import os
import json

import requests
from smolbench.evals import Answer, QnA, Quiz, Marks

OPENROUTER_API_KEY: str = os.environ["OPENROUTER_API_KEY"]
URL: str = "https://openrouter.ai/api/v1/chat/completion"


def query(prompt: str, model: str) -> str:
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
    return requests.post(
        url=URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        data=json.dumps(
            {"model": model, "messages": [{"role": "user", "content": prompt}]}
        ),
        timeout=5,
    )


def evaluate(quiz: Quiz, model: str) -> Marks:
    """
    Evaluates a model given a sequence of quizzes.

    Postconditions
    --------------

    """
    # Quiz response marking bookkeeping.
    correct: int = 0
    incorrect: int = 0
    invalid: int = 0

    # Asks all questions in the quiz.
    q: QnA
    for q in quiz:
        # Gets the response from the LLM.
        response: str = query(q.prompt, model)
        # Tracks if the response given is "nonsensical."
        try:
            response: Answer = q.condition(response)
        except ValueError:
            invalid += 1
            continue

        # Marks any sensical answers and updates scoring.
        part_correct, part_incorrect = q.score()
        correct += part_correct
        incorrect += part_incorrect

    return Marks(
        quiz=quiz, model=model, correct=correct, incorrect=incorrect, invalid=invalid
    )
