"""
Smoke-test the pool runner end-to-end: run 3 targets × 2 conditions × k=2 with
a constant "sorry" stub LLM. Validates loop, context lookup, JSONL logging,
and resume semantics (run twice, second call skips).
"""

import json
import tempfile
from pathlib import Path

from deduction.budget import whitespace_tokenizer
from deduction.inspect import load_corpus, load_traced_lookup, BENCHMARK_DIR
from deduction.pool_runner import (
    DEFAULT_CONDITIONS,
    context_for_condition,
    pilot_pool,
    run_pool,
)
from deduction.prompt import tactics_only_prompt
from deduction.stub_llm import constant_llm


def test_context_for_condition() -> None:
    fake = {
        "intensional": "INT",
        "depth": {
            1: {"ext_nodoc": "N1", "ext_doc": "D1"},
            2: {"ext_nodoc": "N2", "ext_doc": "D2"},
        },
    }
    assert context_for_condition(fake, "intensional") == "INT"
    assert context_for_condition(fake, "ext-nodoc-d1") == "N1"
    assert context_for_condition(fake, "ext-doc-d2") == "D2"
    try:
        context_for_condition(fake, "nonsense")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on unknown condition")
    print("context_for_condition ok")


def test_default_conditions_cover_9() -> None:
    assert len(DEFAULT_CONDITIONS) == 9
    assert DEFAULT_CONDITIONS[0] == "intensional"
    print(f"DEFAULT_CONDITIONS: {len(DEFAULT_CONDITIONS)} entries")


def test_smoke_run() -> None:
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    targets = pilot_pool(corpus, traced_lookup, max_n=3)
    assert len(targets) == 3, f"expected 3 replay-passing targets, got {len(targets)}"
    conditions = ["intensional", "ext-nodoc-d2"]
    k = 2

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "pool.jsonl"
        run_pool(
            targets=targets,
            conditions=conditions,
            llm_fn=constant_llm("sorry"),
            prompt_template=tactics_only_prompt,
            log_path=log_path,
            k=k,
            temperature=0.0,
            model_name="stub-sorry",
            corpus=corpus,
            traced_lookup=traced_lookup,
        )
        records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]

        expected = len(targets) * len(conditions) * k
        assert len(records) == expected, f"expected {expected} records, got {len(records)}"
        assert all(not r["ok"] for r in records), "'sorry' should always fail"

        # Resume: call again, expect all (target, condition) pairs to be skipped.
        size_before = log_path.stat().st_size
        run_pool(
            targets=targets,
            conditions=conditions,
            llm_fn=constant_llm("sorry"),
            prompt_template=tactics_only_prompt,
            log_path=log_path,
            k=k,
            temperature=0.0,
            model_name="stub-sorry",
            corpus=corpus,
            traced_lookup=traced_lookup,
        )
        size_after = log_path.stat().st_size
        assert size_after == size_before, "resume should not append new records"

        print(f"smoke run ok — {expected} records logged and resumed cleanly")


import time


def test_parallel_smoke_run() -> None:
    """Run 3 × 2 × k=2 with max_workers=4; verify same record count as serial."""
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    targets = pilot_pool(corpus, traced_lookup, max_n=3)
    conditions = ["intensional", "ext-nodoc-d2"]
    k = 2

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "pool_parallel.jsonl"
        t0 = time.perf_counter()
        run_pool(
            targets=targets,
            conditions=conditions,
            llm_fn=constant_llm("sorry"),
            prompt_template=tactics_only_prompt,
            log_path=log_path,
            k=k,
            temperature=0.0,
            model_name="stub-sorry-parallel",
            corpus=corpus,
            traced_lookup=traced_lookup,
            max_workers=4,
        )
        elapsed = time.perf_counter() - t0
        records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
        expected = len(targets) * len(conditions) * k
        assert len(records) == expected, f"expected {expected} records, got {len(records)}"
        assert all(not r["ok"] for r in records)
        print(f"parallel smoke ok — {expected} records in {elapsed:.1f}s "
              f"(vs ~serial ~{expected * 7}s est)")


def test_budget_drops_over_budget() -> None:
    """Tight whitespace-token budget: intensional (small) runs, ext-doc-d4 (large) drops."""
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    targets = pilot_pool(corpus, traced_lookup, max_n=1)
    # Whitespace-token budget tight enough that extensional-doc-d4 fails but intensional fits.
    # Intensional on our sample is ~20-60 whitespace tokens; ext-doc-d4 is thousands.
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "pool_budget.jsonl"
        run_pool(
            targets=targets,
            conditions=["intensional", "ext-doc-d4"],
            llm_fn=constant_llm("sorry"),
            prompt_template=tactics_only_prompt,
            log_path=log_path,
            k=2,
            temperature=0.0,
            model_name="stub-sorry-budget",
            corpus=corpus,
            traced_lookup=traced_lookup,
            budget_tokens=500,  # intensional ~166 tok fits, ext-doc-d4 ~1100 tok doesn't
            tokenizer=whitespace_tokenizer,
        )
        records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
        conds_logged = {r["condition"] for r in records}
        assert "intensional" in conds_logged, "intensional should fit in budget"
        assert "ext-doc-d4" not in conds_logged, "ext-doc-d4 should be dropped over-budget"
        print(f"budget filter ok — {len(records)} intensional records, 0 ext-doc-d4 (dropped)")


def main() -> None:
    test_context_for_condition()
    test_default_conditions_cover_9()
    test_smoke_run()
    test_parallel_smoke_run()
    test_budget_drops_over_budget()
    print("\nAll pool-runner tests passed.")


if __name__ == "__main__":
    main()
