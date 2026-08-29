"""Test scripts/results/evidence_manifest.py offline: the EVIDENCE.json mechanism.

``notebooks/*/results/`` is gitignored, so only verify()'s teeth force cited artifacts into git.
"""

from __future__ import annotations

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


@pytest.fixture(scope="module")
def em():
    """Load the module by path; the sys.modules registration is load-bearing."""
    # @dataclass resolves KW_ONLY through sys.modules, which is None for a path exec.
    name = "smolbench_test_evidence_manifest"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "results" / "evidence_manifest.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
        yield mod
    finally:
        sys.modules.pop(name, None)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _make_tarball(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for name, blob in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            tf.addfile(info, io.BytesIO(blob))


@pytest.fixture
def good(tmp_path, em):
    """A writeup citing a plain file, a tarball member reached via '..', and an allowlisted name."""
    pkg, store = tmp_path / "pkg", tmp_path / "store"
    pkg.mkdir()
    store.mkdir()
    (pkg / "report.json").write_bytes(b'{"n": 399}\n')
    _make_tarball(store / "r6.tar.gz", {
        "r6/preregistered_framing.md": b"fixed before grading\n",
        "r6/backup/all_rows.jsonl": b'{"row": 1}\n'})
    (pkg / "REPORT.md").write_text(
        "# report\n\n"
        "Estimates come from `report.json`; the rule was fixed in\n"
        "`preregistered_framing.md` and the raw is `all_rows.jsonl`.\n"
        "Prose false positive: `AlgHom.fieldRange_of_normal/prompts/hint-2.md`.\n")
    manifest = em.build(
        pkg,
        [{"relpath": "REPORT.md", "role": "writeup"},
         {"relpath": "report.json", "role": "analysis_input"},
         {"relpath": PRE, "role": "preregistration"},
         {"relpath": RAW, "role": "raw", "note": "the true raw"}],
        allowlist=[{"name": "AlgHom.fieldRange_of_normal/prompts/hint-2.md",
                    "reason": "prompt path in prose, not an evidence artifact"}])
    return pkg, manifest


def test_build_round_trips(good, em):
    """What build() wrote equals what it returned, with real hashes."""
    pkg, manifest = good
    assert json.loads((pkg / em.MANIFEST_NAME).read_text()) == manifest
    assert manifest["schema"] == em.SCHEMA
    assert [e["relpath"] for e in manifest["entries"]][:2] == ["REPORT.md", "report.json"]
    by_path = {e["relpath"]: e for e in manifest["entries"]}
    assert by_path["report.json"]["sha256"] == _sha((pkg / "report.json").read_bytes())
    assert by_path[PRE]["sha256"] == _sha(b"fixed before grading\n")
    assert by_path[RAW]["note"] == "the true raw"
    assert manifest["allowlist"][0]["reason"].startswith("prompt path")


def test_build_is_deterministic(good, em):
    """Rebuilding unchanged inputs must be byte-identical."""
    pkg, manifest = good
    first = (pkg / em.MANIFEST_NAME).read_bytes()
    em.build(pkg,
             [{"relpath": e["relpath"], "role": e["role"],
               **({"note": e["note"]} if "note" in e else {})}
              for e in manifest["entries"]],
             allowlist=manifest["allowlist"])
    assert (pkg / em.MANIFEST_NAME).read_bytes() == first


@pytest.mark.parametrize(
    "entries, allowlist, exc",
    [([{"relpath": "nope.json", "role": "raw"}], (), FileNotFoundError),
     ([{"relpath": "x.json", "role": "writup"}], (), ValueError),
     ([{"relpath": "x.json", "role": "raw", "sha256": "0" * 64}], (), ValueError),
     ([], [{"name": "x.json"}], ValueError)],
    ids=["missing-file", "bad-role", "contradicting-sha", "allowlist-without-reason"])
def test_build_refuses(tmp_path, em, entries, allowlist, exc):
    """Ghost files, typo'd roles, stale supplied hashes and undocumented allowlist holes."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "x.json").write_text("{}")
    with pytest.raises(exc):
        em.build(pkg, entries, allowlist=allowlist)


def test_verify_passes_good_manifest(good, em, tmp_path):
    """The happy path, and verify() streams rather than extracting into the tree."""
    pkg, _ = good
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    r = em.verify(pkg)
    assert r.ok, r.failures
    assert r.failures == []
    assert r.n_entries == 4
    assert r.roles == {"writeup": 1, "analysis_input": 1, "preregistration": 1, "raw": 1}
    assert r.citations["REPORT.md"] == [
        "AlgHom.fieldRange_of_normal/prompts/hint-2.md", "all_rows.jsonl",
        "preregistered_framing.md", "report.json"]
    assert len(r.allowlist) == 1
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert after == before


@pytest.mark.parametrize(
    "mutate, expected, also",
    [(lambda p, s: (p / "report.json").write_bytes(b'{"n": 400}\n'),
      ("sha256 mismatch", "report.json"), None),
     (lambda p, s: (p / "report.json").unlink(),
      ("missing file", "report.json"), None),
     (lambda p, s: _make_tarball(s / "r6.tar.gz",
                                 {"r6/backup/all_rows.jsonl": b'{"row": 1}\n'}),
      ("missing tarball member", "preregistered_framing.md"), None),
     (lambda p, s: (s / "r6.tar.gz").unlink(),
      ("missing tarball", "r6.tar.gz"), None),
     (lambda p, s: (p / "REPORT.md").write_text(
         (p / "REPORT.md").read_text() + "\nAlso see `pool_analyze.py`.\n"),
      ("cited artifact not covered", "pool_analyze.py"),
      ("sha256 mismatch", "REPORT.md"))],
    ids=["sha-drift", "missing-file", "missing-member", "missing-tarball", "uncovered"])
def test_verify_fails_on(good, em, tmp_path, mutate, expected, also):
    """Each failure mode fires on its own, naming the artifact in one failure line."""
    pkg, _ = good
    mutate(pkg, tmp_path / "store")
    r = em.verify(pkg)
    assert not r.ok
    assert any(all(s in f for s in expected) for f in r.failures), r.failures
    if also:
        assert any(all(s in f for s in also) for f in r.failures), r.failures


def test_allowlisted_citation_is_covered(tmp_path, em):
    """The escape hatch works, and only for the name it names."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "W.md").write_text("see `ghost.json` and `other.json`\n")
    em.build(pkg, [{"relpath": "W.md", "role": "writeup"}],
             allowlist=[{"name": "ghost.json", "reason": "illustrative name, no artifact"}])
    r = em.verify(pkg)
    assert not r.ok
    assert [f for f in r.failures if "cited artifact not covered" in f and "other.json" in f]
    assert not [f for f in r.failures if "ghost.json" in f]


def test_coverage_matches_path_components_not_string_suffix(tmp_path, em):
    """`all_rows.jsonl` is covered by `sub/all_rows.jsonl`, never by `originals_all_rows.jsonl`."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "W.md").write_text("the raw is `all_rows.jsonl`\n")
    (pkg / "originals_all_rows.jsonl").write_text("{}\n")
    em.build(pkg, [{"relpath": "W.md", "role": "writeup"},
                   {"relpath": "originals_all_rows.jsonl", "role": "raw"}])
    r = em.verify(pkg)
    assert not r.ok
    assert any("cited artifact not covered" in f and "all_rows.jsonl" in f
               for f in r.failures), r.failures
    sub = pkg / "sub"
    sub.mkdir()
    (sub / "all_rows.jsonl").write_text("{}\n")
    em.build(pkg, [{"relpath": "W.md", "role": "writeup"},
                   {"relpath": "originals_all_rows.jsonl", "role": "raw"},
                   {"relpath": "sub/all_rows.jsonl", "role": "raw"}])
    assert em.verify(pkg).ok
    assert em.covers("all_rows.jsonl", "sub/all_rows.jsonl")
    assert em.covers("backup/all_rows.jsonl", "r6/backup/all_rows.jsonl")
    assert em.covers("x.json", "x.json")
    assert not em.covers("all_rows.jsonl", "originals_all_rows.jsonl")
    assert not em.covers("backup/all_rows.jsonl", "other/all_rows.jsonl")
    assert not em.covers("r6/backup/all_rows.jsonl", "backup/all_rows.jsonl")


def test_cited_artifacts_is_conservative(em):
    """Backticked artifact-shaped names only, deduped, never across a newline."""
    text = (
        "keeps `a.json`, `b.jsonl`, `c.gz`, `d.yaml`, `e.yml`, `f.txt`, `g.md`, "
        "`h.sh`, `i.py` and `dir/j.json`; drops `sha256(pool_analyze.py) = 3824a4`, "
        "`--no-enable-prefix-caching`, `verify_run`, plain a.json outside backticks, "
        "and `s3://bucket/prefix`.\n")
    assert em.cited_artifacts(text) == [
        "a.json", "b.jsonl", "c.gz", "d.yaml", "dir/j.json", "e.yml",
        "f.txt", "g.md", "h.sh", "i.py"]
    assert em.cited_artifacts("`x.json` `x.json`\n`y.json`") == ["x.json", "y.json"]
    assert em.cited_artifacts("`broken\nx.json`") == []


def test_verify_reports_malformed_entry(tmp_path, em):
    """A hand-edited manifest fails loudly; a missing manifest raises."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "x.json").write_text("{}")
    em.build(pkg, [{"relpath": "x.json", "role": "raw"}])
    m = json.loads((pkg / em.MANIFEST_NAME).read_text())
    m["entries"][0]["sha256"] = "not-a-hash"
    (pkg / em.MANIFEST_NAME).write_text(json.dumps(m, indent=2))
    r = em.verify(pkg)
    assert not r.ok
    assert any("sha256" in f for f in r.failures), r.failures
    (tmp_path / "nomanifest").mkdir()
    with pytest.raises(FileNotFoundError):
        em.verify(tmp_path / "nomanifest")
