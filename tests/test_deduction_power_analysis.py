"""Row-selection contract for the deduction power analysis loader.

`load_joint_cells` turns per-cell rows into a paired success/failure matrix, and
the two decisions it makes about *which* row to believe are the difference
between a pass@1 metric and a flattering one. Both were wrong before
2026-08-15, and both are cheap to get wrong again, so they are pinned here.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "deduction_power_analysis", REPO / "notebooks" / "deduction" / "power_analysis.py"
)
pa = importlib.util.module_from_spec(_SPEC)
# Registered BEFORE exec: the module defines dataclasses, and @dataclass
# resolves annotations via sys.modules[cls.__module__], which is None for a
# module that is still only half-imported.
sys.modules[_SPEC.name] = pa
_SPEC.loader.exec_module(pa)


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    # Deliberately NOT named all_rows.jsonl: that basename triggers the loader's
    # unverified-input warning, which is a separate contract.
    path = tmp_path / "verified_rows.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _cell(model, theorem, verdict, k=1, rung="stepk:1"):
    return {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": 0, "verdict": verdict,
    }


def test_earliest_surviving_attempt_wins_not_the_last(tmp_path):
    """A cell with several surviving attempts is scored on its FIRST one.

    Rows are appended, so file order is chronological. A 2026-08-15 resume bug
    re-ran cells the model had already answered emptily; because generation is
    not deterministic across server processes, those retries were fresh draws
    and 74 cells ended up with more than one surviving attempt. Taking the last
    one reports pass@N as pass@1 -- worth +5.9 points on ministral-3-3b, whose
    worst cell reads [empty, empty, empty, proof].
    """
    rows = [
        _cell("m1", "thm.resampled", "lean_error"),   # first real measurement
        _cell("m1", "thm.resampled", "success"),      # a later, luckier draw
        _cell("m2", "thm.resampled", "success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.resampled"][(1, "stepk:1")]["m1"] == 0, (
        "the later draw must not overwrite the first measurement"
    )
    assert blocks["thm.resampled"][(1, "stepk:1")]["m2"] == 1


def test_exception_rows_are_not_scored_as_model_failures(tmp_path):
    """`exception` means never measured -- it must not count as a 0.

    An exception is a spot interruption, idle watchdog or unreachable endpoint:
    the model never answered. Scoring it 0 charges a lane for the fleet's
    flakiness. deepseek-v3.1 carries 415 such cells (44% of its lane) and would
    read as 415 failures it never had. The cell must instead be absent, so the
    paired filter drops it for every model.
    """
    rows = [
        _cell("m1", "thm.infra", "exception"),
        _cell("m2", "thm.infra", "success"),
        _cell("m1", "thm.ok", "success"),
        _cell("m2", "thm.ok", "success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert "thm.infra" not in blocks, (
        "a cell only one model was measured on cannot be part of a paired block"
    )
    assert blocks["thm.ok"][(1, "stepk:1")] == {"m1": 1, "m2": 1}


def test_exception_then_a_real_attempt_uses_the_real_attempt(tmp_path):
    """Infra failure followed by a genuine re-run: score the re-run.

    This is the legitimate repair case and must keep working -- otherwise every
    cell recovered from a spot interruption would be discarded.
    """
    rows = [
        _cell("m1", "thm.recovered", "exception"),
        _cell("m1", "thm.recovered", "success"),
        _cell("m2", "thm.recovered", "lean_error"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.recovered"][(1, "stepk:1")] == {"m1": 1, "m2": 0}
