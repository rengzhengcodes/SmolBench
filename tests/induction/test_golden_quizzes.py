"""SHA-256 golden pins of the induction generation pipelines.

Hashes in tests/fixtures/golden_quizzes.json are recorded at the studies'
production configs, against conftest.StubTokenizer (offline, byte-stable). Two
sets: the LIBRARY generators at the 1776 seed epoch, and the family-ladder
STUDY's own four-arm bytes through run_study.make_quizzes at seeds 0 and 1.
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
    # NOT the study's production config: a test-local template and the 1776 seed
    # epoch. The family-ladder study's own bytes (BASE_SEED=0, run_study's
    # template, four arms) are pinned by test_production_golden below.
    # This config exercises the LIBRARY generators at n=9.
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    numeric = PeriodicPrompter(PERIODIC_TMPL, numeric_count_query_gen)
    tof = PeriodicPrompter(PERIODIC_TOF_TMPL, tof_membership_query_gen)
    assert_matches(f"periodic_numeric_{seed}",
                   get_periodic_numeric_quiz(cfg, numeric, tokenizer=TOKENIZER))
    assert_matches(f"periodic_tof_{seed}",
                   get_periodic_quiz(cfg, tof, tokenizer=TOKENIZER))


# ---------------------------------------------------------------------------
# 12-19: the production path, at the seeds the study actually runs
# ---------------------------------------------------------------------------
# The pins above cover the LIBRARY generators at test-local templates and the
# 1776 seed epoch (`InductionExperiment.base_seed`'s default). They do not
# cover what the family-ladder study collects: `run_study.py` locks
# `BASE_SEED = 0`, ships its OWN byte-pinned template, and adds a FOURTH arm
# (`zero`) that no hash above touches. Those are the bytes a resumed or
# archived run is compared against, so they get their own pins, generated
# through `run_study.make_quizzes` -- the exact function `ReplicateHarness`
# calls -- rather than through a re-assembled equivalent.

#: The four arms `run_study.INFO_TYPES` declares, in that order.
PRODUCTION_ARMS = ("intens", "extens", "noise_intens", "zero")

#: Any roster key: `make_quizzes` uses it only to look up the tokenizer, which
#: the fixture below stubs out, so the choice cannot affect the bytes.
PRODUCTION_MODEL = "gemma-4-e2b"


@pytest.fixture(scope="module")
def run_study():
    """Import `notebooks/induction/run_study.py` without leaking its environment.

    The driver calls `load_dotenv` and mutates `EC2_EXPERIMENT_TAG` at import
    (both deliberately, before `ec2` freezes its constants), so the import is
    wrapped in an `os.environ` snapshot/restore -- otherwise it would rewrite
    this pytest session's environment, including `SMOLBENCH_RESULTS_S3`.
    """
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
    """Point `run_study.make_quizzes` at the offline, byte-stable stub tokenizer.

    Only the `noise_intens` arm consults it (it is padded to an exact token
    count); `intens`, `extens` and `zero` are tokenizer-independent, which
    `test_production_arms_that_ignore_the_tokenizer` pins separately.
    """
    monkeypatch.setattr(run_study, "for_model", lambda model: TOKENIZER)


@pytest.mark.parametrize("seed", (0, 1))
def test_production_golden(run_study, stub_tokenizer, seed):
    """Hash-pin the STUDY's own quiz bytes: seeds 0 and 1, all four arms.

    Generated through `run_study.make_quizzes(seed, model)`, the same call
    `ReplicateHarness.run_replicates` makes, so the pin covers the production
    template, the `n=9` config, the noise padding AND the zero-information arm
    together -- not a re-assembly of them. Seeds 0 and 1 are the first two of
    `BASE_SEED = 0`'s range (0..29), which is the study's, and deliberately
    NOT the 1776 epoch the pins above use.
    """
    assert run_study.BASE_SEED == 0
    assert run_study.INFO_TYPES == PRODUCTION_ARMS
    assert production_hashes(run_study, seed) == GOLDEN[f"production_seed_{seed}"]


def test_the_production_pins_are_seed_sensitive(run_study, stub_tokenizer):
    """The seed really threads through, so these are 2 pins and not 1 twice.

    Two seeds hashing identically would mean the pin caught template drift but
    was blind to a broken seed path -- the failure mode of pinning a
    generator whose seed argument is ignored.
    """
    zero, one = production_hashes(run_study, 0), production_hashes(run_study, 1)
    for arm in PRODUCTION_ARMS:
        assert zero[arm] != one[arm], arm
    # ... and distinct from the 1776-epoch library pins, which use a different
    # template as well as a different seed.
    assert set(zero.values()).isdisjoint(GOLDEN["periodic_numeric_1776"].values())


def test_the_production_pins_catch_a_one_byte_template_change(run_study,
                                                              stub_tokenizer,
                                                              monkeypatch):
    """A single byte changed in the study template moves every affected hash.

    Proves the pins are load-bearing rather than incidentally stable. `zero`
    renders from the same template, so it moves too; only arms whose text the
    edit does not reach may stay put.
    """
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
    """Only `noise_intens` varies with the tokenizer; the other three must not.

    This is what makes three of the four pins meaningful across every one of
    the study's 21 checkpoints, and it is the invariant that lets the offline
    stub stand in for a served model's tokenizer here at all.
    """
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
