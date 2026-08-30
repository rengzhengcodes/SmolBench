"""Test the row-selection contract for the deduction power analysis loader."""

import importlib.util
import json
import sys
from pathlib import Path

from tests._paths import NOTEBOOKS

_SPEC = importlib.util.spec_from_file_location(
    "deduction_power_analysis", NOTEBOOKS / "deduction" / "analysis" / "power_analysis.py"
)
pa = importlib.util.module_from_spec(_SPEC)
# Register before exec: @dataclass resolves annotations through
# sys.modules[cls.__module__], which is None mid-import.
sys.modules[_SPEC.name] = pa
_SPEC.loader.exec_module(pa)


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    # Not all_rows.jsonl: that basename triggers the unverified-input warning.
    path = tmp_path / "verified_rows.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _cell(model, theorem, verdict, k=1, rung="stepk:1"):
    return {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": 0, "verdict": verdict,
    }


def test_earliest_surviving_attempt_wins(tmp_path):
    """Rows are chronological: score the first NON-exception attempt, not the last."""
    rows = [
        _cell("m1", "thm.resampled", "lean_error"),
        _cell("m1", "thm.resampled", "success"),
        _cell("m2", "thm.resampled", "success"),
        _cell("m1", "thm.recovered", "exception"),
        _cell("m1", "thm.recovered", "success"),
        _cell("m2", "thm.recovered", "lean_error"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.resampled"][(1, "stepk:1")]["m1"] == 0, (
        "the later draw must not overwrite the first measurement"
    )
    assert blocks["thm.resampled"][(1, "stepk:1")]["m2"] == 1
    assert blocks["thm.recovered"][(1, "stepk:1")] == {"m1": 1, "m2": 0}


def test_verdict_classification(tmp_path):
    """exception/replay_failed are unmeasurable and excluded; incomplete is a real 0."""
    rows = [
        _cell("m1", "thm.infra", "exception"),
        _cell("m2", "thm.infra", "success"),
        _cell("m1", "thm.unverifiable", "replay_failed"),
        _cell("m2", "thm.unverifiable", "replay_failed"),
        _cell("m1", "thm.incomplete", "incomplete"),
        _cell("m2", "thm.incomplete", "success"),
        _cell("m1", "thm.ok", "success"),
        _cell("m2", "thm.ok", "success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert "thm.infra" not in blocks, (
        "a cell only one model was measured on cannot be part of a paired block"
    )
    assert "thm.unverifiable" not in blocks, (
        "a cell no model could be tested on must not enter the denominator"
    )
    assert blocks["thm.incomplete"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
    assert blocks["thm.ok"][(1, "stepk:1")] == {"m1": 1, "m2": 1}
