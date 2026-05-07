"""SmolBench (Mathlib 73-target pool) driver — proof-completion (X-axis)
+ depth abbrev expansion (Y-axis lines).

Adds depth `d` on top of smolbench_v10's n_given:
  - At d>0, every Mathlib corpus name in (target sig + visible proof
    prefix) gets a chained `noncomputable abbrev sb_X := <body>` block
    prepended, recursively to depth d (v9 chained-abbrev pattern).
  - The target signature AND visible tactic prefix are then rewritten
    to use `sb_X` names — forcing the model to engage with the abbrev,
    not just see it as floating context.
  - Per-helper verify-and-fallback (v9): if an abbrev doesn't parse
    standalone, it's dropped and the original Mathlib name is kept in
    parent bodies / sig / prefix.

This is the (X, Y) grid:
  X = n_given (0, 1, floor(N/2), N-1, N)
  Y = d (0, 1, 2)
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import threading
import time
from typing import List, Tuple

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import (
    BENCHMARK_DIR, MATHLIB_DIR, load_corpus, load_traced_lookup, source_text,
)
from deduction.pool_runner import pilot_pool
from deduction.kimina.v7_statement_ext import collect_target_ctx
from deduction.kimina.minif2f_v9 import (
    _names_in, _substitute_name, _abbrev_parses, _sb,
)
from deduction.kimina.lean_query import print_decl, extract_def_body
from deduction.kimina.smolbench_v10 import (
    SBTarget, USER_PREFIX, _split_tactics,
    _attr_modifier_strip, _strip_doc_comment, _parse_decl,
    extract_kimina_proof, generate, verify, load_smolbench_problems,
)

SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"


def _build_chain_for_text(visible: str, corpus, depth: int,
                          server_url: str) -> Tuple[List[str], dict]:
    """Run v9's BFS-with-verify chain on text. Returns (abbrev_blocks,
    sb_map). sb_map maps original Mathlib names -> their sb_X aliases
    for those that survived per-helper verification."""
    if depth <= 0:
        return [], {}
    levels: List[List[str]] = []
    seen: set = set()
    bodies: dict = {}

    level0 = _names_in(visible, corpus)
    seen.update(level0)
    levels.append(level0)

    for _ in range(1, depth):
        next_level = []
        for name in levels[-1]:
            if name not in bodies:
                bodies[name] = extract_def_body(print_decl(name, server_url))
            body = bodies[name]
            if body is None:
                continue
            for n in _names_in(body, corpus):
                if n not in seen:
                    seen.add(n)
                    next_level.append(n)
        if not next_level:
            break
        levels.append(next_level)

    for name in levels[-1]:
        if name not in bodies:
            bodies[name] = extract_def_body(print_decl(name, server_url))

    sb_map = {n: _sb(n)
              for level in levels for n in level if bodies.get(n)}

    blocks: List[str] = []
    for k in range(len(levels) - 1, -1, -1):
        for name in levels[k]:
            body = bodies.get(name)
            if body is None:
                continue
            if name not in sb_map:
                continue
            current = body
            for deeper_name in [n for j in range(k + 1, len(levels))
                                  for n in levels[j] if n in sb_map]:
                current = _substitute_name(current, deeper_name, sb_map[deeper_name])
            current = current.replace("⋯", "sorry")
            block = f"noncomputable abbrev {sb_map[name]} := {current}"
            if _abbrev_parses(block, server_url):
                blocks.append(block)
            else:
                del sb_map[name]
    return blocks, sb_map


def build_grid_file(prob: SBTarget, n_given: int, depth: int,
                    corpus, server_url: str = SERVER_DEFAULT) -> str:
    """Build a Lean source file for (n_given, depth) cell."""
    n_given = max(0, min(n_given, len(prob.tactics)))
    # Visible content drives which names get expanded.
    visible = prob.sig_text
    if n_given > 0:
        visible = visible + "\n" + "\n".join(prob.tactics[:n_given])

    blocks, sb_map = _build_chain_for_text(visible, corpus, depth, server_url)

    # Rewrite sig and tactics to use sb_X for surviving abbrevs.
    rewritten_sig = prob.sig_text
    for name in sb_map:
        rewritten_sig = _substitute_name(rewritten_sig, name, sb_map[name])
    rewritten_tactics = []
    for t in prob.tactics[:n_given]:
        for name in sb_map:
            t = _substitute_name(t, name, sb_map[name])
        rewritten_tactics.append(t)

    # Proof section.
    if n_given <= 0:
        proof_section = "  sorry"
    elif n_given >= len(prob.tactics):
        proof_section = "\n".join(rewritten_tactics)
    else:
        proof_section = "\n".join(rewritten_tactics) + "\n  sorry"

    sb_name = "sb_" + re.sub(r'\W', '_', prob.name)
    helpers = ("\n\n".join(blocks) + "\n\n") if blocks else ""

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + prob.file_ctx + "\n\n"
        + helpers
        + f"theorem {sb_name} {rewritten_sig} := by\n"
        + proof_section + "\n"
    )


_LOG_LOCK = None


def _resolve_n(spec: str, n_total: int) -> int:
    if spec == "last-1":
        return max(0, n_total - 1)
    if spec.startswith("frac="):
        return int(float(spec[5:]) * n_total)
    n = int(spec)
    return n_total if n < 0 else n


def _run_one(prob, n_given, n_spec_label, depth, corpus, client, model,
             server_url, k):
    code = build_grid_file(prob, n_given, depth, corpus, server_url)
    user_msg = USER_PREFIX + code
    attempts, any_pass = [], False
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tok = generate(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"})
            continue
        proof = extract_kimina_proof(raw)
        if not proof:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tok})
            continue
        try:
            ok, errs = verify(server_url, proof)
        except Exception as e:
            attempts.append({"k": i, "error": f"ver:{str(e)[:80]}"})
            continue
        attempts.append({
            "k": i, "ok": ok, "tokens_out": tok,
            "first_err": (str(errs[0].get("data"))[:200] if errs else None),
            "wall_ms": int((time.perf_counter() - t0) * 1000),
        })
        if ok:
            any_pass = True
            break
    return {
        "target": prob.name, "n_given": n_given, "n_spec": n_spec_label,
        "depth": depth,
        "n_total_tactics": len(prob.tactics),
        "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }


def process_grid(prob, cells, corpus, client, model, server_url, k, log_path):
    """Run every (n_spec, depth) cell for this single problem (serially
    within the worker), append each as a separate jsonl record."""
    summary = []
    for n_spec_label, n_given, depth in cells:
        rec = _run_one(prob, n_given, n_spec_label, depth, corpus, client,
                       model, server_url, k)
        with _LOG_LOCK:
            with open(log_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
        summary.append((n_spec_label, depth, rec["pass"]))
    return prob.name, summary


def main():
    global _LOG_LOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-specs", required=True,
                    help="Comma-separated n_given specs, e.g. '0,1,frac=0.5,last-1,-1'")
    ap.add_argument("--depths", required=True,
                    help="Comma-separated depths, e.g. '0,1,2'")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    spec_labels = [s.strip() for s in args.n_specs.split(",") if s.strip()]
    depths = [int(d) for d in args.depths.split(",")]

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    problems = load_smolbench_problems()
    print(f"n_specs={spec_labels}  depths={depths}  pool={len(problems)}  "
          f"k={args.k}  workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")
    _LOG_LOCK = threading.Lock()

    t0 = time.time()
    n_done = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {}
        for p in problems:
            cells = [(s, _resolve_n(s, len(p.tactics)), d)
                     for s in spec_labels for d in depths]
            fm[ex.submit(process_grid, p, cells, corpus, client, args.model,
                         args.server_url, args.k, args.log)] = p
        for fut in futs.as_completed(fm):
            name, summary = fut.result()
            n_done += 1
            n_pool = len(problems)
            tag = " ".join(f"{s}/d{d}={'P' if ok else 'F'}"
                           for s, d, ok in summary)
            print(f"  [{n_done:3d}/{n_pool}] {name[:45]:45s}  {tag}",
                  flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"records: {len(problems) * len(spec_labels) * len(depths)}")


if __name__ == "__main__":
    main()
