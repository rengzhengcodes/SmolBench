"""Question, grading, and YAML result types for evaluations."""

import os
import re
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TypeAlias, Sequence, Optional

Answer: TypeAlias = bool | int | str


@dataclass(frozen=True)
class QnA:
    """A quiz question and its ground truth answer."""

    #: Model prompt.
    prompt: str
    #: Expected answer.
    answer: Answer

    @staticmethod
    def condition(ans: str) -> Answer:
        """Convert a raw response."""
        return ans

    def score(self, ans: Answer) -> bool:
        """Return whether `ans` is correct."""
        return ans == self.answer


@dataclass(frozen=True)
class ToF(QnA):
    """A true/false question."""

    def __post_init__(self) -> None:
        if not isinstance(self.answer, bool):
            raise ValueError(
                f"self.answer = {self.answer} of type {type(self.answer)} not bool"
            )

    @staticmethod
    def condition(ans: str) -> bool:
        """Convert a raw response to a boolean.

        Strip nonletters; accept only ``true`` or ``false``.

        Parameters
        ----------
        ans : str
        Returns
        -------
        bool
        """
        # `isalpha` retains Unicode letters without a maintained charset.
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
    """An integer-answer question."""

    def __post_init__(self) -> None:
        if not isinstance(self.answer, int):
            raise ValueError(f"self.answer = {self.answer} is not int")

    @staticmethod
    def condition(ans: str) -> int:
        """Extract the first response integer.

        First-match handles responses with working.

        Parameters
        ----------
        ans : str
        Returns
        -------
        int
        """
        m = re.search(r"-?\d+", ans)
        if m is None:
            raise ValueError(f"No integer found in '{ans}'")
        return int(m.group())


Quiz: TypeAlias = Sequence[QnA]


#: Compliance label, explicit to prevent truthiness inversions.
COMPLIANT = "compliant"


@dataclass(frozen=True)
class Mark:
    """One question's grading result."""

    #: Model prompt.
    query: str
    #: Expected answer.
    answer: Answer
    #: Raw response content.
    response: str
    #: `1` correct, `0` incorrect, or `None` invalid.
    score: Optional[int]
    #: Format label, independent of correctness.
    compliance: str
    #: Returned reasoning, if any.
    reasoning: Optional[str] = None


@dataclass(frozen=True)
class Marks:
    """One model's grading result across a full quiz."""

    #: Evaluated model.
    model: str
    #: Per-question results.
    marks: tuple[Mark, ...]
    #: Run date.
    date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    #: Serving-stack snapshot.
    server_config: Optional[dict] = None
    #: Source run timestamp; S3 logs are append-only.
    regraded_from: Optional[str] = None

    @property
    def correct(self) -> int:
        """Return the number of correct marks."""
        return sum(1 for m in self.marks if m.score == 1)

    @property
    def incorrect(self) -> int:
        """Return the number of incorrect marks."""
        return sum(1 for m in self.marks if m.score == 0)

    @property
    def invalid(self) -> int:
        """Return the number of invalid marks."""
        return sum(1 for m in self.marks if m.score is None)

    @property
    def noncompliant(self) -> int:
        """Count format violations independent of correctness."""
        return sum(1 for m in self.marks if m.compliance != COMPLIANT)

    # Plain YAML mappings avoid Python-object tags and unsafe loaders.

    def dumps(self) -> str:
        """Return a safe-loadable YAML mapping."""
        import yaml

        return yaml.safe_dump(asdict(self), default_flow_style=False, indent=4)

    def dump(self, path: Path) -> None:
        """Write YAML atomically.

        Resume skips require intact existing files.

        Parameters
        ----------
        path : Path
        """
        tmp = f"{path}.tmp"
        with open(tmp, "w") as file:
            file.write(self.dumps())
        os.replace(tmp, path)

    @classmethod
    def loads(cls, text: str) -> "Marks":
        """Load a YAML document written by this class."""
        import yaml

        # Prefer the C loader for large summaries.
        data = yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        return cls(
            model=data["model"],
            marks=tuple(Mark(**m) for m in data["marks"]),
            date=data["date"],
            server_config=data["server_config"],
            regraded_from=data["regraded_from"],
        )

    @classmethod
    def load(cls, path: Path) -> "Marks":
        """Load YAML from `path`."""
        with open(path) as file:
            text = file.read()
        return cls.loads(text)
