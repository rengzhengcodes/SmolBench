"""Build an EARLIEST-selected induction tree, per the 2026-08-16 user ruling.

The published induction numbers were computed on NEWEST-per-cell. The
ruling instead requires earliest-per-cell everywhere. So the three
lanes that own more than one object for some cells must be re-pointed
at their FIRST logged attempt.

Selection rule for this leg: per (model, seed, arm), pick the object
with the lexicographically MINIMUM `--<ts>.yaml` timestamp. There is no
survivorship filter here. Unlike deduction, every induction object is a
complete graded mark file, so earliest simply means min timestamp.

This script writes a hardlink clone of notebooks/induction, so the repo
tree stays untouched. Then it REPLACES (rm, then download -- never
write through a shared inode) only the cells whose earliest attempt
differs from their newest.
"""
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/workspace/SmolBench")
SCRATCH = Path("/tmp/claude-1001/-workspace-SmolBench/54dbdffb-0485-4ced-9231-fa52049df286/scratchpad")
DEST = SCRATCH / "ind_earliest"
BUCKET = "smolbench-results-414266451290"
PREFIX = "analysis/2026-08-16/induction"

sys.path.insert(0, str(REPO / "notebooks" / "induction"))
from run_study import MODELS as TAGS  # model -> local tag

RX = re.compile(r"induction/([^/]+)/seed=(\d+)/([a-z_]+)--(\d{8}T\d{6})Z\.yaml$")

# ---- group every snapshot object by cell ------------------------------------
by_cell = defaultdict(list)
for line in (SCRATCH / "ind_keys.txt").read_text().splitlines():
    size, key = line.split(None, 1)
    m = RX.search(key)
    if m:
        by_cell[(m.group(1), int(m.group(2)), m.group(3))].append(
            (m.group(4), key, int(size)))

multi = {c: v for c, v in by_cell.items() if len(v) > 1}
print(f"cells with more than one logged attempt: {len(multi)}")
lanes = defaultdict(int)
for (model, _, _) in multi:
    lanes[model] += 1
for model, n in sorted(lanes.items()):
    print(f"  {model:24s} {n} cells")

# ---- clone the tree with hardlinks, then replace only what changes ----------
if DEST.exists():
    subprocess.run(["rm", "-rf", str(DEST)], check=True)
subprocess.run(["cp", "-a", str(REPO / "notebooks" / "induction"), str(DEST)],
               check=True)
print(f"\nclone -> {DEST}")

changed = []
for cell, attempts in sorted(multi.items()):
    model, seed, arm = cell
    attempts.sort()                       # lexicographic == chronological
    earliest_ts, earliest_key, earliest_size = attempts[0]
    newest_ts, _, newest_size = attempts[-1]
    if earliest_ts == newest_ts:
        continue
    local = DEST / "results" / f"{TAGS[model]}_{arm}" / f"rep_{seed}.yaml"
    if not local.exists():
        print(f"  !! missing target {local}")
        continue
    # rm first: the clone is hardlinked to the repo tree, so writing through
    # the path would mutate the committed file in place.
    local.unlink()
    subprocess.run(
        ["aws", "s3", "cp", f"s3://{BUCKET}/{earliest_key}", str(local),
         "--region", "us-west-2", "--only-show-errors"], check=True)
    changed.append((model, seed, arm, newest_ts, earliest_ts,
                    newest_size, earliest_size))

print(f"\nreplaced {len(changed)} cells with their earliest attempt")
per_lane = defaultdict(int)
for model, *_ in changed:
    per_lane[model] += 1
for model, n in sorted(per_lane.items()):
    print(f"  {model:24s} {n}")
