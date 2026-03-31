from dataclasses import dataclass

@dataclass(static=True, slots=True)
class QnA:
    """Question and Answer struct we expect."""
    prompt: str
    answer: bool | int | str