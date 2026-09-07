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


#: ``Mark.compliance`` value meaning "the response obeyed the output contract
#: exactly". An explicit label rather than ``None`` so a stored row is
#: self-describing and a truthiness test cannot invert compliant against a
#: violation label.
COMPLIANT = "compliant"


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
    #: How the response broke the prompt's output contract: a violation label
    #: from `smolbench.evals.parsing`, or `COMPLIANT` when it obeyed the
    #: contract exactly. Separate from ``score`` so an analysis can tell "the
    #: model was wrong" from "right but broke the format".
    compliance: str
    #: Chain-of-thought reasoning returned by the model, or None.
    reasoning: Optional[str] = None


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
    #: The ``run_ts`` (see ``results_store.format_run_ts``) of the run this one
    #: RE-GRADES, or ``None`` for an original collection. Set only by
    #: ``ResultsStore.regrade``, never by ``ReplicateHarness.run_replicates``,
    #: which only ever collects originals. The append-only S3 log can never be
    #: edited in place, so a re-graded row has to carry its own provenance to
    #: stay self-describing -- a reader sees a ``Marks`` and can always tell
    #: whether it replaces an earlier judgement of the SAME collected
    #: responses (a regrade) versus a fresh collection, with no side table to
    #: consult. LAST field (after `server_config`): a pure tail addition, so
    #: nothing about the existing plain-dict document's shape changes for it.
    #: A plain default, not a default_factory, so a stored file predating this
    #: field falls back to the class attribute, `None`, exactly as
    #: `server_config` does above.
    regraded_from: Optional[str] = None

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
        following from degraded reasoning. ``len(marks)`` is the denominator
        for a non-compliance rate.
        """
        return sum(1 for m in self.marks if m.compliance != COMPLIANT)

    # -- Serialization ------------------------------------------------------
    # A result file is plain-dict YAML (safe_dump of dataclasses.asdict), NOT
    # yaml.dump of the dataclasses: a python-object tag would weld every stored
    # result to this class's import path (a rename would orphan the results tree)
    # and force readers onto yaml.unsafe_load. PyYAML lives in the notebook
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
        """Load a document written by `dumps`/`dump`."""
        import yaml

        # libyaml's C loader when available: summaries scan hundreds of MB of
        # result YAML, and the pure-Python loader runs about 10x slower.
        data = yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        return cls(
            model=data["model"],
            marks=tuple(Mark(**m) for m in data["marks"]),
            date=data["date"],
            # .get: a file written before the field existed has no key.
            server_config=data.get("server_config"),
            regraded_from=data.get("regraded_from"),
        )

    @classmethod
    def load(cls, path) -> "Marks":
        """Read `path`'s full text and delegate to `loads`."""
        with open(path) as file:
            text = file.read()
        return cls.loads(text)
