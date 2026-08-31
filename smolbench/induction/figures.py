"""Plotting helpers for induction analysis.

Matplotlib is imported LAZILY, inside :func:`plot_archetype_accuracy` only: it
lives in the ``notebook`` extra, not the core dependency set, so importing this
module must not require it. Exercised by
``tests/induction/test_induction_figures.py``.
"""

from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from smolbench.evals import Marks


def accuracy(marks: Marks) -> float:
    """Fraction correct: ``correct / (correct + incorrect + invalid)``.

    Invalids count against the model. An empty ``Marks`` returns ``0.0`` rather
    than raising, so it cannot abort a table build.
    """
    total = marks.correct + marks.incorrect + marks.invalid
    return marks.correct / total if total > 0 else 0.0


def load_condition_accuracies(
    results_dir: Path,
    files: Mapping[Tuple[str, str], str],
) -> Dict[Tuple[str, str], Optional[float]]:
    """Load a ``{(model, condition): accuracy}`` table from result YAMLs.

    Parameters
    ----------
    results_dir : Path
        Flat, single-run ``result2/`` archive -- NOT the per-replicate
        ``results/<tag>/rep_<seed>.yaml`` tree the current experiment writes.
    files : Mapping[Tuple[str, str], str]
        ``(model_key, condition_key) -> filename`` under `results_dir`.

    Returns
    -------
    Dict[Tuple[str, str], Optional[float]]
        One entry per `files` key, in `files` order; ``None`` for a missing
        file, also printed to stdout as ``Missing result file: <path>``.
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
    chance: Optional[float] = None,
    bar_width: float = 0.22,
    figsize: Tuple[float, float] = (9, 6),
    ylim: Tuple[float, float] = (0, 1.1),
    out_path: Optional[Path] = None,
):
    """Render the grouped-bar (model x condition) accuracy figure; return ``(fig, ax)``.

    One group per ``models`` entry ``(model_key, label)``, one bar per
    ``conditions`` entry ``(condition_key, label, color)``, in the given order.
    A key missing from `data` (or mapping to ``None``) plots as a 0-height
    bar annotated "n/a" -- collapsed lanes are first-class results and must
    stay distinguishable from never-collected ones.

    Parameters
    ----------
    chance : float or None, default None
        Y-value of the dashed, labeled "chance" line; ``None`` omits it. Pass
        the quiz's own floor explicitly (0.5 for a binary ToF quiz; a numeric
        quiz's floor is task-specific and usually near zero).
    bar_width : float, default 0.22
        X-axis units per condition bar; the drawn bar is ``bar_width - 0.02``.
    ylim : Tuple[float, float], default (0, 1.1)
        Headroom above 1.0 leaves room for percentage labels near 100%.
    out_path : pathlib.Path or None, default None
        If given, also saves with ``dpi=150, bbox_inches="tight"``.

    Notes
    -----
    The generalized bar offsets reproduce the pinned 3-condition figure
    bit-for-bit.
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import numpy as np

    x = np.arange(len(models))
    n_conditions = len(conditions)
    offsets = (np.arange(n_conditions) - (n_conditions - 1) / 2) * bar_width

    fig, ax = plt.subplots(figsize=figsize)

    for offset, (cond_key, cond_label, color) in zip(offsets, conditions):
        # `is None`, not truthiness: a genuine 0.0 is data (an unlabeled zero
        # bar, as in the pinned figure); None/missing gets an explicit "n/a".
        # An `or 0.0` would conflate the two.
        values = [data.get((model_key, cond_key)) for model_key, _ in models]
        heights = [0.0 if v is None else v for v in values]
        bars = ax.bar(
            x + offset, heights, bar_width - 0.02,
            label=cond_label, color=color, edgecolor="white", linewidth=0.8,
        )
        for bar, h, v in zip(bars, heights, values):
            label = "n/a" if v is None else (f"{h:.0%}" if h > 0 else None)
            if label is not None:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 0.012,
                    label,
                    ha="center", va="bottom", fontsize=8,
                    color="grey" if v is None else "black",
                )

    if chance is not None:
        # Chance floor for a binary (True/False) quiz; the label sits just
        # above the line so it never overlaps the dashes.
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
