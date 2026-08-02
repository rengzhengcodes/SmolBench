"""The induction noise arm: whitespace padding matched on TOKEN count.

``noise_intens`` is a LENGTH CONTROL -- the intensional context padded until
its prompt is as long as the extensional prompt, so an intens-vs-extens gap
cannot be explained by prompt length. It only works if "as long as" is exact
and measured in the unit the model consumes. It used to be neither: random
alphanumerics matched on CHARACTER count came out 1.4-1.6x the extensional
prompt's token count, so the control was longer than the thing it controlled
for.

These tests pin the properties that make the replacement a control:

* the noise prompt's token count EQUALS its extensional counterpart's, per
  question, not on average and not within a tolerance;
* the pad adds only whitespace -- no content the model could read as signal;
* the intensional and extensional arms are untouched by any of it.

They run against `conftest.StubTokenizer` (always) and against real tiktoken
encodings (when the encoding files are locally available), so the machinery
is exercised both under a controlled model of BPE behaviour and under the
real thing.
"""

import string

import pytest

from conftest import MergeEverythingTokenizer, StubTokenizer, TruncatingTokenizer

from smolbench.induction._common import (
    WHITESPACE_UNITS,
    choose_whitespace_unit,
    context_renderer,
    token_matched_noise_prompt,
)
from smolbench.induction.chromatic import (
    ChromaticIntervalsConfig,
    Prompter as ChromaticPrompter,
    get_random_exclusive_quiz,
    succession_query_gen,
)
from smolbench.induction.periodic import (
    PeriodicConfig,
    Prompter as PeriodicPrompter,
    get_periodic_numeric_quiz,
    numeric_count_query_gen,
)

PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
CHROM_TMPL = string.Template(
    "ROLE $role PARADE $parade\n$positive_info\nQ: Has $color1 handed to $color2?"
)
# Mirrors the notebooks' extensional template in the way that matters here:
# it renders from a DIFFERENT template than the intensional arm and adds a
# $query_years block, so equal-length contexts would not give equal-length
# prompts. Only a per-prompt match can close that gap.
CHROM_EXT_TMPL = string.Template(
    "ROLE $role PARADE $parade EXTENSIONAL\n$positive_info\n$query_years\n"
    "Q: Has $color1 handed to $color2?"
)
CHROM_SUB = {"role": "Twislax", "parade": "Gildane"}


def tiktoken_tokenizer(encoding_name: str):
    """Returns a `TiktokenTokenizer`, or skips if it cannot be built offline.

    ``tiktoken`` is an optional extra and its BPE files are fetched on first
    use, so neither is guaranteed in a bare checkout. The offline suite must
    not fail (or reach for the network) on that account -- the stub-tokenizer
    parametrization already covers the logic, and these params add real-BPE
    coverage wherever it happens to be available.
    """
    from smolbench.evals.tokenization import TiktokenTokenizer

    try:
        return TiktokenTokenizer(encoding_name)
    except Exception as exc:  # noqa: BLE001 -- ImportError, network, cache miss
        pytest.skip(f"tiktoken {encoding_name} unavailable offline: {exc}")


@pytest.fixture(params=["stub", "cl100k_base", "o200k_base"])
def tokenizer(request):
    """Every tokenizer the token-matching tests run against."""
    if request.param == "stub":
        return StubTokenizer()
    return tiktoken_tokenizer(request.param)


# ---------------------------------------------------------------------------
# The headline property: exact per-prompt token equality
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", (1776, 1777))
def test_periodic_noise_prompt_matches_extens_token_count(tokenizer, seed):
    """Every periodic noise prompt has EXACTLY its extens prompt's tokens."""
    intens, extens, noise = get_periodic_numeric_quiz(
        PeriodicConfig(n=6, labels=6, seed=seed),
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        tokenizer=tokenizer,
    )
    assert len(intens) > 0  # sanity: the generator actually yielded queries
    for extens_q, noise_q in zip(extens, noise):
        assert tokenizer.count(noise_q.prompt) == tokenizer.count(extens_q.prompt)


@pytest.mark.parametrize("seed", (1776, 1777))
def test_chromatic_noise_prompt_matches_extens_token_count(tokenizer, seed):
    """Same, chromatic -- including the extens-only ``$query_years`` block.

    This is the case a context-level match could not have handled: the
    extensional prompt carries an entire enumerated year list the noise
    prompt's template never renders, so matching the CONTEXTS would leave the
    prompts unequal by however long that block is.
    """
    intens, extens, noise = get_random_exclusive_quiz(
        ChromaticIntervalsConfig(n=250, intervals=62, colors=45, seed=seed),
        ChromaticPrompter(CHROM_TMPL, CHROM_SUB, succession_query_gen, CHROM_EXT_TMPL),
        tokenizer=tokenizer,
    )
    assert len(intens) > 0
    # The templates really do differ, or this test would prove nothing.
    assert "$query_years" not in CHROM_TMPL.template
    for extens_q, noise_q in zip(extens, noise):
        assert tokenizer.count(noise_q.prompt) == tokenizer.count(extens_q.prompt)


# ---------------------------------------------------------------------------
# What the pad may and may not contain
# ---------------------------------------------------------------------------


def test_pad_adds_only_whitespace(tokenizer):
    """The noise prompt is its intensional twin plus whitespace, nothing else.

    Stripping whitespace from both must leave IDENTICAL strings: the pad
    introduces no characters a model could read as content (the previous
    implementation appended random letters and digits, which is filler a
    model can at least try to parse), and it removes nothing from the rules
    the intensional arm states.
    """
    intens, _extens, noise = get_periodic_numeric_quiz(
        PeriodicConfig(n=5, labels=5, seed=99),
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        tokenizer=tokenizer,
    )
    for intens_q, noise_q in zip(intens, noise):
        assert "".join(noise_q.prompt.split()) == "".join(intens_q.prompt.split())
        assert len(noise_q.prompt) > len(intens_q.prompt)  # something was added


def test_other_arms_are_independent_of_the_tokenizer():
    """Only ``noise_intens`` varies with the tokenizer.

    Cross-model comparisons stay paired on identical prompts for the
    intensional and extensional conditions; the quiz factory taking a model
    argument must not leak into anything but the control arm.
    """
    args = (
        PeriodicConfig(n=5, labels=5, seed=7),
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
    )
    stub = get_periodic_numeric_quiz(*args, tokenizer=StubTokenizer())
    other = get_periodic_numeric_quiz(*args, tokenizer=tiktoken_tokenizer("cl100k_base"))
    assert [q.prompt for q in stub[0]] == [q.prompt for q in other[0]]  # intens
    assert [q.prompt for q in stub[1]] == [q.prompt for q in other[1]]  # extens
    assert [q.prompt for q in stub[2]] != [q.prompt for q in other[2]]  # noise


# ---------------------------------------------------------------------------
# Pad-atom selection
# ---------------------------------------------------------------------------


def test_choose_whitespace_unit_picks_a_linear_atom(tokenizer):
    """The chosen atom costs ~1 token per repetition under this tokenizer."""
    unit = choose_whitespace_unit(tokenizer)
    assert unit in WHITESPACE_UNITS
    assert unit.strip() == ""  # whitespace only
    # Not merely "grows" -- grows about proportionally, which is what makes an
    # arbitrary token target reachable.
    assert tokenizer.count(unit * 256) >= 128


def test_repeated_single_space_is_not_a_usable_pad(tokenizer):
    """A naive `" " * n` pad cannot reach a large token target.

    The reason `choose_whitespace_unit` exists: BPE vocabularies carry tokens
    for runs of a single whitespace character, so hundreds of spaces cost a
    handful of tokens. Anyone "simplifying" the pad to plain spaces would
    reintroduce the length confound, silently.
    """
    assert tokenizer.count(" " * 512) < 64


def test_choose_whitespace_unit_rejects_a_truncating_tokenizer():
    """A tokenizer that SATURATES is refused, not quietly accepted.

    The dangerous case, and a live one: a capped tokenizer is perfectly
    linear below its cap, so a probe that stops at 256 repetitions sees a
    healthy atom and hands back a pad that can never grow past 512 tokens.
    The extensional prompt and its pad would then both measure 512 and the
    search would call them matched. The top probe exists to reach past any
    plausible cap so this fails loudly here instead.
    """
    with pytest.raises(ValueError, match="1 token per repetition"):
        choose_whitespace_unit(TruncatingTokenizer(cap=512))


def test_choose_whitespace_unit_raises_when_everything_merges():
    """A tokenizer that merges all whitespace gets an exception, not a pad.

    Silently returning a saturated pad would leave the control arm SHORTER
    than the extensional arm -- the same confound in the other direction.
    """
    with pytest.raises(ValueError, match="1 token per repetition"):
        choose_whitespace_unit(MergeEverythingTokenizer())


# ---------------------------------------------------------------------------
# token_matched_noise_prompt directly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", (40, 41, 137, 1000, 4097))
def test_token_matched_noise_prompt_hits_arbitrary_targets(tokenizer, target):
    """Any reachable target is hit exactly, not approximately."""
    render = context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )
    prompt = token_matched_noise_prompt(
        render, "Every 3 positions write gerbil.\n", target, tokenizer
    )
    assert tokenizer.count(prompt) == target


def test_unreachable_target_returns_the_unpadded_prompt(tokenizer, caplog):
    """A target below the unpadded prompt cannot be reached by appending.

    Appending only grows a prompt, so this asks for the impossible. The
    documented behaviour is to return the unpadded render and warn -- the
    caller gets a usable (if unmatched) prompt and a log line saying so,
    rather than an exception in the middle of generating a replicate.
    """
    render = context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )
    context = "Every 3 positions write gerbil.\n"
    unpadded = render(context)
    with caplog.at_level("WARNING"):
        prompt = token_matched_noise_prompt(render, context, 1, tokenizer)
    assert prompt == unpadded
    assert "cannot be built by appending" in caplog.text


def test_no_silent_mismatch_when_the_target_is_unhittable():
    """A tokenizer whose count jumps over the target raises rather than
    returning a close-enough prompt.

    ``MergeEverythingTokenizer`` cannot grow a whitespace pad at all, so with
    an explicit unit (bypassing `choose_whitespace_unit`'s refusal) no
    repetition count reaches the target. Returning the nearest prompt would
    be the one outcome this module exists to prevent.
    """
    render = context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )
    with pytest.raises(ValueError, match="could not pad to exactly"):
        token_matched_noise_prompt(
            render,
            "Every 3 positions write gerbil.\n",
            5_000,
            MergeEverythingTokenizer(),
            unit=" \t",
        )
