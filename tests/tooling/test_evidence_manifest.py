"""Offline tests for scripts/results/evidence_manifest.py: the EVIDENCE.json mechanism."""

import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

from tests._paths import SCRIPTS

PRE = "tarball:../store/r6.tar.gz!r6/preregistered_framing.md"
RAW = "tarball:../store/r6.tar.gz!r6/backup/all_rows.jsonl"
HINT = "AlgHom.fieldRange_of_normal/prompts/hint-2.md"
BLOBS = {
    "REPORT.md": ("# report\n\nEstimates come from `report.json`; the rule was fixed in\n"
                  f"`preregistered_framing.md` and the raw is `all_rows.jsonl`.\nProse: `{HINT}`.\n").encode(),
    "report.json": b'{"n": 399}\n',
    PRE: b"fixed before grading\n",
    RAW: b'{"row": 1}\n'}
ENTRIES = [{"relpath": "REPORT.md", "role": "writeup"}, {"relpath": "report.json", "role": "analysis_input"},
           {"relpath": PRE, "role": "preregistration"}, {"relpath": RAW, "role": "raw", "note": "the true raw"}]
ALLOW = [{"name": HINT, "reason": "prompt path in prose, not an evidence artifact"}]


@pytest.fixture(scope="module")
def em():
    # @dataclass resolves KW_ONLY through sys.modules, which is None for a path exec.
    name = "smolbench_test_evidence_manifest"
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / "results" / "evidence_manifest.py")
    sys.modules[name] = mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_tarball(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for name, blob in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            tf.addfile(info, io.BytesIO(blob))


def _pkg(tmp_path: Path, files: dict[str, bytes]) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir(exist_ok=True)
    for name, blob in files.items():
        (pkg / name).write_bytes(blob)
    return pkg


@pytest.fixture
def good(tmp_path, em):
    """A writeup citing a plain file, a tarball member reached via '..', and an allowlisted name."""
    pkg = _pkg(tmp_path, {n: BLOBS[n] for n in ("REPORT.md", "report.json")})
    (tmp_path / "store").mkdir()
    _make_tarball(tmp_path / "store" / "r6.tar.gz",
                  {"r6/preregistered_framing.md": BLOBS[PRE], "r6/backup/all_rows.jsonl": BLOBS[RAW]})
    return pkg, em.build(pkg, ENTRIES, allowlist=ALLOW)


def test_good_package(good, em, tmp_path):
    pkg, manifest = good
    written = (pkg / em.MANIFEST_NAME).read_bytes()
    assert json.loads(written) == manifest
    assert manifest == {"schema": em.SCHEMA, "allowlist": ALLOW, "entries": [
        dict(e, sha256=hashlib.sha256(BLOBS[e["relpath"]]).hexdigest()) for e in ENTRIES]}
    tree = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    r = em.verify(pkg)
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == tree
    assert (r.ok, r.failures, r.n_entries, len(r.allowlist)) == (True, [], 4, 1)
    assert r.roles == {"writeup": 1, "analysis_input": 1, "preregistration": 1, "raw": 1}
    assert r.citations["REPORT.md"] == [HINT, "all_rows.jsonl", "preregistered_framing.md", "report.json"]
    em.build(pkg, manifest["entries"], allowlist=ALLOW)
    assert (pkg / em.MANIFEST_NAME).read_bytes() == written


@pytest.mark.parametrize(
    "entries, allowlist, exc",
    [([{"relpath": "nope.json", "role": "raw"}], (), FileNotFoundError),
     ([{"relpath": "x.json", "role": "writup"}], (), ValueError),
     ([{"relpath": "x.json", "role": "raw", "sha256": "0" * 64}], (), ValueError),
     ([], [{"name": "x.json"}], ValueError)])
def test_build_refuses(tmp_path, em, entries, allowlist, exc):
    with pytest.raises(exc):
        em.build(_pkg(tmp_path, {"x.json": b"{}"}), entries, allowlist=allowlist)


@pytest.mark.parametrize(
    "mutate, expected",
    [(lambda p, s: (p / "report.json").write_bytes(b'{"n": 400}\n'), ("sha256 mismatch", "report.json")),
     (lambda p, s: (p / "report.json").unlink(), ("missing file", "report.json")),
     (lambda p, s: _make_tarball(s / "r6.tar.gz", {"r6/backup/all_rows.jsonl": BLOBS[RAW]}),
      ("missing tarball member", "preregistered_framing.md")),
     (lambda p, s: (s / "r6.tar.gz").unlink(), ("missing tarball", "r6.tar.gz")),
     (lambda p, s: (p / "REPORT.md").write_bytes(BLOBS["REPORT.md"] + b"\n`pool_analyze.py`\n"),
      ("cited artifact not covered", "pool_analyze.py"))],
    ids=["sha-drift", "missing-file", "missing-member", "missing-tarball", "uncovered"])
def test_verify_fails_on(good, em, tmp_path, mutate, expected):
    pkg, _ = good
    mutate(pkg, tmp_path / "store")
    assert any(all(s in f for s in expected) for f in em.verify(pkg).failures)


def test_coverage_allowlist_and_malformed_manifest(tmp_path, em):
    """Allowlists excuse only the name they name; coverage is by path component, not suffix."""
    pkg = _pkg(tmp_path, {"W.md": b"see `ghost.json`, `other.json`, `all_rows.jsonl`\n",
                          "originals_all_rows.jsonl": b"{}\n"})
    em.build(pkg, [{"relpath": "W.md", "role": "writeup"}, {"relpath": "originals_all_rows.jsonl", "role": "raw"}],
             allowlist=[{"name": "ghost.json", "reason": "illustrative name, no artifact"}])
    r = em.verify(pkg)
    assert not [f for f in r.failures if "ghost.json" in f]
    for name in ("other.json", "all_rows.jsonl"):
        assert [f for f in r.failures if "cited artifact not covered" in f and name in f], r.failures
    assert em.covers("all_rows.jsonl", "sub/all_rows.jsonl") and em.covers("x.json", "x.json")
    assert em.covers("backup/all_rows.jsonl", "r6/backup/all_rows.jsonl")
    assert not em.covers("all_rows.jsonl", "originals_all_rows.jsonl")
    assert not em.covers("backup/all_rows.jsonl", "other/all_rows.jsonl")
    assert not em.covers("r6/backup/all_rows.jsonl", "backup/all_rows.jsonl")
    m = json.loads((pkg / em.MANIFEST_NAME).read_text())
    m["entries"][0]["sha256"] = "not-a-hash"
    (pkg / em.MANIFEST_NAME).write_text(json.dumps(m, indent=2))
    assert any("sha256" in f for f in em.verify(pkg).failures)
    (tmp_path / "nomanifest").mkdir()
    with pytest.raises(FileNotFoundError):
        em.verify(tmp_path / "nomanifest")


def test_cited_artifacts_is_conservative(em):
    text = ("keeps `a.json`, `b.jsonl`, `c.gz`, `d.yaml`, `e.yml`, `f.txt`, `g.md`, `h.sh`, `i.py` and `dir/j.json`; "
            "drops `sha256(pool_analyze.py) = 3824a4`, `--no-enable-prefix-caching`, `verify_run`, "
            "plain a.json outside backticks, and `s3://bucket/prefix`.\n")
    assert em.cited_artifacts(text) == ["a.json", "b.jsonl", "c.gz", "d.yaml", "dir/j.json",
                                        "e.yml", "f.txt", "g.md", "h.sh", "i.py"]
    assert em.cited_artifacts("`x.json` `x.json`\n`y.json`") == ["x.json", "y.json"]
    assert em.cited_artifacts("`broken\nx.json`") == []
