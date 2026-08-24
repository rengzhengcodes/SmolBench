"""Re-gate the local induction tree on CONTENT, under the EARLIEST-wins ruling.

The gate itself has to flip with the rule. The 2026-08-16 ruling
selects, per (model, seed, arm), the object with the MINIMUM run
timestamp. So a tree that matched the newest version, as the
pre-ruling gate certified, is now WRONG for the 140 multi-attempt
cells. Size discriminates them: the gemma-4-12b seed=8 extens pair is
922,083 vs 1,319,921 bytes.

Expected after the R=30 closure: 2,520 cells (21 models x 4 arms x 30
seeds), from 2,660 snapshot objects (2,520 + 140 duplicates).
"""
import re
import sys
from pathlib import Path

REPO = Path("/workspace/SmolBench")
KEYS = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "notebooks" / "induction"))
from run_study import MODELS as TAGS

RESULTS = REPO / "notebooks" / "induction" / "results"
RX = re.compile(r"induction/([^/]+)/seed=(\d+)/([a-z_]+)--(\d{8}T\d{6})Z\.yaml$")

attempts: dict[tuple, list] = {}
for line in KEYS.read_text().splitlines():
    size, key = line.split(None, 1)
    m = RX.search(key)
    if not m:
        continue
    cell = (m.group(1), int(m.group(2)), m.group(3))
    attempts.setdefault(cell, []).append((m.group(4), int(size)))

dupes = sum(1 for v in attempts.values() if len(v) > 1)
print(f"snapshot objects parsed : {sum(len(v) for v in attempts.values())}")
print(f"distinct cells          : {len(attempts)}")
print(f"cells with >1 attempt   : {dupes}")

ok = missing = stale = 0
bad = []
for (model, seed, arm), v in sorted(attempts.items()):
    v.sort()
    earliest_size = v[0][1]          # min timestamp == earliest, per the ruling
    local = RESULTS / f"{TAGS[model]}_{arm}" / f"rep_{seed}.yaml"
    if not local.exists():
        missing += 1
        bad.append(("MISSING", model, seed, arm, earliest_size, None))
    elif local.stat().st_size != earliest_size:
        stale += 1
        bad.append(("STALE", model, seed, arm, earliest_size,
                    local.stat().st_size))
    else:
        ok += 1

print(f"\nlocal == EARLIEST by size : {ok}")
print(f"missing locally           : {missing}")
print(f"NOT earliest (stale)      : {stale}")
for row in bad[:25]:
    print("   ", row)

seeds_per = {}
for (model, seed, arm) in attempts:
    seeds_per.setdefault(model, set()).add(seed)
uneven = {m: len(s) for m, s in seeds_per.items() if len(s) != 30}
print(f"\nlanes NOT at 30 seeds: {uneven if uneven else 'none -- all 21 at R=30'}")
