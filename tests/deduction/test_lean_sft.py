"""Test smolbench.deduction.lean.sft against the lean_mini fixture.

This file checks two load-bearing properties of the LoRA SFT builder:
the decontamination holdout (eval theorems never leak into training)
and prompt-format parity with the eval (`prompt.SYSTEM`,
`build_user_prompt`, `context.render`). The tests point
SMOLBENCH_LEAN_DATA at the committed 2-theorem fixture, the same
fixture test_lean_corpus.py uses.
"""

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


def test_eval_holdout_names_covers_whole_split(lean_data):
    assert sft.eval_holdout_names([("random", "val")]) == {
        "Mini.theoremA",
        "Mini.theoremB",
    }


def test_decontamination_drops_excluded(lean_data):
    stats: dict = {}
    examples = list(
        sft.iter_dataset(
            train_kind="random",
            train_split="val",
            eval_specs=[],  # exercise the extra_exclude path in isolation
            extra_exclude={"Mini.theoremB"},
            k_strategy="last",
            stats=stats,
        )
    )
    emitted = {e.full_name for e in examples}
    assert emitted == {"Mini.theoremA"}
    assert "Mini.theoremB" not in emitted
    assert stats["pool"] == 2 and stats["dropped"] == 1 and stats["theorems"] == 1
    assert stats["examples"] == 1


def test_holdout_and_training_are_disjoint(lean_data):
    # Train on the same split we hold out -> nothing may be emitted.
    stats: dict = {}
    examples = list(
        sft.iter_dataset(
            train_kind="random",
            train_split="val",
            eval_specs=[("random", "val")],
            k_strategy="all",
            stats=stats,
        )
    )
    assert examples == []
    assert stats["dropped"] == 2 and stats["examples"] == 0


def test_prompt_and_target_match_eval_rendering(lean_data):
    (ex,) = list(
        sft.iter_dataset(
            train_kind="random",
            train_split="val",
            eval_specs=[],
            extra_exclude={"Mini.theoremB"},
            k_strategy="last",
        )
    )
    theorem = {t.full_name: t for t in corpus.load_split("random", "val")}["Mini.theoremA"]
    k = len(theorem.traced_tactics) - 1  # k_strategy="last"

    # System / user are byte-identical to what the runner sends at eval time.
    assert ex.system == prompt.SYSTEM
    assert ex.user == prompt.build_user_prompt(context.render(theorem, k, "stepk", 1))
    assert "## Full tactic state" in ex.user
    assert ex.user.rstrip().endswith(prompt.INSTRUCTION)

    # Target is the raw ground-truth tail (the single final tactic here).
    assert ex.assistant == "exact Mini.premiseA h (Mini.premiseB n)"
    assert ex.k == k and ex.n_tail == 1
    # No code fence: SYSTEM asks for bare tactic lines, and extract_tactic_block
    # round-trips the unfenced target unchanged.
    assert prompt.extract_tactic_block(ex.assistant) == ex.assistant


def test_k_strategy_all_emits_every_step_with_full_tails(lean_data):
    examples = list(
        sft.iter_dataset(
            train_kind="random",
            train_split="val",
            eval_specs=[],
            extra_exclude={"Mini.theoremB"},
            k_strategy="all",
        )
    )
    # theoremA has 3 traced tactics -> steps k=0,1,2 with tails of len 3,2,1.
    assert [e.k for e in examples] == [0, 1, 2]
    assert [e.n_tail for e in examples] == [3, 2, 1]
    assert examples[0].assistant == (
        "intro h\nsimp\nexact Mini.premiseA h (Mini.premiseB n)"
    )
    assert examples[2].assistant == "exact Mini.premiseA h (Mini.premiseB n)"
