"""Plotting helpers for induction analysis.

Matplotlib is imported lazily, inside :func:`plot_archetype_accuracy` only:
it lives in the ``notebook`` extra, not the core dependency set, so importing
this module must not require it.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Mapping, Optional, Sequence, Tuple

from smolbench.evals import Marks

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def accuracy(marks: Marks) -> float:
    """Fraction correct: ``correct / (correct + incorrect + invalid)``.

    Invalids count against the model: an unparseable response stays in the
    denominator and scores as a miss.

    Parameters
    ----------
    marks : Marks
        Graded quiz marks.

    Returns
    -------
    float
        fraction of marks that are correct.

    Raises
    ------
    ValueError
        If ``correct + incorrect + invalid == 0``: the ``Marks`` graded
        nothing. A genuine 0% and an ungraded replicate are different results,
        so this refuses rather than returning ``0.0`` for both; table builders
        map the refusal to their own "not a measurement" value (see
        :func:`load_condition_accuracies`).
    """
    total = marks.correct + marks.incorrect + marks.invalid
    if total == 0:
        raise ValueError(
            f"Marks for model {marks.model!r} graded nothing: 0 correct, 0 "
            "incorrect and 0 invalid, so there is no accuracy to report. A "
            "genuine 0% and an ungraded replicate are different results; "
            "callers that must tolerate the second should map this error to "
            "their own 'no measurement' value rather than to 0.0."
        )
    return marks.correct / total


def load_condition_accuracies(
    results_dir: Path,
    files: Mapping[Tuple[str, str], str],
) -> Dict[Tuple[str, str], Optional[float]]:
    """Load a ``{(model, condition): accuracy}`` table from result YAMLs.

    `files` supplies the whole layout (``(model_key, condition_key) ->
    filename`` under `results_dir`); a caller wanting a per-replicate file
    just puts a relative path in the mapping. ``None`` marks "not a
    measurement", printed to stdout under a distinct prefix for a missing
    file vs. one that graded nothing, so an operator can tell them apart;
    :func:`plot_archetype_accuracy` renders both as "n/a".

    Parameters
    ----------
    results_dir : Path
        Directory containing result YAMLs.
    files : Mapping[Tuple[str, str], str]
        Mapping from model-condition keys to relative filenames.

    Returns
    -------
    Dict[Tuple[str, str], Optional[float]]
        model-condition accuracy table.
    """
    data: Dict[Tuple[str, str], Optional[float]] = {}
    for (model_key, cond_key), fname in files.items():
        fpath = results_dir / fname
        if fpath.exists():
            try:
                data[(model_key, cond_key)] = accuracy(Marks.load(fpath))
            except ValueError:
                # Narrowed to ValueError, the one failure `accuracy` raises;
                # an IO or YAML error from `Marks.load` still propagates,
                # since a corrupt file is a bug, not a result.
                data[(model_key, cond_key)] = None
                print(f"Ungraded (empty) result file: {fpath}")
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
) -> Tuple["Figure", "Axes"]:
    """Render the grouped-bar (model x condition) accuracy figure; return ``(fig, ax)``.

    One group per ``models`` entry, one bar per ``conditions`` entry, in the
    given order. A key missing from `data` (or mapping to ``None``) plots as
    a 0-height bar annotated "n/a": collapsed lanes are first-class results
    and must stay distinguishable from unmeasured ones.

    Parameters
    ----------
    chance : float, optional
        y-value of the dashed "chance" line; pass the quiz's own floor
        (0.5 for a binary ToF quiz).
    """
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    import numpy as np

    x = np.arange(len(models))
    n_conditions = len(conditions)
    offsets = (np.arange(n_conditions) - (n_conditions - 1) / 2) * bar_width

    fig, ax = plt.subplots(figsize=figsize)

    for offset, (cond_key, cond_label, color) in zip(offsets, conditions):
        # `is None`, not truthiness: a genuine 0.0 is data, and `or 0.0`
        # would conflate it with a missing "n/a" value.
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
