"""SHA-256 golden pins of the induction generation pipelines.

Hashes in tests/fixtures/golden_quizzes.json are recorded at the studies'
production configs, against conftest.StubTokenizer (offline, byte-stable).
Any drift in generation, prompting, or noise padding trips these.
"""

import hashlib
import json
import string

import pytest

from conftest import StubTokenizer

from smolbench.induction.periodic import (
    PeriodicConfig,
    Prompter as PeriodicPrompter,
    get_periodic_numeric_quiz,
    get_periodic_quiz,
    numeric_count_query_gen,
    tof_membership_query_gen,
)
from tests._paths import FIXTURES

GOLDEN = json.loads((FIXTURES / "golden_quizzes.json").read_text())

# Minimal templates covering every placeholder each generator produces.
PERIODIC_TMPL = string.Template("CTX:\n$positive_info\nQ: How many of positions 1..$seq_len include '$label'?")
PERIODIC_TOF_TMPL = string.Template("CTX:\n$positive_info\nQ: Does position $pos include '$label'? True/False.")


def quiz_hash(quiz) -> str:
    h = hashlib.sha256()
    for q in quiz:
        h.update(q.prompt.encode())
        h.update(repr(q.answer).encode())
        h.update(type(q).__name__.encode())
    return h.hexdigest()


def assert_matches(key: str, quizzes) -> None:
    got = {k: quiz_hash(q) for k, q in zip(("intens", "extens", "noise_intens"), quizzes)}
    assert got == GOLDEN[key], f"generation drifted from golden {key}"


# The fixed, offline tokenizer the noise arm is sized against.
TOKENIZER = StubTokenizer()


@pytest.mark.parametrize("seed", (1776, 1777))
def test_periodic_golden(seed):
    """Hash-pin regression: numeric and ToF quiz generation must reproduce the
    SHA-256es recorded in golden_quizzes.json, so any drift in prompt text or
    answers is caught before it silently invalidates resumed or archived runs.
    Seeds 1776/1777 are the first two of the default seed epoch
    (InductionExperiment.base_seed)."""
    # The induction study's production config (notebooks/induction/run_study.py).
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    numeric = PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen)
    tof = PeriodicPrompter(PERIODIC_TOF_TMPL, tof_membership_query_gen)
    assert_matches(f"periodic_numeric_{seed}",
                   get_periodic_numeric_quiz(cfg, numeric, tokenizer=TOKENIZER))
    assert_matches(f"periodic_tof_{seed}",
                   get_periodic_quiz(cfg, tof, tokenizer=TOKENIZER))
