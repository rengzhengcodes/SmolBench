"""Contracts for the family-ladder induction driver."""

from __future__ import annotations

from types import ModuleType

import pytest
from conftest import StubTokenizer, import_run_study

from smolbench.evals import study_config
from smolbench.evals.replicates import ReplicateHarness
from smolbench.evals.results_store import experiment_name
from smolbench.induction.experiment import InductionExperiment
from tests._paths import NOTEBOOKS

STUDY_KEYS = sorted(study_config.roster_keys())

MINISTRAL = ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b")
DEEPSEEK = ("deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro")

# Byte equality keeps results comparable to the archived all-MoE study.
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
def run_study() -> ModuleType:
    """Import under a unique name without leaking its environment."""
    module, exc, _env = import_run_study("induction_run_study")
    assert exc is None, exc
    assert isinstance(module, ModuleType)
    return module


def test_roster(run_study: ModuleType) -> None:
    """MODELS matches the roster's unique analysis tags."""
    assert run_study.MODELS == {
        key: study_config.tag_for(key) for key in study_config.roster_keys()
    }
    assert tuple(run_study.MODELS) == study_config.roster_keys()
    assert sorted(run_study.MODELS) == STUDY_KEYS
    assert len(set(run_study.MODELS.values())) == len(run_study.MODELS)


def test_cot_args_is_validated_against_the_config_roster(run_study: ModuleType) -> None:
    """COT_ARGS covers the roster so omissions cannot reach a billing box."""
    assert tuple(run_study.COT_ARGS) == study_config.roster_keys()


def test_the_standalone_tag_comes_from_the_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a fleet export, the experiment tag is the config's standalone tag."""
    monkeypatch.delenv("EC2_EXPERIMENT_TAG", raising=False)
    module, exc, _env = import_run_study(
        "standalone_tag_probe", {"INDUCTION_SHARD": "", "INDUCTION_MODELS": ""}
    )
    assert exc is None, exc
    assert module is not None
    assert module.EXPERIMENT.experiment_tag == (
        study_config.load_study_config().fleet.standalone_tag
    )


def test_cot_args_table(run_study: ModuleType) -> None:
    """Each model has its required CoT toggle."""

    def toggle(key: str) -> dict[str, dict[str, bool]]:
        if key in MINISTRAL:
            return {}
        name = "thinking" if key in DEEPSEEK else "enable_thinking"
        return {"chat_template_kwargs": {name: True}}

    assert run_study.COT_ARGS == {
        key: toggle(key) for key in study_config.roster_keys()
    }


def test_template_is_byte_identical_to_periodic_moe(run_study: ModuleType) -> None:
    """The template matches periodic_moe byte-for-byte."""
    assert run_study.template.template == PERIODIC_MOE_TEMPLATE


def test_experiment_constants(run_study: ModuleType) -> None:
    """Study constants remain locked."""
    assert run_study.BASE_SEED == 0
    assert run_study.EXPERIMENT.n_replicates == 30
    assert run_study.EXPERIMENT.base_seed == 0
    assert run_study.EXPERIMENT.seeds == tuple(range(30))
    assert run_study.INFO_TYPES == ("intens", "extens", "noise_intens", "zero")
    # Derive arms from the renderer's condition mapping.
    from smolbench.induction.periodic import CONDITIONS

    assert run_study.INFO_TYPES == tuple(CONDITIONS)
    assert run_study.EXPERIMENT.info_types == run_study.INFO_TYPES
    assert run_study.EXPERIMENT.notebook_dir == "induction"
    assert run_study.EXPERIMENT.archetype_tags == run_study.MODELS
    assert run_study.CONTEXT_LIMIT == 131_072
    assert experiment_name(run_study.EXPERIMENT.results_dir) == "induction"
    assert run_study.EXPERIMENT.results_dir == NOTEBOOKS / "induction" / "results"


BUDGET_MODEL = "gemma-4-e2b"


def test_completion_budget(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quizzes cover every arm and reserve completion budget."""
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    seeds = range(0, 2)
    quizzes = {seed: run_study.make_quizzes(seed, BUDGET_MODEL) for seed in seeds}
    assert tuple(quizzes[0]) == run_study.INFO_TYPES
    # One question per production label.
    assert {info: len(q) for info, q in quizzes[0].items()} == dict.fromkeys(
        run_study.INFO_TYPES, 9
    )

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


def test_completion_budget_exits_below_the_viability_floor(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Insufficient completion budget aborts before provisioning."""
    from smolbench.induction._common import RenderedQuery

    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(
        run_study,
        "rendered_queries",
        lambda seed, model: [
            RenderedQuery(
                prompts={"intens": "word " * 200_000},
                token_counts={"intens": 200_000},
                answer=1,
            )
        ],
    )
    assert run_study.MIN_VIABLE_BUDGET == 48_000
    with pytest.raises(SystemExit):
        run_study.completion_budget(BUDGET_MODEL, range(0, 1))


@pytest.mark.parametrize("length", (1, 2, 5, 6, 7, 30, 119))
def test_probe_seeds_span_the_range_sorted_and_deduplicated(
    run_study: ModuleType, length: int
) -> None:
    """Probe seeds are ordered, unique, bounded, and include both endpoints."""
    seeds = range(length)
    probes = run_study.probe_seeds(seeds)
    assert probes == sorted(set(probes))
    assert len(probes) <= run_study.PROBE_SEEDS
    assert {seeds[0], seeds[-1]} <= set(probes) <= set(seeds)


class CountingTokenizer(StubTokenizer):
    """Stub tokenizer that records count calls."""

    def __init__(self) -> None:
        self.calls = 0

    def count(self, text: str) -> int:
        self.calls += 1
        return super().count(text)


def test_completion_budget_consumes_generations_counts(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Budgeting reuses counts generated while rendering probes."""
    tokenizer = CountingTokenizer()
    monkeypatch.setattr(run_study, "for_model", lambda model: tokenizer)
    seeds = range(0, 30)
    probes = run_study.probe_seeds(seeds)

    tokenizer.calls = 0
    rendered = {seed: run_study.rendered_queries(seed, BUDGET_MODEL) for seed in probes}
    generation_calls = tokenizer.calls
    # Generation tokenizes to pad the noise arm exactly.
    assert generation_calls > 0

    tokenizer.calls = 0
    budget = run_study.completion_budget(BUDGET_MODEL, seeds)
    assert tokenizer.calls == generation_calls

    worst = max(
        count
        for queries in rendered.values()
        for query in queries
        for count in query.token_counts.values()
    )
    assert budget == run_study.CONTEXT_LIMIT - worst - run_study.TEMPLATE_RESERVE
    # The maximum covers every arm.
    assert set(rendered[probes[0]][0].token_counts) == set(run_study.INFO_TYPES)


def test_the_zero_arm_template_is_the_study_template_without_its_range_clause(
    run_study: ModuleType,
) -> None:
    """The zero arm removes the range clause from the shared template."""
    assert run_study.RANGE_CLAUSE == " 1 through $seq_len"
    assert run_study.RANGE_CLAUSE in run_study.template.template
    zero_template = run_study._zero_template(run_study.template)
    assert zero_template.template == run_study.template.template.replace(
        run_study.RANGE_CLAUSE, ""
    )
    assert "$seq_len" not in zero_template.template
    assert zero_template.template.endswith(
        "How many of the positions include '$label'?"
    )


def test_selected_models(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INDUCTION_MODELS defaults to the roster and rejects unknown keys."""
    monkeypatch.delenv("INDUCTION_MODELS", raising=False)
    assert sorted(run_study.selected_models()) == STUDY_KEYS
    monkeypatch.setenv("INDUCTION_MODELS", "glm-4.7-flash,gemma-4-e2b")
    assert set(run_study.selected_models()) == {"glm-4.7-flash", "gemma-4-e2b"}
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b,not-a-model")
    with pytest.raises(SystemExit):
        run_study.selected_models()


def test_context_limit_is_derived_from_the_deploy_specs(run_study: ModuleType) -> None:
    """CONTEXT_LIMIT matches every roster model's served context."""
    from smolbench.evals.providers.ec2 import get_model_context_length

    served = {get_model_context_length(key) for key in run_study.MODELS}
    assert served == {run_study.CONTEXT_LIMIT}


def test_a_non_uniform_roster_context_raises(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-uniform contexts raise to avoid confounded budget ceilings."""
    with pytest.raises((RuntimeError, SystemExit)) as err:
        run_study.derive_context_limit({"a": 131_072, "b": 32_768})
    assert "32" in str(err.value) or "32768" in str(err.value)
    assert run_study.derive_context_limit({"a": 131_072, "b": 131_072}) == 131_072


def test_request_timeout_is_derived_from_the_budget_and_a_decode_floor(
    run_study: ModuleType,
) -> None:
    """Timeout scales with budget to avoid censoring long CoT responses."""
    fn = run_study.request_timeout_seconds
    floor = run_study.REQUEST_TIMEOUT_FLOOR_SECONDS
    rate = run_study.MIN_DECODE_TOK_S

    # The floor cannot undercut the provider default.
    assert 0 < rate <= 20
    assert floor >= 600

    big = fn(100_000)
    assert big >= 100_000 / rate
    assert big > 600

    assert fn(1) == floor
    assert fn(50_000) <= fn(100_000)

    assert fn(1_000_000) > big


def _stub_main(
    monkeypatch: pytest.MonkeyPatch, run_study: ModuleType, outstanding: bool
) -> None:
    """Pin a one-model offline ``main``: frozen instances reject setattr."""
    monkeypatch.setenv("INDUCTION_MODELS", "gemma-4-e2b")
    monkeypatch.setattr(run_study, "for_model", lambda model: StubTokenizer())
    monkeypatch.setattr(run_study, "completion_budget", lambda model, seeds: 96_000)
    monkeypatch.setattr(
        ReplicateHarness, "has_outstanding", lambda self, model: outstanding
    )


def test_main_passes_the_derived_request_timeout(
    run_study: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main passes the derived timeout to each run."""
    _stub_main(monkeypatch, run_study, outstanding=True)
    monkeypatch.setattr(InductionExperiment, "provision", lambda self: {})
    monkeypatch.setattr(InductionExperiment, "summarize", lambda self, model: None)
    seen = {}
    monkeypatch.setattr(
        InductionExperiment, "run", lambda self, model, **kw: seen.update(kw)
    )

    run_study.main([])

    assert seen["request_timeout"] == run_study.request_timeout_seconds(96_000)
    assert seen["extra_args"]["max_completion_tokens"] == 96_000


def test_main_does_not_provision_when_nothing_is_outstanding(
    run_study: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Completed lanes must not provision billed instances."""
    _stub_main(monkeypatch, run_study, outstanding=False)
    for name in ("provision", "run"):
        monkeypatch.setattr(
            InductionExperiment,
            name,
            lambda *a, **k: pytest.fail("no outstanding work"),
        )

    with caplog.at_level("INFO"):
        run_study.main([])
    assert any("outstanding" in r.getMessage() for r in caplog.records)


def test_unsharded_runs_set_the_study_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unsharded standalone runs are tagged ``induction-scaling`` with no suffix."""
    monkeypatch.delenv("EC2_EXPERIMENT_TAG", raising=False)
    module, exc, _env = import_run_study(
        "induction_run_study_untagged", {"INDUCTION_SHARD": "", "INDUCTION_MODELS": ""}
    )
    assert exc is None, exc
    assert module is not None
    assert module.EXPERIMENT.experiment_tag == "induction-scaling"
    assert module.EXPERIMENT.state_file is None


def test_the_driver_does_not_export_the_tag_at_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tag export is the facade's, per live call; importing the driver sets nothing."""
    monkeypatch.delenv("EC2_EXPERIMENT_TAG", raising=False)
    monkeypatch.delenv("EC2_STATE_FILE", raising=False)
    _module, exc, env = import_run_study(
        "induction_run_study_no_export",
        {"INDUCTION_SHARD": "0/2", "INDUCTION_MODELS": "gemma-4-e2b"},
    )
    assert exc is None, exc
    assert "EC2_EXPERIMENT_TAG" not in env
    assert "EC2_STATE_FILE" not in env


def test_a_fleet_exported_tag_wins_over_the_standalone_tag() -> None:
    """A fleet-exported ``EC2_EXPERIMENT_TAG`` is the base tag, not the config's."""
    module, exc, _env = import_run_study(
        "induction_run_study_fleet_tag",
        {
            "EC2_EXPERIMENT_TAG": "scaling-gemma-4-e2b",
            "INDUCTION_SHARD": "",
            "INDUCTION_MODELS": "gemma-4-e2b",
        },
    )
    assert exc is None, exc
    assert module is not None
    assert module.EXPERIMENT.experiment_tag == "scaling-gemma-4-e2b"


def test_the_shard_lane_tag_is_canonical_order_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model ordering cannot create a second lane; shard ``0/2`` yields ``-s0of2``."""
    monkeypatch.delenv("EC2_EXPERIMENT_TAG", raising=False)
    forward, err_f, _env_f = import_run_study(
        "induction_run_study_lane_a",
        {"INDUCTION_SHARD": "0/2", "INDUCTION_MODELS": "qwen3.5-27b,gemma-4-e2b"},
    )
    reverse, err_r, _env_r = import_run_study(
        "induction_run_study_lane_b",
        {"INDUCTION_SHARD": "0/2", "INDUCTION_MODELS": "gemma-4-e2b,qwen3.5-27b"},
    )
    assert err_f is None and err_r is None, (err_f, err_r)
    assert forward is not None and reverse is not None
    assert forward.EXPERIMENT.experiment_tag == reverse.EXPERIMENT.experiment_tag
    assert forward.EXPERIMENT.experiment_tag == (
        "induction-scaling-qwen3.5-27b-gemma-4-e2b-s0of2"
    )
    assert forward.EXPERIMENT.state_file == reverse.EXPERIMENT.state_file


def test_a_bare_fleet_prefix_is_rejected_even_with_a_lane() -> None:
    """``EC2_EXPERIMENT_TAG=scaling-`` exits even though the lane suffix makes it non-empty."""
    module, exc, _env = import_run_study(
        "induction_run_study_bare_prefix",
        {
            "EC2_EXPERIMENT_TAG": "scaling-",
            "INDUCTION_SHARD": "0/2",
            "INDUCTION_MODELS": "gemma-4-e2b",
        },
    )
    assert module is None
    assert isinstance(exc, SystemExit)
    assert "bare fleet prefix" in str(exc)


def test_bad_shard_bounds_exit_cleanly() -> None:
    """The facade's shard-bounds ``ValueError`` surfaces as a ``SystemExit``."""
    module, exc, _env = import_run_study(
        "induction_run_study_bad_shard",
        {"INDUCTION_SHARD": "2/2", "INDUCTION_MODELS": ""},
    )
    assert module is None
    assert isinstance(exc, SystemExit)
    assert "shard" in str(exc)
