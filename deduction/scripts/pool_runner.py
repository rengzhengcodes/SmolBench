"""Target-pool selection for kimina-based experiments.

Slim module exposing only `pilot_pool` — the well-connected + replay-passing
subset of the Mathlib test split used as the target pool for all kimina
builders (v6, v7, miniF2F).

Historical note: this file previously also contained `run_pool`, a legacy
orchestrator for the original DS-Prover / Qwen pilots. That code is
preserved in git history (see commits before the kimina cleanup) but
retired here since the kimina pipeline uses its own per-version `main()`
and hits the kimina-lean-server directly over HTTP.
"""
import json
from pathlib import Path
from typing import Dict, List

from deduction.scripts.inspect import BENCHMARK_DIR, Premise


def pilot_pool(
    corpus: Dict[str, Premise], traced_lookup: Dict[str, list], max_n: int
) -> List[dict]:
    """Replay-filter-filtered, well-connected subset of the Mathlib test split.

    Intersection of:
      - `pick_well_connected`: targets that are statement-reachable from a
        reasonable number of transitively-traced premises.
      - `replay_filter`: targets whose original Mathlib proof still replays
        cleanly against the current toolchain (excludes targets broken by
        Mathlib drift).
    """
    from .inspect import pick_well_connected

    replay_path = Path(__file__).resolve().parent.parent / "data" / "replay_filter.json"
    replay_cache = json.load(replay_path.open())
    passing = {name for name, r in replay_cache.items() if r["ok"]}

    test = json.load((BENCHMARK_DIR / "random" / "test.json").open())
    candidates = pick_well_connected(test, corpus, traced_lookup, n=max_n * 3)
    filtered = [t for t in candidates if t["full_name"] in passing]
    return filtered[:max_n]
