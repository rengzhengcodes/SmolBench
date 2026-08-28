"""Test resume, second-pass row pairing, and the full-pass sentinel gate.

``scripts/lean_verify_rows.py`` is the deferred verification pass. It
reads a run's immutable ``all_rows.jsonl``, whose cell verdicts are all
the generation-time placeholder ``"unverified"``. It replays each
candidate against real Lean, and writes the graded mirror
``verified_rows.jsonl``. This file pins three properties of that pass.
A silent edit could break any of them while every run still reported
success:

1. **Resume is ALL-cells, not ANY-cell.** A ``(theorem_id, k)`` group is
   atomic *within* one pass, but not *across* passes. If phase 1 appends
   new cells to a group that a prior pass already graded, an ANY-cell
   completion test marks the group done, and the new cells stay
   ungraded forever.
2. **Prior verdicts pair to current rows by IDENTITY, not list
   position.** The output must carry every ``all_rows`` row, in ``all_rows`` order. If
   the output is seeded from that prior, shorter and possibly differently ordered,
   output, then indexed with positions computed against ``all_rows``, the result is an
   ``IndexError`` at best and a silent mis-pairing at worst. Identity is ``(kind, model,
   theorem_id, k, rung, replicate_idx)`` plus an OCCURRENCE ORDINAL. Repeated identities
   are real: regenerating a lane appends a second, or third, row for the same cell, and
   5 of the study's 21 lanes carry hundreds of them.
3. **A full pass that leaves a sentinel behind must exit non-zero.** A
   verification pass that silently no-ops writes a whole file of
   ``"unverified"`` rows, which every downstream loader scores as
   failures.

Everything here is offline: a fake S3 client holding objects in memory,
a fake verifier, and a monkeypatched theorem lookup. No Lean, no
``lean_dojo``, no AWS, no network. So this file runs on BOTH
interpreters.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests._paths import SCRIPTS

# ``scripts/`` is not an importable package, so the module is loaded by
# path. This mirrors tests/test_flip_probe.py's convention for a
# sibling script. The module name is unique to this file, so it never
# collides with the copy tests/deduction/test_deduction_study.py loads and pops.
_SPEC = importlib.util.spec_from_file_location(
    "lean_verify_rows_resume_under_test",
    SCRIPTS / "lean_verify_rows.py",
)
lvr = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = lvr
_SPEC.loader.exec_module(lvr)


# --------------------------------------------------------------------------- #
# Fixtures: rows, a fake S3 client, a fake verifier.
# --------------------------------------------------------------------------- #
def _cell(theorem, k=1, *, rung="stepk:1", rep=0, model="m",
          verdict="unverified", proof="tac", **extra):
    """One ``kind: "cell"`` row carrying the full identity tuple.

    `extra` lands on the row verbatim. Tests use it to tag rows with a
    marker field that `fan_out_verdict` does NOT write, so a test can
    tell WHICH row object ended up in a given output slot.
    """
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
    """Just the cell rows, in order.

    A pass legitimately APPENDS a sanity row for any theorem it replays
    that had none in ``all_rows``. So the output is not always
    ``all_rows`` row-for-row, and assertions about cell rows must say
    so.
    """
    return [r for r in rows if r.get("kind") == "cell"]


def _identity(row):
    """The test's own copy of the identity tuple, written independently.

    This is deliberately NOT imported from the module under test. A
    test that reuses the implementation's key function would pass even
    if that function keyed on something useless.
    """
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
    """Stands in for ``smolbench.deduction.lean.verify``.

    `verdict` is what every ``try_tail`` returns. Tests can set it to
    ``"unverified"`` on purpose, to simulate the no-op verification
    fault the full-pass gate exists to catch.
    """

    def __init__(self, verdict="lean_error", sanity_verdict="success"):
        self.verdict = verdict
        self.sanity_verdict = sanity_verdict
        self.tried: list[tuple[str, str]] = []
        self.replayed: list[str] = []

    @contextlib.contextmanager
    def open_at_step(self, bt, k):
        yield ("dojo", f"state@{k}")

    def try_tail(self, dojo, state_at_k, candidate_text, theorem_id):
        self.tried.append((theorem_id, candidate_text))
        return SimpleNamespace(verdict=self.verdict, error=None,
                               final_state_pp=None)

    def replay_ground_truth(self, bt):
        self.replayed.append("x")
        return SimpleNamespace(verdict=self.sanity_verdict, tactics_applied=5,
                               tactics_total=5, error=None)


def _dump(rows):
    return "".join(json.dumps(r) + "\n" for r in rows).encode("utf-8")


def _run(monkeypatch, tmp_path, all_rows, prior=None, *, verifier=None, **kw):
    """Drive `verify_run` end-to-end against fakes; return (rc, output rows)."""
    monkeypatch.setattr(lvr, "_lookup_theorem", lambda tid: SimpleNamespace(full_name=tid))
    client = _FakeS3()
    rows_key = lvr.run_object_key("", "r", lvr.ROWS_FILENAME)
    verified_key = lvr.run_object_key("", "r", lvr.VERIFIED_FILENAME)
    client.objects[rows_key] = _dump(all_rows)
    if prior is not None:
        client.objects[verified_key] = _dump(prior)

    rc = lvr.verify_run(
        client=client, bucket="b", key_prefix="", run="r", workers=1,
        workdir=tmp_path / "wd", verifier=verifier or _FakeVerifier(), **kw,
    )
    # Read back only what this run actually UPLOADED. The prior file is
    # pre-seeded into the fake bucket above. So reading the key
    # unconditionally would return that pre-seeded content on a run that
    # uploaded nothing, making "the output looks right" vacuously true
    # for a pass that did no work at all.
    body = client.objects.get(verified_key) if client.n_uploads else None
    out = [json.loads(l) for l in body.decode().splitlines() if l.strip()] if body else None
    return rc, out


# --------------------------------------------------------------------------- #
# 1. Resume: ALL cells of a group, not ANY.
# --------------------------------------------------------------------------- #
def test_resume_marks_a_group_done_only_when_every_cell_is_graded():
    """A half-graded group must NOT count as resumed-done.

    The ANY-cell rule this replaces was sound only under its stated
    premise, "one worker task always finishes a whole group". That
    premise holds within a pass, but NOT across passes: a regenerated
    lane appends new cells to a group a prior pass already completed.
    Under ANY, those new cells are skipped on every subsequent pass and
    stay ``"unverified"`` forever.

    Single-cell groups cannot tell the two rules apart, which is why
    both groups here carry two cells.
    """
    prior = [
        # Group ("t1", 1): one cell graded, one still a sentinel -- NOT done.
        _cell("t1", 1, rung="stepk:1", verdict="success"),
        _cell("t1", 1, rung="hint:2", verdict="unverified"),
        # Group ("t2", 1): every cell graded -- done.
        _cell("t2", 1, rung="stepk:1", verdict="lean_error"),
        _cell("t2", 1, rung="hint:2", verdict="success"),
    ]
    assert lvr.resume_done_groups(prior) == {("t2", 1)}


def test_resume_ignores_non_cell_rows_and_coerces_k():
    """Sanity rows never make a group done, and a string ``k`` still matches."""
    prior = [
        _sanity("t1", verdict="success"),
        _cell("t1", "1", verdict="success"),  # string k, as a hand-edited file may carry
    ]
    assert lvr.resume_done_groups(prior) == {("t1", 1)}
    assert lvr.resume_done_groups([_sanity("t9", verdict="success")]) == set()


# --------------------------------------------------------------------------- #
# 2. Second pass over a GROWN all_rows.jsonl.
# --------------------------------------------------------------------------- #
def test_second_pass_over_a_grown_all_rows_verifies_only_the_new_cells(monkeypatch, tmp_path):
    """Growth must not raise, must verify the new cells, and must keep the old.

    If the output is seeded from the prior pass's shorter row list, then indexed with
    positions computed against the CURRENT ``all_rows``, the index walks off the end of
    the list. That raises an ``IndexError`` inside the worker's own last-resort handler,
    which re-raises it out of `verify_run`.
    """
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
    # Every all_rows row is present, in all_rows order. There are no
    # appends here: both theorems already have a sanity row.
    assert [_identity(r) for r in out] == [_identity(r) for r in all_rows]
    by_id = {_identity(r): r for r in out}
    # The already-graded cells keep BOTH their verdict and their verify_ms:
    # "didn't crash" alone would also pass if everything were re-verified.
    assert by_id[("cell", "m", "t1", 1, "stepk:1", 0)]["verdict"] == "success"
    assert by_id[("cell", "m", "t1", 1, "stepk:1", 0)]["verify_ms"] == 111
    assert by_id[("cell", "m", "t1", 1, "hint:2", 0)]["verdict"] == "lean_error"
    assert by_id[("cell", "m", "t1", 1, "hint:2", 0)]["verify_ms"] == 222
    # Exactly the new group was verified.
    assert by_id[("cell", "m", "t2", 2, "stepk:1", 0)]["verdict"] == "incomplete"
    assert by_id[("cell", "m", "t2", 2, "hint:2", 0)]["verdict"] == "incomplete"
    assert {t for t, _ in verifier.tried} == {"t2"}


def test_output_row_order_is_all_rows_order_not_prior_output_order(monkeypatch, tmp_path):
    """The output's row order is ``all_rows``' order; downstream consumers rely on it.

    The prior output here is a PERMUTATION of ``all_rows``, same
    identities, different order, and is the same LENGTH as the pending
    work needs. So a positional implementation does not crash. It just
    silently emits the prior file's order. Only an order assertion
    catches that.
    """
    a, b, c = _cell("t1", 1), _cell("t2", 1), _cell("t3", 1)
    all_rows = [a, b, c]
    prior = [
        _cell("t2", 1, verdict="success", verify_ms=22),
        _cell("t1", 1, verdict="lean_error", verify_ms=11),
        _cell("t3", 1, verdict="unverified"),   # keeps group t3 pending
    ]
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior)

    assert rc == 0
    assert [_identity(r) for r in out[:3]] == [_identity(r) for r in (a, b, c)]
    # The only row beyond the all_rows prefix is the sanity row this pass
    # appended for the theorem it replayed -- appended, never inserted.
    assert len(out) == 4 and out[3]["kind"] == "sanity" and out[3]["theorem_id"] == "t3"
    # ...and identity pairing carried each prior verdict to the RIGHT row.
    assert out[0]["verdict"] == "lean_error" and out[0]["verify_ms"] == 11
    assert out[1]["verdict"] == "success" and out[1]["verify_ms"] == 22
    assert out[2]["verdict"] == "lean_error"  # the fake verifier's verdict


def test_prior_sanity_verdicts_survive_the_reseed(monkeypatch, tmp_path):
    """A prior pass's ground-truth REPLAY results must not be thrown away.

    ``all_rows``' sanity rows are placeholders (``"skipped"``, zero tactics). The real
    replay verdicts live only in the prior ``verified_rows.jsonl``. If the output is
    reseeded from ``all_rows`` and paired only on CELL rows, every sanity row silently
    reverts to its placeholder. That destroys the sanity gate's record for every theorem
    this pass does not happen to touch.
    """
    all_rows = [_sanity("t1"), _cell("t1", 1), _cell("t2", 1), _sanity("t2")]
    prior = [
        _sanity("t1", verdict="success", applied=5, total=5, ms=42),
        _cell("t1", 1, verdict="success"),
    ]
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior)

    assert rc == 0
    assert [_identity(r) for r in out] == [_identity(r) for r in all_rows]
    # The untouched theorem's replay record survives verbatim...
    assert out[0]["verdict"] == "success"
    assert out[0]["tactics_applied"] == 5
    assert out[0]["ms"] == 42
    # ...and the replayed theorem's sanity row is still a SANITY row, updated
    # in place rather than overwritten with a cell verdict by a stray index.
    assert out[3]["kind"] == "sanity" and out[3]["theorem_id"] == "t2"
    assert out[3]["tactics_applied"] == 5
    assert out[2]["verdict"] == "lean_error"  # t2's cell, freshly verified


def test_repeated_identities_pair_by_occurrence_order(monkeypatch, tmp_path):
    """Duplicate cell identities pair 1st-to-1st, 2nd-to-2nd, and so on.

    Repeated identities are the NORM, not an anomaly. When a lane is regenerated, it
    appends a fresh row for a cell that already has one, and real lanes carry up to 16
    occurrences of a single identity. A plain ``dict[identity] -> row`` drops all but
    one of them, then seeds the same prior row into every duplicate slot.

    ``_seq`` is the discriminator. `fan_out_verdict` writes only
    verdict, lean_error, final_state_pp, and verify_ms. So whichever ROW
    OBJECT was seeded into a slot still carries its own ``_seq`` after
    verification.
    """
    ident = dict(rung="stepk:1", rep=0, model="m")
    all_rows = [
        _cell("t1", 1, **ident, _seq="fresh1"),
        _cell("t1", 1, **ident, _seq="fresh2"),
        _cell("t1", 1, **ident, _seq="fresh3"),
    ]
    prior = [
        _cell("t1", 1, **ident, verdict="exception", _seq="prior1"),
        _cell("t1", 1, **ident, verdict="lean_error", _seq="prior2"),
    ]
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior)

    assert rc == 0
    cells = _cells(out)
    assert len(cells) == 3, "no occurrence may be dropped or duplicated"
    assert [r["_seq"] for r in cells] == ["prior1", "prior2", "fresh3"]


def test_prior_rows_absent_from_all_rows_are_appended_with_a_warning(monkeypatch, tmp_path, caplog):
    """An orphaned prior row is kept, appended, never silently dropped.

    This is a REAL shape, not a hypothetical. A pass that replays a theorem with no
    sanity row in ``all_rows`` APPENDS one to its own output. So on the next pass, that
    row has no ``all_rows`` counterpart. That append, rather than an insert, is what
    keeps the shared prefix, and therefore every index computed against ``all_rows``,
    valid.
    """
    all_rows = [_cell("t1", 1), _cell("t2", 1)]
    prior = [
        _cell("t1", 1, verdict="success"),
        _sanity("t9", verdict="success", applied=3, ms=9),  # appended by a prior pass
    ]
    with caplog.at_level("WARNING"):
        rc, out = _run(monkeypatch, tmp_path, all_rows, prior)

    assert rc == 0
    # all_rows' own rows keep their positions...
    assert [_identity(r) for r in out[:2]] == [_identity(r) for r in all_rows]
    # ...and the orphan is still there, exactly once, beyond that prefix.
    orphans = [r for r in out[2:] if r.get("theorem_id") == "t9"]
    assert len(orphans) == 1
    assert orphans[0]["kind"] == "sanity" and orphans[0]["tactics_applied"] == 3
    assert "1" in caplog.text and "all_rows" in caplog.text


# --------------------------------------------------------------------------- #
# 3. The full-pass sentinel gate.
# --------------------------------------------------------------------------- #
def test_full_pass_leaving_a_sentinel_exits_non_zero(monkeypatch, tmp_path):
    """A pass that grades nothing must fail loudly, not report success.

    A verifier that no-ops leaves every row on its generation-time ``"unverified"``
    placeholder. Every analysis loader scores that as a FAILURE, so the run reads as
    "the model proved nothing": a complete, plausible, wrong result. The only way the
    operator finds out is a non-zero exit.
    """
    all_rows = [_cell("t1", 1), _cell("t2", 1)]
    verifier = _FakeVerifier(verdict="unverified")
    rc, out = _run(monkeypatch, tmp_path, all_rows, verifier=verifier)

    assert rc != 0
    # The work is still uploaded -- the gate reports, it does not discard.
    assert out is not None and len(_cells(out)) == 2


def test_full_pass_gate_is_silent_when_every_cell_is_graded(monkeypatch, tmp_path):
    """The positive path: a real full pass still returns 0."""
    all_rows = [_cell("t1", 1), _cell("t2", 1)]
    rc, out = _run(monkeypatch, tmp_path, all_rows, verifier=_FakeVerifier(verdict="success"))
    assert rc == 0
    assert [r["verdict"] for r in _cells(out)] == ["success", "success"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 1},        # --limit: partial by request
        {"theorem": "t1"},   # --theorem: partial by request
        {"dry_run": True},   # --dry-run: nothing verified at all
    ],
    ids=["limit", "theorem", "dry_run"],
)
def test_full_pass_gate_does_not_fire_on_requested_partial_passes(monkeypatch, tmp_path, kwargs):
    """The three flags that ask for partial work must return 0.

    ``--limit``, ``--theorem``, and ``--dry-run`` leave ungraded rows BY
    DESIGN, because the operator asked for a subset. So a gate that
    fired on them would be noise, and noise gets ignored.

    A RESUMED run is deliberately NOT in this list. Under the ALL-cells
    resume rule, a done group carries no sentinel by construction. So
    resume cannot legitimately leave one behind on an otherwise-full
    pass (see `test_resumed_full_pass_leaving_a_sentinel_exits_non_zero`).
    """
    all_rows = [_cell("t1", 1), _cell("t2", 1)]
    rc, _ = _run(monkeypatch, tmp_path, all_rows,
                 verifier=_FakeVerifier(verdict="unverified"), **kwargs)
    assert rc == 0


@pytest.mark.parametrize("scenario", ["swallowed_failure", "sentinel_orphan"])
def test_resumed_full_pass_leaving_a_sentinel_exits_non_zero(monkeypatch, tmp_path, scenario):
    """Resume does NOT excuse a surviving sentinel on a limit-free pass.

    This is the shape of the real incident the gate exists for: a
    resumed completion pass over a partially-verified file. `done` is
    non-empty there, so a gate that also required ``not done`` stays
    silent in exactly the scenario that motivated it.

    Under the ALL-cells rule, a done group has zero sentinel cells BY
    CONSTRUCTION, and every pending group is graded this pass. So on a
    pass with no ``--limit`` and no ``--theorem``, there is no
    legitimate sentinel-remaining state, resumed or not. Both ways one
    can still survive are faults worth an alarm:

    * ``swallowed_failure``: a pending group was "verified", but the
      verdict written back is still the sentinel (a no-op or swallowed
      per-cell failure).
    * ``sentinel_orphan``: an ungraded prior row with no counterpart in
      the current ``all_rows.jsonl``. `group_unverified` reads
      ``all_rows``, so an orphan is never pending and never gets graded.
      Without this gate, it would sit in the output as a silent
      failure-scored cell forever.
    """
    all_rows = [_cell("t1", 1), _cell("t2", 2)]
    prior = [_cell("t1", 1, verdict="success")]      # -> group ("t1", 1) is done
    if scenario == "swallowed_failure":
        verifier = _FakeVerifier(verdict="unverified")
    else:
        verifier = _FakeVerifier(verdict="success")
        # Ungraded, and absent from all_rows -- so nothing will ever verify it.
        prior.append(_cell("t9", 7, verdict="unverified"))

    rc, out = _run(monkeypatch, tmp_path, all_rows, prior, verifier=verifier)

    assert rc == 2, "a full pass that left a sentinel must exit non-zero"
    # Precondition of the test: resume really did mark a group done, so this
    # discriminates against a gate carrying a `not done` term.
    assert any(r.get("verdict") == "success" for r in _cells(out))
    assert any(r.get("verdict") == "unverified" for r in _cells(out))


def test_cells_appended_to_an_already_graded_group_are_verified(monkeypatch, tmp_path):
    """The defect's own scenario: a group GROWS after a pass already graded it.

    This is what the ANY-cell rule got wrong, and it is not the same shape as a
    brand-new group appearing. Here the group ``("t1", 1)`` already has a graded cell
    in the prior output, so an ANY-cell completion test marks it done. The freshly
    appended ``hint:2`` cell is skipped, this pass and every pass after it, because the
    group still looks done next time too.

    Under the ALL-cells rule, the group is pending again, so both of its
    cells are re-verified together. One Dojo session per group is the
    unit of work, and ``all_rows``' own verdicts are all sentinels, so
    the whole group is replayed rather than just the new row.
    """
    all_rows = [
        _cell("t1", 1, rung="stepk:1", proof="NEW PROOF"),
        _cell("t1", 1, rung="hint:2", proof="NEW PROOF"),  # appended later by phase 1
    ]
    prior = [_cell("t1", 1, rung="stepk:1", verdict="success", proof="OLD PROOF")]
    verifier = _FakeVerifier(verdict="incomplete")
    rc, out = _run(monkeypatch, tmp_path, all_rows, prior, verifier=verifier)

    assert rc == 0
    assert out is not None, "the pass must not report success without uploading"
    cells = _cells(out)
    assert [_identity(r) for r in cells] == [_identity(r) for r in all_rows]
    assert [r["verdict"] for r in cells] == ["incomplete", "incomplete"], (
        "the appended cell must not be left on the sentinel"
    )

    # `unique_candidates` reads `candidate_proof` off the SEEDED rows.
    # This pins what the replay actually sends to Lean: a matched slot holds the PRIOR
    # row object wholesale. So the old cell is replayed with the prior pass's candidate
    # text, and only the appended cell carries the current one. That is the deliberate
    # carryover contract, since mixing a regenerated proof with an old verdict would be
    # worse. `--no-resume` is the documented remedy for a lane phase 1 genuinely
    # regenerated.
    assert sorted(text for _theorem, text in verifier.tried) == ["NEW PROOF", "OLD PROOF"], (
        "each distinct candidate text is replayed exactly once"
    )
