"""Shared data types used by the eval harness.

The question/answer structs a quiz is built from (``QnA``, ``ToF``,
``Numeric``), the ``Quiz`` alias, and the ``Mark``/``Marks`` dataclasses
recording one graded quiz. ``Marks`` round-trips through YAML, as a file or an
S3 object body; ``smolbench.evals.results_store`` owns that store.
"""

import re
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from typing import TypeAlias, Sequence, Optional

Answer: TypeAlias = bool | int | str


@dataclass(frozen=True)
class QnA:
    """A quiz question and its ground truth answer."""

    #: Prompt sent to the LLM.
    prompt: str
    #: Ground truth answer for the prompt.
    answer: Answer

    @staticmethod
    def condition(ans: str) -> Answer:
        """Convert a raw model response to this question's answer type.

        Returns `ans` unchanged; subclasses parse and validate.
        """
        return ans

    def score(self, ans: Answer) -> bool:
        """Return whether `ans` (normally `condition`'s output) equals the truth."""
        return ans == self.answer


@dataclass(frozen=True)
class ToF(QnA):
    """A true/false question."""

    def __post_init__(self):
        if not isinstance(self.answer, bool):
            raise ValueError(
                f"self.answer = {self.answer} of type {type(self.answer)} not bool"
            )

    @staticmethod
    def condition(ans: str) -> bool:
        """Convert a raw model response to a bool.

        Case-insensitive, after stripping every non-letter character. The
        lenient recovery path is ``smolbench.evals.parsing.parse_tof``.

        Raises
        ------
        ValueError
            The remainder is not exactly "true"/"false" -- so ``"Answer: False"``
            raises.
        """
        # Strip everything but letters, so wrapping punctuation or markup
        # (e.g. "**True**") does not block the match below.
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

    def __post_init__(self):
        if not isinstance(self.answer, int):
            raise ValueError(f"self.answer = {self.answer} is not int")

    @staticmethod
    def condition(ans: str) -> int:
        """Extract the FIRST integer in a raw model response.

        First-match scores an operand when the model shows its working;
        ``smolbench.evals.parsing.parse_numeric`` is the robust path.

        Raises
        ------
        ValueError
            No integer in the response.
        """
        m = re.search(r"-?\d+", ans)
        if m is None:
            raise ValueError(f"No integer found in '{ans}'")
        return int(m.group())


Quiz: TypeAlias = Sequence[QnA]


@dataclass(frozen=True)
class Mark:
    """One question's grading result."""

    #: Prompt sent to the model.
    query: str
    #: Ground truth answer.
    answer: Answer
    #: Raw, unprocessed model response (the content field only).
    response: str
    #: Score awarded (1=correct, 0=incorrect, None=invalid/unparseable).
    score: Optional[int]
    #: Chain-of-thought reasoning returned by the model, or None.
    reasoning: Optional[str] = None
    #: How the response broke the prompt's output contract; None means it obeyed
    #: the contract exactly. Label values live in `smolbench.evals.parsing`.
    #: Separate from ``score`` so an analysis can tell "the model was wrong" from
    #: "right but broke the format".
    #:
    #: MUST stay optional: stored marks written without it are still read
    #: (``Marks.load`` builds each mark with ``Mark(**m)``), where None means
    #: "not assessed", not "compliant".
    compliance: Optional[str] = None


@dataclass(frozen=True)
class Marks:
    """One model's grading result across a full quiz."""

    #: The model that was evaluated.
    model: str
    #: Per-question marks.
    marks: tuple[Mark, ...]
    #: Date the quiz was run.
    date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    #: Serving-stack snapshot the completions were generated under (instance
    #: type, GPUs, tensor-parallel degree, image, ...), so a result file is
    #: self-describing about its hardware and needs no timestamp -> config side
    #: table. None for a provider with nothing to report, and for stored results
    #: predating the field. A plain default, not a default_factory, so a tagged
    #: file missing the attribute falls back to the class attribute on access.
    server_config: Optional[dict] = None

    @property
    def correct(self) -> int:
        return sum(1 for m in self.marks if m.score == 1)

    @property
    def incorrect(self) -> int:
        return sum(1 for m in self.marks if m.score == 0)

    @property
    def invalid(self) -> int:
        return sum(1 for m in self.marks if m.score is None)

    @property
    def noncompliant(self) -> int:
        """Count the marks whose response broke the prompt's output contract.

        Independent of ``correct``/``incorrect``/``invalid``: a correct response
        can still break the format, so this separates degraded instruction
        following from degraded reasoning.
        """
        return sum(1 for m in self.marks if m.compliance is not None)

    # -- Serialization ------------------------------------------------------
    # A result file is plain-dict YAML (safe_dump of dataclasses.asdict), NOT
    # yaml.dump of the dataclasses: a python-object tag would weld every stored
    # result to this class's import path (a rename would orphan the results tree)
    # and force readers onto yaml.unsafe_load. ``load`` still reads the legacy
    # tagged files this repo already committed. PyYAML lives in the notebook
    # extra, so the imports stay inside the methods.
    #
    # ``dumps``/``loads`` are the str-in/str-out form, ``dump``/``load`` thin path
    # wrappers. The split exists for ``S3ResultsStore``, which round-trips
    # through put_object/get_object bodies with no path to open().

    def dumps(self) -> str:
        """Return this result as a ``yaml.safe_load``-able plain-mapping document."""
        import yaml

        return yaml.safe_dump(asdict(self), default_flow_style=False, indent=4)

    def dump(self, path) -> None:
        """Write `dumps()`'s document to `path` (opened for text write)."""
        with open(path, "w") as file:
            file.write(self.dumps())

    @classmethod
    def loads(cls, text: str) -> "Marks":
        """Load a document written by `dumps`/`dump`, or by the legacy
        ``yaml.dump(marks)`` format (``!!python/object`` tags)."""
        import yaml

        # A legacy file always opens with the top-level Marks tag. Testing the
        # first bytes for that FULL tag (not a substring search, and not the
        # bare "!!python/object" prefix any nested tag also carries) keeps a
        # new-format file whose response text merely quotes a tag off the
        # unsafe path. Committed legacy result files are still read: not dead
        # code.
        if text.startswith("!!python/object:smolbench.evals.Marks"):
            # The tags name this module's class paths, so unsafe_load
            # reconstructs the objects.
            return yaml.unsafe_load(text)
        # libyaml's C loader when available: summaries scan hundreds of MB of
        # result YAML, and the pure-Python loader runs about 10x slower.
        data = yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        return cls(
            model=data["model"],
            marks=tuple(Mark(**m) for m in data["marks"]),
            date=data["date"],
            # .get: a file written before the field existed has no key.
            server_config=data.get("server_config"),
        )

    @classmethod
    def load(cls, path) -> "Marks":
        """Read `path`'s full text and delegate to `loads`."""
        with open(path) as file:
            text = file.read()
        return cls.loads(text)
