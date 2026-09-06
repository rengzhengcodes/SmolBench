"""Section 5 and 6 of ``statistical_analyses.ipynb`` read rows from S3, not from disk.

The heavy deduction cells used to shell out to ``aws s3 sync``, materialise the
``analysis/2026-08-16`` snapshot in a scratch directory and analyse that, and
they left the post-recovery sensitivity arm out entirely -- the notebook said so
in prose ("the post-recovery SENSITIVITY pool is NOT computed below"). Both are
now the shared reader's job: ``rows_source.resolve_rows_dir`` fetches the 21
lanes' ``verified_rows.jsonl`` from the study's spool prefix, and the SAME
function -- one directory over, with the run marker and the candidate file name
overridden -- fetches the DojoInit recovery rows the sensitivity pool needs.

These tests drive the extracted cell source against an INJECTED fake S3, the
way ``tests/deduction/test_deduction_rows_source.py`` drives the scripts: a fake
``boto3`` module in ``sys.modules`` means the cells run their production code
path (no client parameter, no test-only hook in the notebook) with no network,
no credentials and no real boto3 needed.

Nothing here executes the notebook end to end; each cell is extracted by a
stable needle and ``exec``ed on its own namespace. See
``tests/tooling/_notebook_cells.py`` for that machinery.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from tests.tooling._notebook_cells import (
    STATS_NB,
    cell_source,
    load_analysis_modules,
    load_notebook,
)

#: The recovery run whose rows the sensitivity pool needs, as
#: ``scripts/results/audit_lean_pinning.RECOVERY_RUN`` spells it. The notebook
#: has to name the same run: a sensitivity arm computed from a different
#: recovery would not be the one section 5's report.json summarises.
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


def _fake_bucket(models) -> dict[str, str]:
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
        # The recovery rows carry `recovered_verdict`, not `verdict`, and cover
        # theorems the verified pool does not have: that is what makes the
        # post-recovery pool a DIFFERENT pool, which the report must show.
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

    Two pages regardless of size, exactly as
    ``tests/deduction/test_deduction_rows_source.py`` does it: ``ListObjectsV2``
    caps a response at 1000 keys, so a single-page reader would pass here and
    silently truncate a real listing.
    """

    def __init__(self, objects: dict[str, str], calls: list):
        self._objects = objects
        self._calls = calls

    def paginate(self, *, Bucket, Prefix, Delimiter=None):
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

    def __init__(self, objects: dict[str, str]):
        self.objects = objects
        self.listed: list = []
        self.downloads: list[str] = []

    def get_paginator(self, name):
        assert name == "list_objects_v2", name
        return FakePaginator(self.objects, self.listed)

    def download_file(self, bucket, key, dest):
        self.downloads.append(key)
        Path(dest).write_text(self.objects[key])


@pytest.fixture(scope="module")
def nb() -> dict:
    return load_notebook()


@pytest.fixture(scope="module")
def modules() -> dict:
    return load_analysis_modules()


@pytest.fixture
def fake_s3(modules, monkeypatch) -> FakeS3:
    """A fake S3 the cells reach through their own ``import boto3``.

    Injected as a fake ``boto3`` MODULE rather than passed as a ``client=``
    argument: ``rows_source`` imports boto3 inside the download function, and
    the notebook must not carry a client-injection hook that exists only for
    tests. This exercises the production path.
    """
    client = FakeS3(_fake_bucket(modules["ded_pa"].MODELS))
    monkeypatch.setitem(sys.modules, "boto3",
                        types.SimpleNamespace(client=lambda *a, **kw: client))
    return client


def _exec_cell(nb, needle, namespace):
    """Exec the one cell containing `needle` on `namespace`, and return it."""
    exec(compile(cell_source(nb, needle), str(STATS_NB), "exec"), namespace)
    return namespace


# --- the sync is gone ------------------------------------------------------

def test_no_cell_shells_out_to_aws_s3_sync(nb):
    """The whole point of #44: no cell materialises the store with the AWS CLI."""
    offenders = [i for i, cell in enumerate(nb["cells"])
                 if "s3\", \"sync" in "".join(cell["source"])
                 or "aws s3 sync" in "".join(cell["source"])]
    assert not offenders, f"cells {offenders} still sync the store to a local path"


def test_the_gate_cell_declares_no_local_rows_tree(nb):
    """``RUN_HEAVY``'s cell must not pre-declare a scratch rows directory.

    The reader owns the destination now (a fresh temp directory it reports), so
    a ``ROWS_DIR`` under a notebook-chosen ``SCRATCH`` is dead configuration --
    and dead configuration in a gate cell reads as the supported way in.
    """
    source = cell_source(nb, "RUN_HEAVY = ")
    for dead in ("ROWS_DIR", "SCRATCH", "SNAPSHOT_S3", "SNAPSHOT_REGION"):
        assert dead not in source, f"the RUN_HEAVY cell still declares {dead}"


def test_the_recovery_prose_no_longer_says_the_arm_is_skipped(nb):
    """Section 5's markdown and its recovery-report cell must not contradict the code.

    Both used to state that the post-recovery sensitivity pool is NOT computed,
    which is now false. A stale disclaimer is worse than none: a reader who
    believes it will not look for the row that is right there.
    """
    joined = "\n".join("".join(cell["source"]) for cell in nb["cells"])
    for claim in ("SENSITIVITY pool is NOT computed",
                  "sensitivity arm is left out",
                  "does **not** materialise it"):
        assert claim not in joined, f"notebook still claims: {claim!r}"


# --- the cells, executed ---------------------------------------------------

def test_section_5_fetches_rows_and_the_recovery_arm_from_s3(nb, modules, fake_s3,
                                                             capsys):
    """The heavy cell downloads both trees through `rows_source` and reports both.

    Three claims in one run, because they are one behaviour: the verified rows
    come from the spool prefix through the shared reader, the recovery rows come
    from the same reader one directory over, and the report that prints carries
    the post-recovery sensitivity row that the notebook could not produce before.
    """
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    out = capsys.readouterr().out

    verified = [k for k in fake_s3.downloads if k.endswith("verified_rows.jsonl")]
    recovered = [k for k in fake_s3.downloads if k.endswith("recovered_rows.jsonl")]
    assert len(verified) == len(modules["ded_pa"].MODELS), verified
    assert len(recovered) == len(modules["ded_pa"].MODELS), recovered
    assert all(f"/{RECOVERY_RUN}/" in k for k in recovered), recovered

    # The report itself: the recovery pool is a sensitivity ROW, never the
    # headline. Asserted on the affirmative label `mode_report` prints for a
    # pool that exists (``label += " + DojoInit recovery" if rec else ...``),
    # NOT on the word "recovery": the fallback row for a report run WITHOUT
    # --recovery-dir reads "Post-recovery pools are NOT shown", and the
    # section's standing blurb names the recovery too -- so a substring test
    # would pass on a cell that fetched the rows and then failed to pass them
    # on. The negative assertion below is the other half of that.
    assert "+ DojoInit recovery" in out, out[-2500:]
    assert "Post-recovery pools are NOT shown" not in out, out[-2500:]
    assert namespace["ROWS_DIR"].is_dir()
    assert namespace["RECOVERY_DIR"].is_dir()
    # Neither tree lands inside the repository.
    repo = Path(__file__).resolve().parents[2]
    for landed in (namespace["ROWS_DIR"], namespace["RECOVERY_DIR"]):
        assert repo not in landed.resolve().parents, landed


def test_section_5_reads_the_prefix_the_scripts_read(nb, modules, fake_s3):
    """The listing prefixes must be the study's spool prefix and its recovery run.

    Pinned because the cell used to read a THIRD location (the
    ``analysis/2026-08-16`` snapshot), so "it downloaded something" is not
    evidence that it downloaded the rows the published report reads.
    """
    spool = modules["rows_source"].spool_prefix()
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    listed = [prefix for prefix, _delimiter in fake_s3.listed]
    assert f"{spool}/" in listed, listed[:5]
    assert f"{spool}/{RECOVERY_RUN}/" in listed, listed[:5]


def test_section_6_reuses_the_rows_section_5_already_fetched(nb, modules, fake_s3,
                                                             capsys):
    """hint-vs-noise runs against the SAME directory, downloading nothing again.

    A second ``--s3`` would pull all 21 lanes twice for one report; the reader's
    ``--rows-dir`` exists precisely so a tree already on disk is reused.
    """
    namespace = dict(modules, RUN_HEAVY=True)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    downloads_after_section_5 = len(fake_s3.downloads)
    capsys.readouterr()

    _exec_cell(nb, "hint_vs_noise.main(", namespace)
    out = capsys.readouterr().out
    assert len(fake_s3.downloads) == downloads_after_section_5, fake_s3.downloads
    assert "exit code: 0" in out, out[-2000:]


def test_the_heavy_cells_stay_gated(nb, modules, fake_s3, capsys):
    """With ``RUN_HEAVY`` false the cells touch S3 not at all, and say why.

    The gate is the notebook's contract with a reader who has no credentials:
    it must be the FIRST thing each heavy cell consults, not a branch after the
    download.
    """
    namespace = dict(modules, RUN_HEAVY=False)
    _exec_cell(nb, "RECOVERY_RUN", namespace)
    _exec_cell(nb, "hint_vs_noise.main(", namespace)
    out = capsys.readouterr().out
    assert fake_s3.downloads == []
    assert fake_s3.listed == []
    assert out.lower().count("skipped") >= 2, out


def test_an_incomplete_recovery_fetch_stops_the_cell_by_name(nb, modules, monkeypatch):
    """A partial recovery tree must refuse loudly, not quietly change the pool.

    ``error_bars.lane_outcomes`` reads ``<recovery_dir>/<model>/
    recovered_rows.jsonl`` for EVERY model once a recovery directory is given,
    so a lane missing from S3 would otherwise surface as a bare
    ``FileNotFoundError`` deep inside the report -- or, worse, invite a
    "skip the missing lanes" fallback that would compare a 20-lane recovery
    pool against a 21-lane headline.
    """
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
