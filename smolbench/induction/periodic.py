"""Generate periodic-pattern induction quizzes.

Generators use a fresh seeded RNG; prompt and RNG bytes are golden-pinned.
"""

import string
from dataclasses import dataclass
from math import gcd, lcm
from types import MappingProxyType
from typing import (
    Callable,
    Collection,
    Iterable,
    Mapping,
    Optional,
    TypeAlias,
)

import numpy as np

from smolbench.evals import Numeric, QnA, Quiz, ToF
from smolbench.evals.tokenization import (
    Tokenizer,
    choose_whitespace_unit,
    token_matched_noise_prompt,
)
from smolbench.induction._common import (
    Prompter,
    RenderedQuery,
    build_substitution,
    context_renderer,
    quizzes_from_prompts,
    random_labels,
)

__all__ = [
    "PeriodicConfig",
    "Contexts",
    "Condition",
    "CONDITIONS",
    "RANGE_KEYS",
    "get_periodic_prompts",
    "get_periodic_quiz",
    "get_periodic_numeric_quiz",
    "tof_membership_query_gen",
    "numeric_count_query_gen",
]


# Domain vocabulary for the two mappings a sequence is made of. A ``Label`` is
# one rule's word ("fizz"); a ``Period`` is how often that rule fires; a
# ``CompoundLabel`` is the ``sep``-joined labels of every rule firing at one
# position ("fizz|buzz" at position 6 for periods 2 and 3).
Label: TypeAlias = str
Period: TypeAlias = int
CompoundLabel: TypeAlias = str
#: The intensional view: each rule's period to its label.
PeriodToLabel: TypeAlias = dict[Period, Label]
#: The extensional view: each 1-based position to its compound label.
PosToCompound: TypeAlias = dict[int, CompoundLabel]


@dataclass(frozen=True)
class PeriodicConfig:
    """Configure the generation of one periodic pattern."""

    n: int
    # Labels follow ascending period order.
    labels: Collection[Label] | int
    seed: int
    # Must not occur in a label.
    sep: str = "|"
    # Explicit periods prevent default lcm jumps beyond context windows.
    periods: Optional[tuple[int, ...]] = None
    # Pins explicit-period sequence length; otherwise periods must be coprime.
    expect_seq_len: Optional[int] = None

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError("n must be positive.")
        if self.periods is not None:
            periods = tuple(int(p) for p in self.periods)
            if len(periods) != self.n:
                raise ValueError(
                    f"Number of periods ({len(periods)}) must equal n ({self.n})."
                )
            if len(set(periods)) != len(periods):
                raise ValueError(f"Periods must be distinct, got {periods}.")
            if any(p < 1 for p in periods):
                raise ValueError(f"Periods must be positive, got {periods}.")
            if self.expect_seq_len is None:
                for i, a in enumerate(periods):
                    for b in periods[i + 1 :]:
                        if gcd(a, b) != 1:
                            raise ValueError(
                                f"Periods must be pairwise coprime; gcd({a}, {b}) = {gcd(a, b)}. "
                                "Pass expect_seq_len=<length> to use a non-coprime "
                                "set on purpose (the divisor pathway)."
                            )
            else:
                # The divisor pathway varies extensional information density:
                # the full period is always lcm(periods), so adding
                # non-coprime periods that divide it grows the intensional
                # rule list while the extensional listing stays the same
                # length, closing the density gap between the two arms.
                # Exact equality is required; a factorisation-based
                # "close enough" backsolve is issue #63.
                actual = lcm(*periods)
                if actual != self.expect_seq_len:
                    raise ValueError(
                        f"lcm(periods) is {actual}, not the declared expect_seq_len "
                        f"{self.expect_seq_len}."
                    )
            object.__setattr__(self, "periods", periods)
        elif self.expect_seq_len is not None:
            raise ValueError(
                "expect_seq_len only means something alongside an explicit "
                "`periods` set."
            )
        if isinstance(self.labels, int):
            if self.labels != self.n:
                raise ValueError(
                    f"When labels is int it must equal n ({self.n}), got {self.labels}."
                )
            # Multi-character even at small n, where the information-theoretic minimum allows one letter.
            object.__setattr__(
                self,
                "labels",
                random_labels(
                    self.labels, self.seed, charset=_LABEL_CHARSET, min_length=2
                ),
            )
        else:
            object.__setattr__(self, "labels", tuple(self.labels))
        if len(self.labels) != self.n:
            raise ValueError(
                f"Number of labels ({len(self.labels)}) must equal n ({self.n})."
            )
        if len(set(self.labels)) != len(self.labels):
            # Duplicates create contradictory ground truths.
            raise ValueError(f"Labels must be distinct, got {tuple(self.labels)}.")
        for lbl in self.labels:
            if self.sep in lbl:
                raise ValueError(f"Label '{lbl}' contains the separator '{self.sep}'.")
            if any(ch.isdigit() for ch in lbl):
                # Precondition of ``_verify_no_range_leak``: the rendered
                # range-free prompt is scanned for the sequence length's
                # digits, so no substitution may carry digits of its own.
                raise ValueError(f"Label '{lbl}' contains a digit.")

    @property
    def ascending_periods(self) -> tuple[int, ...]:
        """Return the harmonic periods this config asks for, in ascending order.

        Returns
        -------
        tuple[int, ...]
            Harmonic periods in ascending order.
        """
        if self.periods is None:
            return tuple(range(1, self.n + 1))
        return tuple(sorted(self.periods))

    def generate_sequence(self) -> tuple[PeriodToLabel, PosToCompound]:
        """Generate the period-to-label and position-to-compound mappings.

        Returns
        -------
        tuple[PeriodToLabel, PosToCompound]
            Period-to-label and position-to-compound mappings.
        """
        periods = self.ascending_periods
        period_to_label: PeriodToLabel = {
            k: self.labels[i] for i, k in enumerate(periods)
        }
        seq_len = lcm(*periods)
        pos_to_compound: PosToCompound = {
            pos: self.sep.join(period_to_label[k] for k in periods if pos % k == 0)
            for pos in range(1, seq_len + 1)
        }
        return period_to_label, pos_to_compound


# Lowercase labels avoid visual confusion with positions and must contain no
# separator character (enforced in PeriodicConfig.__post_init__).
_LABEL_CHARSET: str = string.ascii_lowercase


def _render_intensional(period_to_label: PeriodToLabel) -> str:
    """Render the harmonic rules as human-readable text."""
    return "".join(
        f"Every {k} positions write {label}.\n"
        for k, label in sorted(period_to_label.items())
    )


def _render_extensional(pos_to_compound: PosToCompound) -> str:
    """Render the sequence as a position-indexed lookup table."""
    return "".join(
        f"Position {pos}: {compound}.\n"
        for pos, compound in sorted(pos_to_compound.items())
    )


@dataclass(frozen=True)
class Contexts:
    """Hold the two rendered context bodies one sequence produces."""

    #: Compact rule list.
    intensional: str
    #: Enumerated position -> compound-label table.
    extensional: str


@dataclass(frozen=True)
class Condition:
    """Specify an arm's context, padding target, and range handling."""

    context: Callable[[Contexts], str]
    match_tokens_to: Optional[str] = None
    omit_range: bool = False


# Immutable shared conditions prevent cross-caller mutation.
CONDITIONS: Mapping[str, Condition] = MappingProxyType(
    {
        "intens": Condition(context=lambda c: c.intensional),
        "extens": Condition(context=lambda c: c.extensional),
        # Matches extens length to isolate prompt length.
        "noise_intens": Condition(
            context=lambda c: c.intensional, match_tokens_to="extens"
        ),
        # Omits the range because it can reveal the period-1 answer. The range
        # placeholders are ``RANGE_KEYS`` below; the range-free wording lives
        # in ``Prompter.range_free_template``.
        "zero": Condition(context=lambda c: "", omit_range=True),
    }
)


# Values that range-free prompts must not reveal.
RANGE_KEYS: tuple[str, ...] = ("seq_len",)


def _resolve_arm_template(
    name: str, condition: Condition, prompter: Prompter
) -> string.Template:
    """Return the template `name`'s condition renders from.

    ``omit_range`` requires its range-free template to prevent answer leakage.

    Parameters
    ----------
    name : str
        Name of the information condition.
    condition : Condition
        Information condition being rendered.
    prompter : Prompter
        Prompt templates and query generator.

    Returns
    -------
    string.Template
        Template selected for the condition.

    Raises
    ------
    ValueError
        If range omission is requested without a range-free template.
    """
    if not condition.omit_range:
        return prompter.template
    if prompter.range_free_template is None:
        raise ValueError(
            f"condition {name!r} has omit_range=True but "
            "prompter.range_free_template is None."
        )
    return prompter.range_free_template


# ``_verify_no_range_leak`` also searches the rendered prompt for the literal
# range value (e.g. "2520"). A one-digit value such as "1" occurs in ordinary
# wording ("Positions are counted starting from 1"), so it would be a false
# positive; values shorter than this are checked only via placeholders.
_MIN_SEARCHABLE_RANGE_VALUE_LEN: int = 2


def _verify_no_range_leak(
    name: str, query: dict[str, str], template: string.Template, rendered: str
) -> None:
    """Raise if `template` or `rendered` reveals any of ``RANGE_KEYS``'s values.

    ``range_free_template`` is caller-supplied, so ``omit_range`` alone does not
    guarantee the range is gone: the template may still substitute ``$seq_len``
    or spell the range out literally, and for the numeric count task ``seq_len``
    is the period-1 answer. A range placeholder is rejected structurally; the
    rendered text is searched only for values too long to collide with
    unrelated digits.

    Precondition: no non-range substitution contains a digit. Labels satisfy
    this by construction (``_LABEL_CHARSET`` is alphabetic and
    ``PeriodicConfig`` rejects caller labels with digits), so the only digits
    in a rendered range-free prompt come from the template's own wording or
    from a leaked range value.

    Parameters
    ----------
    name : str
        Name of the information condition.
    query : dict[str, str]
        Query substitutions whose range values must remain hidden.
    template : string.Template
        Template whose placeholders must not expose range values.
    rendered : str
        Rendered prompt to inspect.
    """
    identifiers = template.get_identifiers()
    for key in RANGE_KEYS:
        if key in identifiers:
            raise ValueError(
                f"condition {name!r} is omit_range=True but its "
                f"range_free_template substitutes {key}."
            )
        if key not in query:
            continue
        value = str(query[key])
        if len(value) >= _MIN_SEARCHABLE_RANGE_VALUE_LEN and value in rendered:
            raise ValueError(
                f"condition {name!r} is omit_range=True but its rendered "
                f"range_free_template prompt still contains "
                f"{key}={query[key]!r}."
            )


def get_periodic_prompts(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> Iterable[RenderedQuery]:
    """Render every condition for each query.

    Parameters
    ----------
    config : PeriodicConfig
        Configuration for the periodic sequence.
    prompter : Prompter
        Prompt templates and query generator.
    tokenizer : Tokenizer
        Must be the model under test's own.
    conditions : Mapping[str, Condition], optional
        Information conditions to render.

    Yields
    ------
    RenderedQuery
        One rendered query containing prompts and token counts for every condition.

    Raises
    ------
    ValueError
        Before rendering, if a condition's token target cannot be satisfied.
    """
    for name, condition in conditions.items():
        target = condition.match_tokens_to
        if target is None:
            continue
        if target not in conditions:
            raise ValueError(
                f"condition {name!r}: match_tokens_to={target!r} names a "
                f"condition not present in conditions ({sorted(conditions)})."
            )
        if conditions[target].match_tokens_to is not None:
            # A padded arm's own count only exists after its pad search, so a
            # chain of padded arms has nothing to bottom out on.
            raise ValueError(
                f"condition {name!r}: match_tokens_to target {target!r} is "
                "itself padded."
            )

    period_to_label, pos_to_compound = config.generate_sequence()

    contexts = Contexts(
        intensional=_render_intensional(period_to_label),
        extensional=_render_extensional(pos_to_compound),
    )

    unpadded = [(n, c) for n, c in conditions.items() if c.match_tokens_to is None]
    padded = [(n, c) for n, c in conditions.items() if c.match_tokens_to is not None]
    unit: Optional[str] = choose_whitespace_unit(tokenizer) if padded else None

    for query, answer in prompter.query_gen(
        period_to_label, pos_to_compound, config.seed
    ):
        prompts: dict[str, str] = {}
        token_counts: dict[str, int] = {}

        for name, condition in unpadded:
            template = _resolve_arm_template(name, condition, prompter)
            rendered = template.safe_substitute(
                build_substitution(query, condition.context(contexts))
            )
            if condition.omit_range:
                _verify_no_range_leak(name, query, template, rendered)
            prompts[name] = rendered
            token_counts[name] = tokenizer.count(rendered)

        for name, condition in padded:
            template = _resolve_arm_template(name, condition, prompter)
            target_count = token_counts[condition.match_tokens_to]
            rendered = token_matched_noise_prompt(
                context_renderer(template, query),
                condition.context(contexts),
                target_count,
                tokenizer,
                unit=unit,
            )
            if condition.omit_range:
                _verify_no_range_leak(name, query, template, rendered)
            prompts[name] = rendered
            # Padding already verified this count.
            token_counts[name] = target_count

        yield RenderedQuery(
            prompts={name: prompts[name] for name in conditions},
            token_counts={name: token_counts[name] for name in conditions},
            answer=answer,
        )


def _get_periodic_quizzes(
    config: PeriodicConfig,
    prompter: Prompter,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition],
    qna_cls: type[QnA],
) -> dict[str, Quiz]:
    """Wrap periodic prompts in the requested question type.

    Parameters
    ----------
    config : PeriodicConfig
        Configuration for the periodic sequence.
    prompter : Prompter
        Prompt templates and query generator.
    tokenizer : Tokenizer
        Tokenizer used to count rendered prompt tokens.
    conditions : Mapping[str, Condition]
        Information conditions to render.
    qna_cls : type[QnA]
        Question type used to wrap each rendered prompt.

    Returns
    -------
    dict[str, Quiz]
        Quizzes keyed by condition name.
    """
    return quizzes_from_prompts(
        get_periodic_prompts(
            config, prompter, tokenizer=tokenizer, conditions=conditions
        ),
        qna_cls,
        conditions,
    )


def get_periodic_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> dict[str, Quiz]:
    """Wrap :func:`get_periodic_prompts` as ``ToF`` quizzes, keyed by condition name.

    Parameters
    ----------
    config : PeriodicConfig
        Configuration for the periodic prompt sequence.
    prompter : Prompter
        Prompter that generates the periodic prompts.
    tokenizer : Tokenizer
        Tokenizer for rendering prompts.
    conditions : Mapping[str, Condition], optional
        Named experimental conditions.

    Returns
    -------
    dict[str, Quiz]
        Quizzes keyed by condition name.
    """
    return _get_periodic_quizzes(config, prompter, tokenizer, conditions, ToF)


def get_periodic_numeric_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> dict[str, Quiz]:
    """Wrap :func:`get_periodic_prompts` as ``Numeric`` quizzes, keyed by condition name.

    Parameters
    ----------
    config : PeriodicConfig
        Configuration for the periodic prompt sequence.
    prompter : Prompter
        Prompter that generates the periodic prompts.
    tokenizer : Tokenizer
        Tokenizer for rendering prompts.
    conditions : Mapping[str, Condition], optional
        Named experimental conditions.

    Returns
    -------
    dict[str, Quiz]
        Quizzes keyed by condition name.
    """
    return _get_periodic_quizzes(config, prompter, tokenizer, conditions, Numeric)


# Fixed polarity count keeps quiz size stable across n.
MAX_QUERIES_PER_POLARITY: int = 10


def tof_membership_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[tuple[dict[str, str], bool]]:
    """Yield True/False queries of the form "Does label appear at position pos?"

    Parameters
    ----------
    period_to_label : PeriodToLabel
        Mapping from each period to its label.
    pos_to_compound : PosToCompound
        Mapping from positions to generated compounds.
    seed : int
        Random seed for sampling queries.

    Yields
    ------
    tuple[dict[str, str], bool]
        Sampled position-label substitutions paired with their Boolean answers.
    """
    rng = np.random.default_rng(seed)

    true_qs: list = []
    false_qs: list = []

    period_labels = sorted(period_to_label.items())
    for pos in sorted(pos_to_compound.keys()):
        for period, label in period_labels:
            if period == 1:
                continue  # true for every position -- skip this trivial query
            entry = ({"pos": str(pos), "label": label}, pos % period == 0)
            (true_qs if pos % period == 0 else false_qs).append(entry)

    n = min(len(true_qs), len(false_qs), MAX_QUERIES_PER_POLARITY)
    if n == 0:
        return

    # True block then False block, unshuffled: each query is a separate prompt, so order leaks nothing.
    for idx in rng.choice(len(true_qs), n, replace=False):
        yield true_qs[idx]
    for idx in rng.choice(len(false_qs), n, replace=False):
        yield false_qs[idx]


def numeric_count_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[tuple[dict[str, str], int]]:
    """Yield count queries of the form "How many positions 1..seq_len contain label?"

    Ignores ``seed`` to share the query-generator protocol; config labels remain seeded.

    Parameters
    ----------
    period_to_label : PeriodToLabel
        Mapping from each period to its label.
    pos_to_compound : PosToCompound
        Mapping from positions to generated compounds.
    seed : int
        Seed accepted by the shared query-generator protocol.

    Yields
    ------
    tuple[dict[str, str], int]
        Label and sequence-length substitutions paired with their counts.
    """
    seq_len = max(pos_to_compound.keys())
    for period, label in sorted(period_to_label.items()):
        yield {"label": label, "seq_len": str(seq_len)}, seq_len // period
