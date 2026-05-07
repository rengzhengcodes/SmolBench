"""Min-prompt baseline runner.

For each target, send the model a *minimal*, MiniF2F-style prompt:
  - `import Mathlib + import Aesop + set_option maxHeartbeats 0`
  - F's scope-only prefix (namespaces/sections/variables/opens)
  - `theorem T sig := by` (no sorry, no K hint, no premises)

Capture the model's continuation, splice it into a Lean source built with
`build_lean_view_min` (uses `example` to dodge T-already-declared), and
verify. One cell per target. K and B don't apply.

This is the "ceiling baseline" — what the model can do under its native
prompt format with full Mathlib in scope. Compares to the K=0 condition
of the main K/B grid.

Output: JSONL at args.out, one record per target. Schema mirrors
runner.py's CellResult where applicable, plus a `prompt_kind: "min"`
tag.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Set

from deduction.src.corpus import load_corpus, load_traced_lookup
from deduction.src.elaborate import expand_premises
from deduction.src.errors import ErrorClass, classify_messages
from deduction.src.kimina import KIMINA_URL_DEFAULT, is_up, verify
from deduction.src.lean_file import build_lean_view_min
from deduction.src.prompt import MIN_SYSTEM, build_min_user_message
from deduction.src.targets import Target, build_target
from deduction.src.vllm_client import (
    MODEL_DEFAULT,
    VLLM_BASE_URL_DEFAULT,
    make_client,
)
from openai import OpenAI


@dataclass
class MinCell:
    target_id: str
    K: int  # 0 = no hint; n_tactics = K=max (full canonical proof shown)
    B: int  # 0 = no premise expansion; >0 = BFS depth of premise rendering
    sample_idx: int  # 0..n_samples-1, identifies sample within the cell
    n_samples: int   # total samples in this (target,K,B) cell
    n_tactics: int
    style: str  # "advisory" or "continuation"
    prompt_premise_chars: int
    prompt_chars: int
    completion_tokens: Optional[int]
    extracted_proof_chars: int
    extraction_path: str
    verify_pass: bool
    error_class: Optional[str]
    error_detail: Optional[str]
    transport_error: Optional[str]
    wall_ms: int
    prompt_full: str = ""
    response_full: str = ""
    proof_body_extracted: Optional[str] = None
    lean_source_submitted: Optional[str] = None
    verifier_messages: Optional[list] = None
    instance_id: Optional[str] = None
    model: Optional[str] = None
    ts: Optional[str] = None


# ---------- extraction (different from runner.py — model continues from `by`) ----------

_FENCE_RE = re.compile(r"```lean4?\s*\n(.*?)\n```", re.DOTALL)


def extract_continuation(model_output: str) -> tuple[Optional[str], str]:
    """Pull the proof body the model produced after the `theorem T sig := by`
    line in our prompt. Strategy:
      1. Look for a fenced ```lean(4)? block; take everything in it.
         If the block contains a fresh `theorem ... := by` line, take what's
         after (model echoed our header).
      2. Else fall back to the last `:= by` in raw output and take after.
    Returns (body, extraction_path)."""
    fences = _FENCE_RE.findall(model_output)
    if fences:
        block = fences[-1]
        m = re.search(r":=\s*by\b\s*\n?", block)
        if m:
            return block[m.end():].rstrip(), "fenced_after_by"
        # No `:= by` inside fence — take the entire fenced content.
        return block.rstrip(), "fenced_raw"
    # No fence — try last `:= by` in raw output.
    m = None
    for mm in re.finditer(r":=\s*by\b\s*\n?", model_output):
        m = mm
    if m:
        return model_output[m.end():].rstrip(), "raw_after_by"
    return None, "parse_error"


def _ensure_indent(body: str) -> str:
    """Ensure each non-empty line is at least 2-space indented (the body is
    spliced after `theorem T sig := by\\n`)."""
    out = []
    for line in body.splitlines():
        if not line.strip():
            out.append(line)
            continue
        if not line.startswith(" "):
            out.append("  " + line)
        else:
            out.append(line)
    return "\n".join(out)


# ---------- run one cell ----------

def run_min_cell(
    target: Target, K: int, B: int, *, style: str,
    n_samples: int,
    corpus, traced_lookup,
    vllm_client: OpenAI, model: str,
    temperature: float, max_tokens: int, server_url: str, verify_timeout: int,
    instance_id: Optional[str],
) -> List[MinCell]:
    """Run one (target, K, B) cell with `n_samples` samples.

    Generation is batched in a single vLLM call (`n=n_samples`) so prefill
    is shared across samples. Verification fans out concurrently across
    samples using a per-cell thread pool — kimina-lean-server queues to
    MAX_REPLS so client-side concurrency beyond that just queues, but
    keeps the in-flight set saturated.
    """
    t0 = time.perf_counter()
    now_iso = lambda: datetime.now(timezone.utc).isoformat()
    elab = expand_premises(target, K=K, B=B, corpus=corpus, traced_lookup=traced_lookup)
    premise_chars = sum(len(s) for block in elab.blocks for s in block)
    user_msg = build_min_user_message(target, K=K, style=style,
                                       premises_blocks=elab.blocks)
    base_common: dict[str, Any] = dict(
        target_id=target.full_name, K=K, B=B,
        n_samples=n_samples, n_tactics=len(target.tactics),
        style=style, prompt_premise_chars=premise_chars,
        instance_id=instance_id, model=model,
    )

    try:
        r = vllm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MIN_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=temperature, max_tokens=max_tokens,
            n=n_samples,
        )
    except Exception as e:
        wall = int((time.perf_counter() - t0) * 1000)
        return [
            MinCell(
                **base_common, sample_idx=i, prompt_chars=len(user_msg),
                completion_tokens=None,
                extracted_proof_chars=0, extraction_path="generate_error",
                verify_pass=False, error_class="other",
                error_detail=f"generate: {e}"[:300], transport_error=None,
                wall_ms=wall, prompt_full=user_msg, response_full="", ts=now_iso(),
            )
            for i in range(n_samples)
        ]

    # OpenAI usage.completion_tokens is the total across all n choices.
    # Per-sample tokens aren't exposed — store the average.
    total_tok = r.usage.completion_tokens if r.usage else None
    avg_tok = (total_tok // len(r.choices)) if (total_tok is not None and r.choices) else None
    raws = [(c.message.content or "") for c in r.choices]
    # vLLM should return exactly n choices; pad with empty if not.
    while len(raws) < n_samples:
        raws.append("")

    def _verify_one(i: int, raw: str) -> MinCell:
        body, ext_path = extract_continuation(raw)
        if body is None:
            wall = int((time.perf_counter() - t0) * 1000)
            return MinCell(
                **base_common, sample_idx=i, prompt_chars=len(user_msg),
                completion_tokens=avg_tok,
                extracted_proof_chars=0, extraction_path=ext_path,
                verify_pass=False, error_class="parse_error",
                error_detail="no extractable body", transport_error=None,
                wall_ms=wall, prompt_full=user_msg, response_full=raw, ts=now_iso(),
            )
        body_indented = _ensure_indent(body)
        src = build_lean_view_min(target, body=body_indented)
        res = verify(src, server_url=server_url, timeout=verify_timeout)
        classified = classify_messages(res.messages)
        primary = next((c for c in classified if c.error_class is not ErrorClass.SORRY), None)
        wall = int((time.perf_counter() - t0) * 1000)
        return MinCell(
            **base_common, sample_idx=i, prompt_chars=len(user_msg),
            completion_tokens=avg_tok,
            extracted_proof_chars=len(body_indented),
            extraction_path=ext_path,
            verify_pass=res.ok and not classified,
            error_class=primary.error_class.value if primary else None,
            error_detail=primary.detail if primary else None,
            transport_error=res.transport_error,
            wall_ms=wall,
            prompt_full=user_msg, response_full=raw,
            proof_body_extracted=body_indented,
            lean_source_submitted=src,
            verifier_messages=res.messages,
            ts=now_iso(),
        )

    if n_samples == 1:
        return [_verify_one(0, raws[0])]
    with ThreadPoolExecutor(max_workers=n_samples) as inner:
        # map preserves input order, so results come back sample_idx-aligned
        return list(inner.map(lambda ir: _verify_one(*ir), enumerate(raws)))


# ---------- pool / meta / resume (mirrors runner.py shape) ----------

def load_pool(path: Path) -> List[str]:
    out = []
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("ok"):
                out.append(r["full_name"])
    return out


def _imds_token() -> Optional[str]:
    try:
        req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token", method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.read().decode()
    except Exception:
        return None


def _imds(path: str, tok: Optional[str]) -> Optional[str]:
    try:
        req = urllib.request.Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": tok} if tok else {})
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def load_completed(out_path: Path, n_samples: int) -> set:
    """(target_id, K, B) tuples that already have >= n_samples records.

    Backward compatible: rows without sample_idx (legacy n=1 runs) are
    counted as one sample each, so a cell with n_samples=1 in legacy
    data resumes correctly. With n_samples>1, partially-filled cells
    re-run from scratch (we never keep a partial cell)."""
    if not out_path.exists():
        return set()
    counts: dict = {}
    with out_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
                key = (r["target_id"], r.get("K", 0), r.get("B", 0))
                counts[key] = counts.get(key, 0) + 1
            except Exception:
                pass
    return {k for k, c in counts.items() if c >= n_samples}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", type=Path, default=Path("data/replay_pool.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--target-limit", type=int, default=None)
    ap.add_argument("--names", nargs="*")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--vllm-url", default=VLLM_BASE_URL_DEFAULT)
    ap.add_argument("--server-url", default=KIMINA_URL_DEFAULT)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--n-samples", type=int, default=1,
                    help="Samples per cell (pass@k). With n>1, vLLM "
                         "batches via `n=` so prefill is shared. Verify "
                         "fans out concurrently per cell.")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--verify-timeout", type=int, default=300)
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--ks", default="0",
                    help="Comma-separated K values for the min prompt, "
                         "e.g. '0,max'. `max` expands per-target to "
                         "n_tactics. Default '0' = MiniF2F-style cold "
                         "(no hint).")
    ap.add_argument("--bs", default="0",
                    help="Comma-separated B values (BFS depth of premise "
                         "expansion). Each visible canonical tactic's "
                         "directly-referenced Mathlib premises are "
                         "rendered (and at B>1, premises-of-premises). "
                         "B=0 disables. With K=0, no premises (no visible "
                         "tactics to derive references from).")
    ap.add_argument("--style", default="advisory",
                    choices=("advisory", "continuation"),
                    help="Where to place the K canonical tactics in the "
                         "prompt. `advisory` (default): separate hint "
                         "block above the theorem; theorem body is "
                         "`sorry`. `continuation`: K tactics inside the "
                         "theorem's `:= by` block followed by `sorry`. "
                         "Continuation biases toward continuation; "
                         "advisory leaves the model free to write the "
                         "complete proof its own way.")
    args = ap.parse_args()
    # Parse ks spec. Tokens: int, "max", "max-N" (where N is a positive int).
    ks_spec: list = []
    for x in args.ks.split(","):
        x = x.strip()
        if not x:
            continue
        if x == "max" or (x.startswith("max-") and x[4:].lstrip("-").isdigit()):
            ks_spec.append(x)
        else:
            ks_spec.append(int(x))

    if not is_up(args.server_url, timeout=120):
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
        print(f"ERROR: pool {args.pool} not found", file=sys.stderr)
        sys.exit(2)
    if args.target_limit is not None:
        names = names[:args.target_limit]

    targets: List[Target] = []
    for name in names:
        if name not in corpus:
            continue
        try:
            targets.append(build_target(name, corpus, traced))
        except Exception:
            continue

    args.out.parent.mkdir(parents=True, exist_ok=True)
    completed = set() if args.no_resume else load_completed(args.out, args.n_samples)

    bs = [int(x) for x in args.bs.split(",") if x.strip()]

    # Build (target, K, B) cells.
    def _resolve(k, n: int):
        if k == "max":
            return n
        if isinstance(k, str) and k.startswith("max-"):
            return max(0, n - int(k[4:]))
        if isinstance(k, int) and k <= n:
            return k
        return None

    pending: list = []
    for t in targets:
        n = len(t.tactics)
        ks = sorted({v for k in ks_spec if (v := _resolve(k, n)) is not None})
        for K in ks:
            for B in bs:
                if (t.full_name, K, B) not in completed:
                    pending.append((t, K, B))
    print(f"Pool: {len(targets)} targets × ks={ks_spec!r} × bs={bs}, "
          f"completed={len(completed)}, pending={len(pending)}", flush=True)
    print(f"Out: {args.out}", flush=True)

    tok = _imds_token()
    meta = {
        "ts_start": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "instance_id": _imds("instance-id", tok),
        "instance_type": _imds("instance-type", tok),
        "model": args.model, "args": {k: str(v) for k, v in vars(args).items()},
        "n_targets": len(targets), "pid": os.getpid(),
        "prompt_kind": "min",
    }
    meta_path = args.out.with_suffix(args.out.suffix + ".meta.jsonl")
    with meta_path.open("a") as mf:
        mf.write(json.dumps(meta, default=str) + "\n")
    instance_id = meta.get("instance_id")
    client = make_client(args.vllm_url)

    n_cells_done = n_cells_pass = 0
    n_samples_done = n_samples_pass = 0
    n_extract_fail = 0
    t0 = time.time()
    with args.out.open("a") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(
                run_min_cell, t, K, B, style=args.style,
                n_samples=args.n_samples,
                corpus=corpus, traced_lookup=traced,
                vllm_client=client, model=args.model,
                temperature=args.temperature, max_tokens=args.max_tokens,
                server_url=args.server_url, verify_timeout=args.verify_timeout,
                instance_id=instance_id,
            ): (t.full_name, K, B)
            for (t, K, B) in pending
        }
        for fut in as_completed(futures):
            cells = fut.result()
            cell_pass = False
            for cell in cells:
                rec = asdict(cell)
                f.write(json.dumps(rec) + "\n")
                n_samples_done += 1
                if rec["verify_pass"]:
                    n_samples_pass += 1
                    cell_pass = True
                if rec["extraction_path"] == "parse_error":
                    n_extract_fail += 1
            f.flush()
            n_cells_done += 1
            if cell_pass:
                n_cells_pass += 1
            if n_cells_done % 5 == 0 or n_cells_done == len(pending):
                cpct = 100 * n_cells_pass / max(n_cells_done, 1)
                spct = 100 * n_samples_pass / max(n_samples_done, 1)
                print(f"  [{n_cells_done:4d}/{len(pending)}] "
                      f"cells_pass@{args.n_samples}={n_cells_pass}({cpct:.0f}%) "
                      f"samples={n_samples_pass}/{n_samples_done}({spct:.0f}%) "
                      f"extract_fail={n_extract_fail}", flush=True)

    print(f"\nDone in {time.time()-t0:.0f}s. "
          f"cells pass@{args.n_samples}: {n_cells_pass}/{len(pending)} "
          f"({100*n_cells_pass/max(len(pending),1):.0f}%); "
          f"per-sample pass: {n_samples_pass}/{n_samples_done} "
          f"({100*n_samples_pass/max(n_samples_done,1):.0f}%).")


if __name__ == "__main__":
    main()
