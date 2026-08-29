"""Test result-file round trips: the safe plain-dict format and legacy tagged files."""

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


def test_dumps_is_exactly_what_dump_writes(tmp_path):
    """``dumps`` is the in-memory twin of ``dump``.

    The S3 store PUTs ``dumps().encode()`` rather than writing a file.
    So any formatting drift between the two would make an S3-stored
    replicate differ byte-for-byte from the local one for the same
    marks. That would stay invisible until something diffed a
    synced-down tree against its local original.
    """
    marks = _sample_marks()
    out = tmp_path / "rep_1.yaml"
    marks.dump(out)
    assert marks.dumps() == out.read_text()


def test_dumps_loads_round_trip():
    marks = _sample_marks()
    assert Marks.loads(marks.dumps()) == marks


def test_loads_reads_the_legacy_tagged_format():
    """Legacy files are read back out of S3 after seeding.

    So the ``!!python/object`` branch stays live on the string path too.
    """
    marks = _sample_marks()
    legacy = yaml.dump(marks, default_flow_style=False, indent=4)
    assert legacy.startswith("!!python/object")
    assert Marks.loads(legacy) == marks


def test_loads_does_not_take_the_unsafe_path_for_a_mention_in_a_response():
    """The legacy check tests the FIRST BYTES, not a substring.

    A model response that happens to contain ``!!python/object`` is ordinary data. If
    that file were routed through ``yaml.unsafe_load``, it would be both a misparse and
    an arbitrary-construction hazard on attacker-influenced text. A substring-based
    check fails this and passes every other test here.
    """
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


#: A REAL legacy-format artifact. It is a genuine chromatic ``moe_intens``
#: result file cut to its first 2 marks and re-dumped with the SAME legacy
#: writer (``yaml.dump``). That subsetting is byte-faithful: the original
#: satisfies ``yaml.dump(yaml.unsafe_load(raw)) == raw`` exactly, so this
#: fixture is precisely what the historical writer would have emitted for
#: those two marks.
LEGACY_FIXTURE = FIXTURES / "legacy_marks_chromatic_moe_intens.yaml"


def test_load_real_legacy_result_file():
    """A genuine pre-safe-dump artifact must stay loadable forever.

    The fixture is committed rather than globbed out of a results tree, so
    this pin cannot go vacuous when those trees move.

    What this actually protects, beyond "the unsafe_load branch runs": every mark in
    this artifact predates BOTH the ``reasoning`` and ``compliance`` fields. So
    ``yaml.unsafe_load`` reconstructs ``Mark`` instances whose ``__dict__`` holds only
    ``answer``, ``query``, ``response``, and ``score``. Those two missing attributes
    resolve only because the dataclass gives them class-level defaults. If ``__slots__``
    were added to ``Mark``, or either field made non-defaulted, every historical result
    file would turn into an ``AttributeError`` the moment anything counted
    ``noncompliant``. Nothing else in this suite would notice.
    """
    assert LEGACY_FIXTURE.is_file(), f"missing fixture {LEGACY_FIXTURE}"
    raw = LEGACY_FIXTURE.read_text()
    assert raw.startswith("!!python/object"), "fixture is not in the legacy format"

    marks = Marks.load(LEGACY_FIXTURE)
    assert marks.model == "qwen/qwen3-30b-a3b-instruct-2507"
    assert len(marks.marks) == 2
    # Tallies must compute over records that carry neither field.
    assert (marks.correct, marks.incorrect, marks.invalid) == (0, 2, 0)
    assert marks.noncompliant == 0
    assert sorted(vars(marks.marks[0])) == ["answer", "query", "response", "score"]
    # The string path must reach the same place as the file path.
    assert Marks.loads(raw) == marks


def test_server_config_round_trips_and_defaults_none():
    marks = _sample_marks()
    assert marks.server_config is None
    assert Marks.loads(marks.dumps()).server_config is None  # key absent pre-field files too

    import dataclasses

    stamped = dataclasses.replace(
        marks, server_config={"instance_type": "p6-b200.48xlarge", "gpu": "8x B200 180GB", "tp": 8}
    )
    loaded = Marks.loads(stamped.dumps())
    assert loaded.server_config == stamped.server_config
    assert loaded == stamped
