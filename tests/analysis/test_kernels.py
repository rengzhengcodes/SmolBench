"""Pin the analysis' statistical kernels against brute force and reference libraries."""

from itertools import product
from types import ModuleType

import numpy as np
import pytest
from scipy.stats import binomtest, chi2
from statsmodels.stats.contingency_tables import StratifiedTable

# pylint: disable=unused-import  # fixture names register pytest fixtures
from tests.analysis._trees import paired_analysis, power_analysis  # noqa: F401


def test_signflip_exact_p_matches_enumeration(paired_analysis: ModuleType) -> None:
    """The convolution equals enumerating every one of the 2^n sign assignments."""
    rng = np.random.default_rng(101)
    signs = np.array(list(product((-1, 1), repeat=8)))
    for _ in range(20):
        diffs = rng.integers(-6, 7, size=8)
        totals = np.abs(signs @ diffs)
        expected = np.count_nonzero(totals >= abs(diffs.sum())) / len(signs)
        assert paired_analysis.signflip_exact_p(diffs) == expected


def test_cmh_stat_matches_statsmodels(paired_analysis: ModuleType) -> None:
    """The batched 2x2xK CMH equals statsmodels' continuity-corrected statistic."""
    rng = np.random.default_rng(202)
    for _ in range(10):
        n, k = int(rng.integers(5, 30)), int(rng.integers(2, 8))
        succ_a = rng.binomial(n, rng.uniform(0.2, 0.9), size=k)
        succ_b = rng.binomial(n, rng.uniform(0.2, 0.9), size=k)
        tables = np.array([[succ_a, n - succ_a], [succ_b, n - succ_b]])
        reference = StratifiedTable(tables).test_null_odds(correction=True).statistic
        ours = paired_analysis.cmh_stat(succ_a, succ_b, n)
        assert np.allclose(ours, reference, atol=1e-9), (ours, reference)


def landis_gcmh(counts: np.ndarray) -> float:
    """Landis general-association GCMH for one ``(I, J, K)`` table."""
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


def test_gcmh_stat_matches_landis_form(power_analysis: ModuleType) -> None:
    """The fixed-covariance shortcut equals the general Landis statistic."""
    rng = np.random.default_rng(303)
    for _ in range(10):
        n, k = int(rng.integers(5, 40)), int(rng.integers(2, 20))
        succ = rng.binomial(n, rng.uniform(0.2, 0.9, size=(1, 3, 1)), size=(1, 3, k))
        counts = np.stack([succ[0], n - succ[0]], axis=1)
        ours = power_analysis.gcmh_stat(succ, n)[0]
        assert np.isclose(ours, landis_gcmh(counts), atol=1e-8), (ours, counts)


def test_gcmh_stat_is_calibrated_under_the_null(power_analysis: ModuleType) -> None:
    """Rejection at alpha .05 against chi2 df=2 stays near nominal."""
    rng = np.random.default_rng(404)
    n_seeds, k, n_sims = 30, 18, 2000
    rates = rng.uniform(0.3, 0.9, size=(1, 1, k))
    succ = rng.binomial(n_seeds, rates, size=(n_sims, 3, k))
    rejected = power_analysis.gcmh_stat(succ, n_seeds) > chi2.isf(0.05, df=2)
    assert 0.03 <= rejected.mean() <= 0.07, rejected.mean()


@pytest.mark.parametrize(("b", "c"), ((0, 0), (3, 3), (0, 5), (2, 9), (7, 1)))
def test_mcnemar_exact_p_matches_binomtest(
    paired_analysis: ModuleType, b: int, c: int
) -> None:
    """Exact McNemar equals the two-sided binomial test; no discordant pairs give 1.0."""
    expected = 1.0 if b + c == 0 else binomtest(b, b + c, 0.5).pvalue
    assert np.isclose(paired_analysis.mcnemar_exact_p(b, c), expected, atol=1e-12)
