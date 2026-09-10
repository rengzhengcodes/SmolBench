"""Tests for the deduction analysis scripts' shared S3 row reader."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests._paths import NOTEBOOKS
from tests.analysis._trees import load_analysis

ANALYSIS = NOTEBOOKS / "deduction" / "analysis"

BUCKET_PREFIX = "deduction_postcutoff/runs/"


@pytest.fixture(scope="module")
def rows_source() -> ModuleType:
    return load_analysis("rows_source", ANALYSIS)


class FakePaginator:
    """Two-page in-memory `list_objects_v2` paginator.

    Two pages prevent a non-paginating caller from passing accidentally.
    """

    def __init__(self, objects: "dict[str, str]", calls: list[Any]) -> None:
        self._objects = objects
        self._calls = calls

    def paginate(self, *, Bucket: str, Prefix: str,
                 Delimiter: str | None = None) -> Iterator[dict[str, Any]]:
        self._calls.append(("paginate", Prefix, Delimiter))
        keys = sorted(k for k in self._objects if k.startswith(Prefix))
        if Delimiter is None:
            half = (len(keys) + 1) // 2
            for chunk in (keys[:half], keys[half:]):
                yield {"Contents": [{"Key": k} for k in chunk]}
            return
        # Match S3 `CommonPrefixes` by retaining the segment after `Prefix`.
        common = sorted({
            Prefix + k[len(Prefix):].split(Delimiter, 1)[0] + Delimiter
            for k in keys if Delimiter in k[len(Prefix):]
        })
        half = (len(common) + 1) // 2
        for chunk in (common[:half], common[half:]):
            yield {"CommonPrefixes": [{"Prefix": p} for p in chunk]}


class FakeS3:
    """Records every call; `download_file` writes the in-memory body to disk."""

    def __init__(self, objects: "dict[str, str]") -> None:
        self.objects = objects
        self.calls: list = []
        self.downloads: list[str] = []

    def get_paginator(self, name: str) -> FakePaginator:
        assert name == "list_objects_v2", name
        return FakePaginator(self.objects, self.calls)

    def download_file(self, bucket: str, key: str, dest: str | Path) -> None:
        self.downloads.append(key)
        Path(dest).write_text(self.objects[key])


def _bucket(**runs: "dict[str, str]") -> "dict[str, str]":
    """``{run_name: {basename: body}}`` -> a flat ``{key: body}`` bucket."""
    out: dict[str, str] = {}
    for run, files in runs.items():
        for name, body in files.items():
            out[f"{BUCKET_PREFIX}{run}/{name}"] = body
    return out


def test_download_lands_the_rows_dir_layout_the_report_scripts_read(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """S3 `scaling_<key>/` lands as local `<key>/`."""
    client = FakeS3(_bucket(**{
        "scaling_glm-4.7": {"verified_rows.jsonl": '{"kind": "cell"}\n',
                            "manifest.json": "{}"},
        "scaling_gemma-4-12b": {"verified_rows.jsonl": '{"kind": "cell"}\n'},
        # Missing candidates are allowed for partially collected studies.
        "scaling_ministral-3-3b": {"manifest.json": "{}"},
        "corpus": {"metadata.json": "{}"},
    }))
    landed = rows_source.download_scaling_rows(
        tmp_path, prefix=BUCKET_PREFIX, client=client)

    assert landed == sorted([tmp_path / "glm-4.7" / "verified_rows.jsonl",
                             tmp_path / "gemma-4-12b" / "verified_rows.jsonl"])
    assert all(p.read_text() == '{"kind": "cell"}\n' for p in landed)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["gemma-4-12b", "glm-4.7"]
    # Only the chosen candidate is fetched -- manifest.json is listed, not pulled.
    assert sorted(Path(k).name for k in client.downloads) == [
        "verified_rows.jsonl", "verified_rows.jsonl"]


def test_download_prefers_verified_rows_over_the_all_rows_fallback(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """Keep fallback basenames so unverified-input warnings remain accurate."""
    client = FakeS3(_bucket(**{
        "scaling_glm-4.7": {"verified_rows.jsonl": "V\n", "all_rows.jsonl": "A\n"},
        "scaling_gemma-4-12b": {"all_rows.jsonl": "A\n"},
    }))
    landed = rows_source.download_scaling_rows(
        tmp_path, prefix=BUCKET_PREFIX,
        candidates=("verified_rows.jsonl", "all_rows.jsonl"), client=client)
    assert [p.relative_to(tmp_path).as_posix() for p in landed] == [
        "gemma-4-12b/all_rows.jsonl", "glm-4.7/verified_rows.jsonl"]

    # The default omits fallback-only lanes rather than hiding their status.
    other = tmp_path / "strict"
    landed = rows_source.download_scaling_rows(other, prefix=BUCKET_PREFIX, client=client)
    assert [p.relative_to(other).as_posix() for p in landed] == [
        "glm-4.7/verified_rows.jsonl"]


def test_a_superseded_object_in_the_bucket_refuses_before_any_download(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """Superseded S3 artifacts must refuse before writing locally."""
    client = FakeS3(_bucket(**{
        "scaling_glm-4.7": {
            "verified_rows.jsonl": "V\n",
            "all_rows_SUPERSEDED-20260815T000000Z.jsonl": "OLD\n",
        },
    }))
    with pytest.raises(SystemExit) as excinfo:
        rows_source.download_scaling_rows(tmp_path, prefix=BUCKET_PREFIX, client=client)
    message = str(excinfo.value)
    assert "REFUSING SUPERSEDED" in message
    assert "all_rows_SUPERSEDED-20260815T000000Z.jsonl" in message
    assert "scaling_glm-4.7" in message, (
        "the refusal must name the RUN, not just the basename:\n" + message)
    assert client.downloads == [], "downloaded before refusing"
    assert list(tmp_path.iterdir()) == [], "wrote to disk before refusing"


def test_bucket_and_region_come_from_the_config(rows_source: ModuleType) -> None:
    """Read the archive address from `study_config`."""
    from smolbench.evals.study_config import load_study_config

    results = load_study_config().results
    assert (rows_source.S3_BUCKET, rows_source.S3_REGION) == (
        results.bucket, results.region)


def test_resolve_rows_dir_local_path_touches_no_client(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """A ``--rows-dir`` run must be usable with no S3 client and no boto3."""
    client = FakeS3({})
    assert rows_source.resolve_rows_dir(
        rows_dir=tmp_path, s3_prefix=None, client=client) == tmp_path
    assert client.calls == [] and client.downloads == []


@pytest.mark.parametrize("rows_dir, s3_prefix", [
    (None, None),
    (Path("/tmp/somewhere"), "deduction_postcutoff/runs"),
])
def test_resolve_rows_dir_demands_exactly_one_source(
    rows_source: ModuleType, rows_dir: Path | None, s3_prefix: str | None
) -> None:
    with pytest.raises(ValueError, match="exactly one of"):
        rows_source.resolve_rows_dir(rows_dir=rows_dir, s3_prefix=s3_prefix)


def test_resolve_rows_dir_refuses_an_empty_prefix(rows_source: ModuleType) -> None:
    """An empty prefix would list the entire bucket rather than this study."""
    with pytest.raises(ValueError, match="empty key prefix"):
        rows_source.resolve_rows_dir(rows_dir=None, s3_prefix="/")


def test_resolve_rows_dir_names_the_uri_when_nothing_landed(rows_source: ModuleType) -> None:
    client = FakeS3({})
    with pytest.raises(SystemExit) as excinfo:
        rows_source.resolve_rows_dir(
            rows_dir=None, s3_prefix=BUCKET_PREFIX, client=client)
    assert f"s3://{rows_source.S3_BUCKET}/{BUCKET_PREFIX}" in str(excinfo.value)


def _lane_rows(n_theorems: int, b: int) -> str:
    """One lane's verified rows: `b` cells where hint:3 wins and noise:3 does not."""
    lines = []
    for i in range(n_theorems):
        hint_ok = i < b
        for rung, ok in (("hint:3", hint_ok), ("noise:3", False)):
            lines.append(json.dumps({
                "kind": "cell", "theorem_id": f"T{i}", "k": 1, "rung": rung,
                "replicate_idx": 0, "verdict": "success" if ok else "lean_error"}))
    return "\n".join(lines) + "\n"


def test_hint_vs_noise_runs_from_s3_with_no_local_rows_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None:
    """hint_vs_noise.py --s3 produces the report from the archive alone."""
    from smolbench.evals import _aws

    hvn = load_analysis("hint_vs_noise", ANALYSIS)
    objects = _bucket(**{
        f"scaling_{model}": {"verified_rows.jsonl": _lane_rows(12, b=8)}
        for model in hvn.MODELS
    })
    client = FakeS3(objects)
    monkeypatch.setattr(_aws, "fresh_client", lambda *a, **k: client)
    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)

    assert hvn.main(["--s3"]) == 0
    out = capsys.readouterr()

    assert all(k.startswith(BUCKET_PREFIX) for k in client.downloads), client.downloads
    assert len(client.downloads) == 21
    # Progress goes to stderr so stdout remains the report.
    assert "Downloading run rows" in out.err and "Downloading" not in out.out
    assert "DEDUCTION: hint:3 vs noise:3, per model" in out.out
    for model in hvn.MODELS:
        assert model in out.out, f"{model} missing from the report"


# --- the recovery tree: same reader, a different run naming convention -----
#
# The DojoInit recovery spools to ``<prefix>/dojoinit_recovery_<date>/<lane>/
# recovered_rows.jsonl`` (the key shape ``scripts/results/audit_lean_pinning.py``
# constructs). That is a run directory that does NOT start with ``scaling_``
# and a file that is not ``verified_rows.jsonl``, so the default filter
# excluded it and the sensitivity pool it feeds was unreachable from S3. One
# optional `run_marker` opens it without moving the default an inch.

RECOVERY_PREFIX = f"{BUCKET_PREFIX}dojoinit_recovery_2026-08-18/"


def _recovery_bucket(**lanes: str) -> "dict[str, str]":
    """``{lane: body}`` -> a flat bucket under the recovery run's prefix."""
    return {f"{RECOVERY_PREFIX}{lane}/recovered_rows.jsonl": body
            for lane, body in lanes.items()}


def test_an_unmarked_run_layout_lands_under_its_own_directory_name(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """``run_marker=""`` accepts every run directory and strips nothing from it.

    The landed tree has to be ``<lane>/recovered_rows.jsonl``, because that is
    what `error_bars.lane_outcomes` reads from ``--recovery-dir`` -- the same
    ``<model>/<file>`` shape the ``scaling_`` path produces, reached by turning
    the marker off rather than by teaching the reader a second layout.
    """
    client = FakeS3(_recovery_bucket(**{"glm-4.7": "R\n", "gemma-4-12b": "R\n"}))
    landed = rows_source.download_scaling_rows(
        tmp_path, prefix=RECOVERY_PREFIX, candidates=("recovered_rows.jsonl",),
        client=client, run_marker="")
    assert [p.relative_to(tmp_path).as_posix() for p in landed] == [
        "gemma-4-12b/recovered_rows.jsonl", "glm-4.7/recovered_rows.jsonl"]
    assert all(p.read_text() == "R\n" for p in landed)


def test_the_default_marker_still_excludes_the_recovery_run(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """The default is unchanged: without the override the recovery tree is invisible.

    This is the behaviour ``error_bars.py``'s ``--recovery-dir`` help text
    describes, and the three existing callers depend on it -- a recovery run
    sitting beside the lanes must never be pulled into a ``--s3`` row fetch.
    """
    client = FakeS3(dict(
        _recovery_bucket(**{"glm-4.7": "R\n"}),
        **_bucket(**{"scaling_glm-4.7": {"verified_rows.jsonl": "V\n"}}),
    ))
    landed = rows_source.download_scaling_rows(
        tmp_path, prefix=BUCKET_PREFIX, client=client)
    assert [p.relative_to(tmp_path).as_posix() for p in landed] == [
        "glm-4.7/verified_rows.jsonl"]
    assert all("dojoinit" not in key for key in client.downloads), client.downloads


def test_the_retired_artifact_guard_covers_the_unmarked_layout(
    rows_source: ModuleType, tmp_path: Path
) -> None:
    """Turning the marker off must not turn the superseded guard off with it.

    The recovery tree is archived data that has been re-spooled before; a
    retired copy beside it is the same "complete, plausible, WRONG report"
    hazard as on the ``scaling_`` path, and refusing has to happen before
    anything lands.
    """
    objects = _recovery_bucket(**{"glm-4.7": "R\n"})
    objects[f"{RECOVERY_PREFIX}glm-4.7/recovered_rows_SUPERSEDED-20260820T000000Z.jsonl"] = "OLD\n"
    client = FakeS3(objects)
    with pytest.raises(SystemExit, match="REFUSING SUPERSEDED"):
        rows_source.download_scaling_rows(
            tmp_path, prefix=RECOVERY_PREFIX, candidates=("recovered_rows.jsonl",),
            client=client, run_marker="")
    assert client.downloads == [], "downloaded before refusing"
    assert list(tmp_path.iterdir()) == [], "wrote to disk before refusing"


def test_resolve_rows_dir_passes_the_marker_through(rows_source: ModuleType) -> None:
    """The one-call entry point reaches the recovery tree too, guard and all.

    The notebook's section 5 calls `resolve_rows_dir`, not the downloader, so
    the passthrough is the difference between "the sensitivity arm is fetched
    with the empty-result refusal" and "the notebook re-implements the fetch".
    """
    client = FakeS3(_recovery_bucket(**{"glm-4.7": "R\n"}))
    landed_dir = rows_source.resolve_rows_dir(
        rows_dir=None, s3_prefix=RECOVERY_PREFIX.rstrip("/"),
        candidates=("recovered_rows.jsonl",), client=client, run_marker="")
    assert (landed_dir / "glm-4.7" / "recovered_rows.jsonl").read_text() == "R\n"

    # And the empty-result refusal still names what it searched.
    with pytest.raises(SystemExit, match="recovered_rows.jsonl"):
        rows_source.resolve_rows_dir(
            rows_dir=None, s3_prefix=f"{BUCKET_PREFIX}nothing-here",
            candidates=("recovered_rows.jsonl",), client=FakeS3({}), run_marker="")
