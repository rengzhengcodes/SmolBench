"""Pass rates and seed-paired contrasts for Horn result rows.

Rows are the JSONL records that ``scripts/deduction/horn/sweep.py`` and
``bedrock_sweep.py`` write (fields ``model``, ``spec_key``, ``rung``, ``arm``, ``seed``,
``rep``, ``verdict``). The unit of analysis is the theory seed: a seed's pass rate in an
arm is the mean over its replicates, and two arms are compared on the seeds they share.
"""

from __future__ import annotations

import collections
import itertools
import json
import random
from pathlib import Path

from .render import ARMS

#: ``(model, rung) -> arm -> seed -> [pass per replicate]``.
Cells = dict[tuple[str, str], dict[str, dict[int, list[bool]]]]

N_BOOT = 5000
N_SIGN_FLIP = 20000


def model_key(row: dict) -> str:
    """The roster key when the row has one, else the served model name."""
    return row.get("spec_key") or row["model"]


def load_rows(paths: list[Path]) -> tuple[Cells, dict[str, int]]:
    """Group rows by model and rung, one row per (model, rung, arm, seed, rep).

    ``exception`` rows are infrastructure failures and are dropped. When a cell appears
    more than once (a resumed run, a back-fill file), the first row read wins.
    Returns the cells and counts of dropped rows by reason.
    """
    seen: set[tuple] = set()
    dropped: collections.Counter = collections.Counter()
    cells: Cells = collections.defaultdict(
        lambda: collections.defaultdict(lambda: collections.defaultdict(list))
    )
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                dropped["unparsable"] += 1
                continue
            if r.get("verdict") == "exception":
                dropped["exception"] += 1
                continue
            key = (model_key(r), r["rung"], r["arm"], int(r["seed"]), int(r["rep"]))
            if key in seen:
                dropped["duplicate"] += 1
                continue
            seen.add(key)
            cells[(key[0], key[1])][key[2]][key[3]].append(r["verdict"] == "success")
    return cells, dict(dropped)


def pass_rate(arm: dict[int, list[bool]]) -> float:
    """Mean over seeds of the per-seed pass rate, in percent."""
    if not arm:
        return float("nan")
    return 100 * sum(sum(v) / len(v) for v in arm.values()) / len(arm)


def contrast(
    a: dict[int, list[bool]], b: dict[int, list[bool]], rng: random.Random
) -> tuple[float, float, float, float, int]:
    """Seed-paired difference ``a - b`` in percentage points.

    Returns the mean difference, a 95% percentile bootstrap CI over seeds, a two-sided
    sign-flip permutation p-value (exact up to 16 seeds, else Monte Carlo), and the
    number of shared seeds.
    """
    seeds = sorted(set(a) & set(b))
    d = [100 * (sum(a[s]) / len(a[s]) - sum(b[s]) / len(b[s])) for s in seeds]
    n = len(d)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), 0
    mean = sum(d) / n
    bs = sorted(sum(rng.choice(d) for _ in range(n)) / n for _ in range(N_BOOT))
    lo, hi = bs[int(0.025 * N_BOOT)], bs[int(0.975 * N_BOOT) - 1]
    obs = abs(mean)
    if n <= 16:
        hits = sum(
            abs(sum(s * x for s, x in zip(signs, d))) / n >= obs - 1e-9
            for signs in itertools.product((1, -1), repeat=n)
        )
        p = hits / 2**n
    else:
        hits = sum(
            abs(sum(rng.choice((1, -1)) * x for x in d)) / n >= obs - 1e-9
            for _ in range(N_SIGN_FLIP)
        )
        p = hits / N_SIGN_FLIP
    return mean, lo, hi, p, n


def format_p(p: float, n_seeds: int) -> str:
    """A p-value for print. A Monte Carlo p of 0 means below one in ``N_SIGN_FLIP``."""
    if p == 0 and n_seeds > 16:
        return f"p<{1 / N_SIGN_FLIP:.0e}"
    return f"p={p:.4f}"


def arm_order(arm: str) -> int:
    """Sort key: the four arms in their standard order, anything else last."""
    return ARMS.index(arm) if arm in ARMS else len(ARMS)
