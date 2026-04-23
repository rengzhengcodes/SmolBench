"""Audit miniF2F v7 extractor: parseability + length at intensional, d1, d4.
Uses a sample (first 30 problems) so it doesn't block vLLM."""
import sys, os, requests
sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from sb_kimina_minif2f_v7 import load_problems, build_mf2f_file, mf2f_type_deps
from deduction.inspect import BENCHMARK_DIR, load_corpus

SERVER = "http://localhost:9000"
corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
problems = load_problems()
SAMPLE = 30  # representative sample, not all 197
problems = problems[:SAMPLE]
print(f"pool (sample): {len(problems)}")


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
    kept_total = considered_total = 0
    for p in problems:
        stats: dict = {}
        code, k, c = build_mf2f_file(p, corpus, cond, with_doc=False,
                                     depth=max(d, 1), server_url=SERVER,
                                     stats=stats)
        kept_total += k
        considered_total += c
        total_len += len(code)
        if verify(code): ok += 1
    avg = total_len / max(len(problems), 1)
    keep_frac = kept_total / max(considered_total, 1) if considered_total else 0
    print(f"  {cond:18s}  parses={ok:2d}/{len(problems)}  avg_len={avg:.0f}  "
          f"premises_kept={kept_total}/{considered_total} ({100*keep_frac:.0f}%)",
          flush=True)

# Also show extracted deps for a few problems
print("\n=== sample type-deps ===")
for p in problems[:5]:
    deps = mf2f_type_deps(p, corpus)
    print(f"  {p.name[:40]:40s}  deps={deps[:8]}  ({len(deps)} total)")
