"""Reasoning length relative to the high-density arm, induction and deduction averaged.

One panel. Each row is a model; each point is the mean output tokens of an arm as a
percent increase over the high-density arm of the same model, averaged over the two
benchmarks on the log scale (geometric mean of the induction and deduction token ratios).
High density is the baseline (0%). The x axis is the token ratio on a log scale,
labelled in percent.

Induction ratios come from the means of the induction reasoning-length table (thousands
of tokens, Fisher, 2026-09-26). Deduction ratios come from the Horn stage-2 rows through
``horn_results.run_pipeline``. Rows pair by ``PAPER_NAME``; a model whose induction
entry is ``None`` (no induction token means yet) is left out of the figure.
No interval is drawn: the induction side has none.

usage: horn_reasoning_figure.py [--scratchpad DIR] [--rungs DIR] [--scoring iclr|default] [--out DIR]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import horn_results as hr  # noqa: E402

#: Induction reasoning-length table: model -> (high density, high density + whitespace,
#: low density) mean output tokens in thousands.
INDUCTION = {
    "Gemma4 E2B-it": (0.58, 0.48, 3.97),
    "Gemma4 12B-it": (3.19, 4.84, 46.16),
    "Gemma4 31B-it": (0.61, 1.02, 5.05),
    "Nemotron3 Nano-4B": (0.31, 0.28, 8.96),
    "Nemotron3 Nano-30B": (0.80, 0.92, 16.88),
    "Nemotron3 Super-120B": (0.23, 0.27, 24.11),
    "Qwen3.5 27B": (1.23, 1.11, 29.07),
    "Qwen3.5 122B": (1.27, 1.41, 18.38),
    "Qwen3.5 397B": (1.41, 1.42, 21.21),
    "Deepseek V4-Flash": (0.84, 0.69, 5.05),
    "Deepseek V3.1": (0.49, 0.76, 2.04),
    "GLM-4.7-Flash": (2.17, 8.15, 35.66),
    # Typed as "GLM-4.5-Air" in the induction table; Fisher confirmed (2026-09-26) it is GLM-4.7.
    "GLM-4.7": (2.18, 2.25, 15.30),
    "Ministral3-2512 3B": (2.64, 2.81, 13.00),
    "Ministral3-2512 8B": (1.23, 4.33, 9.74),
    "Ministral3-2512 14B": (6.41, 8.00, 22.00),
}

N_BOOT = 5000


def deduction_ratios(res: hr.Results) -> dict[str, dict[str, tuple[float, float, float]]]:
    """Model -> arm -> (ratio, lo, hi) of mean output tokens against lem, bootstrapped over seeds."""
    rng = np.random.default_rng(0)
    out: dict[str, dict[str, tuple[float, float, float]]] = {}
    for model in hr.MODELS:
        if model not in res.chosen:
            continue
        m = res.chosen[model]
        per_seed: dict[str, dict[int, list[float]]] = {a: collections.defaultdict(list) for a in ("lem", "pad", "both")}
        for (mo, mm, arm, seed, _rep), r in res.rows.items():
            if mo == model and mm == m and arm in per_seed and isinstance(r.get("completion_tokens"), (int, float)):
                per_seed[arm][seed].append(float(r["completion_tokens"]))
        out[model] = {}
        for arm in ("pad", "both"):
            seeds = sorted(set(per_seed["lem"]) & set(per_seed[arm]))
            if not seeds:
                continue
            base = np.array([np.mean(per_seed["lem"][s]) for s in seeds])
            other = np.array([np.mean(per_seed[arm][s]) for s in seeds])
            ratio = other.mean() / base.mean()
            idx = rng.integers(0, len(seeds), size=(N_BOOT, len(seeds)))
            bs = other[idx].mean(axis=1) / base[idx].mean(axis=1)
            out[model][arm] = (float(ratio), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))
    return out


#: Induction row -> deduction model, where the induction name differs from ``PAPER_NAME``.
PAIRING: dict[str, str] = {}


def combined_ratios(res: hr.Results) -> tuple[list[str], dict[str, dict[str, tuple[float, float, float]]], dict]:
    """Rows in induction order; per row the geometric mean of the two benchmarks' ratios.
    Also returns the per-benchmark ratios for the printed table."""
    ded = deduction_ratios(res)
    by_paper = {hr.PAPER_NAME[m]: m for m in hr.MODELS}
    names, points, detail = [], {}, {}
    for ind_name, vals in INDUCTION.items():
        model = PAIRING.get(ind_name) or by_paper.get(ind_name)
        if vals is None or model is None or model not in ded:
            continue
        h, w, l = vals
        label = ind_name
        names.append(label)
        ind_r = {"pad": w / h, "both": l / h}
        points[label] = {}
        detail[label] = {}
        for arm in ind_r:
            if arm not in ded[model]:
                continue
            d = ded[model][arm][0]
            g = float(np.sqrt(ind_r[arm] * d))
            points[label][arm] = (g, g, g)
            detail[label][arm] = (ind_r[arm], d, g)
    return names, points, detail


def figure(res: hr.Results, out: Path | None = None):
    import matplotlib.pyplot as plt

    names, points, detail = combined_ratios(res)
    arms = (("pad", "high density + irrelevant"), ("both", "low density"))
    labels = names + ["geomean"]
    xs = np.arange(len(labels))
    width = 0.4
    fig, ax = plt.subplots(figsize=(12, 4))
    for k, (arm, label) in enumerate(arms):
        ys = [points[n].get(arm, (np.nan,))[0] for n in names]
        ys.append(float(np.exp(np.nanmean(np.log(ys)))))
        ax.bar(xs + (k - 0.5) * width, ys, width=width, label=label)
    ax.axhline(1.0, linestyle=":", color="black", label="high density")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("normalized reasoning tokens")
    ax.set_ylim(bottom=0)
    ax.legend()
    if out is not None:
        fig.savefig(out / "reasoning_length_increase.pdf", bbox_inches="tight")
        fig.savefig(out / "reasoning_length_increase.png", bbox_inches="tight")
    return fig, detail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--scratchpad", type=Path, default=hr.SCRATCHPAD)
    ap.add_argument("--rungs", type=Path, default=None, help="served rungs (default <scratchpad>/roster2)")
    ap.add_argument("--scoring", choices=list(hr.SCORING_MODES), default=hr.DEFAULT_SCORING)
    ap.add_argument("--out", type=Path, default=hr.OUT, help="outputs go to <out>/<scoring>/")
    a = ap.parse_args(argv)
    a.out = a.out / a.scoring
    a.out.mkdir(parents=True, exist_ok=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = hr.run_pipeline(a.scratchpad, scoring=a.scoring, rungs=a.rungs or a.scratchpad / "roster2")
    fig, detail = figure(res, a.out)
    plt.close(fig)
    print("| Model | + irrelevant: induction | deduction | average | low density: induction | deduction | average |")
    print("|---|---|---|---|---|---|---|")
    for name, v in detail.items():
        cells = []
        for arm in ("pad", "both"):
            i, d, g = v.get(arm, (float("nan"),) * 3)
            cells += [f"{(i - 1) * 100:+,.0f}%", f"{(d - 1) * 100:+,.0f}%", f"{(g - 1) * 100:+,.0f}%"]
        print(f"| {name} | " + " | ".join(cells) + " |")
    print(f"\nWrote {a.out / 'reasoning_length_increase.png'} and .pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
