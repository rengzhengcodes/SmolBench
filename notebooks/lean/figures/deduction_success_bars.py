"""Lean-deduction next-tactic success per (model, rung) for both open-model trios.

Two panels, one per trio, mirroring the induction study's
``notebooks/periodic_moe/figures/accuracy_bars.py``:

- LEFT  = the ARCHETYPE trio (``lean_arch``): the SAME models as the
  ``notebooks/periodic`` induction study -- ``llama-31-405b`` (decode),
  ``nemotron-ultra-253b`` (cot), ``llama4-maverick`` (moe).
- RIGHT = the MoE trio (``lean_moe``): the SAME models as ``notebooks/periodic_moe``
  -- ``gpt-oss-120b``, ``nemotron-3-super-120b-a12b``, ``qwen3.5-397b-a17b``.

Each panel is a grouped bar chart: x = the 4 rungs (``stepk:1`` baseline, the
``hint:2``/``hint:3`` help ladder, and the ``noise:3`` length control), bars =
the trio's three models, y = fraction of gradeable cells whose generated tactic
Lean-verifies as ``ProofFinished`` (``verdict == "success"``). This is the same
success metric the reference ``lean/`` figures use; the number of replicates
(theorems x rollouts per cell) was sized by
``notebooks/lean/power_analysis.py``.

Colors: Okabe-Ito CVD-safe categorical palette, assigned to models in a FIXED
order (never cycled). The MoE trio's three hues are locked to the committed
induction figure so the two studies read as one system.

Run:
    .venv/bin/python notebooks/lean/figures/deduction_success_bars.py
    # test before the full MoE run exists (stand in the pilot):
    .venv/bin/python notebooks/lean/figures/deduction_success_bars.py --moe-run lean_moe_pilot
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RUNS = Path(__file__).resolve().parents[1] / "results" / "runs"
OUT = Path(__file__).resolve().parent / "deduction_success_bars.png"

# Rungs in narrative order: baseline (least context) -> help ladder -> length
# control. Labels are two-line so the x-axis reads without a legend for rungs.
RUNGS = [
    ("stepk:1", "step k:1\n(baseline)"),
    ("hint:2", "hint:2"),
    ("hint:3", "hint:3"),
    ("noise:3", "noise:3\n(control)"),
]

# (result model name, legend label, Okabe-Ito hue) -- FIXED order, never cycled.
# MoE hues match notebooks/periodic_moe/figures/accuracy_bars.py exactly.
ARCH_TRIO = [
    ("llama-31-405b-base", "Llama-3.1-405B (decode)", "#56B4E9"),
    ("nemotron-ultra-253b-base", "Nemotron-Ultra-253B (cot)", "#D55E00"),
    ("llama4-maverick-base", "Llama-4-Maverick (moe)", "#CC79A7"),
]
MOE_TRIO = [
    ("gpt-oss-120b-base", "gpt-oss-120B", "#0072B2"),
    ("nemotron-3-super-120b-a12b-base", "Nemotron-3-Super-120B", "#E69F00"),
    ("qwen3.5-397b-a17b-base", "Qwen3.5-397B", "#009E73"),
]


def rates(run_dir: Path) -> dict[tuple[str, str], tuple[float, int]]:
    """(success fraction, gradeable-cell count) per (model, rung) for a run.

    A cell counts once per (model, rung) using rollout 0 (pass@1); ``success``
    is ``verdict == "success"`` (Lean ``ProofFinished``), everything else
    (lean_error / incomplete / exception) is a non-success. Returns NaN rate
    for cells with no gradeable data so the plotter can skip them.
    """
    succ: dict = {}
    tot: dict = {}
    path = run_dir / "all_rows.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a partial trailing line during a live run
            if r.get("kind") != "cell" or r.get("rollout_idx", 0) != 0:
                continue
            key = (r["model"], r["rung"])
            tot[key] = tot.get(key, 0) + 1
            if r.get("verdict") == "success":
                succ[key] = succ.get(key, 0) + 1
    out = {}
    for key, n in tot.items():
        out[key] = (succ.get(key, 0) / n, n)
    return out


def panel(ax, run_dir: Path, trio, title: str) -> None:
    data = rates(run_dir)
    x = np.arange(len(RUNGS))
    w = 0.26
    any_data = False
    for k, (model, label, color) in enumerate(trio):
        vals = [data.get((model, rung), (float("nan"), 0))[0] * 100 for rung, _ in RUNGS]
        if any(v == v for v in vals):  # not all-NaN
            any_data = True
        bars = ax.bar(x + (k - 1) * w, [0 if v != v else v for v in vals], w,
                      label=label, color=color, zorder=3)
        for b, v in zip(bars, vals):
            if v == v:
                ax.text(b.get_x() + b.get_width() / 2, v + 1.0, f"{v:.0f}",
                        ha="center", va="bottom", fontsize=7.5, color="#333")
    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in RUNGS], fontsize=8)
    ax.set_ylim(0, 45)
    ax.set_ylabel("Next-tactic success (%)")
    ax.set_title(title, fontsize=10)
    ax.grid(axis="y", color="#ececec", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    if not any_data:
        ax.text(0.5, 0.5, "(run not available yet)", transform=ax.transAxes,
                ha="center", va="center", color="#999", fontsize=10)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arch-run", default="lean_arch")
    p.add_argument("--moe-run", default="lean_moe")
    args = p.parse_args()

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    panel(axes[0], RUNS / args.arch_run, ARCH_TRIO,
          f"Archetype trio ({args.arch_run})")
    panel(axes[1], RUNS / args.moe_run, MOE_TRIO,
          f"All-MoE trio ({args.moe_run})")
    fig.suptitle("Lean-4 deduction: next-tactic success by model and rung "
                 "(base models, Lean-verified)", fontsize=11.5)
    fig.text(0.01, 0.005,
             "success = generated tactic verifies as ProofFinished (pass@1); "
             "bars are the fraction of gradeable (theorem, rung) cells. "
             "n_theorems sized by notebooks/lean/power_analysis.py.",
             fontsize=6.3, color="#999")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print("wrote", OUT)
    for run, trio in ((args.arch_run, ARCH_TRIO), (args.moe_run, MOE_TRIO)):
        d = rates(RUNS / run)
        print(f"  {run}:")
        for model, label, _ in trio:
            cells = [d.get((model, rung)) for rung, _ in RUNGS]
            summary = "  ".join(
                f"{rung.split(':')[0]}{rung.split(':')[1]}={c[0]:.2f}(n{c[1]})" if c else f"{rung}=—"
                for (rung, _), c in zip(RUNGS, cells))
            print(f"    {label:34} {summary}")


if __name__ == "__main__":
    main()
