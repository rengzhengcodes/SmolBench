"""Pass rate vs degree of positive information, relative to the MPI level.

Two panels: CoT (reasoning on) and non-CoT. One line per model, colored by
family, through the four paper levels MPI / MPI+Signatures / One-Hop /
Two-Hop (hint:0..3). Each point is the pooled pass-rate delta vs MPI over
the model's analysis set, with a 95% paired bootstrap interval over
theorems. Legend shows each model's theorem count.

Run:
    uv run python figures/success_rate_bars.py
    uv run python figures/success_rate_bars.py --runs main_v3_rescored --weight-class open
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (
    DEFAULT_RUNS, HINT_LEVELS, MPI_RUNG, ROOT,
    add_weight_class_arg, errorbar, family_palette, load_analysis, model_family,
)

OUT_PATH = ROOT / "figures/success_rate_bars.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS)
    add_weight_class_arg(ap)
    args = ap.parse_args()
    a = load_analysis(args.runs, args.weight_class)

    family_color = family_palette()
    rungs = [r for r, _ in HINT_LEVELS]
    labels = [lbl for _, lbl in HINT_LEVELS]
    x = np.arange(len(rungs))
    markers = ["o", "s", "D", "^", "v"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    for ax, reasoning, title in zip(axes, [True, False], ["CoT", "Non-CoT"]):
        group = a.sorted_models(reasoning=reasoning)
        n = max(len(group), 1)
        for i, m in enumerate(group):
            color = family_color.get(model_family(m), "gray")
            alpha = 0.35 if m in a.low_n_models else 1.0
            jitter = (i - (n - 1) / 2) * 0.04
            ys = []
            for j, r in enumerate(rungs):
                d, lo, hi = a.bootstrap_delta(m, r, MPI_RUNG)
                ys.append(d)
                if r != MPI_RUNG:
                    errorbar(ax, x[j] + jitter, d, lo, hi, color=color, alpha=alpha,
                             capsize=2, linewidth=0.8, fmt="none")
            ax.plot(x + jitter, ys, marker=markers[i % len(markers)],
                    label=a.label(m), color=color, linewidth=1.8, markersize=6, alpha=alpha)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=18, ha="right")
        ax.set_xlabel("Degree of positive information")
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_ylabel("Δ pass rate vs MPI (pp), 95% paired bootstrap")
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
