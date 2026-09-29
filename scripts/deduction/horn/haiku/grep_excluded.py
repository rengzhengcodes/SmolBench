"""Per-arm pass rates with and without the cells whose solver used a tool other than Read.
usage: grep_excluded.py <rung_dir> <workflow_dir> [<workflow_dir> ...]
"""
import collections, glob, json, random, sys
from pathlib import Path
root = Path(sys.argv[1]); wfs = [Path(w) for w in sys.argv[2:]]
searched = set()
for wf in wfs:
    lab = {}
    for l in (wf / "journal.jsonl").read_text().splitlines():
        j = json.loads(l)
        if j.get("type") == "started": lab[j.get("agentId")] = j.get("label") or ""
    for aid, label in lab.items():
        fs = glob.glob(str(wf / f"*{aid}*.jsonl"))
        if not fs: continue
        for line in open(fs[0], encoding="utf-8", errors="replace"):
            try: j = json.loads(line)
            except json.JSONDecodeError: continue
            msg = j.get("message") or {}
            if msg.get("role") != "assistant": continue
            if any(p.get("type") == "tool_use" and p.get("name") not in ("Read", "StructuredOutput") for p in msg.get("content") or []):
                parts = label.split(); 
                if len(parts) == 3: searched.add((parts[0], int(parts[1][1:]), int(parts[2][1:])))
                break
rows = [json.loads(l) for l in (root / "scores.jsonl").read_text().splitlines()]
random.seed(0)
def table(rows, title):
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows: cells[r["arm"]][r["seed"]].append(r["verdict"] == "success")
    print(title)
    for a in sorted(cells):
        xs = [x for v in cells[a].values() for x in v]
        print(f"  {a:7s} {sum(xs):3d}/{len(xs):<3d} {100*sum(xs)/len(xs):5.1f}%")
    def cm(a): return {s: sum(v)/len(v) for s, v in cells[a].items()}
    for a, b in (("both", "pad"), ("both", "junk"), ("both", "disc"), ("pad", "lem")):
        if a in cells and b in cells:
            A, B = cm(a), cm(b); ks = sorted(set(A) & set(B)); d = [A[k]-B[k] for k in ks]
            B = 5000
            bs = sorted(100*sum(random.choice(d) for _ in d)/len(d) for _ in range(B))
            print(f"  {a} - {b}: {100*sum(d)/len(d):+.1f} [{bs[int(0.025*B)]:+.1f}, {bs[int(0.975*B)]:+.1f}] (n={len(ks)})")
table(rows, f"{root.name}: all cells ({len(rows)})")
kept = [r for r in rows if (r["arm"], r["seed"], r["sample"]) not in searched]
print(f"  searched cells: {len(searched)} -> " + ", ".join(f"{a}:{n}" for a, n in sorted(collections.Counter(s[0] for s in searched).items())))
table(kept, f"{root.name}: Read-only cells ({len(kept)})")
