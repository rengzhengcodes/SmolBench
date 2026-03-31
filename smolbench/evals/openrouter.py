"""
Interfacing directly with the OpenRouter API.
"""

import os

import requests
from dotenv import load_dotenv

from smolbench.evals import Answer, QnA, Quiz, Marks

load_dotenv(verbose=True)
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", None)
URL: str = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEBUG: bool = bool(int(os.getenv("OPENROUTER_DEBUG", 0)))
OPENROUTER_DEBUG_RESPONSE: bool = bool(int(os.getenv("OPENROUTER_DEBUG_RESPONSE", 0)))


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
    response = requests.post(
        url=URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        },
        timeout=5,
    )

    if not response.ok:
        print(response.text)  
  
    response.raise_for_status()
    body = response.json()
    if OPENROUTER_DEBUG and OPENROUTER_DEBUG_RESPONSE:
        print(body)

    return body["choices"][0]["message"]["content"]


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
        except ValueError as e:
            invalid += 1
            if OPENROUTER_DEBUG:
                print(e)
            continue

        # Marks any sensical answers and updates scoring.
        part_correct, part_incorrect = q.score(response)
        correct += part_correct
        incorrect += part_incorrect

    return Marks(
        quiz=quiz, model=model, correct=correct, incorrect=incorrect, invalid=invalid
    )
