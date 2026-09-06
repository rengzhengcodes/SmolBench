"""Gates over the S3 archive, streamed -- never pulled to disk; skipped offline::

    SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/2026-08-25 \\
        .venv/bin/python -m pytest tests/deduction/test_s3_archive.py -q
"""

from __future__ import annotations

import functools
import hashlib
import importlib.util
import io
import json
import posixpath
import sys
import tarfile
from pathlib import Path

import pytest

from smolbench.deduction.lean import corpus
from tests._paths import SCRIPTS

RESULTS = "notebooks/deduction/results"
DATA = "notebooks/deduction/data"
CORPUS = f"{DATA}/leandojo_benchmark_4"


@pytest.fixture(scope="module")
def em():
    """Load scripts/results/evidence_manifest.py by path."""
    spec = importlib.util.spec_from_file_location(
        "evidence_manifest_s3", SCRIPTS / "results" / "evidence_manifest.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture(scope="module")
def tracked(s3_archive) -> set[str]:
    """Every archive-relative path under the results tree; guards against a vacuous pass."""
    out = set(s3_archive.keys(RESULTS))
    assert len(out) >= 30, sorted(out)
    return out


def _sha256_of_reference(archive, manifest_dir: str, relpath: str, em) -> str:
    """sha256 of a manifest reference, streamed from S3 (tarball members via BytesIO)."""
    path, member = em._split_reference(relpath)
    rel = posixpath.normpath(posixpath.join(manifest_dir, path))
    if member is None:
        return archive.sha256(rel)
    with tarfile.open(fileobj=io.BytesIO(archive.read(rel)), mode="r:*") as tf:
        stream = tf.extractfile(member)
        if stream is None:
            raise FileNotFoundError(f"{rel}!{member}")
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
        return h.hexdigest()


def _verify_on_s3(archive, manifest_dir: str, em) -> list[str]:
    """Port of ``em.verify`` over S3 objects; returns the failure list."""
    data = json.loads(archive.text(f"{manifest_dir}/{em.MANIFEST_NAME}"))
    failures: list[str] = []
    raw_entries = data.get("entries")
    assert isinstance(raw_entries, list) and raw_entries, manifest_dir
    valid = [e for i, e in enumerate(raw_entries) if em._check_entry_schema(i, e, failures)]
    allowlist = em._check_allowlist_schema(data.get("allowlist", []), failures)
    candidates = [c for e in valid for c in em._candidates(e["relpath"])]
    allowed = {a["name"] for a in allowlist}
    for entry in valid:
        relpath = entry["relpath"]
        try:
            actual = _sha256_of_reference(archive, manifest_dir, relpath, em)
        except (FileNotFoundError, KeyError, tarfile.TarError) as exc:
            failures.append(f"{relpath}: unresolvable on S3: {exc}")
            continue
        if actual != entry["sha256"]:
            failures.append(f"{relpath}: sha256 mismatch: manifest={entry['sha256']} actual={actual}")
        if entry["role"] != "writeup":
            continue
        path, member = em._split_reference(relpath)
        rel = posixpath.normpath(posixpath.join(manifest_dir, path))
        if member is None:
            text = archive.text(rel)
        else:
            with tarfile.open(fileobj=io.BytesIO(archive.read(rel)), mode="r:*") as tf:
                text = tf.extractfile(member).read().decode("utf-8", errors="replace")
        for name in em.cited_artifacts(text):
            if name in allowed or any(em.covers(name, c) for c in candidates):
                continue
            failures.append(f"{relpath}: cited artifact not covered: {name}")
    return failures


def test_every_tracked_writeup_has_a_verified_manifest(tracked, s3_archive, em):
    """Every .md/.txt under results/ sits in a manifested dir and is listed."""
    writeups = sorted(p for p in tracked
                      if Path(p).suffix in em.WRITEUP_SUFFIXES
                      and Path(p).name != em.MANIFEST_NAME)
    assert len(writeups) >= 4, writeups
    for rel in writeups:
        d = posixpath.dirname(rel)
        mf = f"{d}/{em.MANIFEST_NAME}"
        assert mf in tracked, f"{rel}: no {em.MANIFEST_NAME} in {d}"
        manifest = json.loads(s3_archive.text(mf))
        listed = [e for e in manifest["entries"]
                  if not e["relpath"].startswith("tarball:")
                  and posixpath.normpath(posixpath.join(d, e["relpath"])) == rel]
        assert listed, f"{rel}: not listed in {mf}"
        if rel.endswith(".md"):
            assert listed[0]["role"] == "writeup", \
                f"{rel}: listed as {listed[0]['role']!r}, must be 'writeup' to be scanned"


def test_every_tracked_manifest_verifies(tracked, s3_archive, em):
    """Every EVIDENCE.json in the archive verifies against its objects."""
    manifests = sorted(p for p in tracked if Path(p).name == em.MANIFEST_NAME)
    assert manifests, "no EVIDENCE.json in the archive"
    for mf in manifests:
        failures = _verify_on_s3(s3_archive, posixpath.dirname(mf), em)
        assert not failures, f"{mf}:\n  " + "\n  ".join(failures)


def test_regime_mean_interim_raw_is_marked_superseded(tracked, s3_archive, em):
    """The interim raw under a ``_final_`` name must be marked SUPERSEDED."""
    mf = f"{RESULTS}/runs/regime_mean_2026-08-21/{em.MANIFEST_NAME}"
    assert mf in tracked
    entries = json.loads(s3_archive.text(mf))["entries"]
    interim = [e for e in entries if e["relpath"].endswith("all_rows_leg2_final_raw.jsonl.gz")
               and not e["relpath"].startswith("tarball:")]
    assert len(interim) == 1, entries
    note = interim[0].get("note", "")
    assert "SUPERSEDED" in note.upper(), note
    assert "all_rows_leg2_full_raw.jsonl.gz" in note, note
    assert any(e["relpath"].endswith("!r6-regime/all_rows_leg2_full_raw.jsonl.gz")
               for e in entries), "the true raw is not pinned"


#: The archived Lean3 -> Lean4 declaration-name map. Spelled here rather than
#: imported from `lean3`: this test's subject is the ARCHIVE's contents, and
#: `lean3` no longer carries name-level detection (or this asset's name) after
#: the never-built asset and its rule were removed. The object itself is still
#: in the archive and is still pinned, so a future reader can tell whether it
#: was deleted from S3 or merely stopped being read.
ALIGN_ASSET_NAME = "lean3_align.json.gz"


def test_archived_data_assets_resolve(s3_archive):
    """Replay-passing sidecars exist and the align asset parses from the archive."""
    import gzip

    for split in ("val", "test"):
        name = corpus.replay_passing_path("novel_premises", split).name
        assert s3_archive.exists(f"{DATA}/{name}"), f"archived sidecar missing: {DATA}/{name}"
    raw = gzip.decompress(s3_archive.read(f"{DATA}/{ALIGN_ASSET_NAME}"))
    pairs = json.loads(raw)["lean3_to_lean4"]
    assert len(pairs) > 100
    assert pairs["ADE_inequality.A"] == "ADEInequality.A"


def test_noise_rung_is_token_matched_to_its_hint_counterpart(s3_archive, monkeypatch):
    """``noise:3`` matches ``hint:3``'s token count exactly, on the real corpus."""
    from smolbench.deduction.lean import context, premises

    corpus.reset_caches()

    @functools.lru_cache(maxsize=None)
    def load_split_s3(kind="random", split="val"):
        raw = json.loads(s3_archive.read(f"{CORPUS}/{kind}/{split}.json"))
        return [corpus._from_json(r) for r in raw]

    @functools.lru_cache(maxsize=1)
    def index_s3():
        idx: dict[str, premises.Premise] = {}
        for line in s3_archive.open(f"{CORPUS}/corpus.jsonl").iter_lines():
            rec = json.loads(line)
            for p in rec["premises"]:
                fn = p["full_name"]
                if fn in idx:
                    continue
                idx[fn] = premises.Premise(
                    full_name=fn, code=p["code"], start=tuple(p["start"]),
                    end=tuple(p["end"]), kind=p["kind"], file_path=rec["path"],
                )
        return idx

    monkeypatch.setattr(corpus, "load_split", load_split_s3)
    monkeypatch.setattr(premises, "_index", index_s3)
    sidecar = corpus.replay_passing_path("novel_premises", "val").name
    passing = {json.loads(line)["full_name"]
               for line in s3_archive.text(f"{DATA}/{sidecar}").splitlines() if line.strip()}
    pool = [t for t in load_split_s3("novel_premises", "val") if t.full_name in passing]
    chosen = None
    for theorem in pool[:60]:
        k = len(theorem.traced_tactics) - 1
        hint2 = context._count_tokens(context.render(theorem, k, "hint", 2).text)
        hint3 = context._count_tokens(context.render(theorem, k, "hint", 3).text)
        if hint3 > hint2:
            chosen = (theorem, k, hint3)
            break
    assert chosen is not None, "no theorem exercised the noise padding path"
    theorem, k, hint3_tokens = chosen
    noise3_tokens = context._count_tokens(context.render(theorem, k, "noise", 3).text)
    assert noise3_tokens == hint3_tokens, (
        f"{theorem.full_name} k={k}: noise:3 is {noise3_tokens} tokens but "
        f"hint:3 is {hint3_tokens}"
    )
