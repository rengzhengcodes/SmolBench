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

Spot-instance behavior:
  - Output JSONL is opened in append mode. On startup, completed
    (target, K, B, seed) cells are read from the file and skipped. A
    spot-interruption-restarted runner thus picks up where the last process
    died.
  - A sibling `<out>.meta.json` records the run-level context (instance,
    model, code SHA, args, launch ts) once per process invocation.
  - Each cell record stores the full prompt + raw model response so the
    run is fully reproducible offline.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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
    # Full-fidelity capture (we want everything in S3 for offline analysis).
    prompt_full: str = ""
    response_full: str = ""
    proof_body_extracted: Optional[str] = None
    lean_source_submitted: Optional[str] = None
    verifier_messages: Optional[list] = None
    # Provenance (so we can merge JSONLs from multiple boxes).
    instance_id: Optional[str] = None
    model: Optional[str] = None
    ts: Optional[str] = None  # ISO 8601 UTC of cell completion


# ---------- run-level metadata ----------

def _get_imds_token() -> Optional[str]:
    try:
        req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.read().decode()
    except Exception:
        return None


def _imds_get(path: str, token: Optional[str]) -> Optional[str]:
    try:
        req = urllib.request.Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token} if token else {},
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def _git_sha(repo_root: Path) -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _git_status(repo_root: Path) -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def collect_run_meta(args, n_targets: int, n_cells: int) -> dict:
    """Snapshot run-level context. Written once per process to <out>.meta.json."""
    repo_root = Path(__file__).resolve().parent.parent
    token = _get_imds_token()
    return {
        "ts_start": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "instance_id": _imds_get("instance-id", token),
        "instance_type": _imds_get("instance-type", token),
        "public_ipv4": _imds_get("public-ipv4", token),
        "availability_zone": _imds_get("placement/availability-zone", token),
        "ami_id": _imds_get("ami-id", token),
        "code_sha": _git_sha(repo_root),
        "code_dirty": _git_status(repo_root),
        "model": args.model,
        "vllm_url": args.vllm_url,
        "kimina_url": args.server_url,
        "args": vars(args),
        "n_targets": n_targets,
        "n_cells_total": n_cells,
        "pid": os.getpid(),
    }


# ---------- resumability ----------

def load_completed(out_path: Path) -> Set[Tuple[str, int, int, int]]:
    """Read existing JSONL output and return the set of completed cells.

    A cell is "completed" if its record was successfully written, regardless
    of verify_pass — we don't want to re-run an already-graded cell, only
    pick up cells that were never graded due to interruption.
    """
    if not out_path.exists():
        return set()
    done: Set[Tuple[str, int, int, int]] = set()
    n_bad = 0
    with out_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                done.add((r["target_id"], r["K"], r["B"], r["seed"]))
            except Exception:
                n_bad += 1
    if n_bad:
        print(f"  (resume) skipped {n_bad} malformed line(s) in {out_path}",
              file=sys.stderr)
    return done


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
    max_prompt_chars: int,
    instance_id: Optional[str],
) -> CellResult:
    t_total = time.perf_counter()
    now_iso = lambda: datetime.now(timezone.utc).isoformat()
    base_kwargs = dict(
        target_id=target.full_name, K=K, B=B, seed=seed,
        instance_id=instance_id, model=model,
    )

    # 1. Elaborate premises
    elab = expand_premises(target, K=K, B=B, corpus=corpus, traced_lookup=traced_lookup)

    # 2. LLM view
    user_msg = build_user_message(target, K=K, premises_blocks=elab.blocks)
    premise_chars = sum(len(s) for block in elab.blocks for s in block)

    # 2b. Context-overflow guard: skip cells whose prompt is too big to fit
    # the model's context window with reasonable headroom for the response.
    # We compare against char count (rough proxy for tokens at ~4 chars/tok).
    if max_prompt_chars > 0 and len(user_msg) > max_prompt_chars:
        wall = int((time.perf_counter() - t_total) * 1000)
        return CellResult(
            **base_kwargs,
            prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
            completion_tokens=None, extracted_proof_chars=0,
            extraction_path="context_overflow_skip",
            verify_pass=False, error_class="context_overflow",
            error_detail=f"prompt {len(user_msg)} chars > cap {max_prompt_chars}",
            lookup_leak_attempt=False, transport_error=None, wall_ms=wall,
            skipped_no_corpus_count=len(elab.skipped_no_corpus),
            skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
            prompt_full=user_msg, response_full="", proof_body_extracted=None,
            lean_source_submitted=None, verifier_messages=None,
            ts=now_iso(),
        )

    # 3. Generate
    try:
        gen = generate(
            vllm_client, user_msg,
            model=model, temperature=temperature, max_tokens=max_tokens, seed=seed,
        )
    except Exception as e:
        wall = int((time.perf_counter() - t_total) * 1000)
        return CellResult(
            **base_kwargs,
            prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
            completion_tokens=None, extracted_proof_chars=0,
            extraction_path="generate_error",
            verify_pass=False, error_class="other", error_detail=f"generate: {e}"[:300],
            lookup_leak_attempt=False, transport_error=None, wall_ms=wall,
            skipped_no_corpus_count=len(elab.skipped_no_corpus),
            skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
            prompt_full=user_msg, response_full="", proof_body_extracted=None,
            lean_source_submitted=None, verifier_messages=None,
            ts=now_iso(),
        )

    # 4. Extract proof body
    pb = extract_proof_body(gen.raw, target.local_name)
    if pb.body is None:
        wall = int((time.perf_counter() - t_total) * 1000)
        return CellResult(
            **base_kwargs,
            prompt_chars=len(user_msg), prompt_premise_chars=premise_chars,
            completion_tokens=gen.completion_tokens, extracted_proof_chars=0,
            extraction_path=pb.extraction_path,
            verify_pass=False, error_class="parse_error",
            error_detail="model output had no extractable proof body",
            lookup_leak_attempt=False, transport_error=None, wall_ms=wall,
            skipped_no_corpus_count=len(elab.skipped_no_corpus),
            skipped_non_mathlib_count=len(elab.skipped_non_mathlib),
            prompt_full=user_msg, response_full=gen.raw, proof_body_extracted=None,
            lean_source_submitted=None, verifier_messages=None,
            ts=now_iso(),
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
        **base_kwargs,
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
        prompt_full=user_msg, response_full=gen.raw, proof_body_extracted=pb.body,
        lean_source_submitted=src, verifier_messages=res.messages,
        ts=now_iso(),
    )


# ---------- grid + concurrency ----------

def parse_int_list(spec: str) -> List[int]:
    return [int(x) for x in spec.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", type=Path, default=Path("data/replay_pool.jsonl"),
                    help="Replay-pool JSONL (output of deduction.filter).")
    ap.add_argument("--out", type=Path, required=True,
                    help="Per-cell JSONL output path. Opened in APPEND mode "
                         "— a re-run on the same path skips already-completed "
                         "cells.")
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
    ap.add_argument("--max-prompt-chars", type=int, default=100_000,
                    help="Skip cells whose prompt exceeds this many chars "
                         "(rough char->token at ~4 chars/tok). 0 disables. "
                         "Default 100K chars ≈ 25K tokens, leaves headroom "
                         "for response on a 32K-context model.")
    ap.add_argument("--no-resume", action="store_true",
                    help="If set, ignore any existing rows in --out and start "
                         "fresh. Default: resume from existing rows.")
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

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Resumability: skip cells already in output.
    completed: Set[Tuple[str, int, int, int]] = set()
    if not args.no_resume:
        completed = load_completed(args.out)
    if completed:
        print(f"Resume: {len(completed)} cells already in {args.out}; "
              f"will skip those.", flush=True)
    pending_cells = [
        (t, f_down, K, B, seed)
        for (t, f_down, K, B, seed) in cells
        if (t.full_name, K, B, seed) not in completed
    ]

    print(f"Pool: {len(targets)} targets, "
          f"Ks={Ks}, Bs={Bs}, k_seeds={args.k_seeds}, "
          f"total cells={len(cells)}, pending={len(pending_cells)}", flush=True)
    print(f"Log: {args.out}", flush=True)

    # Run-level metadata: emitted once per process invocation. Append-mode by
    # design — multiple restarts produce a JSONL of process-start records
    # (also gives us a record of how many spot-restarts happened).
    meta = collect_run_meta(args, n_targets=len(targets), n_cells=len(cells))
    meta_path = args.out.with_suffix(args.out.suffix + ".meta.jsonl")
    with meta_path.open("a") as mf:
        mf.write(json.dumps(meta) + "\n")
    print(f"Meta: {meta_path} (instance={meta.get('instance_id')}, "
          f"sha={(meta.get('code_sha') or '?')[:8]})", flush=True)

    instance_id = meta.get("instance_id")
    client = make_client(args.vllm_url)

    n_done = 0
    n_pass = 0
    n_extract_fail = 0
    n_leak = 0
    n_overflow = 0
    t0 = time.time()

    with args.out.open("a") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(
                run_cell, t, K, B, seed,
                corpus=corpus, traced_lookup=traced, f_downstream=f_down,
                vllm_client=client, model=args.model,
                temperature=args.temperature, max_tokens=args.max_tokens,
                server_url=args.server_url, verify_timeout=args.verify_timeout,
                max_prompt_chars=args.max_prompt_chars,
                instance_id=instance_id,
            ): (t.full_name, K, B, seed)
            for (t, f_down, K, B, seed) in pending_cells
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
            if rec["error_class"] == "context_overflow":
                n_overflow += 1
            if n_done % 5 == 0 or n_done == len(pending_cells):
                pct = 100 * n_pass / max(n_done, 1)
                print(f"  [{n_done:4d}/{len(pending_cells)}] pass={n_pass} "
                      f"extract_fail={n_extract_fail} leak={n_leak} "
                      f"overflow={n_overflow} ({pct:.0f}% pass)", flush=True)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. {n_pass}/{len(pending_cells)} pass "
          f"({100 * n_pass / max(len(pending_cells), 1):.0f}%).")


if __name__ == "__main__":
    main()
