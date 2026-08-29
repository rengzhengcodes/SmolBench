"""Re-gate the local induction tree on CONTENT, under earliest-wins.

Selects, per (model, seed, arm), the object with the MINIMUM run
timestamp and compares the local file's SIZE against it -- content, not
row counts.

Usage: pass an ``aws s3 ls --recursive`` key listing ("<size> <key>" per
line) as ``argv[1]``.
"""
import re
import sys
from pathlib import Path

# This file is <repo>/notebooks/induction/audits/<name>.py, so parents[1] is
# the study root (.../notebooks/induction), where `run_study.py` and
# `results/` live. Anchored on __file__ rather than an absolute checkout
# path, so this probe reads the tree it actually ships in (a git worktree
# has its own).
STUDY = Path(__file__).resolve().parents[1]
KEYS = Path(sys.argv[1])
sys.path.insert(0, str(STUDY))
from run_study import MODELS as TAGS

RESULTS = STUDY / "results"
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
