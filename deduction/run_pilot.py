"""
First real deduction pilot on EC2: full replay-passing pool × 9 conditions ×
k=10 with Qwen2.5-7B-Instruct served by local vLLM. Writes to
`data/pilot_qwen7b.jsonl` and mirrors the log to S3 if AWS credentials are
available.

Re-entrant: if interrupted, re-running resumes from the last logged trial.
Parallelizes Dojo across many (target × condition) pairs — tune
`MAX_WORKERS` to available vCPU × RAM headroom.
"""

import json
import os
import subprocess
from pathlib import Path

from deduction.budget import hf_tokenizer
from deduction.inspect import (
    BENCHMARK_DIR,
    load_corpus,
    load_traced_lookup,
)
from deduction.llm_http import openai_compat_llm
from deduction.pool_runner import DEFAULT_CONDITIONS, pilot_pool, run_pool
from deduction.prompt import tactics_only_prompt

ROOT = Path(__file__).resolve().parent.parent

# Configuration via env vars so a single script can iterate over models without
# code edits. Defaults are the first-pilot Qwen 7B run.
MODEL = os.environ.get("SB_MODEL", "Qwen/Qwen2.5-7B-Instruct")
LOG_NAME = os.environ.get("SB_LOG_NAME", "pilot.jsonl")
LOG_PATH = ROOT / "data" / LOG_NAME

MAX_TARGETS = int(os.environ.get("SB_MAX_TARGETS", "200"))
K = int(os.environ.get("SB_K", "10"))
TEMPERATURE = float(os.environ.get("SB_TEMPERATURE", "0.7"))
MAX_WORKERS = int(os.environ.get("SB_MAX_WORKERS", "16"))
BUDGET_TOKENS = int(os.environ.get("SB_BUDGET_TOKENS", "14000"))
MAX_TOKENS_OUT = int(os.environ.get("SB_MAX_TOKENS_OUT", "1024"))
S3_DEST = "s3://training-runs-us-east-2-414266451290/runs/dev-fisher/"


def sync_to_s3(log_path: Path) -> None:
    """Best-effort copy of the log to S3; silently skip on failure."""
    try:
        subprocess.run(
            ["aws", "s3", "cp", str(log_path), S3_DEST + log_path.name,
             "--only-show-errors"],
            check=False, timeout=60,
        )
    except Exception as e:
        print(f"(s3 sync skipped: {e})")


def summarize(log_path: Path) -> None:
    if not log_path.exists():
        print("No log.")
        return
    records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    print(f"\n=== pilot summary: {len(records)} trials ===")
    by_cond: dict = {}
    for r in records:
        by_cond.setdefault(r["condition"], []).append(r)
    print(f"  {'condition':15s}  {'pass':>10s}  {'mean_wall_ms':>14s}  {'mean_tok_in':>12s}")
    for cond in DEFAULT_CONDITIONS:
        rs = by_cond.get(cond, [])
        if not rs:
            continue
        n_pass = sum(1 for r in rs if r["ok"])
        mean_wall = sum(r["wall_ms"] for r in rs) / len(rs)
        mean_in = sum((r["tokens_in"] or 0) for r in rs) / len(rs)
        print(f"  {cond:15s}  {n_pass:4d}/{len(rs):<5d}  {mean_wall:>14.0f}  {mean_in:>12.0f}")


def main() -> None:
    print("Loading corpus + traced lookup ...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()

    targets = pilot_pool(corpus, traced_lookup, max_n=MAX_TARGETS)
    print(f"Pool: {len(targets)} replay-passing well-connected targets")

    print(f"Model: {MODEL}")
    print(f"Log path: {LOG_PATH}")
    llm = openai_compat_llm(model=MODEL, max_tokens=MAX_TOKENS_OUT)

    print(f"Loading tokenizer for {MODEL} ...")
    tokenizer = hf_tokenizer(MODEL)

    run_pool(
        targets=targets,
        conditions=DEFAULT_CONDITIONS,
        llm_fn=llm,
        prompt_template=tactics_only_prompt,
        log_path=LOG_PATH,
        k=K,
        temperature=TEMPERATURE,
        model_name=MODEL,
        max_depth=4,
        corpus=corpus,
        traced_lookup=traced_lookup,
        budget_tokens=BUDGET_TOKENS,
        tokenizer=tokenizer,
        max_workers=MAX_WORKERS,
    )

    summarize(LOG_PATH)
    print(f"\nSyncing log to {S3_DEST}{LOG_PATH.name} ...")
    sync_to_s3(LOG_PATH)


if __name__ == "__main__":
    main()
