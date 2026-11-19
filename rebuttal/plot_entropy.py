"""Plot the mean prompt entropy per model, study and condition with 95% intervals.

Usage::

    python rebuttal/plot_entropy.py              # plot from the stored intervals
    python rebuttal/plot_entropy.py --recompute  # read the capture mirror first

``--recompute`` reads the local mirror of the attention captures
(``results/attention-v2``, see ``attention_replay.pull_captures``), bootstraps the
intervals with ``attention_replay.entropy_ci`` and writes
``results/attention_ci--<model>.json``. Without it the figure is drawn from those files.
The figure goes to ``figures/entropy_ci.pdf`` and ``figures/entropy_ci.png``.

Each panel is one model and one study, induction in the first row. A bar is the mean,
over responses, of the Shannon entropy (nats) of a response token's attention on the
input prompt; the error bar and the bracket in the label are the 95% bootstrap interval
that resamples seeds. Gemma 4 31B is shown over its
global-attention layers and the other models over all attention layers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
RESULTS_DIR = _HERE / "results"
FIGURES_DIR = _HERE / "figures"

#: Roster key, display name and the layers its entropy is averaged over.
MODELS: Tuple[Tuple[str, str, str], ...] = (
    ("gemma-4-31b", "Gemma4 31B-it", "global"),
    ("nemotron-3-super-120b-a12b", "Nemotron3 Super-120B", "all"),
    ("deepseek-v3.1", "Deepseek V3.1", "all"),
)
#: Condition label and its arm in each study, in plotting order.
CONDITIONS: Tuple[Tuple[str, str, str], ...] = (
    ("high density", "intens", "lem"),
    ("high density\n+ irrelevant", "noise_intens", "pad"),
    ("high density\n+ related", "related_intens", "tjunk"),
    ("low density", "extens", "both"),
)
#: Study key in the interval files, row title and index of its arm in ``CONDITIONS``.
STUDIES: Tuple[Tuple[str, str, int], ...] = (("induction", "Induction", 1), ("horn", "Deduction", 2))
N_BOOT = 10_000


def recompute(models: Tuple[Tuple[str, str, str], ...] = MODELS) -> None:
    """Bootstrap the intervals from the capture mirror and write one JSON file per model.

    Reads ``results/attention-v2`` with ``attention_replay.read_entropy_table``. Needs the
    cached model configuration, as every reader of the captures does.
    """
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    import attention_replay as ar  # pylint: disable=import-outside-toplevel

    for key, _name, layers in models:
        table = ar.read_entropy_table(key, RESULTS_DIR / "attention-v2")
        out: Dict[str, Dict[str, object]] = {}
        for (study, arm), stats in table.items():
            mean, lower, upper, n, n_seeds = ar.entropy_ci(stats, layers=layers, n_boot=N_BOOT, seed=0)
            out[f"{study}/{arm}"] = {
                "mean": mean, "lower": lower, "upper": upper, "responses": n, "seeds": n_seeds,
                "layers": layers, "n_boot": N_BOOT,
            }
        path = RESULTS_DIR / f"attention_ci--{key}.json"
        path.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path}")


def load_intervals(key: str) -> Dict[str, Dict[str, float]]:
    """Return the stored intervals of one model, keyed ``<study>/<arm>``."""
    path = RESULTS_DIR / f"attention_ci--{key}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing: run with --recompute")
    return json.loads(path.read_text(encoding="utf-8"))


def plot(out_dir: Path = FIGURES_DIR) -> List[Path]:
    """Draw the figure and return the files written (PDF and PNG)."""
    import matplotlib  # pylint: disable=import-outside-toplevel

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel

    # Design: bars from a zero baseline in the default matplotlib colour cycle, one colour
    # per condition, the same in every panel. The tick labels name the conditions, so
    # colour is never the only cue. Induction is the first row. Each bar is labelled with
    # its mean and its interval, because most intervals are too narrow to read off the
    # error bar.
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    fig, axes = plt.subplots(
        len(STUDIES), len(MODELS), figsize=(12.0, 6.4), sharex=True, constrained_layout=True
    )
    for col, (key, name, layers) in enumerate(MODELS):
        intervals = load_intervals(key)
        for row, (study, study_name, arm_index) in enumerate(STUDIES):
            ax = axes[row][col]
            top = 0.0
            for x, condition in enumerate(CONDITIONS):
                cell = intervals[f"{study}/{condition[arm_index]}"]
                lower, upper = cell["mean"] - cell["lower"], cell["upper"] - cell["mean"]
                ax.bar(x, cell["mean"], width=0.72, color=colors[x], edgecolor="white", linewidth=1.0)
                ax.errorbar(
                    x, cell["mean"], yerr=[[lower], [upper]], fmt="none", ecolor="black",
                    capsize=4, elinewidth=1.2, capthick=1.2,
                )
                ax.annotate(
                    f"{cell['mean']:.3f}\n[{cell['lower']:.3f}, {cell['upper']:.3f}]",
                    (x, cell["upper"]), textcoords="offset points", xytext=(0, 3),
                    ha="center", va="bottom", fontsize=7, color="0.15", linespacing=1.15,
                )
                top = max(top, cell["upper"])
            ax.set_xlim(-0.6, len(CONDITIONS) - 0.4)
            ax.set_ylim(0.0, top * 1.22)  # headroom for the two-line labels
            ax.grid(axis="y", color="0.9", linewidth=0.8)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            if row == 0:
                scope = "global layers" if layers == "global" else "all layers"
                ax.set_title(f"{name}\n({scope})", fontsize=10)
            if col == 0:
                ax.set_ylabel(f"{study_name}\nprompt entropy (nats)", fontsize=9)
            ax.set_xticks(range(len(CONDITIONS)))
            ax.set_xticklabels([c[0] for c in CONDITIONS], fontsize=8)
            ax.tick_params(axis="y", labelsize=8)
    fig.suptitle("Mean prompt entropy of response tokens (label: mean [95% bootstrap interval])", fontsize=11)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [out_dir / "entropy_ci.pdf", out_dir / "entropy_ci.png"]
    fig.savefig(written[0])
    fig.savefig(written[1], dpi=200)
    plt.close(fig)
    return written


def main(argv: Optional[List[str]] = None) -> int:
    """Command-line entry point; returns the exit status."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--recompute", action="store_true",
                        help="bootstrap the intervals from the capture mirror before plotting")
    args = parser.parse_args(argv)
    if args.recompute:
        recompute()
    for path in plot():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
