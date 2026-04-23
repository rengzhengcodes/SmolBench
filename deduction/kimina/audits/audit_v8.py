"""Audit v8 unfolded-signature parseability and length at intensional,
d1, d2, d4 for the 73-target pool.

For each failed build, categorize the first error so we can see what the
compound effect (text length + lost lemma transfer) actually breaks:
 - synth_fail: typeclass instance not found (lost transfer through the
   semi-reducible def)
 - unknown_id: a name in the unfolded signature isn't resolved (missing
   namespace, private, etc.)
 - parse_fail: malformed Lean (our text substitution produced garbage)
 - other
"""
import sys, os
from collections import Counter
import requests
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.kimina.v8_unfolded import build_file
from deduction.inspect import BENCHMARK_DIR, load_corpus, load_traced_lookup
from deduction.pool_runner import pilot_pool

SERVER = "http://localhost:9000"
corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
traced = load_traced_lookup()
targets = pilot_pool(corpus, traced, max_n=73)
print(f"pool: {len(targets)}")


def verify(code, timeout=120):
    try:
        r = requests.post(f"{SERVER}/verify",
                          json={"codes": [{"custom_id": "x", "proof": code}]},
                          timeout=timeout)
        msgs = r.json()["results"][0].get("response", {}).get("messages", [])
        errs = [m for m in msgs if m.get("severity") == "error"]
        return (not errs, errs)
    except Exception as e:
        return (False, [{"data": f"exception: {e}"}])


def bucket(err_data: str) -> str:
    s = err_data.lower()
    if "failed to synthesize" in s: return "synth_fail"
    if "unknown identifier" in s or "unknown constant" in s: return "unknown_id"
    if "unexpected token" in s or "expected" in s and "got" in s: return "parse_fail"
    if "type mismatch" in s: return "type_mismatch"
    return "other"


for cond in ["intensional", "ext-nodoc-d1", "ext-nodoc-d2", "ext-nodoc-d4"]:
    d = int(cond.split("-d")[-1]) if "-d" in cond else 0
    ok = 0
    total_len = 0
    errs = Counter()
    for t in targets:
        code = build_file(t["full_name"], corpus, cond, depth=max(d, 1),
                          server_url=SERVER)
        if code is None:
            errs["build_none"] += 1
            continue
        total_len += len(code)
        parses, es = verify(code)
        if parses:
            ok += 1
        else:
            first = str(es[0].get("data", ""))[:120] if es else ""
            errs[bucket(first)] += 1
    avg = total_len / max(len(targets), 1)
    print(f"  {cond:18s}  parses={ok:2d}/{len(targets)}  "
          f"avg_len={avg:.0f}  errs={dict(errs)}", flush=True)
