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

    Invalids count against the model: an unparseable response stays in the
    denominator and scores as a miss.

    Returns
    -------
    float
        ``correct / (correct + incorrect + invalid)``, in ``[0.0, 1.0]``. Only
        ever computed from at least one graded mark -- see `Raises`.

    Raises
    ------
    ValueError
        If ``correct + incorrect + invalid == 0``: the ``Marks`` graded nothing.
        A genuine 0% and an ungraded replicate are DIFFERENT results and this
        function cannot represent the second, so it refuses rather than
        returning ``0.0`` for both. (It used to return ``0.0`` "so it cannot
        abort a table build"; the cost was that an existing-but-empty replicate
        stored as a real zero and ``plot_archetype_accuracy``'s ``None ->
        "n/a"`` branch became unreachable from disk. Empty quizzes are produced
        BY DESIGN -- ``periodic.tof_membership_query_gen`` yields none at a
        config too small to admit both polarities.) Table builders map this to
        their own "not a measurement" value; see
        :func:`load_condition_accuracies`.
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

    Parameters
    ----------
    results_dir : Path
        Directory each `files` value is resolved against; the function joins
        ``results_dir / filename`` and does not walk any directory tree of its
        own. `files` supplies the whole layout, so a caller wanting a
        per-replicate file just puts a relative path in the mapping.
    files : Mapping[Tuple[str, str], str]
        ``(model_key, condition_key) -> filename`` under `results_dir`.

    Returns
    -------
    Dict[Tuple[str, str], Optional[float]]
        One entry per `files` key, in `files` order. ``None`` marks "not a
        measurement", for either of two reasons, each printed to stdout under
        its own distinct prefix so an operator can tell them apart: the file
        does not exist (``Missing result file: <path>``), or it exists and
        graded nothing (``Ungraded (empty) result file: <path>``).
        :func:`plot_archetype_accuracy` renders both as "n/a".
    """
    data: Dict[Tuple[str, str], Optional[float]] = {}
    for (model_key, cond_key), fname in files.items():
        fpath = results_dir / fname
        if fpath.exists():
            try:
                data[(model_key, cond_key)] = accuracy(Marks.load(fpath))
            except ValueError:
                # Not a silent fallback: this function's declared return type is
                # Optional[float] and None is its DOCUMENTED "not a measurement"
                # value, already used for a missing file and already rendered as
                # "n/a". An empty replicate is exactly that -- no measurement --
                # so mapping it onto the existing sentinel preserves information
                # rather than discarding it, and the distinct print below keeps
                # it distinguishable from the missing-file case. The catch is
                # narrowed to ValueError (never a bare except) because that is
                # the ONE failure `accuracy` raises; an IO or YAML error from
                # `Marks.load` still propagates, since a corrupt file is a bug,
                # not a result.
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
):
    """Render the grouped-bar (model x condition) accuracy figure; return ``(fig, ax)``.

    One group per ``models`` entry ``(model_key, label)``, one bar per
    ``conditions`` entry ``(condition_key, label, color)``, in the given order.
    A key missing from `data` (or mapping to ``None``) plots as a 0-height
    bar annotated "n/a" -- collapsed lanes are first-class results and must
    stay distinguishable from unmeasured ones. ``None`` means "not a
    measurement" generally, not specifically "never collected":
    :func:`load_condition_accuracies` produces it both for a result file that
    does not exist and for one that exists but graded nothing.

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
