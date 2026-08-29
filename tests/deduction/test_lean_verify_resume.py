"""Tests for scripts/deduction/lean_verify_rows.py, the deferred verification pass.

Pins resume (ALL cells of a group, not ANY), identity-and-occurrence pairing of prior
verdicts onto the current all_rows order, the full-pass sentinel exit gate, and the
pure units (grouping, candidate dedup, RAM cap, S3 paths). Fully offline, both venvs.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import itertools
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests._paths import SCRIPTS

# ``scripts/`` is not an importable package, so the module is loaded by path under a
# name unique to this file.
_SPEC = importlib.util.spec_from_file_location(
    "lean_verify_rows_resume_under_test",
    SCRIPTS / "deduction" / "lean_verify_rows.py",
)
lvr = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = lvr
_SPEC.loader.exec_module(lvr)


def _cell(theorem, k=1, *, rung="stepk:1", rep=0, model="m",
          verdict="unverified", proof="tac", **extra):
    """One ``kind: "cell"`` row carrying the full identity tuple; `extra` lands verbatim."""
    row = {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": rep, "verdict": verdict,
        "candidate_proof": proof, "lean_error": None, "final_state_pp": None,
        "verify_ms": 0, "seed": 0,
    }
    row.update(extra)
    return row


def _sanity(theorem, *, verdict="skipped", applied=0, total=1, ms=0):
    """One ``kind: "sanity"`` row -- the ground-truth replay gate's record."""
    return {"kind": "sanity", "theorem_id": theorem, "verdict": verdict,
            "tactics_applied": applied, "tactics_total": total, "ms": ms,
            "error": None}


def _cells(rows):
    return [r for r in rows if r.get("kind") == "cell"]


def _identity(row):
    """The identity tuple, written independently of the module under test."""
    return (row.get("kind"), row.get("model"), row.get("theorem_id"),
            row.get("k"), row.get("rung"), row.get("replicate_idx"))


class _FakeS3:
    """In-memory stand-in for the S3 client `verify_run` reads and writes."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.n_uploads = 0

    def get_object(self, Bucket, Key):
        from botocore.exceptions import ClientError

        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "no such key"}},
                "GetObject",
            )
        return {"Body": io.BytesIO(self.objects[Key])}

    def upload_file(self, filename, bucket, key):
        self.objects[key] = Path(filename).read_bytes()
        self.n_uploads += 1


class _FakeVerifier:
    """Stands in for ``smolbench.deduction.lean.verify``; `verdict` is what try_tail returns."""

    def __init__(self, verdict="lean_error", sanity_verdict="success"):
        self.verdict = verdict
        self.sanity_verdict = sanity_verdict
        self.tried: list[tuple[str, str]] = []

    @contextlib.contextmanager
    def open_at_step(self, bt, k):
        yield ("dojo", f"state@{k}")

    def try_tail(self, dojo, state_at_k, candidate_text, theorem_id):
        self.tried.append((theorem_id, candidate_text))
        return SimpleNamespace(verdict=self.verdict, error=None,
                               final_state_pp=None)

    def replay_ground_truth(self, bt):
        return SimpleNamespace(verdict=self.sanity_verdict, tactics_applied=5,
                               tactics_total=5, error=None)


_WORKDIRS = itertools.count()


def _dump(rows):
    return "".join(json.dumps(r) + "\n" for r in rows).encode("utf-8")


def _run(monkeypatch, tmp_path, all_rows, prior=None, *, verifier=None, **kw):
    """Drive `verify_run` end-to-end against fakes; return (rc, uploaded rows or None)."""
    monkeypatch.setattr(lvr, "_lookup_theorem", lambda tid: SimpleNamespace(full_name=tid))
    client = _FakeS3()
    rows_key = lvr.run_object_key("", "r", lvr.ROWS_FILENAME)
    verified_key = lvr.run_object_key("", "r", lvr.VERIFIED_FILENAME)
    client.objects[rows_key] = _dump(all_rows)
    if prior is not None:
        client.objects[verified_key] = _dump(prior)

    rc = lvr.verify_run(
        client=client, bucket="b", key_prefix="", run="r", workers=1,
        workdir=tmp_path / f"wd{next(_WORKDIRS)}", verifier=verifier or _FakeVerifier(), **kw,
    )
    # Read back only what this run actually UPLOADED, so a pass that did no work
    # cannot look right off the pre-seeded prior file.
    body = client.objects.get(verified_key) if client.n_uploads else None
    out = [json.loads(l) for l in body.decode().splitlines() if l.strip()] if body else None
    return rc, out


def test_resume_done_groups_all_cells_rule():
    """A half-graded group is not done; sanity rows never complete one; str k coerces."""
    prior = [
        _cell("t1", 1, rung="stepk:1", verdict="success"),
        _cell("t1", 1, rung="hint:2", verdict="unverified"),
        _cell("t2", 1, rung="stepk:1", verdict="lean_error"),
        _cell("t2", 1, rung="hint:2", verdict="success"),
    ]
    assert lvr.resume_done_groups(prior) == {("t2", 1)}
    assert lvr.resume_done_groups([_sanity("t9", verdict="success")]) == set()
    assert lvr.resume_done_groups(
        [_sanity("t1", verdict="success"), _cell("t1", "1", verdict="success")]
    ) == {("t1", 1)}


def test_second_pass_over_a_grown_all_rows_verifies_only_the_new_cells(monkeypatch, tmp_path):
    """Growth keeps graded cells verbatim and verifies exactly the new group."""
    all_rows = [
        _cell("t1", 1, rung="stepk:1"), _cell("t1", 1, rung="hint:2"),
        _cell("t2", 2, rung="stepk:1"), _cell("t2", 2, rung="hint:2"),
        _sanity("t1"), _sanity("t2"),
    ]
    prior = [
        _cell("t1", 1, rung="stepk:1", verdict="success", verify_ms=111),
        _cell("t1", 1, rung="hint:2", verdict="lean_error", verify_ms=222),
        _sanity("t1", verdict="success", applied=5, ms=7),
    ]
    verifier = _FakeVerifier(verdict="incomplete")
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior, verifier=verifier)

    assert rc == 0
    assert [_identity(r) for r in out] == [_identity(r) for r in all_rows]
    by_id = {_identity(r): r for r in out}
    assert {k: r["verdict"] for k, r in by_id.items() if k[0] == "cell"} == {
        ("cell", "m", "t1", 1, "stepk:1", 0): "success",
        ("cell", "m", "t1", 1, "hint:2", 0): "lean_error",
        ("cell", "m", "t2", 2, "stepk:1", 0): "incomplete",
        ("cell", "m", "t2", 2, "hint:2", 0): "incomplete",
    }
    assert by_id[("cell", "m", "t1", 1, "stepk:1", 0)]["verify_ms"] == 111
    assert by_id[("cell", "m", "t1", 1, "hint:2", 0)]["verify_ms"] == 222
    assert {t for t, _ in verifier.tried} == {"t2"}


def test_pairing_is_by_identity_and_occurrence(monkeypatch, tmp_path):
    """Output follows all_rows order; duplicates pair by occurrence; orphans append."""
    a, b, c = _cell("t1", 1), _cell("t2", 1), _cell("t3", 1)
    prior = [
        _cell("t2", 1, verdict="success", verify_ms=22),
        _cell("t1", 1, verdict="lean_error", verify_ms=11),
        _cell("t3", 1, verdict="unverified"),
    ]
    rc, out = _run(monkeypatch, tmp_path, [a, b, c], prior)

    assert rc == 0
    assert [_identity(r) for r in out[:3]] == [_identity(r) for r in (a, b, c)]
    assert len(out) == 4 and out[3]["kind"] == "sanity" and out[3]["theorem_id"] == "t3"
    assert out[0]["verdict"] == "lean_error" and out[0]["verify_ms"] == 11
    assert out[1]["verdict"] == "success" and out[1]["verify_ms"] == 22
    assert out[2]["verdict"] == "lean_error"

    ident = dict(rung="stepk:1", rep=0, model="m")
    rc, out = _run(
        monkeypatch, tmp_path,
        [_cell("t1", 1, **ident, _seq=f"fresh{i}") for i in (1, 2, 3)],
        [_cell("t1", 1, **ident, verdict="exception", _seq="prior1"),
         _cell("t1", 1, **ident, verdict="lean_error", _seq="prior2")],
    )
    assert rc == 0
    assert [r["_seq"] for r in _cells(out)] == ["prior1", "prior2", "fresh3"]

    all_rows = [_cell("t1", 1), _cell("t2", 1)]
    prior = [_cell("t1", 1, verdict="success"),
             _sanity("t9", verdict="success", applied=3, ms=9)]
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior)
    assert rc == 0
    assert [_identity(r) for r in out[:2]] == [_identity(r) for r in all_rows]
    orphans = [r for r in out[2:] if r.get("theorem_id") == "t9"]
    assert len(orphans) == 1
    assert orphans[0]["kind"] == "sanity" and orphans[0]["tactics_applied"] == 3


def test_prior_sanity_verdicts_survive_the_reseed(monkeypatch, tmp_path):
    """A prior pass's ground-truth replay results are not reverted to all_rows placeholders."""
    all_rows = [_sanity("t1"), _cell("t1", 1), _cell("t2", 1), _sanity("t2")]
    prior = [
        _sanity("t1", verdict="success", applied=5, total=5, ms=42),
        _cell("t1", 1, verdict="success"),
    ]
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior)

    assert rc == 0
    assert [_identity(r) for r in out] == [_identity(r) for r in all_rows]
    assert out[0]["verdict"] == "success"
    assert out[0]["tactics_applied"] == 5
    assert out[0]["ms"] == 42
    assert out[3]["kind"] == "sanity" and out[3]["theorem_id"] == "t2"
    assert out[3]["tactics_applied"] == 5
    assert out[2]["verdict"] == "lean_error"


def test_cells_appended_to_an_already_graded_group_are_verified(monkeypatch, tmp_path):
    """A group that GROWS after being graded is pending again, and replays each candidate once."""
    all_rows = [
        _cell("t1", 1, rung="stepk:1", proof="NEW PROOF"),
        _cell("t1", 1, rung="hint:2", proof="NEW PROOF"),
    ]
    prior = [_cell("t1", 1, rung="stepk:1", verdict="success", proof="OLD PROOF")]
    verifier = _FakeVerifier(verdict="incomplete")
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior, verifier=verifier)

    assert rc == 0
    assert out is not None, "the pass must not report success without uploading"
    cells = _cells(out)
    assert [_identity(r) for r in cells] == [_identity(r) for r in all_rows]
    assert [r["verdict"] for r in cells] == ["incomplete", "incomplete"]
    # A matched slot holds the PRIOR row wholesale, so its candidate text is what replays.
    assert sorted(text for _theorem, text in verifier.tried) == ["NEW PROOF", "OLD PROOF"]


@pytest.mark.parametrize(
    "kwargs, verdict, prior, expected_rc",
    [
        ({}, "unverified", None, 2),
        ({}, "success", None, 0),
        ({"limit": 1}, "unverified", None, 0),
        ({"theorem": "t1"}, "unverified", None, 0),
        ({"dry_run": True}, "unverified", None, 0),
        ({}, "unverified", "done_t1", 2),
        ({}, "success", "orphan", 2),
    ],
)
def test_full_pass_sentinel_gate(monkeypatch, tmp_path, kwargs, verdict, prior, expected_rc):
    """A limit-free pass that leaves a sentinel exits non-zero; requested partials do not."""
    all_rows = [_cell("t1", 1), _cell("t2", 2)]
    prior_rows = None
    if prior is not None:
        prior_rows = [_cell("t1", 1, verdict="success")]
        if prior == "orphan":
            prior_rows.append(_cell("t9", 7, verdict="unverified"))

    rc, out = _run(monkeypatch, tmp_path, all_rows, prior_rows,
                   verifier=_FakeVerifier(verdict=verdict), **kwargs)

    assert rc == expected_rc
    if not kwargs:
        # The gate reports, it does not discard: the work is still uploaded.
        assert out is not None and len(_cells(out)) >= 2
    if prior is None and not kwargs:
        assert [r["verdict"] for r in _cells(out)] == [verdict, verdict]
    elif prior is not None:
        # Resume really did mark a group done, so the gate cannot carry a `not done` term.
        assert any(r["verdict"] == "success" for r in _cells(out))
        assert any(r["verdict"] == "unverified" for r in _cells(out))


def test_group_unverified_groups_by_theorem_and_k():
    """Only ``unverified`` cell rows are grouped, keyed by (theorem, int k)."""
    rows = [
        _cell("T.a", 1, rung="stepk:1", proof="simp"),
        _cell("T.a", 1, rung="hint:2", proof="ring"),
        _cell("T.a", 2, rung="stepk:1", proof="simp"),
        _cell("T.b", 0, rung="stepk:1", proof="rfl"),
        _cell("T.a", 1, rung="hint:3", verdict="success", proof="aesop"),
        _sanity("T.a"),
    ]
    groups = lvr.group_unverified(rows)
    assert list(groups) == [("T.a", 1), ("T.a", 2), ("T.b", 0)]
    assert groups[("T.a", 1)] == [0, 1]
    assert groups[("T.a", 2)] == [2]
    assert groups[("T.b", 0)] == [3]
    assert list(lvr.group_unverified([_cell("T.a", "3")])) == [("T.a", 3)]


def test_unique_candidates_dedups_and_fans_out():
    """Byte-identical candidates replay once and the verdict reaches every row."""
    rows = [
        _cell("T.a", 1, rung="stepk:1", proof="simp"),
        _cell("T.a", 1, rung="hint:2", proof="ring"),
        _cell("T.a", 1, rung="hint:3", proof="simp"),
    ]
    uniq = lvr.unique_candidates(rows, [0, 1, 2])
    assert list(uniq) == ["simp", "ring"]
    assert uniq["simp"] == [0, 2]
    assert uniq["ring"] == [1]

    lvr.fan_out_verdict(rows, uniq["simp"], {
        "verdict": "success", "lean_error": None,
        "final_state_pp": None, "verify_ms": 12,
    })
    assert rows[0]["verdict"] == "success" and rows[2]["verdict"] == "success"
    assert rows[0]["verify_ms"] == 12 and rows[2]["verify_ms"] == 12
    assert rows[1]["verdict"] == "unverified"
    assert rows[0]["seed"] == 0 and rows[0]["rung"] == "stepk:1"

    row = _cell("T.a", 1)
    row.pop("candidate_proof")
    assert list(lvr.unique_candidates([row], [0])) == [""]


def test_available_ram_and_worker_cap():
    """RAM parsing and the worker cap read a supplied meminfo, never the host's."""
    meminfo = "MemTotal:       65788432 kB\nMemAvailable:   12582912 kB\nSwapFree: 0 kB\n"
    assert lvr.available_ram_gb(meminfo) == pytest.approx(12.0)
    assert lvr.max_workers_allowed(meminfo) == 2
    with pytest.raises(ValueError):
        lvr.available_ram_gb("MemTotal: 100 kB\n")

    lvr.check_workers(1, meminfo)
    lvr.check_workers(2, meminfo)
    with pytest.raises(SystemExit):
        lvr.check_workers(3, meminfo)
    with pytest.raises(SystemExit):
        lvr.check_workers(0, meminfo)


def test_s3_path_mapping():
    """URI parsing and key construction. The run layout is a fleet contract."""
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs/") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket") == ("bucket", "")
    with pytest.raises(ValueError):
        lvr.parse_s3_uri("https://bucket/key")

    key = lvr.run_object_key("deduction/runs", "scaling_glm-4.7", "verified_rows.jsonl")
    assert key == "deduction/runs/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")


def test_verify_import_guard():
    """On >=3.13 the verify module must raise an ImportError naming the .venv-lean remedy."""
    sys.modules.pop("smolbench.deduction.lean.verify", None)

    if sys.version_info >= (3, 13):
        with pytest.raises(ImportError) as excinfo:
            import smolbench.deduction.lean.verify  # noqa: F401
        assert ".venv-lean" in str(excinfo.value)
    else:
        pytest.importorskip("lean_dojo")
        import smolbench.deduction.lean.verify  # noqa: F401
