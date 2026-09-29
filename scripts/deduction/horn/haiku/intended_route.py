"""Intended route of every written proof: which heads it derives (lemma heads vs tree
intermediates), whether the proof succeeded, and its length.

usage: intended_route.py <rung_dir> [<rung_dir> ...]
"""
import collections, json, random, re, sys
from pathlib import Path
from smolbench.deduction.horn.theory import Theory

def classify(root):
    rows = [json.loads(l) for l in (root / "scores.jsonl").read_text().splitlines()]
    th = {}
    out = []
    for r in rows:
        t = th.get(r["seed"])
        if t is None:
            t = th[r["seed"]] = Theory.from_json((root / f"s{r['seed']:04d}" / "theory.json").read_text())
        lem_heads = {lm.head for lm in t.library}
        tree = {p for lm in t.library for k, p in lm.node_pred.items() if 0 < len(k) < lm.height}
        f = root / f"s{r['seed']:04d}" / r["arm"] / f"answer.s{r['sample']}.md"
        heads = [m.group(1) for m in re.finditer(r"^\s*derive\s+(\w+)", f.read_text(), re.M)]
        n_tree = sum(h in tree for h in heads)
        kind = "none" if not heads else ("tree" if n_tree else "lemma")
        out.append((r["arm"], r["seed"], kind, r["verdict"] == "success", len(heads), n_tree, r.get("reason", "")))
    return out

for d in sys.argv[1:]:
    root = Path(d)
    out = classify(root)
    print(f"## {root.name}: pass rate by intended route (any tree-intermediate head => tree)")
    ladder = ("lem", "pad", "junk", "disc", "both")
    arms = sorted({o[0] for o in out}, key=lambda a: ladder.index(a) if a in ladder else 9)
    print(f"{'arm':7s} {'n':>3s} {'pass':>6s} | {'lemma-only':>16s} {'via tree':>16s} {'none':>5s} | mean written steps lemma / tree")
    for a in arms:
        rs = [o for o in out if o[0] == a]
        by = collections.defaultdict(list); ln = collections.defaultdict(list)
        for o in rs: by[o[2]].append(o[3]); ln[o[2]].append(o[4])
        def cell(k):
            v = by.get(k, []); return f"{sum(v):3d}/{len(v):<3d}{(100*sum(v)/len(v)) if v else 0:5.0f}%"
        ml = lambda k: f"{sum(ln[k])/len(ln[k]):.1f}" if ln.get(k) else "-"
        print(f"{a:7s} {len(rs):3d} {100*sum(o[3] for o in rs)/len(rs):5.1f}% | {cell('lemma'):>16s} {cell('tree'):>16s} {len(by.get('none',[])):5d} | {ml('lemma')} / {ml('tree')}")
    # seed-paired contrast of both vs pad and lem
    cells = collections.defaultdict(lambda: collections.defaultdict(list))
    for o in out: cells[o[0]][o[1]].append(o[3])
    random.seed(0)
    def boot(d, B=5000):
        bs = sorted(100*sum(random.choice(d) for _ in d)/len(d) for _ in range(B)); return 100*sum(d)/len(d), bs[int(.025*B)], bs[int(.975*B)]
    for a, b in (("both","pad"),("both","junk"),("both","disc"),("pad","lem")):
        if a in cells and b in cells:
            A = {s: sum(v)/len(v) for s, v in cells[a].items()}; Bm = {s: sum(v)/len(v) for s, v in cells[b].items()}
            ks = sorted(set(A) & set(Bm)); m, lo, hi = boot([A[k]-Bm[k] for k in ks])
            print(f"  {a} - {b}: {m:+.1f} [{lo:+.1f}, {hi:+.1f}]")
    print()
