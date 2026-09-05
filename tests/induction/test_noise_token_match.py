"""Induction noise arm: whitespace padding matched on TOKEN count.

``noise_intens`` is a length control: exact per-question token parity with
extens, whitespace only."""

import dataclasses
import string

import pytest

from conftest import MergeEverythingTokenizer, StubTokenizer, TruncatingTokenizer

from smolbench.induction._common import (
    WHITESPACE_UNITS, choose_whitespace_unit, context_renderer, token_matched_noise_prompt)
from smolbench.induction.periodic import (
    CONDITIONS, PeriodicConfig, get_periodic_numeric_quiz)
from smolbench.induction.periodic import Prompter as PeriodicPrompter, numeric_count_query_gen

PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
CONTEXT = "Every 3 positions write gerbil.\n"

#: The arms whose question text states the range; the zero arm needs a
#: range-free template these minimal fixtures do not carry.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}

def tiktoken_tokenizer(encoding_name: str):
    """Return a `TiktokenTokenizer`, or skip if it cannot be built offline."""
    from smolbench.evals.tokenization import TiktokenTokenizer

    try:
        return TiktokenTokenizer(encoding_name)
    except Exception as exc:  # noqa: BLE001 -- ImportError, network, cache miss
        pytest.skip(f"tiktoken {encoding_name} unavailable offline: {exc}")

def _render():
    return context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )

@pytest.fixture(params=["stub", "cl100k_base", "o200k_base"])
def tokenizer(request):
    """Every tokenizer the token-matching tests run against."""
    if request.param == "stub":
        return StubTokenizer()
    return tiktoken_tokenizer(request.param)

def test_noise_prompt_matches_extens_token_count(tokenizer):
    """Every noise prompt has EXACTLY its extens prompt's token count.

    The former ``extens_template`` parametrization is gone with the field
    itself (12-32): all three arms now render from the ONE ``template``, so
    there is a single build to pin.
    """
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=6, labels=6, seed=1776),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        tokenizer=tokenizer, conditions=POSITIVE_ARMS,
    )
    intens, extens, noise = (
        quizzes["intens"], quizzes["extens"], quizzes["noise_intens"])
    assert len(intens) == len(extens) == len(noise) > 0
    for extens_q, noise_q in zip(extens, noise):
        assert tokenizer.count(noise_q.prompt) == tokenizer.count(extens_q.prompt)

def test_pad_adds_only_whitespace(tokenizer):
    """The noise prompt is its intensional twin plus whitespace, nothing else."""
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=5, labels=5, seed=99),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        tokenizer=tokenizer, conditions=POSITIVE_ARMS,
    )
    intens, noise = quizzes["intens"], quizzes["noise_intens"]
    assert len(intens) == len(noise) > 0
    for intens_q, noise_q in zip(intens, noise):
        assert "".join(noise_q.prompt.split()) == "".join(intens_q.prompt.split())
        assert len(noise_q.prompt) > len(intens_q.prompt)

def test_other_arms_are_independent_of_the_tokenizer():
    """Only ``noise_intens`` varies with the tokenizer."""
    args = (
        PeriodicConfig(n=5, labels=5, seed=7),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
    )
    stub = get_periodic_numeric_quiz(*args, tokenizer=StubTokenizer(),
                                     conditions=POSITIVE_ARMS)
    other = get_periodic_numeric_quiz(*args, tokenizer=tiktoken_tokenizer("cl100k_base"),
                                      conditions=POSITIVE_ARMS)
    for arm in ("intens", "extens"):
        assert [q.prompt for q in stub[arm]] == [q.prompt for q in other[arm]]
    assert ([q.prompt for q in stub["noise_intens"]]
            != [q.prompt for q in other["noise_intens"]])

def test_choose_whitespace_unit_picks_a_linear_atom(tokenizer):
    """The chosen atom is whitespace costing ~1 token per repetition."""
    unit = choose_whitespace_unit(tokenizer)
    assert unit in WHITESPACE_UNITS
    assert unit.strip() == ""
    # "linear atom" = >= 0.5 tokens per repetition (no runaway merging) ...
    assert tokenizer.count(unit * 256) >= 128
    # ... unlike naive spaces, which BPE merges ~10:1 or worse.
    assert tokenizer.count(" " * 512) < 64

@pytest.mark.parametrize(
    "bad", (TruncatingTokenizer(cap=512), MergeEverythingTokenizer()),
    ids=["truncating", "merges_all"])
def test_choose_whitespace_unit_rejects_bad_tokenizers(bad):
    """Saturating or all-merging tokenizers are refused, not quietly accepted."""
    with pytest.raises(ValueError):
        choose_whitespace_unit(bad)

@pytest.mark.parametrize("target", (40, 137, 4097))
def test_token_matched_noise_prompt_hits_arbitrary_targets(tokenizer, target):
    """Any reachable target is hit exactly, not approximately."""
    prompt = token_matched_noise_prompt(_render(), CONTEXT, target, tokenizer)
    assert tokenizer.count(prompt) == target

def test_unmatched_targets_raise(tokenizer):
    """BOTH unreachable targets raise; neither returns a silently unpadded prompt.

    Pins the 12-09 fix. An already-over-long base used to log a warning and
    return the UNPADDED intensional render, which no caller checked: the
    "length control" arm then shipped byte-identical to the arm it controls
    for. The over-long case and the un-hittable-target case are now the same
    loud ``ValueError``.
    """
    render = _render()
    with pytest.raises(ValueError) as over_long:
        token_matched_noise_prompt(render, CONTEXT, 1, tokenizer)
    # The message must name both counts, or an operator cannot tell this
    # failure from the search failure below.
    assert "1" in str(over_long.value)
    with pytest.raises(ValueError):
        token_matched_noise_prompt(
            render, CONTEXT, 5_000, MergeEverythingTokenizer(), unit=" \t"
        )


@pytest.mark.parametrize("n", (1, 2))
def test_tiny_configs_raise_rather_than_ship_an_unpadded_noise_arm(tokenizer, n):
    """At n<=2 quiz generation RAISES instead of emitting noise == intens.

    Measured at HEAD under all three tokenizers: at n=1 and n=2 the
    extensional listing is no longer than the intensional rules, so no
    appended pad can reach the target and every noise prompt came back
    unpadded. ``get_periodic_prompts`` now lets the ``ValueError``
    propagate (12-09), so the precondition failure is visible at the quiz
    boundary rather than inside a study's collected data. n=3 is unaffected.
    """
    with pytest.raises(ValueError):
        get_periodic_numeric_quiz(
            PeriodicConfig(n=n, labels=n, seed=0),
            PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
            tokenizer=tokenizer, conditions=POSITIVE_ARMS,
        )


def test_prompter_has_no_legacy_chromatic_hooks():
    """``Prompter`` carries neither ``substitution`` nor ``extens_template`` (12-32).

    Both served the deleted chromatic ``query_years`` mechanism: the first was
    ``{}`` at all 11 construction sites, the second had no production caller.
    Their removal is pinned by field name, so a re-introduction (or a revived
    ``resolved_extens_template`` property) fails here rather than growing a
    second, silently-unused render path.
    """
    prompter = PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen)
    assert not hasattr(prompter, "substitution")
    assert not hasattr(prompter, "extens_template")
    assert not hasattr(prompter, "resolved_extens_template")
    # `range_free_template` is the ONE field that came back, and unlike the two
    # above it is LIVE: the zero condition renders from it, and the production
    # study supplies it (see run_study.zero_template). The field list stays an
    # exact pin so a fourth, unused hook cannot appear unnoticed.
    assert [f.name for f in dataclasses.fields(prompter)] == [
        "template", "query_gen", "range_free_template"]
