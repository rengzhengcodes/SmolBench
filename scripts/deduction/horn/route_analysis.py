"""Route taken by every attempt (successes and failures) and pass rate by route.

usage: route_analysis.py <rung_dir>
"""
import collections, json, random, re, sys
from pathlib import Path

root = Path(sys.argv[1])
rows = [json.loads(l) for l in (root / "scores.jsonl").read_text().splitlines()]
LADDER = ("lem", "pad", "junk", "disc", "both")
ARMS = sorted({r["arm"] for r in rows}, key=lambda a: LADDER.index(a) if a in LADDER else 9)

def why(r):
    s = r.get("reason") or ""
    if r["verdict"] == "success": return "ok"
    if "no library rule" in s: return "invented rule"
    if "premise not derived" in s: return "premise not derived"
    if "is about" in s: return "wrong constant"
    if "goal not derived" in s: return "incomplete"
    return r["verdict"]

print(f"{'arm':6s} {'n':>3s} {'pass':>6s} | attempts by route: short / mixed / long / none | pass by route")
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    ok = sum(r["verdict"] == "success" for r in rs)
    byr = collections.defaultdict(list)
    for r in rs: byr[r["route"] or "none"].append(r["verdict"] == "success")
    att = " / ".join(f"{len(byr.get(k, [])):2d}" for k in ("short", "mixed", "long", "none"))
    pr = "  ".join(f"{k}:{sum(v)}/{len(v)}" for k, v in byr.items() if k != "none")
    print(f"{a:6s} {len(rs):3d} {100*ok/len(rs):5.1f}% | {att} | {pr}")

print("\nfailure reasons by arm and route (route = kinds of rules used before the bad step)")
for a in ARMS:
    c = collections.Counter((r["route"] or "none", why(r)) for r in rows if r["arm"] == a and r["verdict"] != "success")
    if c: print(f"  {a:6s} " + ", ".join(f"{k[0]}/{k[1]}={v}" for k, v in sorted(c.items())))

print("\nsteps used before failure / proof length on success (mean)")
for a in ARMS:
    rs = [r for r in rows if r["arm"] == a]
    ok = [r["steps"] for r in rs if r["verdict"] == "success"]
    bad = [r["steps"] for r in rs if r["verdict"] != "success"]
    tree = [sum(k in ("axiom", "disc") for k in r["used_kinds"]) for r in rs]
    print(f"  {a:6s} success len {sum(ok)/max(1,len(ok)):5.1f}  failed at step {sum(bad)/max(1,len(bad)):5.1f}  tree-rule steps per attempt {sum(tree)/len(rs):5.1f}")

random.seed(0)
cells = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows: cells[r["arm"]][r["seed"]].append(r["verdict"] == "success")
def cm(a): return {s: sum(v)/len(v) for s, v in cells[a].items()}
def boot(d, B=5000):
    bs = sorted(100*sum(random.choice(d) for _ in d)/len(d) for _ in range(B))
    return 100*sum(d)/len(d), bs[int(.025*B)], bs[int(.975*B)]
print("\npaired contrasts (pp, 95% seed bootstrap)")
for a, b in (("both", "pad"), ("both", "junk"), ("both", "disc"), ("junk", "pad"), ("disc", "pad"), ("pad", "lem"), ("both", "lem")):
    if a in cells and b in cells:
        A, Bm = cm(a), cm(b); ks = sorted(set(A) & set(Bm))
        m, lo, hi = boot([A[k]-Bm[k] for k in ks])
        print(f"  {a} - {b}: {m:+.1f} [{lo:+.1f}, {hi:+.1f}]")
