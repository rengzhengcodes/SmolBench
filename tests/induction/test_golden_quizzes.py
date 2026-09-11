"""SHA-256 pins for induction generation.

Offline stub-tokenizer hashes catch generation, prompt, and padding drift.
"""

import hashlib
import json
import string
from types import ModuleType

import pytest
from conftest import StubTokenizer, import_run_study

from smolbench.evals import Quiz
from smolbench.induction._common import Prompter as PeriodicPrompter
from smolbench.induction.periodic import (
    CONDITIONS,
    PeriodicConfig,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)
from tests._paths import FIXTURES

GOLDEN = json.loads((FIXTURES / "golden_quizzes.json").read_text())

# Covers every generator placeholder.
PERIODIC_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?"
)
PERIODIC_TOF_TMPL = string.Template(
    "CTX:\n$positive_info\nQ: Does position $pos include '$label'? True/False."
)


def quiz_hash(quiz: Quiz) -> str:
    """Hash quiz prompts, answers, and concrete types."""
    h = hashlib.sha256()
    for q in quiz:
        h.update(q.prompt.encode())
        h.update(repr(q.answer).encode())
        h.update(type(q).__name__.encode())
    return h.hexdigest()


def assert_matches(key: str, quizzes: dict) -> None:
    """Assert generated quizzes match the pinned golden hash."""
    got = {arm: quiz_hash(quiz) for arm, quiz in quizzes.items()}
    assert got == GOLDEN[key], f"generation drifted from golden {key}"


#: Excludes ``zero``; production pins cover it with a range-free template.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}


# Offline tokenizer used to size the noise arm.
TOKENIZER = StubTokenizer()


@pytest.mark.parametrize("seed", (1776, 1777))
def test_periodic_golden(seed: int) -> None:
    """Pin library numeric and ToF generation at seeds 1776 and 1777."""
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    numeric = PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen)
    tof = PeriodicPrompter(PERIODIC_TOF_TMPL, tof_membership_query_gen)
    assert_matches(
        f"periodic_numeric_{seed}",
        get_periodic_numeric_quiz(
            cfg, numeric, tokenizer=TOKENIZER, conditions=POSITIVE_ARMS
        ),
    )
    assert_matches(
        f"periodic_tof_{seed}",
        get_periodic_quiz(cfg, tof, tokenizer=TOKENIZER, conditions=POSITIVE_ARMS),
    )


#: Production arm order.
PRODUCTION_ARMS = ("intens", "extens", "noise_intens", "zero")

#: Any roster key works because the tokenizer is stubbed.
PRODUCTION_MODEL = "gemma-4-e2b"


@pytest.fixture(scope="module")
def run_study() -> ModuleType:
    """Import ``run_study`` without leaking its import-time environment changes."""
    module, exc, _env = import_run_study("golden_run_study")
    assert exc is None, exc
    assert isinstance(module, ModuleType)
    return module


def production_hashes(run_study: ModuleType, seed: int) -> "dict[str, str]":
    """Hash all four production arms for `seed`, under the offline stub tokenizer."""
    quizzes = run_study.make_quizzes(seed, PRODUCTION_MODEL)
    assert tuple(quizzes) == PRODUCTION_ARMS, tuple(quizzes)
    return {arm: quiz_hash(quiz) for arm, quiz in quizzes.items()}


@pytest.fixture
def stub_tokenizer(run_study: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the byte-stable tokenizer; only ``noise_intens`` consults it."""
    monkeypatch.setattr(run_study, "for_model", lambda model: TOKENIZER)


@pytest.mark.parametrize("seed", (0, 1))
def test_production_golden(
    run_study: ModuleType, stub_tokenizer: None, seed: int
) -> None:
    """Pin production quiz bytes for both seeds and all arms."""
    assert run_study.BASE_SEED == 0
    assert run_study.INFO_TYPES == PRODUCTION_ARMS
    assert production_hashes(run_study, seed) == GOLDEN[f"production_seed_{seed}"]


def test_the_production_pins_are_seed_sensitive(
    run_study: ModuleType, stub_tokenizer: None
) -> None:
    """Distinct seeds must produce distinct pins."""
    zero, one = production_hashes(run_study, 0), production_hashes(run_study, 1)
    for arm in PRODUCTION_ARMS:
        assert zero[arm] != one[arm], arm
    # Production uses a distinct template and seed.
    assert set(zero.values()).isdisjoint(GOLDEN["periodic_numeric_1776"].values())


def test_production_arms_that_ignore_the_tokenizer(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only ``noise_intens`` may vary with tokenizer choice."""
    from smolbench.evals.tokenization import TiktokenTokenizer

    try:
        other = TiktokenTokenizer("cl100k_base")
    except Exception as exc:  # noqa: BLE001 -- ImportError, network, cache miss
        pytest.skip(f"tiktoken cl100k_base unavailable offline: {exc}")

    monkeypatch.setattr(run_study, "for_model", lambda model: TOKENIZER)
    stub = production_hashes(run_study, 0)
    monkeypatch.setattr(run_study, "for_model", lambda model: other)
    real = production_hashes(run_study, 0)

    assert stub["noise_intens"] != real["noise_intens"]
    for arm in ("intens", "extens", "zero"):
        assert stub[arm] == real[arm], arm
