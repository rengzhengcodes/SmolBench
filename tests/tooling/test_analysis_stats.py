"""Statistical contracts of the family-ladder analysis scripts (offline)."""

import argparse
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from tests._paths import NOTEBOOKS

def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, NOTEBOOKS / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass annotation resolution needs it early
    spec.loader.exec_module(mod)
    sys.modules[Path(rel).stem] = mod  # siblings import each other by bare name
    return mod

# Both legs ship a power_analysis.py imported by bare name, so every deduction
# script must exec before the induction ones rebind it; then unbind them all.
ded_pa = _load("ded_power_analysis", "deduction/analysis/power_analysis.py")
error_bars = _load("ded_error_bars", "deduction/analysis/error_bars.py")
hint_vs_noise = _load("ded_hint_vs_noise", "deduction/analysis/hint_vs_noise.py")
ind_pa = _load("ind_power_analysis", "induction/analysis/power_analysis.py")
paired = _load("ind_paired", "induction/analysis/paired_analysis.py")
significance = _load("ind_significance", "induction/analysis/significance_report.py")
extens_vs_noise = _load("ind_extens_vs_noise", "induction/analysis/extens_vs_noise.py")
for _bare in ("power_analysis", "error_bars", "hint_vs_noise", "paired_analysis",
              "significance_report", "extens_vs_noise"):
    sys.modules.pop(_bare, None)

import _power_common as pc  # noqa: E402

def test_shared_scaffolding_wiring():
    assert (ind_pa.RESULTS_DIR, ded_pa.RESULTS_DIR) == (
        NOTEBOOKS / "induction" / "results", NOTEBOOKS / "deduction" / "results")
    # None means "not reached within the cap"; a number prints bare, even at/past it
    assert [pc.fmt_r(*a) for a in ((None, 80), (None, 200), (1, 80), (80, 80), (200, 80))] == [
        ">80", ">200", "1", "80", "200"]
    script = NOTEBOOKS / "induction" / "analysis" / "power_analysis.py"
    assert pc.results_dir(__file__) == Path(__file__).resolve().parent / "results"
    assert pc.results_dir(str(script), up=1) == NOTEBOOKS / "induction" / "results"
    assert pc.results_dir(str(script), up=0) == pc.results_dir(str(script))
    # no script carries a private copy of a multiplicity procedure
    assert (extens_vs_noise.holm, significance.holm, hint_vs_noise.holm) == (
        paired.holm, paired.holm, error_bars.holm)
    assert extens_vs_noise.hochberg is significance.hochberg

#: Each procedure with its verdict on the m=3 case that separates them (thresholds
#: .0167/.025/.05): Holm stops at the first failure, Hochberg steps up from 0.045.
PROCEDURES = [pytest.param(paired.holm, [True, False, False], id="induction-holm"),
              pytest.param(error_bars.holm, [True, False, False], id="deduction-holm"),
              pytest.param(significance.hochberg, [True, True, True], id="hochberg")]
FLOOR_P = 2 / 2 ** 30  # the seed sign-flip test's resolution floor at S = 30

@pytest.mark.parametrize("procedure, stepped", PROCEDURES)
@pytest.mark.parametrize("pvals", [
    # ties at the floor, and ties exactly ON a threshold (alpha/(m-i), m=6)
    [FLOOR_P, FLOOR_P, FLOOR_P, 0.02, 0.02, 0.9],
    [0.05 / 6, 0.05 / 6, 0.05 / 4, 0.05 / 4, 0.3, 0.3]],
    ids=["floor-ties", "threshold-ties"])
def test_tie_order_invariance_and_stepping(procedure, stepped, pvals):
    base = np.array(pvals, dtype=float)
    reject = procedure(base)
    for perm in map(list, itertools.permutations(range(base.size))):
        assert np.array_equal(procedure(base[perm]), reject[perm]), perm
    assert procedure(np.array([0.01, 0.04, 0.045])).tolist() == stepped
    # m=4: the tied values sit exactly at 0.05/4; a `<` would reject all four
    tie = np.array([0.0125, 0.0125, 0.0125, 0.9])
    assert procedure(tie).tolist() == [True, True, True, False]

@pytest.mark.parametrize("diffs, expected", [
    ([2, 1], 2 / 4), ([3, 1, 1], 2 / 8),   # totals +-3 +-1 / +-5 +-3 +-3 +-1: only |T_obs|
    ([2, -1, 1], 6 / 8),                   # |T| >= 2 in 6 of 8
    ([2, 1, 0], 2 / 4),                    # a zero cluster doubles tail and denominator
    ([0, 0, 0], 1.0), ([], 1.0)])          # |T_obs| = 0 matches all; empty family guarded
def test_signflip_exact_p_matches_hand_enumeration(diffs, expected):
    p = paired.signflip_exact_p(diffs)
    assert p == pytest.approx(expected)
    assert p == pytest.approx(paired.signflip_exact_p([-d for d in diffs]))
    assert 0 < p <= 1
    if diffs:  # the observed assignment and its global negation always qualify
        assert p >= 2 / 2 ** len(diffs)

@pytest.mark.parametrize("nb, nc", [(0, 0), (1, 0), (2, 3), (3, 1), (5, 1), (4, 4), (7, 2)])
def test_signflip_equals_mcnemar_for_every_singleton_split(nb, nc):
    # with one item per cluster the cluster test IS exact McNemar
    a = np.array([1] * nb + [0] * nc + [1, 0, 1, 0], dtype=bool)
    b = np.array([0] * nb + [1] * nc + [1, 0, 1, 0], dtype=bool)
    p = paired.signflip_exact_p(paired.seed_diffs(a, b, np.arange(a.size)))
    assert p == pytest.approx(paired.mcnemar_exact_p(nb, nc))
    if (nb, nc) == (3, 1):
        # hand anchor: 6 concordant cancel; |T| >= 2 for 1+4+4+1 = 10 of 16
        assert p == pytest.approx(0.625)

def test_paired_signal_reductions():
    # ``sum_s d_s == b - c``, and one cell per block reduces to exact McNemar
    a = np.array([1, 1, 0, 1, 0, 0, 1, 1, 1], dtype=bool)  # 3 seeds of 3 items
    b = np.array([0, 1, 1, 1, 0, 1, 0, 1, 0], dtype=bool)
    nb, nc = int((a & ~b).sum()), int((~a & b).sum())
    diffs = paired.seed_diffs(a, b, np.repeat(np.arange(3), 3))
    assert diffs == [0, -1, 2]   # per seed: (2-2), (1-2), (3-1)
    assert (nb, nc) == (3, 2)    # A wins items 0, 6, 8; B wins 2, 5
    assert sum(diffs) == nb - nc == 1
    # b=5, c=2, 6 concordant: 2 * (1 + 7 + 21) / 128 = 58/128, tol ~5 SE at B=20k
    succ = np.array([(0, 1)] * 5 + [(1, 0)] * 2 + [(1, 1)] * 3 + [(0, 0)] * 3, dtype=np.int32)
    models, contrasts, kw = ["m_a", "m_b"], [("a v b", "m_a", "m_b")], dict(B=20_000, seed=1)
    p_block = error_bars.block_signflip_p(succ, models, contrasts, **kw)[0]
    assert ded_pa.mcnemar_exact_p(2, 5) == pytest.approx(58 / 128)
    assert abs(p_block - 58 / 128) < 0.018
    assert p_block == error_bars.block_signflip_p(succ, models, contrasts, **kw)[0]
    # the observed assignment is in its own reference distribution -> 1.0, not 1/(B+1)
    null = np.array([[1, 1], [0, 0], [1, 1], [0, 0]], dtype=np.int32)
    assert error_bars.block_signflip_p(null, models, contrasts, B=1_000, seed=1)[0] == 1.0

def _cell(model, theorem, verdict, k=1, rung="stepk:1", replicate_idx=0):
    return {"kind": "cell", "model": model, "theorem_id": theorem, "k": k,
            "rung": rung, "replicate_idx": replicate_idx, "verdict": verdict}

def _write_rows(path: Path, *cells, model="m1", extra=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_cell(model, c[0], c[-1], rung=c[1] if len(c) == 3 else "stepk:1") for c in cells]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows + list(extra)))
    return path

def _lane(root: Path, model: str, *cells, extra=()):
    return _write_rows(root / model / "verified_rows.jsonl", *cells, model=model, extra=extra)

@pytest.mark.parametrize("verdicts, expected", [
    (["success"], 1), (["failure"], 0), (["incomplete"], 0), (["exception", "success"], 1),
    (["replay_failed", "failure"], 0),
    (["success", "failure"], 1), (["failure", "success"], 0),  # earliest wins, both ways
    (["exception", "replay_failed"], None), ([], None)])       # unmeasurable is None, not 0
def test_grade_verdicts_is_the_row_rule(verdicts, expected):
    assert ded_pa.grade_verdicts(verdicts) == expected

def test_all_loaders_share_the_one_row_rule(tmp_path, monkeypatch):
    # thm_a graded in both lanes, thm_b only in m2, thm_c nowhere, plus rows to ignore
    _lane(tmp_path, "m1", ("thm_a", "exception"), ("thm_a", "success"), ("thm_a", "failure"),
          ("thm_b", "exception"), ("thm_b", "replay_failed"), ("thm_c", "replay_failed"),
          extra=[_cell("m1", "thm_a", "success", k=2, replicate_idx=1),
                 {"kind": "sanity", "model": "m1", "verdict": "success"}])
    _lane(tmp_path, "m2", ("thm_a", "failure"), ("thm_b", "success"), ("thm_c", "exception"))
    monkeypatch.setattr(error_bars, "MODELS", ["m1", "m2"])
    _m, blocks, _r, meta = error_bars.build_pool(tmp_path, count_as_failure=False)
    lanes = [tmp_path / m / "verified_rows.jsonl" for m in ("m1", "m2")]
    ref_models, ref_blocks, _ = ded_pa.load_joint_cells(lanes, models=("m1", "m2"))
    assert ref_models == ["m1", "m2"]
    # only thm_a survives the pairing: m1 on its earliest surviving row
    assert blocks == ref_blocks == {"thm_a": {(1, "stepk:1"): {"m1": 1, "m2": 0}}}
    assert meta["count_as_failure"] is False
    # thm_b's fault travelled with m1's own output -> scored 0; thm_c never is
    _m, blocks, _r, meta = error_bars.build_pool(tmp_path, count_as_failure=True)
    assert sorted(blocks) == ["thm_a", "thm_b"]
    assert blocks["thm_b"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
    assert meta["added"] == {"m1": [("thm_b", 1, "stepk:1")]}
    assert meta["n_unresolved"] == {"m1": 1, "m2": 1}
    assert set(meta["own_denominator"].values()) == {2}

def test_rule_cost_is_measured_per_lane_not_per_added_cell(tmp_path, monkeypatch):
    """A lane gaining two cells reports the cost of removing BOTH; 0/0 stays None."""
    _lane(tmp_path, "m1", ("t1", "stepk:1", "success"), ("t2", "stepk:1", "success"),
          ("t3", "stepk:1", "exception"), ("t4", "hint:2", "exception"))
    _lane(tmp_path, "m2", ("t1", "stepk:1", "success"), ("t2", "stepk:1", "failure"),
          ("t3", "stepk:1", "success"), ("t4", "hint:2", "failure"))
    monkeypatch.setattr(error_bars, "MODELS", ["m1", "m2"])
    _m, _b, _r, meta = error_bars.build_pool(tmp_path, count_as_failure=True)
    by_rung = {c["rung"]: c for c in meta["rule_cost"]}
    assert {c["model"] for c in meta["rule_cost"]} == {"m1"}
    step = by_rung["stepk:1"]
    # both added cells leave the lane denominator, not just this rung's one
    assert (step["n_added"], step["n_lane"], step["theorems"]) == (1, 4, ["t3@k1"])
    assert (step["pooled_caf"], step["pooled_drop"]) == (2 / 4, 2 / 2)
    assert (step["rung_caf"], step["rung_drop"]) == (2 / 3, 2 / 2)
    # hint:2 held exactly one cell and it was added: the drop rate is undefined
    assert by_rung["hint:2"]["rung_drop"] is None

def test_hint_vs_noise_loader_applies_the_same_rule(tmp_path):
    path = _write_rows(tmp_path / "verified_rows.jsonl",
                      ("t1", "hint:3", "exception"), ("t1", "hint:3", "success"),
                      ("t1", "noise:3", "success"), ("t1", "noise:3", "failure"),
                      ("t2", "hint:3", "replay_failed"), ("t2", "noise:3", "failure"),
                      ("t3", "stepk:1", "success"))  # later draws and other rungs: ignored
    # t2's hint:3 has no surviving row -> absent, not 0
    assert hint_vs_noise.load_rungs(path) == {("t1", 1): {"hint:3": 1, "noise:3": 1},
                                                    ("t2", 1): {"noise:3": 0}}
    ungraded = _write_rows(tmp_path / "u.jsonl", ("t1", "hint:3", "success"),
                          ("t1", "noise:3", "unverified"))
    with pytest.raises(SystemExit, match="unverified"):
        hint_vs_noise.load_rungs(ungraded)

@pytest.mark.parametrize("nc_extens, nc_noise, expected", [
    (0.00, 0.00, "information"), (0.10, 0.24, "information"),  # under the 25% criterion
    (0.10, 0.25, "COLLAPSE"), (0.90, 0.99, "COLLAPSE"),  # inclusive; noise broken wins
    (0.30, 0.10, "extens degraded")])  # otherwise the extens arm's own rate labels it
def test_extens_vs_noise_mechanism_labels(nc_extens, nc_noise, expected):
    assert extens_vs_noise.mechanism(nc_extens, nc_noise) == expected

SUPERSEDED_NAME = "all_rows_SUPERSEDED-20260815T000000Z.jsonl"

@pytest.mark.parametrize("name, refused", [
    (SUPERSEDED_NAME, True), ("all_rows_STALE-20260814T000000Z.jsonl", True),
    ("verified_rows_BROKEN-20260813T000000Z.jsonl", True),
    # markers are anchored on ``_MARKER-``: ordinary words must not trip
    ("stale_check_rows.jsonl", False), ("unBROKEN.jsonl", False), ("rows_STALEMATE.jsonl", False),
    # matched on the BASENAME, not on any parent directory
    ("SUPERSEDED_audit/verified_rows.jsonl", False)])
def test_retired_artifact_markers(tmp_path, name, refused):
    from smolbench.deduction.lean import runner
    paths = [tmp_path / "verified_rows.jsonl", tmp_path / name]
    if not refused:
        ded_pa.reject_superseded(paths)
        runner.reject_superseded_rows(paths)
        return
    with pytest.raises(SystemExit) as excinfo:
        ded_pa.reject_superseded(paths)
    assert name in str(excinfo.value)
    with pytest.raises(ValueError):
        runner.reject_superseded_rows(paths)

def _theorem_dir_with(root: Path, filename: str) -> Path:
    theorem_dir = root / "theorems" / "T"
    _write_rows(theorem_dir / "outputs" / filename, ("T", "hint:3", "success"))
    (theorem_dir / "meta.json").write_text(json.dumps(
        {"full_name": "T", "k": 1, "n_total_tactics": 2, "file_path": "F.lean",
         "ground_truth_remaining_from_k": "exact rfl", "true_premises_at_k": []}))
    return theorem_dir

def test_retired_artifacts_are_refused_by_every_scanner(tmp_path):
    from smolbench.deduction.lean import cli, runner
    rows = _write_rows(tmp_path / SUPERSEDED_NAME, ("t1", "success"))
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        ded_pa.load_joint_cells([rows], models=("m1",))
    hint = _write_rows(tmp_path / "h" / SUPERSEDED_NAME, ("t1", "hint:3", "success"))
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        hint_vs_noise.load_rungs(hint)
    bad = tmp_path / "bad"
    with pytest.raises(ValueError, match="SUPERSEDED"):
        runner.write_theorem_summary(_theorem_dir_with(bad, SUPERSEDED_NAME))
    with pytest.raises(ValueError, match="SUPERSEDED"):
        cli.cmd_show(argparse.Namespace(run_dir=str(bad), theorem=None))
    assert error_bars.reject_superseded is ded_pa.reject_superseded
    assert ded_pa.RETIRED_MARKERS == runner.RETIRED_MARKERS
    clean = _theorem_dir_with(tmp_path / "ok", "hint-3__m1.jsonl")
    assert cli.cmd_show(argparse.Namespace(run_dir=str(tmp_path / "ok"), theorem=None)) == 0
    (clean / "outputs" / "hint-3__m1.jsonl").unlink()  # row schema is not the
    runner.write_theorem_summary(clean)                # subject of this test
    assert (clean / "summary.md").exists()

def test_lane_outcomes_refuses_ungraded_rows(tmp_path):
    _lane(tmp_path / "rows", "m1", ("t1", "success"), ("t2", "unverified"))
    with pytest.raises(SystemExit, match="unverified"):
        error_bars.lane_outcomes(tmp_path / "rows", "m1")
    _lane(tmp_path / "clean", "m1", ("t1", "exception"), ("t1", "success"),
          ("t2", "replay_failed"))
    # the recovery sibling is screened on ITS field, not on `verdict`
    rec = _cell("m1", "t3", None) | {"recovered_verdict": "unverified"}
    rec.pop("verdict")
    _write_rows(tmp_path / "rec" / "m1" / "recovered_rows.jsonl", extra=[rec])
    with pytest.raises(SystemExit, match="unverified"):
        error_bars.lane_outcomes(tmp_path / "clean", "m1", tmp_path / "rec")
    _write_rows(tmp_path / "rec2" / "m1" / "recovered_rows.jsonl")
    graded, no_survivor = error_bars.lane_outcomes(tmp_path / "clean", "m1", tmp_path / "rec2")
    assert graded == {("t1", 1, "stepk:1"): 1}
    assert no_survivor == {("t2", 1, "stepk:1")}
