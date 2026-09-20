"""Test the row-selection contract for the deduction power analysis loader."""

from pathlib import Path

from conftest import cell_row, write_jsonl

from tests._paths import NOTEBOOKS, load_by_path

pa = load_by_path(
    NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py",
    "deduction_power_analysis",
)


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    # Avoid `all_rows.jsonl`, which triggers the unverified-input warning.
    path = tmp_path / "verified_rows.jsonl"
    write_jsonl(path, rows)
    return path


def test_earliest_surviving_attempt_wins(tmp_path: Path) -> None:
    """Rows are chronological: score the first NON-exception attempt, not the last."""
    rows = [
        cell_row(model="m1", theorem_id="thm.resampled", verdict="lean_error"),
        cell_row(model="m1", theorem_id="thm.resampled", verdict="success"),
        cell_row(model="m2", theorem_id="thm.resampled", verdict="success"),
        cell_row(model="m1", theorem_id="thm.recovered", verdict="exception"),
        cell_row(model="m1", theorem_id="thm.recovered", verdict="success"),
        cell_row(model="m2", theorem_id="thm.recovered", verdict="lean_error"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert (
        blocks["thm.resampled"][(1, "stepk:1")]["m1"] == 0
    ), "the later draw must not overwrite the first measurement"
    assert blocks["thm.resampled"][(1, "stepk:1")]["m2"] == 1
    assert blocks["thm.recovered"][(1, "stepk:1")] == {"m1": 1, "m2": 0}


def test_verdict_classification(tmp_path: Path) -> None:
    """exception/replay_failed are unmeasurable and excluded; incomplete is a real 0."""
    rows = [
        cell_row(model="m1", theorem_id="thm.infra", verdict="exception"),
        cell_row(model="m2", theorem_id="thm.infra", verdict="success"),
        cell_row(model="m1", theorem_id="thm.unverifiable", verdict="replay_failed"),
        cell_row(model="m2", theorem_id="thm.unverifiable", verdict="replay_failed"),
        cell_row(model="m1", theorem_id="thm.incomplete", verdict="incomplete"),
        cell_row(model="m2", theorem_id="thm.incomplete", verdict="success"),
        cell_row(model="m1", theorem_id="thm.ok", verdict="success"),
        cell_row(model="m2", theorem_id="thm.ok", verdict="success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert (
        "thm.infra" not in blocks
    ), "a cell only one model was measured on cannot be part of a paired block"
    assert (
        "thm.unverifiable" not in blocks
    ), "a cell no model could be tested on must not enter the denominator"
    assert blocks["thm.incomplete"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
    assert blocks["thm.ok"][(1, "stepk:1")] == {"m1": 1, "m2": 1}


def test_no_answer_is_measurable_and_scores_zero(tmp_path: Path) -> None:
    """`no_answer` is a measured zero; excluding it would shrink denominators."""
    assert pa.UNMEASURABLE_VERDICTS == frozenset({"exception", "replay_failed"})
    assert pa.grade_verdicts(["no_answer"]) == 0
    assert pa.grade_verdicts(["exception", "no_answer"]) == 0, (
        "earliest SURVIVING attempt wins: the exception is skipped, the "
        "no_answer is the measurement"
    )
    rows = [
        cell_row(model="m1", theorem_id="thm.silent", verdict="no_answer"),
        cell_row(model="m2", theorem_id="thm.silent", verdict="success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.silent"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
