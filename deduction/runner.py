"""Orchestrate the (target × K × B × seed) grid.

Reads a replay-passing pool (output of `filter.py`), iterates the grid, and
logs one JSONL record per cell per DESIGN.md's logging schema.

Pipeline per cell:
  1. `elaborate.expand_premises(target, K, B)` → premises_blocks
  2. `prompt.build_user_message(target, K, premises_blocks)` → user_msg
  3. `vllm_client.generate(client, user_msg, seed=seed)` → completion
  4. `vllm_client.extract_proof_body(completion, target.local_name)` → body
  5. `lean_file.build_lean_view(target, K, body)` → Lean source
  6. `kimina.verify(source)` → ok / messages
  7. `errors.classify_messages` + `is_lookup_leak` → typed error class
  8. Append JSONL record.

K=0..N; B=0..B_max. Each cell is sampled k_seeds times. Verdict per-cell is
any-of-k success per DESIGN.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from deduction.corpus import Premise, load_corpus, load_traced_lookup
from deduction.elaborate import expand_premises
from deduction.errors import (
    ErrorClass,
    classify_messages,
    is_lookup_leak,
)
from deduction.kimina import KIMINA_URL_DEFAULT, is_up, verify
from deduction.lean_file import build_lean_view
from deduction.prompt import build_user_message
from deduction.targets import Target, build_target
from deduction.vllm_client import (
    MODEL_DEFAULT,
    VLLM_BASE_URL_DEFAULT,
    extract_proof_body,
    generate,
    make_client,
)


@dataclass
class CellResult:
    target_id: str
    K: int
    B: int
    seed: int
    prompt_chars: int
    prompt_premise_chars: int
    completion_tokens: Optional[int]
    extracted_proof_chars: int
    extraction_path: str
    verify_pass: bool
    error_class: Optional[str]
    error_detail: Optional[str]
    lookup_leak_attempt: bool
    transport_error: Optional[str]
    wall_ms: int
    skipped_no_corpus_count: int
    skipped_non_mathlib_count: int


# ---------- pool loading ----------

def load_pool(path: Path) -> List[str]:
    """Read the replay-pool JSONL and return full_names of OK targets."""
    out: List[str] = []
    with path.open() as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("ok"):
                out.append(rec["full_name"])
    return out


# ---------- per-cell orchestration ----------

def _f_downstream_of_t(corpus: Dict[str, Premise], target: Target) -> List[str]:
    """Names declared in F at lines >= L (siblings/corollaries declared
    after T in F). Used by lookup-leak detection."""
    f_path = target.file_path  # repo-relative
    L = target.start_line
    # Pull every corpus entry whose file_path == F.file_path and start.line >= L
    return [
        p.full_name
        for p in corpus.values()
        if p.file_path == f_path and p.start[0] >= L
    ]


def run_cell(
    target: Target,
    K: int,
    B: int,
    seed: int,
    *,
    corpus: Dict[str, Premise],
    traced_lookup: Dict[str, list],
    f_downstream: List[str],
    vllm_client,
    model: str,
    temperature: float,
    max_tokens: int,
    server_url: str,
    verify_timeout: int,
) -> CellResult:
    t_total = time.perf_counter()

    # 1. Elaborate premises
    elab = expand_premises(target, K=K, B=B, corpus=corpus, traced_lookup=traced_lookup)

    # 2. LLM view
    user_msg = build_user_message(target, K=K, premises_blocks=elab.blocks)
    premise_chars = sum(len(s) for block in elab.blocks for s in block)

    # 3. Generate
    try:
        gen = generate(
            vllm_client, user_msg,
            model=model, temperature=temperature, max_tokens=max_tokens, seed=seed,
        )
    except Exception as e:
        wall = int((time.perf_counter() - t_total) * 1000)
        return CellResult(
            target_id=target.full_name, K=K, B=B, seed=seed,
            prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
            completion_tokens=None, extracted_proof_chars=0,
            extraction_path="generate_error",
            verify_pass=False, error_class="other", error_detail=f"generate: {e}"[:300],
            lookup_leak_attempt=False, transport_error=None, wall_ms=wall,
            skipped_no_corpus_count=len(elab.skipped_no_corpus),
            skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
        )

    # 4. Extract proof body
    pb = extract_proof_body(gen.raw, target.local_name)
    if pb.body is None:
        wall = int((time.perf_counter() - t_total) * 1000)
        return CellResult(
            target_id=target.full_name, K=K, B=B, seed=seed,
            prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
            completion_tokens=gen.completion_tokens, extracted_proof_chars=0,
            extraction_path=pb.extraction_path,
            verify_pass=False, error_class="parse_error",
            error_detail="model output had no extractable proof body",
            lookup_leak_attempt=False, transport_error=None, wall_ms=wall,
            skipped_no_corpus_count=len(elab.skipped_no_corpus),
            skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
        )

    # 5+6. Lean view + verify
    src = build_lean_view(target, K=K, continuation=pb.body)
    res = verify(src, server_url=server_url, timeout=verify_timeout)

    # 7. Classify
    classified = classify_messages(res.messages)
    primary = next((c for c in classified if c.error_class is not ErrorClass.SORRY), None)
    error_class = primary.error_class.value if primary else None
    error_detail = primary.detail if primary else None
    leak = False
    if primary is not None:
        leak = is_lookup_leak(
            primary,
            target_full_name=target.full_name,
            target_local_name=target.local_name,
            f_downstream_of_t_names=f_downstream,
        )

    wall = int((time.perf_counter() - t_total) * 1000)
    return CellResult(
        target_id=target.full_name, K=K, B=B, seed=seed,
        prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
        completion_tokens=gen.completion_tokens,
        extracted_proof_chars=len(pb.body),
        extraction_path=pb.extraction_path,
        verify_pass=res.ok and not classified,
        error_class=error_class, error_detail=error_detail,
        lookup_leak_attempt=leak, transport_error=res.transport_error,
        wall_ms=wall,
        skipped_no_corpus_count=len(elab.skipped_no_corpus),
        skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
    )


# ---------- grid + concurrency ----------

def parse_int_list(spec: str) -> List[int]:
    return [int(x) for x in spec.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", type=Path, default=Path("data/replay_pool.jsonl"),
                    help="Replay-pool JSONL (output of deduction.filter).")
    ap.add_argument("--out", type=Path, required=True,
                    help="Per-cell JSONL output path.")
    ap.add_argument("--ks", default="0,1",
                    help="Comma-separated K values, e.g. '0,1,2'. Capped at "
                         "len(target.tactics) per target.")
    ap.add_argument("--bs", default="0,1",
                    help="Comma-separated B values.")
    ap.add_argument("--k-seeds", type=int, default=4,
                    help="Decoding seeds per cell.")
    ap.add_argument("--target-limit", type=int, default=None,
                    help="Cap on number of targets from the pool.")
    ap.add_argument("--names", nargs="*",
                    help="Optional explicit full_names; bypasses --pool.")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--vllm-url", default=VLLM_BASE_URL_DEFAULT)
    ap.add_argument("--server-url", default=KIMINA_URL_DEFAULT)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--workers", type=int, default=2,
                    help="Concurrent (target,K,B,seed) cells.")
    ap.add_argument("--verify-timeout", type=int, default=180)
    args = ap.parse_args()

    if not is_up(args.server_url):
        print(f"ERROR: kimina-lean-server not reachable at {args.server_url}",
              file=sys.stderr)
        sys.exit(2)

    print("Loading corpus + traced_lookup ...", flush=True)
    corpus = load_corpus()
    traced = load_traced_lookup()

    if args.names:
        names = list(args.names)
    elif args.pool.exists():
        names = load_pool(args.pool)
    else:
        print(f"ERROR: pool file {args.pool} not found and --names not given",
              file=sys.stderr)
        sys.exit(2)

    if args.target_limit is not None:
        names = names[:args.target_limit]

    targets: List[Target] = []
    for name in names:
        if name not in corpus:
            print(f"  skip {name}: not in corpus", file=sys.stderr)
            continue
        try:
            targets.append(build_target(name, corpus, traced))
        except Exception as e:
            print(f"  skip {name}: {e}", file=sys.stderr)

    Ks = parse_int_list(args.ks)
    Bs = parse_int_list(args.bs)

    cells = []
    for t in targets:
        f_down = _f_downstream_of_t(corpus, t)
        for K in Ks:
            if K > len(t.tactics):
                continue
            for B in Bs:
                for seed in range(args.k_seeds):
                    cells.append((t, f_down, K, B, seed))

    print(f"Pool: {len(targets)} targets, "
          f"Ks={Ks}, Bs={Bs}, k_seeds={args.k_seeds}, "
          f"total cells={len(cells)}", flush=True)
    print(f"Log: {args.out}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    client = make_client(args.vllm_url)

    n_done = 0
    n_pass = 0
    n_extract_fail = 0
    n_leak = 0
    t0 = time.time()

    with args.out.open("w") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(
                run_cell, t, K, B, seed,
                corpus=corpus, traced_lookup=traced, f_downstream=f_down,
                vllm_client=client, model=args.model,
                temperature=args.temperature, max_tokens=args.max_tokens,
                server_url=args.server_url, verify_timeout=args.verify_timeout,
            ): (t.full_name, K, B, seed)
            for (t, f_down, K, B, seed) in cells
        }
        for fut in as_completed(futures):
            rec = asdict(fut.result())
            f.write(json.dumps(rec) + "\n")
            f.flush()
            n_done += 1
            if rec["verify_pass"]:
                n_pass += 1
            if rec["extraction_path"] == "parse_error":
                n_extract_fail += 1
            if rec["lookup_leak_attempt"]:
                n_leak += 1
            if n_done % 5 == 0 or n_done == len(cells):
                pct = 100 * n_pass / max(n_done, 1)
                print(f"  [{n_done:4d}/{len(cells)}] pass={n_pass} "
                      f"extract_fail={n_extract_fail} leak={n_leak} "
                      f"({pct:.0f}% pass)", flush=True)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. {n_pass}/{len(cells)} pass "
          f"({100 * n_pass / max(len(cells), 1):.0f}%).")


if __name__ == "__main__":
    main()
