"""Bootstrap-prover driver — generate proofs for benchmark statements that
ship without proofs (PutnamBench, ProofNet).

Workflow:
  1. Load .lean files from a configurable pool dir; each file has the
     theorem ending in `:= sorry` or `:= by sorry` (no real proof).
  2. Prompt a strong prover model (DSP-V2-671B) to complete the proof.
  3. Verify the model's output against kimina-lean-server (no syntactic
     check on the model's text — let Lean be the judge).
  4. For each problem, retry up to k attempts; on first pass, save the
     completed .lean file to an out_dir so it becomes our ground-truth
     corpus for the proof-completion experiment.

Output:
  - JSONL log: one record per problem with {name, pass, k_tried, attempts}.
  - <out_dir>/<name>.lean: full passing proof (only if pass=True).

Designed to run on us-west-2c (which has the lean-server) while the
prover model is on a different box (DSP-V2-671B node), reachable via
SSH tunnel forwarding the prover's :8010 to localhost.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import glob
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import requests
from openai import OpenAI

SERVER_DEFAULT = "http://localhost:9000"
PROVER_URL_DEFAULT = "http://localhost:8010/v1"
PROVER_MODEL_DEFAULT = "deepseek-ai/DeepSeek-Prover-V2-671B"

# DSP-V2 prompt: the canonical "Complete the following Lean 4 code" template
# used in DeepSeek-Prover-V2's training corpus. Chat template applied by
# tokenizer wraps in <|begin_of_sentence|><|User|>...<|Assistant|>.
SYSTEM = ""  # DSP-V2 doesn't use a system message in its training format
USER_TEMPLATE = (
    "Complete the following Lean 4 code:\n\n"
    "```lean4\n"
    "{code}\n"
    "```\n\n"
    "Before producing the Lean 4 code to formally prove the given theorem, "
    "provide a detailed proof plan outlining the main proof steps and "
    "strategies.\n"
    "The plan should highlight key ideas, intermediate lemmas, and proof "
    "structures that will guide the construction of the final formal proof."
)

_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)


@dataclass
class StatementProblem:
    name: str
    file_path: str
    full_text: str   # the entire .lean file as shipped, ending in `:= sorry`
    header: str      # everything before `theorem <name>` — imports/opens/docstrings


def load_problems(dir_path: str) -> List[StatementProblem]:
    out = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        out.append(StatementProblem(
            name=name, file_path=path, full_text=text,
            header=text[:m.start()],
        ))
    return out


def build_prompt(prob: StatementProblem) -> str:
    """Replace any trailing `sorry` with `:= by sorry` to standardize, then
    drop into the DSP-V2 user template."""
    code = prob.full_text.rstrip()
    # PutnamBench uses `:= sorry` (no `by`), ProofNet ditto. Either elaborates
    # but DSP-V2 saw `:= by sorry` more in training; normalize.
    code = re.sub(r':=\s*sorry\s*$', ':= by sorry', code, flags=re.MULTILINE)
    return USER_TEMPLATE.format(code=code)


def extract_proof(text: str) -> str:
    """Extract the last fenced lean4 block containing a tactic-proof theorem.
    DSP-V2 emits just the theorem (no `import` line) inside ```lean4 ... ```,
    so we don't require an import — that's the caller's job to prepend."""
    blocks = _FENCE_RE.findall(text)
    valid = [
        b for b in blocks
        if "by" in b and ("theorem" in b or "example" in b)
    ]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=16384, temperature=1.0):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_msg}],
        temperature=temperature, max_tokens=max_tokens,
    )
    raw = r.choices[0].message.content or ""
    u = r.usage
    return raw, (u.completion_tokens if u else None)


def verify(server_url: str, code: str, timeout: int = 180):
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    msgs = r.json()["results"][0].get("response", {}).get("messages", [])
    errs = [m for m in msgs if m.get("severity") == "error"]
    return len(errs) == 0, errs


def process(prob: StatementProblem, client, model, server_url: str,
            k: int, log_path: str, out_dir: str,
            raw_dir: Optional[str] = None) -> tuple:
    user_msg = build_prompt(prob)
    attempts, any_pass = [], False
    passing_proof = None
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tok = generate(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"})
            continue
        if raw_dir:
            with open(os.path.join(raw_dir, f"{prob.name}.k{i}.txt"), "w") as f:
                f.write(raw)
        proof_block = extract_proof(raw)
        if not proof_block:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tok})
            continue
        # Reattach the original problem's header (import + opens + docstring)
        # since the model's fenced output omits it.
        proof = prob.header.rstrip() + "\n\n" + proof_block + "\n"
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
            passing_proof = proof
            break
    if any_pass and passing_proof:
        with open(os.path.join(out_dir, f"{prob.name}.lean"), "w") as f:
            f.write(passing_proof)
    rec = {
        "target": prob.name, "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool-dir", required=True,
                    help="dir of .lean statement files")
    ap.add_argument("--out-dir", required=True,
                    help="dir to write passing .lean files")
    ap.add_argument("--raw-dir", default=None,
                    help="if set, write each model attempt's raw text to "
                         "<raw-dir>/<name>.k<i>.txt for post-hoc reprocessing")
    ap.add_argument("--log", required=True, help="JSONL log path")
    ap.add_argument("--k", type=int, default=8,
                    help="attempts per problem")
    ap.add_argument("--n", type=int, default=0,
                    help="if >0, limit pool size (for dev)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--prover-url", default=PROVER_URL_DEFAULT)
    ap.add_argument("--prover-model", default=PROVER_MODEL_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    if args.raw_dir:
        os.makedirs(args.raw_dir, exist_ok=True)
    open(args.log, "w").close()

    problems = load_problems(args.pool_dir)
    if args.n > 0:
        problems = problems[: args.n]
    print(f"Pool: {len(problems)} problems from {args.pool_dir}")
    print(f"Prover: {args.prover_url}  model={args.prover_model}")
    print(f"Verifier: {args.server_url}  k={args.k}  workers={args.workers}")
    print(f"Out: log={args.log}  proofs={args.out_dir}\n")

    client = OpenAI(base_url=args.prover_url, api_key="EMPTY")

    t0 = time.time()
    passed = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {
            ex.submit(process, p, client, args.prover_model,
                      args.server_url, args.k, args.log, args.out_dir,
                      args.raw_dir): p
            for p in problems
        }
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            if ok:
                passed += 1
            tag = "PASS" if ok else "FAIL"
            print(f"  [{done:4d}/{len(problems)}] {tag}  {name[:50]:50s}  "
                  f"k={kt}  (running {passed}/{done})", flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
