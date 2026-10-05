"""Reproduction and analysis of the released Horn results."""

from __future__ import annotations

import io
import json
import random

from smolbench.deduction.horn import repro
from smolbench.deduction.horn.render import ARMS
from smolbench.deduction.horn.stats import contrast, format_p, load_rows, pass_rate


def test_protocol_record_is_complete():
    """The protocol records all models, rungs, and published scores."""
    proto = repro.load_protocol()
    assert proto["seeds"] == "100-199" and proto["replicates"] == 3
    assert proto["arms"] == list(ARMS) and proto["scoring"] == "iclr"
    assert proto["bucket"] == "smolbench-public-release"
    assert proto["region"] == "us-west-2"
    assert proto["prefix"] == "deduction/smolbench-horn-data-v1/"
    assert len(proto["models"]) == 16
    for key, e in proto["models"].items():
        assert str(e["m"]) in proto["rung_digests"], key
        assert set(e["results"]) == {"iclr", "default"}
    for digests in proto["rung_digests"].values():
        assert sorted(map(int, digests)) == list(range(100, 200))


def _row(seed, rep, arm, verdict, rung="m2", model="glm-4.7"):
    return {
        "model": "zai.glm-4.7",
        "spec_key": model,
        "rung": rung,
        "arm": arm,
        "seed": seed,
        "rep": rep,
        "verdict": verdict,
    }


def test_load_rows_dedupes_cells_and_keeps_rungs_apart(tmp_path):
    """Rows deduplicate by cell while keeping different rungs separate."""
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    a.write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                _row(1, 0, "lem", "success"),
                _row(1, 0, "both", "exception"),
                _row(1, 0, "both", "invalid_step"),
            ]
        )
        + "\n{torn"
    )
    b.write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                _row(
                    1, 0, "lem", "invalid_step"
                ),  # duplicate of a's cell: the first read wins
                _row(1, 0, "lem", "success", rung="m6"),
            ]
        )
        + "\n"
    )
    cells, dropped = load_rows([a, b])
    assert cells[("glm-4.7", "m2")]["lem"][1] == [True]
    assert cells[("glm-4.7", "m2")]["both"][1] == [False]
    assert cells[("glm-4.7", "m6")]["lem"][1] == [True]
    assert dropped == {"exception": 1, "unparsable": 1, "duplicate": 1}


def test_pass_rate_and_contrast_are_seed_paired():
    """Contrasts use paired seed results and exact sign flips."""
    lem = {1: [True, True], 2: [True, False]}
    both = {1: [False, False], 2: [True, False], 3: [True, True]}
    assert pass_rate(lem) == 75.0
    mean, lo, hi, p, n = contrast(lem, both, random.Random(0))
    # differences 100 and 0: every sign flip has the same |mean|, so the exact p is 1
    assert (mean, n) == (50.0, 2) and lo <= mean <= hi and p == 1.0
    assert format_p(0.0, 100) == "p<5e-05" and format_p(0.5, 2) == "p=0.5000"


def test_report_compares_with_the_published_values(tmp_path):
    """The report prints reproduced scores next to published values."""
    rows = tmp_path / "rows.jsonl"
    rows.write_text(
        "\n".join(
            json.dumps(
                _row(
                    s,
                    0,
                    arm,
                    "success" if arm == "lem" or s == 0 else "invalid_step",
                    rung="m48",
                )
            )
            for s in range(4)
            for arm in ARMS
        )
        + "\n"
    )
    text = repro.report([rows])
    assert "== glm-4.7 m48: 16 cells, 4 seeds, scoring iclr" in text
    assert "published" in text and "74.0" in text  # the published lem rate


class _FakeS3:
    """An S3 client over an in-memory ``{key: bytes}`` bucket."""

    def __init__(self, objects):
        self.objects = objects
        self.gets = []

    def get_paginator(self, _name):
        """Return a paginator yielding the objects under each requested prefix."""
        objects = self.objects

        class _Pages:
            @staticmethod
            def paginate(Bucket, Prefix):  # pylint: disable=invalid-name
                """Yield the objects matching the requested prefix."""
                del Bucket
                yield {
                    "Contents": [
                        {"Key": key, "Size": len(value)}
                        for key, value in objects.items()
                        if key.startswith(Prefix)
                    ]
                }

        return _Pages()

    def get_object(self, Bucket, Key):  # pylint: disable=invalid-name
        """Return an object body and record its key."""
        del Bucket
        self.gets.append(Key)
        return {"Body": io.BytesIO(self.objects[Key])}


def test_fetch_strips_the_root_and_resumes(tmp_path, monkeypatch):
    """Fetch places the manifest at the results root and skips downloaded objects."""
    proto = repro.load_protocol()
    prefix = proto["prefix"]
    key = f"{prefix}MANIFEST.json"
    client = _FakeS3({key: b'{"files": {}}', "other/MANIFEST.json": b"ignored"})
    monkeypatch.setattr(repro.public_release, "client", lambda _region: client)
    assert repro.main(["fetch", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "MANIFEST.json").read_bytes() == b'{"files": {}}'
    assert not (tmp_path / "other" / "MANIFEST.json").exists()
    assert client.gets == [key]
    assert repro.main(["fetch", "--out", str(tmp_path)]) == 0
    assert client.gets == [key]
