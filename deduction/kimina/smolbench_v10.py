"""SmolBench (Mathlib 73-target pool) driver for proof-completion.

Same X axis as miniF2F v10:
  X = n_given (number of leading tactics from the reference proof)

Reference proofs come directly from Mathlib source — guaranteed to
compile (the pool is filtered to "replay-passing" targets when built
in deduction.inspect.pilot_pool).

Mathlib proofs are typically much shorter than miniF2F competition
proofs (1-5 tactics median), so the dose curve has fewer interior
points per problem.

The Lean source emitted at the file level mirrors what the v7
extensional builders produce: `import Mathlib` + the target file's
file-level scope (open / variable / universe / namespace stack) so
that the theorem's notations and binders resolve correctly.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import List

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import (
    BENCHMARK_DIR, MATHLIB_DIR, load_corpus, load_traced_lookup, source_text,
)
from deduction.pool_runner import pilot_pool
from deduction.kimina.v7_statement_ext import collect_target_ctx
from deduction.kimina.minif2f_v10 import (
    _split_signature, _split_tactics, USER_PREFIX, extract_kimina_proof,
    generate, verify,
)

SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"


@dataclass
class SBTarget:
    name: str
    sig_text: str
    proof_body: str
    tactics: List[str]
    file_ctx: str   # opens/variables/namespace from target's Mathlib file


def _attr_modifier_strip(src: str) -> str:
    """Strip leading attributes and modifiers so the regex below sees a
    clean `theorem <name>` head."""
    src = re.sub(r'@\[[^\]]*\]\s*', "", src)
    src = re.sub(
        r'^(?:\s*(?:noncomputable|private|protected|scoped|partial|mutual|unsafe)\s+)+',
        "", src, flags=re.MULTILINE,
    )
    return src


def _strip_doc_comment(src: str) -> str:
    """Remove a leading `/-- ... -/` doc-string before the theorem keyword."""
    m = re.match(r'\s*/--.*?-/\s*', src, flags=re.DOTALL)
    if m:
        return src[m.end():]
    return src


def _parse_decl(src: str) -> tuple[str, str] | None:
    """Given source text starting with `theorem`/`lemma <name> <sig> := <body>`,
    return (sig, body). `sig` excludes the keyword and decl name; `body`
    excludes the `:=`. Returns None on parse failure."""
    src = _strip_doc_comment(src)
    src = _attr_modifier_strip(src)
    # Strip leading `theorem|lemma <name> ` (Lean identifiers can include
    # subscripts and unicode letters; \w matches Unicode by default).
    m = re.match(r'\s*(?:theorem|lemma)\s+[\w.\']+\s*', src)
    if m is None:
        return None
    rest = src[m.end():]
    # Find top-level `:=` outside brackets
    depth = 0
    i = 0
    body_idx = -1
    while i < len(rest) - 1:
        c = rest[i]
        if c in "[({":
            depth += 1
        elif c in "])}":
            depth -= 1
        elif depth == 0 and c == ":" and rest[i + 1] == "=":
            body_idx = i
            break
        i += 1
    if body_idx == -1:
        return None
    sig = rest[:body_idx].rstrip()
    body = rest[body_idx + 2:].lstrip()
    if body.startswith("by"):
        body = body[2:]
    return sig, body


def load_smolbench_problems(max_n: int = 73) -> List[SBTarget]:
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced = load_traced_lookup()
    pool = pilot_pool(corpus, traced, max_n=max_n)
    probs: List[SBTarget] = []
    for t in pool:
        p = corpus[t["full_name"]]
        src = source_text(p)
        if src is None: continue
        parsed = _parse_decl(src)
        if parsed is None: continue
        sig, body_src = parsed
        tactics = _split_tactics(body_src)
        # File context (opens, variables, namespace) at the target's line
        src_path = MATHLIB_DIR / p.file_path
        if not src_path.exists(): continue
        file_text = src_path.read_text()
        file_ctx = collect_target_ctx(file_text, p.start[0] - 1)
        probs.append(SBTarget(
            name=p.full_name, sig_text=sig, proof_body=body_src,
            tactics=tactics, file_ctx=file_ctx,
        ))
    return probs


def build_completion_file(prob: SBTarget, n_given: int) -> str:
    """Build a Lean source with the target's file-level scope, the
    theorem signature, and the first `n_given` tactics of its reference
    proof. Empty / partial body ends with `sorry` for Kimina to close."""
    if n_given <= 0:
        proof_section = "  sorry"
    elif n_given >= len(prob.tactics):
        proof_section = "\n".join(prob.tactics)
    else:
        prefix = "\n".join(prob.tactics[:n_given])
        proof_section = prefix + "\n  sorry"

    # Use a sanitized name to avoid colliding with Mathlib's existing
    # declaration when verified (file-level context may already declare
    # the original).
    sb_name = "sb_" + re.sub(r'\W', '_', prob.name)

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + prob.file_ctx + "\n\n"
        + f"theorem {sb_name} {prob.sig_text} := by\n"
        + proof_section + "\n"
    )


_LOG_LOCK = None  # set in main()


def _run_one(prob, n_given, n_spec_label, client, model, server_url, k):
    code = build_completion_file(prob, n_given)
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
        "n_total_tactics": len(prob.tactics),
        "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }


def process_all_specs(prob, n_specs, client, model, server_url, k, log_path):
    """Run every n_spec for this single problem (serially within the
    worker), append each as a separate jsonl record. Atomic per-problem
    completion: at any cutoff, any record we've written has the full
    dose curve for that problem."""
    summary = []
    for n_spec_label, n_given in n_specs:
        rec = _run_one(prob, n_given, n_spec_label, client, model,
                       server_url, k)
        with _LOG_LOCK:
            with open(log_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
        summary.append((n_spec_label, rec["pass"]))
    return prob.name, summary


def _resolve_n(spec, n_total):
    if spec == "last-1":
        return max(0, n_total - 1)
    if spec.startswith("frac="):
        f = float(spec[5:])
        return int(f * n_total)
    n = int(spec)
    if n < 0:
        return n_total  # -1 = full
    return n


def main():
    import threading
    global _LOG_LOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-specs", required=True,
                    help="Comma-separated list of n_given specs. Each may be "
                         "an integer ('1', '-1' for full), 'frac=<float>', or "
                         "'last-1'. Per-problem, ALL listed specs are run "
                         "serially before moving to the next problem.")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    spec_labels = [s.strip() for s in args.n_specs.split(",") if s.strip()]

    problems = load_smolbench_problems()
    print(f"n_specs={spec_labels}  pool={len(problems)}  k={args.k}  "
          f"workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")
    _LOG_LOCK = threading.Lock()

    t0 = time.time()
    n_done = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {}
        for p in problems:
            specs = [(s, _resolve_n(s, len(p.tactics))) for s in spec_labels]
            fm[ex.submit(process_all_specs, p, specs, client, args.model,
                         args.server_url, args.k, args.log)] = p
        for fut in futs.as_completed(fm):
            name, summary = fut.result()
            n_done += 1
            n_pool = len(problems)
            tag = " ".join(f"{s}={'P' if ok else 'F'}" for s, ok in summary)
            print(f"  [{n_done:3d}/{n_pool}] {name[:50]:50s}  {tag}",
                  flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"records: {len(problems) * len(spec_labels)}")


if __name__ == "__main__":
    main()
