"""Run static contract tests for the family-ladder induction driver.

``notebooks/induction/run_study.py`` is the single source of truth for the
scaling study's configuration; the notebook imports it, instead of
re-declaring anything. So every constant in it is a study invariant, not
an implementation detail. Each check below guards a failure that would
otherwise only surface after a 21-instance spot fleet has already billed:

* The roster must stay total over ``EC2_DEPLOY_SPECS``'s 21 study keys. A
  model added to the specs but missing from ``MODELS`` silently never runs.
* Every model must carry a CoT toggle. A missing or incorrect
  ``chat_template_kwargs`` collects silently non-thinking data, which is
  worse than no data.
* The prompt template must stay byte-identical to the ``periodic_moe``
  study's, or the new results cannot be compared against the archived ones.
* ``BASE_SEED``/``n_replicates`` are user-locked at 0/30. Every prior
  study used 1776, so a copy-paste from a sibling driver would be
  invisible.
* The S3 experiment name must derive to exactly ``"induction"``, since
  that string is the top-level key component of every result object
  written.
* The completion-budget arithmetic must be derivable offline, from the
  tokenizer alone, before anything is provisioned.

Offline: every test here monkeypatches ``run_study.for_model`` to a
``StubTokenizer``. Nothing downloads a tokenizer, and nothing touches AWS.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys

import pytest

from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS
from smolbench.evals.results_store import experiment_name

from conftest import StubTokenizer
from tests._paths import NOTEBOOKS

RUN_STUDY_PATH = NOTEBOOKS / "induction" / "run_study.py"

# The smoke entry predates the study and is not a counted rung. Every
# other spec key is one of the 21 study models (the same split
# tests/evals/test_deploy_specs.py makes).
STUDY_KEYS = sorted(set(EC2_DEPLOY_SPECS) - {"qwen2.5-1.5b"})

# The study's spec-key to analysis-tag map, copied from the study
# directive. This is vendored here, not imported, so this test can fail
# when run_study's copy drifts. If it were imported instead, the check would be
# vacuous.
EXPECTED_TAGS = {
    "qwen3.5-27b": "qwen35_27b",
    "qwen3.5-122b-a10b": "qwen35_122b",
    "qwen3.5-397b-a17b": "qwen35_397b",
    "nemotron-3-nano-4b": "nemo3_4b",
    "nemotron-3-nano-30b-a3b": "nemo3_30b",
    "nemotron-3-super-120b-a12b": "nemo3_120b",
    "gemma-4-e2b": "gemma4_e2b",
    "gemma-4-12b": "gemma4_12b",
    "gemma-4-31b": "gemma4_31b",
    "glm-4.7-flash": "glm_flash",
    "glm-4.5-air": "glm_air",
    "glm-4.7": "glm_47",
    "ministral-3-3b": "min3_3b",
    "ministral-3-8b": "min3_8b",
    "ministral-3-14b": "min3_14b",
    "exaone-4.0-32b": "exaone_32b",
    "exaone-4.5-33b": "exaone_33b",
    "k-exaone-236b-a23b": "exaone_236b",
    "deepseek-v4-flash": "ds_flash",
    "deepseek-v3.1": "ds_v31",
    "deepseek-v4-pro": "ds_pro",
}

# The periodic_moe prompt template, verbatim. Provenance:
#   git show f13b60d0~1:notebooks/periodic_moe/run_pilot.py  (the `template`
#   assignment's string.Template argument)
# 518 characters, sha256
#   e4a66d32c357cac4e898a8bf66d84b6ea3717f174ad7e5a88907bb5afb7a6279
# Byte equality here is what makes the family-ladder results comparable to
# the archived all-MoE study: same task, same wording, only the roster changed.
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
    """Import ``notebooks/induction/run_study.py`` without leaking its env.

    Two hazards this fixture exists to contain:

    1. The driver calls ``load_dotenv(keys.env)`` at import time. It
       must: ``smolbench.evals.providers.ec2`` freezes its ``EC2_*`` constants at
       import. That mutates the pytest process's ``os.environ``,
       including ``SMOLBENCH_RESULTS_S3``, which would leak into every
       later test in the session. The snapshot/restore pair around the
       import undoes it. Nothing the module captured at import time is
       re-read afterwards, so restoring is safe.
    2. It loads from an explicit file path under a unique module name,
       instead of putting ``notebooks/induction`` on ``sys.path``. The
       deduction study ships its own ``run_study.py``, so a bare
       ``import run_study`` would be ambiguous the moment both
       directories are importable.
    """
    saved = dict(os.environ)
    try:
        spec = importlib.util.spec_from_file_location(
            "induction_run_study", RUN_STUDY_PATH
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["induction_run_study"] = module
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    return module


# ---------------------------------------------------------------------------
# Roster totality: MODELS / COT_ARGS vs EC2_DEPLOY_SPECS
# ---------------------------------------------------------------------------


def test_models_covers_exactly_the_study_specs(run_study):
    assert sorted(run_study.MODELS) == STUDY_KEYS


def test_models_maps_to_the_locked_analysis_tags(run_study):
    assert run_study.MODELS == EXPECTED_TAGS


def test_analysis_tags_are_unique(run_study):
    tags = list(run_study.MODELS.values())
    assert len(set(tags)) == len(tags)


def test_cot_args_is_total_over_models(run_study):
    """Every model carries an entry, including the empty Ministral ones.

    Totality is the point: a missing key would raise ``KeyError`` at
    ``EXPERIMENT.run`` time, that is, after the box is already up and
    billing.
    """
    assert sorted(run_study.COT_ARGS) == sorted(run_study.MODELS)


@pytest.mark.parametrize("key", ["ministral-3-3b", "ministral-3-8b", "ministral-3-14b"])
def test_ministral_entries_are_present_but_empty(run_study, key):
    """Ministral's think protocol rides the deploy-spec ``system_prompt``.

    A ``chat_template_kwargs`` toggle would do nothing for these three
    (their shipped template has no thinking kwarg at all), so the entry
    must be present but empty, not absent. See the spec table's Ministral
    note in ``smolbench/evals/providers/ec2.py``.
    """
    assert run_study.COT_ARGS[key] == {}
    assert EC2_DEPLOY_SPECS[key].get("system_prompt")


@pytest.mark.parametrize(
    "key",
    [
        "qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b",
        "nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b",
        "gemma-4-e2b", "gemma-4-12b", "gemma-4-31b",
        "glm-4.7-flash", "glm-4.5-air", "glm-4.7",
        "exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b",
    ],
)
def test_enable_thinking_families(run_study, key):
    """Gemma-4 and EXAONE-4.0-32B default enable_thinking to False.

    So the driver is the only thing that can turn CoT on for them. The rest are
    checked the same way, so the table stays uniform.
    """
    assert run_study.COT_ARGS[key] == {"chat_template_kwargs": {"enable_thinking": True}}


@pytest.mark.parametrize("key", ["deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro"])
def test_deepseek_uses_the_thinking_kwarg(run_study, key):
    """DeepSeek's toggle is named ``thinking``, not ``enable_thinking``.

    It drives both the V4 inline template branch and vLLM's deepseek_v4
    parser.
    """
    assert run_study.COT_ARGS[key] == {"chat_template_kwargs": {"thinking": True}}


# ---------------------------------------------------------------------------
# Experiment-defining constants
# ---------------------------------------------------------------------------


def test_template_is_byte_identical_to_periodic_moe(run_study):
    assert run_study.template.template == PERIODIC_MOE_TEMPLATE
    assert (
        hashlib.sha256(run_study.template.template.encode()).hexdigest()
        == "e4a66d32c357cac4e898a8bf66d84b6ea3717f174ad7e5a88907bb5afb7a6279"
    )


def test_base_seed_is_zero(run_study):
    """User-locked at 0.

    Every prior study used 1776, so a copy-pasted driver would look
    completely normal while collecting under the wrong seeds.
    """
    assert run_study.BASE_SEED == 0


def test_thirty_replicates_seeded_zero_through_twentynine(run_study):
    assert run_study.EXPERIMENT.n_replicates == 30
    assert run_study.EXPERIMENT.base_seed == 0
    assert run_study.EXPERIMENT.seeds == tuple(range(30))


def test_info_types_are_the_four_arms(run_study):
    assert run_study.INFO_TYPES == ("intens", "extens", "noise_intens", "zero")
    assert run_study.EXPERIMENT.info_types == run_study.INFO_TYPES


def test_experiment_is_wired_to_the_models_table(run_study):
    assert run_study.EXPERIMENT.notebook_dir == "induction"
    assert run_study.EXPERIMENT.archetype_tags == run_study.MODELS


def test_s3_experiment_name_is_induction(run_study):
    """The S3 log key is ``induction/<spec-key>/seed=<s>/<info>--<ts>.yaml``.

    This pins its first component.
    """
    assert experiment_name(run_study.EXPERIMENT.results_dir) == "induction"
    assert run_study.EXPERIMENT.results_dir == NOTEBOOKS / "induction" / "results"


# ---------------------------------------------------------------------------
# Quiz factory + completion-budget arithmetic (stub tokenizer, no network)
# ---------------------------------------------------------------------------

BUDGET_MODEL = "gemma-4-e2b"


def test_make_quizzes_yields_the_four_arms(run_study, monkeypatch):
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    quizzes = run_study.make_quizzes(0, BUDGET_MODEL)
    assert tuple(quizzes) == run_study.INFO_TYPES
    # PeriodicConfig(n=9, labels=9) -> one count question per harmonic.
    assert {info: len(q) for info, q in quizzes.items()} == {info: 9 for info in run_study.INFO_TYPES}


def test_completion_budget_is_context_minus_worst_prompt_minus_reserve(
    run_study, monkeypatch
):
    """budget == 131072 - worst - 8000, over the worst prompt in any arm.

    ``seeds`` is a 2-element range, so the probe's bracketing subsample is
    unambiguously "both seeds." The expected worst is then computable here
    without restating the driver's subsampling rule.
    """
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    tok = StubTokenizer()
    seeds = range(0, 2)
    worst = max(
        tok.count(qna.prompt)
        for seed in seeds
        for quiz in run_study.make_quizzes(seed, BUDGET_MODEL).values()
        for qna in quiz
    )
    assert run_study.CONTEXT_LIMIT == 131_072
    assert run_study.TEMPLATE_RESERVE == 8_000
    assert run_study.completion_budget(BUDGET_MODEL, seeds) == 131_072 - worst - 8_000


def test_budget_cap_is_the_full_context_for_every_model(run_study):
    """No per-model caps.

    A scaling study cannot let the completion budget vary by vendor, or
    "the big one truncated" becomes unfalsifiable.
    """
    assert run_study.BUDGET_CAP == run_study.CONTEXT_LIMIT == 131_072


def test_completion_budget_exits_below_the_viability_floor(run_study, monkeypatch):
    """A prompt so long that <48k completion tokens remain must abort.

    It must abort before provisioning, not collect empties on a billing box.
    """

    class _Question:
        def __init__(self, prompt: str) -> None:
            self.prompt = prompt

    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(
        run_study,
        "make_quizzes",
        lambda seed, model: {"intens": (_Question("word " * 200_000),)},
    )
    assert run_study.MIN_VIABLE_BUDGET == 48_000
    with pytest.raises(SystemExit):
        run_study.completion_budget(BUDGET_MODEL, range(0, 1))


# ---------------------------------------------------------------------------
# Model selection (INDUCTION_MODELS filter)
# ---------------------------------------------------------------------------


def test_selected_models_defaults_to_the_whole_roster(run_study, monkeypatch):
    monkeypatch.delenv("INDUCTION_MODELS", raising=False)
    assert sorted(run_study.selected_models()) == STUDY_KEYS


def test_selected_models_filters_by_spec_key(run_study, monkeypatch):
    """The fleet supervisor sets ``INDUCTION_MODELS=<spec key>`` per lane.

    So the filter is keyed on the spec key, not the analysis tag.
    """
    monkeypatch.setenv("INDUCTION_MODELS", "glm-4.7-flash,gemma-4-e2b")
    assert set(run_study.selected_models()) == {"glm-4.7-flash", "gemma-4-e2b"}


def test_selected_models_rejects_unknown_keys(run_study, monkeypatch):
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b,not-a-model")
    with pytest.raises(SystemExit):
        run_study.selected_models()
