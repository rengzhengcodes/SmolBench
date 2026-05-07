"""miniF2F driver for the proof-completion experiment.

Each problem comes with a reference proof. We give the model the first
N tactic-chunks of the reference proof and ask it to COMPLETE the rest.

Two-axis design:
  X (per-record): n_tactics_given = how many leading tactics are visible
  Lines: depth = how deep we expand abbrevs for names visible in the
                 theorem signature + given tactic prefix (0 = no expansion)

For the sanity check we only vary X at depth=0. Expectations:
  n=0:    pass rate ≈ standard intensional baseline (Kimina at ~75%)
  n=k>0:  pass rate ≥ baseline (more proof given can only help)
  n=full: pass rate ≈ 100% (model just echos the proof back)

Reference proofs source: DeepSeek-Prover-V2 minif2f-solutions.zip
(217 proofs of the 244-problem Test split).

Tactic chunking heuristic:
  The proof body starts after `:= by`. We identify the proof's base
  indent (= indent of the first non-blank line). A "tactic chunk" is
  one logical step: a line at the base indent (e.g., `have h := ...`,
  `apply foo`, `rw [bar]`, `<;> linarith`) plus any continuation
  lines indented deeper. We split on transitions back to the base
  indent.
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
from typing import List

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus

PROOFS_DIR = "/opt/dlami/nvme/test"
SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"

SYSTEM = ("You are an expert programmer and mathematician who helps "
          "formalizing mathematical problems in Lean 4.")
USER_PREFIX = (
    "Think about and solve the following problems step by step in "
    "Lean 4.\n\n"
)

_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)


@dataclass
class ProofProblem:
    name: str
    file_path: str
    sig_text: str       # binders + return type (no `theorem` keyword, no `:= by ...`)
    proof_body: str     # full text after `:= by`, including indentation
    tactics: List[str]  # proof_body split into tactic chunks
    opens: List[str]


def _split_signature(thm_src: str) -> str:
    """Return text from after `theorem <name>` up to the `:=` start."""
    depth = 0
    body_idx = -1
    i = 0
    while i < len(thm_src) - 1:
        c = thm_src[i]
        if c in "[({":
            depth += 1
        elif c in "])}":
            depth -= 1
        elif depth == 0 and c == ":" and thm_src[i + 1] == "=":
            body_idx = i
            break
        i += 1
    head = thm_src if body_idx == -1 else thm_src[:body_idx]
    m = re.match(r'\s*theorem\s+[A-Za-z0-9_\']+\s*', head)
    if m:
        head = head[m.end():]
    return head.strip(), body_idx


def _split_tactics(body: str) -> List[str]:
    """Split a `by ...` proof body into tactic chunks.

    Heuristic: identify the base indent (first non-blank line's leading
    whitespace). Each chunk starts at a line whose indent equals the
    base indent. Continuation lines (deeper indent or blank) attach to
    the preceding chunk.
    """
    lines = body.splitlines()
    # Skip leading blank lines
    while lines and not lines[0].strip():
        lines = lines[1:]
    if not lines:
        return []
    # Determine base indent
    base = len(lines[0]) - len(lines[0].lstrip())
    chunks: List[str] = []
    cur: List[str] = []
    for ln in lines:
        if not ln.strip():
            cur.append(ln)
            continue
        ind = len(ln) - len(ln.lstrip())
        # A line at base indent starts a new chunk if cur already has
        # any non-blank content (regardless of trailing blank lines).
        has_nonblank = any(l.strip() for l in cur)
        if ind == base and has_nonblank:
            chunks.append("\n".join(cur).rstrip())
            cur = [ln]
        else:
            cur.append(ln)
    if cur and any(l.strip() for l in cur):
        chunks.append("\n".join(cur).rstrip())
    return chunks


def load_problems(dir_path: str = PROOFS_DIR) -> List[ProofProblem]:
    probs = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        line = text[:m.start()].count("\n") + 1
        thm_src = text[m.start():].rstrip()
        sig, body_start = _split_signature(thm_src)
        if body_start == -1:
            continue
        # Body is everything after `:=`. We strip a leading ` by` if
        # present (Lean accepts both `:= by ...` and `:= ...term...`,
        # but for tactic proofs we split tactics).
        body_src = thm_src[body_start + 2:]
        body_src = body_src.lstrip()
        if body_src.startswith("by"):
            body_src = body_src[2:]
        # Now body_src is the contents of the by-block (sans the `by`).
        tactics = _split_tactics(body_src)
        opens = []
        for ln in text.splitlines()[:line - 1]:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        probs.append(ProofProblem(
            name=name, file_path=path, sig_text=sig,
            proof_body=body_src, tactics=tactics, opens=opens,
        ))
    return probs


def build_completion_file(prob: ProofProblem, n_given: int) -> str:
    """Build a Lean source file with the first `n_given` tactics of
    `prob`'s proof, leaving the rest for the model to complete.

    The file ends mid-proof; the model is expected to wrap a complete
    theorem in a fenced lean4 block."""
    if n_given <= 0:
        proof_section = "  sorry"
    elif n_given >= len(prob.tactics):
        # Full reference proof.
        proof_section = "\n".join(prob.tactics)
    else:
        prefix = "\n".join(prob.tactics[:n_given])
        proof_section = prefix + "\n  sorry"

    opens_line = ""
    if prob.opens:
        opens_line = "open " + " ".join(prob.opens) + "\n"

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + opens_line + "\n"
        + f"theorem {prob.name} {prob.sig_text} := by\n"
        + proof_section + "\n"
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [b for b in blocks
             if all(k in b for k in ("by", ":=", "import"))
             and ("theorem" in b or "example" in b)]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=32000, temperature=0.1):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user_msg}],
        temperature=temperature, max_tokens=max_tokens,
    )
    raw = r.choices[0].message.content or ""
    u = r.usage
    return raw, (u.completion_tokens if u else None)


def verify(server_url, code, timeout=180):
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    msgs = r.json()["results"][0].get("response", {}).get("messages", [])
    errs = [m for m in msgs if m.get("severity") == "error"]
    return len(errs) == 0, errs


def process(prob, n_given, client, model, server_url, k, log_path):
    code = build_completion_file(prob, n_given)
    # Single prompt for all conditions — the partial-proof prefix is
    # presented in the file but not flagged in any directive. If Kimina
    # ignores the prefix and re-derives, that's a valid failure mode.
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
    rec = {
        "target": prob.name, "n_given": n_given,
        "n_total_tactics": len(prob.tactics),
        "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-given", type=int, required=True,
                    help="Number of leading tactics to give. Use a sentinel "
                         "value of -1 to mean 'all (full proof)'.")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n-problems", type=int, default=0,
                    help="Limit pool size (0 = all)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    problems = load_problems()
    if args.n_problems > 0:
        problems = problems[:args.n_problems]

    print(f"n_given={args.n_given}  pool={len(problems)}  k={args.k}  "
          f"workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {}
        for p in problems:
            n = args.n_given if args.n_given >= 0 else len(p.tactics)
            fm[ex.submit(process, p, n, client, args.model,
                         args.server_url, args.k, args.log)] = p
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(problems)
            tag = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"  [{done:3d}/{n}] {tag}  {name[:55]:55s}  k={kt}  "
                  f"(running {passed}/{done})", flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
