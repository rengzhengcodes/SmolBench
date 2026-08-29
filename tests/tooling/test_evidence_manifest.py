"""Test scripts/results/evidence_manifest.py, offline: the EVIDENCE.json mechanism.

``notebooks/*/results/`` is gitignored wholesale (.gitignore:235), so every
tracked file under it is a hand-picked ``git add -f`` and nothing forces a
writeup's cited artifacts into git. An EVIDENCE.json per results directory
closes that hole, but only if the checks have teeth. So the synthetic
fixtures in ``tmp_path`` below prove each failure mode fires on its own: sha
drift, a vanished file, a vanished tarball member, a cited artifact covered
by nothing, and, the subtle one, a citation that a string-suffix match would
wrongly accept (``all_rows.jsonl`` must not be satisfied by
``originals_all_rows.jsonl``). A verify() that always returns ok would pass a
test suite that only checked the happy path. Each of these tests exists to
make the tool say no.

``scripts/`` is not an importable package, so the module loads by path.
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


@pytest.fixture(scope="module")
def em():
    """Load scripts/results/evidence_manifest.py by path.

    The module is registered in ``sys.modules`` before ``exec_module`` and
    removed after. That is importlib's own documented recipe, and here it
    is load-bearing, not cosmetic. Under ``from __future__ import
    annotations``, every annotation is a string, and ``@dataclass``
    resolves ``dataclasses.KW_ONLY`` by looking its own module up in
    ``sys.modules``, which returns None for a module executed by path. So
    the decorator dies with ``AttributeError: 'NoneType' object has no
    attribute '__dict__'`` before any test runs.
    """
    name = "smolbench_test_evidence_manifest"
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / "results" / "evidence_manifest.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
        yield mod
    finally:
        # Leave no global state behind.
        sys.modules.pop(name, None)


# --------------------------------------------------------------------------
# helpers for the synthetic layer
# --------------------------------------------------------------------------

def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _make_tarball(path: Path, members: dict[str, bytes]) -> None:
    """Write a .tar.gz holding ``members`` (member path -> bytes)."""
    with tarfile.open(path, "w:gz") as tf:
        for name, blob in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            tf.addfile(info, io.BytesIO(blob))


@pytest.fixture
def good(tmp_path, em):
    """A minimal but representative package.

    It has a writeup that cites a plain artifact, a tarball member, and an
    allowlisted name, plus a tarball that lives outside the manifest dir,
    so the '..' traversal path is exercised. (The real regime-mean
    manifest reaches up two levels to the preserved tarballs; a
    stay-inside-the-directory guard would break it.)
    """
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    store = tmp_path / "store"
    store.mkdir()

    (pkg / "report.json").write_bytes(b'{"n": 399}\n')
    _make_tarball(store / "r6.tar.gz", {
        "r6/preregistered_framing.md": b"fixed before grading\n",
        "r6/backup/all_rows.jsonl": b'{"row": 1}\n',
    })
    (pkg / "REPORT.md").write_text(
        "# report\n\n"
        "Estimates come from `report.json`; the rule was fixed in\n"
        "`preregistered_framing.md` and the raw is `all_rows.jsonl`.\n"
        "Prose false positive: `AlgHom.fieldRange_of_normal/prompts/hint-2.md`.\n"
    )

    manifest = em.build(
        pkg,
        [
            {"relpath": "REPORT.md", "role": "writeup"},
            {"relpath": "report.json", "role": "analysis_input"},
            {"relpath": "tarball:../store/r6.tar.gz!r6/preregistered_framing.md",
             "role": "preregistration"},
            {"relpath": "tarball:../store/r6.tar.gz!r6/backup/all_rows.jsonl",
             "role": "raw", "note": "the true raw"},
        ],
        allowlist=[{"name": "AlgHom.fieldRange_of_normal/prompts/hint-2.md",
                    "reason": "prompt path in prose, not an evidence artifact"}],
    )
    return pkg, manifest


# --------------------------------------------------------------------------
# layer 1a -- build()
# --------------------------------------------------------------------------

def test_build_round_trips(good, em, tmp_path):
    """build() writes EVIDENCE.json, and what it wrote equals what it returned.

    The shas are the real hashes, not placeholders.
    """
    pkg, manifest = good
    on_disk = json.loads((pkg / em.MANIFEST_NAME).read_text())
    assert on_disk == manifest
    assert manifest["schema"] == em.SCHEMA
    assert [e["relpath"] for e in manifest["entries"]][:2] == ["REPORT.md", "report.json"]
    by_path = {e["relpath"]: e for e in manifest["entries"]}
    assert by_path["report.json"]["sha256"] == _sha((pkg / "report.json").read_bytes())
    assert by_path["tarball:../store/r6.tar.gz!r6/preregistered_framing.md"]["sha256"] == \
        _sha(b"fixed before grading\n")
    assert by_path["tarball:../store/r6.tar.gz!r6/backup/all_rows.jsonl"]["note"] == "the true raw"
    assert manifest["allowlist"][0]["reason"].startswith("prompt path")


def test_build_is_deterministic(good, em):
    """If unchanged inputs are rebuilt, the result must be byte-identical.

    A timestamp or a set-ordered dump would make every rebuild a spurious
    diff, and "the manifest changed" has to mean "the evidence changed."
    """
    pkg, manifest = good
    first = (pkg / em.MANIFEST_NAME).read_bytes()
    em.build(pkg,
             [{"relpath": e["relpath"], "role": e["role"],
               **({"note": e["note"]} if "note" in e else {})}
              for e in manifest["entries"]],
             allowlist=manifest["allowlist"])
    assert (pkg / em.MANIFEST_NAME).read_bytes() == first


def test_build_refuses_missing_file(tmp_path, em):
    """A manifest of ghosts is worse than no manifest."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    with pytest.raises(FileNotFoundError):
        em.build(pkg, [{"relpath": "nope.json", "role": "raw"}])


def test_build_refuses_bad_role(tmp_path, em):
    """The role vocabulary is closed; a typo must not invent a role."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "x.json").write_text("{}")
    with pytest.raises(ValueError):
        em.build(pkg, [{"relpath": "x.json", "role": "writup"}])


def test_build_refuses_contradicting_precomputed_sha(tmp_path, em):
    """If the caller supplies a sha, build() must not silently bless a wrong one.

    Copy-pasting a stale hash is exactly how a manifest starts lying.
    """
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "x.json").write_text("{}")
    with pytest.raises(ValueError):
        em.build(pkg, [{"relpath": "x.json", "role": "raw", "sha256": "0" * 64}])


def test_build_refuses_allowlist_without_reason(tmp_path, em):
    """An allowlist entry with no reason is an undocumented hole."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    with pytest.raises(ValueError):
        em.build(pkg, [], allowlist=[{"name": "x.json"}])


# --------------------------------------------------------------------------
# layer 1b -- verify() on a good manifest
# --------------------------------------------------------------------------

def test_verify_passes_good_manifest(good, em):
    pkg, _ = good
    r = em.verify(pkg)
    assert r.ok, r.failures
    assert r.failures == []
    assert r.n_entries == 4
    assert r.roles == {"writeup": 1, "analysis_input": 1, "preregistration": 1, "raw": 1}
    assert r.citations["REPORT.md"] == [
        "AlgHom.fieldRange_of_normal/prompts/hint-2.md",
        "all_rows.jsonl",
        "preregistered_framing.md",
        "report.json",
    ]
    assert len(r.allowlist) == 1


def test_verify_does_not_extract_into_the_tree(good, em, tmp_path):
    """Streaming, not extraction: verify() must leave the tree exactly as it found it.

    (An extracted 91 MiB scratch dir inside a gitignored results directory
    is how untracked evidence gets born in the first place.)
    """
    pkg, _ = good
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert em.verify(pkg).ok
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert after == before


# --------------------------------------------------------------------------
# layer 1c -- the failure modes, one test each (the teeth)
# --------------------------------------------------------------------------

def test_verify_fails_on_sha_mismatch(good, em):
    """(a) content drifted under a pinned hash."""
    pkg, _ = good
    (pkg / "report.json").write_bytes(b'{"n": 400}\n')  # one byte of drift
    r = em.verify(pkg)
    assert not r.ok
    assert any("sha256 mismatch" in f and "report.json" in f for f in r.failures), r.failures


def test_verify_fails_on_missing_file(good, em):
    """(b) a listed plain file is gone."""
    pkg, _ = good
    (pkg / "report.json").unlink()
    r = em.verify(pkg)
    assert not r.ok
    assert any("missing file" in f and "report.json" in f for f in r.failures), r.failures


def test_verify_fails_on_missing_tarball_member(good, em, tmp_path):
    """(c) the tarball is present but no longer holds the member.

    This is the failure a plain "does the tarball exist?" check would
    sail past.
    """
    pkg, manifest = good
    _make_tarball(tmp_path / "store" / "r6.tar.gz",
                  {"r6/backup/all_rows.jsonl": b'{"row": 1}\n'})
    r = em.verify(pkg)
    assert not r.ok
    assert any("missing tarball member" in f and "preregistered_framing.md" in f
               for f in r.failures), r.failures


def test_verify_fails_on_missing_tarball(good, em, tmp_path):
    """(c') the tarball itself is gone."""
    pkg, _ = good
    (tmp_path / "store" / "r6.tar.gz").unlink()
    r = em.verify(pkg)
    assert not r.ok
    assert any("missing tarball" in f for f in r.failures), r.failures


def test_verify_fails_on_uncovered_citation(good, em):
    """(d) the defect this whole mechanism exists for.

    A writeup cites an artifact that is in neither the entries nor the
    allowlist.
    """
    pkg, _ = good
    (pkg / "REPORT.md").write_text(
        (pkg / "REPORT.md").read_text() + "\nAlso see `pool_analyze.py`.\n")
    r = em.verify(pkg)
    assert not r.ok
    assert any("cited artifact not covered" in f and "pool_analyze.py" in f
               for f in r.failures), r.failures
    # The stale sha of the writeup itself is caught too, independently.
    assert any("sha256 mismatch" in f and "REPORT.md" in f for f in r.failures)


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
    """(e) the subtle one.

    "a suffix of some entry's path" must mean whole path components: `all_rows.jsonl` is
    covered by `sub/all_rows.jsonl` but not by `originals_all_rows.jsonl`, which merely
    ends with those bytes. A str.endswith() implementation passes every other test in
    this file.
    """
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


def test_covers_helper_is_component_wise(em):
    assert em.covers("all_rows.jsonl", "sub/all_rows.jsonl")
    assert em.covers("backup/all_rows.jsonl", "r6/backup/all_rows.jsonl")
    assert em.covers("x.json", "x.json")
    assert not em.covers("all_rows.jsonl", "originals_all_rows.jsonl")
    assert not em.covers("backup/all_rows.jsonl", "other/all_rows.jsonl")
    assert not em.covers("r6/backup/all_rows.jsonl", "backup/all_rows.jsonl")


def test_tarball_member_covers_by_member_path(tmp_path, em):
    """A citation is covered by the member path inside the tarball.

    Coverage is not limited to files on disk; that is the whole point of
    preserving tarballs.
    """
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    _make_tarball(pkg / "r5.tar.gz", {"r5/env.sh": b"export X=1\n"})
    (pkg / "W.md").write_text("the environment was `env.sh`\n")
    em.build(pkg, [{"relpath": "W.md", "role": "writeup"},
                   {"relpath": "tarball:r5.tar.gz!r5/env.sh", "role": "config"}])
    assert em.verify(pkg).ok


# --------------------------------------------------------------------------
# layer 1d -- the scanner
# --------------------------------------------------------------------------

def test_cited_artifacts_is_conservative(em):
    text = (
        "keeps `a.json`, `b.jsonl`, `c.gz`, `d.yaml`, `e.yml`, `f.txt`, `g.md`, "
        "`h.sh`, `i.py` and `dir/j.json`; drops `sha256(pool_analyze.py) = 3824a4`, "
        "`--no-enable-prefix-caching`, `verify_run`, plain a.json outside backticks, "
        "and `s3://bucket/prefix`.\n"
    )
    assert em.cited_artifacts(text) == [
        "a.json", "b.jsonl", "c.gz", "d.yaml", "dir/j.json", "e.yml",
        "f.txt", "g.md", "h.sh", "i.py",
    ]


def test_cited_artifacts_dedupes_and_ignores_newlines(em):
    assert em.cited_artifacts("`x.json` `x.json`\n`y.json`") == ["x.json", "y.json"]
    assert em.cited_artifacts("`broken\nx.json`") == []


# --------------------------------------------------------------------------
# layer 1e -- schema policing
# --------------------------------------------------------------------------

def test_verify_reports_malformed_entry(tmp_path, em):
    """A hand-edited manifest must fail loudly, not be read past."""
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


def test_verify_missing_manifest_raises(tmp_path, em):
    with pytest.raises(FileNotFoundError):
        em.verify(tmp_path)






