"""Grouped-bar accuracy per (model, info-type) for the all-MoE induction study.

Reads ``notebooks/periodic_moe/results/{model}_{info}/rep_*.yaml`` and plots
accuracy over GRADEABLE marks (``acc_valid = correct / (correct + incorrect)``)
for the three MoE models x FOUR information types at R=30: the three
positive-information amounts (intensional rules / extensional full listing /
noise-padded intensional) plus a ZERO-info baseline (empty context -> chance
floor). Invalid marks (empty/truncated completions -- the reasoning models
over-run their token budget on the ~21k-token EXTENSIONAL listing) are
EXCLUDED, not counted as failures; the excluded cells are annotated. The story:
on extensional counting Nemotron-3 collapses while gpt-oss and Qwen3.5 hold,
and with no rules at all every model drops to the floor.

Colors: Okabe-Ito CVD-safe categorical palette, assigned to models in a FIXED
order (never cycled).

Run:
    .venv/bin/python notebooks/periodic_moe/figures/accuracy_bars.py
"""
import glob
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = Path(__file__).resolve().parent / "accuracy_bars.png"

# (result-dir tag, legend label, Okabe-Ito hue) -- FIXED order, never cycled.
MODELS = [
    ("gptoss", "gpt-oss-120B", "#0072B2"),
    ("nemotron3", "Nemotron-3-Super-120B", "#E69F00"),
    ("qwen35", "Qwen3.5-397B", "#009E73"),
]
INFOS = [
    ("intens", "Intensional"),
    ("extens", "Extensional"),
    ("noise_intens", "Noise"),
    ("zero", "Zero-info"),  # empty-context baseline -> chance floor
]


def stats(tag: str, info: str) -> tuple[float, int]:
    """(acc over gradeable marks, invalid-mark count) for one condition."""
    c = i = v = 0
    for f in glob.glob(str(RESULTS / f"{tag}_{info}" / "rep_*.yaml")):
        for s in re.findall(r"^\s*score:\s*(\S+)", open(f).read(), re.M):
            if s == "1":
                c += 1
            elif s == "0":
                i += 1
            else:
                v += 1
    return (c / (c + i) if (c + i) else float("nan")), v


def main() -> None:
    data = {tag: [stats(tag, info) for info, _ in INFOS] for tag, _, _ in MODELS}

    fig, ax = plt.subplots(figsize=(9.8, 4.9))
    x = np.arange(len(INFOS))
    w = 0.26
    for k, (tag, label, color) in enumerate(MODELS):
        vals = [data[tag][j][0] for j in range(len(INFOS))]
        bars = ax.bar(x + (k - 1) * w, vals, w, label=label, color=color, zorder=3)
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.012, f"{val:.2f}",
                    ha="center", va="bottom", fontsize=8, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in INFOS])
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Accuracy (gradeable marks)")
    ax.set_title("All-MoE periodic induction: accuracy by information type (R=30)")
    ax.grid(axis="y", color="#ececec", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.20))

    # Call out the one interesting positive-info cell.
    je = [i for i, (k, _) in enumerate(INFOS) if k == "extens"][0]
    # Placed in the clear column above the SHORT Nemotron bar (its tall gpt-oss
    # and Qwen neighbours leave no mid-height gap), lifted above their tops.
    ax.annotate(
        "Nemotron-3 alone collapses\non extensional counting",
        xy=(x[je], data["nemotron3"][je][0] + 0.02),
        xytext=(x[je], 1.02), fontsize=8.5, color="#8a5a00",
        ha="center", va="bottom",
        arrowprops=dict(arrowstyle="->", color="#8a5a00", lw=1.1),
    )

    # Mark the zero-info floor: with no rules given, all three sit near chance.
    jz = [i for i, (k, _) in enumerate(INFOS) if k == "zero"][0]
    ax.annotate(
        "Zero-info baseline\n(no rules -> chance floor)",
        xy=(x[jz], 0.06), xytext=(x[jz], 0.30), fontsize=8.5, color="#555",
        ha="center", arrowprops=dict(arrowstyle="->", color="#999", lw=1.0),
    )

    # Invalid (empty/truncated) marks are EXCLUDED from accuracy, never counted
    # as failures; list every nonzero cell so the exclusion stays auditable.
    reps = 30
    nz = [f"{mlabel} {ilabel.lower()} n={data[tag][j][1]}"
          for tag, mlabel, _ in MODELS
          for j, (_, ilabel) in enumerate(INFOS) if data[tag][j][1]]
    fig.text(0.01, 0.005,
             f"acc = correct / (correct + incorrect); invalid (empty/truncated) "
             f"completions excluded, of {reps * 9} marks per cell "
             f"(R={reps} x 9 harmonics). "
             + ("Nonzero invalids: " + "; ".join(nz) + "."
                if nz else "No invalid marks in any cell."),
             fontsize=6.3, color="#999")
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print("wrote", OUT)
    for tag, label, _ in MODELS:
        print(f"  {label:24} " + "  ".join(
            f"{lbl}={data[tag][j][0]:.3f}(inv{data[tag][j][1]})" for j, (_, lbl) in enumerate(INFOS)))


if __name__ == "__main__":
    main()
