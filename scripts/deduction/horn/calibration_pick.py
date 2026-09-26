"""Pick each model's chain length from its calibration levels.

Reads ``<results_dir>/<spec_key>_m<m>.jsonl`` files (one lem-only calibration level per
file, as ``sweep.py`` / ``bedrock_sweep.py`` write them), fits a logistic curve of the
pass rate against ``log m`` per model over every level with at least ``--min-cells``
scored cells, and reports the level nearest (in log m) to where the fitted curve crosses
``--target``. Models whose fitted curve never reaches the target on the ladder are
"below floor"; those above it everywhere are "near ceiling". Exception rows are ignored.

usage: calibration_pick.py <results_dir> [<results_dir> ...] [--target 0.7] [--json out.json]
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path

_NAME = re.compile(r"^(?P<model>.+)_m(?P<m>\d+)\.jsonl$")


def load_levels(dirs: list[Path]) -> dict[str, dict[int, tuple[int, int, int]]]:
    """``model -> m -> (passed, scored, length)``; later directories add to earlier ones."""
    out: dict[str, dict[int, tuple[int, int, int]]] = collections.defaultdict(dict)
    for d in dirs:
        for f in sorted(d.glob("*_m*.jsonl")):
            mt = _NAME.match(f.name)
            if not mt:
                continue
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            scored = [r for r in rows if r.get("verdict") != "exception"]
            if not scored:
                continue
            ok = sum(r["verdict"] == "success" for r in scored)
            length = sum(r.get("finish_reason") == "length" for r in scored)
            m = int(mt.group("m"))
            prev = out[mt.group("model")].get(m, (0, 0, 0))
            out[mt.group("model")][m] = (prev[0] + ok, prev[1] + len(scored), prev[2] + length)
    return out


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def _loglik(a: float, b: float, points: list[tuple[float, int, int]], ridge: float) -> float:
    ll = -0.5 * ridge * (a * a + b * b)
    for x, k, n in points:
        p = min(max(_sigmoid(a + b * x), 1e-12), 1 - 1e-12)
        ll += k * math.log(p) + (n - k) * math.log(1 - p)
    return ll


def fit_logistic(points: list[tuple[float, int, int]], ridge: float = 0.05) -> tuple[float, float]:
    """Penalized maximum-likelihood ``(a, b)`` for ``P(pass) = sigmoid(a + b x)`` from
    ``(x, passed, n)`` points: damped Newton steps with backtracking, and a small ridge
    so separable data (all pass or all fail) still gives a finite fit."""
    a, b = 0.0, -1.0
    ll = _loglik(a, b, points, ridge)
    for _ in range(200):
        g_a, g_b = -ridge * a, -ridge * b
        h_aa = h_bb = ridge
        h_ab = 0.0
        for x, k, n in points:
            p = _sigmoid(a + b * x)
            w = n * p * (1 - p)
            g_a += k - n * p
            g_b += (k - n * p) * x
            h_aa += w
            h_ab += w * x
            h_bb += w * x * x
        det = h_aa * h_bb - h_ab * h_ab
        da = (h_bb * g_a - h_ab * g_b) / det
        db = (h_aa * g_b - h_ab * g_a) / det
        step = 1.0
        while step > 1e-4:
            ll_new = _loglik(a + step * da, b + step * db, points, ridge)
            if ll_new >= ll:
                break
            step /= 2
        a, b, ll_prev, ll = a + step * da, b + step * db, ll, ll_new
        if abs(ll - ll_prev) < 1e-10:
            break
    return a, b


def pick(levels: dict[int, tuple[int, int, int]], target: float, min_cells: int) -> dict:
    """The chosen level and the fit for one model."""
    full = {m: v for m, v in levels.items() if v[1] >= min_cells}
    if not full:
        return {"status": "no complete level", "levels": {}}
    pts = [(math.log(m), v[0], v[1]) for m, v in sorted(full.items())]
    a, b = fit_logistic(pts)
    logit_t = math.log(target / (1 - target))
    rates = {m: v[0] / v[1] for m, v in full.items()}
    if b >= 0 or abs(b) < 1e-6:  # no decreasing trend: fall back to the closest level
        best = min(full, key=lambda m: (abs(rates[m] - target), -m))
        m70 = None
    else:
        x70 = (logit_t - a) / b
        m70 = math.exp(x70)
        best = min(full, key=lambda m: abs(math.log(m) - x70))
    status = "ok"
    if max(rates.values()) < target - 0.1 and best == min(full):
        status = "below floor"
    elif min(rates.values()) > target + 0.1 and best == max(full):
        status = "near ceiling"
    return {
        "status": status,
        "chosen_m": best,
        "chosen_rate": round(rates[best], 3),
        "fitted_m70": None if m70 is None else round(m70, 1),
        "fit": {"a": round(a, 3), "b": round(b, 3)},
        "levels": {str(m): {"pass": round(rates[m], 3), "n": full[m][1], "length": full[m][2]} for m in sorted(full)},
    }


def main(argv: list[str] | None = None) -> int:
    """Print a table and, with ``--json``, write the picks."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--target", type=float, default=0.70)
    ap.add_argument("--min-cells", type=int, default=25)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    levels = load_levels(a.dirs)
    picks = {model: pick(lv, a.target, a.min_cells) for model, lv in sorted(levels.items())}
    ms = sorted({m for lv in levels.values() for m in lv})
    print(f"{'model':28s}" + "".join(f"{'m'+str(m):>7s}" for m in ms) + "   chosen  fitted m70  status")
    for model, p in picks.items():
        cells = []
        for m in ms:
            v = levels[model].get(m)
            cells.append(f"{100*v[0]/v[1]:4.0f}{'L' if v[2] else ' '}{'' if v[1] >= a.min_cells else '?'}" if v else "-")
        print(f"{model:28s}" + "".join(f"{c:>7s}" for c in cells) + f"   {p.get('chosen_m', '-'):>6}  {p.get('fitted_m70', '-')!s:>10}  {p['status']}")
    print("(pass %; L = cap hits; ? = fewer than the minimum cells, not used in the fit)")
    if a.json:
        Path(a.json).write_text(json.dumps(picks, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
