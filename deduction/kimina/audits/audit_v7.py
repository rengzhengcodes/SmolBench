"""Audit v7: statement-extensional (type-deps) with per-premise verify+drop.
Measures parseability AND average file length for intensional, d1, d2, d4."""
import sys, os, requests
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from sb_kimina_ext_v7 import build_file
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
        return not any(m.get("severity") == "error" for m in msgs)
    except Exception:
        return False


for cond in ["intensional", "ext-nodoc-d1", "ext-nodoc-d2", "ext-nodoc-d4"]:
    d = int(cond.split("d")[-1]) if "-d" in cond else 0
    ok = 0
    total_len = 0
    kept_total = 0
    considered_total = 0
    for t in targets:
        stats: dict = {}
        f = build_file(t["full_name"], corpus, traced, cond,
                       with_doc=False, depth=max(d, 1),
                       server_url=SERVER, premise_filter_stats=stats)
        kept, considered = stats.get(t["full_name"], (0, 0))
        kept_total += kept
        considered_total += considered
        if f:
            total_len += len(f)
            if verify(f): ok += 1
    avg = total_len / max(len(targets), 1)
    keep_frac = kept_total / max(considered_total, 1)
    print(f"  {cond:18s}  parses={ok:2d}/{len(targets)}  avg_len={avg:.0f}  "
          f"premises_kept={kept_total}/{considered_total} ({100*keep_frac:.0f}%)",
          flush=True)
