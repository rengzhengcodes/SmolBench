"""Audit v3 parseability: per-premise file context collection."""
import sys, os, requests
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from sb_kimina_ext_v3 import build_file
from deduction.inspect import BENCHMARK_DIR, load_corpus, load_traced_lookup
from deduction.pool_runner import pilot_pool

corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
traced = load_traced_lookup()
targets = pilot_pool(corpus, traced, max_n=73)
print(f"pool: {len(targets)}")

for cond in ["intensional", "ext-nodoc-d1", "ext-nodoc-d2", "ext-nodoc-d4",
             "ext-doc-d1", "ext-doc-d4"]:
    with_doc = "-doc-" in cond and "nodoc" not in cond
    d = int(cond.split("d")[-1]) if "-d" in cond else 1
    ok = 0
    file_chars_total = 0
    for t in targets:
        f = build_file(t["full_name"], corpus, traced, cond, with_doc, d)
        if f is None: continue
        file_chars_total += len(f)
        try:
            r = requests.post(
                "http://localhost:9000/verify",
                json={"codes": [{"custom_id": "x", "proof": f}]},
                timeout=120,
            )
            msgs = r.json()["results"][0].get("response", {}).get("messages", [])
            errs = [m for m in msgs if m.get("severity") == "error"]
            if not errs: ok += 1
        except Exception:
            pass
    print(f"  {cond:18s}  parses={ok:2d}/{len(targets)}  "
          f"avg_len={file_chars_total/max(len(targets),1):.0f}")
