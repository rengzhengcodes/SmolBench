"""The shared replication harness: pooling, resume-skip, and summaries."""

import pytest

from smolbench.evals import Mark, Marks, Numeric, provider
from smolbench.evals.replicates import ReplicateHarness


def make_quizzes(seed: int, model: str):
    """Two info types with different sizes so pooled slicing is observable.

    Takes the model because the real quiz factories do: the induction noise
    arm is token-matched with the tokenizer of the model under test. This
    stub ignores it beyond recording that it arrives (see
    ``test_run_replicates_passes_model_to_quiz_factory``).
    """
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


def test_run_replicates_passes_model_to_quiz_factory(tmp_path, fake_evaluate):
    """The quiz factory receives (seed, model), not seed alone.

    The induction benchmarks' noise arm is padded to an exact TOKEN count
    under the tokenizer of the model being evaluated, so the factory cannot
    build a replicate without knowing which model it is for. If the harness
    ever went back to calling ``make_quizzes(seed)``, every noise prompt
    would silently be sized against whatever tokenizer the factory guessed.
    """
    seen: list = []

    def recording_factory(seed: int, model: str):
        seen.append((seed, model))
        return {"intens": (Numeric(prompt=f"i/{seed}/{model}", answer=1),)}

    ReplicateHarness(
        results_dir=tmp_path,
        archetype_tags={"stub-model": "decode"},
        make_quizzes=recording_factory,
        seeds=(1, 2),
        info_types=("intens",),
    ).run_replicates("stub-model")

    assert seen == [(1, "stub-model"), (2, "stub-model")]
    # ... and the model-dependent prompt really is what got evaluated.
    assert Marks.load(tmp_path / "decode_intens" / "rep_1.yaml").marks[0].query == (
        "i/1/stub-model"
    )


def test_run_replicates_unknown_model_raises_keyerror(harness):
    """archetype_tags is looked up with a plain ``self.archetype_tags[model]``
    subscript (see run_replicates' source) -- no ``.get()``, no try/except.
    An unconfigured model is therefore a caller bug the harness surfaces
    immediately as KeyError, rather than silently skipping the archetype or
    falling back to some placeholder tag that would corrupt the results
    layout."""
    with pytest.raises(KeyError):
        harness.run_replicates("some-unconfigured-model")


def test_cot_chain_lengths_reports_word_counts(harness, capsys):
    """cot_chain_lengths has no return value (see its source): like
    summarize(), its contract is entirely print-based, so this test drives
    it through capsys rather than inspecting a return value.

    Builds the cached CoT replicate files with Marks.dump (never
    hand-crafting the YAML format) at the paths the harness's own
    ``_rep_path("cot", info, seed)`` convention expects, with a mix of
    substantive, empty-string, and None ``Mark.reasoning`` values. The
    empty/None entries must be excluded from the word-count stats (the
    source's ``if mark.reasoning:`` guard skips falsy values) -- this
    mirrors real runs, where non-reasoning archetypes or truncated
    responses leave ``reasoning`` unset.
    """
    # seed 1 contributes word counts [3, 2] (the None entry is skipped);
    # seed 2 contributes [4] (the empty string is falsy and skipped too).
    reasoning_by_seed = {1: ["a b c", None, "d e"], 2: ["", "f g h i"]}
    for seed, texts in reasoning_by_seed.items():
        marks = Marks(
            model="stub-model",
            marks=tuple(
                Mark(query=f"q{i}", answer=1, response="1", score=1, reasoning=r)
                for i, r in enumerate(texts)
            ),
        )
        path = harness._rep_path("cot", "intens", seed)
        path.parent.mkdir(parents=True, exist_ok=True)
        marks.dump(path)
    # "extens" (the harness's other configured info type) gets no replicate
    # files at all, exercising the "no reasoning chains found" branch.

    harness.cot_chain_lengths()  # default tag="cot"
    out = capsys.readouterr().out

    # Pooled across both seeds: lengths = [3, 2, 4] -> n=3 min=2 max=4
    # mean=3 median=3. The exact spacing mirrors cot_chain_lengths' format
    # spec (n:4d, min/max:5d, mean/median:6.0f) so a format change is
    # caught here just as much as a value change.
    assert (
        "cot/intens: n=   3  min=    2  max=    4  "
        "mean=     3  median=     3  words  (~tokens x 1.3)"
    ) in out
    assert "cot/extens: no reasoning chains found" in out


def test_has_outstanding_tracks_serialized_replicates(harness, fake_evaluate):
    """Reports whether a model has work left, so callers can skip SERVING it.

    This is a spend guard, not an optimisation. ``InductionExperiment.run``
    enters ``serve_model`` before looking for work, which swaps the
    instance's vLLM container to that checkpoint -- hundreds of GB for the
    large archetypes. On a resumed run the already-finished arms get served
    first and the pull is billed to discover there is nothing to do.
    """
    assert harness.has_outstanding("stub-model")
    harness.run_replicates("stub-model")
    assert not harness.has_outstanding("stub-model")


def test_has_outstanding_is_true_when_only_one_arm_is_missing(harness, fake_evaluate, tmp_path):
    """A single missing (info, seed) is enough to require serving."""
    harness.run_replicates("stub-model")
    (tmp_path / "decode_extens" / "rep_2.yaml").unlink()
    assert harness.has_outstanding("stub-model")


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
