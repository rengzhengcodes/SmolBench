"""Pin the analysis' statistical kernels against brute force and reference libraries."""

from itertools import product

import numpy as np
import pytest
from scipy.stats import binomtest, chi2
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

from tests.analysis._trees import (
    DEEP_DEPTH,
    N_PRIMARY,
    N_REPLICATES,
    _power_common,
    multiplicity_sim,
    paired_analysis,
    study_design,
)


def test_signflip_exact_p_matches_enumeration() -> None:
    """The convolution equals enumerating every one of the 2^n sign assignments."""
    rng = np.random.default_rng(101)
    signs = np.array(list(product((-1, 1), repeat=8)))
    for _ in range(20):
        diffs = rng.integers(-6, 7, size=8)
        totals = np.abs(signs @ diffs)
        expected = np.count_nonzero(totals >= abs(diffs.sum())) / len(signs)
        assert paired_analysis.signflip_exact_p(diffs) == expected


def test_cmh_stat_matches_statsmodels() -> None:
    """The batched 2x2xK CMH equals statsmodels' continuity-corrected statistic."""
    rng = np.random.default_rng(202)
    for _ in range(10):
        n, k = int(rng.integers(5, 30)), int(rng.integers(2, 8))
        succ_a = rng.binomial(n, rng.uniform(0.2, 0.9), size=k)
        succ_b = rng.binomial(n, rng.uniform(0.2, 0.9), size=k)
        tables = np.array([[succ_a, n - succ_a], [succ_b, n - succ_b]])
        reference = StratifiedTable(tables).test_null_odds(correction=True).statistic
        ours = study_design.cmh_stat(succ_a, succ_b, n)
        assert np.allclose(ours, reference, atol=1e-9), (ours, reference)


def _landis_gcmh(counts: np.ndarray) -> float:
    """Landis general-association GCMH, ``(I - 1)(J - 1)`` df, for one table of counts indexed ``(row, column, stratum)``."""
    n_i, n_j, _ = counts.shape
    t_vec = np.zeros((n_i - 1) * (n_j - 1))
    cov = np.zeros((t_vec.size, t_vec.size))
    for table in np.moveaxis(counts, 2, 0):
        total = table.sum()
        p, q = table.sum(axis=1) / total, table.sum(axis=0) / total
        expected = total * np.outer(p, q)
        t_vec += (table - expected)[:-1, :-1].ravel()
        v_rows = (np.diag(p) - np.outer(p, p))[:-1, :-1]
        v_cols = (np.diag(q) - np.outer(q, q))[:-1, :-1]
        cov += total**2 / (total - 1) * np.kron(v_rows, v_cols)
    return float(t_vec @ np.linalg.solve(cov, t_vec))


def test_gcmh_stat_matches_landis_form() -> None:
    """The fixed-covariance shortcut equals the general Landis statistic."""
    rng = np.random.default_rng(303)
    for _ in range(10):
        n, k = int(rng.integers(5, 40)), int(rng.integers(2, 20))
        shape = (1, study_design.N_RUNGS, 1)
        succ = rng.binomial(n, rng.uniform(0.2, 0.9, size=shape), size=shape[:2] + (k,))
        counts = np.stack([succ[0], n - succ[0]], axis=1)
        ours = study_design.gcmh_stat(succ, n)[0]
        assert np.isclose(ours, _landis_gcmh(counts), atol=1e-8), (ours, counts)


def test_gcmh_stat_is_calibrated_under_the_null() -> None:
    """Rejection at ALPHA against chi2 df=N_RUNGS-1 stays near nominal."""
    rng = np.random.default_rng(404)
    n_seeds, k, n_sims = 30, 18, 2000
    rates = rng.uniform(0.3, 0.9, size=(1, 1, k))
    succ = rng.binomial(n_seeds, rates, size=(n_sims, study_design.N_RUNGS, k))
    rejected = study_design.gcmh_stat(succ, n_seeds) > chi2.isf(
        _power_common.ALPHA, df=study_design.N_RUNGS - 1
    )
    assert 0.03 <= rejected.mean() <= 0.07, rejected.mean()


def test_mcnemar_exact_p_matches_binomtest() -> None:
    """Batched exact McNemar equals scipy's two-sided binomial test; no discordant pairs give 1.0."""
    rng = np.random.default_rng(3)
    b = np.append(rng.integers(0, 40, 300), [0, 4, 0])
    c = np.append(rng.integers(0, 40, 300), [0, 4, 5])
    expected = [
        1.0 if n == 0 else binomtest(int(x), int(n), 0.5).pvalue
        for x, n in zip(b, b + c)
    ]
    np.testing.assert_allclose(study_design.mcnemar_exact_p(b, c), expected, atol=1e-12)
    assert study_design.mcnemar_exact_p(0, 0) == 1.0


def test_mcnemar_is_defined_once() -> None:
    """One implementation serves every call site."""
    assert paired_analysis.mcnemar_exact_p is study_design.mcnemar_exact_p
    assert multiplicity_sim.mcnemar_exact_p is study_design.mcnemar_exact_p


def test_trend_stat_matches_the_single_stratum_closed_form() -> None:
    """With one stratum the Mantel trend statistic is ``(N - 1) r**2`` for rung scores 1..N_RUNGS."""
    rng = np.random.default_rng(5)
    n = N_REPLICATES
    shape = (1, study_design.N_RUNGS, 1)
    scores = np.arange(1, study_design.N_RUNGS + 1)
    for _ in range(20):
        succ = rng.binomial(n, rng.uniform(0.2, 0.9, size=shape), size=shape)
        x = np.repeat(scores, n)
        y = np.concatenate([[1] * int(s) + [0] * (n - int(s)) for s in succ[0, :, 0]])
        r = np.corrcoef(x, y)[0, 1]
        ours = multiplicity_sim.trend_stat(succ, n)[0]
        assert np.isclose(ours, (x.size - 1) * r * r, atol=1e-9), (ours, succ)


def test_apply_corrections_matches_statsmodels() -> None:
    """Batched masks agree with statsmodels row by row away from exact ties."""
    alpha = _power_common.ALPHA
    rng = np.random.default_rng(7)
    pv = np.vstack(
        [
            rng.uniform(0, 1, size=(40, 6)),
            rng.uniform(0, 0.02, size=(10, 6)),
            np.array([[0.001, 0.011, 0.021, 0.031, 0.041, 0.9]]),
        ]
    )
    got = _power_common.apply_corrections(pv, alpha)
    methods = {
        "Bonferroni": "bonferroni",
        "Holm": "holm",
        "Hochberg": "simes-hochberg",
        "BH": "fdr_bh",
    }
    for name, method in methods.items():
        for row, mask in zip(pv, got[name]):
            expected = multipletests(row, alpha=alpha, method=method)[0]
            assert list(mask) == list(expected), (name, row.tolist())


def test_apply_corrections_share_one_inclusive_boundary() -> None:
    """Every procedure rejects a p-value sitting exactly on its threshold."""
    alpha = _power_common.ALPHA
    m = 4
    pv = np.array(
        [
            [alpha / m, alpha / (m - 1), 0.5, 0.9],
            [alpha * 1 / m, alpha * 2 / m, alpha * 3 / m, alpha * 4 / m],
        ]
    )
    got = _power_common.apply_corrections(pv, alpha)
    assert list(got["Bonferroni"][0]) == [True, False, False, False]
    assert list(got["Holm"][0]) == [True, True, False, False]
    assert list(got["Hochberg"][0]) == [True, True, False, False]
    assert list(got["BH"][1]) == [True, True, True, True]


@pytest.mark.parametrize("method", ("Holm", "Hochberg", "BH"))
def test_rejection_sets_do_not_depend_on_contrast_build_order(method: str) -> None:
    """Tie ordering cannot change `method`'s rank-monotone rejection decisions."""
    alpha = _power_common.ALPHA
    rng = np.random.default_rng(7)
    tie_rng = np.random.default_rng(20260905)
    # Sign-flip floors at study and deep depth, ALPHA, the primary share, and tie-prone values.
    pool = np.array(
        [
            2 / 2**N_REPLICATES,
            2 / 2**DEEP_DEPTH,
            1.0,
            alpha,
            alpha / N_PRIMARY,
            1e-8,
            0.5,
            0.02,
        ]
    )
    for i in range(60):
        m = int(tie_rng.integers(2, 80))
        pvals = (
            np.round(tie_rng.random(m), 2)
            if i % 3 == 0
            else tie_rng.choice(pool, size=m)
        )
        perm = rng.permutation(pvals.size)
        base = paired_analysis.rejections(pvals, method, alpha)
        permuted = paired_analysis.rejections(pvals[perm], method, alpha)
        assert np.array_equal(permuted, base[perm]), (pvals, perm)
