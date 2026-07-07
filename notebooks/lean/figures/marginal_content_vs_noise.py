"""Marginal value of content over equivalent-volume noise.

For each level N where noise is defined (N ≥ 2 in user labels = internal
N ≥ 1), compute pass_rate(hint:N) − pass_rate(noise:N) at matched volume.
positive = content helps; negative = content actively hurts more than the
same volume of filler ("pollution").

Single panel, reasoning vs non-reasoning models grouped with a small gap
between groups. Family colors: each toggle pair shares a family color, with
the reasoning version drawn in the saturated color and the non-reasoning
sibling in a lightened blend. Same conventions as success_rate_bars.py.

Run:
    .venv/bin/python notebooks/lean/figures/marginal_content_vs_noise.py
    .venv/bin/python notebooks/lean/figures/marginal_content_vs_noise.py --runs main_v3
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from smolbench.lean.figures import (
    DEFAULT_FIGSIZE,
    EXCLUDE_MODELS,
    FAMILY_ORDER,
    family_color_map,
    figure_out_path,
    is_reasoning,
    lighten,
    load_rows,
    model_family,
    models_per_run,
    order_within_group,
    parse_runs_args,
    pretty_model,
    save_figure,
    trivial_skip_keys,
)

# figure_out_path now takes an explicit output directory (this module lives
# in a different package from the figure scripts — see smolbench.lean.figures
# .figure_out_path's docstring), so pass this script's own directory.
OUT_PATH = figure_out_path("marginal_content_vs_noise", Path(__file__).resolve().parent)

# (hint_rung, noise_rung, x-axis label) — labels match the
# Degree-of-positive-information convention used in success_rate_bars.
PAIRS = [
    ("hint:1", "noise:1", "2: Signatures"),
    ("hint:2", "noise:2", "3: Derivations"),
    ("hint:3", "noise:3", "4: 1-hop deriv."),
]
ALL_RUNGS = sorted({r for h, n, _ in PAIRS for r in (h, n)})


def main():
    runs = parse_runs_args()
    print(f"runs: {runs}")
    rows = load_rows(runs)
    real = [r for r in rows if r.get("model")]

    keep = trivial_skip_keys(real, ALL_RUNGS)
    print(f"theorems present at every level shown: {len(keep)}")

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
        bucket.setdefault((m, rung), []).append(v)

    by_run = models_per_run(real)
    main_v3_models = by_run.get("main_v3", set())
    low_n_models = {m for m in {k[0] for k in bucket} if m not in main_v3_models}

    # family/colors mirroring success_rate_bars (shared via _util's
    # model_family/order_within_group/family_color_map/lighten).
    family = model_family
    family_color = family_color_map()

    all_in_bucket = {k[0] for k in bucket}
    reasoning = order_within_group([m for m in all_in_bucket if is_reasoning(m)], low_n_models)
    non_reasoning = order_within_group([m for m in all_in_bucket if not is_reasoning(m)], low_n_models)

    def rate(model, rung):
        vs = bucket.get((model, rung), [])
        if not vs:
            return np.nan
        return 100 * sum(1 for v in vs if v == "success") / len(vs)

    deltas_by_model = {
        m: [rate(m, h) - rate(m, n) for h, n, _ in PAIRS]
        for m in reasoning + non_reasoning
    }

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    n_levels = len(PAIRS)
    x_centers = np.arange(n_levels)

    GAP = 0.7  # in bar-widths
    N_r, N_nr = len(reasoning), len(non_reasoning)
    total_slots = N_r + GAP + N_nr
    bar_w = 0.92 / total_slots

    def offset_for(idx, group):
        slot = idx if group == "reasoning" else N_r + GAP + idx
        return (slot - (total_slots - 1) / 2) * bar_w

    def draw(model, slot_offset, fill_color):
        base_alpha = 0.45 if model in low_n_models else 1.0
        xs = x_centers + slot_offset
        ys = deltas_by_model[model]
        for j, y in enumerate(ys):
            if np.isnan(y):
                continue
            ax.bar(xs[j], y, width=bar_w, color=fill_color, alpha=base_alpha,
                   edgecolor=fill_color, linewidth=0.4)

    for i, m in enumerate(reasoning):
        draw(m, offset_for(i, "reasoning"), family_color[family(m)])
    for i, m in enumerate(non_reasoning):
        draw(m, offset_for(i, "non-reasoning"), lighten(family_color[family(m)]))

    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x_centers)
    ax.set_xticklabels([lbl for _, _, lbl in PAIRS])
    ax.set_xlabel("Degree of positive information")
    ax.set_ylabel("Positive information − noise pass rate (pp)")
    ax.grid(True, axis="y", alpha=0.3)

    # Legend: column-major fill, left = reasoning, right = non-reasoning
    from matplotlib.patches import Patch
    families_present = [f for f in FAMILY_ORDER
                        if any(family(m) == f for m in reasoning + non_reasoning)]
    r_handles, r_labels, nr_handles, nr_labels = [], [], [], []
    for f in families_present:
        c = family_color[f]
        r_models = [m for m in reasoning if family(m) == f]
        nr_models = [m for m in non_reasoning if family(m) == f]
        if r_models:
            r_handles.append(Patch(facecolor=c, edgecolor=c))
            r_labels.append(pretty_model(r_models[0]))
        else:
            r_handles.append(Patch(facecolor="none", edgecolor="none"))
            r_labels.append("")
        if nr_models:
            nr_handles.append(Patch(facecolor=lighten(c), edgecolor=lighten(c)))
            nr_labels.append(pretty_model(nr_models[0]))
        else:
            nr_handles.append(Patch(facecolor="none", edgecolor="none"))
            nr_labels.append("")
    ax.legend(
        r_handles + nr_handles,
        r_labels + nr_labels,
        fontsize=8, loc="best", ncol=2, framealpha=0.9,
        columnspacing=1.6, handletextpad=0.6,
        title="reasoning                            non-reasoning",
        title_fontsize=8,
    )

    save_figure(OUT_PATH)


if __name__ == "__main__":
    main()
