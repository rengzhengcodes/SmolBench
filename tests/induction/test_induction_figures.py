"""Test smolbench.induction.figures: the plotting helpers extracted from the notebook."""

import os

# Must precede any pyplot import (here or lazily inside figures).
os.environ.setdefault("MPLBACKEND", "Agg")

from datetime import datetime, timezone
from pathlib import Path

import pytest

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT
from smolbench.induction.figures import accuracy, load_condition_accuracies, plot_archetype_accuracy


def _marks(scores: list[int | None]) -> Marks:
    """Build a Marks with one Mark per entry of `scores` (1/0/None)."""
    return Marks(
        model="stub-model",
        marks=tuple(
            Mark(query=f"q{i}", answer=True, response="x", score=s,
                 compliance=COMPLIANT)
            for i, s in enumerate(scores)
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize(
    "scores, expected",
    [([1, 1, 1], 1.0), ([1, 1, 0, None], 0.5), ([0, 0, None], 0.0)],
)
def test_accuracy(scores: list[int | None], expected: float) -> None:
    """A None (unparseable) mark counts as a miss but stays in the denominator,
    so [1, 1, 0, None] is 2/4."""
    assert accuracy(_marks(scores)) == expected


def test_accuracy_refuses_an_empty_marks() -> None:
    """Empty Marks raises rather than scoring 0.0, so a replicate that graded
    nothing (tiny configs can produce empty quizzes) isn't confused with a genuine zero."""
    with pytest.raises(ValueError):
        accuracy(_marks([]))


def test_load_condition_accuracies_present_missing_and_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A present YAML maps to its accuracy; a missing or empty-replicate file maps to None."""
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


def test_plot_archetype_accuracy_smoke(tmp_path: Path) -> None:
    """Renders a grouped bar chart: one bar container per condition, one x tick
    per model, None drawn as a zero-height bar."""
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
