"""Box plot of prompt token length per paper level (Table 1).

Dedupes by (theorem, k): prompt size depends only on (theorem, k, rung),
not on model or rollout. Per (theorem, k, rung) the MEDIAN provider-reported
prompt_tokens across rollouts/models is used, since providers tokenize
differently. Restricted to (theorem, k) pairs present at every level.

Run:
    uv run python figures/prompt_length_vs_hint.py
    uv run python figures/prompt_length_vs_hint.py --runs main_v3_rescored
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import DEFAULT_RUNS, LEVELS, ROOT, load_rows

OUT_PATH = ROOT / "figures/prompt_length_vs_hint.png"

RUNGS = [r for r, _ in LEVELS]
LABELS = [lbl for _, lbl in LEVELS]


def load_prompt_tokens_by_level(runs):
    rows = load_rows(runs)
    real = [r for r in rows if r.get("model")]
    raw = {l: {} for l in RUNGS}
    for r in real:
        rung = r.get("rung")
        if rung not in raw:
            continue
        key = (r.get("theorem_id"), r.get("k"))
        pt = r.get("prompt_tokens", 0) or 0
        if pt > 0:
            raw[rung].setdefault(key, []).append(pt)

    common = set.intersection(*[set(raw[l].keys()) for l in RUNGS])
    return [[int(np.median(raw[l][k])) for k in sorted(common)] for l in RUNGS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS,
                    help="run dirs under results/runs/ to merge (default: %(default)s)")
    args = ap.parse_args()
    print(f"runs: {args.runs}")
    data = load_prompt_tokens_by_level(args.runs)
    print("n per level: " + ", ".join(f"{LABELS[i]}={len(data[i])}" for i in range(len(RUNGS))))
    print("median tokens: " + ", ".join(
        f"{LABELS[i]}={int(np.median(data[i])) if data[i] else 'n/a'}" for i in range(len(RUNGS))))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(
        data, tick_labels=LABELS, showmeans=True, meanline=True,
        patch_artist=True,
        boxprops=dict(facecolor="#cfe2ff", edgecolor="#1f77b4"),
        medianprops=dict(color="#1f77b4", linewidth=1.5),
        meanprops=dict(color="red", linewidth=1.2, linestyle="--"),
        whiskerprops=dict(color="#1f77b4"),
        capprops=dict(color="#1f77b4"),
        flierprops=dict(marker=".", markersize=3, alpha=0.4),
    )

    ax.set_xlabel("Degree of positive information")
    ax.set_ylabel("Prompt length (tokens)")
    ax.set_title(f"Prompt length per level  —  {' + '.join(args.runs)}")
    ax.set_yscale("log")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(
        [Line2D([], [], color="#1f77b4"), Line2D([], [], color="red", linestyle="--")],
        ["median", "mean"], loc="upper left",
    )

    for i, vals in enumerate(data):
        if vals:
            med = int(np.median(vals))
            ax.annotate(
                f"{med}", xy=(i + 1, med), xytext=(0, 8), textcoords="offset points",
                ha="center", fontsize=8, color="#1f77b4",
            )

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
