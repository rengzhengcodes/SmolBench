"""Offline contract for scripts/results/regrade.py; no AWS, no network.

Two properties the reviewer of PR #14 found broken:

* ``--write`` must round-trip every ``Marks`` field it does not re-grade. It
  previously rebuilt ``Marks(model=, marks=, date=)`` by hand and so wrote
  ``server_config: null`` over the serving-stack provenance of every replicate.
* The S3-backed refusal must not hand the operator a recipe for switching the
  guard off, because there is no path that writes a local regrade back to the
  append-only S3 log.
"""

from datetime import datetime, timezone

import pytest

from scripts.results import regrade
from smolbench.evals import Mark, Marks

#: Serving-stack snapshot: the field a hand-rolled re-construction dropped.
SERVER_CONFIG = {
    "instance_type": "p6-b200.48xlarge",
    "gpu_count": 8,
    "tp": 8,
    "vllm_image": "vllm/vllm-openai@sha256:26354b5e",
}
#: Pinned so the assertion cannot pass by re-stamping "now".
COLLECTED_AT = datetime(2026, 8, 16, 3, 4, 5, tzinfo=timezone.utc)


@pytest.fixture
def local_study(tmp_path, monkeypatch):
    """Point regrade at a local, one-condition results tree and return its rep path.

    Both module-level anchors are redirected (``REPO`` and ``STUDIES``), so the
    real, gitignored ``notebooks/induction/results`` tree is never read or
    written by this test.
    """
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3", raising=False)
    monkeypatch.setattr(regrade, "REPO", tmp_path)
    monkeypatch.setattr(regrade, "STUDIES", {"induction": "results"})
    rep = tmp_path / "results" / "cot_intens" / "rep_00.yaml"
    rep.parent.mkdir(parents=True)
    Marks(
        model="deepseek-v4-pro",
        marks=(
            # score=None on both: the pre-compliance parser refused them, so a
            # regrade genuinely changes this file (recovered 2), which is what
            # makes the round-trip assertion below non-vacuous.
            Mark(query="q1", answer=42, response="42", score=None),
            Mark(query="q2", answer=7, response="**7**", score=None),
        ),
        date=COLLECTED_AT,
        server_config=SERVER_CONFIG,
    ).dump(rep)
    return rep


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
    assert after.model == "deepseek-v4-pro"
    # ...and the re-grade really did happen: both marks were invalid, both now
    # score, and the markup violation is recorded on the second.
    assert [m.score for m in after.marks] == [1, 1]
    assert after.marks[0].compliance is None
    assert after.marks[1].compliance is not None
    assert "recovered" not in capsys.readouterr().err  # no stderr noise


def test_dry_run_writes_nothing(local_study):
    """Without --write the tree is byte-identical afterwards."""
    original = local_study.read_bytes()
    assert regrade.main([]) == 0
    assert local_study.read_bytes() == original


def test_s3_backed_tree_is_refused_with_no_workaround(monkeypatch, capsys):
    """The refusal names the tracking issue and offers no way to disable itself (14-08).

    Uses the REAL ``REPO``/``STUDIES``, since ``resolve_store`` only returns an
    ``S3ResultsStore`` for a directory under ``repo_root()``; the guard runs
    before any file is opened, so the (gitignored, possibly absent) results tree
    is never touched.
    """
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://smolbench-results-414266451290")
    assert regrade.main(["--write"]) == 1
    out = capsys.readouterr().out
    assert "REFUSING to regrade" in out
    assert "(see the regrade-through-the-store issue)" in out
    # The old recovery steps told the operator to turn the guard off and produce
    # exactly the local-only regrade the guard exists to prevent.
    assert "Unset SMOLBENCH_RESULTS_S3" not in out
    assert "Re-run this regrade" not in out
