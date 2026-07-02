"""Pass rate per (model, rung) with both hint and noise trendlines.

Two panels: reasoning vs non-reasoning. Each model has a solid hint trendline
through (no hint, hint 1..4) and a dashed noise trendline through (noise 2..4).
Hint indexing shifted up by 1.

Filtering matches the response-length plot:
  - intersection over (theorem, k) pairs present at every hint AND noise level
  - "no hint" point per model further restricted to theorems where the model
    succeeded at any hint/noise rung
  - excludes v3.2-speciale (cf. EXCLUDE_MODELS)
  - models only in main_v3_2 (Sonnet, GPT-5.5) plot at low alpha

Run:
    uv run python figures/success_rate_with_noise.py
    uv run python figures/success_rate_with_noise.py --runs main_v3
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import (
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

OUT_PATH = figure_out_path("success_rate_with_noise")


def main():
    runs = parse_runs_args()
    print(f"runs: {runs}")
    rows = load_rows(runs)
    real = [r for r in rows if r.get("model")]

    # Same pipeline as success_rate_per_model_rung.py, centralized in
    # _util.build_success_buckets — the one difference is `keep_rungs`: this
    # figure also draws a noise trendline, so its trivial-skip intersection
    # must additionally require presence at every noise rung (not just every
    # hint rung), or the noise line could gap out on theorems the hint line
    # still shows.
    all_rungs = HINT_RUNGS + [r for r in NOISE_RUNGS if r is not None]
    sb = build_success_buckets(real, HINT_RUNGS, NOISE_RUNGS, keep_rungs=all_rungs)
    print(f"theorems present at every (hint, noise) level: {len(sb.keep)}")

    fig, axes = plt.subplots(1, 2, figsize=DEFAULT_FIGSIZE, sharey=True)
    cmap = plt.get_cmap("tab10")
    x = np.arange(len(HINT_RUNGS))

    def rate(model, rung):
        vs = sb.bucket.get((model, rung), [])
        if not vs:
            return np.nan
        return 100 * sum(1 for v in vs if v == "success") / len(vs)

    for ax, group, title in zip(axes, [sb.reasoning, sb.non_reasoning], ["Reasoning", "Non-reasoning"]):
        for i, m in enumerate(group):
            color = cmap(i % 10)
            base_alpha = 0.45 if m in sb.low_n_models else 1.0
            hint_ys = [rate(m, r) for r in HINT_RUNGS]
            noise_ys = [rate(m, r) if r is not None else np.nan for r in NOISE_RUNGS]
            ax.plot(x, hint_ys, marker="o", label=f"{pretty_model(m)} (hint)",
                    color=color, linewidth=1.7, markersize=5, alpha=base_alpha)
            ax.plot(x, noise_ys, marker="s", label=f"{pretty_model(m)} (noise)",
                    color=color, linewidth=1.4, markersize=5,
                    linestyle="--", alpha=base_alpha * 0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(HINT_LABELS, rotation=20, ha="right")
        ax.set_xlabel("Hint level")
        ax.set_ylabel("Pass rate (%)")
        ax.set_title(f"{title} models  —  {' + '.join(runs)}")
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=7, loc="best", ncol=1)

    save_figure(OUT_PATH)


if __name__ == "__main__":
    main()
