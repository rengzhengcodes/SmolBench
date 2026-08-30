"""Test smolbench.deduction.lean.sft (decontamination holdout + eval prompt parity)."""

import pytest

import smolbench.deduction.lean.corpus as corpus
from smolbench.deduction.lean import context, prompt, sft
from tests._paths import LEAN_MINI as FIXTURE


@pytest.fixture
def lean_data(monkeypatch):
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    yield FIXTURE
    corpus.reset_caches()


def test_decontamination_holdout(lean_data):
    """Excluded theorems never reach the emitted set, and a full-split holdout emits nothing."""
    assert sft.eval_holdout_names([("random", "val")]) == {"Mini.theoremA", "Mini.theoremB"}

    stats: dict = {}
    examples = list(sft.iter_dataset(
        train_kind="random", train_split="val", eval_specs=[],
        extra_exclude={"Mini.theoremB"}, k_strategy="last", stats=stats,
    ))
    assert {e.full_name for e in examples} == {"Mini.theoremA"}
    assert stats["pool"] == 2 and stats["dropped"] == 1
    assert stats["theorems"] == 1 and stats["examples"] == 1

    stats = {}
    assert list(sft.iter_dataset(
        train_kind="random", train_split="val", eval_specs=[("random", "val")],
        k_strategy="all", stats=stats,
    )) == []
    assert stats["dropped"] == 2 and stats["examples"] == 0


def test_prompt_target_parity_and_k_strategy(lean_data):
    """SFT rows reproduce the eval's prompt byte-for-byte; k_strategy walks every step."""
    (ex,) = list(sft.iter_dataset(
        train_kind="random", train_split="val", eval_specs=[],
        extra_exclude={"Mini.theoremB"}, k_strategy="last",
    ))
    theorem = {t.full_name: t for t in corpus.load_split("random", "val")}["Mini.theoremA"]
    k = len(theorem.traced_tactics) - 1

    assert ex.system == prompt.SYSTEM
    assert ex.user == prompt.build_user_prompt(context.render(theorem, k, "stepk", 1))
    assert ex.k == k and ex.n_tail == 1
    assert prompt.extract_tactic_block(ex.assistant) == ex.assistant

    examples = list(sft.iter_dataset(
        train_kind="random", train_split="val", eval_specs=[],
        extra_exclude={"Mini.theoremB"}, k_strategy="all",
    ))
    assert [e.k for e in examples] == [0, 1, 2]
    assert [e.n_tail for e in examples] == [3, 2, 1]
    assert examples[0].assistant == "intro h\nsimp\nexact Mini.premiseA h (Mini.premiseB n)"
    assert examples[2].assistant == "exact Mini.premiseA h (Mini.premiseB n)"
