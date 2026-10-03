"""Statistical contracts of the family-ladder analysis scripts (offline)."""

import itertools
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from tests._paths import NOTEBOOKS, load_by_path

def _load(name: str, rel: str) -> ModuleType:
    mod = load_by_path(NOTEBOOKS / rel, name)
    sys.modules[Path(rel).stem] = mod  # siblings import each other by bare name
    return mod

ind_pa = _load("ind_power_analysis", "induction/analysis/power_analysis.py")
paired = _load("ind_paired", "induction/analysis/paired_analysis.py")
significance = _load("ind_significance", "induction/analysis/significance_report.py")
extens_vs_noise = _load("ind_extens_vs_noise", "induction/analysis/extens_vs_noise.py")
for _bare in (
    "power_analysis",
    "paired_analysis",
    "significance_report",
    "extens_vs_noise",
):
    sys.modules.pop(_bare, None)

import _power_common as pc  # noqa: E402

def test_shared_scaffolding_wiring() -> None:
    assert ind_pa.RESULTS_DIR == NOTEBOOKS / "induction" / "results"
    # ``None`` means not reached within the cap.
    assert [pc.fmt_r(*a) for a in ((None, 80), (None, 200), (1, 80), (80, 80), (200, 80))] == [
        ">80", ">200", "1", "80", "200"]
    assert pc.results_dir("induction") == NOTEBOOKS / "induction" / "results"
    # Multiplicity procedures must have one implementation.
    assert (extens_vs_noise.holm, significance.holm) == (paired.holm, paired.holm)
    assert extens_vs_noise.hochberg is significance.hochberg

#: The m=3 verdicts differ because Holm stops at the first failure while Hochberg
#: steps up from 0.045, at .0167/.025/.05 thresholds.
PROCEDURES = [pytest.param(paired.holm, [True, False, False], id="induction-holm"),
              pytest.param(significance.hochberg, [True, True, True], id="hochberg")]
FLOOR_P = 2 / 2 ** 30  # Sign-flip resolution floor for 30 seeds.

@pytest.mark.parametrize("procedure, stepped", PROCEDURES)
@pytest.mark.parametrize("pvals", [
    # Ties at the floor and exact m=6 thresholds.
    [FLOOR_P, FLOOR_P, FLOOR_P, 0.02, 0.02, 0.9],
    [0.05 / 6, 0.05 / 6, 0.05 / 4, 0.05 / 4, 0.3, 0.3]],
    ids=["floor-ties", "threshold-ties"])
def test_tie_order_invariance_and_stepping(
    procedure: Callable[[np.ndarray], np.ndarray], stepped: list[bool], pvals: list[float]
) -> None:
    base = np.array(pvals, dtype=float)
    reject = procedure(base)
    for perm in map(list, itertools.permutations(range(base.size))):
        assert np.array_equal(procedure(base[perm]), reject[perm]), perm
    assert procedure(np.array([0.01, 0.04, 0.045])).tolist() == stepped
    # Exact 0.05/4 ties reject; strict ``<`` would not.
    tie = np.array([0.0125, 0.0125, 0.0125, 0.9])
    assert procedure(tie).tolist() == [True, True, True, False]

@pytest.mark.parametrize("diffs, expected", [
    ([2, 1], 2 / 4), ([3, 1, 1], 2 / 8),   # totals +-3 +-1 / +-5 +-3 +-3 +-1: only |T_obs|
    ([2, -1, 1], 6 / 8),                   # |T| >= 2 in 6 of 8
    ([2, 1, 0], 2 / 4),                    # a zero cluster doubles tail and denominator
    ([0, 0, 0], 1.0), ([], 1.0)])          # |T_obs| = 0 matches all; empty family guarded
def test_signflip_exact_p_matches_hand_enumeration(diffs: list[int], expected: float) -> None:
    p = paired.signflip_exact_p(diffs)
    assert p == pytest.approx(expected)
    assert p == pytest.approx(paired.signflip_exact_p([-d for d in diffs]))
    assert 0 < p <= 1
    if diffs:  # the observed assignment and its global negation always qualify
        assert p >= 2 / 2 ** len(diffs)

@pytest.mark.parametrize("nb, nc", [(0, 0), (1, 0), (2, 3), (3, 1), (5, 1), (4, 4), (7, 2)])
def test_signflip_equals_mcnemar_for_every_singleton_split(nb: int, nc: int) -> None:
    # with one item per cluster the cluster test is exact McNemar
    a = np.array([1] * nb + [0] * nc + [1, 0, 1, 0], dtype=bool)
    b = np.array([0] * nb + [1] * nc + [1, 0, 1, 0], dtype=bool)
    p = paired.signflip_exact_p(paired.seed_diffs(a, b, np.arange(a.size)))
    assert p == pytest.approx(paired.mcnemar_exact_p(nb, nc))
    if (nb, nc) == (3, 1):
        # hand anchor: 6 concordant cancel; |T| >= 2 for 1+4+4+1 = 10 of 16
        assert p == pytest.approx(0.625)

def test_paired_signal_reductions() -> None:
    # ``sum_s d_s == b - c``, and one cell per block reduces to exact McNemar
    a = np.array([1, 1, 0, 1, 0, 0, 1, 1, 1], dtype=bool)  # 3 seeds of 3 items
    b = np.array([0, 1, 1, 1, 0, 1, 0, 1, 0], dtype=bool)
    nb, nc = int((a & ~b).sum()), int((~a & b).sum())
    diffs = paired.seed_diffs(a, b, np.repeat(np.arange(3), 3))
    assert diffs == [0, -1, 2]   # per seed: (2-2), (1-2), (3-1)
    assert (nb, nc) == (3, 2)    # A wins items 0, 6, 8; B wins 2, 5
    assert sum(diffs) == nb - nc == 1


@pytest.mark.parametrize(
    "nc_extens, nc_noise, expected",
    [
        (0.00, 0.00, "information"),
        (0.10, 0.24, "information"),  # under the 25% criterion
        (0.10, 0.25, "noise COLLAPSED"),
        (0.90, 0.99, "both COLLAPSED"),
        (0.30, 0.10, "extens COLLAPSED"),
    ],
)
def test_extens_vs_noise_mechanism_labels(
    nc_extens: float, nc_noise: float, expected: str
) -> None:
    assert extens_vs_noise.mechanism(nc_extens, nc_noise) == expected
