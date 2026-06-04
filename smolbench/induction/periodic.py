"""
Generates periodic patterns (generalized FizzBuzz).
"""

import string
from dataclasses import dataclass
from math import lcm
from typing import TypeAlias, Collection, Iterable, Tuple, Dict, Callable, Optional

from ordered_set import OrderedSet
import numpy as np

from smolbench.evals import Quiz, ToF, Numeric, Answer


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Label: TypeAlias = str          # label string for a single harmonic
Period: TypeAlias = int          # period k: fires at positions k, 2k, 3k, …
CompoundLabel: TypeAlias = str   # sep-joined labels active at a position
PeriodToLabel: TypeAlias = Dict[Period, Label]
PosToCompound: TypeAlias = Dict[int, CompoundLabel]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodicConfig:
    """Config for generating some periodic pattern."""

    # Number of harmonics; the k-th harmonic fires at positions k, 2k, 3k, … for k in 1..n.
    n: int
    # Labels for each harmonic: n strings or int n → auto-generate n random labels.
    labels: Collection[Label] | int
    # RNG seed for reproducibility.
    seed: int
    # Separator placed between active labels in compound output; must not appear in any label.
    sep: str = "|"

    def __post_init__(self):
        if self.n < 1:
            raise ValueError("n must be positive.")
        if isinstance(self.labels, int):
            if self.labels != self.n:
                raise ValueError(
                    f"When labels is int it must equal n ({self.n}), got {self.labels}."
                )
            length = max(
                2,
                int(np.ceil(np.emath.logn(len(_LABEL_CHARSET), self.labels))) * 2,
            )
            object.__setattr__(
                self,
                "labels",
                tuple(
                    _get_random_labels(self.labels, length, np.random.default_rng(self.seed))
                ),
            )
        else:
            object.__setattr__(self, "labels", tuple(self.labels))
        if len(self.labels) != self.n:
            raise ValueError(
                f"Number of labels ({len(self.labels)}) must equal n ({self.n})."
            )
        for lbl in self.labels:
            if self.sep in lbl:
                raise ValueError(
                    f"Label '{lbl}' contains the separator '{self.sep}'."
                )


# Charset restricted to lowercase letters so the default '|' separator is always safe.
_LABEL_CHARSET: str = string.ascii_lowercase


# ---------------------------------------------------------------------------
# Label generation
# ---------------------------------------------------------------------------

def _get_random_labels(
    n: int,
    l: int,
    rng: np.random.Generator,
    charset: Collection[str] = _LABEL_CHARSET,
) -> OrderedSet[Label]:
    """
    Generates n unique random labels of length l.

    Parameters
    ----------
    n:
        Number of labels to generate.
    l:
        Length of each label.
    rng:
        The RNG being used.
    charset:
        Character set for labels (must not include the separator in use).

    Returns
    -------
    OrderedSet of n unique label strings.

    Raises
    ------
    ValueError if l < ceil(log_{len(charset)}(n)).
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len = np.ceil(np.emath.logn(base, n))
    if l < min_len:
        raise ValueError(
            f"l={l} < {min_len} = ceil(log_{base}({n})): "
            f"insufficient length to generate {n} unique labels."
        )
    indices: np.ndarray = rng.choice(base ** l, size=n, replace=False)
    digits: np.ndarray = np.empty((n, l), dtype=np.int64)
    for idx in range(l - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    return OrderedSet("".join(row) for row in charset_array[digits])


# ---------------------------------------------------------------------------
# Sequence generation
# ---------------------------------------------------------------------------

def _seq_len(n: int) -> int:
    """Returns the period of n harmonics: lcm(1, 2, …, n)."""
    return lcm(*range(1, n + 1))


def generate_sequence(config: PeriodicConfig) -> Tuple[PeriodToLabel, PosToCompound]:
    """
    Returns the period→label mapping and the position→compound mapping.

    The sequence covers exactly one full period: positions 1..lcm(1..n).
    At each position the compound label is the sep-joined concatenation of all labels
    whose period divides that position, in ascending period order.
    """
    period_to_label: PeriodToLabel = {
        k: config.labels[k - 1] for k in range(1, config.n + 1)
    }
    seq_len = _seq_len(config.n)
    pos_to_compound: PosToCompound = {
        pos: config.sep.join(
            period_to_label[k] for k in range(1, config.n + 1) if pos % k == 0
        )
        for pos in range(1, seq_len + 1)
    }
    return period_to_label, pos_to_compound


# ---------------------------------------------------------------------------
# Prompt renderers
# ---------------------------------------------------------------------------

def _render_intensional(period_to_label: PeriodToLabel) -> str:
    """Renders the harmonic rules as human-readable text."""
    return "".join(
        f"Every {k} positions write {label}.\n"
        for k, label in sorted(period_to_label.items())
    )


def _render_extensional(pos_to_compound: PosToCompound) -> str:
    """Renders the sequence as a position-indexed lookup table."""
    return "".join(
        f"Position {pos}: {compound}.\n"
        for pos, compound in sorted(pos_to_compound.items())
    )


def _make_noise(length: int, rng: np.random.Generator) -> str:
    """Generates random noise of the given character length."""
    charset = list(string.ascii_letters + string.digits + "   \n")
    return "".join(charset[i] for i in rng.integers(len(charset), size=length))


# ---------------------------------------------------------------------------
# Prompter
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Prompter:
    """Everything needed to prompt an LLM given the periodic context."""

    template: string.Template
    substitution: Dict[str, str]
    query_gen: Callable[
        [PeriodToLabel, PosToCompound, int],
        Iterable[Tuple[Dict[str, str], Answer]],
    ]
    #: Optional template for extensional prompts; falls back to template if absent.
    extens_template: Optional[string.Template] = None


# ---------------------------------------------------------------------------
# Core prompt generation
# ---------------------------------------------------------------------------

def get_periodic_prompts(
    config: PeriodicConfig,
    prompter: Prompter,
) -> Iterable[Tuple[str, str, str, Answer]]:
    """
    Generates intensional, extensional, and noise-padded intensional prompts.

    The noise-padded intensional appends random noise so its length matches the
    extensional, ablating context length as a confound.

    Yields
    ------
    (intens, extens, noise_intens, answer) for each query.
    """
    period_to_label, pos_to_compound = generate_sequence(config)

    intension: str = _render_intensional(period_to_label)
    extension: str = _render_extensional(pos_to_compound)

    noise_rng: np.random.Generator = np.random.default_rng(config.seed + 1)
    noise_intension: str = intension + _make_noise(
        max(0, len(extension) - len(intension)), noise_rng
    )

    extens_template = prompter.extens_template or prompter.template

    for query, answer in prompter.query_gen(period_to_label, pos_to_compound, config.seed):
        intens_sub = query | prompter.substitution | {"positive_info": intension}
        intens = prompter.template.safe_substitute(intens_sub)

        extens_sub = query | prompter.substitution | {"positive_info": extension}
        extens = extens_template.safe_substitute(extens_sub)

        noise_intens_sub = query | prompter.substitution | {"positive_info": noise_intension}
        noise_intens = prompter.template.safe_substitute(noise_intens_sub)

        yield intens, extens, noise_intens, answer


# ---------------------------------------------------------------------------
# Quiz wrappers
# ---------------------------------------------------------------------------

def get_periodic_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz, Quiz]:
    """
    Wraps get_periodic_prompts to produce True/False QnA format.

    Returns
    -------
    (intensional Quiz, extensional Quiz, noise-padded intensional Quiz)
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in get_periodic_prompts(config, prompter):
        intens_quiz.append(ToF(prompt=intens, answer=answer))
        extens_quiz.append(ToF(prompt=extens, answer=answer))
        noise_intens_quiz.append(ToF(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)


def get_periodic_numeric_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
) -> Tuple[Quiz, Quiz, Quiz]:
    """
    Wraps get_periodic_prompts to produce integer-answer QnA format.

    Returns
    -------
    (intensional Quiz, extensional Quiz, noise-padded intensional Quiz)
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in get_periodic_prompts(config, prompter):
        intens_quiz.append(Numeric(prompt=intens, answer=answer))
        extens_quiz.append(Numeric(prompt=extens, answer=answer))
        noise_intens_quiz.append(Numeric(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)


# ---------------------------------------------------------------------------
# Built-in query generators
# ---------------------------------------------------------------------------

def tof_membership_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[Tuple[Dict[str, str], bool]]:
    """
    Yields True/False queries of the form 'Does label appear at position pos?'

    Period-1 labels are always present and are excluded (trivially True). The
    remaining queries are balanced between True and False cases.
    """
    rng = np.random.default_rng(seed)

    true_qs: list = []
    false_qs: list = []

    for pos in sorted(pos_to_compound.keys()):
        for period, label in sorted(period_to_label.items()):
            if period == 1:
                continue  # always True for every position — omit trivial queries
            entry = ({"pos": str(pos), "label": label}, pos % period == 0)
            (true_qs if pos % period == 0 else false_qs).append(entry)

    n = min(len(true_qs), len(false_qs), 10)
    if n == 0:
        return

    for idx in rng.choice(len(true_qs), n, replace=False):
        yield true_qs[idx]
    for idx in rng.choice(len(false_qs), n, replace=False):
        yield false_qs[idx]


def numeric_count_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[Tuple[Dict[str, str], int]]:
    """
    Yields count queries of the form 'How many positions 1..seq_len contain label?'

    The ground-truth answer is floor(seq_len / period) for each label, which is
    always an exact integer since each period divides lcm(1..n).
    """
    seq_len = max(pos_to_compound.keys())
    for period, label in sorted(period_to_label.items()):
        yield {"label": label, "seq_len": str(seq_len)}, seq_len // period


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tof_template = string.Template(
        "Context:\n"
        "---\n"
        "There is a counting game. Count positions starting from 1. "
        "At each position write down words according to the following rules:\n"
        "$positive_info\n"
        "Query:\n"
        "Does '$label' appear at position $pos? "
        "Answer with only one word: 'True' or 'False'."
    )

    count_template = string.Template(
        "Context:\n"
        "---\n"
        "There is a counting game. Count positions starting from 1. "
        "At each position write down words according to the following rules:\n"
        "$positive_info\n"
        "Query:\n"
        "How many of the positions 1 through $seq_len include '$label'? "
        "Answer with a single integer."
    )

    cfg = PeriodicConfig(
        n=3,
        labels=["fizz", "buzz", "gerbil"],
        seed=42,
    )

    print("=== True/False membership queries ===\n")
    for intens, extens, noise_intens, answer in get_periodic_prompts(
        cfg,
        Prompter(tof_template, {}, tof_membership_query_gen),
    ):
        print("-- intensional --")
        print(intens)
        print("-- extensional --")
        print(extens)
        print("answer:", answer)
        print()

    print("=== Numeric count queries ===\n")
    for intens, extens, noise_intens, answer in get_periodic_prompts(
        cfg,
        Prompter(count_template, {}, numeric_count_query_gen),
    ):
        print("-- intensional --")
        print(intens)
        print("-- extensional --")
        print(extens)
        print("answer:", answer)
        print()
