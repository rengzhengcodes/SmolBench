"""Pass rate per (model, rung) across selected sweeps.

Two panels: reasoning vs non-reasoning. One trendline per model through
(no hint, hint 1..5). Hint indexing shifted up by 1.

The "no hint" point is restricted (per model) to theorems where the SAME model
passed at least one hint/noise rung — so the no-hint baseline is on the
solvable-by-this-model subset, not on hopeless theorems.

Run:
    .venv/bin/python notebooks/lean/figures/success_rate_per_model_rung.py
    .venv/bin/python notebooks/lean/figures/success_rate_per_model_rung.py --runs main_v3
    .venv/bin/python notebooks/lean/figures/success_rate_per_model_rung.py --runs main_v3 main_v3_2
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from smolbench.deduction.lean.figures import (
    DEFAULT_FIGSIZE,
    HINT_LABELS,
    HINT_RUNGS,
    NOISE_RUNGS_ALIGNED as NOISE_RUNGS,
    build_success_buckets,
    figure_out_path,
    load_rows,
    parse_runs_args,
    pretty_model,
    save_figure,
)

# figure_out_path now takes an explicit output directory (this module lives
# in a different package from the figure scripts — see smolbench.deduction.lean.figures
# .figure_out_path's docstring), so pass this script's own directory.
OUT_PATH = figure_out_path("success_rate_per_model_rung", Path(__file__).resolve().parent)


def main():
    runs = parse_runs_args()
    print(f"runs: {runs}")
    rows = load_rows(runs)
    real = [r for r in rows if r.get("model")]

    # Trivial-skip intersection, per-model solvable-subset restriction on the
    # "no hint" cell, EXCLUDE_MODELS filtering, and the low-n/reasoning
    # splits are all identical between this script and
    # success_rate_with_noise.py — centralized in _util.build_success_buckets
    # (this script's only difference from that one is `keep_rungs`: here we
    # only require presence at every HINT_RUNGS level, not every noise level
    # too, since this figure never plots a noise trendline).
    sb = build_success_buckets(real, HINT_RUNGS, NOISE_RUNGS)
    print(f"theorems present at every hint level: {len(sb.keep)}")

    fig, axes = plt.subplots(1, 2, figsize=DEFAULT_FIGSIZE, sharey=True)
    cmap = plt.get_cmap("tab10")
    x = np.arange(len(HINT_RUNGS))

    def rate_and_n(model, rung):
        verdicts = sb.bucket.get((model, rung), [])
        if not verdicts:
            return (np.nan, 0)
        s = sum(1 for v in verdicts if v == "success")
        return (100 * s / len(verdicts), len(verdicts))

    for ax, group, title in zip(axes, [sb.reasoning, sb.non_reasoning], ["Reasoning", "Non-reasoning"]):
        for i, m in enumerate(group):
            color = cmap(i % 10)
            hint_pairs = [rate_and_n(m, r) for r in HINT_RUNGS]
            hint_ys = [p[0] for p in hint_pairs]
            alpha = 0.45 if m in sb.low_n_models else 1.0
            ax.plot(x, hint_ys, marker="o", label=pretty_model(m),
                    color=color, linewidth=1.7, markersize=5, alpha=alpha)
        ax.set_xticks(x)
        ax.set_xticklabels(HINT_LABELS, rotation=20, ha="right")
        ax.set_xlabel("Hint level")
        ax.set_ylabel("Pass rate (%)")
        ax.set_title(f"{title} models  —  {' + '.join(runs)}")
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8, loc="best")

    save_figure(OUT_PATH)


if __name__ == "__main__":
    main()
