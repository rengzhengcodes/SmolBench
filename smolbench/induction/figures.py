"""Plotting helpers for induction analysis.

Score a ``Marks`` into a scalar accuracy, load a ``{(model, condition):
accuracy}`` table from a directory of result YAMLs, and render the grouped-bar
comparison figure. Matplotlib is imported LAZILY, inside
:func:`plot_archetype_accuracy` only: it lives in the ``notebook`` extra (see
``pyproject.toml``), not the core dependency set, so importing this module must
not require it. Exercised by ``tests/induction/test_induction_figures.py``.
"""

from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from smolbench.evals import Marks


def accuracy(marks: Marks) -> float:
    """Fraction correct: ``correct / (correct + incorrect + invalid)``.

    Invalid/unparseable responses count against the model like incorrect ones.
    An empty ``Marks`` returns ``0.0`` rather than raising, so it cannot abort
    a table build.
    """
    total = marks.correct + marks.incorrect + marks.invalid
    return marks.correct / total if total > 0 else 0.0


def load_condition_accuracies(
    results_dir: Path,
    files: Mapping[Tuple[str, str], str],
) -> Dict[Tuple[str, str], Optional[float]]:
    """Load a ``{(model, condition): accuracy}`` table from result YAMLs.

    ``files`` maps ``(model_key, condition_key) -> filename`` under
    `results_dir`; one output entry per key, in ``files`` iteration order,
    ``None`` when the file is absent (and printed to stdout as ``Missing result
    file: <path>``, so an incomplete checkout still surfaces a diagnostic).
    `results_dir` is a flat, single-run ``result2/`` archive -- NOT the
    per-replicate ``results/<tag>/rep_<seed>.yaml`` tree the current experiment
    writes.
    """
    data: Dict[Tuple[str, str], Optional[float]] = {}
    for (model_key, cond_key), fname in files.items():
        fpath = results_dir / fname
        if fpath.exists():
            data[(model_key, cond_key)] = accuracy(Marks.load(fpath))
        else:
            data[(model_key, cond_key)] = None
            print(f"Missing result file: {fpath}")
    return data


def plot_archetype_accuracy(
    data: Mapping[Tuple[str, str], Optional[float]],
    models: Sequence[Tuple[str, str]],
    conditions: Sequence[Tuple[str, str, str]],
    *,
    title: str,
    chance: Optional[float] = 0.5,
    bar_width: float = 0.22,
    figsize: Tuple[float, float] = (9, 6),
    ylim: Tuple[float, float] = (0, 1.1),
    out_path: Optional[Path] = None,
):
    """Render the grouped-bar (model x condition) accuracy figure; return ``(fig, ax)``.

    One group of bars per ``models`` entry ``(model_key, display_label)``, one
    bar per ``conditions`` entry ``(condition_key, display_label, color)``
    within each group, in the given order. Missing keys in `data` are treated as
    ``None`` and plotted at 0 with no label, so a genuine 0% is
    indistinguishable from missing data.

    Parameters
    ----------
    chance : float or None, default 0.5
        Y-value of the dashed, labeled "chance" line; ``None`` omits it.
    bar_width : float, default 0.22
        X-axis units per condition bar; the drawn bar is ``bar_width - 0.02``.
    ylim : Tuple[float, float], default (0, 1.1)
        Headroom above 1.0 leaves room for percentage labels near 100%.
    out_path : pathlib.Path or None, default None
        If given, also saves the figure with ``dpi=150, bbox_inches="tight"``.

    Notes
    -----
    Bar offsets are ``(i - (len(conditions) - 1) / 2) * bar_width``, which at
    exactly 3 conditions reproduces the pinned figure bit-for-bit while
    generalizing to any number of conditions per group.
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import numpy as np

    x = np.arange(len(models))
    n_conditions = len(conditions)
    offsets = (np.arange(n_conditions) - (n_conditions - 1) / 2) * bar_width

    fig, ax = plt.subplots(figsize=figsize)

    for offset, (cond_key, cond_label, color) in zip(offsets, conditions):
        heights = [
            data.get((model_key, cond_key)) or 0.0
            for model_key, _ in models
        ]
        bars = ax.bar(
            x + offset, heights, bar_width - 0.02,
            label=cond_label, color=color, edgecolor="white", linewidth=0.8,
        )
        for bar, h in zip(bars, heights):
            if h > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 0.012,
                    f"{h:.0%}",
                    ha="center", va="bottom", fontsize=8,
                )

    if chance is not None:
        # Reference line + label marking the pass/fail floor for a binary
        # (True/False) quiz; positioned just above the line so it never
        # overlaps the dashes.
        ax.axhline(chance, color="grey", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.text(
            len(models) - 0.5, chance + 0.01, "chance",
            color="grey", fontsize=8, va="bottom",
        )

    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in models])
    ax.set_ylabel("Accuracy")
    ax.set_ylim(*ylim)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
    ax.set_title(title, pad=12)
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if out_path is not None:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
    return fig, ax
