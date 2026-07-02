"""Defines convenience TypeAlias and structs for evals."""

import re
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from typing import TypeAlias, Sequence, Optional

Answer: TypeAlias = bool | int | str


@dataclass(frozen=True)
class QnA:
    """Question and Answer struct we expect."""

    #: Prompt that is queried to the LLM.
    prompt: str
    #: Ground truth answer to the prompt.
    answer: Answer

    @staticmethod
    def condition(ans: str) -> Answer:
        """Conditions the LLM response to match that of answer key."""
        return ans

    def score(self, ans: Answer) -> bool:
        """Returns whether the conditioned answer matches the ground truth."""
        return ans == self.answer


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
        # Preprocesses the answer to isolate only letters.
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
        m = re.search(r"-?\d+", ans)
        if m is None:
            raise ValueError(f"No integer found in '{ans}'")
        return int(m.group())


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

    # -- Serialization ------------------------------------------------------
    # Result files are plain-dict YAML (safe_dump of dataclasses.asdict), NOT
    # yaml.dump of the dataclasses themselves: python-object tags would weld
    # every stored result to this class's import path (a rename/move orphans
    # the whole results tree) and force readers into yaml.unsafe_load.
    # ``load`` still reads the legacy tagged files this repo already
    # committed. PyYAML lives in the notebook extra, so the imports stay
    # inside the methods and the base package remains dependency-light.

    def dump(self, path) -> None:
        """Serializes to ``path`` as plain-mapping YAML (safe_load-able)."""
        import yaml

        with open(path, "w") as file:
            yaml.safe_dump(asdict(self), file, default_flow_style=False, indent=4)

    @classmethod
    def load(cls, path) -> "Marks":
        """Loads a result file written by ``dump`` or by the legacy
        ``yaml.dump(marks)`` format (``!!python/object`` tags)."""
        import yaml

        with open(path) as file:
            text = file.read()
        # Legacy files always open with the top-level Marks tag; testing the
        # first bytes (not a substring search) keeps a NEW-format file whose
        # response text merely mentions "!!python/object" off the unsafe path.
        if text.startswith("!!python/object"):
            # Legacy tagged file: the tags reference this module's class
            # paths directly, so unsafe_load reconstructs the objects.
            return yaml.unsafe_load(text)
        # libyaml's C loader when available (summaries scan hundreds of MB of
        # result YAML; the pure-python loader is ~10x slower).
        data = yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        return cls(
            model=data["model"],
            marks=tuple(Mark(**m) for m in data["marks"]),
            date=data["date"],
        )
