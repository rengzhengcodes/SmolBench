"""Box plot of prompt token length per hint level.

Dedupes by (theorem, k) since prompt size depends only on (theorem, k, rung) —
independent of model/rollout. Hint levels relabeled hint 1..5 (internal
hint:0..hint:4); `stepk:2` shown as 'no hint'.

Run:
    uv run python figures/prompt_length_vs_hint.py
    uv run python figures/prompt_length_vs_hint.py --runs main_v3 main_v3_2
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import figure_out_path, load_rows, parse_runs_args, save_figure

OUT_PATH = figure_out_path("prompt_length_vs_hint")

LEVELS = ["stepk:2", "hint:0", "hint:1", "hint:2", "hint:3"]
LABELS = ["no hint", "hint 1", "hint 2", "hint 3", "hint 4"]


def load_prompt_tokens_by_level(runs):
    """Per (theorem, k, rung), take the MEDIAN reported prompt_tokens across
    all rollouts/models. Different providers tokenize differently (and
    occasionally misreport), so a single pick is unreliable.

    Restrict to (theorem, k) pairs present at every level — keeps box-plot
    columns directly comparable. Theorems trivial-skipped at higher rungs are dropped."""
    rows = load_rows(runs)
    real = [r for r in rows if r.get("model")]
    raw = {l: {} for l in LEVELS}
    for r in real:
        rung = r.get("rung")
        if rung not in raw:
            continue
        key = (r.get("theorem_id"), r.get("k"))
        pt = r.get("prompt_tokens", 0) or 0
        if pt > 0:
            raw[rung].setdefault(key, []).append(pt)

    common = set.intersection(*[set(raw[l].keys()) for l in LEVELS])
    out = []
    for l in LEVELS:
        out.append([int(np.median(raw[l][k])) for k in sorted(common)])
    return out


def main():
    runs = parse_runs_args()
    print(f"runs: {runs}")
    data = load_prompt_tokens_by_level(runs)
    print("n per level: " + ", ".join(f"{LABELS[i]}={len(data[i])}" for i in range(len(LEVELS))))

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

    ax.set_xlabel("Hint level")
    ax.set_ylabel("Prompt length (tokens)")
    ax.set_title(f"Prompt length vs hint level  —  {' + '.join(runs)}")
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

    save_figure(OUT_PATH)


if __name__ == "__main__":
    main()
