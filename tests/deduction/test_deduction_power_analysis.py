"""Test the row-selection contract for the deduction power analysis loader.

`load_joint_cells` turns per-cell rows into a paired success/failure matrix.
It makes two decisions about which row to believe, and those decisions are
the difference between a pass@1 metric and a flattering one. Both decisions
were wrong before 2026-08-15, and both are cheap to get wrong again, so this
file pins them.
"""

import importlib.util
import json
import sys
from pathlib import Path

from tests._paths import REPO_ROOT as REPO

_SPEC = importlib.util.spec_from_file_location(
    "deduction_power_analysis", REPO / "notebooks" / "deduction" / "power_analysis.py"
)
pa = importlib.util.module_from_spec(_SPEC)
# Register the module before exec. The module defines dataclasses, and
# @dataclass resolves annotations through sys.modules[cls.__module__],
# which is None for a module that is still only half-imported.
sys.modules[_SPEC.name] = pa
_SPEC.loader.exec_module(pa)


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    # This file is deliberately not named all_rows.jsonl: that basename
    # triggers the loader's unverified-input warning, a separate contract.
    path = tmp_path / "verified_rows.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _cell(model, theorem, verdict, k=1, rung="stepk:1"):
    return {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": 0, "verdict": verdict,
    }


def test_earliest_surviving_attempt_wins_not_the_last(tmp_path):
    """A cell with several surviving attempts is scored on its first one.

    Rows are appended, so file order is chronological. A 2026-08-15 resume bug re-ran
    cells the model had already answered with an empty output. Because generation is not
    deterministic across server processes, those retries were fresh draws, and 74 cells
    ended up with more than one surviving attempt. If the last one is taken, that
    reports pass@N as pass@1, worth +5.9 points on ministral-3-3b, whose worst cell
    reads [empty, empty, empty, proof].
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
    """`exception` means never measured; it must not count as a 0.

    An exception is a spot interruption, an idle watchdog, or an unreachable endpoint:
    the model never answered. If it is scored 0, that charges a lane for the fleet's
    flakiness. deepseek-v3.1 carries 415 such cells (44% of its lane), and would read as
    415 failures it never had. The cell must instead be absent, so the paired filter
    drops it for every model.
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

    This is the legitimate repair case, and it must keep working.
    Otherwise every cell recovered from a spot interruption would be
    discarded.
    """
    rows = [
        _cell("m1", "thm.recovered", "exception"),
        _cell("m1", "thm.recovered", "success"),
        _cell("m2", "thm.recovered", "lean_error"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.recovered"][(1, "stepk:1")] == {"m1": 1, "m2": 0}


def test_replay_failed_is_unmeasurable_not_a_model_failure(tmp_path):
    """`replay_failed` means verification could not be set up; exclude it.

    There are two causes, both upstream of the model's candidate. Either LeanDojo
    could not open a session for the theorem (a missing *.ast.json in the traced
    cache), or the ground-truth prefix of k tactics would not replay.

    The proof that this is not model behavior: the replay_failed cell set
    is byte-identical across lanes. It has exactly 232 cells, 100% overlap,
    in every one of 21 models (151 DojoInit + 81 prefix-tactic). No
    model-dependent outcome can do that.

    If these cells are scored 0, that deflates every model's marginal rate by up to
    232/944 = 24.6%. Measured on real lanes: gemma-4-e2b goes 0.110 -> 0.083, and
    glm-4.7-flash goes 0.146 -> 0.110. Paired McNemar survives this, because concordant
    zeros cancel, but every reported rate would be wrong, and the write-up quotes rates.
    """
    rows = [
        _cell("m1", "thm.unverifiable", "replay_failed"),
        _cell("m2", "thm.unverifiable", "replay_failed"),
        _cell("m1", "thm.real", "success"),
        _cell("m2", "thm.real", "lean_error"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert "thm.unverifiable" not in blocks, (
        "a cell no model could be tested on must not enter the denominator"
    )
    assert blocks["thm.real"][(1, "stepk:1")] == {"m1": 1, "m2": 0}


def test_incomplete_is_real_model_behaviour_and_is_scored(tmp_path):
    """`incomplete` is model-dependent, so it counts as a failure, not a gap.

    Unlike replay_failed, its cell sets differ per model (68, 30, 50 across
    three real lanes, only 8 shared). This is what genuine behavior looks
    like. It must stay in the denominator.
    """
    rows = [
        _cell("m1", "thm.x", "incomplete"),
        _cell("m2", "thm.x", "success"),
    ]
    _, blocks, _ = pa.load_joint_cells([_write(tmp_path, rows)], models=("m1", "m2"))
    assert blocks["thm.x"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
