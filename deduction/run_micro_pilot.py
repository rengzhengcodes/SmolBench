"""
Local micro-pilot: 5 replay-passing targets × 3 conditions × k=5 with Qwen
2.5 1.5B served by a local vLLM. Validates the full `pool_runner × real LLM
× Dojo verify × JSONL log` path before scaling to EC2.

Not a thesis measurement: a 1.5B general-purpose model isn't expected to
prove Mathlib theorems, so we're exercising plumbing, not density effects.

Requires vLLM running locally (see deduction/llm_http.py for the launch
command). Appends trials to `data/pilot_micro.jsonl` and resumes cleanly
if re-run.
"""

import json
from collections import Counter
from pathlib import Path

from deduction.inspect import (
    BENCHMARK_DIR,
    load_corpus,
    load_traced_lookup,
)
from deduction.llm_http import openai_compat_llm
from deduction.pool_runner import pilot_pool, run_pool
from deduction.prompt import tactics_only_prompt

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "data" / "pilot_micro.jsonl"

N_TARGETS = 5
CONDITIONS = ["intensional", "ext-nodoc-d2", "ext-nodoc-d4"]
K = 5
TEMPERATURE = 0.3
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
MAX_WORKERS = 4


def summarize(log_path: Path) -> None:
    """Per-(condition, target) pass/fail tally from the JSONL log."""
    if not log_path.exists():
        print("No log yet.")
        return
    records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    print(f"\n=== pilot summary: {len(records)} trials ===")
    by_cond: dict = {}
    for r in records:
        key = r["condition"]
        by_cond.setdefault(key, []).append(r)
    for cond, rs in by_cond.items():
        n_pass = sum(1 for r in rs if r["ok"])
        mean_wall = sum(r["wall_ms"] for r in rs) / max(len(rs), 1)
        mean_in = sum((r["tokens_in"] or 0) for r in rs) / max(len(rs), 1)
        mean_out = sum((r["tokens_out"] or 0) for r in rs) / max(len(rs), 1)
        print(f"  {cond:15s}: {n_pass}/{len(rs)} passed  "
              f"(mean_wall={mean_wall:.0f}ms  tokens_in~{mean_in:.0f}  tokens_out~{mean_out:.0f})")

    # Top error types
    errors = Counter()
    for r in records:
        if not r["ok"] and r["error"]:
            first_line = r["error"].split("\n")[0][:80]
            errors[first_line] += 1
    if errors:
        print("\n  Top Lean errors:")
        for err, n in errors.most_common(5):
            print(f"    [{n:2d}x] {err}")


def main() -> None:
    print("Loading corpus + traced lookup ...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()

    targets = pilot_pool(corpus, traced_lookup, max_n=N_TARGETS)
    print(f"Pool: {len(targets)} replay-passing well-connected targets")
    for t in targets:
        print(f"  - {t['full_name']}")

    llm = openai_compat_llm(model=MODEL, max_tokens=512)

    run_pool(
        targets=targets,
        conditions=CONDITIONS,
        llm_fn=llm,
        prompt_template=tactics_only_prompt,
        log_path=LOG_PATH,
        k=K,
        temperature=TEMPERATURE,
        model_name=MODEL,
        max_depth=4,
        corpus=corpus,
        traced_lookup=traced_lookup,
        max_workers=MAX_WORKERS,
    )

    summarize(LOG_PATH)


if __name__ == "__main__":
    main()
