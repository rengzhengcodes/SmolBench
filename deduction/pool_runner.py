"""
Pool runner: iterates (targets × conditions × k) calling `run_trial`, appends
each TrialResult to a JSONL log. Target-outer loop so `build_all_depths` is
called once per target and reused across conditions.

Resume semantics: on start, read the existing log and count records per
(target_id, condition) *for the current model_name*. Skip pairs that already
have >=k entries. Partial-k pairs are re-run wholesale (accepted redundancy
for a pilot; the duplicates are harmless since analysis dedupes by key).

The pool runner is deliberately the only module that knows how to map a
condition string to a context slot, via `context_for_condition`. All other
harness code treats the condition as an opaque label.
"""

import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from deduction.budget import Tokenizer, within_budget
from deduction.harness import LLMFn, PromptTemplate, run_trial
from deduction.inspect import (
    BENCHMARK_DIR,
    Premise,
    build_all_depths,
    load_corpus,
    load_traced_lookup,
    split_signature,
)

DEFAULT_CONDITIONS: List[str] = [
    "intensional",
    "ext-nodoc-d1", "ext-nodoc-d2", "ext-nodoc-d3", "ext-nodoc-d4",
    "ext-doc-d1",   "ext-doc-d2",   "ext-doc-d3",   "ext-doc-d4",
]

_COND_RE = re.compile(r"ext-(nodoc|doc)-d(\d+)")


def context_for_condition(contexts: dict, condition: str) -> str:
    """Pull the right context text out of `build_all_depths` output."""
    if condition == "intensional":
        return contexts["intensional"]
    m = _COND_RE.fullmatch(condition)
    if not m:
        raise ValueError(f"unknown condition: {condition!r}")
    kind, depth = m.group(1), int(m.group(2))
    return contexts["depth"][depth][f"ext_{kind}"]


def _load_done(log_path: Path, model_name: str) -> Dict[tuple, int]:
    """Return {(target_id, condition): count_of_trials_logged} for this model."""
    done: Dict[tuple, int] = {}
    if not log_path.exists():
        return done
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("model") != model_name:
                continue
            key = (r["target_id"], r["condition"])
            done[key] = done.get(key, 0) + 1
    return done


def run_pool(
    targets: List[dict],
    conditions: List[str],
    llm_fn: LLMFn,
    prompt_template: PromptTemplate,
    log_path: Path,
    *,
    k: int = 10,
    temperature: float = 0.7,
    model_name: str = "stub",
    max_depth: int = 4,
    corpus: Optional[Dict[str, Premise]] = None,
    traced_lookup: Optional[Dict[str, list]] = None,
    budget_tokens: Optional[int] = None,
    tokenizer: Optional[Tokenizer] = None,
    max_workers: int = 1,
) -> None:
    """Run pass@k trials across (targets × conditions), append to JSONL log.

    If `budget_tokens` and `tokenizer` are both supplied, any (target, condition)
    whose full prompt exceeds `budget_tokens` is skipped (not truncated —
    truncation would confound density-dilution with clipping artifacts). Skipped
    pairs are reported to stderr and not written to the trial log.

    `max_workers` controls (target × condition) concurrency via a
    ThreadPoolExecutor. Each worker calls `run_trial` which spawns its own
    Lean subprocess via Dojo — thread-based concurrency is fine because the
    Python side is IO-bound on subprocess IPC. The log file is append-written
    under a mutex so concurrent workers don't interleave lines."""
    if corpus is None:
        corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    if traced_lookup is None:
        traced_lookup = load_traced_lookup()
    budget_active = budget_tokens is not None and tokenizer is not None

    done = _load_done(log_path, model_name)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    n_trials_total = len(targets) * len(conditions) * k
    n_trials_done = sum(min(v, k) for v in done.values())
    print(
        f"Pool run: {len(targets)} targets × {len(conditions)} conditions × "
        f"k={k} = {n_trials_total} trials. Already logged: {n_trials_done}. "
        f"Workers: {max_workers}.",
        flush=True,
    )
    if budget_active:
        print(f"Context budget: {budget_tokens} tokens per prompt.", flush=True)

    # Serially precompute (target_sig, contexts) for every target so workers
    # don't race on build_all_depths. Fast — ~tens of ms per target.
    target_info: List[tuple] = []
    for t_idx, target in enumerate(targets, 1):
        target_id = target["full_name"]
        target_sig = split_signature(corpus[target_id].corpus_code)
        contexts = build_all_depths(target, corpus, traced_lookup, max_depth=max_depth)
        target_info.append((t_idx, target, target_sig, contexts))

    log_lock = threading.Lock()

    def process_pair(t_idx, target, target_sig, contexts, c_idx, condition) -> None:
        target_id = target["full_name"]
        tag = f"[{t_idx}/{len(targets)}] {target_id}  [{c_idx}/{len(conditions)}] {condition}"
        if done.get((target_id, condition), 0) >= k:
            print(f"  {tag}: cached ({k}/{k})", flush=True)
            return
        context_text = context_for_condition(contexts, condition)
        if budget_active:
            prompt = prompt_template(target_sig, context_text)
            fits, n_tokens = within_budget(prompt, budget_tokens, tokenizer)
            if not fits:
                print(
                    f"  {tag} ({len(context_text)} chars, {n_tokens} tokens): "
                    f"DROPPED (> budget {budget_tokens})",
                    file=sys.stderr, flush=True,
                )
                return
        print(
            f"  {tag} ({len(context_text)} chars): running k={k} ...",
            flush=True,
        )
        results = run_trial(
            target_id=target_id,
            file_path=target["file_path"],
            target_sig=target_sig,
            context_text=context_text,
            condition=condition,
            prompt_template=prompt_template,
            llm_fn=llm_fn,
            k=k,
            temperature=temperature,
            model_name=model_name,
        )
        n_pass = sum(1 for r in results if r.ok)
        mean_ms = sum(r.wall_ms for r in results) / max(len(results), 1)
        print(f"    -> {tag}: {n_pass}/{k} passed, mean_wall_ms={mean_ms:.0f}", flush=True)
        with log_lock:
            with log_path.open("a") as f:
                for r in results:
                    f.write(json.dumps(r.to_json_dict()) + "\n")

    pairs = [
        (t_idx, target, target_sig, contexts, c_idx, condition)
        for (t_idx, target, target_sig, contexts) in target_info
        for c_idx, condition in enumerate(conditions, 1)
    ]

    if max_workers <= 1:
        for args in pairs:
            process_pair(*args)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(process_pair, *args) for args in pairs]
        for f in as_completed(futures):
            exc = f.exception()
            if exc is not None:
                raise exc


def pilot_pool(
    corpus: Dict[str, Premise], traced_lookup: Dict[str, list], max_n: int
) -> List[dict]:
    """Large replay-filter-filtered pool of well-connected test theorems, up to max_n.

    'Well-connected' filter + replay-filter intersection. This is what the
    actual pilot will run against; we pass a small slice of it in smoke tests.
    """
    from deduction.inspect import pick_well_connected

    replay_path = Path(__file__).resolve().parent.parent / "data" / "replay_filter.json"
    replay_cache = json.load(replay_path.open())
    passing = {name for name, r in replay_cache.items() if r["ok"]}

    test = json.load((BENCHMARK_DIR / "random" / "test.json").open())
    # `pick_well_connected` sees the raw test split; only take replay-passing ones.
    # Its signature takes a target count; ask for more than max_n since we'll filter.
    candidates = pick_well_connected(test, corpus, traced_lookup, n=max_n * 3)
    filtered = [t for t in candidates if t["full_name"] in passing]
    return filtered[:max_n]
