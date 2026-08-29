"""Static contract tests for the family-ladder induction driver.

``notebooks/induction/run_study.py`` is the single source of truth for the study's
configuration, so every constant in it is a study invariant. Offline: ``for_model``
is stubbed, nothing downloads a tokenizer and nothing touches AWS.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS
from smolbench.evals.results_store import experiment_name

from conftest import StubTokenizer
from tests._paths import NOTEBOOKS

RUN_STUDY_PATH = NOTEBOOKS / "induction" / "run_study.py"

# The smoke entry predates the study and is not a counted rung.
STUDY_KEYS = sorted(set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"})

# The spec-key -> analysis-tag map, vendored (not imported) so drift fails here.
EXPECTED_TAGS = dict(
    pair.split(":") for pair in (
        "qwen3.5-27b:qwen35_27b", "qwen3.5-122b-a10b:qwen35_122b", "qwen3.5-397b-a17b:qwen35_397b",
        "nemotron-3-nano-4b:nemo3_4b", "nemotron-3-nano-30b-a3b:nemo3_30b",
        "nemotron-3-super-120b-a12b:nemo3_120b",
        "gemma-4-e2b:gemma4_e2b", "gemma-4-12b:gemma4_12b", "gemma-4-31b:gemma4_31b",
        "glm-4.7-flash:glm_flash", "glm-4.5-air:glm_air", "glm-4.7:glm_47",
        "ministral-3-3b:min3_3b", "ministral-3-8b:min3_8b", "ministral-3-14b:min3_14b",
        "exaone-4.0-32b:exaone_32b", "exaone-4.5-33b:exaone_33b", "k-exaone-236b-a23b:exaone_236b",
        "deepseek-v4-flash:ds_flash", "deepseek-v3.1:ds_v31", "deepseek-v4-pro:ds_pro",
    )
)

MINISTRAL = ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b")
DEEPSEEK = ("deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro")

# The periodic_moe prompt template, verbatim: byte equality here is what makes the
# family-ladder results comparable to the archived all-MoE study.
PERIODIC_MOE_TEMPLATE = (
    "You are a precise integer counter.\n"
    "\n"
    "Task: answer the question below with a single integer and nothing else.\n"
    "\n"
    "Output format:\n"
    "Return exactly one integer and nothing else.\n"
    "Do not output any explanation, punctuation, quotes, or extra whitespace.\n"
    "Stop immediately after writing the integer.\n"
    "\n"
    "Context:\n"
    "There is a counting game. Positions are counted starting from 1. "
    "At each position, words are written according to the following rules:\n"
    "$positive_info\n"
    "Question:\n"
    "How many of the positions 1 through $seq_len include '$label'?"
)


@pytest.fixture(scope="module")
def run_study():
    """Import notebooks/induction/run_study.py under a unique name, without leaking its env.

    The driver calls ``load_dotenv`` at import, which would otherwise mutate the
    session's ``os.environ`` (including ``SMOLBENCH_RESULTS_S3``).
    """
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location("induction_run_study", RUN_STUDY_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules["induction_run_study"] = module
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


def test_roster(run_study):
    """MODELS is exactly the 21 study spec keys, mapped to unique locked analysis tags."""
    assert run_study.MODELS == EXPECTED_TAGS
    assert sorted(run_study.MODELS) == STUDY_KEYS
    assert len(set(run_study.MODELS.values())) == len(run_study.MODELS)


def test_cot_args_table(run_study):
    """Every model carries a CoT toggle: Ministral rides its system prompt, DeepSeek's key differs."""
    def toggle(key):
        if key in MINISTRAL:
            return {}
        name = "thinking" if key in DEEPSEEK else "enable_thinking"
        return {"chat_template_kwargs": {name: True}}

    assert run_study.COT_ARGS == {key: toggle(key) for key in EXPECTED_TAGS}


def test_template_is_byte_identical_to_periodic_moe(run_study):
    assert run_study.template.template == PERIODIC_MOE_TEMPLATE


def test_experiment_constants(run_study):
    """The user-locked seeds, arms, budget cap, and S3 experiment name."""
    assert run_study.BASE_SEED == 0
    assert run_study.EXPERIMENT.n_replicates == 30
    assert run_study.EXPERIMENT.base_seed == 0
    assert run_study.EXPERIMENT.seeds == tuple(range(30))
    assert run_study.INFO_TYPES == ("intens", "extens", "noise_intens", "zero")
    assert run_study.EXPERIMENT.info_types == run_study.INFO_TYPES
    assert run_study.EXPERIMENT.notebook_dir == "induction"
    assert run_study.EXPERIMENT.archetype_tags == run_study.MODELS
    assert run_study.BUDGET_CAP == run_study.CONTEXT_LIMIT == 131_072
    assert experiment_name(run_study.EXPERIMENT.results_dir) == "induction"
    assert run_study.EXPERIMENT.results_dir == NOTEBOOKS / "induction" / "results"


BUDGET_MODEL = "gemma-4-e2b"


def test_completion_budget(run_study, monkeypatch):
    """Quizzes cover the four arms, and budget == context - worst prompt - reserve."""
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    seeds = range(0, 2)
    quizzes = {seed: run_study.make_quizzes(seed, BUDGET_MODEL) for seed in seeds}
    assert tuple(quizzes[0]) == run_study.INFO_TYPES
    assert {info: len(q) for info, q in quizzes[0].items()} == dict.fromkeys(run_study.INFO_TYPES, 9)

    tok = StubTokenizer()
    worst = max(
        tok.count(qna.prompt)
        for by_arm in quizzes.values()
        for quiz in by_arm.values()
        for qna in quiz
    )
    assert run_study.CONTEXT_LIMIT == 131_072
    assert run_study.TEMPLATE_RESERVE == 8_000
    assert run_study.completion_budget(BUDGET_MODEL, seeds) == 131_072 - worst - 8_000


def test_completion_budget_exits_below_the_viability_floor(run_study, monkeypatch):
    """A prompt leaving <48k completion tokens must abort before provisioning."""

    class _Question:
        def __init__(self, prompt: str) -> None:
            self.prompt = prompt

    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(
        run_study, "make_quizzes",
        lambda seed, model: {"intens": (_Question("word " * 200_000),)},
    )
    assert run_study.MIN_VIABLE_BUDGET == 48_000
    with pytest.raises(SystemExit):
        run_study.completion_budget(BUDGET_MODEL, range(0, 1))


def test_selected_models(run_study, monkeypatch):
    """INDUCTION_MODELS defaults to the whole roster, filters on spec keys, rejects unknowns."""
    monkeypatch.delenv("INDUCTION_MODELS", raising=False)
    assert sorted(run_study.selected_models()) == STUDY_KEYS
    monkeypatch.setenv("INDUCTION_MODELS", "glm-4.7-flash,gemma-4-e2b")
    assert set(run_study.selected_models()) == {"glm-4.7-flash", "gemma-4-e2b"}
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b,not-a-model")
    with pytest.raises(SystemExit):
        run_study.selected_models()
