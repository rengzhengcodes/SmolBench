"""Offline contract for scripts/results/regrade.py; no AWS, no network.

Three properties, two of them found broken by the reviewer of PR #14:

* ``--write`` must round-trip every ``Marks`` field it does not re-grade. It
  previously rebuilt ``Marks(model=, marks=, date=)`` by hand and so wrote
  ``server_config: null`` over the serving-stack provenance of every replicate.
* An S3-backed tree must actually be re-gradable. ``main`` used to REFUSE it
  and print a "sync down, unset the env var, re-run" recipe, i.e. the
  local-only regrade the guard existed to prevent; ``results_store`` has since
  grown the store-level primitive (``ResultsStore.regrade``: a new run
  carrying ``regraded_from``, plus a ``.superseded`` marker retiring the run
  it replaces), so the regrade now goes THROUGH the store on either backend.
* A regrade is a WRITER of compliance labels, so it must spell ``COMPLIANT``
  explicitly rather than store the pre-``COMPLIANT`` ``compliance: null``
  that ``Marks.loads``' legacy shim exists to translate on the way back in.
"""

import io
import json
from datetime import datetime, timezone

import pytest
from botocore.exceptions import ClientError

from scripts.results import regrade
from smolbench.evals import Mark, Marks
from smolbench.evals import results_store as rs
from smolbench.evals.quiz import COMPLIANT
from smolbench.evals.results_store import format_run_ts
from smolbench.evals.study_config import tag_for

#: Serving-stack snapshot: the field a hand-rolled re-construction dropped.
SERVER_CONFIG = {
    "instance_type": "p6-b200.48xlarge",
    "gpu_count": 8,
    "tp": 8,
    "vllm_image": "vllm/vllm-openai@sha256:26354b5e",
}
#: Pinned so the assertion cannot pass by re-stamping "now".
COLLECTED_AT = datetime(2026, 8, 16, 3, 4, 5, tzinfo=timezone.utc)
#: The instant every regrade in this file is stamped with (``rs.utcnow`` is
#: patched to it), distinct from `COLLECTED_AT` so a new run's key and the
#: run it replaces can never be confused.
REGRADED_AT = datetime(2026, 8, 20, 11, 12, 13, tzinfo=timezone.utc)
#: A roster spec key (the S3 log's key dimension) and its analysis tag (the
#: local directory key). Read from the committed study config rather than
#: re-typed, per #46.
MODEL = "gemma-4-e2b"
TAG = tag_for(MODEL)
#: The replicate seed every test in this file collects at. A plain int, since
#: that is what `ReplicateAddress.seed` carries and what `LocalResultsStore`
#: renders as ``rep_<seed>.yaml``; a zero-padded spelling is addressable by
#: neither store.
SEED = 1776


def _marks(model=MODEL, date=COLLECTED_AT) -> Marks:
    """Two marks the OLD parser refused, so a regrade genuinely changes them."""
    return Marks(
        model=model,
        marks=(
            Mark(query="q1", answer=42, response="42", score=None),
            Mark(query="q2", answer=7, response="**7**", score=None),
        ),
        date=date,
        server_config=SERVER_CONFIG,
    )


@pytest.fixture
def local_study(tmp_path, monkeypatch):
    """Point regrade at a local, one-condition results tree and return its rep path.

    Both module-level anchors are redirected (``REPO`` and ``STUDIES``), so the
    real, gitignored ``notebooks/induction/results`` tree is never read or
    written by this test.

    The replicate is laid down BY ``LocalResultsStore.dump_marks`` rather than
    by a hand-spelled path, so the fixture models exactly the layout the
    production writer (``ReplicateHarness``) produces -- directory name,
    ``rep_<seed>.yaml`` spelling and all -- instead of a name only this test
    would ever create.
    """
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    monkeypatch.setattr(regrade, "REPO", tmp_path)
    monkeypatch.setattr(regrade, "STUDIES", {"induction": "results"})
    monkeypatch.setattr(rs, "utcnow", lambda: REGRADED_AT)
    store = rs.LocalResultsStore(tmp_path / "results")
    addr = rs.ReplicateAddress(tag=TAG, info="intens", seed=SEED, model=MODEL)
    store.dump_marks(_marks(), addr, COLLECTED_AT)
    return tmp_path / "results" / f"{TAG}_intens" / f"rep_{SEED}.yaml"


def test_write_preserves_server_config_and_date(local_study, capsys):
    """--write re-grades the scores and leaves every other field alone (14-01)."""
    before = Marks.load(local_study)
    assert before.server_config == SERVER_CONFIG  # fixture sanity

    assert regrade.main(["--write"]) == 0

    after = Marks.load(local_study)
    # THE regression: this was `None` before the fix, silently destroying the
    # hardware provenance with no git safety net and nothing to re-fetch from.
    assert after.server_config == SERVER_CONFIG
    assert after.date == COLLECTED_AT
    assert after.model == MODEL
    # ...and the re-grade really did happen: both marks were invalid, both now
    # score, and the markup violation is recorded on the second.
    assert [m.score for m in after.marks] == [1, 1]
    # COMPLIANT is written OUT, not left as the legacy `compliance: null` that
    # `Marks.loads`' read-compat shim exists to translate (#50): a regrade is a
    # producer of compliance labels, so it must spell the value.
    assert after.marks[0].compliance == COMPLIANT
    assert after.marks[1].compliance not in (COMPLIANT, None)
    raw = local_study.read_text()
    assert f"compliance: {COMPLIANT}" in raw and "compliance: null" not in raw
    assert "recovered" not in capsys.readouterr().err  # no stderr noise


def test_a_local_regrade_retires_the_file_it_replaces(local_study):
    """The replaced file survives under the SUPERSEDED name, and the new one says so.

    ``LocalResultsStore.supersede`` renames rather than overwrites, so the
    pre-regrade bytes are still on disk (the only undo this script has ever
    had), and the replacement carries ``regraded_from`` naming the run it
    replaces -- for a local file, the collection date it was stamped with.
    """
    original = local_study.read_bytes()

    assert regrade.main(["--write"]) == 0

    retired = sorted(local_study.parent.glob(f"rep_{SEED}.SUPERSEDED-*.yaml"))
    assert len(retired) == 1, sorted(p.name for p in local_study.parent.iterdir())
    assert retired[0].read_bytes() == original, "the replaced bytes must survive verbatim"
    assert Marks.load(local_study).regraded_from == format_run_ts(COLLECTED_AT)
    # ...and the retired file is invisible to readers, which is what makes the
    # rename a supersede rather than a second live replicate.
    assert rs.LocalResultsStore(local_study.parents[1]).list_seeds(
        None, TAG, "intens") == [SEED]


def test_dry_run_writes_nothing(local_study):
    """Without --write the tree is byte-identical afterwards."""
    original = local_study.read_bytes()
    assert regrade.main([]) == 0
    assert local_study.read_bytes() == original
    assert not list(local_study.parent.glob("*SUPERSEDED*"))


# ---------------------------------------------------------------------------
# 14-08: the S3-backed path
# ---------------------------------------------------------------------------
class FakeS3Client:
    """In-memory stand-in for the S3 calls `S3ResultsStore` makes.

    Deliberately the same shape as ``tests/evals/test_results_store.py``'s
    fake (one dict of key -> body, a paginator that yields one key per page),
    so this file exercises the REAL store against a recorded call log rather
    than a store-shaped mock: `puts` is every ``put_object`` in order, which
    is what lets a test assert that a dry run writes nothing at all.
    """

    def __init__(self):
        self.objects: dict = {}
        self.puts: list = []  # (Key, Body) of every put_object, in order

    def fresh_client(self, service, region=None):
        return self

    def put_object(self, Bucket, Key, Body):
        self.puts.append((Key, Body))
        self.objects[Key] = Body

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "no"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix="", MaxKeys=None):
        keys = sorted(k for k in self.objects if k.startswith(Prefix))[:MaxKeys]
        return {"Contents": [{"Key": k, "Size": len(self.objects[k])} for k in keys]}

    def get_paginator(self, operation_name):
        return self

    def paginate(self, Bucket=None, Prefix="", **kwargs):
        for key in sorted(k for k in self.objects if k.startswith(Prefix)):
            yield {"Contents": [{"Key": key, "Size": len(self.objects[key])}]}
        yield {}


#: The run_ts of the already-logged run every S3 test regrades.
LOGGED_TS = format_run_ts(COLLECTED_AT)
#: Key of that run: ``<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``.
LOGGED_KEY = f"induction/{MODEL}/seed={SEED}/intens--{LOGGED_TS}.yaml"


@pytest.fixture
def s3_study(tmp_path, monkeypatch):
    """Point regrade at an S3-backed tree served by a `FakeS3Client`.

    ``repo_root`` is redirected at ``tmp_path`` so ``resolve_store``'s
    hermeticity fallback (results_dir must be under the repo root) selects the
    S3 store without the real checkout being involved, and ``rs.utcnow`` is
    pinned so the new run's key is deterministic.
    """
    client = FakeS3Client()
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://test-bucket")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")
    monkeypatch.setattr(rs, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(rs._aws, "fresh_client", client.fresh_client)
    monkeypatch.setattr(rs, "utcnow", lambda: REGRADED_AT)
    monkeypatch.setattr(regrade, "REPO", tmp_path)
    monkeypatch.setattr(regrade, "STUDIES", {"induction": "notebooks/induction/results"})
    client.objects[LOGGED_KEY] = _marks().dumps().encode()
    return client


def test_an_s3_backed_tree_is_regraded_through_the_store(s3_study, capsys):
    """14-08: the refusal is gone; the regrade lands in the log readers actually read.

    The append-only log cannot be edited, so a regrade is TWO writes: the new
    run naming what it replaces, and a ``.superseded`` marker retiring the old
    run so earliest-wins stops serving it. The old run OBJECT is untouched.
    """
    original = s3_study.objects[LOGGED_KEY]

    assert regrade.main(["--write"]) == 0

    new_key = f"induction/{MODEL}/seed={SEED}/intens--{format_run_ts(REGRADED_AT)}.yaml"
    marker_key = f"induction/{MODEL}/seed={SEED}/intens--{LOGGED_TS}.superseded"
    written = dict(s3_study.puts)
    assert set(written) == {new_key, marker_key}, sorted(written)
    assert s3_study.objects[LOGGED_KEY] == original, "the log is append-only"

    regraded = Marks.loads(written[new_key].decode())
    assert regraded.regraded_from == LOGGED_TS
    assert [m.score for m in regraded.marks] == [1, 1]
    assert regraded.marks[0].compliance == COMPLIANT
    assert regraded.server_config == SERVER_CONFIG and regraded.date == COLLECTED_AT

    marker = json.loads(written[marker_key].decode())
    assert marker["superseded_at"] == REGRADED_AT.isoformat()
    assert marker["reason"].strip() and "regrade" in marker["reason"].lower()

    # ...and what a reader now gets back is the regraded run, not the original.
    store = rs.resolve_store(regrade.REPO / regrade.STUDIES["induction"])
    addr = rs.ReplicateAddress(tag=TAG, info="intens", seed=SEED, model=MODEL)
    assert store.load_marks(addr).regraded_from == LOGGED_TS

    out = capsys.readouterr().out
    assert "REFUSING" not in out and "Unset SMOLBENCH_RESULTS_S3" not in out
    assert f"{TAG}_intens" in out, "the per-condition table still names the arm"


def test_an_s3_dry_run_writes_nothing(s3_study, capsys):
    """The dry run reports the same tallies without a single write."""
    assert regrade.main([]) == 0
    assert s3_study.puts == []
    assert "Dry run only" in capsys.readouterr().out


def test_the_arm_filter_still_selects_on_s3(s3_study):
    """--arm is a condition filter, so an unselected arm is never written."""
    assert regrade.main(["--write", "--arm", "extens"]) == 0
    assert s3_study.puts == []
    assert regrade.main(["--write", "--arm", "intens"]) == 0
    assert len(s3_study.puts) == 2


def test_the_refusal_and_its_workaround_are_gone():
    """The recipe the refusal printed produced exactly the loss it warned about."""
    assert not hasattr(regrade, "_s3_backed_studies")
    source = (regrade.REPO / "scripts" / "results" / "regrade.py").read_text()
    for gone in ("REFUSING to regrade", "Unset SMOLBENCH_RESULTS_S3", "Re-run this regrade"):
        assert gone not in source, gone
