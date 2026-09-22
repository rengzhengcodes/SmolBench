"""Sanity check: pass rate at None (stepk:2) vs MPI (hint:0) per model.

CoT models left, non-CoT right, on one axis. Two bars per model: hatched =
None, solid = MPI, each with a 95% bootstrap interval over theorems. The
MPI − None delta is annotated above each pair with its 95% paired interval.

Run:
    uv run python figures/none_vs_mpi.py
    uv run python figures/none_vs_mpi.py --runs main_v3_rescored
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (
    DEFAULT_RUNS, MPI_RUNG, NONE_RUNG, ROOT,
    add_weight_class_arg, errorbar, family_palette, load_analysis, model_family,
)

OUT_PATH = ROOT / "figures/none_vs_mpi.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS)
    add_weight_class_arg(ap)
    args = ap.parse_args()
    a = load_analysis(args.runs, args.weight_class)

    family_color = family_palette()
    cot = a.sorted_models(reasoning=True)
    non_cot = a.sorted_models(reasoning=False)

    # One x-axis: CoT first, then non-CoT, with a gap.
    GAP = 0.6
    all_models = cot + non_cot
    positions = list(range(len(cot))) + [len(cot) + GAP + i for i in range(len(non_cot))]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bar_w = 0.25

    for px, m in zip(positions, all_models):
        c = family_color.get(model_family(m), "gray")
        alpha = 0.35 if m in a.low_n_models else 1.0
        none_r, none_lo, none_hi = a.bootstrap_rate(m, NONE_RUNG)
        mpi_r, mpi_lo, mpi_hi = a.bootstrap_rate(m, MPI_RUNG)
        ax.bar(px - bar_w / 2, none_r, bar_w, color=c, alpha=alpha,
               hatch="//", edgecolor="black", linewidth=0.6)
        ax.bar(px + bar_w / 2, mpi_r, bar_w, color=c, alpha=alpha,
               edgecolor=c, linewidth=0.4)
        errorbar(ax, px - bar_w / 2, none_r, none_lo, none_hi, color="black",
                 capsize=2, linewidth=0.8, fmt="none")
        errorbar(ax, px + bar_w / 2, mpi_r, mpi_lo, mpi_hi, color="black",
                 capsize=2, linewidth=0.8, fmt="none")
        d, lo, hi = a.bootstrap_delta(m, MPI_RUNG, NONE_RUNG)
        if not np.isnan(d):
            top = max(none_hi, mpi_hi)
            ax.annotate(f"{d:+.0f}\n[{lo:+.0f},{hi:+.0f}]", xy=(px, top + 1),
                        ha="center", fontsize=6, color="black")

    ax.set_xticks(positions)
    ax.set_xticklabels([a.label(m) for m in all_models], rotation=70, ha="right", fontsize=8)
    ax.set_ylabel("Pass rate (%), 95% bootstrap")
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", alpha=0.3)

    if cot and non_cot:
        c_center = float(np.mean(positions[:len(cot)]))
        nc_center = float(np.mean(positions[len(cot):]))
        for center, text in ((c_center, "CoT"), (nc_center, "Non-CoT")):
            ax.text(center, -0.55, text, ha="center", fontsize=9,
                    transform=ax.get_xaxis_transform(), color="black", fontstyle="italic")

    ax.legend(
        [Patch(facecolor="gray", edgecolor="black", hatch="//"),
         Patch(facecolor="gray", edgecolor="gray")],
        ["None (no premises)", "MPI (premise names)"],
        fontsize=8, loc="upper left",
    )

    plt.subplots_adjust(bottom=0.35)
    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
