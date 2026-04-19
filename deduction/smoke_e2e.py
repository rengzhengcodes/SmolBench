"""
End-to-end plumbing test: pick one well-connected sample, build its contexts,
run the harness with a stub LLM at two settings (ground-truth and constant
"sorry"), and confirm pass/fail behaves as expected.

Exists to validate the full pipeline (context generation → prompt → LLM call
→ verify → TrialResult) before we swap the stub for a real LLM on EC2.
"""

import json
from pathlib import Path

from deduction.harness import run_trial
from deduction.inspect import (
    BENCHMARK_DIR,
    build_all_depths,
    load_corpus,
    load_traced_lookup,
    pick_well_connected,
    split_signature,
)
from deduction.prompt import tactics_only_prompt
from deduction.stub_llm import constant_llm, ground_truth_llm


def main() -> None:
    print("Loading corpus + traced lookup ...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    test = json.load((BENCHMARK_DIR / "random" / "test.json").open())

    # Prefer a target we already know replays cleanly.
    replay_cache = json.load((Path(__file__).resolve().parent.parent / "data" / "replay_filter.json").open())
    passing_names = {name for name, r in replay_cache.items() if r["ok"]}

    candidates = pick_well_connected(test, corpus, traced_lookup, n=50)
    target = next(t for t in candidates if t["full_name"] in passing_names)

    print(f"Target: {target['full_name']}")
    contexts = build_all_depths(target, corpus, traced_lookup, max_depth=2)
    intens_text = contexts["intensional"]
    ext_d1_text = contexts["depth"][1]["ext_nodoc"]
    target_sig = split_signature(corpus[target["full_name"]].corpus_code)

    # --- Case 1: ground-truth stub on intensional condition. Should pass. ---
    gt = ground_truth_llm(target["traced_tactics"])
    gt_results = run_trial(
        target_id=target["full_name"],
        file_path=target["file_path"],
        target_sig=target_sig,
        context_text=intens_text,
        condition="intensional",
        prompt_template=tactics_only_prompt,
        llm_fn=gt,
        k=2,
        temperature=0.0,
        model_name="stub-ground-truth",
    )
    print("\n=== ground-truth stub, intensional, k=2 ===")
    for r in gt_results:
        print(f"  k={r.k_index}  ok={r.ok}  tactics_applied={r.tactics_applied}  wall_ms={r.wall_ms}")
    assert all(r.ok for r in gt_results), "ground truth should always pass"

    # --- Case 2: constant "sorry" on ext-nodoc-d1. Should fail. ---
    srry = constant_llm("sorry")
    srry_results = run_trial(
        target_id=target["full_name"],
        file_path=target["file_path"],
        target_sig=target_sig,
        context_text=ext_d1_text,
        condition="ext-nodoc-d1",
        prompt_template=tactics_only_prompt,
        llm_fn=srry,
        k=2,
        temperature=0.0,
        model_name="stub-sorry",
    )
    print("\n=== 'sorry' stub, ext-nodoc-d1, k=2 ===")
    for r in srry_results:
        err = (r.error or "")[:60]
        print(f"  k={r.k_index}  ok={r.ok}  err={err!r}  wall_ms={r.wall_ms}")
    assert all(not r.ok for r in srry_results), "'sorry' should always fail"

    # --- Dump one result as JSON to confirm schema ---
    print("\n=== sample TrialResult JSON ===")
    print(json.dumps(gt_results[0].to_json_dict(), indent=2))


if __name__ == "__main__":
    main()
