"""Per-model arm pass rates and seed-paired contrasts from sweep rows.

Reads JSONL rows as ``sweep.py`` / ``bedrock_sweep.py`` write them. Rows are grouped by
model and rung, and a cell that appears in more than one file counts once
(``smolbench.deduction.horn.stats.load_rows``). For every model and rung: the pass rate
per arm (mean over seeds of the per-seed pass rate), and seed-paired contrasts in
percentage points with a 95% bootstrap CI and a sign-flip permutation p-value.

usage: rows_contrast.py <rows.jsonl> [<rows.jsonl> ...] [--contrasts both-pad,both-disc,...]
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from smolbench.deduction.horn.stats import (  # noqa: E402
    arm_order,
    contrast,
    format_p,
    load_rows,
    pass_rate,
)

DEFAULT = "lem-both,pad-both,disc-both"


def main(argv: list[str] | None = None) -> int:
    """Print the tables."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("rows", nargs="+", type=Path)
    ap.add_argument("--contrasts", default=DEFAULT)
    a = ap.parse_args(argv)
    cells, dropped = load_rows(a.rows)
    rng = random.Random(0)
    for (model, rung), arms in sorted(cells.items()):
        print(f"== {model} {rung}")
        for arm in sorted(arms, key=arm_order):
            n = sum(len(v) for v in arms[arm].values())
            print(f"   {arm:5s} {pass_rate(arms[arm]):5.1f}%  (n={n} cells, {len(arms[arm])} seeds)")
        for c in a.contrasts.split(","):
            x, y = c.split("-")
            if x in arms and y in arms:
                mean, lo, hi, p, n = contrast(arms[x], arms[y], rng)
                print(f"   {x} - {y}: {mean:+.1f} [{lo:+.1f}, {hi:+.1f}]  {format_p(p, n)}  (n={n} seeds)")
    if dropped:
        print(f"dropped rows: {dropped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
