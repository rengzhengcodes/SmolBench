"""Audit v6 parseability with per-premise verify+drop. Also record file
lengths and premise-kept fractions so we can compare against v5."""
import sys, os, requests
from collections import Counter
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from sb_kimina_ext_v6 import build_file as build_v6
from sb_kimina_ext_v5 import build_file as build_v5
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
    with_doc = False
    d = int(cond.split("d")[-1]) if "-d" in cond else 1
    ok_v6 = ok_v5 = 0
    len_v6 = len_v5 = 0
    kept_total = 0
    considered_total = 0
    for t in targets:
        # v5 build (no filter)
        f5 = build_v5(t["full_name"], corpus, traced, cond, with_doc, d)
        if f5:
            len_v5 += len(f5)
            if verify(f5): ok_v5 += 1
        # v6 build (with per-premise filter)
        stats: dict = {}
        f6 = build_v6(t["full_name"], corpus, traced, cond, with_doc, d,
                      server_url=SERVER, premise_filter_stats=stats)
        kept, considered = stats.get(t["full_name"], (0, 0))
        kept_total += kept
        considered_total += considered
        if f6:
            len_v6 += len(f6)
            if verify(f6): ok_v6 += 1
    avg5 = len_v5 / max(len(targets), 1)
    avg6 = len_v6 / max(len(targets), 1)
    keep_frac = kept_total / max(considered_total, 1)
    print(f"  {cond:18s}  v5 parse={ok_v5:2d}/{len(targets)} avg_len={avg5:.0f}    "
          f"v6 parse={ok_v6:2d}/{len(targets)} avg_len={avg6:.0f}   "
          f"premises_kept={kept_total}/{considered_total} ({100*keep_frac:.0f}%)",
          flush=True)
