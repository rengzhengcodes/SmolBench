"""
Full end-to-end with a real (tiny) model via local vLLM. Requires the vLLM
server to be running at localhost:8000 with Qwen/Qwen2.5-1.5B-Instruct loaded
(see deduction/llm_http.py for the launch command).

Runs one replay-passing well-connected target × two conditions × k=2. We do
not assert pass rate — a 1.5B general-purpose model on Mathlib is expected to
be near-zero — we assert that the plumbing runs end-to-end and produces
TrialResults with populated proof_text.
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
from deduction.llm_http import openai_compat_llm
from deduction.prompt import tactics_only_prompt


def main() -> None:
    print("Loading corpus + traced lookup ...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    test = json.load((BENCHMARK_DIR / "random" / "test.json").open())

    replay = json.load((Path(__file__).resolve().parent.parent.parent / "data" / "replay_filter.json").open())
    passing = {name for name, r in replay.items() if r["ok"]}

    candidates = pick_well_connected(test, corpus, traced_lookup, n=50)
    target = next(t for t in candidates if t["full_name"] in passing)
    print(f"Target: {target['full_name']}")

    contexts = build_all_depths(target, corpus, traced_lookup, max_depth=2)
    target_sig = split_signature(corpus[target["full_name"]].corpus_code)

    llm = openai_compat_llm(
        model="Qwen/Qwen2.5-1.5B-Instruct",
        max_tokens=512,
    )

    for condition, ctx_text in (
        ("intensional", contexts["intensional"]),
        ("ext-nodoc-d1", contexts["depth"][1]["ext_nodoc"]),
    ):
        print(f"\n=== {condition} ({len(ctx_text)} chars) ===")
        results = run_trial(
            target_id=target["full_name"],
            file_path=target["file_path"],
            target_sig=target_sig,
            context_text=ctx_text,
            condition=condition,
            prompt_template=tactics_only_prompt,
            llm_fn=llm,
            k=2,
            temperature=0.7,
            model_name="Qwen2.5-1.5B-Instruct",
        )
        for r in results:
            print(f"  k={r.k_index}  ok={r.ok}  tokens_in={r.tokens_in}  tokens_out={r.tokens_out}  wall_ms={r.wall_ms}")
            print(f"    proof: {r.proof_text[:200]!r}")
            if not r.ok and r.error:
                print(f"    error: {r.error[:100]!r}")


if __name__ == "__main__":
    main()
