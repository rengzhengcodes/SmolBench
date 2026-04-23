"""SmolBench × Kimina-Prover pilot using the v2 file builder that includes
preceding namespace/variable/open context from Mathlib. Conditions supported:
  - intensional (i): bare target, no extensional premises.
  - ext-nodoc-dN: premises expanded to depth N as renamed Lean lemmas.
  - ext-doc-dN:   same with docstrings preserved.

This script runs only the `i` (intensional) condition to calibrate: how many
of our 73 replay-passing targets can Kimina solve with bare `import Mathlib`
access?
"""
import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import time
import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import (
    BENCHMARK_DIR, MATHLIB_DIR, load_corpus, load_traced_lookup, source_text,
)
from deduction.pool_runner import pilot_pool

SYSTEM = "You are an expert programmer and mathematician who helps formalizing mathematical problems in Lean 4."
USER_PREFIX = "Think about and solve the following problems step by step in Lean 4.\n\n"

_NAMED_DECL_RE = re.compile(r'^(\s*)(?:@\[[^\]]*\]\s*)?(?:theorem|lemma)\s+\S+', re.MULTILINE)
_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_CTX_PREFIXES = ("namespace ", "section ", "end ", "end\n", "variable ", "variable{",
                 "variable(", "variable[", "open ", "open scoped ",
                 "universe ", "universes ")


def _replace_body_with_sorry(decl: str) -> str:
    depth = 0
    i = 0
    while i < len(decl) - 1:
        c = decl[i]
        if c == "[": depth += 1
        elif c == "]": depth -= 1
        elif depth == 0 and c == ":" and decl[i + 1] == "=":
            return decl[:i].rstrip() + " := by sorry\n"
        i += 1
    return decl.rstrip() + "\n"


def collect_context(file_text: str, theorem_line_zero_indexed: int) -> str:
    ctx = []
    lines = file_text.splitlines()
    for i in range(min(theorem_line_zero_indexed, len(lines))):
        l = lines[i]
        if l.strip().startswith(_CTX_PREFIXES):
            ctx.append(l)
    return "\n".join(ctx)


def build_kimina_file_intensional(full_name: str, corpus) -> str | None:
    p = corpus.get(full_name)
    if p is None:
        return None
    src = source_text(p)
    if not src:
        return None
    src_path = MATHLIB_DIR / p.file_path
    if not src_path.exists():
        return None
    file_text = src_path.read_text()
    ctx = collect_context(file_text, p.start[0] - 1)
    decl = _NAMED_DECL_RE.sub(r"\1example", src, count=1)
    decl = _replace_body_with_sorry(decl)
    return f"import Mathlib\n\n{ctx}\n\n{decl}\n"


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [b for b in blocks if all(k in b for k in ("by", ":=", "import"))
             and ("theorem" in b or "example" in b)]
    return valid[-1] if valid else ""


def generate_one(client, model, user_msg, max_tokens=14000, temperature=0.1):
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
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
    data = r.json()
    resp = data["results"][0].get("response", {})
    errs = [m for m in resp.get("messages", []) if m.get("severity") == "error"]
    return len(errs) == 0, errs


def process(target, corpus, client, model, server_url, k, log_path):
    fn = target["full_name"]
    kfile = build_kimina_file_intensional(fn, corpus)
    if kfile is None:
        rec = {"target": fn, "skip": "build_failed", "pass": False}
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return fn, False, 0, "build_failed"

    # First sanity: does the base parse at all?
    base_ok, base_errs = verify(server_url, kfile)
    if not base_ok:
        err_sample = str(base_errs[0].get("data"))[:150] if base_errs else ""
        rec = {"target": fn, "skip": "base_unparseable", "base_err": err_sample,
               "pass": False}
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return fn, False, 0, f"base:{err_sample[:60]}"

    user_msg = USER_PREFIX + kfile
    attempts = []
    any_pass = False
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tokens_out = generate_one(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"})
            continue
        proof = extract_kimina_proof(raw)
        if not proof:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tokens_out})
            continue
        try:
            ok, errs = verify(server_url, proof)
        except Exception as e:
            attempts.append({"k": i, "error": f"ver:{str(e)[:80]}"})
            continue
        attempts.append({
            "k": i, "ok": ok, "tokens_out": tokens_out,
            "first_err": (str(errs[0].get("data"))[:200] if errs else None),
            "wall_ms": int((time.perf_counter() - t0) * 1000),
        })
        if ok:
            any_pass = True
            break

    rec = {"target": fn, "condition": "intensional", "k_tried": len(attempts),
           "pass": any_pass, "attempts": attempts}
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return fn, any_pass, len(attempts), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n-targets", type=int, default=73)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default="http://localhost:8010/v1")
    ap.add_argument("--server-url", default="http://localhost:9000")
    ap.add_argument("--model", default="AI-MO/Kimina-Prover-72B")
    ap.add_argument("--log", default="/opt/dlami/nvme/sb/sb_kimina_v2_intensional.jsonl")
    args = ap.parse_args()

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced = load_traced_lookup()
    targets = pilot_pool(corpus, traced, max_n=args.n_targets)
    print(f"pool={len(targets)}  k={args.k}  workers={args.workers}")
    print(f"vllm={args.vllm_url}  server={args.server_url}  log={args.log}")

    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = skipped = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {ex.submit(process, t, corpus, client, args.model,
                        args.server_url, args.k, args.log): t for t in targets}
        for fut in futs.as_completed(fm):
            fn, ok, kt, err = fut.result()
            if err:
                skipped += 1
                tag = "SKIP"
                extra = err[:50]
            elif ok:
                passed += 1
                tag = "PASS"
                extra = f"k={kt}"
            else:
                tag = "FAIL"
                extra = f"k={kt}"
            done = sum(1 for f in fm if f.done())
            n = len(targets)
            print(f"  [{done:2d}/{n}] {tag}  {fn[:55]:55s}  {extra}  "
                  f"(running {passed}/{done-skipped} attempted, {skipped} skipped)",
                  flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(targets)-skipped} attempted "
          f"= {100*passed/max(len(targets)-skipped,1):.1f}%   "
          f"({skipped} skipped as base-unparseable)")


if __name__ == "__main__":
    main()
