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
from smolbench.evals.replicates import ReplicateHarness
from smolbench.evals.results_store import experiment_name
from smolbench.induction.experiment import InductionExperiment

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


def import_run_study(name: str, env: "dict[str, str] | None" = None):
    """Import the driver by path under `name`, with `env` applied, restoring os.environ.

    The tag/state-file block at the top of ``run_study.py`` runs at IMPORT
    time and MUTATES ``os.environ`` (it must, to precede ``ec2``'s
    import-time constant freeze), so its behaviour can only be observed by
    re-importing under a controlled environment. Returns
    ``(module_or_None, exc_or_None, env_after)``: `env_after` is the snapshot
    of ``os.environ`` taken BEFORE restoration, which is where the tag the
    module set is visible.
    """
    saved = dict(os.environ)
    module = exc = None
    try:
        os.environ.update(env or {})
        spec = importlib.util.spec_from_file_location(name, RUN_STUDY_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException as err:      # SystemExit is a BaseException
            module, exc = None, err
        env_after = dict(os.environ)
    finally:
        os.environ.clear()
        os.environ.update(saved)
        sys.modules.pop(name, None)
    return module, exc, env_after


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
    """The prompt template must stay byte-identical to periodic_moe's, so that
    only (model, quiz generator, harmonic set) vary between the two studies."""
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
    # 131_072 = the vLLM serving context. BUDGET_CAP is GONE (12-23): it was
    # defined as == CONTEXT_LIMIT, so the min() against it could never bind.
    assert not hasattr(run_study, "BUDGET_CAP")
    assert run_study.CONTEXT_LIMIT == 131_072
    assert experiment_name(run_study.EXPERIMENT.results_dir) == "induction"
    assert run_study.EXPERIMENT.results_dir == NOTEBOOKS / "induction" / "results"


BUDGET_MODEL = "gemma-4-e2b"


def test_completion_budget(run_study, monkeypatch):
    """Quizzes cover the four arms, and budget == context - worst prompt - reserve."""
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    seeds = range(0, 2)
    quizzes = {seed: run_study.make_quizzes(seed, BUDGET_MODEL) for seed in seeds}
    assert tuple(quizzes[0]) == run_study.INFO_TYPES
    # 9 questions per arm: one per label of the n=9 production config.
    assert {info: len(q) for info, q in quizzes[0].items()} == dict.fromkeys(run_study.INFO_TYPES, 9)

    tok = StubTokenizer()
    worst = max(
        tok.count(qna.prompt)
        for by_arm in quizzes.values()
        for quiz in by_arm.values()
        for qna in quiz
    )
    # Both constants' derivations live at their run_study definitions.
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


# ---------------------------------------------------------------------------
# 12-23: CONTEXT_LIMIT is derived from the roster, not restated
# ---------------------------------------------------------------------------

def test_context_limit_is_derived_from_the_deploy_specs(run_study):
    """CONTEXT_LIMIT equals ec2's own max_model_len for EVERY roster entry.

    It used to be a hand-written 131_072 restating all 21 EC2_DEPLOY_SPECS
    entries: a spec edit on one checkpoint would leave the study deriving
    completion budgets against a context that checkpoint is not served with.
    Deriving it means the two can no longer disagree silently.
    """
    from smolbench.evals.providers.ec2 import get_model_context_length

    served = {get_model_context_length(key) for key in run_study.MODELS}
    assert served == {run_study.CONTEXT_LIMIT}


def test_a_non_uniform_roster_context_raises(run_study, monkeypatch):
    """The uniformity check RAISES; it is not an assert and not a silent max().

    A scaling study cannot let context vary with the vendor's own YaRN
    generosity -- a family's ceiling would be confounded with its context
    budget. Feeding one short entry must abort, naming the offender.
    """
    with pytest.raises((RuntimeError, SystemExit)) as err:
        run_study.derive_context_limit({"a": 131_072, "b": 32_768})
    assert "32" in str(err.value) or "32768" in str(err.value)
    # ... and the uniform case returns the shared value rather than raising.
    assert run_study.derive_context_limit({"a": 131_072, "b": 131_072}) == 131_072


# ---------------------------------------------------------------------------
# 12-23: the probe-seed picks, simplified but provably unchanged
# ---------------------------------------------------------------------------

def _legacy_picks(seeds, probe_seeds):
    """The pre-simplification `picks` expression, vendored verbatim from HEAD.

    Kept in the test rather than the driver so the simplification is proved
    against the ORIGINAL text, not against a paraphrase of it.
    """
    return sorted({seeds[0], seeds[-1],
                   *(seeds[i * (len(seeds) - 1) // (probe_seeds - 1)]
                     for i in range(probe_seeds))}) if len(seeds) > 1 else list(seeds)


@pytest.mark.parametrize("length", range(1, 120))
def test_probe_seeds_matches_the_legacy_expression(run_study, length):
    """The simplified probe-seed picker is equal to the old one at every length 1..119.

    The endpoints the old expression unioned in explicitly are already
    produced by its own generator (i=0 -> seeds[0], i=PROBE_SEEDS-1 ->
    seeds[-1]), and at len==1 every index collapses to 0, so the len>1 branch
    was redundant too. This pins the equality rather than asserting it in
    prose; 119 covers well past the study's 30 replicates.
    """
    for base in (0, 7):
        seeds = range(base, base + length)
        assert run_study.probe_seeds(seeds) == _legacy_picks(seeds, run_study.PROBE_SEEDS)


# ---------------------------------------------------------------------------
# 12-06: request_timeout derived from the per-model budget
# ---------------------------------------------------------------------------

def test_request_timeout_is_derived_from_the_budget_and_a_decode_floor(run_study):
    """A ~100k-token CoT budget buys far more than ec2's 600 s default.

    Finishing 100k tokens inside 600 s needs >= 167 tok/s of single-request
    decode on a 397B/236B MoE; ec2 re-times-out on every attempt, censoring
    the top of the CoT-length distribution on the arm carrying the headline
    contrast. The derivation is budget / MIN_DECODE_TOK_S, floored at the
    provider default -- a floor, never a cap.
    """
    fn = run_study.request_timeout_seconds
    floor = run_study.REQUEST_TIMEOUT_FLOOR_SECONDS
    rate = run_study.MIN_DECODE_TOK_S

    # A plausible slow decode rate, and a floor no smaller than ec2's default.
    assert 0 < rate <= 20
    assert floor >= 600

    # Production-sized budget: strictly longer than the 600 s default, and
    # long enough for the whole budget at the floor rate.
    big = fn(100_000)
    assert big >= 100_000 / rate
    assert big > 600

    # Monotone in the budget, and never below the floor for a tiny one.
    assert fn(1) == floor
    assert fn(50_000) <= fn(100_000)

    # No ceiling: a bigger budget always buys at least as much time.
    assert fn(1_000_000) > big


def test_main_passes_the_derived_request_timeout(run_study, monkeypatch):
    """main() actually hands request_timeout to EXPERIMENT.run for every model.

    The derivation is worthless if the call site keeps the default; this pins
    the wiring, not just the arithmetic.
    """
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b")
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(run_study, "completion_budget", lambda model, seeds: 96_000)
    # Patch the CLASSES, not the instances: InductionExperiment and
    # ReplicateHarness are both frozen dataclasses, so setattr on an instance
    # raises FrozenInstanceError at the patch line, before main() ever runs.
    monkeypatch.setattr(ReplicateHarness, "has_outstanding",
                        lambda self, model: True)
    monkeypatch.setattr(InductionExperiment, "provision", lambda self: {})
    monkeypatch.setattr(InductionExperiment, "summarize", lambda self, model: None)
    seen = {}
    monkeypatch.setattr(InductionExperiment, "run",
                        lambda self, model, **kw: seen.update(kw))

    run_study.main([])

    assert seen["request_timeout"] == run_study.request_timeout_seconds(96_000)
    assert seen["extra_args"]["max_completion_tokens"] == 96_000


# ---------------------------------------------------------------------------
# 12-07: nothing outstanding => never provision a spot box
# ---------------------------------------------------------------------------

def test_main_does_not_provision_when_nothing_is_outstanding(run_study, monkeypatch,
                                                             caplog):
    """A lane re-run after completion must not boot a billing box to do nothing.

    ``run()`` already skipped the serve, but ``provision()`` ran first and
    unconditionally, and ``main()`` never tears down -- so the box stayed up.
    """
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b")
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(run_study, "completion_budget", lambda model, seeds: 96_000)
    # Class-level, for the frozen-dataclass reason given above.
    monkeypatch.setattr(ReplicateHarness, "has_outstanding",
                        lambda self, model: False)

    def explode(*a, **k):
        raise AssertionError("must not provision or run with no outstanding work")

    monkeypatch.setattr(InductionExperiment, "provision", explode)
    monkeypatch.setattr(InductionExperiment, "run", explode)

    with caplog.at_level("INFO"):
        run_study.main([])
    assert any("outstanding" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# 12-08: every run gets an explicit, non-retired EC2 tag
# ---------------------------------------------------------------------------

def test_unsharded_runs_set_the_study_tag():
    """An UNSHARDED, standalone run no longer inherits ec2's retired default.

    ``EC2_EXPERIMENT_TAG`` used to be set only inside the ``INDUCTION_SHARD``
    branch, so the documented standalone invocation kept ec2.py's
    "periodic-induction" -- a RETIRED study's tag. Tag-based recovery would
    then reattach to any live box carrying it and ``serve_model`` would swap
    that box's model out from under the other driver; ``--teardown`` would
    terminate it.
    """
    module, exc, env = import_run_study("induction_run_study_untagged",
                                        {"INDUCTION_SHARD": "", "INDUCTION_MODELS": ""})
    assert exc is None, exc
    assert env["EC2_EXPERIMENT_TAG"] == "induction-scaling"


def test_the_retired_default_tag_is_refused():
    """Resolving to ec2's retired "periodic-induction" default aborts the run."""
    _module, exc, _env = import_run_study(
        "induction_run_study_retired",
        {"EC2_EXPERIMENT_TAG": "periodic-induction", "INDUCTION_SHARD": "",
         "INDUCTION_MODELS": ""},
    )
    assert isinstance(exc, SystemExit), exc
    assert "periodic-induction" in str(exc)


def test_the_shard_lane_tag_is_canonical_order_independent():
    """Reordering INDUCTION_MODELS must not mint a second tag and state file.

    ``_LANE`` was built from the RAW ``INDUCTION_MODELS`` string while
    ``selected_models()`` canonicalizes to MODELS declaration order, so two
    spellings of one lane produced two tags -- and so two boxes and two state
    files -- for the same work.
    """
    forward, err_f, env_f = import_run_study(
        "induction_run_study_lane_a",
        {"INDUCTION_SHARD": "0/2", "INDUCTION_MODELS": "qwen3.5-27b,gemma-4-e2b"},
    )
    reverse, err_r, env_r = import_run_study(
        "induction_run_study_lane_b",
        {"INDUCTION_SHARD": "0/2", "INDUCTION_MODELS": "gemma-4-e2b,qwen3.5-27b"},
    )
    assert err_f is None and err_r is None, (err_f, err_r)
    assert env_f["EC2_EXPERIMENT_TAG"] == env_r["EC2_EXPERIMENT_TAG"]
    assert env_f["EC2_EXPERIMENT_TAG"].startswith("induction-scaling-")
    assert env_f["EC2_EXPERIMENT_TAG"].endswith("-s0of2")
    assert forward.EXPERIMENT.state_file == reverse.EXPERIMENT.state_file
