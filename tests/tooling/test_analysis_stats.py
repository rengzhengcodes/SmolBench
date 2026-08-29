"""Statistical contracts of the family-ladder analysis scripts and their shared scaffolding.

Tie-order invariance, sign-flip exactness and its McNemar reduction, the one-row
and one-denominator rules, and the retired/ungraded artifact refusals. Offline.
"""

import importlib.util
import itertools
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from tests._paths import NOTEBOOKS

# Both legs have a power_analysis.py that siblings import by bare name, so each
# script execs with the right one bound under the bare name, then unbound.
def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclass annotation resolution needs it early
    spec.loader.exec_module(module)
    return module

@contextmanager
def _bound(**modules):
    """Bind modules under bare names for the duration of the block."""
    saved = {n: sys.modules.get(n) for n in modules}
    sys.modules.update(modules)
    try:
        yield
    finally:
        for n, old in saved.items():
            if old is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = old

_DED = NOTEBOOKS / "deduction" / "analysis"
_IND = NOTEBOOKS / "induction" / "analysis"

ded_pa = _load("ded_power_analysis", _DED / "power_analysis.py")
with _bound(power_analysis=ded_pa):
    error_bars = _load("ded_error_bars", _DED / "error_bars.py")
    with _bound(error_bars=error_bars):
        hint_vs_noise = _load("ded_hint_vs_noise", _DED / "hint_vs_noise.py")

ind_pa = _load("ind_power_analysis", _IND / "power_analysis.py")
with _bound(power_analysis=ind_pa):
    paired = _load("ind_paired_analysis", _IND / "paired_analysis.py")
    with _bound(paired_analysis=paired):
        significance = _load("ind_significance_report", _IND / "significance_report.py")
        with _bound(significance_report=significance):
            extens_vs_noise = _load("ind_extens_vs_noise", _IND / "extens_vs_noise.py")

# The scripts put notebooks/ on sys.path at exec time; nothing there can shadow this.
import _power_common as pc  # noqa: E402

def test_both_legs_resolve_their_study_results_dir():
    """Each leg's ``RESULTS_DIR`` is ``notebooks/<study>/results``: the shape results_store.experiment_name shortens."""
    assert ind_pa.RESULTS_DIR == NOTEBOOKS / "induction" / "results"
    assert ded_pa.RESULTS_DIR == NOTEBOOKS / "deduction" / "results"

def test_fmt_r_censors_only_none():
    """``None`` means "not reached within the cap"; every number prints bare."""
    assert pc.fmt_r(None, 80) == ">80"
    assert pc.fmt_r(None, 200) == ">200"
    assert pc.fmt_r(1, 80) == "1"
    assert pc.fmt_r(80, 80) == "80"     # equals the cap, still not censored
    assert pc.fmt_r(200, 80) == "200"

def test_results_dir_is_file_anchored():
    """``results_dir`` resolves off the given file, never the process cwd."""
    assert pc.results_dir(__file__) == Path(__file__).resolve().parent / "results"
    script = NOTEBOOKS / "periodic" / "analysis" / "power_analysis.py"
    assert pc.results_dir(str(script), up=1) == NOTEBOOKS / "periodic" / "results"
    assert pc.results_dir(str(script), up=0) == pc.results_dir(str(script))

#: Every step-wise procedure under test. The two legs never share code, so both
#: Holm copies must independently hold the property.
PROCEDURES = [
    pytest.param(paired.holm, id="induction-holm"),
    pytest.param(error_bars.holm, id="deduction-holm"),
    pytest.param(significance.hochberg, id="induction-hochberg"),
]

#: The seed sign-flip test's hard resolution floor at S = 30 replicates.
FLOOR_P = 2 / 2 ** 30

@pytest.mark.parametrize("procedure", PROCEDURES)
@pytest.mark.parametrize("pvals", [
        # Ties at the floor, and ties sitting exactly ON a Holm/Hochberg
        # threshold (alpha/(m-i) for m = 6 at alpha = 0.05).
        [FLOOR_P, FLOOR_P, FLOOR_P, 0.02, 0.02, 0.9],
        [0.05 / 6, 0.05 / 6, 0.05 / 4, 0.05 / 4, 0.3, 0.3]],
    ids=["floor-ties", "threshold-ties"])
def test_tie_order_invariance_exhaustive(procedure, pvals):
    """A permutation of tied p-values permutes the rejection set, and nothing else."""
    base = np.array(pvals, dtype=float)
    reject = procedure(base)
    for perm in itertools.permutations(range(base.size)):
        perm = np.array(perm)
        assert np.array_equal(procedure(base[perm]), reject[perm]), perm.tolist()

def test_hochberg_steps_up_and_holm_steps_down():
    """The case that separates the procedures, plus the ``<=`` boundary tie."""
    # m = 3, alpha = 0.05, thresholds 0.0167 / 0.025 / 0.05. Holm stops at the
    # first failure (0.04 > 0.025) -> 1; Hochberg rejects from 0.045 <= 0.05 down -> 3.
    pvals = np.array([0.01, 0.04, 0.045])
    for holm_impl in (paired.holm, error_bars.holm):
        assert holm_impl(pvals).tolist() == [True, False, False]
    assert significance.hochberg(pvals).tolist() == [True, True, True]

    # m = 4: the three tied values sit exactly at 0.05/4; a `<` would reject 0.
    tie = np.array([0.0125, 0.0125, 0.0125, 0.9])
    for procedure in (paired.holm, error_bars.holm, significance.hochberg):
        assert int(procedure(tie).sum()) == 3
        assert not procedure(tie)[3]

    # No script carries a private copy of a multiplicity procedure.
    assert extens_vs_noise.holm is paired.holm
    assert extens_vs_noise.hochberg is significance.hochberg
    assert significance.holm is paired.holm
    assert hint_vs_noise.holm is error_bars.holm

@pytest.mark.parametrize("diffs, expected", [
        # S = 2, d = (2, 1): totals +3 +1 -1 -3; |T_obs| = 3 -> 2/4.
        ([2, 1], 2 / 4),
        # S = 3, d = (3, 1, 1): totals +5 +3 +3 +1 -1 -3 -3 -5; |T_obs| = 5 -> 2/8.
        ([3, 1, 1], 2 / 8),
        # d = (2, -1, 1): totals +2 +4 0 +2 -2 0 -4 -2; |T| >= 2 in 6 of 8.
        ([2, -1, 1], 6 / 8),
        # A zero cluster doubles tail and denominator alike: p unchanged.
        ([2, 1, 0], 2 / 4),
        # |T_obs| = 0, so every assignment matches it.
        ([0, 0, 0], 1.0),
        # Empty family: guarded rather than dividing by zero.
        ([], 1.0)])
def test_signflip_exact_p_matches_hand_enumeration(diffs, expected):
    """Hand-enumerated reference distributions, plus symmetry and the 2/2**S floor."""
    p = paired.signflip_exact_p(diffs)
    assert p == pytest.approx(expected)
    assert p == pytest.approx(paired.signflip_exact_p([-d for d in diffs]))
    assert 0 < p <= 1
    if diffs:
        # The observed assignment and its global negation always qualify.
        assert p >= 2 / 2 ** len(diffs)

def _one_item_per_seed(marks_a, marks_b):
    """Build ``aligned``-shaped arrays with one item per replicate seed."""
    a = np.array(marks_a, dtype=bool)
    b = np.array(marks_b, dtype=bool)
    return a, b, np.arange(a.size)

@pytest.mark.parametrize("nb, nc", [(0, 0), (1, 0), (2, 3), (3, 1), (5, 1), (4, 4), (7, 2)])
def test_signflip_equals_mcnemar_for_every_singleton_split(nb, nc):
    """With one item per cluster the cluster test IS exact McNemar."""
    marks_a = [1] * nb + [0] * nc + [1, 0, 1, 0]
    marks_b = [0] * nb + [1] * nc + [1, 0, 1, 0]
    a, b, sidx = _one_item_per_seed(marks_a, marks_b)
    p = paired.signflip_exact_p(paired.seed_diffs(a, b, sidx))
    assert p == pytest.approx(paired.mcnemar_exact_p(nb, nc))
    if (nb, nc) == (3, 1):
        # Hand anchor: the 6 concordant items cancel; over the 4 discordant
        # clusters |T| >= 2 holds for 1 + 4 + 4 + 1 = 10 of 16 -> 0.625.
        assert p == pytest.approx(0.625)

def test_seed_diffs_sums_to_the_mcnemar_margin():
    """``sum_s d_s == b - c`` exactly: both tests read the same signal."""
    #        seed 0  |  seed 1  |  seed 2
    a = np.array([1, 1, 0,   1, 0, 0,   1, 1, 1], dtype=bool)
    b = np.array([0, 1, 1,   1, 0, 1,   0, 1, 0], dtype=bool)
    sidx = np.repeat(np.arange(3), 3)
    nb = int((a & ~b).sum())
    nc = int((~a & b).sum())
    diffs = paired.seed_diffs(a, b, sidx)
    assert diffs == [0, -1, 2]          # per seed: (2-2), (1-2), (3-1)
    assert (nb, nc) == (3, 2)           # A wins items 0, 6, 8; B wins 2, 5
    assert sum(diffs) == nb - nc == 1

def test_block_signflip_reduces_to_exact_mcnemar_with_one_cell_per_block():
    """One cell per block -> McNemar up to MC error; deterministic; null gives p = 1."""
    # b=5, c=2, 6 concordant: 2 * (1 + 7 + 21) / 128 = 58/128, tol ~5 SE at B=20k.
    n_win_b, n_win_a, n_tied = 5, 2, 6
    succ = np.array([(0, 1)] * n_win_b + [(1, 0)] * n_win_a
                    + [(1, 1)] * 3 + [(0, 0)] * (n_tied - 3), dtype=np.int32)
    models = ["m_a", "m_b"]
    contrasts = [("m_a vs m_b", "m_a", "m_b")]
    kw = dict(B=20_000, seed=20260821)
    p_block = error_bars.block_signflip_p(succ, models, contrasts, **kw)[0]
    assert ded_pa.mcnemar_exact_p(n_win_a, n_win_b) == pytest.approx(58 / 128)
    assert abs(p_block - 58 / 128) < 0.018
    assert p_block == error_bars.block_signflip_p(succ, models, contrasts, **kw)[0]
    # The observed assignment is in its own reference distribution -> 1.0, not 1/(B+1).
    null = np.array([[1, 1], [0, 0], [1, 1], [0, 0]], dtype=np.int32)
    assert error_bars.block_signflip_p(null, models, [("null", "m_a", "m_b")],
                                       B=1_000, seed=1)[0] == pytest.approx(1.0)

def _cell(model, theorem, verdict, k=1, rung="stepk:1", replicate_idx=0):
    return {"kind": "cell", "model": model, "theorem_id": theorem, "k": k,
            "rung": rung, "replicate_idx": replicate_idx, "verdict": verdict}

@pytest.fixture
def rows_dir(tmp_path):
    """Two lanes: thm_a graded in both, thm_b only in m2, thm_c nowhere, plus rows to ignore."""
    lanes = {
        "m1": [
            _cell("m1", "thm_a", "exception"),
            _cell("m1", "thm_a", "success"),
            _cell("m1", "thm_a", "failure"),        # later retry: must not win
            _cell("m1", "thm_b", "exception"),
            _cell("m1", "thm_b", "replay_failed"),
            _cell("m1", "thm_c", "replay_failed"),
            _cell("m1", "thm_a", "success", k=2, replicate_idx=1),
            {"kind": "sanity", "model": "m1", "verdict": "success"},
        ],
        "m2": [
            _cell("m2", "thm_a", "failure"),
            _cell("m2", "thm_b", "success"),
            _cell("m2", "thm_c", "exception"),
        ],
    }
    for model, rows in lanes.items():
        lane = tmp_path / model
        lane.mkdir()
        (lane / "verified_rows.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
    return tmp_path

@pytest.mark.parametrize("verdicts, expected", [
        (["success"], 1),
        (["failure"], 0),
        (["incomplete"], 0),                       # real behaviour, scores 0
        (["exception", "success"], 1),             # unmeasurable row yields
        (["replay_failed", "failure"], 0),
        (["success", "failure"], 1),               # EARLIEST survivor wins ...
        (["failure", "success"], 0),               # ... in both directions
        (["exception", "replay_failed"], None),    # nothing measurable at all
        ([], None)])
def test_grade_verdicts_is_the_row_rule(verdicts, expected):
    """Earliest survivor wins; unmeasurable is None, deliberately not 0."""
    assert ded_pa.grade_verdicts(verdicts) == expected

def test_all_loaders_share_the_one_row_rule(rows_dir, monkeypatch):
    """``build_pool`` un-augmented == ``load_joint_cells``; count-as-failure adds only model-dependent cells."""
    monkeypatch.setattr(error_bars, "MODELS", ["m1", "m2"])

    _models, blocks, _rungs, meta = error_bars.build_pool(rows_dir, count_as_failure=False)
    ref_models, ref_blocks, _ = ded_pa.load_joint_cells(
        [rows_dir / m / "verified_rows.jsonl" for m in ("m1", "m2")], models=("m1", "m2"))

    def flatten(bl):
        return {(thm, ck[0], ck[1], model): value
                for thm, cmap in bl.items()
                for ck, mv in cmap.items() for model, value in mv.items()}

    assert ref_models == ["m1", "m2"]
    assert flatten(blocks) == flatten(ref_blocks)
    # Only thm_a survives the pairing: m1 on its earliest surviving row.
    assert flatten(blocks) == {("thm_a", 1, "stepk:1", "m1"): 1,
                               ("thm_a", 1, "stepk:1", "m2"): 0}
    assert meta["count_as_failure"] is False

    # thm_b's fault travelled with m1's own output -> scored 0; thm_c never is.
    _models, blocks, _rungs, meta = error_bars.build_pool(rows_dir, count_as_failure=True)
    assert sorted(blocks) == ["thm_a", "thm_b"]
    assert blocks["thm_b"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
    assert meta["added"] == {"m1": [("thm_b", 1, "stepk:1")]}
    assert meta["n_unresolved"] == {"m1": 1, "m2": 1}
    assert set(meta["own_denominator"].values()) == {2}

def test_hint_vs_noise_loader_applies_the_same_rule(tmp_path):
    """``load_rungs`` grades both rungs through ``grade_verdicts``, earliest survivor first."""
    path = tmp_path / "verified_rows.jsonl"
    rows = [
        _cell("m1", "t1", "exception", rung="hint:3"),
        _cell("m1", "t1", "success", rung="hint:3"),
        _cell("m1", "t1", "success", rung="noise:3"),
        _cell("m1", "t1", "failure", rung="noise:3"),   # later draw: ignored
        _cell("m1", "t2", "replay_failed", rung="hint:3"),
        _cell("m1", "t2", "failure", rung="noise:3"),
        _cell("m1", "t3", "success", rung="stepk:1"),   # other rung: ignored
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    cells = hint_vs_noise.load_rungs(path, "m1")
    assert cells[("t1", 1)] == {"hint:3": 1, "noise:3": 1}
    # t2's hint:3 has no surviving row -> absent, not 0; t3 is a different rung.
    assert cells[("t2", 1)] == {"noise:3": 0}
    assert ("t3", 1) not in cells

@pytest.mark.parametrize("nc_extens, nc_noise, expected", [
        (0.00, 0.00, "information"),        # both arms well-formed
        (0.10, 0.24, "information"),        # under the 25% criterion, both arms
        (0.10, 0.25, "COLLAPSE"),           # criterion is inclusive (>=)
        (0.90, 0.99, "COLLAPSE"),           # noise broken wins the label ...
        (0.30, 0.10, "extens degraded")])   # ... otherwise the extens arm's own
def test_extens_vs_noise_mechanism_labels(nc_extens, nc_noise, expected):
    """Which mechanism a lane's contrast can speak to, from measured rates."""
    assert extens_vs_noise.mechanism(nc_extens, nc_noise) == expected

SUPERSEDED_NAME = "all_rows_SUPERSEDED-20260815T000000Z.jsonl"

def _write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path

def test_retired_artifacts_are_refused_everywhere(tmp_path):
    """Every loader hard-refuses a retirement-marked artifact, and names it."""
    from smolbench.deduction.lean import runner

    good = tmp_path / "verified_rows.jsonl"
    with pytest.raises(SystemExit) as excinfo:
        ded_pa.reject_superseded([good, tmp_path / SUPERSEDED_NAME])
    assert SUPERSEDED_NAME in str(excinfo.value)
    ded_pa.reject_superseded([good])
    # The marker is matched on the BASENAME, not on any parent directory.
    ded_pa.reject_superseded([tmp_path / "SUPERSEDED_audit" / "verified_rows.jsonl"])

    path = _write_rows(tmp_path / SUPERSEDED_NAME, [_cell("m1", "t1", "success")])
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        ded_pa.load_joint_cells([path], models=("m1",))
    hint_path = _write_rows(tmp_path / "h" / SUPERSEDED_NAME,
                            [_cell("m1", "t1", "success", rung="hint:3")])
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        hint_vs_noise.load_rungs(hint_path, "m1")

    with pytest.raises(ValueError, match="SUPERSEDED"):
        runner.reject_superseded_rows([tmp_path / SUPERSEDED_NAME])
    assert error_bars.reject_superseded is ded_pa.reject_superseded
    assert ded_pa.RETIRED_MARKERS == runner.RETIRED_MARKERS

    # The snapshot writes three markers for one audit-trail class.
    for name in ("all_rows_SUPERSEDED-20260815T000000Z.jsonl",
                 "all_rows_STALE-20260814T000000Z.jsonl",
                 "verified_rows_BROKEN-20260813T000000Z.jsonl"):
        with pytest.raises(SystemExit):
            ded_pa.reject_superseded([tmp_path / name])
        with pytest.raises(ValueError):
            runner.reject_superseded_rows([tmp_path / name])
    # STALE/BROKEN are anchored on ``_MARKER-``: ordinary words must not trip.
    for name in ("stale_check_rows.jsonl", "unBROKEN.jsonl", "rows_STALEMATE.jsonl"):
        ded_pa.reject_superseded([tmp_path / name])
        runner.reject_superseded_rows([tmp_path / name])

def _theorem_dir_with(tmp_path: Path, filename: str) -> Path:
    """Build a ``theorems/<slug>/`` tree whose outputs hold exactly `filename`."""
    theorem_dir = tmp_path / "theorems" / "T"
    outputs = theorem_dir / "outputs"
    outputs.mkdir(parents=True)
    (theorem_dir / "meta.json").write_text(json.dumps(
        {"full_name": "T", "k": 1, "n_total_tactics": 2, "file_path": "F.lean",
         "ground_truth_remaining_from_k": "exact rfl", "true_premises_at_k": []}))
    _write_rows(outputs / filename,
                [{"rung": "hint:3", "model": "m1", "verdict": "success"}])
    return theorem_dir

def test_lean_runner_and_cli_refuse_superseded_outputs(tmp_path, caplog, capsys):
    """Both ``outputs/*.jsonl`` scanners refuse the artifact and leave the clean path alone."""
    import argparse

    from smolbench.deduction.lean import cli, runner

    theorem_dir = _theorem_dir_with(tmp_path, SUPERSEDED_NAME)
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match="SUPERSEDED"):
            runner.write_theorem_summary(theorem_dir)
    assert SUPERSEDED_NAME in caplog.text
    with pytest.raises(ValueError, match="SUPERSEDED"):
        cli.cmd_show(argparse.Namespace(run_dir=str(tmp_path), theorem=None))

    clean_root = tmp_path / "clean"
    clean = _theorem_dir_with(clean_root, "hint-3__m1.jsonl")
    assert cli.cmd_show(argparse.Namespace(run_dir=str(clean_root),
                                           theorem=None)) == 0
    assert "1/1" in capsys.readouterr().out
    (clean / "outputs" / "hint-3__m1.jsonl").unlink()   # row schema is not the
    runner.write_theorem_summary(clean)                 # subject of this test
    assert (clean / "summary.md").exists()

def test_loaders_refuse_ungraded_rows(tmp_path):
    """The ``unverified`` sentinel is refused on ingestion by both loaders; graded lanes still load."""
    _write_rows(tmp_path / "rows" / "m1" / "verified_rows.jsonl",
                [_cell("m1", "t1", "success"), _cell("m1", "t2", "unverified")])
    with pytest.raises(SystemExit, match="unverified"):
        error_bars.lane_outcomes(tmp_path / "rows", "m1")

    # The recovery sibling is screened on ITS field, not on `verdict`.
    _write_rows(tmp_path / "clean" / "m1" / "verified_rows.jsonl",
                [_cell("m1", "t1", "exception"), _cell("m1", "t1", "success"),
                 _cell("m1", "t2", "replay_failed")])
    rec = _cell("m1", "t3", None)
    rec.pop("verdict")
    rec["recovered_verdict"] = "unverified"
    _write_rows(tmp_path / "rec" / "m1" / "recovered_rows.jsonl", [rec])
    with pytest.raises(SystemExit, match="unverified"):
        error_bars.lane_outcomes(tmp_path / "clean", "m1", tmp_path / "rec")

    _write_rows(tmp_path / "rec2" / "m1" / "recovered_rows.jsonl", [])
    graded, no_survivor = error_bars.lane_outcomes(
        tmp_path / "clean", "m1", tmp_path / "rec2")
    assert graded == {("t1", 1, "stepk:1"): 1}
    assert no_survivor == {("t2", 1, "stepk:1")}

    path = _write_rows(tmp_path / "hvn.jsonl",
                       [_cell("m1", "t1", "success", rung="hint:3"),
                        _cell("m1", "t1", "unverified", rung="noise:3")])
    with pytest.raises(SystemExit, match="unverified"):
        hint_vs_noise.load_rungs(path, "m1")
    clean = _write_rows(tmp_path / "clean.jsonl",
                        [_cell("m1", "t1", "success", rung="hint:3"),
                         _cell("m1", "t1", "lean_error", rung="noise:3")])
    assert hint_vs_noise.load_rungs(clean, "m1") == {("t1", 1): {"hint:3": 1,
                                                                 "noise:3": 0}}
