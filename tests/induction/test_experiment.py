"""Test ``InductionExperiment`` offline: no AWS, no network."""

import contextlib
import os
import subprocess
import sys

import pytest

from smolbench.evals import Numeric
from smolbench.evals.providers import ec2
from smolbench.evals.replicates import ReplicateHarness
from smolbench.induction.experiment import InductionExperiment, repo_root


def make_quizzes(seed: int):
    """One-question-per-info-type stub quiz factory, keyed by seed."""
    return {
        "intens": (Numeric(prompt=f"i/{seed}", answer=1),),
        "extens": (Numeric(prompt=f"e/{seed}", answer=2),),
    }


@pytest.fixture
def exp():
    """A small (n_replicates=3) periodic-style experiment, no state_file."""
    return InductionExperiment(
        notebook_dir="periodic", archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes, n_replicates=3, info_types=("intens", "extens"),
    )


def test_config_and_harness_passthrough(exp):
    """Every config field reaches the harness, for both a default and a custom experiment."""
    assert exp.results_dir == repo_root() / "notebooks" / "periodic" / "results"
    assert exp.shard is None
    harness = exp.harness
    assert isinstance(harness, ReplicateHarness)
    assert harness.results_dir == exp.results_dir
    assert harness.archetype_tags == {"stub-model": "decode"}
    assert harness.make_quizzes is make_quizzes
    # 1776 = InductionExperiment.base_seed's documented default epoch.
    assert harness.seeds == exp.seeds == (1776, 1777, 1778)
    assert harness.info_types == ("intens", "extens")
    assert harness.prefix == ""
    assert harness.force_seeds is None

    custom = InductionExperiment(
        notebook_dir="divisor", archetype_tags={"m": "decode"}, make_quizzes=make_quizzes,
        n_replicates=4, base_seed=100, prefix="one_hop_", force_seeds=frozenset({100}),
    )
    assert custom.results_dir == repo_root() / "notebooks" / "divisor" / "results"
    assert custom.seeds == (100, 101, 102, 103)
    assert custom.harness.prefix == "one_hop_"
    assert custom.harness.force_seeds == frozenset({100})


def test_apply_env(monkeypatch, exp):
    """_apply_env sets the provider and either sets or pops EC2_STATE_FILE."""
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("EC2_STATE_FILE", raising=False)
    namespaced = InductionExperiment(
        notebook_dir="divisor", archetype_tags={}, make_quizzes=make_quizzes,
        state_file=".ec2_state_divisor.json",
    )
    namespaced._apply_env()
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"
    assert os.environ["EC2_STATE_FILE"] == str(repo_root() / ".ec2_state_divisor.json")

    monkeypatch.setenv("EC2_STATE_FILE", "/tmp/some_other_experiments_state.json")
    exp._apply_env()
    assert "EC2_STATE_FILE" not in os.environ


NO_KWARGS = {"extra_args": None, "max_parallel": None, "request_timeout": None}
SOME_KWARGS = {"extra_args": {"max_completion_tokens": 64}, "max_parallel": 8}


@pytest.mark.parametrize("kwargs, expected",
                         [({}, NO_KWARGS), (SOME_KWARGS, {**NO_KWARGS, **SOME_KWARGS})])
def test_run_serves_then_runs_replicates_then_exits(monkeypatch, exp, kwargs, expected):
    """run() applies env, serves, forwards only what the caller passed, then exits."""
    monkeypatch.setattr(ReplicateHarness, "has_outstanding", lambda self, model: True)
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    events = []

    @contextlib.contextmanager
    def fake_serve_model(model):
        events.append(("enter", model))
        yield model
        events.append(("exit", model))

    monkeypatch.setattr(ec2, "serve_model", fake_serve_model)
    captured = {}

    def fake_run(self, model, **kw):
        events.append(("run", model))
        captured.update(kw)

    monkeypatch.setattr(ReplicateHarness, "run_replicates", fake_run)

    exp.run("stub-model", **kwargs)

    assert events == [("enter", "stub-model"), ("run", "stub-model"), ("exit", "stub-model")]
    assert isinstance(captured.pop("server_config"), dict)
    assert captured == expected
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"


def test_run_skips_serving_when_nothing_is_outstanding(monkeypatch, exp):
    """No outstanding replicate: never swap the instance's vLLM container."""
    served = []
    monkeypatch.setattr(ec2, "serve_model",
                        lambda m: served.append(m) or contextlib.nullcontext(m))
    monkeypatch.setattr(ReplicateHarness, "has_outstanding", lambda self, model: False)
    monkeypatch.setattr(ReplicateHarness, "run_replicates",
                        lambda *a, **k: pytest.fail("must not run with no work"))
    exp.run("stub-model")
    assert served == []


def test_provision_applies_env_prints_summary_and_returns_state(monkeypatch, exp, capsys):
    """provision() returns the raw state and prints the notebooks' one-line summary."""
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    fixed_state = {
        "instance_id": "i-0123456789abcdef0", "instance_type": "p5.48xlarge",
        "availability_zone": "us-east-1a", "public_ip": "203.0.113.5",
    }
    monkeypatch.setattr(ec2, "provision_spot_instance", lambda: fixed_state)

    returned = exp.provision()

    assert returned is fixed_state
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"
    assert "instance i-0123456789abcdef0 (p5.48xlarge) in us-east-1a at 203.0.113.5" \
        in capsys.readouterr().out


def test_offline_delegates(exp):
    """summarize()/cot_chain_lengths() are pure harness delegates, the latter tagged "cot"."""
    recorded = []

    class _Recorder:
        def summarize(self, model):
            recorded.append(("summarize", model))

        def cot_chain_lengths(self, tag):
            recorded.append(("cot_chain_lengths", tag))

    exp.__dict__["harness"] = _Recorder()
    exp.summarize("stub-model")
    exp.cot_chain_lengths()
    assert recorded == [("summarize", "stub-model"), ("cot_chain_lengths", "cot")]


@pytest.mark.parametrize("method, ec2_fn, returns", [
    ("agent_status", "agent_status", {"healthy": True}),
    ("teardown", "shutdown_instance", None),
])
def test_ec2_delegates(monkeypatch, exp, method, ec2_fn, returns):
    """The EC2 delegates apply the env, then forward to the ec2 module."""
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    calls = []
    monkeypatch.setattr(ec2, ec2_fn, lambda: calls.append(ec2_fn) or returns)
    assert getattr(exp, method)() == returns
    assert calls == [ec2_fn]
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"


def test_importing_experiment_does_not_import_ec2():
    """A bare import of the facade module must never pull in ``ec2``."""
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys, smolbench.induction.experiment; "
         "sys.exit(1 if 'smolbench.evals.providers.ec2' in sys.modules else 0)"],
        cwd=str(repo_root()),
    )
    assert result.returncode == 0


def _sharded(count, index, n_replicates=30):
    return InductionExperiment(
        notebook_dir="periodic", archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes, n_replicates=n_replicates, shard=(index, count),
    )


def test_shard_partition():
    """Shards partition the replicates exactly, stay balanced, and keep seed identity."""
    unsharded = InductionExperiment(
        notebook_dir="periodic", archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes).seeds
    # base_seed default 1776 + the default 30 replicates.
    assert unsharded == tuple(range(1776, 1806))
    for count in (1, 2, 3, 4, 7, 30):
        shards = [_sharded(count, i).seeds for i in range(count)]
        collected = [s for shard in shards for s in shard]
        assert sorted(collected) == sorted(unsharded), f"count={count} is not a partition"
        assert len(collected) == len(set(collected)), f"count={count} has overlap"
        sizes = [len(shard) for shard in shards]
        assert max(sizes) - min(sizes) <= 1, f"count={count} sizes {sizes}"
        assert sum(sizes) == 30
        for index, shard in enumerate(shards):
            assert all((s - 1776) % count == index for s in shard)


@pytest.mark.parametrize("bad", [(0, 0), (3, 3), (-1, 2), (2, 2), (5, 3)])
def test_invalid_shards_are_rejected(bad):
    """A malformed shard must fail at construction, not collect a wrong slice."""
    with pytest.raises(ValueError, match="shard"):
        _sharded(bad[1], bad[0])
