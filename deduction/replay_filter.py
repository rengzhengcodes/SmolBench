"""
Filter pilot samples to ones whose canonical Mathlib proof replays cleanly
through LeanDojo's Dojo. Published LeanDojo replay rate is ~80-90% — the rest
fail when submitted tactic-by-tactic through Dojo (case-split reconstruction
artifacts, structured-proof edge cases, etc.). Those theorems are unreachable
by any LLM proof via our verification path, so they can't yield experimental
signal and must be excluded from the pilot pool.

Caches results incrementally to data/replay_filter.json so we don't pay the
~10s-per-theorem Dojo cost on re-runs. Each call persists after every sample,
so an interrupted run resumes cleanly.

Running this at pilot scale (~30-100 samples) takes 5-20 min serial. Can be
parallelized with multiprocessing later; for now serial is fine and keeps the
code simple.
"""

import json
from pathlib import Path
from typing import Dict, List

from deduction.inspect import (
    BENCHMARK_DIR,
    load_corpus,
    load_traced_lookup,
    pick_well_connected,
    N_SAMPLES,
)
from deduction.verifier import verify

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "replay_filter.json"


def check_one(theorem: dict) -> dict:
    """Run the theorem's canonical tactics through Dojo, return pass/fail + metadata."""
    tactics = [t["tactic"] for t in theorem.get("traced_tactics", [])]
    result = verify(theorem["file_path"], theorem["full_name"], tactics)
    return {
        "ok": result.ok,
        "n_tactics": len(tactics),
        "tactics_applied": result.tactics_applied,
        "error": result.error[:300] if result.error else None,
    }


def replay_filter(
    samples: List[dict], cache_path: Path = CACHE_PATH
) -> List[dict]:
    """For each sample, record whether its ground-truth proof replays in Dojo.
    Returns list of {name, ok, n_tactics, tactics_applied, error} in input order.
    Persists after every sample to cache_path."""
    cache: Dict[str, dict] = {}
    if cache_path.exists():
        cache = json.load(cache_path.open())

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    results: List[dict] = []
    for i, thm in enumerate(samples, start=1):
        name = thm["full_name"]
        if name in cache:
            r = cache[name]
            print(f"[{i}/{len(samples)}] {name}: cached ok={r['ok']}")
        else:
            n_tac = len(thm.get("traced_tactics", []))
            print(f"[{i}/{len(samples)}] {name}: running dojo ({n_tac} tactics)...", flush=True)
            r = check_one(thm)
            cache[name] = r
            json.dump(cache, cache_path.open("w"), indent=2)
            print(f"    -> ok={r['ok']} applied={r['tactics_applied']}/{r['n_tactics']}")
        results.append({"name": name, **r})
    return results


def summarize(results: List[dict]) -> None:
    n_pass = sum(1 for r in results if r["ok"])
    n_total = len(results)
    print(f"\n=== Replay filter summary ===")
    print(f"Passed: {n_pass}/{n_total} ({100*n_pass/max(n_total,1):.0f}%)")
    print(f"\nPer-sample status:")
    for r in results:
        status = "PASS" if r["ok"] else f"FAIL @ {r['tactics_applied']}/{r['n_tactics']}"
        print(f"  {r['name'][:60]:62s} {status}")


def main() -> None:
    print("Loading corpus and traced_tactics lookup...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced_lookup = load_traced_lookup()
    test = json.load((BENCHMARK_DIR / "random" / "test.json").open())

    samples = pick_well_connected(test, corpus, traced_lookup, N_SAMPLES)
    print(f"Picked {len(samples)} well-connected samples; checking each in Dojo...\n")

    results = replay_filter(samples)
    summarize(results)


if __name__ == "__main__":
    main()
