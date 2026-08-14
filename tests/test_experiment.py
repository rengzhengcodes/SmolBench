"""Offline tests for ``InductionExperiment`` (no AWS, no network).

Mirrors ``tests/test_replicates.py``'s style: a stub quiz factory, a fake
``provider.evaluate``-free approach here since ``InductionExperiment`` never
calls the provider directly -- it delegates to ``ReplicateHarness`` (already
covered by ``test_replicates.py``) and to ``smolbench.evals.ec2``'s public
lifecycle functions, both of which are monkeypatched rather than hit for
real. See ``smolbench/induction/experiment.py``'s module docstring for the
lazy-import contract this file's ``test_importing_experiment_does_not_import_ec2``
exists to pin down.
"""

import contextlib
import os
import subprocess
import sys

import pytest

from smolbench.evals import Mark, Marks, Numeric
from smolbench.evals import ec2
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
        notebook_dir="periodic",
        archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes,
        n_replicates=3,
        info_types=("intens", "extens"),
    )


# -- results_dir / seeds -----------------------------------------------------


def test_results_dir_is_repo_root_anchored(exp):
    assert exp.results_dir == repo_root() / "notebooks" / "periodic" / "results"


def test_results_dir_uses_notebook_dir():
    chromatic = InductionExperiment(
        notebook_dir="chromatic",
        archetype_tags={},
        make_quizzes=make_quizzes,
    )
    assert chromatic.results_dir == repo_root() / "notebooks" / "chromatic" / "results"


def test_seeds_default_matches_every_notebooks_r30_base1776():
    default_exp = InductionExperiment(
        notebook_dir="periodic",
        archetype_tags={},
        make_quizzes=make_quizzes,
    )
    assert default_exp.seeds == tuple(range(1776, 1806))


def test_seeds_respects_n_replicates_and_base_seed():
    custom = InductionExperiment(
        notebook_dir="periodic",
        archetype_tags={},
        make_quizzes=make_quizzes,
        n_replicates=4,
        base_seed=100,
    )
    assert custom.seeds == (100, 101, 102, 103)


# -- harness passthrough (functools.cached_property) -------------------------


def test_harness_receives_every_config_field(exp):
    harness = exp.harness
    assert isinstance(harness, ReplicateHarness)
    assert harness.results_dir == exp.results_dir
    assert harness.archetype_tags == {"stub-model": "decode"}
    assert harness.make_quizzes is make_quizzes
    assert harness.seeds == exp.seeds
    assert harness.info_types == ("intens", "extens")
    assert harness.prefix == ""


def test_harness_forwards_prefix():
    prefixed = InductionExperiment(
        notebook_dir="chromatic",
        archetype_tags={"m": "decode"},
        make_quizzes=make_quizzes,
        prefix="one_hop_",
    )
    assert prefixed.harness.prefix == "one_hop_"


def test_harness_is_cached_across_accesses(exp):
    # cached_property must build ReplicateHarness exactly once per instance:
    # repeated access returns the SAME object, not an equal-but-distinct one.
    first = exp.harness
    second = exp.harness
    assert first is second


# -- _apply_env ---------------------------------------------------------------


def test_apply_env_sets_inference_provider_and_state_file(monkeypatch):
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("EC2_STATE_FILE", raising=False)
    namespaced = InductionExperiment(
        notebook_dir="chromatic",
        archetype_tags={},
        make_quizzes=make_quizzes,
        state_file=".ec2_state_chromatic.json",
    )
    namespaced._apply_env()
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"
    assert os.environ["EC2_STATE_FILE"] == str(
        repo_root() / ".ec2_state_chromatic.json"
    )


def test_apply_env_pops_state_file_when_none(monkeypatch, exp):
    # Simulate a prior chromatic experiment having set EC2_STATE_FILE in the
    # same kernel/session; a state_file=None experiment (periodic) must not
    # silently inherit it -- see _apply_env's docstring for why the pop is
    # load-bearing rather than merely leaving the variable untouched.
    monkeypatch.setenv("EC2_STATE_FILE", "/tmp/some_other_experiments_state.json")
    exp._apply_env()
    assert "EC2_STATE_FILE" not in os.environ


# -- run() sequencing -----------------------------------------------------


def test_run_serves_then_runs_replicates_then_exits(monkeypatch, exp):
    # run() now skips serving when the model has no outstanding replicates
    # (serving means pulling the checkpoint, so doing it for no work is
    # billed time). This test is about the serve/forward SEQUENCING, so it
    # states the precondition explicitly rather than depending on whatever
    # happens to be in the repo's real results tree -- which is what `exp`
    # points at, and which is fully populated for this archetype.
    monkeypatch.setattr(ReplicateHarness, "has_outstanding", lambda self, model: True)
    events = []

    @contextlib.contextmanager
    def fake_serve_model(model):
        events.append(("enter", model))
        yield model
        events.append(("exit", model))

    monkeypatch.setattr(ec2, "serve_model", fake_serve_model)

    captured_kwargs = {}

    def fake_run_replicates(
        self, model, extra_args=None, max_parallel=None, request_timeout=None,
        server_config=None,
    ):
        events.append(("run_replicates", model))
        captured_kwargs.update(
            extra_args=extra_args,
            max_parallel=max_parallel,
            request_timeout=request_timeout,
            server_config=server_config,
        )

    monkeypatch.setattr(ReplicateHarness, "run_replicates", fake_run_replicates)
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)

    exp.run("stub-model", extra_args={"max_completion_tokens": 64}, max_parallel=8)

    # serve_model entered before run_replicates fired, and exited only after.
    assert events == [
        ("enter", "stub-model"),
        ("run_replicates", "stub-model"),
        ("exit", "stub-model"),
    ]
    # Only the kwargs the caller passed carry a non-None value through;
    # request_timeout (never passed here) forwards as None, which
    # ReplicateHarness.run_replicates treats identically to "omitted".
    # server_config is ALWAYS captured inside the serve block (provenance
    # is not caller-optional); with no live state file it degrades to a
    # schema-complete snapshot of Nones, never to an error.
    assert isinstance(captured_kwargs.pop("server_config"), dict)
    assert captured_kwargs == {
        "extra_args": {"max_completion_tokens": 64},
        "max_parallel": 8,
        "request_timeout": None,
    }
    # run() must have applied the env before touching ec2.
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"


def test_run_skips_serving_when_nothing_is_outstanding(monkeypatch, exp):
    """No work => do not swap the instance's vLLM container.

    Entering serve_model pulls and loads the checkpoint -- hundreds of GB for
    the large archetypes -- so doing it only to find every replicate already
    on disk is pure billed time. Hit for real on a resumed run, where the
    finished arms are re-served before the outstanding one is reached.
    """
    served = []
    monkeypatch.setattr(
        ec2, "serve_model", lambda model: served.append(model) or contextlib.nullcontext(model)
    )
    monkeypatch.setattr(ReplicateHarness, "has_outstanding", lambda self, model: False)
    monkeypatch.setattr(
        ReplicateHarness,
        "run_replicates",
        lambda *a, **k: pytest.fail("run_replicates must not run with no work"),
    )

    exp.run("stub-model")
    assert served == []


def test_run_forwards_no_kwargs_when_caller_passes_none(monkeypatch, exp):
    monkeypatch.setattr(ReplicateHarness, "has_outstanding", lambda self, model: True)
    monkeypatch.setattr(ec2, "serve_model", lambda model: contextlib.nullcontext(model))
    captured_kwargs = {}

    def fake_run_replicates(
        self, model, extra_args=None, max_parallel=None, request_timeout=None,
        server_config=None,
    ):
        captured_kwargs.update(
            extra_args=extra_args,
            max_parallel=max_parallel,
            request_timeout=request_timeout,
            server_config=server_config,
        )

    monkeypatch.setattr(ReplicateHarness, "run_replicates", fake_run_replicates)

    exp.run("stub-model")

    assert isinstance(captured_kwargs.pop("server_config"), dict)
    assert captured_kwargs == {
        "extra_args": None,
        "max_parallel": None,
        "request_timeout": None,
    }


# -- summarize() over a tmp results tree --------------------------------------


def test_summarize_prints_harness_format(exp, tmp_path, capsys):
    # Precompute the cached `harness` property against tmp_path instead of
    # the real repo results tree, by writing directly into the frozen
    # instance's __dict__ -- exactly the mechanism functools.cached_property
    # itself uses internally (see InductionExperiment.harness's docstring),
    # so this doubles as a demonstration that the trick is safe.
    exp.__dict__["harness"] = ReplicateHarness(
        results_dir=tmp_path,
        archetype_tags=exp.archetype_tags,
        make_quizzes=exp.make_quizzes,
        seeds=exp.seeds,
        info_types=exp.info_types,
        prefix=exp.prefix,
    )
    for seed in exp.seeds:
        marks = Marks(
            model="stub-model",
            marks=(Mark(query="q", answer=1, response="1", score=1),),
        )
        path = tmp_path / "decode_intens" / f"rep_{seed}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)
        # "extens" is left with no replicate files, exercising the "n/a" path.

    exp.summarize("stub-model")
    out = capsys.readouterr().out

    assert (
        "decode/intens: 3/3 replicates -- correct=3 incorrect=0 invalid=0 acc=1.000"
        in out
    )
    assert (
        "decode/extens: 0/3 replicates -- correct=0 incorrect=0 invalid=0 acc=n/a"
        in out
    )


# -- provision() ---------------------------------------------------------


def test_provision_applies_env_prints_summary_and_returns_state(
    monkeypatch, exp, capsys
):
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    fixed_state = {
        "instance_id": "i-0123456789abcdef0",
        "instance_type": "p5.48xlarge",
        "availability_zone": "us-east-1a",
        "public_ip": "203.0.113.5",
    }
    monkeypatch.setattr(ec2, "provision_spot_instance", lambda: fixed_state)

    returned = exp.provision()

    assert returned is fixed_state
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"
    out = capsys.readouterr().out
    # Locks the one-line summary format against drift -- this must keep
    # matching every notebook's cell-3 print exactly (see provision()'s
    # docstring), since it is the one facade method with real logic beyond
    # a pure ReplicateHarness/ec2 delegate.
    assert (
        "instance i-0123456789abcdef0 (p5.48xlarge) in us-east-1a at 203.0.113.5" in out
    )


# -- lazy-import pin -----------------------------------------------------------


def test_importing_experiment_does_not_import_ec2():
    """Importing the facade module alone must never pull in ``ec2`` -- see
    the module docstring's CRITICAL section. Run in a fresh subprocess so an
    ``ec2`` import anywhere else in this test session (e.g. this very test
    file's own ``from smolbench.evals import ec2``) cannot mask a real
    regression.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, smolbench.induction.experiment; "
            "sys.exit(1 if 'smolbench.evals.ec2' in sys.modules else 0)",
        ],
        cwd=str(repo_root()),
    )
    assert result.returncode == 0


# -- agent_status() / teardown() / cot_chain_lengths() delegates -------------


def test_agent_status_applies_env_and_delegates(monkeypatch, exp):
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    monkeypatch.setattr(ec2, "agent_status", lambda: {"healthy": True})
    assert exp.agent_status() == {"healthy": True}
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"


def test_teardown_applies_env_and_delegates(monkeypatch, exp):
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    calls = []
    monkeypatch.setattr(ec2, "shutdown_instance", lambda: calls.append("called"))
    exp.teardown()
    assert calls == ["called"]
    assert os.environ["INFERENCE_PROVIDER"] == "ec2"


def test_cot_chain_lengths_delegates_to_harness_with_default_tag(exp, tmp_path, capsys):
    exp.__dict__["harness"] = ReplicateHarness(
        results_dir=tmp_path,
        archetype_tags=exp.archetype_tags,
        make_quizzes=exp.make_quizzes,
        seeds=exp.seeds,
        info_types=exp.info_types,
        prefix=exp.prefix,
    )
    exp.cot_chain_lengths()
    out = capsys.readouterr().out
    assert "cot/intens: no reasoning chains found" in out
    assert "cot/extens: no reasoning chains found" in out


# ---------------------------------------------------------------------------
# Replicate sharding: N instances collecting one model's replicates in parallel
# ---------------------------------------------------------------------------


def _sharded(count, index, n_replicates=30):
    return InductionExperiment(
        notebook_dir="periodic",
        archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes,
        n_replicates=n_replicates,
        shard=(index, count),
    )


def test_shards_partition_the_replicates_exactly():
    """Across all shards every replicate appears EXACTLY once.

    This is the only correctness property sharding needs, and it is the one
    that costs money to get wrong in either direction: an overlap means two
    instances race on the same ``rep_{seed}.yaml`` and one pays GPU time for
    a result the other already has, while a gap means the study quietly
    finishes short of R and every downstream power number is computed against
    a replicate count that never existed.
    """
    unsharded = InductionExperiment(
        notebook_dir="periodic", archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes, n_replicates=30,
    ).seeds
    for count in (1, 2, 3, 4, 7, 30):
        collected = [s for i in range(count) for s in _sharded(count, i).seeds]
        assert sorted(collected) == sorted(unsharded), f"count={count} is not a partition"
        assert len(collected) == len(set(collected)), f"count={count} has overlap"


def test_shards_stay_within_one_replicate_of_each_other():
    """Striding must keep shard sizes balanced when count does not divide R.

    The point of sharding is wall-clock, which is set by the SLOWEST shard, so
    an unbalanced split gives back the speedup it was bought for. Striding
    splits 30 over 4 as 8/8/7/7; contiguous blocking would give 8/8/8/6, and
    that last shard finishes early while everyone waits on the first.
    """
    for count in (4, 7, 8, 9):
        sizes = [len(_sharded(count, i).seeds) for i in range(count)]
        assert max(sizes) - min(sizes) <= 1, f"count={count} sizes {sizes}"
        assert sum(sizes) == 30


def test_unsharded_is_unchanged():
    """shard=None must behave exactly as before the flag existed, so already
    collected studies and any un-sharded relaunch stay bit-for-bit comparable."""
    exp = InductionExperiment(
        notebook_dir="periodic", archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes, n_replicates=5, base_seed=1776,
    )
    assert exp.shard is None
    assert exp.seeds == (1776, 1777, 1778, 1779, 1780)


def test_seed_identity_is_shard_independent():
    """A seed must name the same replicate regardless of which shard runs it.

    Seeds are both the quiz generator's seed and the decoding seed, so if
    sharding renumbered them, two shards would produce different quizzes for
    the "same" replicate and the results tree would silently mix them.
    """
    assert _sharded(3, 0).seeds[0] == 1776
    assert _sharded(3, 1).seeds[0] == 1777
    assert _sharded(3, 2).seeds[0] == 1778
    for count in (2, 3, 5):
        for i in range(count):
            for s in _sharded(count, i).seeds:
                assert (s - 1776) % count == i


@pytest.mark.parametrize("bad", [(0, 0), (3, 3), (-1, 2), (2, 2), (5, 3)])
def test_invalid_shards_are_rejected(bad):
    """A malformed shard must fail at construction, not silently collect the
    wrong slice -- an out-of-range index yields an EMPTY seed list, which
    looks exactly like 'already finished' to a resume-skipping run."""
    with pytest.raises(ValueError, match="shard"):
        _sharded(bad[1], bad[0])
