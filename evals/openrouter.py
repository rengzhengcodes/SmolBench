"""
Interfacing directly with the OpenRouter API.
"""

from typing import Sequence
from evals import QnA

def prompt(query: str, model: str) -> str:
    """
    Prompts a model using openrouter.

    Parameters
    ----------
    qna:
        The question and expected answer from the LLM.
    model:
        The model to evaluate on OpenRouter.
    
    Returns
    -------
    The model's output.
    """
    pass


def eval(quiz: Sequence[QnA], model: str) -> str:
    """
    Evaluates a model using 
    """