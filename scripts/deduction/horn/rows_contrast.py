"""Per-model arm pass rates and seed-paired contrasts from sweep rows.

Reads JSONL rows as ``sweep.py`` / ``bedrock_sweep.py`` write them (fields ``model``,
``arm``, ``seed``, ``rep``, ``verdict``; exception rows are ignored). For every model:
pass rate per arm (mean over cells), and seed-paired contrasts in percentage points with
a percentile bootstrap over seeds (95%) and a sign-flip permutation p-value (exact when
the seed count is at most 16, else Monte Carlo with 20,000 draws).

usage: rows_contrast.py <rows.jsonl> [<rows.jsonl> ...] [--contrasts both-pad,both-disc,...]
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import random
import sys
from pathlib import Path

DEFAULT = "both-pad,both-disc,disc-pad,pad-lem,both-lem"
ORDER = ("lem", "pad", "disc", "both")


def load(paths: list[Path]) -> dict[str, dict[str, dict[int, list[bool]]]]:
    """``model -> arm -> seed -> [pass per replicate]``."""
    out: dict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("verdict") == "exception":
                continue
            out[r["model"]][r["arm"]][int(r["seed"])].append(r["verdict"] == "success")
    return out


def contrast(a: dict[int, list[bool]], b: dict[int, list[bool]], rng: random.Random) -> tuple[float, float, float, float, int]:
    """Mean difference of cell means (pp), bootstrap CI, sign-flip p, n seeds."""
    seeds = sorted(set(a) & set(b))
    d = [100 * (sum(a[s]) / len(a[s]) - sum(b[s]) / len(b[s])) for s in seeds]
    n = len(d)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), 0
    mean = sum(d) / n
    bs = sorted(sum(rng.choice(d) for _ in range(n)) / n for _ in range(5000))
    lo, hi = bs[int(0.025 * 5000)], bs[int(0.975 * 5000) - 1]
    obs = abs(mean)
    if n <= 16:
        hits = sum(abs(sum(s * x for s, x in zip(signs, d))) / n >= obs - 1e-9 for signs in itertools.product((1, -1), repeat=n))
        p = hits / 2**n
    else:
        draws = 20000
        hits = sum(abs(sum(rng.choice((1, -1)) * x for x in d)) / n >= obs - 1e-9 for _ in range(draws))
        p = hits / draws
    return mean, lo, hi, p, n


def main(argv: list[str] | None = None) -> int:
    """Print the tables."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("rows", nargs="+", type=Path)
    ap.add_argument("--contrasts", default=DEFAULT)
    a = ap.parse_args(argv)
    data = load(a.rows)
    rng = random.Random(0)
    for model, arms in sorted(data.items()):
        print(f"== {model}")
        for arm in sorted(arms, key=lambda x: ORDER.index(x) if x in ORDER else 9):
            cells = [v for vs in arms[arm].values() for v in vs]
            print(f"   {arm:5s} {100 * sum(cells) / len(cells):5.1f}%  (n={len(cells)} cells, {len(arms[arm])} seeds)")
        for c in a.contrasts.split(","):
            x, y = c.split("-")
            if x in arms and y in arms:
                mean, lo, hi, p, n = contrast(arms[x], arms[y], rng)
                print(f"   {x} - {y}: {mean:+.1f} [{lo:+.1f}, {hi:+.1f}]  p={p:.3f}  (n={n} seeds)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
