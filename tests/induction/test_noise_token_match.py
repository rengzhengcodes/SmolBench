"""Test whitespace-padded, token-matched induction noise prompts."""

import string

import pytest
from conftest import MergeEverythingTokenizer, StubTokenizer, TruncatingTokenizer

from smolbench.evals.tokenization import (
    WHITESPACE_UNITS,
    TiktokenTokenizer,
    choose_whitespace_unit,
    token_matched_noise_prompt,
)
from smolbench.induction._common import Prompter as PeriodicPrompter
from smolbench.induction._common import context_renderer
from smolbench.induction.periodic import (
    CONDITIONS,
    PeriodicConfig,
    get_periodic_numeric_quiz,
    numeric_count_query_gen,
)

PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
CONTEXT = "Every 3 positions write gerbil.\n"

#: Exclude range-free zero arm: these fixtures use a ranged template.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}


def tiktoken_tokenizer(encoding_name: str) -> TiktokenTokenizer:
    """Build a tokenizer or skip unavailable offline encodings."""

    try:
        return TiktokenTokenizer(encoding_name)
    except Exception as exc:  # noqa: BLE001 -- ImportError, network, cache miss
        pytest.skip(f"tiktoken {encoding_name} unavailable offline: {exc}")
        raise


def _render() -> str:
    return context_renderer(
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        {"seq_len": "60", "label": "gerbil"},
    )


@pytest.fixture(params=["stub", "cl100k_base", "o200k_base"])
def tokenizer(request: pytest.FixtureRequest) -> "StubTokenizer | TiktokenTokenizer":
    """Provide tokenizers for matching tests."""
    if request.param == "stub":
        return StubTokenizer()
    return tiktoken_tokenizer(request.param)


def test_noise_prompt_matches_extens_token_count(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
) -> None:
    """Match each noise prompt to extens token count."""
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=6, labels=6, seed=1776),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        tokenizer=tokenizer,
        conditions=POSITIVE_ARMS,
    )
    intens, extens, noise = (
        quizzes["intens"],
        quizzes["extens"],
        quizzes["noise_intens"],
    )
    assert len(intens) == len(extens) == len(noise) > 0
    for extens_q, noise_q in zip(extens, noise):
        assert tokenizer.count(noise_q.prompt) == tokenizer.count(extens_q.prompt)


def test_pad_adds_only_whitespace(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
) -> None:
    """Permit only whitespace differences from intens prompts."""
    quizzes = get_periodic_numeric_quiz(
        PeriodicConfig(n=5, labels=5, seed=99),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
        tokenizer=tokenizer,
        conditions=POSITIVE_ARMS,
    )
    intens, noise = quizzes["intens"], quizzes["noise_intens"]
    assert len(intens) == len(noise) > 0
    for intens_q, noise_q in zip(intens, noise):
        assert "".join(noise_q.prompt.split()) == "".join(intens_q.prompt.split())
        assert len(noise_q.prompt) > len(intens_q.prompt)


def test_other_arms_are_independent_of_the_tokenizer() -> None:
    """Restrict tokenizer-dependent output to ``noise_intens``."""
    args = (
        PeriodicConfig(n=5, labels=5, seed=7),
        PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
    )
    stub = get_periodic_numeric_quiz(
        *args, tokenizer=StubTokenizer(), conditions=POSITIVE_ARMS
    )
    other = get_periodic_numeric_quiz(
        *args, tokenizer=tiktoken_tokenizer("cl100k_base"), conditions=POSITIVE_ARMS
    )
    for arm in ("intens", "extens"):
        assert [q.prompt for q in stub[arm]] == [q.prompt for q in other[arm]]
    assert [q.prompt for q in stub["noise_intens"]] != [
        q.prompt for q in other["noise_intens"]
    ]


def test_choose_whitespace_unit_picks_a_linear_atom(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
) -> None:
    """Choose a whitespace unit with near-linear token cost."""
    unit = choose_whitespace_unit(tokenizer)
    assert unit in WHITESPACE_UNITS
    assert unit.strip() == ""
    # Prevent runaway token merging.
    assert tokenizer.count(unit * 256) >= 128
    assert tokenizer.count(" " * 512) < 64


@pytest.mark.parametrize(
    "bad",
    (TruncatingTokenizer(cap=512), MergeEverythingTokenizer()),
    ids=["truncating", "merges_all"],
)
def test_choose_whitespace_unit_rejects_bad_tokenizers(
    bad: TruncatingTokenizer | MergeEverythingTokenizer,
) -> None:
    """Reject saturating and all-merging tokenizers."""
    with pytest.raises(ValueError):
        choose_whitespace_unit(bad)


@pytest.mark.parametrize("target", (40, 137, 4097))
def test_token_matched_noise_prompt_hits_arbitrary_targets(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
    target: int,
) -> None:
    """Hit reachable token targets exactly."""
    prompt = token_matched_noise_prompt(_render(), CONTEXT, target, tokenizer)
    assert tokenizer.count(prompt) == target


def test_unmatched_targets_raise(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
) -> None:
    """Reject unreachable token targets."""
    render = _render()
    with pytest.raises(ValueError) as over_long:
        token_matched_noise_prompt(render, CONTEXT, 1, tokenizer)
    # Name counts to distinguish length from search failures.
    assert "1" in str(over_long.value)
    with pytest.raises(ValueError):
        token_matched_noise_prompt(
            render, CONTEXT, 5_000, MergeEverythingTokenizer(), unit=" \t"
        )


@pytest.mark.parametrize("n", (1, 2))
def test_tiny_configs_raise_rather_than_ship_an_unpadded_noise_arm(
    tokenizer: "StubTokenizer | TiktokenTokenizer",
    n: int,
) -> None:
    """Reject tiny configs: extens listings cannot pad their noise controls."""
    with pytest.raises(ValueError):
        get_periodic_numeric_quiz(
            PeriodicConfig(n=n, labels=n, seed=0),
            PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen),
            tokenizer=tokenizer,
            conditions=POSITIVE_ARMS,
        )
