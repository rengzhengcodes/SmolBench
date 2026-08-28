"""Evaluation harness for OpenAI-compatible inference providers.

``quiz.py``'s public names (``Answer``, ``QnA``, ``ToF``, ``Numeric``,
``Quiz``, ``Mark``, ``Marks``) are re-exported below so ``from
smolbench.evals import Marks`` keeps working and the legacy YAML tag
``!!python/object:smolbench.evals.Marks`` still resolves.

See ``smolbench/evals/README.md`` for the layout and the rationale.
"""

from smolbench.evals.quiz import Answer, QnA, ToF, Numeric, Quiz, Mark, Marks

__all__ = [
    "Answer",
    "QnA",
    "ToF",
    "Numeric",
    "Quiz",
    "Mark",
    "Marks",
]
