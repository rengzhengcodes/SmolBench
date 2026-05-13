"""Defines convenience TypeAlias and structs for evals."""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import TypeAlias, Sequence, Tuple, Optional

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
        return (1, 0) if ans == self.answer else (0, 1)


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
        cleaned_ans = "".join([char for char in ans if char.isalpha()])
        match cleaned_ans.lower():
            case "false":
                return False
            case "true":
                return True
            case _:
                raise ValueError(f"'{ans}' is not a bool.")


@dataclass(frozen=True)
class Numeric(QnA):
    """Integer answer question."""

    def __post_init__(self):
        if not isinstance(self.answer, int):
            raise ValueError(f"self.answer = {self.answer} is not int")

    @staticmethod
    def condition(ans: str) -> int:
        import re
        m = re.search(r"-?\d+", ans)
        if m is None:
            raise ValueError(f"No integer found in '{ans}'")
        return int(m.group())

    def score(self, ans: int) -> Tuple[int, int]:
        return (1, 0) if ans == self.answer else (0, 1)


Quiz: TypeAlias = Sequence[QnA]


@dataclass(frozen=True)
class Mark:
    """Per-question grading result."""

    #: Prompt sent to the model.
    query: str
    #: Ground truth answer.
    answer: Answer
    #: Raw, unprocessed model response (content field only).
    response: str
    #: Score awarded (1=correct, 0=incorrect, None=invalid/unparseable).
    score: Optional[int]
    #: Chain-of-thought reasoning returned by the model, if any.
    reasoning: Optional[str] = None


@dataclass(frozen=True)
class Marks:
    """Grading result of the LLM across a full quiz."""

    #: The model that was evaluated.
    model: str
    #: Per-question marks.
    marks: tuple[Mark, ...]
    #: Date the quiz was run.
    date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def correct(self) -> int:
        return sum(1 for m in self.marks if m.score == 1)

    @property
    def incorrect(self) -> int:
        return sum(1 for m in self.marks if m.score == 0)

    @property
    def invalid(self) -> int:
        return sum(1 for m in self.marks if m.score is None)
