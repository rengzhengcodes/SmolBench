"""Median completion length vs degree of positive information.

CoT models only, single panel. `completion_tokens` is used as the reasoning
proxy: it includes the visible answer, but for these models the answer is
under 3% of the count. Normalized to the MPI level = 100%. Computed over
each model's analysis set (see _util).

Run:
    uv run python figures/response_length_per_model_rung.py
    uv run python figures/response_length_per_model_rung.py --runs main_v3_rescored
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (
    DEFAULT_RUNS, HINT_LEVELS, MPI_RUNG, ROOT,
    add_weight_class_arg, family_palette, load_analysis, model_family, pretty_model,
)

OUT_PATH = ROOT / "figures/response_length_per_model_rung.png"


def median_completion(a, model, rung) -> float:
    toks = [
        r.get("completion_tokens") or 0
        for rows in a.cells.get((model, rung), {}).values()
        for r in rows
    ]
    toks = [t for t in toks if t > 0]
    return float(np.median(toks)) if toks else float("nan")


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

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m in a.sorted_models(reasoning=True):
        color = family_color.get(model_family(m), "gray")
        medians = [median_completion(a, m, r) for r in rungs]
        baseline = median_completion(a, m, MPI_RUNG)
        if np.isnan(baseline) or baseline <= 0:
            continue
        normed = [100 * v / baseline for v in medians]
        alpha = 0.35 if m in a.low_n_models else 1.0
        ax.plot(x, normed, marker="o", color=color, linewidth=1.7, markersize=6, alpha=alpha,
                label=f"{pretty_model(m)} ({int(baseline):,} tok at MPI, n={a.n_theorems(m)})")

    ax.axhline(100, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Degree of positive information")
    ax.set_ylabel("Median completion tokens (% of MPI)")
    ax.grid(True, axis="y", alpha=0.3, which="both")
    ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
