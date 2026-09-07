"""Test result-file round trips through the safe plain-dict format."""

import dataclasses
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from smolbench.evals import Mark, Marks
from smolbench.evals.quiz import COMPLIANT


def mark(compliance: str = COMPLIANT, **kwargs: Any) -> Mark:
    return Mark(query="q", answer=1, response="1", score=1,
                compliance=compliance, **kwargs)


def _sample_marks() -> Marks:
    return Marks(
        model="stub-model",
        marks=(
            Mark(query="q1", answer=7, response="7", score=1,
                 compliance=COMPLIANT, reasoning="think\nlines"),
            Mark(query="q2", answer=True, response="banana", score=None,
                 compliance="empty"),
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def test_dump_dumps_load_loads_round_trip(tmp_path: Path) -> None:
    """dump/dumps agree byte-for-byte and every reader round-trips."""
    marks = _sample_marks()
    out = tmp_path / "rep_1.yaml"
    marks.dump(out)
    text = out.read_text()
    yaml.safe_load(text)
    # A python-object tag would force readers onto yaml.unsafe_load.
    assert "!!python/object" not in text
    assert marks.dumps() == text
    assert Marks.load(out) == Marks.loads(text) == marks
    assert "compliance" in text

    assert marks.server_config is None
    assert Marks.loads(text).server_config is None
    stamped = dataclasses.replace(
        marks, server_config={"instance_type": "p6-b200.48xlarge", "gpu": "8x B200 180GB", "tp": 8}
    )
    loaded = Marks.loads(stamped.dumps())
    assert loaded.server_config == stamped.server_config
    assert loaded == stamped


# ---------------------------------------------------------------------------
# COMPLIANT is an explicit label, not an overloaded None
# ---------------------------------------------------------------------------

def test_compliant_is_a_written_label(tmp_path: Path) -> None:
    """The string is what lands in the YAML, so a stored row says what it means."""
    marks = Marks(model="m", marks=(mark(),),
                  date=datetime(2026, 7, 1, tzinfo=timezone.utc))
    text = marks.dumps()
    assert "compliance: compliant" in text
    assert Marks.loads(text).marks[0].compliance == COMPLIANT


def test_the_census_property_counts_the_constant_not_a_none_test() -> None:
    """``noncompliant`` counts every mark whose label is not `COMPLIANT`."""
    marks = Marks(
        model="m",
        marks=(mark(), mark("empty"), mark("multiple-values")),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    assert marks.noncompliant == 2
    assert marks.noncompliant <= len(marks.marks)
