"""Test whitespace-padded, token-matched induction noise prompts."""

import difflib

import pytest
from conftest import MergeEverythingTokenizer, StubTokenizer, TruncatingTokenizer
from tests.induction._periodic import PERIODIC_TMPL, POSITIVE_ARMS

from smolbench.evals.tokenization import (
    WHITESPACE_UNITS,
    TiktokenTokenizer,
    choose_whitespace_unit,
    token_matched_noise_prompt,
)
from smolbench.induction._common import Prompter as PeriodicPrompter
from smolbench.induction._common import context_renderer
from smolbench.induction.periodic import (
    PeriodicConfig,
    get_periodic_numeric_quiz,
    numeric_count_query_gen,
)

CONTEXT = "Every 3 positions write gerbil.\n"


def tiktoken_tokenizer(encoding_name: str) -> TiktokenTokenizer:
    """Build a tokenizer or skip unavailable offline encodings."""

    try:
        return TiktokenTokenizer(encoding_name)
    except Exception as exc:  # ImportError, network, or cache miss
        pytest.skip(f"tiktoken {encoding_name} unavailable offline: {exc}")
        raise


def _render() -> str:
    return context_renderer(PERIODIC_TMPL, {"seq_len": "60", "label": "gerbil"})


@pytest.fixture(params=["stub", "cl100k_base", "o200k_base"])
def tokenizer(request: pytest.FixtureRequest) -> StubTokenizer | TiktokenTokenizer:
    """Provide tokenizers for matching tests."""
    if request.param == "stub":
        return StubTokenizer()
    return tiktoken_tokenizer(request.param)


def test_noise_prompt_matches_extens_token_count(
    tokenizer: StubTokenizer | TiktokenTokenizer,
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
    tokenizer: StubTokenizer | TiktokenTokenizer,
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
        # Strip-and-compare alone would pass if whitespace were moved rather
        # than added, so also require the intens prompt to survive verbatim
        # once the inserted pad is removed: the diff must be one whitespace run.
        diff = [
            op
            for op in difflib.SequenceMatcher(
                None, intens_q.prompt, noise_q.prompt, autojunk=False
            ).get_opcodes()
            if op[0] != "equal"
        ]
        assert len(diff) == 1
        tag, i1, i2, j1, j2 = diff[0]
        assert tag == "insert" and i1 == i2
        assert noise_q.prompt[j1:j2].isspace()
        assert noise_q.prompt[:j1] + noise_q.prompt[j2:] == intens_q.prompt


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
    tokenizer: StubTokenizer | TiktokenTokenizer,
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
    tokenizer: StubTokenizer | TiktokenTokenizer,
    target: int,
) -> None:
    """Hit reachable token targets exactly."""
    prompt = token_matched_noise_prompt(_render(), CONTEXT, target, tokenizer)
    assert tokenizer.count(prompt) == target


def test_a_target_below_the_unpadded_prompt_raises(
    tokenizer: StubTokenizer | TiktokenTokenizer,
) -> None:
    """Padding only appends, so a target the unpadded prompt already exceeds is unreachable."""
    render = _render()
    base = tokenizer.count(render(CONTEXT))
    assert base > 1
    with pytest.raises(ValueError, match="already") as over_long:
        token_matched_noise_prompt(render, CONTEXT, 1, tokenizer)
    # The message names both counts so length failures read differently
    # from search failures.
    assert str(base) in str(over_long.value)


def test_a_target_the_pad_unit_cannot_step_to_raises() -> None:
    """A unit whose token cost is not fine-grained enough exhausts the search.

    ``MergeEverythingTokenizer`` counts any whitespace run as one token, so
    every pad length yields the same count: the target is above the unpadded
    prompt, but no repetition count can reach it.
    """
    render = _render()
    tokenizer = MergeEverythingTokenizer()
    assert tokenizer.count(render(CONTEXT)) < 5_000
    with pytest.raises(ValueError, match="could not pad"):
        token_matched_noise_prompt(render, CONTEXT, 5_000, tokenizer, unit=" \t")


@pytest.mark.parametrize("n", (1, 2))
def test_tiny_configs_raise_rather_than_ship_an_unpadded_noise_arm(
    tokenizer: StubTokenizer | TiktokenTokenizer,
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
