"""Section 5 and 6 of ``statistical_analyses.ipynb`` read rows from S3, not from disk.

Both are the shared reader's job: ``rows_source.resolve_rows_dir`` fetches the
21 lanes' ``verified_rows.jsonl`` from the study's spool prefix, and the same
function -- one directory over, with the run marker and file name overridden --
fetches the DojoInit recovery rows the sensitivity pool needs.

These tests drive the extracted cell source against an injected fake S3, the
way ``tests/deduction/test_deduction_rows_source.py`` drives the scripts: a
fake ``boto3`` module in ``sys.modules`` runs the cells' production code path
(no client parameter, no test-only hook) with no network or credentials.

Each cell is extracted by a stable needle and ``exec``ed on its own namespace;
nothing here runs the notebook end to end.
"""

from __future__ import annotations

import json
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests.tooling._notebook_cells import (
    STATS_NB,
    cell_source,
    load_analysis_modules,
    load_notebook,
)

#: Must match ``scripts/results/audit_lean_pinning.RECOVERY_RUN``: a
#: sensitivity arm computed from a different recovery would not be the one
#: section 5's report summarises.
RECOVERY_RUN = "dojoinit_recovery_2026-08-18"

#: Theorem ids and rungs the fake lanes carry. Three rungs because
#: ``hint_vs_noise`` pairs ``hint:3`` against ``noise:3`` and needs both in
#: every lane; eight theorems so the block bootstrap has blocks to resample.
THEOREMS = tuple(f"thm_{i}" for i in range(8))
RUNGS = ("stepk:1", "hint:3", "noise:3")


def _cell_row(model: str, theorem: str, verdict: str, rung: str) -> dict:
    """One graded cell row, in the schema ``power_analysis.grade_verdicts`` reads."""
    return {"kind": "cell", "model": model, "theorem_id": theorem, "k": 1,
            "rung": rung, "replicate_idx": 0, "verdict": verdict}


def _fake_bucket(models: tuple[str, ...]) -> dict[str, str]:
    """Build ``{s3 key: body}`` for a whole study: 21 lanes plus the recovery run.

    Verdicts vary with the lane index so the lanes do not all agree -- an
    all-identical pool makes every contrast degenerate and would let a report
    that computed nothing still print.
    """
    objects: dict[str, str] = {}
    for lane_index, model in enumerate(models):
        rows = [_cell_row(model, theorem,
                          "success" if (i + lane_index) % 3 else "failure", rung)
                for i, theorem in enumerate(THEOREMS) for rung in RUNGS]
        objects[f"deduction_postcutoff/runs/scaling_{model}/verified_rows.jsonl"] = \
            "".join(json.dumps(row) + "\n" for row in rows)
        # `recovered_verdict` (not `verdict`) on theorems the verified pool
        # lacks is what makes this a DIFFERENT pool, which the report must show.
        recovered = []
        for theorem in THEOREMS[:2]:
            row = _cell_row(model, f"rec_{theorem}", "success", "stepk:1")
            row.pop("verdict")
            row["recovered_verdict"] = "success"
            recovered.append(row)
        objects[f"deduction_postcutoff/runs/{RECOVERY_RUN}/{model}/recovered_rows.jsonl"] = \
            "".join(json.dumps(row) + "\n" for row in recovered)
    return objects


class FakePaginator:
    """``list_objects_v2`` over an in-memory bucket, in two pages.

    Two pages because real ``ListObjectsV2`` caps a response at 1000 keys; a
    single-page fake would pass here and hide a reader that truncates.
    """

    def __init__(self, objects: dict[str, str], calls: list) -> None:
        self._objects = objects
        self._calls = calls

    def paginate(
        self, *, Bucket: str, Prefix: str, Delimiter: str | None = None
    ) -> Iterator[dict[str, Any]]:
        self._calls.append((Prefix, Delimiter))
        keys = sorted(k for k in self._objects if k.startswith(Prefix))
        if Delimiter is None:
            half = (len(keys) + 1) // 2
            for chunk in (keys[:half], keys[half:]):
                yield {"Contents": [{"Key": k} for k in chunk]}
            return
        common = sorted({
            Prefix + k[len(Prefix):].split(Delimiter, 1)[0] + Delimiter
            for k in keys if Delimiter in k[len(Prefix):]
        })
        half = (len(common) + 1) // 2
        for chunk in (common[:half], common[half:]):
            yield {"CommonPrefixes": [{"Prefix": p} for p in chunk]}


class FakeS3:
    """Records every listing and download; `download_file` writes the body out."""

    def __init__(self, objects: dict[str, str]) -> None:
        self.objects = objects
        self.listed: list = []
        self.downloads: list[str] = []

    def get_paginator(self, name: str) -> FakePaginator:
        assert name == "list_objects_v2", name
        return FakePaginator(self.objects, self.listed)

    def download_file(self, bucket: str, key: str, dest: str | Path) -> None:
        self.downloads.append(key)
        Path(dest).write_text(self.objects[key])


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


@pytest.fixture(scope="module")
def modules() -> dict:
    return load_analysis_modules()


@pytest.fixture
def fake_s3(
    modules: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> FakeS3:
    """A fake S3 the cells reach through their own ``import boto3``.

    Injected as a fake ``boto3`` module, not a ``client=`` argument:
    ``rows_source`` imports boto3 inside the download function, and the
    notebook must not carry a test-only injection hook.
    """
    client = FakeS3(_fake_bucket(modules["ded_pa"].MODELS))
    monkeypatch.setitem(sys.modules, "boto3",
                        types.SimpleNamespace(client=lambda *a, **kw: client))
    return client


def _exec_cell(
    nb: dict[str, Any], needle: str, namespace: dict[str, Any]
) -> dict[str, Any]:
    """Exec the one cell containing `needle` on `namespace`, and return it."""
    exec(compile(cell_source(nb, needle), str(STATS_NB), "exec"), namespace)
    return namespace


# --- the cells, executed ---------------------------------------------------

def test_section_5_fetches_rows_and_the_recovery_arm_from_s3(
    nb: dict[str, Any], modules: dict[str, Any], fake_s3: FakeS3,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """The heavy cell must download both trees through `rows_source` and report both in one run."""
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    out = capsys.readouterr().out

    verified = [k for k in fake_s3.downloads if k.endswith("verified_rows.jsonl")]
    recovered = [k for k in fake_s3.downloads if k.endswith("recovered_rows.jsonl")]
    assert len(verified) == len(modules["ded_pa"].MODELS), verified
    assert len(recovered) == len(modules["ded_pa"].MODELS), recovered
    assert all(f"/{RECOVERY_RUN}/" in k for k in recovered), recovered

    # Asserted on the affirmative label `mode_report` prints when a recovery
    # pool exists, not the substring "recovery": the no-recovery fallback and
    # the section's own blurb both name "recovery" too, so a plain substring
    # check would pass even if the cell fetched rows and dropped them.
    assert "+ DojoInit recovery" in out, out[-2500:]
    assert "Post-recovery pools are NOT shown" not in out, out[-2500:]
    assert namespace["ROWS_DIR"].is_dir()
    assert namespace["RECOVERY_DIR"].is_dir()
    # Neither tree lands inside the repository.
    repo = Path(__file__).resolve().parents[2]
    for landed in (namespace["ROWS_DIR"], namespace["RECOVERY_DIR"]):
        assert repo not in landed.resolve().parents, landed


def test_section_5_reads_the_prefix_the_scripts_read(
    nb: dict[str, Any], modules: dict[str, Any], fake_s3: FakeS3
) -> None:
    """The listing prefixes must be the study's spool prefix and its recovery run, not just "something downloaded"."""
    spool = modules["rows_source"].spool_prefix()
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    listed = [prefix for prefix, _delimiter in fake_s3.listed]
    assert f"{spool}/" in listed, listed[:5]
    assert f"{spool}/{RECOVERY_RUN}/" in listed, listed[:5]


def test_section_6_reuses_the_rows_section_5_already_fetched(
    nb: dict[str, Any], modules: dict[str, Any], fake_s3: FakeS3,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """hint-vs-noise must reuse section 5's directory, not re-download all 21 lanes via a second `--s3`."""
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    downloads_after_section_5 = len(fake_s3.downloads)
    capsys.readouterr()

    _exec_cell(nb, "hint_vs_noise.main(", namespace)
    out = capsys.readouterr().out
    assert len(fake_s3.downloads) == downloads_after_section_5, fake_s3.downloads
    assert "exit code: 0" in out, out[-2000:]


def test_the_heavy_cells_stay_gated(
    nb: dict[str, Any], modules: dict[str, Any], fake_s3: FakeS3,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """With `RUN_HEAVY` false, the cells must touch S3 not at all and say so: the gate must be checked before any download, not after."""
    namespace = dict(modules, RUN_HEAVY=False)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    _exec_cell(nb, "hint_vs_noise.main(", namespace)
    out = capsys.readouterr().out
    assert fake_s3.downloads == []
    assert fake_s3.listed == []
    assert out.lower().count("skipped") >= 2, out


def test_an_incomplete_recovery_fetch_stops_the_cell_by_name(
    nb: dict[str, Any], modules: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A partial recovery tree must refuse loudly by naming the missing model, not silently compare a short pool against the full headline."""
    objects = _fake_bucket(modules["ded_pa"].MODELS)
    dropped = modules["ded_pa"].MODELS[3]
    del objects[
        f"deduction_postcutoff/runs/{RECOVERY_RUN}/{dropped}/recovered_rows.jsonl"]
    client = FakeS3(objects)
    monkeypatch.setitem(sys.modules, "boto3",
                        types.SimpleNamespace(client=lambda *a, **kw: client))

    namespace = dict(modules, RUN_HEAVY=True)
    with pytest.raises(SystemExit) as excinfo:
        _exec_cell(nb, "RECOVERY_RUN", namespace)
    assert dropped in str(excinfo.value), str(excinfo.value)
