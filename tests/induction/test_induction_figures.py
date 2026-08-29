"""Test smolbench.induction.figures: the plotting helpers extracted from the notebook.

Matplotlib is set to the non-interactive "Agg" backend (through the
MPLBACKEND env var, read at import time) before pyplot is ever imported
anywhere in the process. This is required to render figures headlessly in
CI or offline test runs with no display. It must happen before
``matplotlib.pyplot`` is first imported (by this module or by
``smolbench.induction.figures``, which imports it lazily inside
``plot_archetype_accuracy``). So it is set here at module import time,
ahead of any test that invokes that function.
"""

import os

os.environ.setdefault("MPLBACKEND", "Agg")

from datetime import datetime, timezone

from smolbench.evals import Mark, Marks
from smolbench.induction.figures import (
    accuracy,
    load_condition_accuracies,
    plot_archetype_accuracy,
)


def _marks(scores) -> Marks:
    """Build a Marks with one Mark per entry of `scores` (1/0/None)."""
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(query=f"q{i}", answer=True, response="x", score=s)
            for i, s in enumerate(scores)
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# accuracy
# ---------------------------------------------------------------------------


def test_accuracy_all_correct():
    assert accuracy(_marks([1, 1, 1])) == 1.0


def test_accuracy_mixed_correct_incorrect_invalid():
    # 2 correct, 1 incorrect, 1 invalid -> 2/4 = 0.5.
    marks = _marks([1, 1, 0, None])
    assert accuracy(marks) == 0.5


def test_accuracy_all_incorrect_or_invalid():
    assert accuracy(_marks([0, 0, None])) == 0.0


def test_accuracy_zero_total_returns_zero_not_zero_division_error():
    # Empty Marks: correct + incorrect + invalid == 0. The notebook's
    # original inline `accuracy` guards this with `if total > 0 else
    # 0.0`, moved verbatim, so this must not raise ZeroDivisionError.
    assert accuracy(_marks([])) == 0.0


# ---------------------------------------------------------------------------
# load_condition_accuracies
# ---------------------------------------------------------------------------


def test_load_condition_accuracies_present_and_missing(tmp_path, capsys):
    present = _marks([1, 1, 0, None])  # accuracy 0.5
    present.dump(tmp_path / "present.yaml")

    files = {
        ("modelA", "intens"): "present.yaml",
        ("modelB", "intens"): "missing.yaml",
    }
    data = load_condition_accuracies(tmp_path, files)

    assert data[("modelA", "intens")] == 0.5
    assert data[("modelB", "intens")] is None

    # The exact diagnostic string the notebook cell printed for a missing
    # file, preserved so the rewired notebook still surfaces it identically.
    captured = capsys.readouterr()
    expected_path = tmp_path / "missing.yaml"
    assert captured.out == f"Missing result file: {expected_path}\n"


# ---------------------------------------------------------------------------
# plot_archetype_accuracy
# ---------------------------------------------------------------------------


def test_plot_archetype_accuracy_smoke(tmp_path):
    data = {
        ("decode", "intens"): 0.9,
        ("decode", "extens"): 0.4,
        ("cot", "intens"): 0.7,
        ("cot", "extens"): None,  # missing -> drawn as a 0-height bar, no label
    }
    models = [("decode", "Decoder-only\n(stub-a)"), ("cot", "CoT\n(stub-b)")]
    conditions = [
        ("intens", "Intensional", "#4C72B0"),
        ("extens", "Extensional", "#DD8452"),
    ]
    out_path = tmp_path / "smoke.png"

    fig, ax = plot_archetype_accuracy(
        data, models, conditions, title="Smoke Test", out_path=out_path,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0
    # Basic sanity on the returned objects: one bar container per condition,
    # and the x-axis has one tick per model group.
    assert len(ax.containers) == len(conditions)
    assert len(ax.get_xticks()) == len(models)

    fig_module = type(fig).__module__
    assert fig_module.startswith("matplotlib")

