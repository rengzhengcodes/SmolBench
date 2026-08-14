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
    #: How the response disobeyed the prompt's output contract, or None when
    #: it obeyed it exactly. See `smolbench.evals.parsing` for the labels.
    #: Separating this from ``score`` is what lets an analysis distinguish
    #: "the model was wrong" from "the model was right but ignored the
    #: format" -- the two used to be the same event, because a response the
    #: strict parser could not read scored as a failure. Optional with a None
    #: default so replicate YAMLs written before this field existed still
    #: load (``Marks.load`` builds each mark with ``Mark(**m)``); None there
    #: means "not assessed", not "compliant".
    compliance: Optional[str] = None


@dataclass(frozen=True)
class Marks:
    """Grading result of the LLM across a full quiz."""

    #: The model that was evaluated.
    model: str
    #: Per-question marks.
    marks: tuple[Mark, ...]
    #: Date the quiz was run.
    date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    #: Serving-stack snapshot the completions were generated under (instance
    #: type, GPUs, tensor-parallel degree, image, ...) -- provenance so a
    #: result file is self-describing about its hardware instead of needing a
    #: timestamp->config side table (the 2026-08-13 confound audit had to
    #: reconstruct exactly that). None on results written before this field
    #: existed, and for providers with nothing meaningful to report; a plain
    #: default (not default_factory) so legacy ``!!python/object`` files
    #: missing the attribute fall back to the class attribute on access.
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
        """Marks whose response disobeyed the prompt's output contract.

        Counted independently of ``correct``/``incorrect``/``invalid``: a
        response can be graded correct and still have ignored the format, and
        that is exactly the population worth reporting when a condition (the
        induction ``noise_intens`` arm, say) is suspected of degrading
        instruction following rather than reasoning.
        """
        return sum(1 for m in self.marks if m.compliance is not None)

    # -- Serialization ------------------------------------------------------
    # Result files are plain-dict YAML (safe_dump of dataclasses.asdict), NOT
    # yaml.dump of the dataclasses themselves: python-object tags would weld
    # every stored result to this class's import path (a rename/move orphans
    # the whole results tree) and force readers into yaml.unsafe_load.
    # ``load`` still reads the legacy tagged files this repo already
    # committed. PyYAML lives in the notebook extra, so the imports stay
    # inside the methods and the base package remains dependency-light.
    #
    # ``dumps``/``loads`` do the actual (de)serialization to/from an in-memory
    # str; ``dump``/``load`` are thin ``path``-based wrappers around them.
    # The split exists because a result may now live in
    # ``smolbench.evals.results_store``'s S3 backend, where there is no local
    # path to ``open()`` -- an ``S3ResultsStore`` round-trips through
    # ``put_object``/``get_object`` request/response bodies (bytes over the
    # wire) instead of a filesystem, so it needs the str-in/str-out form
    # directly. ``LocalResultsStore`` and every pre-existing on-disk caller
    # keep using ``dump``/``load`` unchanged.

    def dumps(self) -> str:
        """Serializes to a plain-mapping YAML string (safe_load-able).

        Passing no ``stream`` argument is what makes ``yaml.safe_dump``
        RETURN the document as a ``str`` instead of writing it somewhere --
        exactly what a caller with no filesystem path (e.g. an S3
        ``put_object`` body) needs.
        """
        import yaml

        return yaml.safe_dump(asdict(self), default_flow_style=False, indent=4)

    def dump(self, path) -> None:
        """Serializes to ``path`` as plain-mapping YAML (safe_load-able).

        Thin wrapper around ``dumps``; byte-identical to writing ``dumps()``
        to ``path`` directly.
        """
        with open(path, "w") as file:
            file.write(self.dumps())

    @classmethod
    def loads(cls, text: str) -> "Marks":
        """Loads a result document from ``text``, written by ``dumps``/
        ``dump`` or by the legacy ``yaml.dump(marks)`` format
        (``!!python/object`` tags)."""
        import yaml

        # Legacy files always open with the top-level Marks tag; testing the
        # first bytes (not a substring search) keeps a NEW-format file whose
        # response text merely mentions "!!python/object" off the unsafe path.
        # Legacy files are still read back after being seeded into S3, so
        # this branch is load-bearing, not dead code.
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
            # .get: files written before the field existed have no key.
            server_config=data.get("server_config"),
        )

    @classmethod
    def load(cls, path) -> "Marks":
        """Loads a result file written by ``dump`` or by the legacy
        ``yaml.dump(marks)`` format (``!!python/object`` tags).

        Thin wrapper around ``loads``; reads ``path``'s full text then
        delegates.
        """
        with open(path) as file:
            text = file.read()
        return cls.loads(text)
