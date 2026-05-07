"""miniF2F driver using v8's target-signature unfolding.

Difference from minif2f_v7:
  - v7 prepends helper definitions as floating padding; the target
    signature is unchanged and uses real Mathlib names. Helpers are
    informational only, not load-bearing for the proof.
  - v8 REWRITES the target's signature itself, substituting each
    Mathlib name with the body of its `#print` output (parenthesized).
    The theorem is now stated in unfolded Lean — the model must
    actually engage with the substituted bodies.

Pipeline:
  1. Read the miniF2F `.lean` file. Extract the theorem signature text
     (everything between `theorem <name>` and the body's `:=`).
  2. Substitute Mathlib names recursively up to depth d, using
     `unfold_signature` from v8 (which queries kimina-lean-server's
     `#print`).
  3. Emit:  import Mathlib + opens + `example : <unfolded_sig> := by sorry`

Caveats (same as v8 on SmolBench):
  - Names backed by `structure`/`class`/`inductive` have no `:=` body,
    so `extract_def_body` returns None for those and the original name
    is left in place. Bounds how much can be unfolded.
  - Some substitutions break instance/lemma resolution because
    typeclass resolution doesn't see through the (now anonymous,
    substituted) form. Expected drop in pass rate at higher depth is
    the compound effect of (text dilution + lost lemma transfer).
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
from typing import List, Optional, Tuple

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus
from deduction.kimina.v8_unfolded import unfold_signature

MINIF2F_DIR = "/tmp/minif2f_test_solved/src"
SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"
SYSTEM = ("You are an expert programmer and mathematician who helps "
          "formalizing mathematical problems in Lean 4.")
USER_PREFIX = ("Think about and solve the following problems step by "
               "step in Lean 4.\n\n")
_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)


@dataclass
class MF2FProblem:
    name: str
    file_path: str
    file_text: str
    theorem_src: str   # full text from `theorem` to end of file
    sig_text: str      # signature (binders + return type), no body
    theorem_line: int
    opens: List[str]


def _split_signature(thm_src: str) -> str:
    """Given the full theorem source, return everything between
    `theorem <name>` and the top-level `:=` (i.e., binders + return type).
    Strips the leading `theorem <name>` keyword + name."""
    # Find the body start: top-level `:=` outside brackets.
    depth = 0
    i = 0
    body_idx = -1
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
    if body_idx == -1:
        head = thm_src
    else:
        head = thm_src[:body_idx]
    # Strip leading `theorem <name>`
    m = re.match(r'\s*theorem\s+[A-Za-z0-9_\']+\s*', head)
    if m:
        head = head[m.end():]
    return head.strip()


def load_problems(dir_path: str = MINIF2F_DIR) -> List[MF2FProblem]:
    probs = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        line = text[:m.start()].count("\n") + 1
        thm_src = text[m.start():].rstrip()
        sig_text = _split_signature(thm_src)
        opens = []
        for ln in text.splitlines()[:line - 1]:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        probs.append(MF2FProblem(
            name=name, file_path=path, file_text=text,
            theorem_src=thm_src, sig_text=sig_text,
            theorem_line=line, opens=opens,
        ))
    return probs


def build_mf2f_v8_file(
    prob: MF2FProblem, corpus, condition: str, depth: int = 1,
    server_url: str = SERVER_DEFAULT,
) -> str:
    """Build a Lean prompt file with the target signature unfolded to
    depth d (intensional = depth 0, no substitution)."""
    if condition == "intensional":
        body_sig = prob.sig_text
    else:
        body_sig = unfold_signature(prob.sig_text, depth, corpus, server_url)

    opens_line = ""
    if prob.opens:
        opens_line = "open " + " ".join(prob.opens) + "\n"

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + opens_line
        + "\n"
        + f"example {body_sig} := by sorry\n"
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [
        b for b in blocks
        if all(k in b for k in ("by", ":=", "import"))
        and ("theorem" in b or "example" in b)
    ]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=128000, temperature=0.1):
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


def process(prob, corpus, condition, depth, client, model, server_url,
            k, log_path):
    code = build_mf2f_v8_file(prob, corpus, condition, depth=depth,
                              server_url=server_url)
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
        "target": prob.name, "condition": condition, "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    cond = args.condition
    if cond == "intensional":
        depth = 0
    elif cond.startswith("ext-nodoc-d"):
        depth = int(cond.split("-d")[-1])
    else:
        sys.exit(f"bad condition: {cond}")

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    problems = load_problems()
    if args.n > 0:
        problems = problems[:args.n]
    print(f"condition={cond}  pool={len(problems)}  k={args.k}  "
          f"workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {ex.submit(process, p, corpus, cond, depth,
                        client, args.model, args.server_url, args.k,
                        args.log): p
              for p in problems}
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(problems)
            tag = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"  [{done:3d}/{n}] {tag}  {name[:55]:55s}  k={kt}  "
                  f"(running {passed}/{done})", flush=True)

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
