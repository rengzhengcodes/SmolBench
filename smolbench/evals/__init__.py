"""Defines convenience TypeAlias and structs for evals."""

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import TypeAlias, Sequence, Tuple

Answer: TypeAlias = bool | int | str


@dataclass(frozen=True)
class QnA:
    """Question and Answer struct we expect."""

    #: Prompt that is queried to the LLM.
    prompt: str
    #: Ground truth tot he prompt.
    answer: Answer

    @staticmethod
    def condition(ans: str) -> Answer:
        """Conditions the LLM response to match that of answer key."""
        return ans

    def score(self, ans: Answer) -> Tuple[int, int]:
        """
        Scoring function for the conditioned answer from the LLM.

        Returns
        -------
        Correct Score, Incorrect Score
        """
        return 1, 0 if ans == self.answer else 0, 1


@dataclass(frozen=True)
class ToF(QnA):
    """True or False question."""

    def __post_init__(self):
        if not isinstance(self.answer, bool):
            raise ValueError(
                f"self.answer = {self.answer} of type {type(self.answer)} not bool"
            )

    @staticmethod
    def condition(ans: str) -> bool:
        """Conditions response to be a bool."""
        # Prepossesses answer to isolate only letters.
        ans = "".join([char for char in ans if char.isalpha()])
        match ans.lower():
            case "false":
                return False
            case "true":
                return True
            case _:
                raise ValueError(f"'{ans}' is not a bool.")


Quiz: TypeAlias = Sequence[QnA]


@dataclass(frozen=True)
class Marks:
    """Grading result of the LLM."""

    #: What the marks were generated from.
    quiz: Quiz
    #: The model answering the quiz.
    model: str
    #: Number of responses correct.
    correct: int
    #: Number of responses incorrect.
    incorrect: int
    #: Number of responses excluded due to incorrect LLM formatting.
    invalid: int
    #: Date the quiz was generated.
    date: datetime = datetime.now(timezone.utc)
