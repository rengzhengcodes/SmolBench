"""Shared data types used by the eval harness.

The question/answer structs a quiz is built from (``QnA``, ``ToF``,
``Numeric``), the ``Quiz`` alias, and the ``Mark``/``Marks`` dataclasses
recording one graded quiz. ``Marks`` round-trips through YAML, as a file or an
S3 object body; ``smolbench.evals.results_store`` owns that store.
"""

import os
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
        # (e.g. "**True**") does not block the match below. Not a regex sub:
        # measured equal at answer-sized inputs (~0.15us either way; regex only
        # wins past ~200 chars, where this parser rejects anyway), and
        # str.isalpha keeps the Unicode letter class without a charset to
        # maintain.
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


#: ``Mark.compliance`` value meaning "assessed: the response obeyed the output
#: contract exactly". None (YAML ``null``) rather than a marker string, because
#: the S3 results log is append-only: files already written cannot be rewritten,
#: so a new marker string would sit in old files' place and read as one more
#: violation mode to every reader that classifies by label. Both readers key on
#: ``compliance: null`` == obeyed -- ``Marks.noncompliant`` (the census
#: numerator) and ``Marks.assessed`` (its denominator).
COMPLIANT = None
#: ``Mark.compliance`` value meaning "never run through the compliance-aware
#: parser". The field's DEFAULT, so a stored mark predating the field (loaded
#: via ``Mark(**m)`` with no ``compliance`` key, or a legacy tagged file whose
#: attribute lookup falls back to the class attribute) reads as not-assessed
#: instead of masquerading as `COMPLIANT`.
NOT_ASSESSED = "not-assessed"


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
    #: How the response broke the prompt's output contract: a violation label
    #: from `smolbench.evals.parsing`, `COMPLIANT` (None) when it obeyed the
    #: contract exactly, or `NOT_ASSESSED` when nothing ever judged it -- the
    #: default, so legacy stored marks that lack the field load as
    #: not-assessed rather than as compliant. Separate from ``score`` so an
    #: analysis can tell "the model was wrong" from "right but broke the
    #: format".
    compliance: Optional[str] = NOT_ASSESSED


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
        following from degraded reasoning. `NOT_ASSESSED` marks (legacy files)
        count as neither compliant nor noncompliant.
        """
        return sum(
            1 for m in self.marks if m.compliance not in (COMPLIANT, NOT_ASSESSED)
        )

    @property
    def assessed(self) -> int:
        """Count the marks a compliance-aware parser actually judged.

        The DENOMINATOR for a non-compliance rate,
        ``noncompliant / assessed``. A mark is assessed when it carries either
        `COMPLIANT` (it obeyed the contract) or a violation label; every
        `noncompliant` mark is therefore assessed, so a rate taken over this
        can never exceed 1.0.

        `NOT_ASSESSED` marks are UNKNOWN, not compliant: it is the field's
        default, so stored results predating the field load as not-assessed.
        They are excluded from BOTH numerator and denominator, which is what
        keeps a wholly legacy lane from publishing as a 100% collapse (it would
        otherwise look like every mark violated the contract, or like every
        mark obeyed it, depending on which way the default were read).

        Callers MUST guard the division: a `Marks` whose every mark is
        `NOT_ASSESSED` returns 0, and there is no meaningful rate to report for
        it -- the right output is "unmeasured", not a number.
        """
        return sum(1 for m in self.marks if m.compliance != NOT_ASSESSED)

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
        """Write `dumps()`'s document to `path` atomically (tmp + ``os.replace``).

        Resume-skips gate on bare file presence (``ResultsStore.exists``), so
        a file that exists must never be a torn write: an interrupted dump
        would otherwise be skipped as already-collected forever.
        """
        tmp = f"{path}.tmp"
        with open(tmp, "w") as file:
            file.write(self.dumps())
        os.replace(tmp, path)

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
