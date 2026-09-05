"""Test smolbench.induction.figures: the plotting helpers extracted from the notebook."""

import os

# Must precede any pyplot import (here or lazily inside figures).
os.environ.setdefault("MPLBACKEND", "Agg")

from datetime import datetime, timezone

import pytest

from smolbench.evals import Mark, Marks
from smolbench.induction.figures import accuracy, load_condition_accuracies, plot_archetype_accuracy


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


@pytest.mark.parametrize(
    "scores, expected",
    [([1, 1, 1], 1.0), ([1, 1, 0, None], 0.5), ([0, 0, None], 0.0)],
)
def test_accuracy(scores, expected):
    """accuracy() counts invalids against the model: a ``None`` (unparseable)
    mark STAYS in the denominator and scores as a miss, so [1, 1, 0, None] is
    2/4. (Corrects this docstring's former claim that None marks leave the
    denominator -- figures.accuracy has always kept them in it.)"""
    assert accuracy(_marks(scores)) == expected


def test_accuracy_refuses_an_empty_marks():
    """An empty ``Marks`` RAISES rather than scoring 0.0 (12-14).

    A genuine 0% and "this replicate graded nothing" are different results,
    and ``tof_membership_query_gen`` produces empty quizzes by design at tiny
    configs. Returning 0.0 stored the second as the first and made
    ``plot_archetype_accuracy``'s ``None -> "n/a"`` branch unreachable from
    disk."""
    with pytest.raises(ValueError):
        accuracy(_marks([]))


def test_load_condition_accuracies_present_missing_and_empty(tmp_path, capsys):
    """A present YAML maps to its accuracy; a missing file AND an existing-but-empty
    replicate both map to None (12-14).

    The empty case is the one that regressed: it used to load as a genuine
    0.0, indistinguishable in the plotted table from a lane that really scored
    zero. ``accuracy`` now raises on it and the loader maps that raise to
    ``None``, the same value the plotter renders as "n/a"."""
    _marks([1, 1, 0, None]).dump(tmp_path / "present.yaml")
    _marks([]).dump(tmp_path / "empty.yaml")
    files = {("modelA", "intens"): "present.yaml",
             ("modelB", "intens"): "missing.yaml",
             ("modelC", "intens"): "empty.yaml"}
    data = load_condition_accuracies(tmp_path, files)
    assert data[("modelA", "intens")] == 0.5
    assert data[("modelB", "intens")] is None
    assert data[("modelC", "intens")] is None
    assert "missing.yaml" in capsys.readouterr().out


def test_plot_archetype_accuracy_smoke(tmp_path):
    """plot_archetype_accuracy renders a grouped bar chart to disk: one bar
    container per condition, one x tick per model, and a None accuracy drawn as
    a zero-height bar instead of crashing."""
    data = {  # ("cot", "extens") is missing -> 0-height bar, no label
        ("decode", "intens"): 0.9, ("decode", "extens"): 0.4,
        ("cot", "intens"): 0.7, ("cot", "extens"): None,
    }
    models = [("decode", "Decoder-only\n(stub-a)"), ("cot", "CoT\n(stub-b)")]
    conditions = [("intens", "Intensional", "#4C72B0"), ("extens", "Extensional", "#DD8452")]
    out_path = tmp_path / "smoke.png"

    _fig, ax = plot_archetype_accuracy(data, models, conditions, title="Smoke", out_path=out_path)

    assert out_path.exists()
    assert out_path.stat().st_size > 0
    assert len(ax.containers) == len(conditions)
    assert len(ax.get_xticks()) == len(models)
    # The None cell must be visibly absent, not a silent zero bar.
    assert any(t.get_text() == "n/a" for t in ax.texts)
