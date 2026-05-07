"""Audit v9 chained-abbrev parseability + length on miniF2F."""
import sys, os
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
import requests
from collections import Counter

from deduction.kimina.minif2f_v9 import load_problems, build_mf2f_v9_file
from deduction.inspect import BENCHMARK_DIR, load_corpus

SERVER = "http://localhost:9000"
corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
problems = load_problems()
print(f"pool: {len(problems)}")


def verify(code, timeout=180):
    try:
        r = requests.post(f"{SERVER}/verify",
                          json={"codes": [{"custom_id": "x", "proof": code}]},
                          timeout=timeout)
        msgs = r.json()["results"][0].get("response", {}).get("messages", [])
        errs = [m for m in msgs if m.get("severity") == "error"]
        return (not errs), errs
    except Exception as e:
        return False, [{"data": f"exception: {e}"}]


def bucket(err: str) -> str:
    s = err.lower()
    if "unexpected token" in s or ("expected" in s and "got" in s): return "parse"
    if "failed to synthesize" in s: return "synth"
    if "unknown" in s: return "unknown_id"
    if "type mismatch" in s: return "type_mismatch"
    if "redundant binder" in s: return "redundant_binder"
    return "other"


for cond in ["intensional", "ext-nodoc-d1", "ext-nodoc-d2", "ext-nodoc-d4"]:
    if cond == "intensional":
        d = 0
    else:
        d = int(cond.split("-d")[-1])
    ok = 0
    total_len = 0
    err_buckets = Counter()
    samples = []
    for p in problems:
        code = build_mf2f_v9_file(p, corpus, cond, depth=d, server_url=SERVER)
        total_len += len(code)
        parses, errs = verify(code)
        if parses:
            ok += 1
        else:
            first = str(errs[0].get("data", ""))[:120] if errs else ""
            err_buckets[bucket(first)] += 1
            if len(samples) < 3 and cond != "intensional":
                samples.append((p.name, first))
    avg = total_len / max(len(problems), 1)
    print(f"  {cond:18s}  parses={ok:3d}/{len(problems)}  avg_len={avg:.0f}  "
          f"errs={dict(err_buckets)}", flush=True)
    if samples:
        for nm, e in samples:
            print(f"    sample fail: {nm[:40]:40s}  {e[:90]}")
