"""The shared replication harness: pooling, resume-skip, and summaries."""

import pytest

from smolbench.evals import Mark, Marks, Numeric, provider
from smolbench.evals.replicates import ReplicateHarness


def make_quizzes(seed: int):
    """Two info types with different sizes so pooled slicing is observable."""
    return {
        "intens": (Numeric(prompt=f"i1/{seed}", answer=1), Numeric(prompt=f"i2/{seed}", answer=2)),
        "extens": (Numeric(prompt=f"e1/{seed}", answer=3),),
    }


@pytest.fixture
def harness(tmp_path):
    return ReplicateHarness(
        results_dir=tmp_path,
        archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes,
        seeds=(1, 2),
        info_types=("intens", "extens"),
    )


@pytest.fixture
def fake_evaluate(monkeypatch):
    """Answers every question correctly; records call shapes."""
    calls = []

    def _evaluate(quiz, model, seed, **kwargs):
        calls.append({"n": len(quiz), "model": model, "seed": seed, "kwargs": kwargs})
        return Marks(
            model=model,
            marks=tuple(
                Mark(query=q.prompt, answer=q.answer, response=str(q.answer), score=1)
                for q in quiz
            ),
        )

    monkeypatch.setattr(provider, "evaluate", _evaluate)
    return calls


def test_run_replicates_pools_and_serializes(harness, fake_evaluate, tmp_path):
    harness.run_replicates("stub-model", extra_args={"max_completion_tokens": 64})
    # One POOLED evaluate per seed (2 intens + 1 extens = 3 questions), and
    # only the kwargs actually passed are forwarded.
    assert [c["n"] for c in fake_evaluate] == [3, 3]
    assert fake_evaluate[0]["kwargs"] == {"extra_args": {"max_completion_tokens": 64}}
    assert fake_evaluate[0]["seed"] == 1
    # Sliced back per info type and serialized to the resumable layout.
    for seed in (1, 2):
        intens = Marks.load(tmp_path / "decode_intens" / f"rep_{seed}.yaml")
        extens = Marks.load(tmp_path / "decode_extens" / f"rep_{seed}.yaml")
        assert [m.query for m in intens.marks] == [f"i1/{seed}", f"i2/{seed}"]
        assert [m.query for m in extens.marks] == [f"e1/{seed}"]


def test_run_replicates_resumes(harness, fake_evaluate):
    harness.run_replicates("stub-model")
    fake_evaluate.clear()
    # Everything serialized -> a rerun must be a no-op (idempotent cells).
    harness.run_replicates("stub-model")
    assert fake_evaluate == []


def test_run_replicates_partial_resume(harness, fake_evaluate, tmp_path):
    harness.run_replicates("stub-model")
    fake_evaluate.clear()
    (tmp_path / "decode_extens" / "rep_2.yaml").unlink()
    harness.run_replicates("stub-model")
    # Only seed 2's missing extens (1 question) re-runs; intens is not redone.
    assert [c["n"] for c in fake_evaluate] == [1]


def test_summarize_and_prefix(harness, fake_evaluate, tmp_path, capsys):
    prefixed = ReplicateHarness(
        results_dir=tmp_path,
        archetype_tags=harness.archetype_tags,
        make_quizzes=harness.make_quizzes,
        seeds=harness.seeds,
        info_types=harness.info_types,
        prefix="one_hop_",
    )
    prefixed.run_replicates("stub-model")
    assert (tmp_path / "one_hop_decode_intens" / "rep_1.yaml").exists()
    prefixed.summarize("stub-model")
    out = capsys.readouterr().out
    assert "decode/intens: 2/2 replicates" in out
    assert "acc=1.000" in out
