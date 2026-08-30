"""Tests for scripts/deduction/lean_verify_rows.py: resume, pairing, sentinel gate, pure units."""

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
from botocore.exceptions import ClientError

from tests._paths import SCRIPTS

_SPEC = importlib.util.spec_from_file_location(
    "lean_verify_rows_resume_under_test", SCRIPTS / "deduction" / "lean_verify_rows.py")
lvr = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = lvr
_SPEC.loader.exec_module(lvr)

_IDENTITY = ("kind", "model", "theorem_id", "k", "rung", "replicate_idx")
_WORKDIRS = itertools.count()


def _cell(theorem, k=1, *, rung="stepk:1", rep=0, model="m", verdict="unverified",
          proof="tac", **extra):
    return {"kind": "cell", "model": model, "theorem_id": theorem, "k": k, "rung": rung,
            "replicate_idx": rep, "verdict": verdict, "candidate_proof": proof,
            "lean_error": None, "final_state_pp": None, "verify_ms": 0, "seed": 0, **extra}


def _sanity(theorem, *, verdict="skipped", applied=0, total=1, ms=0):
    return {"kind": "sanity", "theorem_id": theorem, "verdict": verdict, "error": None,
            "tactics_applied": applied, "tactics_total": total, "ms": ms}


def _dump(rows):
    return "".join(json.dumps(r) + "\n" for r in rows).encode()


def _cells(rows):
    return [r for r in rows if r.get("kind") == "cell"]


def _proj(rows, *fields):
    return [tuple(r.get(f) for f in fields) for r in rows]


def _ids(rows):  # identity tuples, spelled out independently of the module under test
    return _proj(rows, *_IDENTITY)


class _Fake:
    """S3 client and verifier in one recording fake; `verdict` is what try_tail returns."""

    def __init__(self, verdict="lean_error"):
        self.verdict, self.n_uploads = verdict, 0
        self.objects, self.tried = {}, []

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "no"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def upload_file(self, filename, bucket, key):
        self.objects[key] = Path(filename).read_bytes()
        self.n_uploads += 1

    @contextlib.contextmanager
    def open_at_step(self, bt, k):
        yield ("dojo", f"state@{k}")

    def try_tail(self, dojo, state_at_k, candidate_text, theorem_id):
        self.tried.append((theorem_id, candidate_text))
        return SimpleNamespace(verdict=self.verdict, error=None, final_state_pp=None)

    def replay_ground_truth(self, bt):
        return SimpleNamespace(verdict="success", tactics_applied=5, tactics_total=5, error=None)


def _run(monkeypatch, tmp_path, all_rows, prior=None, *, fake=None, **kw):
    """Drive `verify_run` end-to-end against the fake; return (rc, uploaded rows or None)."""
    monkeypatch.setattr(lvr, "_lookup_theorem", lambda tid: SimpleNamespace(full_name=tid))
    fake = fake or _Fake()
    key = lvr.run_object_key("", "r", lvr.VERIFIED_FILENAME)
    fake.objects[lvr.run_object_key("", "r", lvr.ROWS_FILENAME)] = _dump(all_rows)
    if prior is not None:
        fake.objects[key] = _dump(prior)
    rc = lvr.verify_run(client=fake, bucket="b", key_prefix="", run="r", workers=1,
                        workdir=tmp_path / f"wd{next(_WORKDIRS)}", verifier=fake, **kw)
    # Read back only what this run UPLOADED: a pass that did no work must not look right.
    body = fake.objects.get(key) if fake.n_uploads else None
    return rc, ([json.loads(l) for l in body.decode().splitlines() if l.strip()] if body else None)


def test_second_pass_pairs_by_identity_and_verifies_only_pending_cells(monkeypatch, tmp_path):
    """Graded cells and prior sanity verdicts survive verbatim; new and REGROWN groups verify."""
    all_rows = [_sanity("t1"), _cell("t1", 1, rung="stepk:1"), _cell("t1", 1, rung="hint:2"),
                _cell("t2", 2, rung="stepk:1"), _cell("t2", 2, rung="hint:2"), _sanity("t2"),
                _cell("t3", 3, rung="stepk:1", proof="NEW"),
                _cell("t3", 3, rung="hint:2", proof="NEW"),
                *[_cell("t4", 4, _seq=f"fresh{i}") for i in (1, 2, 3)], _sanity("t4")]
    prior = [_sanity("t1", verdict="success", applied=5, total=5, ms=42),
             _cell("t1", 1, rung="hint:2", verdict="lean_error", verify_ms=222),
             _cell("t3", 3, rung="stepk:1", verdict="success", proof="OLD"),
             _cell("t1", 1, rung="stepk:1", verdict="success", verify_ms=111),
             _sanity("t9", verdict="success", applied=3, ms=9),
             _cell("t4", 4, verdict="exception", _seq="prior1"),
             _cell("t4", 4, verdict="lean_error", _seq="prior2")]
    fake = _Fake(verdict="incomplete")
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior, fake=fake)
    assert rc == 0
    assert _ids(out[:12]) == _ids(all_rows)
    assert sorted(_proj(out[12:], "kind", "theorem_id", "verdict", "tactics_applied")) == [
        ("sanity", "t3", "success", 5), ("sanity", "t9", "success", 3)]
    assert [r["_seq"] for r in _cells(out) if r["theorem_id"] == "t4"] == [
        "prior1", "prior2", "fresh3"]
    assert _proj(_cells(out), "theorem_id", "rung", "verdict") == [
        ("t1", "stepk:1", "success"), ("t1", "hint:2", "lean_error"),
        ("t2", "stepk:1", "incomplete"), ("t2", "hint:2", "incomplete"),
        ("t3", "stepk:1", "incomplete"), ("t3", "hint:2", "incomplete"),
        *[("t4", "stepk:1", "incomplete")] * 3]
    assert _proj(out[1:3], "verify_ms") == [(111,), (222,)]
    assert _proj([out[0], out[5]], "verdict", "tactics_applied") == [("success", 5)] * 2
    assert out[0]["ms"] == 42  # a prior replay is not reverted to the all_rows placeholder
    # t1 skipped; t2 dedups; t3's slot holds the PRIOR row wholesale, so OLD text replays too.
    assert sorted(fake.tried) == [("t2", "tac"), ("t3", "NEW"), ("t3", "OLD"), ("t4", "tac")]


@pytest.mark.parametrize(
    "kwargs, verdict, prior, expected_rc",
    [({}, "unverified", None, 2), ({}, "success", None, 0),
     ({"limit": 1}, "unverified", None, 0), ({"theorem": "t1"}, "unverified", None, 0),
     ({"dry_run": True}, "unverified", None, 0), ({}, "unverified", "done_t1", 2),
     ({}, "success", "orphan", 2)],
)
def test_full_pass_sentinel_gate(monkeypatch, tmp_path, kwargs, verdict, prior, expected_rc):
    """A limit-free pass that leaves a sentinel exits non-zero; requested partials do not."""
    prior_rows = None if prior is None else [_cell("t1", 1, verdict="success")]
    if prior == "orphan":
        prior_rows.append(_cell("t9", 7, verdict="unverified"))
    rc, out = _run(monkeypatch, tmp_path, [_cell("t1", 1), _cell("t2", 2)], prior_rows,
                   fake=_Fake(verdict=verdict), **kwargs)
    assert rc == expected_rc
    if not kwargs:
        assert out is not None and len(_cells(out)) >= 2
        verdicts = [r["verdict"] for r in _cells(out)]
        if prior is None:
            assert verdicts == [verdict, verdict]
        else:
            # Resume really marked a group done, so the gate carries no `not done` term.
            assert {"success", "unverified"} <= set(verdicts)


def test_resume_done_groups_all_cells_rule():
    """A half-graded group is not done; sanity rows never complete one; str k coerces."""
    prior = [_cell("t1", 1, rung="stepk:1", verdict="success"),
             _cell("t1", 1, rung="hint:2", verdict="unverified"),
             _cell("t2", 1, rung="stepk:1", verdict="lean_error"),
             _cell("t2", 1, rung="hint:2", verdict="success")]
    assert lvr.resume_done_groups(prior) == {("t2", 1)}
    assert lvr.resume_done_groups([_sanity("t9", verdict="success")]) == set()
    assert lvr.resume_done_groups(
        [_sanity("t1", verdict="success"), _cell("t1", "1", verdict="success")]) == {("t1", 1)}


def test_group_unverified_dedups_and_fans_out():
    """Only unverified cells group by (theorem, int k); identical candidates replay once."""
    rows = [_cell("T.a", 1, rung="stepk:1", proof="simp"),
            _cell("T.a", 1, rung="hint:2", proof="ring"),
            _cell("T.a", 2, rung="stepk:1", proof="simp"),
            _cell("T.b", 0, rung="stepk:1", proof="rfl"),
            _cell("T.a", 1, rung="hint:3", verdict="success", proof="aesop"),
            _sanity("T.a"), _cell("T.a", "1", rung="hint:4", proof="simp")]
    groups = lvr.group_unverified(rows)
    assert groups == {("T.a", 1): [0, 1, 6], ("T.a", 2): [2], ("T.b", 0): [3]}
    assert list(groups) == [("T.a", 1), ("T.a", 2), ("T.b", 0)]
    uniq = lvr.unique_candidates(rows, groups[("T.a", 1)])
    assert uniq == {"simp": [0, 6], "ring": [1]}
    assert list(uniq) == ["simp", "ring"]
    lvr.fan_out_verdict(rows, uniq["simp"], {"verdict": "success", "lean_error": None,
                                             "final_state_pp": None, "verify_ms": 12})
    assert _proj([rows[0], rows[6], rows[1]], "verdict", "verify_ms") == [
        ("success", 12), ("success", 12), ("unverified", 0)]
    assert rows[0]["seed"] == 0 and rows[0]["rung"] == "stepk:1"
    row = _cell("T.a", 1)
    row.pop("candidate_proof")
    assert list(lvr.unique_candidates([row], [0])) == [""]


def test_ram_cap_and_s3_path_mapping():
    """RAM/worker budget reads a supplied meminfo; the run key layout is a fleet contract."""
    meminfo = "MemTotal:       65788432 kB\nMemAvailable:   12582912 kB\nSwapFree: 0 kB\n"
    assert lvr.available_ram_gb(meminfo) == pytest.approx(12.0)
    assert lvr.max_workers_allowed(meminfo) == 2
    with pytest.raises(ValueError):
        lvr.available_ram_gb("MemTotal: 100 kB\n")
    lvr.check_workers(1, meminfo)
    lvr.check_workers(2, meminfo)
    for bad in (3, 0):
        with pytest.raises(SystemExit):
            lvr.check_workers(bad, meminfo)
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs/") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket") == ("bucket", "")
    with pytest.raises(ValueError):
        lvr.parse_s3_uri("https://bucket/key")
    key = lvr.run_object_key("deduction/runs", "scaling_glm-4.7", "verified_rows.jsonl")
    assert key == "deduction/runs/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")


def test_verify_imports_with_its_lean_backend():
    """A cold import of the verifier needs `lean_interact`, not `lean_dojo`.

    The verifier's backend was swapped to `lean_interact` (which drives
    leanprover-community/repl); `lean_dojo` is still a declared dependency, but
    only for corpus tracing and premise slicing, so importorskipping on it here
    would pin a relationship that no longer exists.

    The pop is restored on the way out: re-executing the module binds a NEW
    object onto the `smolbench.deduction.lean` package, and leaving that in
    place makes `runner._default_verifier()` return something no longer
    identical to another module's imported `verify` -- an order-dependent
    failure. See tests/deduction/test_lean_repl_verifier.py, which pins that
    identity.
    """
    pytest.importorskip("lean_interact")
    from smolbench.deduction import lean as lean_pkg

    saved = sys.modules.pop("smolbench.deduction.lean.verify", None)
    try:
        import smolbench.deduction.lean.verify  # noqa: F401
    finally:
        if saved is not None:
            sys.modules["smolbench.deduction.lean.verify"] = saved
            lean_pkg.verify = saved


def test_default_s3_prefix_resolves_to_the_recollection_keys(monkeypatch, tmp_path):
    """The `--s3-prefix` DEFAULT is built after parsing; nothing else exercises it.

    `--help` proves the parser builds and every other test passes a prefix
    explicitly, so a missing or misordered resolution line would only surface on
    a live run -- as `parse_s3_uri(None)` crashing, or worse, a wrong
    bucket/prefix split writing `verified_rows.jsonl` to the wrong key.
    """
    from smolbench.deduction.lean.runner import DEDUCTION_SPOOL_PREFIX

    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)
    monkeypatch.delenv("LEAN_ALLOW_LEGACY_PREFIX", raising=False)
    args = lvr._build_arg_parser().parse_args([])
    assert args.s3_prefix is None, "the default must NOT be resolved at parser-build time"

    # Drive main() itself, intercepting at list_runs, so this proves main
    # RESOLVES the default -- not merely that the expression would be correct.
    seen = {}

    def _list_runs(client, bucket, key_prefix, pattern):
        seen.update(bucket=bucket, key_prefix=key_prefix)
        return []

    monkeypatch.setattr(lvr, "_build_s3_client", lambda: object())
    monkeypatch.setattr(lvr, "list_runs", _list_runs)
    assert lvr.main(["--dry-run", "--workdir", str(tmp_path)]) == 0
    assert seen == {"bucket": lvr.SPOOL_BUCKET, "key_prefix": DEDUCTION_SPOOL_PREFIX}

    key = lvr.run_object_key(seen["key_prefix"], "scaling_glm-4.7", lvr.VERIFIED_FILENAME)
    assert key == f"{DEDUCTION_SPOOL_PREFIX}/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")

    # An explicit flag still reaches the published pre-cutoff study, with no env
    # opt-in -- that is the read-only analysis path.
    legacy = lvr._build_arg_parser().parse_args(
        ["--s3-prefix", f"s3://{lvr.SPOOL_BUCKET}/deduction/runs"])
    assert lvr.parse_s3_uri(legacy.s3_prefix) == (lvr.SPOOL_BUCKET, "deduction/runs")
