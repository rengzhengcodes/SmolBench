"""Check the survivorship claim on ministral-3-14b's re-collected seeds.

Claim under test: the 7 re-collected seeds (19, 24-29) run 62-79% empty
responses against 11-36% on the 23 that landed pre-fix, confined to the
cap-length arms, with the noise arm identical across groups. If true, shipping
at R=23 would have baked a LENGTH-SELECTION bias into the lane -- the seeds
that landed are the ones whose draws capped out least -- and the re-collection
removed it rather than introducing an inhomogeneity.
"""
import sys
from pathlib import Path

sys.path.insert(0, "/workspace/SmolBench/notebooks/induction")
import yaml
from response_audit import TagIgnoringLoader

RESULTS = Path("/workspace/SmolBench/notebooks/induction/results")
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
