"""Test the statistical contracts of the five family-ladder analysis scripts.

The scripts under ``notebooks/induction`` and ``notebooks/deduction`` produce
the study's headline numbers. Until now, none of them had a single pytest.
This file pins four properties. A silent edit could break any of them while
every report still looks right.

1. Tie-order invariance of Holm and Hochberg. Both families have many exact
   ties. The seed sign-flip test has a hard resolution floor at
   ``2 / 2**30``, and several contrasts sit exactly on it. So the rejection
   set must be a function of the p-values, never of the order the contrasts
   are built in. (The 2026-08-21 engineering pass checked this invariance ad
   hoc. It is a permanent test now.)
2. Exactness of the seed-level sign-flip test. Its p-values are checked
   against hand-enumerated reference distributions on 2-3 clusters. These are
   written out in the comments, so the test is an independent calculation,
   not a transcription of the implementation.
3. The singleton reduction, twice. Both cluster tests -- the induction seed
   sign-flip and the deduction block sign-flip -- claim in their docstrings
   to collapse onto exact McNemar when every cluster holds one item. That
   claim is load-bearing: it is why the cluster test is a correction, not a
   different question. This file checks the claim.
4. One row rule, one denominator rule. ``grade_verdicts`` is now the only
   implementation of earliest-surviving-row-per-cell plus the
   unmeasurable-verdict exclusion. ``error_bars.build_pool``'s un-augmented
   pool must equal ``load_joint_cells``'s blocks exactly. This equality used
   to be asserted at runtime on every report run (``_check_against_loader``);
   it lives here now. The superseded-artifact refusal is pinned alongside it.

Everything here is fixture-based and offline: no results tree, no rows
directory, no network. The whole file runs in well under a second.
"""

import importlib.util
import itertools
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import binom

REPO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Importing the scripts.
#
# Both legs have a file called ``power_analysis.py``, and each script imports
# it by bare name after putting its own directory on ``sys.path``. So
# whichever leg imports first would win ``sys.modules["power_analysis"]`` for
# the rest of the session. Instead of relying on pytest's collection order,
# each script runs with the right ``power_analysis`` (and, where needed, its
# sibling modules) bound under the bare names for exactly the duration of its
# exec, then unbound. Nothing about the scripts changes; this is purely how
# the test harness reaches them.
# --------------------------------------------------------------------------- #
def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register the module before exec. Dataclass annotation resolution looks
    # up the module in sys.modules while it is still half-imported.
    sys.modules[name] = module
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


_DED = REPO / "notebooks" / "deduction"
_IND = REPO / "notebooks" / "induction"

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


# --------------------------------------------------------------------------- #
# 1. Holm / Hochberg: the rejection set is a function of the p-VALUES.
# --------------------------------------------------------------------------- #
#: Every step-wise procedure under test. Holm has two independent
#: implementations (the two legs never share code), and both copies must hold
#: the property, so this file drives both.
PROCEDURES = [
    pytest.param(paired.holm, id="induction-holm"),
    pytest.param(error_bars.holm, id="deduction-holm"),
    pytest.param(significance.hochberg, id="induction-hochberg"),
]

#: The seed sign-flip test's hard resolution floor at S = 30 replicates. No
#: contrast can report a smaller p, so several report exactly this value.
#: Floor ties are the tie case that actually occurs in this study.
FLOOR_P = 2 / 2 ** 30


@pytest.mark.parametrize("procedure", PROCEDURES)
@pytest.mark.parametrize(
    "pvals",
    [
        # Ties at the floor, ties mid-range, and ties sitting exactly ON a
        # Holm/Hochberg threshold (alpha/(m-i) for m = 6 is 1/120, 1/100, 1/75,
        # 1/60, 1/40, 1/20 at alpha = 0.05).
        [FLOOR_P, FLOOR_P, FLOOR_P, 0.02, 0.02, 0.9],
        [0.05 / 6, 0.05 / 6, 0.05 / 4, 0.05 / 4, 0.3, 0.3],
        [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
        [1.0, 1.0, 1.0, 0.5, 0.5, 0.5],
        [FLOOR_P, 0.05 / 6, 0.0125, 0.0125, 0.5, 1.0],
    ],
    ids=["floor-ties", "threshold-ties", "all-tied", "all-null", "mixed"],
)
def test_tie_order_invariance_exhaustive(procedure, pvals):
    """A permutation of tied p-values permutes the rejection set, and nothing else.

    This test checks all 720 permutations of a 6-element family, so no
    ordering escapes. The property is not an accident of the implementation.
    Holm's and Hochberg's critical values ``alpha / (m - i)`` strictly
    increase with rank, so a group of equal p-values can never straddle the
    stopping rank. Either the first of them already fails its (smallest)
    threshold, and the step stops there for every ordering, or all of them
    clear thresholds at least as large. A rejection that depended on which
    tied contrast sorted first would be a bug. This test turns the two
    implementations' ``kind="stable"`` sorts into a contract, not just a
    habit.
    """
    base = np.array(pvals, dtype=float)
    reject = procedure(base)
    for perm in itertools.permutations(range(base.size)):
        perm = np.array(perm)
        permuted = procedure(base[perm])
        assert np.array_equal(permuted, reject[perm]), (
            f"rejection set moved under permutation {perm.tolist()}"
        )


@pytest.mark.parametrize("procedure", PROCEDURES)
def test_tie_order_invariance_large_family(procedure):
    """Same property on a 210-item family, the size the study actually reports.

    This test uses random permutations, not exhaustive ones, with a fixed
    seed so a failure is reproducible. The family mixes floor ties, a dense
    block of identical mid-range values, and a null tail -- the shape of the
    real primary family.
    """
    rng = np.random.default_rng(20260821)
    base = np.concatenate([
        np.full(5, FLOOR_P),
        np.full(40, 1e-6),
        np.full(60, 0.05 / 210),      # exactly Holm's strictest threshold
        np.full(45, 0.01),
        np.full(60, 0.7),
    ])
    assert base.size == 210
    reject = procedure(base)
    for _ in range(50):
        perm = rng.permutation(base.size)
        assert np.array_equal(procedure(base[perm]), reject[perm])


def test_holm_and_hochberg_admit_a_boundary_tie():
    """A p-value exactly at its own threshold is rejected (``<=``, not ``<``).

    Hand-computed: m = 4, alpha = 0.05, thresholds 0.0125 / 0.0167 / 0.025 /
    0.05. With p = (0.0125, 0.0125, 0.0125, 0.9), all three tied values sit
    at or under their own threshold, and the fourth fails. So both
    procedures must reject exactly 3. A ``<`` comparison would stop at rank 1
    and reject 0 -- the failure mode a family full of floor ties would
    otherwise hide.
    """
    pvals = np.array([0.0125, 0.0125, 0.0125, 0.9])
    for procedure in (paired.holm, error_bars.holm, significance.hochberg):
        assert int(procedure(pvals).sum()) == 3
        assert not procedure(pvals)[3]


def test_hochberg_steps_up_and_holm_steps_down():
    """The one case that separates the two procedures, hand-computed.

    m = 3, alpha = 0.05, thresholds by rank: 0.0167, 0.025, 0.05.
    p = (0.01, 0.04, 0.045).

      Holm (steps down from the smallest): 0.01 <= 0.0167 rejects; 0.04 <=
      0.025 fails, and Holm stops at the first failure -> 1 rejection.

      Hochberg (steps up from the largest): 0.045 <= 0.05 at the loosest
      threshold, so it rejects that rank and every smaller one -> 3
      rejections.

    A Holm that stepped up, or a Hochberg that stepped down, would return the
    other procedure's answer here. This test drives both legs' Holm
    implementations, so neither copy can drift into the wrong direction
    unnoticed.
    """
    pvals = np.array([0.01, 0.04, 0.045])
    for holm_impl in (paired.holm, error_bars.holm):
        assert holm_impl(pvals).tolist() == [True, False, False]
    assert significance.hochberg(pvals).tolist() == [True, True, True]

    # This check is a sanity check only, not a second direction test. On a
    # family with no gap for step-up to exploit, both procedures give the
    # same set, and a step-up Holm would give that same set too. The case
    # above is what separates the directions.
    agree = np.array([0.001, 0.2, 0.9])
    assert paired.holm(agree).tolist() == significance.hochberg(agree).tolist()


def test_every_script_shares_one_holm_and_one_hochberg():
    """No script carries a private copy of a multiplicity procedure.

    ``extens_vs_noise`` and ``significance_report`` correct over the same
    210-contrast family as ``paired_analysis``. If any of them grew its own
    Holm, the reports could disagree with each other while every individual
    file still looked correct. The study has exactly two Holm
    implementations, one per leg (the legs never share code), and one
    Hochberg.
    """
    assert extens_vs_noise.holm is paired.holm
    assert extens_vs_noise.hochberg is significance.hochberg
    assert significance.holm is paired.holm
    assert hint_vs_noise.holm is error_bars.holm


# --------------------------------------------------------------------------- #
# 2. The seed-level sign-flip test is EXACT.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "diffs, expected, why",
    [
        # S = 2, d = (2, 1). The 4 sign assignments give totals
        # +3, +1, -1, -3; |T_obs| = 3, so only +3 and -3 qualify: 2/4.
        ([2, 1], 2 / 4, "two clusters, one extreme pair"),
        # S = 3, d = (3, 1, 1). The 8 totals are
        # +5 +3 +3 +1 -1 -3 -3 -5; |T_obs| = 5 -> 2/8.
        ([3, 1, 1], 2 / 8, "three clusters, only the global flip ties it"),
        # S = 3, d = (2, -1, 1). Totals: +2 +4 0 +2 -2 0 -4 -2; T_obs = 2, so
        # everything with |T| >= 2 counts: 6 of 8.
        ([2, -1, 1], 6 / 8, "a sign-reversed cluster does not cancel the test"),
        # A cluster that contributed no difference doubles both the tail and
        # the denominator, leaving p unchanged: (2, 1) above with a zero added.
        ([2, 1, 0], 2 / 4, "zero clusters are inert"),
        # No difference anywhere: |T_obs| = 0 and every assignment matches it.
        ([0, 0, 0], 1.0, "a null contrast reports p = 1"),
        # Empty family -- guarded rather than dividing by zero.
        ([], 1.0, "no clusters at all"),
    ],
)
def test_signflip_exact_p_matches_hand_enumeration(diffs, expected, why):
    """Hand-enumerated reference distributions, 2-3 clusters (see the table).

    Each case's full sign-flip distribution is written out in the parameter
    comment, and the expected p is read off it. So this is an independent
    calculation of the same quantity, not a snapshot of the DP.
    """
    assert paired.signflip_exact_p(diffs) == pytest.approx(expected), why


def test_signflip_is_symmetric_and_bounded():
    """Check two-sidedness on the same tiny families.

    A negation of every cluster's difference cannot change the p-value,
    and no p escapes the range (0, 1].
    """
    for diffs in ([2, 1], [3, 1, 1], [2, -1, 1], [5, -2, 3]):
        p = paired.signflip_exact_p(diffs)
        assert p == pytest.approx(paired.signflip_exact_p([-d for d in diffs]))
        assert 0 < p <= 1
        # The floor: the observed assignment and its global negation always
        # qualify, so no family of S clusters can report below 2/2**S.
        assert p >= 2 / 2 ** len(diffs)


def _one_item_per_seed(marks_a, marks_b):
    """Build ``aligned``-shaped arrays with one item per replicate seed."""
    a = np.array(marks_a, dtype=bool)
    b = np.array(marks_b, dtype=bool)
    return a, b, np.arange(a.size)


def test_signflip_reduces_to_exact_mcnemar_on_singleton_clusters():
    """With one item per cluster, the cluster test is exact McNemar.

    Hand-computed anchor: 3 items where arm A wins, 1 where B wins, and 6
    concordant items. ``seed_diffs`` turns that into d = (+1, +1, +1, -1) with
    six zeros. Over the 2**10 sign assignments, the zeros contribute a factor
    of 2**6 to the tail and to the denominator, so they cancel exactly. That
    leaves the 4 discordant clusters: |T| >= 2 happens for T in {+4, +2, -2,
    -4}, that is 1 + 4 + 4 + 1 = 10 of 16 assignments -> p = 0.625. Exact
    McNemar on b = 3, c = 1 is 2 * P(X <= 1), X ~ Binomial(4, 1/2) = 2 * 5/16
    = 0.625. The two agree because they are the same test. That is the claim.
    """
    a, b, sidx = _one_item_per_seed(
        [1, 1, 1, 0] + [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1] + [1, 1, 0, 0, 0, 0],
    )
    diffs = paired.seed_diffs(a, b, sidx)
    assert diffs == [1, 1, 1, -1, 0, 0, 0, 0, 0, 0]

    p_cluster = paired.signflip_exact_p(diffs)
    p_mcnemar = paired.mcnemar_exact_p(3, 1)
    assert p_cluster == pytest.approx(0.625)
    assert p_mcnemar == pytest.approx(2 * binom.cdf(1, 4, 0.5))
    assert p_cluster == pytest.approx(p_mcnemar)


@pytest.mark.parametrize("nb, nc", [(0, 0), (1, 0), (2, 3), (5, 1), (4, 4), (7, 2)])
def test_signflip_equals_mcnemar_for_every_singleton_split(nb, nc):
    """The reduction holds for any discordant split, not just the anchor case.

    This test builds the data through ``seed_diffs``, so the composition
    ``aligned -> seed_diffs -> signflip_exact_p`` is covered end to end. The
    data is padded with concordant items, which must stay inert.
    """
    marks_a = [1] * nb + [0] * nc + [1, 0, 1, 0]
    marks_b = [0] * nb + [1] * nc + [1, 0, 1, 0]
    a, b, sidx = _one_item_per_seed(marks_a, marks_b)
    assert paired.signflip_exact_p(paired.seed_diffs(a, b, sidx)) == pytest.approx(
        paired.mcnemar_exact_p(nb, nc)
    )


def test_seed_diffs_sums_to_the_mcnemar_margin():
    """``sum_s d_s == b - c`` exactly -- the two tests read the same signal.

    Nine items spread over three seeds, so the clusters are genuinely
    multi-item. This is the property that makes the cluster test a
    correction to the item-level McNemar, not a different question about the
    data.
    """
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


# --------------------------------------------------------------------------- #
# 3. The deduction block sign-flip reduces to exact McNemar too.
# --------------------------------------------------------------------------- #
def test_block_signflip_reduces_to_exact_mcnemar_with_one_cell_per_block():
    """One cell per theorem block -> the block test is McNemar, up to MC error.

    Hand-computed reference: 5 blocks where model B wins, 2 where A wins, 6
    concordant blocks (D_t = 0, inert under a sign flip). Exact McNemar on
    b = 5, c = 2 is 2 * P(X <= 2), X ~ Binomial(7, 1/2)
    = 2 * (1 + 7 + 21) / 128 = 58/128 = 0.453125. The sign-flip enumeration
    agrees by the same arithmetic. Over the 7 discordant blocks, |T| >= 3 for
    every assignment except the 2 * C(7, 3) = 70 with |T| = 1, that is
    (128 - 70) / 128 = 58/128.

    This test is Monte Carlo. The implementation resamples and applies the
    ``(count + 1) / (B + 1)`` finite-B correction, so it can never equal the
    exact value. The case is chosen well away from the 1/(B+1) floor. The
    tolerance is about 5 standard errors of a B = 20,000 draw at p = 0.45,
    5 * sqrt(0.45 * 0.55 / 20000) = 0.018. The literal value 0.453125 comes
    from the arithmetic above, not from running the code.
    """
    n_win_b, n_win_a, n_tied = 5, 2, 6
    rows = (
        [(0, 1)] * n_win_b + [(1, 0)] * n_win_a
        + [(1, 1)] * 3 + [(0, 0)] * (n_tied - 3)
    )
    succ = np.array(rows, dtype=np.int32)          # (n_blocks, 2 models)
    models = ["m_a", "m_b"]
    contrasts = [("m_a vs m_b", "m_a", "m_b")]

    p_block = error_bars.block_signflip_p(
        succ, models, contrasts, B=20_000, seed=20260821
    )[0]
    p_exact = ded_pa.mcnemar_exact_p(n_win_a, n_win_b)
    assert p_exact == pytest.approx(58 / 128)
    assert abs(p_block - 58 / 128) < 0.018

    # Determinism: the report must be byte-reproducible from the same rows, so
    # the same seed must give the same p.
    again = error_bars.block_signflip_p(
        succ, models, contrasts, B=20_000, seed=20260821
    )[0]
    assert p_block == again


def test_block_signflip_counts_the_observed_assignment():
    """A contrast with no difference at all reports p = 1, not 1/(B+1).

    The observed sign assignment is always in its own reference distribution.
    If you drop it, you get the classic off-by-one that makes a permutation
    test anticonservative.
    """
    succ = np.array([[1, 1], [0, 0], [1, 1], [0, 0]], dtype=np.int32)
    p = error_bars.block_signflip_p(
        succ, ["m_a", "m_b"], [("null", "m_a", "m_b")], B=1_000, seed=1
    )[0]
    assert p == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# 4. One row rule; one denominator rule; and no superseded artifacts.
# --------------------------------------------------------------------------- #
def _cell(model, theorem, verdict, k=1, rung="stepk:1", replicate_idx=0):
    return {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": replicate_idx, "verdict": verdict,
    }


@pytest.fixture
def rows_dir(tmp_path):
    """A two-lane rows tree exercising every branch of the row rule.

    * ``thm_a`` -- graded in both lanes, and in ``m1`` only after an
      ``exception`` row. So earliest-surviving (not earliest, not latest) is
      the only rule that gets it right: the surviving order is success, then
      a later retry that failed.
    * ``thm_b`` -- every ``m1`` row is unmeasurable, so the cell has no
      survivor. ``m2`` grades it, which makes it model-dependent and
      therefore the count-as-failure rule's business.
    * ``thm_c`` -- unmeasurable in both lanes: never measured anywhere, so no
      rule may resurrect it.
    * plus a non-cell row and a second replicate, both of which must be
      ignored.
    """
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
            "".join(json.dumps(r) + "\n" for r in rows)
        )
    return tmp_path


@pytest.mark.parametrize(
    "verdicts, expected",
    [
        (["success"], 1),
        (["failure"], 0),
        (["incomplete"], 0),                       # real behaviour, scores 0
        (["exception", "success"], 1),             # unmeasurable row yields
        (["replay_failed", "failure"], 0),
        (["success", "failure"], 1),               # EARLIEST survivor wins ...
        (["failure", "success"], 0),               # ... in both directions
        (["exception", "replay_failed"], None),    # nothing measurable at all
        ([], None),
    ],
)
def test_grade_verdicts_is_the_row_rule(verdicts, expected):
    """The shared rule: earliest survivor wins, unmeasurable is not a result.

    ``None`` means "no surviving attempt" and is deliberately not 0. The
    difference between the drop rule and count-as-failure is what the caller
    then does with it.
    """
    assert ded_pa.grade_verdicts(verdicts) == expected


def test_all_loaders_share_the_one_row_rule(rows_dir, monkeypatch):
    """``lane_outcomes`` and ``load_joint_cells`` agree, cell for cell.

    This is the check ``error_bars._check_against_loader`` used to make on
    every report run. Since 2026-08-21 the two read rows through the same
    ``grade_verdicts``, so drift is no longer possible by construction. But
    the equality is the contract the count-as-failure and recovery layers
    are built on, so this test pins it here instead of dropping it.
    """
    monkeypatch.setattr(error_bars, "MODELS", ["m1", "m2"])

    _models, blocks, _rungs, meta = error_bars.build_pool(
        rows_dir, count_as_failure=False
    )
    ref_models, ref_blocks, _ = ded_pa.load_joint_cells(
        [rows_dir / m / "verified_rows.jsonl" for m in ("m1", "m2")],
        models=("m1", "m2"),
    )

    def flatten(bl):
        return {(thm, ck[0], ck[1], model): value
                for thm, cmap in bl.items()
                for ck, mv in cmap.items() for model, value in mv.items()}

    assert ref_models == ["m1", "m2"]
    assert flatten(blocks) == flatten(ref_blocks)
    # And the pool is the one the fixture describes: only thm_a survives the
    # pairing, m1 on its earliest surviving row (success), m2 on its failure.
    assert flatten(blocks) == {
        ("thm_a", 1, "stepk:1", "m1"): 1,
        ("thm_a", 1, "stepk:1", "m2"): 0,
    }
    assert meta["count_as_failure"] is False


def test_count_as_failure_adds_only_model_dependent_cells(rows_dir, monkeypatch):
    """The denominator rule, measured on the fixture that separates the cases.

    ``thm_b`` has no surviving row in m1 but grades in m2, so the fault
    travelled with m1's own output: it is scored 0 and joins the pool.
    ``thm_c`` is unmeasurable in every lane, so it stays out. If you
    scored it, you would invent a failure nobody observed.
    """
    monkeypatch.setattr(error_bars, "MODELS", ["m1", "m2"])
    _models, blocks, _rungs, meta = error_bars.build_pool(
        rows_dir, count_as_failure=True
    )
    assert sorted(blocks) == ["thm_a", "thm_b"]
    assert blocks["thm_b"][(1, "stepk:1")] == {"m1": 0, "m2": 1}
    assert meta["added"] == {"m1": [("thm_b", 1, "stepk:1")]}
    # thm_c is unresolved for both lanes and never becomes a failure.
    assert meta["n_unresolved"] == {"m1": 1, "m2": 1}
    # Every lane ends on the SAME denominator, which is the point of the rule.
    assert set(meta["own_denominator"].values()) == {2}


def test_hint_vs_noise_loader_applies_the_same_rule(tmp_path):
    """``load_rungs`` grades its two rungs through ``grade_verdicts`` as well.

    The retry after an exception must be graded, and the second surviving row
    for the same cell must be ignored. A last-wins rule here would report
    pass@2 as pass@1 on exactly the cells a resume bug re-ran.
    """
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


@pytest.mark.parametrize(
    "nc_extens, nc_noise, expected",
    [
        (0.00, 0.00, "information"),        # both arms well-formed
        (0.10, 0.24, "information"),        # under the 25% criterion, both arms
        (0.10, 0.25, "COLLAPSE"),           # criterion is inclusive (>=)
        (0.90, 0.99, "COLLAPSE"),           # noise broken wins the label ...
        (0.30, 0.10, "extens degraded"),    # ... otherwise the extens arm's own
    ],
)
def test_extens_vs_noise_mechanism_labels(nc_extens, nc_noise, expected):
    """Which mechanism a lane's contrast can speak to, from measured rates.

    The report's two-mechanism reading rests on this branch. Where the noise
    arm has stopped obeying the output contract, an extens-higher result is
    mechanically forced and cannot be read as an information effect. Where
    the extens arm is the broken one, the asymmetry runs the other way. Only
    with both arms well-formed is "information" available. The order
    matters: the noise arm is tested first, so a lane with both arms
    collapsed is labelled COLLAPSE, the conservative reading.
    """
    assert extens_vs_noise.mechanism(nc_extens, nc_noise) == expected
    assert extens_vs_noise.COLLAPSE_THRESHOLD == 0.25


# --- superseded artifacts ---------------------------------------------------
SUPERSEDED_NAME = "all_rows_SUPERSEDED-20260815T000000Z.jsonl"


def _write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_reject_superseded_names_every_offender(tmp_path):
    """The refusal is loud, names the file, and is a hard refusal, not a warning.

    A byte-identical copy of the retired mixed-hardware ``all_rows`` artifact
    sits inside the S3 analysis snapshot. It parses cleanly, so a loader that
    only warned would emit a complete, plausible, wrong report.
    """
    good = tmp_path / "verified_rows.jsonl"
    bad = tmp_path / SUPERSEDED_NAME
    with pytest.raises(SystemExit) as excinfo:
        ded_pa.reject_superseded([good, bad])
    message = str(excinfo.value)
    assert SUPERSEDED_NAME in message
    assert "SUPERSEDED" in message
    # A clean list passes silently.
    ded_pa.reject_superseded([good])
    # The marker is matched on the BASENAME: a directory named after an audit
    # is not the artifact being guarded against.
    ded_pa.reject_superseded([tmp_path / "SUPERSEDED_audit" / "verified_rows.jsonl"])


def test_load_joint_cells_refuses_a_superseded_file(tmp_path):
    rows = [_cell("m1", "t1", "success")]
    path = _write_rows(tmp_path / SUPERSEDED_NAME, rows)
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        ded_pa.load_joint_cells([path], models=("m1",))


def test_lane_outcomes_guards_both_of_its_sources(tmp_path):
    """``lane_outcomes`` screens both sources, and still loads a clean pair.

    Its two paths are built from fixed basenames
    (``<dir>/<model>/verified_rows.jsonl`` and the recovery sibling), so a
    superseded artifact cannot reach it through today's call sites. The
    guard is defence in depth against a future caller that builds the list
    some other way. That is why this test exercises the refusal itself on
    the shared function, and exercises the loader on the path it really
    takes.
    """
    assert error_bars.reject_superseded is ded_pa.reject_superseded
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        error_bars.reject_superseded([tmp_path / "m1" / SUPERSEDED_NAME])

    _write_rows(tmp_path / "rows" / "m1" / "verified_rows.jsonl",
                [_cell("m1", "t1", "exception"), _cell("m1", "t1", "success"),
                 _cell("m1", "t2", "replay_failed")])
    _write_rows(tmp_path / "rec" / "m1" / "recovered_rows.jsonl", [])
    graded, no_survivor = error_bars.lane_outcomes(
        tmp_path / "rows", "m1", tmp_path / "rec"
    )
    assert graded == {("t1", 1, "stepk:1"): 1}
    assert no_survivor == {("t2", 1, "stepk:1")}


def test_hint_vs_noise_refuses_a_superseded_file(tmp_path):
    path = _write_rows(tmp_path / SUPERSEDED_NAME,
                       [_cell("m1", "t1", "success", rung="hint:3")])
    with pytest.raises(SystemExit, match="SUPERSEDED"):
        hint_vs_noise.load_rungs(path, "m1")


# --------------------------------------------------------------------------- #
# The ungraded sentinel. Cell rows are written with verdict "unverified" at
# generation time, and a later verification pass grades them. `grade_verdicts`
# scores that placeholder 0, a real failure, because it is not in
# UNMEASURABLE_VERDICTS. It must not be added there either: that would turn a
# loud condition into a silent drop. So the loaders refuse it at the point
# rows enter, the same way they refuse a superseded artifact, and for the
# same reason: the resulting report would be complete, plausible, and wrong.
# --------------------------------------------------------------------------- #
def test_lane_outcomes_refuses_ungraded_rows(tmp_path):
    """Both of ``lane_outcomes``' sources are screened, and clean rows load.

    Each source is checked on the verdict field it reads: ``verdict`` for the
    primary rows, ``recovered_verdict`` for the recovery sibling. So a
    sentinel cannot enter through either one.
    """
    _write_rows(tmp_path / "rows" / "m1" / "verified_rows.jsonl",
                [_cell("m1", "t1", "success"), _cell("m1", "t2", "unverified")])
    with pytest.raises(SystemExit) as excinfo:
        error_bars.lane_outcomes(tmp_path / "rows", "m1")
    message = str(excinfo.value)
    assert "unverified" in message
    assert "1" in message, "the message must carry the offending row COUNT"
    assert "verified_rows.jsonl" in message, "the message must name the FILE"

    # The recovery sibling is screened on ITS field, not on `verdict`.
    _write_rows(tmp_path / "clean" / "m1" / "verified_rows.jsonl",
                [_cell("m1", "t1", "success")])
    rec = _cell("m1", "t2", None)
    rec.pop("verdict")
    rec["recovered_verdict"] = "unverified"
    _write_rows(tmp_path / "rec" / "m1" / "recovered_rows.jsonl", [rec])
    with pytest.raises(SystemExit, match="unverified"):
        error_bars.lane_outcomes(tmp_path / "clean", "m1", tmp_path / "rec")

    # Positive path: a fully graded lane still loads, so the guard is not a
    # blanket refusal of every input.
    graded, no_survivor = error_bars.lane_outcomes(tmp_path / "clean", "m1")
    assert graded == {("t1", 1, "stepk:1"): 1}
    assert no_survivor == set()


def test_hint_vs_noise_refuses_ungraded_rows(tmp_path):
    """``load_rungs`` refuses a sentinel row and still loads a graded file.

    The refusal happens on ingestion, before the rung filter. An ungraded row
    in a rung this comparison does not read is still evidence the
    verification pass did not finish, and the paired hint-vs-noise b/c
    counts are exactly the statistic a silently-failed row biases.
    """
    path = _write_rows(tmp_path / "verified_rows.jsonl",
                       [_cell("m1", "t1", "success", rung="hint:3"),
                        _cell("m1", "t1", "unverified", rung="noise:3")])
    with pytest.raises(SystemExit) as excinfo:
        hint_vs_noise.load_rungs(path, "m1")
    message = str(excinfo.value)
    assert "unverified" in message
    assert "1" in message, "the message must carry the offending row COUNT"
    assert "verified_rows.jsonl" in message, "the message must name the FILE"

    clean = _write_rows(tmp_path / "clean.jsonl",
                        [_cell("m1", "t1", "success", rung="hint:3"),
                         _cell("m1", "t1", "lean_error", rung="noise:3")])
    assert hint_vs_noise.load_rungs(clean, "m1") == {
        ("t1", 1): {"hint:3": 1, "noise:3": 0}
    }


def _theorem_dir_with(tmp_path: Path, filename: str) -> Path:
    """Build a ``theorems/<slug>/`` tree whose outputs hold exactly `filename`."""
    theorem_dir = tmp_path / "theorems" / "T"
    outputs = theorem_dir / "outputs"
    outputs.mkdir(parents=True)
    (theorem_dir / "meta.json").write_text(json.dumps(
        {"full_name": "T", "k": 1, "n_total_tactics": 2, "file_path": "F.lean",
         "ground_truth_remaining_from_k": "exact rfl", "true_premises_at_k": []}
    ))
    _write_rows(outputs / filename,
                [{"rung": "hint:3", "model": "m1", "verdict": "success"}])
    return theorem_dir


def test_lean_runner_refuses_superseded_outputs(tmp_path, caplog):
    """``write_theorem_summary``'s ``outputs/*.jsonl`` glob refuses the artifact.

    Today's archive is written one directory above this glob, so the guard
    is a guarantee against a future layout, not a fix for a live bug. That is
    exactly when the guard is cheapest to install. It both logs and raises:
    this function runs inside the sweep's per-theorem worker, whose caller
    catches ``Exception`` and prints a single line, so the file name has to
    survive that path.
    """
    from smolbench.deduction.lean import runner

    with pytest.raises(ValueError, match="SUPERSEDED"):
        runner.reject_superseded_rows([tmp_path / SUPERSEDED_NAME])
    runner.reject_superseded_rows([tmp_path / "hint-3__m1.jsonl"])  # clean: silent

    theorem_dir = _theorem_dir_with(tmp_path, SUPERSEDED_NAME)
    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match="SUPERSEDED"):
            runner.write_theorem_summary(theorem_dir)
    assert SUPERSEDED_NAME in caplog.text

    # The guard does not disturb the clean path: a theorem whose outputs hold
    # no superseded artifact still writes its summary.
    clean = _theorem_dir_with(tmp_path / "clean", "hint-3__m1.jsonl")
    (clean / "outputs" / "hint-3__m1.jsonl").unlink()   # row schema is not the
    runner.write_theorem_summary(clean)                 # subject of this test
    assert (clean / "summary.md").exists()


def test_lean_cli_show_refuses_superseded_outputs(tmp_path, capsys):
    """``cmd_show``'s listing mode re-scans ``outputs/*.jsonl``, guarded too.

    The listing tallies pass counts by reading those files directly, so an
    ingested superseded artifact would print a plausible, wrong coverage
    table.
    """
    import argparse

    from smolbench.deduction.lean import cli

    _theorem_dir_with(tmp_path, SUPERSEDED_NAME)
    args = argparse.Namespace(run_dir=str(tmp_path), theorem=None)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        cli.cmd_show(args)

    clean_root = tmp_path / "clean"
    _theorem_dir_with(clean_root, "hint-3__m1.jsonl")
    assert cli.cmd_show(argparse.Namespace(run_dir=str(clean_root),
                                           theorem=None)) == 0
    assert "1/1" in capsys.readouterr().out


def test_all_three_retirement_markers_are_refused(tmp_path):
    """The snapshot writes three retirement markers for one audit-trail class.

    (See scripts/snapshot_analysis_data.py: *_SUPERSEDED-*, *_STALE-*,
    *_BROKEN-*.) The guard must refuse all three, in both the notebook and
    package copies.
    """
    from smolbench.deduction.lean import runner

    for name in ("all_rows_SUPERSEDED-20260815T000000Z.jsonl",
                  "all_rows_STALE-20260814T000000Z.jsonl",
                  "verified_rows_BROKEN-20260813T000000Z.jsonl"):
        with pytest.raises(SystemExit):
            ded_pa.reject_superseded([tmp_path / name])
        with pytest.raises(ValueError):
            runner.reject_superseded_rows([tmp_path / name])
    # STALE/BROKEN are anchored on ``_MARKER-``. Ordinary words that contain
    # those letters must not trip the guard. SUPERSEDED stays bare, the
    # historical form of the one real retired artifact.
    for name in ("stale_check_rows.jsonl", "unBROKEN.jsonl",
                  "rows_STALEMATE.jsonl"):
        ded_pa.reject_superseded([tmp_path / name])
        runner.reject_superseded_rows([tmp_path / name])
    assert ded_pa.RETIRED_MARKERS == runner.RETIRED_MARKERS
