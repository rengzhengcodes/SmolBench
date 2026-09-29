"""Paired analysis of a rung: per-arm pass@1, seed-paired contrasts, route split, proof length.

usage: pilot_analysis.py <pilot_dir>
"""
import collections, json, random, sys
from pathlib import Path

root = Path(sys.argv[1])
rows = [json.loads(l) for l in (root / "scores.jsonl").read_text().splitlines()]
cells = collections.defaultdict(lambda: collections.defaultdict(list))  # arm -> seed -> [pass]
routes = collections.defaultdict(collections.Counter)
verd = collections.defaultdict(collections.Counter)
for r in rows:
    ok = r["verdict"] == "success"
    cells[r["arm"]][r["seed"]].append(ok)
    verd[r["arm"]][r["verdict"]] += 1
    if ok:
        routes[r["arm"]][r["route"]] += 1
print(f"{'arm':8s} {'n':>3s} {'pass@1':>7s} {'pass@3':>7s}  verdicts / routes")
for arm in sorted(cells):
    xs = [x for v in cells[arm].values() for x in v]
    p3 = sum(any(v) for v in cells[arm].values())
    print(f"{arm:8s} {len(xs):3d} {100*sum(xs)/len(xs):6.1f}% {p3:4d}/{len(cells[arm])}  {dict(verd[arm])}  {dict(routes[arm]) if routes[arm] else ''}")

random.seed(0)
def boot(d, B=5000):
    m = 100 * sum(d) / len(d); bs = []
    for _ in range(B):
        s = [d[random.randrange(len(d))] for _ in d]; bs.append(100 * sum(s) / len(s))
    bs.sort(); return m, bs[int(0.025 * B)], bs[int(0.975 * B)]
def cm(arm): return {s: sum(v) / len(v) for s, v in cells[arm].items()}
def signflip_p(d):
    """Exact two-sided sign-flip permutation p-value for a paired mean of n differences."""
    import itertools
    n = len(d); obs = abs(sum(d))
    hits = sum(abs(sum(x * s for x, s in zip(d, signs))) >= obs - 1e-12 for signs in itertools.product((1, -1), repeat=n))
    return hits / 2 ** n
print("\npaired contrasts (cell means, pp, 95% seed bootstrap; sign-flip permutation p)")
for a, b in (("both", "pad"), ("both", "junk"), ("both", "disc"), ("junk", "pad"), ("disc", "pad"), ("pad", "lem"), ("both", "lem")):
    if a in cells and b in cells:
        A, Bm = cm(a), cm(b); ks = sorted(set(A) & set(Bm))
        d = [A[k] - Bm[k] for k in ks]
        m, lo, hi = boot(d)
        print(f"  {a} - {b}: {m:+.1f} [{lo:+.1f}, {hi:+.1f}]  (n={len(ks)} seeds, sign-flip p={signflip_p(d):.3f})")
print("\nper-seed pass counts")
seeds = sorted({s for a in cells for s in cells[a]})
print("seed " + " ".join(f"{a:>7s}" for a in sorted(cells)))
for s in seeds:
    print(f"{s:4d} " + " ".join(f"{sum(cells[a].get(s, [])):3d}/{len(cells[a].get(s, [])):<3d}" for a in sorted(cells)))

# ---- proof length and a step budget (the Lean analog of a tactic/heartbeat cap)
import statistics
theory = json.loads(sorted(root.glob("s[0-9]*/theory.json"))[0].read_text())
m = theory["m"]
print(f"\nproof length among successes, and pass@1 under a step budget (m={m})")
print(f"{'arm':8s} {'mean':>6s} {'median':>7s} {'max':>4s}   {'<=1.0m':>7s} {'<=1.5m':>7s} {'<=2.0m':>7s} {'<=3.0m':>7s}")
for arm in sorted(cells):
    ok = [r for r in rows if r["arm"] == arm and r["verdict"] == "success"]
    n = sum(len(v) for v in cells[arm].values())
    st = [r["steps"] for r in ok]
    caps = []
    for f in (1.0, 1.5, 2.0, 3.0):
        caps.append(100 * sum(1 for r in ok if r["steps"] <= f * m) / n)
    if st:
        print(f"{arm:8s} {statistics.mean(st):6.1f} {statistics.median(st):7.1f} {max(st):4d}   " + " ".join(f"{c:6.1f}%" for c in caps))
