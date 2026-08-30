"""Test the replication harness (pooling, resume, forcing) against the local store."""

import dataclasses
import re
from datetime import datetime, timezone

import pytest

from smolbench.evals import Mark, Marks, Numeric, provider
from smolbench.evals.replicates import ReplicateHarness
from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress

RUN_TS = datetime(2026, 8, 10, tzinfo=timezone.utc)


def make_quizzes(seed: int, model: str):
    """Two info types of different sizes so pooled slicing is observable."""
    return {
        "intens": (Numeric(prompt=f"i1/{seed}", answer=1), Numeric(prompt=f"i2/{seed}", answer=2)),
        "extens": (Numeric(prompt=f"e1/{seed}", answer=3),),
    }


@pytest.fixture
def harness(tmp_path):
    return ReplicateHarness(
        results_dir=tmp_path, archetype_tags={"stub-model": "decode"}, make_quizzes=make_quizzes,
        seeds=(1, 2), info_types=("intens", "extens"),
    )


@pytest.fixture
def fake_evaluate(monkeypatch):
    """Answers every question correctly; records call shapes."""
    calls = []

    def _evaluate(quiz, model, seed, **kwargs):
        calls.append({"n": len(quiz), "model": model, "seed": seed, "kwargs": kwargs})
        marks = tuple(
            Mark(query=q.prompt, answer=q.answer, response=str(q.answer), score=1) for q in quiz
        )
        return Marks(model=model, marks=marks)

    monkeypatch.setattr(provider, "evaluate", _evaluate)
    return calls


def test_run_replicates_pools_and_serializes(harness, fake_evaluate, tmp_path):
    harness.run_replicates("stub-model", extra_args={"max_completion_tokens": 64})
    assert [c["n"] for c in fake_evaluate] == [3, 3]
    assert fake_evaluate[0]["kwargs"] == {"extra_args": {"max_completion_tokens": 64}}
    assert fake_evaluate[0]["seed"] == 1
    for seed in (1, 2):
        intens = Marks.load(tmp_path / "decode_intens" / f"rep_{seed}.yaml")
        extens = Marks.load(tmp_path / "decode_extens" / f"rep_{seed}.yaml")
        assert [m.query for m in intens.marks] == [f"i1/{seed}", f"i2/{seed}"]
        assert [m.query for m in extens.marks] == [f"e1/{seed}"]
        assert intens.server_config is None
    with pytest.raises(KeyError):
        harness.run_replicates("some-unconfigured-model")

    cfg = {"instance_type": "g7.12xlarge", "tp": 2}
    forced = dataclasses.replace(harness, force_seeds=frozenset(harness.seeds))
    forced.run_replicates("stub-model", server_config=cfg)
    stored = Marks.load(tmp_path / "decode_intens" / "rep_1.yaml")
    assert stored.server_config == cfg and stored.server_config is not cfg


def test_run_replicates_resume(harness, fake_evaluate, tmp_path):
    assert harness.has_outstanding("stub-model")
    harness.run_replicates("stub-model")
    fake_evaluate.clear()
    harness.run_replicates("stub-model")
    assert fake_evaluate == []
    assert not harness.has_outstanding("stub-model")
    (tmp_path / "decode_extens" / "rep_2.yaml").unlink()
    assert harness.has_outstanding("stub-model")
    harness.run_replicates("stub-model")
    assert [c["n"] for c in fake_evaluate] == [1]


def test_run_replicates_passes_model_to_quiz_factory(tmp_path, fake_evaluate):
    """The quiz factory receives (seed, model): the noise arm is token-matched per model."""
    seen: list = []

    def recording_factory(seed: int, model: str):
        seen.append((seed, model))
        return {"intens": (Numeric(prompt=f"i/{seed}/{model}", answer=1),)}

    ReplicateHarness(
        results_dir=tmp_path, archetype_tags={"stub-model": "decode"},
        make_quizzes=recording_factory, seeds=(1, 2), info_types=("intens",),
    ).run_replicates("stub-model")
    assert seen == [(1, "stub-model"), (2, "stub-model")]
    assert Marks.load(tmp_path / "decode_intens" / "rep_1.yaml").marks[0].query == "i/1/stub-model"


def test_force_seeds(harness, fake_evaluate):
    """force_seeds bypasses the resume-skip for exactly the forced seeds."""
    harness.run_replicates("stub-model")
    assert not harness.has_outstanding("stub-model")
    n_first = len(fake_evaluate)
    forced = dataclasses.replace(harness, force_seeds=frozenset(harness.seeds))
    assert forced.has_outstanding("stub-model")
    forced.run_replicates("stub-model")
    assert len(fake_evaluate) == 2 * n_first
    assert not harness.has_outstanding("stub-model")
    one = dataclasses.replace(harness, force_seeds=frozenset({harness.seeds[0]}))
    assert one.has_outstanding("stub-model")
    one.run_replicates("stub-model")
    assert len(fake_evaluate) == 2 * n_first + 1
    assert not dataclasses.replace(harness, force_seeds=frozenset({999})).has_outstanding(
        "stub-model"
    )


def test_cot_chain_lengths(harness, capsys):
    """Word-count stats pool over seeds, skipping falsy reasoning."""
    for seed, texts in {1: ["a b c", None, "d e"], 2: ["", "f g h i"]}.items():
        marks = tuple(
            Mark(query=f"q{i}", answer=1, response="1", score=1, reasoning=r)
            for i, r in enumerate(texts)
        )
        addr = ReplicateAddress(tag="cot", info="intens", seed=seed, model=None)
        harness.store.dump_marks(Marks(model="stub-model", marks=marks), addr, RUN_TS)
    harness.cot_chain_lengths()
    out = re.sub(r"\s+", "", capsys.readouterr().out)
    assert "cot/intens:n=3min=2max=4mean=3median=3words" in out
    assert "cot/extens:noreasoningchainsfound" in out


def test_store_is_local_and_cached(harness, tmp_path, monkeypatch):
    """The store resolves once, stays local for a non-repo dir, and honours prefix."""
    assert isinstance(harness.store, LocalResultsStore)
    assert harness.store.root == tmp_path
    assert harness.store is harness.store
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://smolbench-results-414266451290")
    assert isinstance(harness.store, LocalResultsStore)
    prefixed = dataclasses.replace(harness, prefix="one_hop_")
    addr = ReplicateAddress(tag="decode", info="intens", seed=1, model="stub-model")
    prefixed.store.dump_marks(Marks(model="stub-model", marks=()), addr, RUN_TS)
    assert (tmp_path / "one_hop_decode_intens" / "rep_1.yaml").is_file()
