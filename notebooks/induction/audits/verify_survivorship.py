"""Show the empty-response profile of ministral-3-14b's re-collected seeds vs the rest.

This measures the gap this lane's exclusion-bias caveat rests on: the 7
re-collected seeds (19, 24-29) against the 23 that landed before the
delivery fault, per arm. The expected shape is a large lift confined to
the arms whose draws reach the token cap. The noise arm, which does not
reach it, should stay unmoved.

WHAT THIS SHOWS, AND WHAT IT DOES NOT
-------------------------------------
This shows the GAP. It does not establish the mechanism. The frame is
MISSING-NOT-AT-RANDOM exclusion: the 7 re-collected seeds are intrinsically
cap-out-prone, which is why they could not finish inside the fault window.
The flat noise arm below rules out arm-uniform causes, but a length-mediated
per-process shift would spare the noise arm too. The evidence that pins the
mechanism is external to this script: server counters from inside the fault
window.
"""
import sys
from pathlib import Path

# Anchored on __file__, never an absolute checkout path: `response_audit`
# is this probe's own sibling under `audits/`, and `results/` sits one
# level up at the study root.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import yaml
from response_audit import TagIgnoringLoader

RESULTS = HERE.parent / "results"
REDONE = {19, 24, 25, 26, 27, 28, 29}
ARMS = ("intens", "extens", "noise_intens", "zero")

print(f"{'arm':14s} {'group':10s} {'seeds':>6s} {'marks':>6s} {'empty':>6s} "
      f"{'empty %':>8s}")
print("-" * 58)
summary = {}
for arm in ARMS:
    d = RESULTS / f"min3_14b_{arm}"
    for gname, want in (("pre-fix", False), ("re-run", True)):
        n = empty = seeds = 0
        for path in sorted(d.glob("rep_*.yaml")):
            seed = int(path.stem.split("_")[1])
            if (seed in REDONE) != want:
                continue
            seeds += 1
            for mark in yaml.load(path.read_text(), Loader=TagIgnoringLoader)["marks"]:
                r = mark.get("response") or ""
                n += 1
                if not str(r).strip():
                    empty += 1
        rate = empty / n if n else float("nan")
        summary[(arm, gname)] = rate
        print(f"{arm:14s} {gname:10s} {seeds:6d} {n:6d} {empty:6d} {rate:8.1%}")
    print()

print("DELTA (re-run minus pre-fix), in percentage points:")
for arm in ARMS:
    d = (summary[(arm, "re-run")] - summary[(arm, "pre-fix")]) * 100
    tag = "  <-- cap-length arm" if abs(d) > 15 else ""
    print(f"  {arm:14s} {d:+6.1f} pt{tag}")
