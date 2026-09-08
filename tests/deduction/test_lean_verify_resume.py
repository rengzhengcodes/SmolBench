"""Tests for scripts/deduction/lean_verify_rows.py: resume, pairing, sentinel gate, pure units."""

from __future__ import annotations

import contextlib
import io
import itertools
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import pytest
from botocore.exceptions import ClientError

from conftest import cell_row
from tests._paths import SCRIPTS, load_by_path

lvr = load_by_path(
    SCRIPTS / "deduction" / "lean_verify_rows.py", "lean_verify_rows_resume_under_test"
)

_IDENTITY = ("kind", "model", "theorem_id", "k", "rung", "replicate_idx")
_WORKDIRS = itertools.count()


def _cell(theorem: str, k: int = 1, *, rung: str = "stepk:1", rep: int = 0,
          model: str = "m", verdict: str = "unverified", proof: str = "tac",
          **extra: Any) -> dict[str, Any]:
    return cell_row(model=model, theorem_id=theorem, k=k, rung=rung,
                    replicate_idx=rep, verdict=verdict, candidate_proof=proof, **extra)


def _dump(rows: list[dict[str, Any]]) -> bytes:
    return "".join(json.dumps(r) + "\n" for r in rows).encode()


def _cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("kind") == "cell"]


def _proj(rows: list[dict[str, Any]], *fields: str) -> list[tuple[Any, ...]]:
    return [tuple(r.get(f) for f in fields) for r in rows]


def _ids(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:  # identity tuples, spelled out independently of the module under test
    return _proj(rows, *_IDENTITY)


class _Fake:
    """S3 client and verifier in one recording fake; `verdict` is what try_tail returns."""

    def __init__(self, verdict: str = "lean_error") -> None:
        self.verdict, self.n_uploads = verdict, 0
        self.objects, self.tried = {}, []

    def get_object(self, Bucket: str, Key: str) -> dict[str, io.BytesIO]:
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "no"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def upload_file(self, filename: str | Path, bucket: str, key: str) -> None:
        self.objects[key] = Path(filename).read_bytes()
        self.n_uploads += 1

    @contextlib.contextmanager
    def open_at_step(self, bt: Any, k: int) -> Iterator[tuple[str, str]]:
        yield ("dojo", f"state@{k}")

    def try_tail(self, dojo: str, state_at_k: str, candidate_text: str,
                 theorem_id: str) -> SimpleNamespace:
        self.tried.append((theorem_id, candidate_text))
        return SimpleNamespace(verdict=self.verdict, error=None, final_state_pp=None)

    def replay_ground_truth(self, bt: Any) -> SimpleNamespace:
        return SimpleNamespace(verdict="success", tactics_applied=5, tactics_total=5, error=None)


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
         all_rows: list[dict[str, Any]], prior: list[dict[str, Any]] | None = None,
         *, fake: _Fake | None = None,
         **kw: Any) -> tuple[int, list[dict[str, Any]] | None]:
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


def test_second_pass_pairs_by_identity_and_verifies_only_pending_cells(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Graded cells and prior sanity verdicts survive verbatim; new and REGROWN groups verify."""
    all_rows = [cell_row(kind="sanity", theorem_id="t1"),
                _cell("t1", 1, rung="stepk:1"), _cell("t1", 1, rung="hint:2"),
                _cell("t2", 2, rung="stepk:1"), _cell("t2", 2, rung="hint:2"), cell_row(kind="sanity", theorem_id="t2"),
                _cell("t3", 3, rung="stepk:1", proof="NEW"),
                _cell("t3", 3, rung="hint:2", proof="NEW"),
                *[_cell("t4", 4, _seq=f"fresh{i}") for i in (1, 2, 3)],
                cell_row(kind="sanity", theorem_id="t4")]
    prior = [cell_row(kind="sanity", theorem_id="t1", verdict="success",
                      tactics_applied=5, tactics_total=5, ms=42, error=None),
             _cell("t1", 1, rung="hint:2", verdict="lean_error", verify_ms=222),
             _cell("t3", 3, rung="stepk:1", verdict="success", proof="OLD"),
             _cell("t1", 1, rung="stepk:1", verdict="success", verify_ms=111),
             cell_row(kind="sanity", theorem_id="t9", verdict="success",
                      tactics_applied=3, ms=9, error=None),
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
def test_full_pass_sentinel_gate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                 kwargs: dict[str, Any], verdict: str, prior: str | None,
                                 expected_rc: int) -> None:
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


def test_resume_done_groups_all_cells_rule() -> None:
    """A half-graded group is not done; sanity rows never complete one."""
    prior = [_cell("t1", 1, rung="stepk:1", verdict="success"),
             _cell("t1", 1, rung="hint:2", verdict="unverified"),
             _cell("t2", 1, rung="stepk:1", verdict="lean_error"),
             _cell("t2", 1, rung="hint:2", verdict="success")]
    assert lvr.resume_done_groups(prior) == {("t2", 1)}
    assert lvr.resume_done_groups([
        cell_row(kind="sanity", theorem_id="t9", verdict="success")]) == set()
    assert lvr.resume_done_groups(
        [cell_row(kind="sanity", theorem_id="t1", verdict="success"),
         _cell("t1", 1, verdict="success")]) == {("t1", 1)}


def test_group_unverified_dedups_and_fans_out() -> None:
    """Only unverified cells group by (theorem, k); identical candidates replay once."""
    rows = [_cell("T.a", 1, rung="stepk:1", proof="simp"),
            _cell("T.a", 1, rung="hint:2", proof="ring"),
            _cell("T.a", 2, rung="stepk:1", proof="simp"),
            _cell("T.b", 0, rung="stepk:1", proof="rfl"),
            _cell("T.a", 1, rung="hint:3", verdict="success", proof="aesop"),
            cell_row(kind="sanity", theorem_id="T.a"),
            _cell("T.a", 1, rung="hint:4", proof="simp")]
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


def test_ram_cap_and_s3_path_mapping() -> None:
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
    key = lvr.run_object_key("deduction/runs", "scaling_glm-4.7", "verified_rows.jsonl")
    assert key == "deduction/runs/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")


def test_default_s3_prefix_resolves_to_the_recollection_keys(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--s3-prefix's default; every other test passes a prefix explicitly, so a wrong default would only surface on a live run."""
    from smolbench.evals.spool import DEDUCTION_SPOOL_PREFIX

    monkeypatch.delenv("LEAN_SPOOL_PREFIX", raising=False)

    # Drive main() itself, intercepting at list_runs, so this proves main resolves
    # the default rather than merely computing it correctly.
    seen = {}

    def _list_runs(client: Any, bucket: str, key_prefix: str, pattern: str) -> list[str]:
        seen.update(bucket=bucket, key_prefix=key_prefix)
        return []

    monkeypatch.setattr(lvr, "_build_s3_client", lambda: object())
    monkeypatch.setattr(lvr, "list_runs", _list_runs)
    assert lvr.main(["--dry-run", "--workdir", str(tmp_path)]) == 0
    assert seen == {"bucket": lvr.SPOOL_BUCKET, "key_prefix": DEDUCTION_SPOOL_PREFIX}

    key = lvr.run_object_key(seen["key_prefix"], "scaling_glm-4.7", lvr.VERIFIED_FILENAME)
    assert key == f"{DEDUCTION_SPOOL_PREFIX}/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")

    # An explicit flag overrides the default.
    other = lvr._build_arg_parser().parse_args(
        ["--s3-prefix", f"s3://{lvr.SPOOL_BUCKET}/somewhere/else"])
    assert lvr.parse_s3_uri(other.s3_prefix) == (lvr.SPOOL_BUCKET, "somewhere/else")


# A group of only replay_failed/exception cells is not done.


def test_resume_treats_an_all_replay_failed_group_as_pending() -> None:
    """A group where every cell reads replay_failed/exception was never measured and must stay pending; resume_done_groups used to treat "no unverified cell" as done, disagreeing with error_bars, which scores those same cells as failures."""
    unmeasured = [_cell("T", rung="stepk:1", verdict="replay_failed"),
                  _cell("T", rung="hint:2", verdict="exception")]
    assert lvr.resume_done_groups(unmeasured) == set(), (
        "a group whose every cell is replay_failed/exception was never measured"
    )
    mixed = unmeasured + [_cell("T", rung="hint:3", verdict="lean_error")]
    assert lvr.resume_done_groups(mixed) == {("T", 1)}, (
        "one real verdict is a measurement; do not retry the whole group"
    )
    graded = [_cell("U", rung="stepk:1", verdict="success")]
    assert lvr.resume_done_groups(graded) == {("U", 1)}
    pending_sentinel = [_cell("V", rung="stepk:1", verdict="unverified")]
    assert lvr.resume_done_groups(pending_sentinel) == set()


# A torn final line, and per-run isolation.


def test_download_rows_tolerates_and_reports_a_torn_final_line(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """A half-written last line (SIGKILL mid-write on a spot box) must be dropped AND reported, not silently swallowed alongside real corruption."""
    fake = _Fake()
    good = [_cell("T", rung="stepk:1"), cell_row(kind="sanity", theorem_id="T")]
    fake.objects["k"] = _dump(good)[:-1] + b'\n{"kind": "cell", "theo'

    with caplog.at_level(0):
        rows = lvr.download_rows(fake, "b", "k", tmp_path / "rows.jsonl")

    assert _ids(rows) == _ids(good), "the intact rows must survive"
    assert "torn" in caplog.text.lower() or "truncat" in caplog.text.lower(), (
        "the drop must be reported, not silent:\n" + caplog.text
    )


def test_download_rows_still_refuses_mid_file_corruption(tmp_path: Path) -> None:
    """Only the final line is recoverable; a corrupt line elsewhere is real damage that must propagate, since resume can't re-derive a row from the middle of a file."""
    fake = _Fake()
    fake.objects["k"] = b'{"kind": "cell", "theo\n' + _dump([_cell("T")])

    with pytest.raises(json.JSONDecodeError):
        lvr.download_rows(fake, "b", "k", tmp_path / "rows.jsonl")


def test_one_run_failing_does_not_abort_the_others(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One bad run must not abort the rest of _verify_every_run's loop; each run is isolated and counted as failed instead of dying mid-pass."""
    seen = []

    def _verify_run(*, run: str, **kw: Any) -> int:
        seen.append(run)
        if run == "scaling_bad":
            raise RuntimeError("REPL exploded on this lane")
        return 0

    monkeypatch.setattr(lvr, "_build_s3_client", lambda: object())
    monkeypatch.setattr(lvr, "list_runs",
                        lambda *a, **k: ["scaling_a", "scaling_bad", "scaling_c"])
    monkeypatch.setattr(lvr, "verify_run", _verify_run)

    rc = lvr.main(["--dry-run", "--workdir", str(tmp_path)])
    assert seen == ["scaling_a", "scaling_bad", "scaling_c"], (
        f"the pass stopped at the failing lane: {seen}"
    )
    assert rc != 0, "a lane that raised must be reported as failed, not as success"
