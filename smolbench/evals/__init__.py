"""Defines convenience TypeAlias and structs for evals."""

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import TypeAlias, Callable, Sequence

Answer: TypeAlias = bool | int | str


@dataclass(slots=True)
class QnA:
    """Question and Answer struct we expect."""

    #: Prompt that is queried to the LLM.
    prompt: str
    #: Ground truth tot he prompt.
    answer: Answer
    # Conditions the LLM response to match that of answer key.
    condition: Callable[[str], Answer] = lambda ans: ans


Quiz: TypeAlias = Sequence[QnA]


@dataclass(slots=True)
class Marks:
    """Grading result of the LLM."""

    #: What the marks were generated from.
    quiz: Quiz
    #: The model answering the quiz.
    model: str
    #: Date the quiz was generated.
    date: datetime = datetime.now(timezone.utc)
    #: Number of responses correct.
    correct: int
    #: Number of responses incorrect.
    incorrect: int
    #: Number of responses excluded due to incorrect LLM formatting.
    invalid: int
