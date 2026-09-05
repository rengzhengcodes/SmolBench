"""Test result-file round trips: the safe plain-dict format and legacy tagged files."""

import dataclasses
from datetime import datetime, timezone

import yaml

from smolbench.evals import Mark, Marks


def _sample_marks() -> Marks:
    return Marks(
        model="stub-model",
        marks=(
            Mark(query="q1", answer=7, response="7", score=1, reasoning="think\nlines"),
            Mark(query="q2", answer=True, response="banana", score=None),
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def test_dump_dumps_load_loads_round_trip(tmp_path):
    """dump/dumps agree byte-for-byte and every reader round-trips."""
    marks = _sample_marks()
    out = tmp_path / "rep_1.yaml"
    marks.dump(out)
    text = out.read_text()
    assert "!!python/object" not in text
    yaml.safe_load(text)
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


def test_loads_uses_first_bytes_not_substring():
    """A response merely mentioning ``!!python/object`` must not take the unsafe path."""
    marks = Marks(
        model="stub-model",
        marks=(
            Mark(
                query="q",
                answer=1,
                response="!!python/object:smolbench.evals.Mark {}",
                score=1,
            ),
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    text = marks.dumps()
    assert "!!python/object" in text and not text.startswith("!!python/object")
    assert Marks.loads(text) == marks




def test_assessed_counts_only_marks_a_compliance_parser_judged():
    """``Marks.assessed`` is the census denominator, added beside ``noncompliant`` (12-26).

    The analysis census previously re-derived this rule with its own,
    different denominator while re-parsing the same YAML the loader had just
    read. The rule pinned here is the one the census must use: a mark counts
    as assessed when it carries EITHER ``COMPLIANT`` (None -- obeyed the
    contract) OR a violation label; ``NOT_ASSESSED`` marks (the field default,
    so pre-field stored results) count as neither compliant nor violating and
    are excluded, keeping a legacy lane from publishing as a collapse.
    """
    from smolbench.evals.quiz import COMPLIANT, NOT_ASSESSED

    def mark(compliance):
        return Mark(query="q", answer=1, response="1", score=1, compliance=compliance)

    marks = Marks(
        model="stub-model",
        marks=(
            mark(COMPLIANT), mark(COMPLIANT),
            mark("empty"), mark("multiple-values"),
            mark(NOT_ASSESSED), mark(NOT_ASSESSED), mark(NOT_ASSESSED),
        ),
        date=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    assert marks.assessed == 4
    assert marks.noncompliant == 2
    # The two properties are consistent by construction: every noncompliant
    # mark is assessed, so the census rate can never exceed 1.0.
    assert marks.noncompliant <= marks.assessed

    # A wholly legacy Marks is UNMEASURED, not compliant: 0, so a caller that
    # divides by it must guard rather than publish a 0% collapse rate.
    legacy = Marks(model="m", marks=(mark(NOT_ASSESSED),),
                   date=datetime(2026, 7, 1, tzinfo=timezone.utc))
    assert legacy.assessed == 0
