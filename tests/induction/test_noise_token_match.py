"""Induction noise arm: whitespace padding matched on TOKEN count.

``noise_intens`` is a length control: exact per-question token parity with
extens, whitespace only."""

import string

import pytest

from conftest import MergeEverythingTokenizer, StubTokenizer, TruncatingTokenizer

from smolbench.induction._common import (
    WHITESPACE_UNITS, choose_whitespace_unit, context_renderer, token_matched_noise_prompt)
from smolbench.induction.periodic import PeriodicConfig, get_periodic_numeric_quiz
from smolbench.induction.periodic import Prompter as PeriodicPrompter, numeric_count_query_gen

PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
# Extens can use a different, longer template, so only a per-prompt match equalizes.
PERIODIC_EXT_TMPL = string.Template(
    "CTX EXTENSIONAL LISTING:\n$positive_info\n"
    "Q: How many of positions 1..$seq_len include '$label'?"
)

CONTEXT = "Every 3 positions write gerbil.\n"

def tiktoken_tokenizer(encoding_name: str):
    """Return a `TiktokenTokenizer`, or skip if it cannot be built offline."""
    from smolbench.evals.tokenization import TiktokenTokenizer

    try:
        return TiktokenTokenizer(encoding_name)
    except Exception as exc:  # noqa: BLE001 -- ImportError, network, cache miss
        pytest.skip(f"tiktoken {encoding_name} unavailable offline: {exc}")

def _render():
    return context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )

@pytest.fixture(params=["stub", "cl100k_base", "o200k_base"])
def tokenizer(request):
    """Every tokenizer the token-matching tests run against."""
    if request.param == "stub":
        return StubTokenizer()
    return tiktoken_tokenizer(request.param)

@pytest.mark.parametrize(
    "build", (
        lambda tok: get_periodic_numeric_quiz(
            PeriodicConfig(n=6, labels=6, seed=1776),
            PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
            tokenizer=tok,
        ),
        lambda tok: get_periodic_numeric_quiz(
            PeriodicConfig(n=6, labels=6, seed=1776),
            PeriodicPrompter(
                PERIODIC_TMPL, {}, numeric_count_query_gen, PERIODIC_EXT_TMPL),
            tokenizer=tok,
        ),
    ), ids=["shared_template", "extens_template"])
def test_noise_prompt_matches_extens_token_count(tokenizer, build):
    """Every noise prompt has EXACTLY its extens prompt's token count."""
    intens, extens, noise = build(tokenizer)
    assert len(intens) == len(extens) == len(noise) > 0
    for extens_q, noise_q in zip(extens, noise):
        assert tokenizer.count(noise_q.prompt) == tokenizer.count(extens_q.prompt)

def test_pad_adds_only_whitespace(tokenizer):
    """The noise prompt is its intensional twin plus whitespace, nothing else."""
    intens, _extens, noise = get_periodic_numeric_quiz(
        PeriodicConfig(n=5, labels=5, seed=99),
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
        tokenizer=tokenizer,
    )
    assert len(intens) == len(noise) > 0
    for intens_q, noise_q in zip(intens, noise):
        assert "".join(noise_q.prompt.split()) == "".join(intens_q.prompt.split())
        assert len(noise_q.prompt) > len(intens_q.prompt)

def test_other_arms_are_independent_of_the_tokenizer():
    """Only ``noise_intens`` varies with the tokenizer."""
    args = (
        PeriodicConfig(n=5, labels=5, seed=7),
        PeriodicPrompter(PERIODIC_TMPL, {}, numeric_count_query_gen),
    )
    stub = get_periodic_numeric_quiz(*args, tokenizer=StubTokenizer())
    other = get_periodic_numeric_quiz(*args, tokenizer=tiktoken_tokenizer("cl100k_base"))
    assert [q.prompt for q in stub[0]] == [q.prompt for q in other[0]]  # intens
    assert [q.prompt for q in stub[1]] == [q.prompt for q in other[1]]  # extens
    assert [q.prompt for q in stub[2]] != [q.prompt for q in other[2]]  # noise

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

def test_unmatched_targets_warn_or_raise(tokenizer, caplog):
    """Unreachable-by-shrinking warns and returns unpadded; unhittable raises."""
    render = _render()
    with caplog.at_level("WARNING"):
        assert token_matched_noise_prompt(render, CONTEXT, 1, tokenizer) == render(CONTEXT)
    assert any(r.levelname == "WARNING" for r in caplog.records)
    with pytest.raises(ValueError):
        token_matched_noise_prompt(
            render, CONTEXT, 5_000, MergeEverythingTokenizer(), unit=" \t"
        )
