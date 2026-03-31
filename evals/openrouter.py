"""
Interfacing directly with the OpenRouter API.
"""

import os
import json
import requests

from typing import Sequence
from evals import QnA

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
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        data = json.dumps({
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
    )


def eval(quiz: Sequence[QnA], model: str) -> str:
    """
    Evaluates a model using 
    """