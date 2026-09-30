"""Pin the analysis' statistical kernels against brute force and reference libraries."""

from itertools import product

import numpy as np
from scipy.stats import binomtest, chi2
from statsmodels.stats.contingency_tables import StratifiedTable

from tests.analysis._trees import (
    N_REPLICATES,
    multiplicity_sim,
    paired_analysis,
    power_analysis,
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
        ours = power_analysis.cmh_stat(succ_a, succ_b, n)
        assert np.allclose(ours, reference, atol=1e-9), (ours, reference)


def landis_gcmh(counts: np.ndarray) -> float:
    """Landis general-association GCMH for one ``(I, J, K)`` table.

    Parameters
    ----------
    counts : np.ndarray
        Counts indexed ``(row, column, stratum)``.

    Returns
    -------
    float
        Generalized CMH statistic with ``(I - 1)(J - 1)`` degrees of freedom.
    """
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
        succ = rng.binomial(n, rng.uniform(0.2, 0.9, size=(1, 3, 1)), size=(1, 3, k))
        counts = np.stack([succ[0], n - succ[0]], axis=1)
        ours = power_analysis.gcmh_stat(succ, n)[0]
        assert np.isclose(ours, landis_gcmh(counts), atol=1e-8), (ours, counts)


def test_gcmh_stat_is_calibrated_under_the_null() -> None:
    """Rejection at ALPHA against chi2 df=N_RUNGS-1 stays near nominal."""
    rng = np.random.default_rng(404)
    n_seeds, k, n_sims = 30, 18, 2000
    rates = rng.uniform(0.3, 0.9, size=(1, 1, k))
    succ = rng.binomial(n_seeds, rates, size=(n_sims, 3, k))
    rejected = power_analysis.gcmh_stat(succ, n_seeds) > chi2.isf(
        power_analysis.ALPHA, df=power_analysis.N_RUNGS - 1
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
    np.testing.assert_allclose(
        power_analysis.mcnemar_exact_p(b, c), expected, atol=1e-12
    )
    assert power_analysis.mcnemar_exact_p(0, 0) == 1.0


def test_trend_stat_matches_the_single_stratum_closed_form() -> None:
    """With one stratum the Mantel trend statistic is ``(N - 1) r**2`` for rung scores 1..N_RUNGS."""
    rng = np.random.default_rng(5)
    n = N_REPLICATES
    shape = (1, power_analysis.N_RUNGS, 1)
    scores = np.arange(1, power_analysis.N_RUNGS + 1)
    for _ in range(20):
        succ = rng.binomial(n, rng.uniform(0.2, 0.9, size=shape), size=shape)
        x = np.repeat(scores, n)
        y = np.concatenate([[1] * int(s) + [0] * (n - int(s)) for s in succ[0, :, 0]])
        r = np.corrcoef(x, y)[0, 1]
        ours = multiplicity_sim.trend_stat(succ, n)[0]
        assert np.isclose(ours, (x.size - 1) * r * r, atol=1e-9), (ours, succ)
