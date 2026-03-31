from dataclasses import dataclass
from typing import TypeAlias


Answer: TypeAlias = bool | int | str
@dataclass(static=True, slots=True)
class QnA:
    """Question and Answer struct we expect."""
    prompt: str
    # Prompt that is queried to the LLM.
    answer: Answer
    # Ground truth tot he prompt.
    conditioner: Callable[[str], Answer] = lambda ans: ans
    # Codnitions the LLM response to match that of answer key.
