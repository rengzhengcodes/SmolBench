"""The shared S3 row reader the three deduction analysis scripts use.

Before ``rows_source.py`` existed, only ``power_analysis.py`` could read the
archive, and it landed files as ``<tmp>/scaling_<key>/verified_rows.jsonl``.
``error_bars.py`` and ``hint_vs_noise.py`` -- the scripts the PUBLISHED
deduction numbers come from -- read only a local ``--rows-dir`` laid out as
``<dir>/<model>/verified_rows.jsonl``, a layout nothing in the tree writes, so
they could not read the archive at all.

These tests pin the shared reader's contract with an INJECTED fake S3 client
(no network, no credentials, no boto3 needed for the injected path) and then
drive ``hint_vs_noise.main(["--s3", ...])`` end to end through a monkeypatched
``boto3.client``, which is the only way to exercise the lazy import, the
default-prefix resolution and the layout agreement together.

The scripts are loaded by file path, as they are in production: they run under
``uv run --no-project --with numpy --with scipy`` with no smolbench installed
except through their own repo-root ``sys.path`` insert.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests._paths import NOTEBOOKS

ANALYSIS = NOTEBOOKS / "deduction" / "analysis"

#: Bare module names the deduction and induction analysis scripts share. These
#: scripts import their siblings by bare name off their own ``sys.path``
#: insert, so a cached INDUCTION sibling (left by ``tests/analysis``) would be
#: handed to a deduction script and fail on a symbol only one of them has.
#: Evict foreign siblings before loading. ``rows_source`` is deduction-only
#: today and has no induction twin, but it is listed so that adding one later
#: cannot silently reintroduce the collision this guard exists for.
_BARE_SIBLINGS = ("_power_common", "power_analysis", "paired_analysis", "error_bars",
                  "hint_vs_noise", "rows_source", "significance_report",
                  "extens_vs_noise", "multiplicity_sim")

BUCKET_PREFIX = "deduction_postcutoff/runs/"


def _owned_by(module, directory: Path) -> bool:
    file = getattr(module, "__file__", None)
    return bool(file) and Path(file).resolve().parent == directory.resolve()


def _load(name: str):
    for sibling in _BARE_SIBLINGS:
        mod = sys.modules.get(sibling)
        if mod is not None and not _owned_by(mod, ANALYSIS):
            del sys.modules[sibling]
    spec = importlib.util.spec_from_file_location(
        f"deduction_analysis_{name}", ANALYSIS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rows_source():
    return _load("rows_source")


class FakePaginator:
    """`list_objects_v2` paginator over an in-memory ``{key: body}`` bucket.

    Splits its output over TWO pages regardless of size, so a single-page
    implementation of the caller cannot pass by accident: ``ListObjectsV2``
    caps a response at 1000 keys and continues past that, and the
    retired-artifact scan below is only complete if the caller paginates.
    """

    def __init__(self, objects: "dict[str, str]", calls: list):
        self._objects = objects
        self._calls = calls

    def paginate(self, *, Bucket, Prefix, Delimiter=None):
        self._calls.append(("paginate", Prefix, Delimiter))
        keys = sorted(k for k in self._objects if k.startswith(Prefix))
        if Delimiter is None:
            half = (len(keys) + 1) // 2
            for chunk in (keys[:half], keys[half:]):
                yield {"Contents": [{"Key": k} for k in chunk]}
            return
        # Delimiter mode: roll each key up to its first path segment past
        # `Prefix`, exactly as S3's CommonPrefixes does.
        common = sorted({
            Prefix + k[len(Prefix):].split(Delimiter, 1)[0] + Delimiter
            for k in keys if Delimiter in k[len(Prefix):]
        })
        half = (len(common) + 1) // 2
        for chunk in (common[:half], common[half:]):
            yield {"CommonPrefixes": [{"Prefix": p} for p in chunk]}


class FakeS3:
    """Records every call; `download_file` writes the in-memory body to disk."""

    def __init__(self, objects: "dict[str, str]"):
        self.objects = objects
        self.calls: list = []
        self.downloads: list[str] = []

    def get_paginator(self, name):
        assert name == "list_objects_v2", name
        return FakePaginator(self.objects, self.calls)

    def download_file(self, bucket, key, dest):
        self.downloads.append(key)
        Path(dest).write_text(self.objects[key])


def _bucket(**runs: "dict[str, str]") -> "dict[str, str]":
    """``{run_name: {basename: body}}`` -> a flat ``{key: body}`` bucket."""
    out: dict[str, str] = {}
    for run, files in runs.items():
        for name, body in files.items():
            out[f"{BUCKET_PREFIX}{run}/{name}"] = body
    return out


def test_download_lands_the_rows_dir_layout_the_report_scripts_read(rows_source, tmp_path):
    """``scaling_<key>/`` on S3 becomes ``<key>/`` locally -- one layout, three scripts.

    Stripping the ``scaling_`` prefix is the whole reason one downloader can
    serve all three: it is exactly what `error_bars.lane_outcomes` and
    `hint_vs_noise.main` already expect from ``--rows-dir``, while
    `power_analysis.load_joint_cells` keys models off each row's own ``model``
    field and never looks at the directory name.
    """
    client = FakeS3(_bucket(**{
        "scaling_glm-4.7": {"verified_rows.jsonl": '{"kind": "cell"}\n',
                            "manifest.json": "{}"},
        "scaling_gemma-4-12b": {"verified_rows.jsonl": '{"kind": "cell"}\n'},
        # No candidate present: silently omitted, not an error -- a partially
        # collected study is a legitimate power_analysis input.
        "scaling_ministral-3-3b": {"manifest.json": "{}"},
        # Not a run at all.
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


def test_download_prefers_verified_rows_over_the_all_rows_fallback(rows_source, tmp_path):
    """`candidates` is a PREFERENCE order; the landed basename keeps the choice visible.

    `power_analysis` passes both names so its documented ``all_rows.jsonl``
    fallback survives, and because the candidate name is also the local
    basename, `load_joint_cells`' "this input is unverified" banner still fires
    on the fallback. `error_bars`/`hint_vs_noise` pass only the verified name.
    """
    client = FakeS3(_bucket(**{
        "scaling_glm-4.7": {"verified_rows.jsonl": "V\n", "all_rows.jsonl": "A\n"},
        "scaling_gemma-4-12b": {"all_rows.jsonl": "A\n"},
    }))
    landed = rows_source.download_scaling_rows(
        tmp_path, prefix=BUCKET_PREFIX,
        candidates=("verified_rows.jsonl", "all_rows.jsonl"), client=client)
    assert [p.relative_to(tmp_path).as_posix() for p in landed] == [
        "gemma-4-12b/all_rows.jsonl", "glm-4.7/verified_rows.jsonl"]

    # With the single-element default, the fallback-only lane vanishes instead
    # of arriving under a name that hides what it is.
    other = tmp_path / "strict"
    landed = rows_source.download_scaling_rows(other, prefix=BUCKET_PREFIX, client=client)
    assert [p.relative_to(other).as_posix() for p in landed] == [
        "glm-4.7/verified_rows.jsonl"]


def test_a_superseded_object_in_the_bucket_refuses_before_any_download(rows_source, tmp_path):
    """The retired-artifact guard is reachable on the S3 path, and fires FIRST.

    This is the reason the reader lists a run instead of blind-downloading its
    candidate: with a 404-probe loop an ``all_rows_SUPERSEDED-<stamp>.jsonl``
    object sitting beside the live rows is never seen, so every ``--s3`` reader
    silently produces the complete, plausible, WRONG report that guard exists
    to prevent.

    The teeth are the two assertions AFTER the raise: refusing only once the
    superseded lane's rows are already on disk would leave a poisoned tree for
    a later ``--rows-dir`` run to pick up.
    """
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


def test_resolve_rows_dir_local_path_touches_no_client(rows_source, tmp_path):
    """A ``--rows-dir`` run must be usable with no S3 client and no boto3."""
    client = FakeS3({})
    assert rows_source.resolve_rows_dir(
        rows_dir=tmp_path, s3_prefix=None, client=client) == tmp_path
    assert client.calls == [] and client.downloads == []


@pytest.mark.parametrize("rows_dir, s3_prefix", [
    (None, None),
    (Path("/tmp/somewhere"), "deduction_postcutoff/runs"),
])
def test_resolve_rows_dir_demands_exactly_one_source(rows_source, rows_dir, s3_prefix):
    with pytest.raises(ValueError, match="exactly one of"):
        rows_source.resolve_rows_dir(rows_dir=rows_dir, s3_prefix=s3_prefix)


def test_resolve_rows_dir_refuses_an_empty_prefix(rows_source):
    """An empty prefix would list the entire bucket rather than this study."""
    with pytest.raises(ValueError, match="empty key prefix"):
        rows_source.resolve_rows_dir(rows_dir=None, s3_prefix="/")


def test_resolve_rows_dir_names_the_uri_when_nothing_landed(rows_source):
    client = FakeS3({})
    with pytest.raises(SystemExit) as excinfo:
        rows_source.resolve_rows_dir(
            rows_dir=None, s3_prefix=BUCKET_PREFIX, client=client)
    assert f"s3://{rows_source.S3_BUCKET}/{BUCKET_PREFIX}" in str(excinfo.value)


# ---------------------------------------------------------------------------
# End to end: hint_vs_noise reads the archive with no local tree at all.
# ---------------------------------------------------------------------------


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


def test_hint_vs_noise_runs_from_s3_with_no_local_rows_dir(tmp_path, monkeypatch, capsys):
    """``hint_vs_noise.py --s3`` produces the report from the archive alone.

    This is the issue in one test: before the shared reader, this script could
    only ever read a local ``<model>/verified_rows.jsonl`` tree that nothing in
    the repo writes, so reproducing a published number meant an out-of-band
    ``aws s3 sync``. ``boto3.client`` is monkeypatched rather than a client
    injected, so the lazy import inside `download_scaling_rows` and the
    after-parsing default-prefix resolution are both exercised for real.
    """
    import boto3

    hvn = _load("hint_vs_noise")
    objects = _bucket(**{
        f"scaling_{model}": {"verified_rows.jsonl": _lane_rows(12, b=8)}
        for model in hvn.MODELS
    })
    client = FakeS3(objects)
    monkeypatch.setattr(boto3, "client", lambda *a, **k: client)
    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)

    assert hvn.main(["--s3"]) == 0
    out = capsys.readouterr()

    # The default prefix was resolved AFTER parsing, from spool_prefix().
    assert all(k.startswith(BUCKET_PREFIX) for k in client.downloads), client.downloads
    assert len(client.downloads) == 21
    # The progress line goes to stderr; stdout is the report itself.
    assert "Downloading run rows" in out.err and "Downloading" not in out.out
    assert "DEDUCTION: hint:3 vs noise:3, per model" in out.out
    for model in hvn.MODELS:
        assert model in out.out, f"{model} missing from the report"
