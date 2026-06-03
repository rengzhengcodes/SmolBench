"""Grouped-bar success rate per (model, hint level).

Two panels (reasoning, non-reasoning), one bar per model at each hint level,
with each model's peak-rate bar cross-hatched. Same filtering as the line
version: trivial-skip intersection across all hint levels, "no hint" point
restricted per model to theorems where the model passed at least one hint
or noise rung. Low-alpha for models with limited theorem coverage
(only present in the smaller main_v3_2 sweep).

Run:
    uv run python figures/success_rate_bars.py
    uv run python figures/success_rate_bars.py --runs main_v3 main_v3_2
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
OUT_PATH = ROOT / "figures/success_rate_bars.png"

HINT_RUNGS = ["stepk:2", "hint:0", "hint:1", "hint:2", "hint:3"]
HINT_LABELS = ["None", "1: Names", "2: Signatures", "3: Derivations", "4: 1-hop deriv."]
NOISE_RUNGS = ["noise:1", "noise:2", "noise:3"]
EXCLUDE_MODELS = {"v3.2-speciale"}


def is_reasoning(model_name: str) -> bool:
    n = model_name.lower()
    return ("high" in n) or ("thinking" in n) or ("speciale" in n)


def load_rows(runs):
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
    ap.add_argument("--runs", nargs="+", default=DEFAULT_RUNS)
    args = ap.parse_args()
    print(f"runs: {args.runs}")
    rows = load_rows(args.runs)
    real = [r for r in rows if r.get("model")]

    # Trivial-skip filter: keep only (theorem, k) present at every hint level.
    rung_to_keys = {r: set() for r in HINT_RUNGS}
    for r in real:
        rung = r.get("rung")
        if rung in rung_to_keys:
            rung_to_keys[rung].add((r.get("theorem_id"), r.get("k")))
    keep = set.intersection(*rung_to_keys.values())
    print(f"theorems present at every hint level: {len(keep)}")

    # No-hint per-model filter: theorems where this model succeeded somewhere
    # in {hint, noise} rungs.
    HINT_NOISE_RUNGS = HINT_RUNGS[1:] + NOISE_RUNGS
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
        v = r.get("verdict")
        if v not in ("success", "lean_error", "exception", "incomplete"):
            continue
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if rung == "stepk:2":
            triple = (m, r.get("theorem_id"), r.get("k"))
            if triple not in solvable:
                continue
        bucket.setdefault((m, rung), []).append(v)

    by_run = models_per_run(real)
    main_v3_models = by_run.get("main_v3", set())
    low_n_models = {m for m in {k[0] for k in bucket} if m not in main_v3_models}

    # Family detection: each toggle pair shares one family color, with the
    # reasoning version drawn in the saturated family color and the
    # non-reasoning version in a lighter blend of the same color.
    def family(model: str) -> str:
        if model.startswith("gemini-flash-"): return "gemini"
        if model.startswith("kimi-k2.6-"): return "kimi"
        if model.startswith("v3.2-"): return "deepseek"
        if model.startswith("gpt-5.5-"): return "gpt-5.5"
        if model.startswith("sonnet-4.6-"): return "sonnet-4.6"
        return model

    family_order = ["gemini", "kimi", "deepseek", "gpt-5.5", "sonnet-4.6"]
    cmap = plt.get_cmap("tab10")
    family_color = {f: cmap(i) for i, f in enumerate(family_order)}

    import matplotlib.colors as mcolors
    def lighten(c, factor=0.55):
        rgb = mcolors.to_rgb(c)
        return tuple(rgb[i] + (1.0 - rgb[i]) * factor for i in range(3))

    # Within each group (reasoning, non-reasoning), order by family then put
    # low-n models last (so gpt-5.5 / sonnet-4.6 sit at the right edge).
    def family_idx(m):
        f = family(m)
        return family_order.index(f) if f in family_order else 999

    def order_within_group(models):
        return sorted(models, key=lambda m: (1 if m in low_n_models else 0, family_idx(m), m))

    all_in_bucket = {k[0] for k in bucket}
    reasoning = order_within_group([m for m in all_in_bucket if is_reasoning(m)])
    non_reasoning = order_within_group([m for m in all_in_bucket if not is_reasoning(m)])

    def rate(model, rung):
        vs = bucket.get((model, rung), [])
        if not vs:
            return np.nan
        return 100 * sum(1 for v in vs if v == "success") / len(vs)

    rates_by_model = {m: [rate(m, r) for r in HINT_RUNGS] for m in reasoning + non_reasoning}
    peak_idx = {m: int(np.nanargmax(vals)) if not np.all(np.isnan(vals)) else -1
                for m, vals in rates_by_model.items()}

    fig, ax = plt.subplots(figsize=(14, 5.5))
    n_levels = len(HINT_RUNGS)
    x_centers = np.arange(n_levels)

    # Layout: positions 0..N_r-1 for reasoning, then a gap of GAP slots, then
    # N_r+GAP..N_r+GAP+N_nr-1 for non-reasoning. Total bar slots = N_r + GAP + N_nr.
    GAP = 0.7  # in bar-widths
    N_r, N_nr = len(reasoning), len(non_reasoning)
    total_slots = N_r + GAP + N_nr
    bar_w = 0.92 / total_slots

    def offset_for(model_index_in_group, group):
        if group == "reasoning":
            slot = model_index_in_group
        else:
            slot = N_r + GAP + model_index_in_group
        return (slot - (total_slots - 1) / 2) * bar_w

    def draw(model, slot_offset, fill_color):
        base_alpha = 0.45 if model in low_n_models else 1.0
        xs = x_centers + slot_offset
        ys = rates_by_model[model]
        for j, y in enumerate(ys):
            if np.isnan(y):
                continue
            is_peak = (j == peak_idx[model])
            ax.bar(xs[j], y, width=bar_w, color=fill_color, alpha=base_alpha,
                   hatch="//" if is_peak else None,
                   edgecolor="black" if is_peak else fill_color,
                   linewidth=1.0 if is_peak else 0.4)

    for i, m in enumerate(reasoning):
        draw(m, offset_for(i, "reasoning"), family_color[family(m)])
    for i, m in enumerate(non_reasoning):
        draw(m, offset_for(i, "non-reasoning"), lighten(family_color[family(m)]))

    ax.set_xticks(x_centers)
    ax.set_xticklabels(HINT_LABELS)
    ax.set_xlabel("Degree of positive information")
    ax.set_ylabel("Pass rate (%)")
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", alpha=0.3)

    # Legend: left column = reasoning models (saturated family swatch), right
    # column = non-reasoning siblings (lightened swatch). Matplotlib's legend
    # fills COLUMN-major, so handles must be ordered as the full left column
    # followed by the full right column.
    from matplotlib.patches import Patch
    families_present = [f for f in family_order
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

    fam_legend = ax.legend(
        r_handles + nr_handles,
        r_labels + nr_labels,
        fontsize=8, loc="upper left", ncol=2, framealpha=0.9,
        columnspacing=1.6, handletextpad=0.6,
        title="reasoning                            non-reasoning",
        title_fontsize=8,
    )
    ax.add_artist(fam_legend)
    # Separate legend for the peak-rate hatching key, so it doesn't fight the
    # column layout of the family legend.
    ax.legend(
        [Patch(facecolor="white", edgecolor="black", hatch="//")],
        ["best pass rate per model"],
        fontsize=8, loc="upper right", framealpha=0.9,
    )

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=140)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
