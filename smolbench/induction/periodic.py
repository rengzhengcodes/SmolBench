"""Test periodic-pattern induction (generalized FizzBuzz).

A sequence of ``n`` overlapping periodic "harmonics": the k-th fires at every
multiple of its period, and each position's label is the sep-joined
concatenation of every label whose period divides it (:func:`generate_sequence`),
over exactly one full period, positions 1..lcm(periods). Queries ask whether a
label appears at a position (:func:`tof_membership_query_gen`) or how many
positions contain it (:func:`numeric_count_query_gen`). :class:`PeriodicConfig`
plus a ``_common.Prompter`` determine a run; the canonical eval configs live in
``notebooks/induction/run_study.py``.

Information conditions, all built from one sequence in ONE render loop by
:func:`get_periodic_prompts`, and declared in exactly one place, the
``CONDITIONS`` mapping below: **intens** = the compact rules ("Every 3
positions write gerbil."); **extens** = the enumerated position ->
compound-label table ("Position 6: fizz|buzz|gerbil."); **noise_intens** = the
intensional text plus whitespace until the RENDERED PROMPT hits ``extens``'s
token count, isolating length as a confound; **zero** = empty context, the
chance floor -- rendered from a RANGE-FREE question ("How many of the
positions include 'vw'?", no ``$seq_len``) via ``prompter.range_free_template``,
because on the default 1..n pathway the period-1 harmonic's answer IS
``seq_len``, and the range-stating question the other three arms use ("...
positions 1 through $seq_len...") would print that answer directly into the
prompt of the very arm meant to measure the floor a model reaches with NO
positive information at all (a model echoing the only large number in its own
prompt scored 11.1 pp on it). See ``CONDITIONS`` for the mapping that drives
the loop and ``RANGE_KEYS`` for how the zero arm's promise is verified rather
than trusted.

Re-collection note: any ``zero``-arm rows collected before this change carry
the OLD, range-stating question and must be re-collected, not compared
against the new ones -- they measured a different (leakier) floor.
``notebooks/induction/run_study.py``'s ``INDUCTION_FORCE_RERUN`` re-collects
past the resume-skip, but forcing is PER-SEED: it re-collects all four info
arms of a forced seed in one pooled call, not the ``zero`` arm alone -- there
is no way to force just one arm (see that module's docstring).

Noise-arm PRECONDITION -- a requirement on the config, not a property the
benchmark guarantees: for every query, the extensional prompt must be STRICTLY
longer in tokens than the intensional one. The pad is appended, so it can only
GROW a prompt; a config that violates this raises out of
:func:`get_periodic_prompts` rather than emitting a "control" arm identical to
the arm it controls for. The enumeration is NOT always at least as long.
Measured with cl100k_base under the production template: at n=1 the intensional
prompt costs 105 tokens against the extensional 104 (extens strictly SHORTER),
and at n=2 every query ties exactly (113 against 113, 114 against 114 -- EQUAL
also fails a strict inequality). On the DEFAULT 1..n pathway the rule list is
overtaken from n=3 on (120 against 150), and the production configs (n=9, lcm
2,520) clear the precondition by a wide margin. n alone does not settle it,
though: the divisor pathway below deliberately adds rules while pinning the
listing, so an explicit small-lcm ``periods`` set can violate the precondition
at any n. Hence a precondition CHECKED at generation time, not a property the
config shape guarantees.

Period sets: the default 1..n makes sequence length the step function lcm(1..n)
-- lcm(1..10) == lcm(1..9) == 2520, then n=11 leaps to 27,720 positions (~341k
tokens, past every context window). ``PeriodicConfig`` therefore accepts an
explicit ``periods`` set in two dual modes, documented and validated on that
field: pairwise coprime lengthens the EXTENSIONAL listing, factor-sharing
lengthens the INTENSIONAL rule list at a near-fixed listing (against 2,520, 9
harmonics -> 26 grows it 2.5%, but all 48 divisors would grow it 31%). The
pathways diverge only in :func:`_periods_of`.

Tokenizer discipline: the noise arm's tokenizer is REQUIRED, not defaulted -- a
plausible-but-wrong default would silently de-calibrate the very length control
this arm provides -- so quizzes are per-(seed, model), with only
``noise_intens`` varying across models.

Every generator takes an explicit ``seed`` and builds a fresh
``np.random.default_rng(seed)``, never global RNG state; the noise pad consumes
no RNG. Generation is byte-pinned by ``tests/induction/test_golden_quizzes.py``
at the notebooks' production configs, so any change to RNG call order or count,
or to the noise-padding scheme, breaks that pin -- fix the change, never
re-baseline the fixture. The ``__main__`` demo uses seed 42.
"""

import string
from dataclasses import dataclass
from math import gcd, lcm
from types import MappingProxyType
from typing import Callable, Collection, Dict, Iterable, Mapping, Optional, Tuple, TypeAlias

import numpy as np

from smolbench.evals import Quiz, ToF, Numeric
from smolbench.evals.tokenization import (
    TiktokenTokenizer,
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

# Prompter is re-exported for callers configuring the benchmark; the class
# itself lives in ``_common`` with the rest of the generation machinery.
__all__ = [
    "PeriodicConfig",
    "Prompter",
    "Contexts",
    "Condition",
    "CONDITIONS",
    "RANGE_KEYS",
    "generate_sequence",
    "get_periodic_prompts",
    "get_periodic_quiz",
    "get_periodic_numeric_quiz",
    "tof_membership_query_gen",
    "numeric_count_query_gen",
]


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
    """Configure the generation of one periodic pattern."""

    # Number of harmonics. With the default periods (None), the k-th harmonic
    # fires at positions k, 2k, 3k, … for k in 1..n; with an explicit `periods`
    # set, n is how many periods that set holds.
    n: int
    # Labels for each harmonic: n strings, or int n to auto-generate n random
    # labels. Assigned in ascending-period order, so labels[i] belongs to the
    # i-th smallest period.
    labels: Collection[Label] | int
    # RNG seed for reproducibility.
    seed: int
    # Separator placed between active labels in compound output. Must not
    # appear in any label.
    sep: str = "|"
    # Explicit harmonic periods, replacing the default 1..n. None selects the
    # consecutive-integer pathway, whose generated bytes are pinned by
    # tests/induction/test_golden_quizzes.py.
    periods: Tuple[int, ...] | None = None
    # The sequence length `periods` is expected to produce. Omit it and the
    # periods must be PAIRWISE COPRIME, so lcm == product and the caller dials
    # the length by multiplying out -- the pathway for a longer EXTENSIONAL
    # listing. Supply it and coprimality is NOT required; lcm(periods) must
    # equal it exactly instead, letting a DIVISOR set add harmonics while
    # pinning the length -- the pathway for a longer INTENSIONAL rule list at a
    # fixed extensional listing. Either way construction fails when the periods
    # disagree with the declared length, because that failure is otherwise
    # invisible: a wrong-length set still generates a self-consistent quiz, just
    # not the one that was asked for.
    expect_seq_len: int | None = None

    def __post_init__(self):
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
                # Pairwise coprimality makes lcm(periods) == prod(periods), so
                # sequence length is a product the caller dials directly
                # instead of the step function lcm(1..n).
                for i, a in enumerate(periods):
                    for b in periods[i + 1:]:
                        if gcd(a, b) != 1:
                            raise ValueError(
                                f"Periods must be pairwise coprime; gcd({a}, {b}) = {gcd(a, b)}. "
                                "Without coprimality lcm(periods) < prod(periods) and the "
                                "sequence length is no longer the product you asked for. "
                                "Pass expect_seq_len=<length> to use a non-coprime set on "
                                "purpose (the divisor pathway)."
                            )
            else:
                # Divisor pathway: the periods deliberately SHARE factors so
                # lcm stays put. Each period d contributes seq_len/d
                # occurrences to the extensional listing, so adding large
                # divisors grows the rule list and leaves the listing ~fixed.
                actual = lcm(*periods)
                if actual != self.expect_seq_len:
                    raise ValueError(
                        f"lcm(periods) is {actual}, not the declared expect_seq_len "
                        f"{self.expect_seq_len}. Every period must divide the declared "
                        "length (and together they must reach it) or the extensional "
                        "listing silently changes size, which is the one thing this "
                        "pathway exists to hold fixed."
                    )
            object.__setattr__(self, "periods", periods)
        elif self.expect_seq_len is not None:
            raise ValueError(
                "expect_seq_len only means something alongside an explicit `periods` "
                "set; on the default 1..n pathway the length is lcm(1..n) by definition."
            )
        if isinstance(self.labels, int):
            if self.labels != self.n:
                raise ValueError(
                    f"When labels is int it must equal n ({self.n}), got {self.labels}."
                )
            # min_length=2: periodic labels are always multi-character, even at
            # small n where the information-theoretic minimum would allow
            # single letters -- see random_labels' docstring.
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
            # A duplicate label states two rules for one string, giving a
            # single prompt two contradictory ground truths. Auto-generated
            # labels are unique by construction; this guards explicit lists.
            raise ValueError(f"Labels must be distinct, got {tuple(self.labels)}.")
        for lbl in self.labels:
            if self.sep in lbl:
                raise ValueError(
                    f"Label '{lbl}' contains the separator '{self.sep}'."
                )


# Design: lowercase letters only (26), not letters + digits (62). The choice is
# free in PROMPT LENGTH at every count this benchmark uses. `random_labels`
# sizes a label at max(min_length, 1, ceil(log_base(count)) *
# LABEL_LENGTH_SAFETY_FACTOR); for any count <= 26 that ceiling is 1 under BOTH
# bases, so both charsets yield the same length-2 label (the min_length=2 floor
# `PeriodicConfig` passes coincides with that computed value here, rather than
# overriding it). The two only diverge
# from count=27 up, where base 26 needs a second digit and the safety factor
# doubles it to 4 against the alphanumeric 2 -- past every in-repo harmonic set
# (production is n=9; the largest set the module docstring contemplates is 26
# divisors, still length 2 either way).
#
# What the restriction actually buys is READABILITY of the rendered rules.
# Labels are drawn for exact-string distinctness, which is NOT case-folded, so a
# mixed-case charset could legitimately draw "aQ" and "Aq" as two different
# labels -- visually confusable, and ambiguous to a reader or model matching a
# query's label against the rule list case-insensitively. Excluding digits keeps
# a label from reading as a position number in "Every 3 positions write 3x." or
# "Position 6: ...". Uniform lowercase makes every label the same shape.
#
# Separately: the charset must contain no separator character, since a label
# holding `sep` would split into two on render. That is enforced, not assumed --
# `PeriodicConfig.__post_init__` rejects any label containing `sep`, covering
# explicit label lists as well as these auto-generated ones.
_LABEL_CHARSET: str = string.ascii_lowercase


# ---------------------------------------------------------------------------
# Sequence generation
# ---------------------------------------------------------------------------

def _periods_of(config: PeriodicConfig) -> Tuple[int, ...]:
    """Return the harmonic periods this config asks for, in ascending order.

    The only point where the default 1..n and explicit-``periods`` pathways
    differ; everything downstream is shared verbatim.
    """
    if config.periods is None:
        return tuple(range(1, config.n + 1))
    return tuple(sorted(config.periods))


def _seq_len_of(config: PeriodicConfig) -> int:
    """Return the sequence length: the lcm of the config's harmonic periods."""
    return lcm(*_periods_of(config))


def generate_sequence(config: PeriodicConfig) -> Tuple[PeriodToLabel, PosToCompound]:
    """Generate the period-to-label and position-to-compound mappings.

    Covers positions 1..lcm(periods), each mapped to the sep-joined labels whose
    periods divide it, in ascending period order (``labels[i]`` belonging to the
    i-th smallest period).
    """
    periods = _periods_of(config)
    period_to_label: PeriodToLabel = {
        k: config.labels[i] for i, k in enumerate(periods)
    }
    seq_len = _seq_len_of(config)
    pos_to_compound: PosToCompound = {
        pos: config.sep.join(
            period_to_label[k] for k in periods if pos % k == 0
        )
        for pos in range(1, seq_len + 1)
    }
    return period_to_label, pos_to_compound


# ---------------------------------------------------------------------------
# Prompt renderers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Information conditions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Contexts:
    """The two rendered context bodies one sequence produces.

    Bundles :func:`_render_intensional`'s and :func:`_render_extensional`'s
    output for a single query's generation pass, so a :class:`Condition`'s
    ``context`` callable can pick whichever body (or neither) its arm shows,
    without every call site re-deriving both renders by hand.
    """

    #: The compact rule list ("Every 3 positions write gerbil.").
    intensional: str
    #: The enumerated position -> compound-label table ("Position 6: ...").
    extensional: str


@dataclass(frozen=True)
class Condition:
    """One information condition: which context it shows, and how.

    Parameters
    ----------
    context : Callable[[Contexts], str]
        Selects this arm's ``positive_info`` body from the query's
        :class:`Contexts` (e.g. ``lambda c: c.intensional``, or ``lambda c:
        ""`` for the zero arm).
    match_tokens_to : Optional[str]
        The name of another condition whose RENDERED prompt's token count
        this arm's rendering must exactly match, via whitespace padding (see
        :func:`~smolbench.evals.tokenization.token_matched_noise_prompt`).
        ``None`` (the default) renders this arm plainly, with no padding.
        Must name another entry of the same ``conditions`` mapping that does
        NOT itself carry a ``match_tokens_to`` -- see
        :func:`get_periodic_prompts`'s validation for why a padded arm's own
        count is not a usable pad target.
    omit_range : bool
        If ``True``, this arm renders from ``prompter.range_free_template``
        instead of ``prompter.template``, and the rendered text is verified
        to contain none of ``RANGE_KEYS``'s values. ``False`` (the default)
        renders from ``prompter.template`` like every other arm.
    """

    context: Callable[[Contexts], str]
    match_tokens_to: Optional[str] = None
    omit_range: bool = False


# The single declaration of this benchmark's information conditions -- every
# consumer (get_periodic_prompts's default, InductionExperiment.info_types,
# run_study.INFO_TYPES) derives from THIS mapping rather than restating the
# arm names, so the four names and their order live in exactly one place.
# MappingProxyType, not a plain dict: the mapping is a shared, module-level
# default (get_periodic_prompts's own default argument, plus every importer
# that reads it directly), and a caller mutating a plain dict in place would
# silently change every other caller's default underneath it.
CONDITIONS: Mapping[str, Condition] = MappingProxyType({
    # The compact rule list. Fewer tokens than extens at any n this benchmark
    # exercises past the tiny configs the noise-arm precondition excludes
    # (see the module docstring's "Noise-arm PRECONDITION").
    "intens": Condition(context=lambda c: c.intensional),
    # The full position-by-position enumeration. Usually more tokens than
    # intens; the pairing the noise arm isolates length from.
    "extens": Condition(context=lambda c: c.extensional),
    # intens's text, whitespace-padded until the RENDERED prompt hits
    # extens's token count -- a length-matched control arm, so a gap between
    # this and intens cannot be explained by prompt length alone.
    "noise_intens": Condition(context=lambda c: c.intensional, match_tokens_to="extens"),
    # No context at all, and a range-free question: the chance floor with no
    # positive information AND no leaked seq_len (see the module docstring's
    # "Information conditions" section for why the range must be omitted
    # here specifically).
    "zero": Condition(context=lambda c: "", omit_range=True),
})


# The query-substitution keys that name the position range ("1 through
# $seq_len", "positions 1..$seq_len"). An ``omit_range`` condition's RENDERED
# prompt is verified, at generation time, to contain none of these keys'
# VALUES -- not merely to have been built from a template that lacks the
# placeholder -- because a template that still names the key elsewhere (or a
# caller's mistake) would otherwise ship the same leak this benchmark's
# ``zero`` condition exists to remove. A query generator that never emits any
# of these keys in the first place (``tof_membership_query_gen``, whose
# questions state a POSITION, not a range) is already range-free by
# construction, and the check is vacuously satisfied for it -- there is
# nothing to strip, and nothing to verify against.
RANGE_KEYS: Tuple[str, ...] = ("seq_len",)


# ---------------------------------------------------------------------------
# Core prompt generation
# ---------------------------------------------------------------------------

def _resolve_arm_template(name: str, condition: Condition, prompter: Prompter) -> string.Template:
    """Return the template `name`'s condition renders from.

    ``omit_range`` conditions render from ``prompter.range_free_template``;
    every other condition renders from ``prompter.template``.

    Raises
    ------
    ValueError
        If `condition` is ``omit_range=True`` and ``prompter.range_free_template``
        is ``None``. No silent fallback to ``prompter.template`` here: that
        fallback IS the leak an ``omit_range`` condition exists to avoid (see
        the module docstring's "Information conditions" section).
    """
    if not condition.omit_range:
        return prompter.template
    if prompter.range_free_template is None:
        raise ValueError(
            f"condition {name!r} has omit_range=True but "
            "prompter.range_free_template is None: a range-omitting "
            "condition must be given its own range-free question. Falling "
            "back to prompter.template would render the ordinary, "
            "range-stating question -- exactly the leak this condition "
            "exists to remove."
        )
    return prompter.range_free_template


def _verify_no_range_leak(name: str, query: Dict[str, str], rendered: str) -> None:
    """Raise if `rendered` reveals any of ``RANGE_KEYS``'s values from `query`.

    Checked against the RENDERED prompt, not the template used to build it:
    see ``RANGE_KEYS``'s own docstring for why a promise about the template
    is not enough. A query lacking some ``RANGE_KEYS`` entry entirely (e.g.
    ``tof_membership_query_gen``'s queries, which carry no ``seq_len``) makes
    that key's check vacuously true -- there is nothing to leak.

    Raises
    ------
    ValueError
        Naming the offending key and its value, and `name`, when that value's
        string form appears in `rendered`.
    """
    for key in RANGE_KEYS:
        if key in query and str(query[key]) in rendered:
            raise ValueError(
                f"condition {name!r} is omit_range=True (its prompt must "
                f"never reveal the position range) but its rendered prompt "
                f"still contains {key}={query[key]!r}: the supplied "
                "range_free_template leaks the very thing it exists to omit."
            )


def get_periodic_prompts(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> Iterable[RenderedQuery]:
    """Render every information condition of every query, in one loop.

    For each query :func:`generate_sequence` (via ``prompter.query_gen``)
    produces, renders every entry of `conditions` against that query's
    :class:`Contexts` and yields one :class:`~smolbench.induction._common.RenderedQuery`
    carrying all of them, keyed by condition name in `conditions`'s iteration
    order. `tokenizer` defines every padded arm's token target and must be
    the model's own -- see the module docstring's tokenizer discipline.

    Rendering happens in two stages per query: first every condition WITHOUT
    ``match_tokens_to`` (recording its rendered prompt and
    ``tokenizer.count(...)`` of it), then every condition WITH one, via
    :func:`~smolbench.evals.tokenization.token_matched_noise_prompt` against
    the ALREADY-RECORDED target condition's count. A padded condition's own
    count is its target by construction -- the pad search verifies it hits
    the target exactly -- so it is not re-tokenized after padding.

    Raises
    ------
    ValueError
        Raised once, before any query is rendered, if some condition's
        ``match_tokens_to`` names a condition absent from `conditions` (names
        the missing condition), or names a condition that is ITSELF padded
        (names it): a padded arm's own count is not available to pad
        against, since it depends on the pad search that has not run yet,
        and a chain of padded arms has no count to bottom out on.
    ValueError
        Propagated from :func:`~smolbench.evals.tokenization.token_matched_noise_prompt`
        when the noise arm's precondition fails for some query -- that query's
        extensional prompt is not STRICTLY longer, in tokens, than its
        intensional one, so no appended pad can reach the target (see the module
        docstring's "Noise-arm PRECONDITION"; measured to happen at n <= 2).
        Deliberately NOT caught here: a fallback to the unpadded render would
        ship a length control byte-identical to the arm it controls for, and no
        caller checked for that. Failing at quiz-construction time keeps the
        confound out of collected data.
    ValueError
        Also propagated from ``token_matched_noise_prompt`` (or
        :func:`~smolbench.evals.tokenization.choose_whitespace_unit`) when no
        whitespace pad can hit the target exactly under `tokenizer`.
    ValueError
        From :func:`_resolve_arm_template` when an ``omit_range`` condition's
        ``prompter.range_free_template`` is ``None`` (naming the condition and
        ``range_free_template``), or from :func:`_verify_no_range_leak` when
        an ``omit_range`` condition's rendered prompt still reveals a
        ``RANGE_KEYS`` value (naming the condition and the leaked key).
    """
    # Validate the mapping ONCE, before any query is rendered: a bad
    # `match_tokens_to` is a construction-time mistake in `conditions` itself,
    # not something that should only surface after partial work on the first
    # query.
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
            raise ValueError(
                f"condition {name!r}: match_tokens_to target {target!r} is "
                f"itself padded (match_tokens_to={conditions[target].match_tokens_to!r}). "
                "A padded arm's own count is not available to pad against "
                "-- it depends on the very pad search that has not run yet "
                "-- and a chain of padded arms has no count to bottom out on."
            )

    period_to_label, pos_to_compound = generate_sequence(config)

    contexts = Contexts(
        intensional=_render_intensional(period_to_label),
        extensional=_render_extensional(pos_to_compound),
    )

    # Probe the pad atom once, not per query: it depends only on the tokenizer.
    unit: str = choose_whitespace_unit(tokenizer)

    # Split once: order-independent of `conditions`'s own iteration order,
    # since stage membership only depends on `match_tokens_to`, not on where
    # an entry sits in the mapping.
    unpadded = [(n, c) for n, c in conditions.items() if c.match_tokens_to is None]
    padded = [(n, c) for n, c in conditions.items() if c.match_tokens_to is not None]

    for query, answer in prompter.query_gen(period_to_label, pos_to_compound, config.seed):
        prompts: Dict[str, str] = {}
        token_counts: Dict[str, int] = {}

        # Stage 1: every condition that renders plainly, with no pad target
        # to wait on.
        for name, condition in unpadded:
            template = _resolve_arm_template(name, condition, prompter)
            rendered = template.safe_substitute(
                build_substitution(query, prompter, condition.context(contexts))
            )
            if condition.omit_range:
                _verify_no_range_leak(name, query, rendered)
            prompts[name] = rendered
            token_counts[name] = tokenizer.count(rendered)

        # Stage 2: every condition padded to a stage-1 condition's count.
        # `context_renderer` renders exactly as stage 1 above, so the two
        # differ only in the appended whitespace pad.
        for name, condition in padded:
            template = _resolve_arm_template(name, condition, prompter)
            target_count = token_counts[condition.match_tokens_to]
            rendered = token_matched_noise_prompt(
                context_renderer(prompter, query, template=template),
                condition.context(contexts),
                target_count,
                tokenizer,
                unit=unit,
            )
            if condition.omit_range:
                _verify_no_range_leak(name, query, rendered)
            prompts[name] = rendered
            # NOT tokenizer.count(rendered) again: the pad search already
            # verified this hits target_count exactly, and the tokenizer ran
            # during that search regardless of whether anyone reads the count.
            token_counts[name] = target_count

        # Emit in `conditions`'s own order, not the stage-1/stage-2 split
        # order used to build the two dicts above.
        yield RenderedQuery(
            prompts={name: prompts[name] for name in conditions},
            token_counts={name: token_counts[name] for name in conditions},
            answer=answer,
        )


# ---------------------------------------------------------------------------
# Quiz wrappers
# ---------------------------------------------------------------------------

def get_periodic_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> Dict[str, Quiz]:
    """Wrap :func:`get_periodic_prompts` as ``ToF`` quizzes, keyed by condition name.

    Returns a ``dict`` in `conditions`'s iteration order (``CONDITIONS``'s
    default order: ``intens``, ``extens``, ``noise_intens``, ``zero``), not a
    positional tuple: a caller reads a specific arm by NAME
    (``quizzes["extens"]``) rather than by position, so adding, removing or
    reordering conditions can never silently relabel an existing caller's
    arms.
    """
    return quizzes_from_prompts(
        get_periodic_prompts(config, prompter, tokenizer=tokenizer, conditions=conditions),
        ToF,
        conditions,
    )


def get_periodic_numeric_quiz(
    config: PeriodicConfig,
    prompter: Prompter,
    *,
    tokenizer: Tokenizer,
    conditions: Mapping[str, Condition] = CONDITIONS,
) -> Dict[str, Quiz]:
    """Wrap :func:`get_periodic_prompts` as ``Numeric`` quizzes, keyed by condition name.

    See :func:`get_periodic_quiz`'s docstring for the return shape rationale;
    this is the same wrapper over ``Numeric`` instead of ``ToF``.
    """
    return quizzes_from_prompts(
        get_periodic_prompts(config, prompter, tokenizer=tokenizer, conditions=conditions),
        Numeric,
        conditions,
    )


# ---------------------------------------------------------------------------
# Built-in query generators
# ---------------------------------------------------------------------------

# tof_membership_query_gen samples at most this many queries of EACH polarity
# per quiz, so quiz size stays fixed as n grows. n changes task difficulty and
# the lcm(1..n) context length; it must never silently change sample size,
# because a replication design is powered around fixed question counts. (This
# ToF generator is pinned by the golden hashes and used by sibling studies;
# the family-ladder driver runs numeric_count_query_gen, whose count is n by
# construction.)
MAX_QUERIES_PER_POLARITY: int = 10


def tof_membership_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[Tuple[Dict[str, str], bool]]:
    """Yield True/False queries of the form "Does label appear at position pos?"

    Yields ``({"pos": ..., "label": ...}, answer)`` pairs: at most
    ``MAX_QUERIES_PER_POLARITY`` True queries and equally many False ones (fewer
    if the pattern admits fewer of either polarity), sampled without replacement
    under ``seed``; period-1 labels are excluded as trivially True. Both mappings
    come from :func:`generate_sequence`.
    """
    rng = np.random.default_rng(seed)

    true_qs: list = []
    false_qs: list = []

    # Hoisted: the (period, label) ordering is position-independent.
    period_labels = sorted(period_to_label.items())
    for pos in sorted(pos_to_compound.keys()):
        for period, label in period_labels:
            if period == 1:
                continue  # true for every position -- skip this trivial query
            entry = ({"pos": str(pos), "label": label}, pos % period == 0)
            (true_qs if pos % period == 0 else false_qs).append(entry)

    n = min(len(true_qs), len(false_qs), MAX_QUERIES_PER_POLARITY)
    if n == 0:
        # Too small to admit both polarities -> empty quiz, not an error
        # (legitimate for tiny test configs).
        return

    # True block then False block, unshuffled: each query is a separate
    # prompt, so order leaks nothing between questions.
    for idx in rng.choice(len(true_qs), n, replace=False):
        yield true_qs[idx]
    for idx in rng.choice(len(false_qs), n, replace=False):
        yield false_qs[idx]


def numeric_count_query_gen(
    period_to_label: PeriodToLabel,
    pos_to_compound: PosToCompound,
    seed: int,
) -> Iterable[Tuple[Dict[str, str], int]]:
    """Yield count queries of the form "How many positions 1..seq_len contain label?"

    Yields one ``({"label": ..., "seq_len": ...}, answer)`` pair per label, the
    answer being floor(seq_len / period) -- always exact, since seq_len is the
    lcm of the harmonic periods on every pathway. Reads only ``pos_to_compound``'s
    KEYS (to find ``seq_len``).

    The query SET is deterministic: one query per label, in ascending-period
    order, so this generator consumes no randomness and IGNORES `seed`. The
    parameter stays because ``Prompter.query_gen`` is one interchangeable
    protocol -- ``(period_to_label, pos_to_compound, seed)`` -- that
    :func:`get_periodic_prompts` calls without knowing which generator it holds,
    and the sibling :func:`tof_membership_query_gen` genuinely samples under it.
    Dropping the argument here would make the two generators non-substitutable
    and push a hasattr/try-except call shim into the shared caller for no gain.
    A seed still reaches this generator's OUTPUT indirectly, through the labels:
    ``PeriodicConfig`` draws them with the same seed, so across replicates the
    label strings change while the query structure does not.
    """
    seq_len = max(pos_to_compound.keys())
    for period, label in sorted(period_to_label.items()):
        yield {"label": label, "seq_len": str(seq_len)}, seq_len // period


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    template = string.Template(
        "Context:\n"
        "---\n"
        "There is a counting game. Count positions starting from 1. "
        "At each position write down words according to the following rules:\n"
        "$positive_info\n"
        "Query:\n"
        "How many of the positions 1 through $seq_len include '$label'? "
        "Answer with a single integer."
    )

    # The `zero` condition's range-free counterpart of `template` above: the
    # same question with its position-range clause removed, exactly as a real
    # driver supplies one (see `notebooks/induction/run_study.py`'s
    # `zero_template`/`RANGE_CLAUSE`). See the module docstring's
    # "Information conditions" section for why `zero` needs this rather than
    # `template` itself.
    range_free_template = string.Template(
        template.template.replace(" 1 through $seq_len", "")
    )

    cfg = PeriodicConfig(
        n=3,
        labels=["fizz", "buzz", "gerbil"],
        seed=42,
    )

    # No served model here, so measure with a fixed tiktoken encoding. A real
    # run passes the model under test's; see the module docstring's tokenizer
    # discipline.
    demo_tokenizer = TiktokenTokenizer("cl100k_base")

    # A real caller supplies BOTH templates (see `Prompter.range_free_template`'s
    # docstring in `_common.py`), so this demo does too, and renders every
    # entry of `CONDITIONS` (the default) -- `zero` included.
    for rendered in get_periodic_prompts(
        cfg,
        Prompter(template, numeric_count_query_gen, range_free_template=range_free_template),
        tokenizer=demo_tokenizer,
    ):
        print("-- intensional --")
        print(rendered.prompts["intens"])
        print("-- extensional --")
        print(rendered.prompts["extens"])
        print("-- zero --")
        print(rendered.prompts["zero"])
        print("answer:", rendered.answer)
        print(
            "token counts -- intens:", rendered.token_counts["intens"],
            "extens:", rendered.token_counts["extens"],
            "noise_intens:", rendered.token_counts["noise_intens"],
            "zero:", rendered.token_counts["zero"],
        )
        print()
