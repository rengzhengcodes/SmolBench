"""Audit v4 parseability: stack-aware per-premise scope reconstruction."""
import sys, os, requests
from collections import Counter
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from sb_kimina_ext_v4 import build_file
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
    err_samples = Counter()
    for t in targets:
        f = build_file(t["full_name"], corpus, traced, cond, with_doc, d)
        if f is None:
            continue
        try:
            r = requests.post("http://localhost:9000/verify",
                              json={"codes": [{"custom_id": "x", "proof": f}]},
                              timeout=120)
            msgs = r.json()["results"][0].get("response", {}).get("messages", [])
            errs = [m for m in msgs if m.get("severity") == "error"]
            if not errs:
                ok += 1
            else:
                msg = str(errs[0].get("data"))[:120].lower()
                if "already been declared" in msg: err_samples["universe_dup"] += 1
                elif "redundant binder" in msg: err_samples["redundant_binder"] += 1
                elif "simp made no progress" in msg: err_samples["simp"] += 1
                elif "rewrite" in msg and "failed" in msg: err_samples["rewrite"] += 1
                elif "type mismatch" in msg: err_samples["type_mismatch"] += 1
                elif "failed to synthesize" in msg: err_samples["synth"] += 1
                elif "unknown" in msg: err_samples["unknown"] += 1
                elif "invalid 'end'" in msg: err_samples["bad_end"] += 1
                elif "unsolved" in msg: err_samples["unsolved"] += 1
                else: err_samples["other"] += 1
        except Exception:
            err_samples["exception"] += 1
    print(f"  {cond:18s}  parses={ok:2d}/{len(targets)}  errs={dict(err_samples)}",
          flush=True)
