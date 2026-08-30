"""Test result-file round trips: the safe plain-dict format and legacy tagged files."""

import dataclasses
from datetime import datetime, timezone

import yaml

from smolbench.evals import Mark, Marks
from tests._paths import FIXTURES


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


#: A genuine legacy-format artifact: a chromatic ``moe_intens`` result file cut to its
#: first 2 marks and re-dumped with the same legacy writer, byte-faithfully.
LEGACY_FIXTURE = FIXTURES / "legacy_marks_chromatic_moe_intens.yaml"


def test_load_real_legacy_result_file():
    """Pre-safe-dump artifacts, whose marks lack reasoning/compliance, stay loadable."""
    assert LEGACY_FIXTURE.is_file(), f"missing fixture {LEGACY_FIXTURE}"
    raw = LEGACY_FIXTURE.read_text()
    # The sniff is the FULL top-level Marks tag, not the bare object prefix.
    assert raw.startswith("!!python/object:smolbench.evals.Marks"), "fixture is not legacy format"

    marks = Marks.load(LEGACY_FIXTURE)
    assert marks.model == "qwen/qwen3-30b-a3b-instruct-2507"
    assert len(marks.marks) == 2
    assert (marks.correct, marks.incorrect, marks.invalid) == (0, 2, 0)
    assert marks.noncompliant == 0
    assert sorted(vars(marks.marks[0])) == ["answer", "query", "response", "score"]
    assert Marks.loads(raw) == marks
