"""Median response length (completion_tokens) per (model, rung).

Two panels: reasoning vs non-reasoning. Each model has a solid hint trendline
and a dashed noise trendline. Hint indexing shifted up by 1. `stepk:2`
displayed as 'no hint'.

Run:
    uv run python figures/response_length_per_model_rung.py
    uv run python figures/response_length_per_model_rung.py --runs main_v3
    uv run python figures/response_length_per_model_rung.py --runs main_v3 main_v3_2
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
OUT_PATH = ROOT / "figures/response_length_per_model_rung.png"

# Two trendlines per model: hint line through (no hint, hint 1..5), noise line
# through (noise 2..5). Noise paired with hint:N at matched token volume; user
# labels shifted up by 1, so internal noise:1 == user "noise 2".
HINT_RUNGS = ["stepk:2", "hint:0", "hint:1", "hint:2", "hint:3"]
HINT_LABELS = ["no hint", "hint 1", "hint 2", "hint 3", "hint 4"]
NOISE_RUNGS = [None, None, "noise:1", "noise:2", "noise:3"]  # aligned to HINT positions
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

    # Drop (theorem, k) pairs that were trivial-skipped at any rung shown.
    # Keep only those present at every hint level AND every noise level so
    # the lines describe the same theorems across the x-axis.
    all_rungs = HINT_RUNGS + [r for r in NOISE_RUNGS if r is not None]
    rung_to_keys = {r: set() for r in all_rungs}
    for r in real:
        rung = r.get("rung")
        if rung in rung_to_keys:
            rung_to_keys[rung].add((r.get("theorem_id"), r.get("k")))
    keep = set.intersection(*rung_to_keys.values())
    print(f"theorems present at every (hint, noise) level shown: {len(keep)}")

    # For the "no hint" point, further restrict to (model, theorem, k) where
    # the same model succeeded on at least one hint/noise rung — so the no-hint
    # baseline is on solvable-by-this-model theorems, not on hopeless ones.
    HINT_NOISE_RUNGS = HINT_RUNGS[1:] + [r for r in NOISE_RUNGS if r is not None]
    solvable = set()
    for r in real:
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if r.get("rung") in HINT_NOISE_RUNGS and r.get("verdict") == "success":
            solvable.add((r.get("model"), r.get("theorem_id"), r.get("k")))

    bucket = {}
    for r in real:
        m = r.get("model")
        if m in EXCLUDE_MODELS:
            continue
        rung = r.get("rung")
        ct = r.get("completion_tokens", 0) or 0
        if ct <= 0:
            continue
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if rung == "stepk:2":
            triple = (m, r.get("theorem_id"), r.get("k"))
            if triple not in solvable:
                continue
        bucket.setdefault((m, rung), []).append(ct)

    by_run = models_per_run(real)
    main_v3_models = by_run.get("main_v3", set())
    low_n_models = {m for m in {k[0] for k in bucket} if m not in main_v3_models}

    models = sorted({k[0] for k in bucket}, key=lambda m: model_sort_key(m, low_n_models))
    reasoning = [m for m in models if is_reasoning(m)]
    non_reasoning = [m for m in models if not is_reasoning(m)]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    cmap = plt.get_cmap("tab10")
    x = np.arange(len(HINT_RUNGS))

    def med_and_n(model, rung):
        xs = bucket.get((model, rung), [])
        return (np.median(xs) if xs else np.nan, len(xs))

    for ax, group, title in zip(axes, [reasoning, non_reasoning], ["Reasoning", "Non-reasoning"]):
        for i, m in enumerate(group):
            color = cmap(i % 10)
            hint_pairs = [med_and_n(m, r) for r in HINT_RUNGS]
            noise_pairs = [
                med_and_n(m, r) if r is not None else (np.nan, 0) for r in NOISE_RUNGS
            ]
            hint_ys = [p[0] for p in hint_pairs]
            noise_ys = [p[0] for p in noise_pairs]
            base_alpha = 0.45 if m in low_n_models else 1.0
            ax.plot(x, hint_ys, marker="o", label=f"{pretty_model(m)} (hint)",
                    color=color, linewidth=1.7, markersize=5, alpha=base_alpha)
            ax.plot(x, noise_ys, marker="s", label=f"{pretty_model(m)} (noise)",
                    color=color, linewidth=1.4, markersize=5,
                    linestyle="--", alpha=base_alpha * 0.7)
            # annotate n at each point
            for xi, (y, n) in zip(x, hint_pairs):
                if not np.isnan(y):
                    ax.annotate(f"n={n}", xy=(xi, y), xytext=(0, 6),
                                textcoords="offset points",
                                ha="center", fontsize=6, color=color, alpha=0.85)
            for xi, (y, n) in zip(x, noise_pairs):
                if not np.isnan(y):
                    ax.annotate(f"n={n}", xy=(xi, y), xytext=(0, -10),
                                textcoords="offset points",
                                ha="center", fontsize=6, color=color, alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(HINT_LABELS, rotation=20, ha="right")
        ax.set_xlabel("Hint level")
        ax.set_ylabel("Median response length (completion_tokens)")
        ax.set_title(f"{title} models  —  {' + '.join(args.runs)}")
        ax.grid(True, axis="y", alpha=0.3, which="both")
        ax.legend(fontsize=7, loc="best", ncol=1)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
