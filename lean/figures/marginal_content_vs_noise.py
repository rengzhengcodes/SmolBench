"""Marginal positive information vs marginal noise — bar chart.

For each paper level N above MPI, shows hint:N − noise:N per model. Since
noise:N is hint:(N-1) padded with lorem ipsum to hint:N's token count, the
difference is

    (marginal positive content at step N) − (matched-length neutral filler)

Positive = the content helps over filler; negative = the content hurts
(pollution). Bars carry a 95% paired bootstrap interval over theorems.

Two panels: CoT (left), Non-CoT (right). Family colors.

Run:
    uv run python figures/marginal_content_vs_noise.py
    uv run python figures/marginal_content_vs_noise.py --weight-class open
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (
    DEFAULT_RUNS, NOISE_PAIRS, ROOT,
    add_weight_class_arg, errorbar, family_palette, load_analysis, model_family,
)

OUT_PATH = ROOT / "figures/marginal_content_vs_noise.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS)
    add_weight_class_arg(ap)
    args = ap.parse_args()
    a = load_analysis(args.runs, args.weight_class)

    family_color = family_palette()
    x_centers = np.arange(len(NOISE_PAIRS))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    for ax, reasoning, title in zip(axes, [True, False], ["CoT", "Non-CoT"]):
        group = a.sorted_models(reasoning=reasoning)
        N = len(group)
        if N == 0:
            continue
        bar_w = 0.85 / N
        offsets = (np.arange(N) - (N - 1) / 2) * bar_w

        for i, m in enumerate(group):
            color = family_color.get(model_family(m), "gray")
            alpha = 0.35 if m in a.low_n_models else 1.0
            ys = []
            for j, (h, n, _) in enumerate(NOISE_PAIRS):
                d, lo, hi = a.bootstrap_delta(m, h, n)
                ys.append(d)
                errorbar(ax, x_centers[j] + offsets[i], d, lo, hi, color="black",
                         alpha=0.6, capsize=2, linewidth=0.8, fmt="none")
            ax.bar(x_centers + offsets[i], ys, width=bar_w, color=color, alpha=alpha,
                   edgecolor=color, linewidth=0.4, label=a.label(m))
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_xticks(x_centers)
        ax.set_xticklabels([lbl for _, _, lbl in NOISE_PAIRS])
        ax.set_xlabel("Degree of positive information")
        ax.set_ylabel("Marginal positive − marginal noise (pp), 95% paired bootstrap")
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
