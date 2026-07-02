"""Result-file round trips: the safe plain-dict format and legacy tagged files."""

from datetime import datetime, timezone
from pathlib import Path

import yaml

from smolbench.evals import Mark, Marks

REPO = Path(__file__).resolve().parents[1]


def _sample_marks() -> Marks:
    return Marks(
        model="stub-model",
        marks=(
            Mark(query="q1", answer=7, response="7", score=1, reasoning="think\nlines"),
            Mark(query="q2", answer=True, response="banana", score=None),
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def test_dump_load_round_trip(tmp_path):
    marks = _sample_marks()
    out = tmp_path / "rep_1.yaml"
    marks.dump(out)
    # The file must be safe_load-able (no python/object tags -> no coupling
    # of stored results to this package's class paths).
    raw = out.read_text()
    assert "!!python/object" not in raw
    yaml.safe_load(raw)
    assert Marks.load(out) == marks


def test_load_legacy_tagged_format(tmp_path):
    marks = _sample_marks()
    out = tmp_path / "rep_legacy.yaml"
    with open(out, "w") as fh:
        yaml.dump(marks, fh, default_flow_style=False, indent=4)  # old writer
    assert "!!python/object" in out.read_text()
    assert Marks.load(out) == marks


def test_load_committed_legacy_result_file():
    """The already-committed results tree must stay loadable forever."""
    committed = sorted(
        (REPO / "notebooks" / "periodic" / "results").glob("*/rep_*.yaml")
    )
    if not committed:  # results pruned from a shallow checkout
        return
    marks = Marks.load(committed[0])
    assert marks.marks and marks.correct + marks.incorrect + marks.invalid == len(marks.marks)
