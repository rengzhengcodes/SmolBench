"""SHA-256 golden pins of the induction generation pipelines.

Hashes in tests/fixtures/golden_quizzes.json are recorded against
conftest.StubTokenizer (offline, byte-stable): the library generators at the
1776 seed epoch, and the family-ladder study's own four-arm bytes through
run_study.make_quizzes at seeds 0 and 1. Any drift in generation, prompting,
or noise padding trips these.
"""

import hashlib
import json
import string

import pytest

from conftest import StubTokenizer

from smolbench.induction.periodic import (
    CONDITIONS,
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


def assert_matches(key: str, quizzes: dict) -> None:
    got = {arm: quiz_hash(quiz) for arm, quiz in quizzes.items()}
    assert got == GOLDEN[key], f"generation drifted from golden {key}"


#: Excludes ``zero``: it needs a range-free template these minimal fixtures
#: don't carry. The production pins below cover all four via the study's own prompter.
POSITIVE_ARMS = {name: c for name, c in CONDITIONS.items() if not c.omit_range}


# The fixed, offline tokenizer the noise arm is sized against.
TOKENIZER = StubTokenizer()


@pytest.mark.parametrize("seed", (1776, 1777))
def test_periodic_golden(seed):
    """Numeric and ToF generation reproduce golden_quizzes.json at seeds
    1776/1777, the default seed epoch's (InductionExperiment.base_seed) first two."""
    # Test-local template + 1776 epoch, not the study's production config
    # (BASE_SEED=0, run_study's own template, four arms) -- that's pinned by
    # test_production_golden below. Exercises the library generators at n=9.
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    numeric = PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen)
    tof = PeriodicPrompter(PERIODIC_TOF_TMPL, tof_membership_query_gen)
    assert_matches(f"periodic_numeric_{seed}",
                   get_periodic_numeric_quiz(cfg, numeric, tokenizer=TOKENIZER,
                                             conditions=POSITIVE_ARMS))
    assert_matches(f"periodic_tof_{seed}",
                   get_periodic_quiz(cfg, tof, tokenizer=TOKENIZER,
                                     conditions=POSITIVE_ARMS))


# --- The production path: the seeds the study actually runs ---
# The pins above cover the library generators at test-local templates and the
# 1776 epoch. The study locks BASE_SEED=0, uses its own template, and adds a
# fourth arm (`zero`); those bytes are pinned here via `run_study.make_quizzes`,
# the exact call `ReplicateHarness` makes, not a re-assembled equivalent.

#: The four arms `run_study.INFO_TYPES` declares, in that order.
PRODUCTION_ARMS = ("intens", "extens", "noise_intens", "zero")

#: Any roster key: `make_quizzes` uses it only to look up the tokenizer, which
#: the fixture below stubs out, so the choice cannot affect the bytes.
PRODUCTION_MODEL = "gemma-4-e2b"


@pytest.fixture(scope="module")
def run_study():
    """Imports run_study.py under an os.environ snapshot/restore: the module
    mutates EC2_EXPERIMENT_TAG and calls load_dotenv at import time, which would
    otherwise leak into this pytest session (e.g. SMOLBENCH_RESULTS_S3)."""
    import importlib.util
    import os
    import sys

    from tests._paths import NOTEBOOKS

    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(
            "golden_run_study", NOTEBOOKS / "induction" / "run_study.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["golden_run_study"] = module
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


def production_hashes(run_study, seed: int) -> "dict[str, str]":
    """Hash all four production arms for `seed`, under the offline stub tokenizer."""
    quizzes = run_study.make_quizzes(seed, PRODUCTION_MODEL)
    assert tuple(quizzes) == PRODUCTION_ARMS, tuple(quizzes)
    return {arm: quiz_hash(quiz) for arm, quiz in quizzes.items()}


@pytest.fixture
def stub_tokenizer(run_study, monkeypatch):
    """Points `run_study.make_quizzes` at the offline, byte-stable stub tokenizer
    (only `noise_intens` consults it; the other three arms are tokenizer-independent)."""
    monkeypatch.setattr(run_study, "for_model", lambda model: TOKENIZER)


@pytest.mark.parametrize("seed", (0, 1))
def test_production_golden(run_study, stub_tokenizer, seed):
    """Hash-pins the study's own quiz bytes (seeds 0/1, all four arms) via
    `run_study.make_quizzes`, the same call `ReplicateHarness` makes."""
    assert run_study.BASE_SEED == 0
    assert run_study.INFO_TYPES == PRODUCTION_ARMS
    assert production_hashes(run_study, seed) == GOLDEN[f"production_seed_{seed}"]


def test_the_production_pins_are_seed_sensitive(run_study, stub_tokenizer):
    """The seed threads through: two pins, not one pin duplicated (a generator
    that ignored its seed argument would hash identically for both)."""
    zero, one = production_hashes(run_study, 0), production_hashes(run_study, 1)
    for arm in PRODUCTION_ARMS:
        assert zero[arm] != one[arm], arm
    # ... and distinct from the 1776-epoch library pins, which use a different
    # template as well as a different seed.
    assert set(zero.values()).isdisjoint(GOLDEN["periodic_numeric_1776"].values())


def test_the_production_pins_catch_a_one_byte_template_change(run_study,
                                                              stub_tokenizer,
                                                              monkeypatch):
    """A single byte changed in the study template moves every hash it reaches
    (including `zero`, which shares the template)."""
    baseline = production_hashes(run_study, 0)
    perturbed = string.Template(run_study.template.template.replace(
        "You are a precise integer counter.", "You are a precise integer counter!"
    ))
    assert perturbed.template != run_study.template.template
    monkeypatch.setattr(run_study, "template", perturbed)
    after = production_hashes(run_study, 0)
    for arm in PRODUCTION_ARMS:
        assert after[arm] != baseline[arm], arm


def test_production_arms_that_ignore_the_tokenizer(run_study, monkeypatch):
    """Only `noise_intens` varies with the tokenizer; the other three must not --
    the invariant that lets the offline stub stand in for a served tokenizer."""
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
