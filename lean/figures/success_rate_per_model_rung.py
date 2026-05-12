"""Pass rate per (model, rung) across selected sweeps.

Two panels: reasoning vs non-reasoning. One trendline per model through
(no hint, hint 1..5). Hint indexing shifted up by 1.

The "no hint" point is restricted (per model) to theorems where the SAME model
passed at least one hint/noise rung — so the no-hint baseline is on the
solvable-by-this-model subset, not on hopeless theorems.

Run:
    uv run python figures/success_rate_per_model_rung.py
    uv run python figures/success_rate_per_model_rung.py --runs main_v3
    uv run python figures/success_rate_per_model_rung.py --runs main_v3 main_v3_2
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import pretty_model, model_sort_key

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ["main_v3", "main_v3_2"]
OUT_PATH = ROOT / "figures/success_rate_per_model_rung.png"

HINT_RUNGS = ["stepk:2", "hint:0", "hint:1", "hint:2", "hint:3"]
HINT_LABELS = ["no hint", "hint 1", "hint 2", "hint 3", "hint 4"]
NOISE_RUNGS = [None, None, "noise:1", "noise:2", "noise:3"]
EXCLUDE_MODELS = {"v3.2-speciale"}


def is_reasoning(model_name: str) -> bool:
    n = model_name.lower()
    return ("high" in n) or ("thinking" in n) or ("speciale" in n)


def load_rows(runs):
    """Load rows, tagging each with the run it came from."""
    rows = []
    for run in runs:
        path = ROOT / f"results/runs/{run}/all_rows.jsonl"
        if not path.exists():
            print(f"warning: {path} missing, skipping")
            continue
        for l in path.open():
            if not l.strip():
                continue
            r = json.loads(l)
            r["_run"] = run
            rows.append(r)
    return rows


def models_per_run(real):
    """For each run in the data, the set of models contributing rows."""
    out = {}
    for r in real:
        if r.get("model"):
            out.setdefault(r["_run"], set()).add(r["model"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS,
                    help="run dirs under results/runs/ to merge (default: %(default)s)")
    args = ap.parse_args()
    print(f"runs: {args.runs}")
    rows = load_rows(args.runs)
    real = [r for r in rows if r.get("model")]

    # Drop (theorem, k) pairs that were trivial-skipped at any hint level — keep
    # only theorems that contribute a cell at EVERY level on the x-axis. Yields
    # apples-to-apples comparison across rungs (no trivial-skip cascade).
    rung_to_keys = {r: set() for r in HINT_RUNGS}
    for r in real:
        rung = r.get("rung")
        if rung in rung_to_keys:
            rung_to_keys[rung].add((r.get("theorem_id"), r.get("k")))
    keep = set.intersection(*rung_to_keys.values())
    print(f"theorems present at every hint level: {len(keep)}")

    # Restrict no-hint cells per model to theorems where THAT model succeeded
    # on at least one hint/noise rung (within the kept set).
    HINT_NOISE_RUNGS = HINT_RUNGS[1:] + [r for r in NOISE_RUNGS if r is not None]
    solvable = set()
    for r in real:
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if r.get("rung") in HINT_NOISE_RUNGS and r.get("verdict") == "success":
            solvable.add((r.get("model"), r.get("theorem_id"), r.get("k")))

    # bucket: (model, rung) -> [verdicts], filtered as described
    bucket = {}
    for r in real:
        m = r.get("model")
        if m in EXCLUDE_MODELS:
            continue
        rung = r.get("rung")
        v = r.get("verdict")
        if v not in ("success", "lean_error", "exception", "incomplete"):
            continue
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if rung == "stepk:2":
            triple = (m, r.get("theorem_id"), r.get("k"))
            if triple not in solvable:
                continue
        bucket.setdefault((m, rung), []).append(v)

    # Tag any model only present in main_v3_2 (frontier closed-weight, 30
    # theorems vs main_v3's 100) for reduced-alpha plotting.
    by_run = models_per_run(real)
    main_v3_models = by_run.get("main_v3", set())
    low_n_models = {m for m in {k[0] for k in bucket} if m not in main_v3_models}

    models = sorted({k[0] for k in bucket}, key=lambda m: model_sort_key(m, low_n_models))
    reasoning = [m for m in models if is_reasoning(m)]
    non_reasoning = [m for m in models if not is_reasoning(m)]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    cmap = plt.get_cmap("tab10")
    x = np.arange(len(HINT_RUNGS))

    def rate_and_n(model, rung):
        verdicts = bucket.get((model, rung), [])
        if not verdicts:
            return (np.nan, 0)
        s = sum(1 for v in verdicts if v == "success")
        return (100 * s / len(verdicts), len(verdicts))

    for ax, group, title in zip(axes, [reasoning, non_reasoning], ["Reasoning", "Non-reasoning"]):
        for i, m in enumerate(group):
            color = cmap(i % 10)
            hint_pairs = [rate_and_n(m, r) for r in HINT_RUNGS]
            hint_ys = [p[0] for p in hint_pairs]
            alpha = 0.45 if m in low_n_models else 1.0
            ax.plot(x, hint_ys, marker="o", label=pretty_model(m),
                    color=color, linewidth=1.7, markersize=5, alpha=alpha)
        ax.set_xticks(x)
        ax.set_xticklabels(HINT_LABELS, rotation=20, ha="right")
        ax.set_xlabel("Hint level")
        ax.set_ylabel("Pass rate (%)")
        ax.set_title(f"{title} models  —  {' + '.join(args.runs)}")
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
