"""Provide plotting helpers for induction analysis.

Three steps: score a ``Marks`` into a scalar accuracy, load a
``{(model, condition): accuracy}`` table from a directory of result YAMLs,
and render the grouped-bar comparison figure. Exercised by
``tests/induction/test_induction_figures.py``.

This module imports matplotlib LAZILY, inside :func:`plot_archetype_accuracy`
only. Matplotlib lives in this project's ``notebook`` extra (see
``pyproject.toml``), not the core dependency set, so importing this module
(or the rest of ``smolbench.induction``) must not require it. ``accuracy``
and ``load_condition_accuracies`` need only ``smolbench.evals.Marks``,
which is core, so they import cleanly with no extras installed. Only
actually building a figure pulls in matplotlib.
"""

from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple

from smolbench.evals import Marks


def accuracy(marks: Marks) -> float:
    """Compute the fraction of a quiz's questions the model answered correctly.

    Parameters
    ----------
    marks : Marks
        A graded quiz result, as returned by ``ChatClient.evaluate`` or
        loaded from a result file via ``Marks.load``.

    Returns
    -------
    float
        ``correct / (correct + incorrect + invalid)``, i.e. correct answers
        as a fraction of all questions. Invalid/unparseable responses count
        against the model in this denominator, the same as incorrect ones.
        Returns ``0.0`` if ``marks`` has no questions at all (``total == 0``).
        Returning 0.0 (a valid, in-range value) rather than raising keeps
        an empty ``Marks`` from aborting a table build.
    """
    total = marks.correct + marks.incorrect + marks.invalid
    return marks.correct / total if total > 0 else 0.0


def load_condition_accuracies(
    results_dir: Path,
    files: Mapping[Tuple[str, str], str],
) -> Dict[Tuple[str, str], Optional[float]]:
    """Load a ``{(model, condition): accuracy}`` table from result YAMLs.

    For each ``(model_key, condition_key) -> filename`` entry, loads
    ``results_dir / filename`` via ``Marks.load`` and scores it with
    :func:`accuracy`, or records ``None`` and prints a diagnostic when the
    file is absent.

    Parameters
    ----------
    results_dir : pathlib.Path
        Directory containing the result YAML files (a flat, single-run
        ``result2/`` archive -- NOT the per-replicate
        ``results/<tag>/rep_<seed>.yaml`` tree the current experiment
        writes).
    files : Mapping[Tuple[str, str], str]
        Maps ``(model_key, condition_key)`` to the result filename expected
        under ``results_dir`` (the notebook's ``FILES`` dict).

    Returns
    -------
    Dict[Tuple[str, str], Optional[float]]
        One entry per key in ``files``, in iteration order: the file's
        :func:`accuracy` score if ``results_dir / filename`` exists, else
        ``None``.

    Notes
    -----
    Side effect: prints ``f"Missing result file: {path}"`` to stdout for
    every missing file, exactly as the notebook cell did (preserved so the
    notebook's rewired call site still surfaces the same diagnostic when
    re-run against an incomplete ``result2/`` checkout).
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
    """Render the grouped-bar (model x condition) accuracy comparison figure.

    Renders one group of bars per entry in ``models`` (x-axis), one bar per
    entry in ``conditions`` within each group. ``MODELS``/``CONDITIONS``/
    title/chance-line/output-filename are parameters with defaults.

    One group of bars is drawn per entry in ``models`` (x-axis), with one
    bar per entry in ``conditions`` inside each group, colored per
    ``conditions``' own color and labeled in the legend by ``conditions``'
    own label. Each bar is annotated with its own height as a percentage,
    unless the height is exactly 0. A bar of height 0 is not annotated
    (``data.get(...) or 0.0`` makes a genuine 0% indistinguishable from
    missing data).

    Parameters
    ----------
    data : Mapping[Tuple[str, str], Optional[float]]
        ``(model_key, condition_key) -> accuracy`` (or ``None``/missing),
        as produced by :func:`load_condition_accuracies`. Entries not
        present in ``data`` are treated the same as ``None`` (via
        ``.get``), so callers may pass a partial mapping.
    models : Sequence[Tuple[str, str]]
        ``(model_key, display_label)`` pairs, one per x-axis group, in
        left-to-right display order. ``display_label`` may contain
        embedded ``\\n`` line breaks (the notebook's model labels do, to fit
        a model name under the archetype name).
    conditions : Sequence[Tuple[str, str, str]]
        ``(condition_key, display_label, color)`` triples, one per bar
        within each group, in the order bars are drawn (and legend entries
        listed). ``color`` is any value ``matplotlib`` accepts for the
        ``color=`` keyword (e.g. a hex string).
    title : str
        Axes title.
    chance : float or None, default 0.5
        Y-value of the dashed "chance" reference line, labeled directly on
        the figure. Pass ``None`` to omit the reference line entirely (the
        notebook always draws one, so this is a new capability, not a
        behavior change for existing callers that omit the argument).
    bar_width : float, default 0.22
        Width, in x-axis units, of the space allotted to each condition's
        bar within a group (the drawn bar is slightly narrower, at
        ``bar_width - 0.02``, leaving a hairline gap between adjacent
        bars -- both values match the notebook's hardcoded ``bar_w``).
    figsize : Tuple[float, float], default (9, 6)
        Figure size in inches, forwarded to ``plt.subplots``.
    ylim : Tuple[float, float], default (0, 1.1)
        Y-axis limits. The default's headroom above 1.0 leaves room for the
        percentage labels on bars near 100% accuracy.
    out_path : pathlib.Path or None, default None
        If given, the figure is saved here (``dpi=150, bbox_inches="tight"``,
        matching the notebook's ``plt.savefig`` call) before being returned.
        If ``None``, the figure is only returned -- no file is written.

    Returns
    -------
    Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        The created figure and its single axes, for callers that want to
        further customize or display it (e.g. a notebook cell calling
        ``plt.show()`` afterward) rather than only save it to disk.

    Notes
    -----
    Design: bar offsets are computed as
    ``(i - (len(conditions) - 1) / 2) * bar_width`` for each condition index
    ``i``, which for exactly 3 conditions reduces to the notebook's
    hardcoded ``[-1, 0, 1] * bar_w`` -- the formula generalizes the layout
    to any number of conditions per group while reproducing the pinned
    3-condition figure bit-for-bit (verified by the pixel/data comparison
    performed when this function was extracted; see the module docstring).

    Matplotlib is imported inside this function body, not at module level --
    see the module docstring for why.
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
