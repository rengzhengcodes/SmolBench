"""Define the shared data types used by the eval harness.

This module holds the question/answer structs a quiz is built from
(``QnA``, ``ToF``, ``Numeric``), the ``Quiz`` type alias, and the
``Mark``/``Marks`` dataclasses that record one graded quiz. ``Marks``
also serializes to and loads from YAML, so a graded quiz round-trips
through a file or an S3 object. See ``smolbench.evals.results_store``
for the store that reads and writes this format.
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

        The base implementation returns `ans` unchanged. A subclass
        overrides this to parse and validate the raw response text.

        Parameters
        ----------
        ans : str
            Raw model response text.

        Returns
        -------
        Answer
            `ans`, unchanged.
        """
        return ans

    def score(self, ans: Answer) -> bool:
        """Return whether `ans` matches this question's ground truth.

        Parameters
        ----------
        ans : Answer
            A conditioned answer, normally the output of `condition`.

        Returns
        -------
        bool
            True when `ans` equals ``self.answer``.
        """
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

        Parameters
        ----------
        ans : str
            Raw model response text.

        Returns
        -------
        bool
            True for "true", False for "false" (case-insensitive, after
            every non-letter character is stripped).

        Raises
        ------
        ValueError
            `ans` does not reduce to "true" or "false" once the
            non-letter characters are stripped.
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
        """Extract the first integer in a raw model response.

        Parameters
        ----------
        ans : str
            Raw model response text.

        Returns
        -------
        int
            The first integer substring found in `ans`.

        Raises
        ------
        ValueError
            `ans` contains no integer.
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
    #: How the response broke the prompt's output contract. None means the
    #: response obeyed the contract exactly. See `smolbench.evals.parsing`
    #: for the label values.
    #:
    #: This field is kept separate from ``score``. That split lets an
    #: analysis tell "the model was wrong" apart from "the model was right
    #: but broke the format". Before this field existed, both cases
    #: counted as the same failure: the strict parser could not read a
    #: non-compliant response, so it scored as a failure either way.
    #:
    #: The default is None, not a required value. A replicate YAML written
    #: before this field existed still loads (``Marks.load`` builds each
    #: mark with ``Mark(**m)``). For such an old mark, None means "not
    #: assessed", not "compliant".
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
    #: Serving-stack snapshot the completions were generated under
    #: (instance type, GPUs, tensor-parallel degree, image, ...). This is
    #: provenance: it makes a result file self-describing about its
    #: hardware, so a reader does not need a separate timestamp -> config
    #: side table (the 2026-08-13 confound audit had to reconstruct
    #: exactly that table). None on a result written before this field
    #: existed, and for a provider with nothing meaningful to report. The
    #: default is a plain value, not a default_factory, so a legacy
    #: ``!!python/object`` file missing the attribute still falls back to
    #: the class attribute on access.
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

        This count is independent of ``correct``/``incorrect``/``invalid``:
        a response can be graded correct and still have broken the format.
        That population matters when a condition (the induction
        ``noise_intens`` arm, for example) is suspected of degrading
        instruction following rather than reasoning.
        """
        return sum(1 for m in self.marks if m.compliance is not None)

    # -- Serialization ------------------------------------------------------
    # A result file is plain-dict YAML (safe_dump of dataclasses.asdict), NOT
    # yaml.dump of the dataclasses themselves. A python-object tag would weld
    # every stored result to this class's import path, so a rename or move
    # would orphan the whole results tree, and would force readers to use
    # yaml.unsafe_load. ``load`` still reads the legacy tagged files this
    # repo already committed. PyYAML lives in the notebook extra, so the
    # imports stay inside the methods and the base package stays
    # dependency-light.
    #
    # ``dumps``/``loads`` do the actual (de)serialization to and from an
    # in-memory str; ``dump``/``load`` are thin ``path``-based wrappers
    # around them. This split exists because a result may live in
    # ``smolbench.evals.results_store``'s S3 backend, where there is no
    # local path to ``open()``. An ``S3ResultsStore`` round-trips through
    # ``put_object``/``get_object`` request/response bodies (bytes over the
    # wire), not a filesystem, so it needs the str-in/str-out form directly.
    # ``LocalResultsStore`` and every pre-existing on-disk caller keep using
    # ``dump``/``load`` unchanged.

    def dumps(self) -> str:
        """Serialize this result to a plain-mapping YAML string.

        Returns
        -------
        str
            A ``yaml.safe_load``-able document.

        Notes
        -----
        With no ``stream`` argument, ``yaml.safe_dump`` RETURNS the
        document as a str, instead of writing it somewhere. That is what a
        caller with no filesystem path needs (for example, an S3
        ``put_object`` body).
        """
        import yaml

        return yaml.safe_dump(asdict(self), default_flow_style=False, indent=4)

    def dump(self, path) -> None:
        """Serialize this result to `path` as plain-mapping YAML.

        Thin wrapper around `dumps`. Writing `path` gives the same bytes
        `dumps` returns.

        Parameters
        ----------
        path : path-like
            Destination file. Opened for text write.
        """
        with open(path, "w") as file:
            file.write(self.dumps())

    @classmethod
    def loads(cls, text: str) -> "Marks":
        """Load a result document from `text`.

        Parameters
        ----------
        text : str
            A document written by `dumps`/`dump`, or by the legacy
            ``yaml.dump(marks)`` format (``!!python/object`` tags).

        Returns
        -------
        Marks
        """
        import yaml

        # A legacy file always opens with the top-level Marks tag. Testing
        # the first bytes (not a substring search) keeps a NEW-format file
        # whose response text merely mentions "!!python/object" off the
        # unsafe path. Legacy files are still read back after being seeded
        # into S3, so this branch is load-bearing, not dead code.
        if text.startswith("!!python/object"):
            # Legacy tagged file: the tags reference this module's class
            # paths directly, so unsafe_load reconstructs the objects.
            return yaml.unsafe_load(text)
        # Prefer libyaml's C loader when it is available. Summaries scan
        # hundreds of MB of result YAML, and the pure-Python loader runs
        # about 10x slower.
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
        """Load a result file written by `dump`, or by the legacy format.

        Thin wrapper around `loads`. Reads `path`'s full text, then
        delegates.

        Parameters
        ----------
        path : path-like
            File written by `dump`, or by the legacy
            ``yaml.dump(marks)`` format (``!!python/object`` tags).

        Returns
        -------
        Marks
        """
        with open(path) as file:
            text = file.read()
        return cls.loads(text)
