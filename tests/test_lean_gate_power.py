"""Tests for ``scripts/lean_gate_power.py`` -- the CoT-gate power analysis.

The script is pure ``numpy`` + stdlib (neither venv ships scipy), so ``numpy``
is guarded with ``importorskip`` for belt-and-suspenders even though it is
present in both project venvs. Every test uses a small grid and ``--sims`` on
the order of a few hundred so the whole module runs in a few seconds.

The properties pinned here are the ones a mis-edit of the model would break:
- **Determinism**: identical args -> identical printed table / power values
  (the ``seed=[SEED, coords]`` per-point stream must be coordinate-derived, not
  a shared mutable stream).
- **Monotonicity**: power rises with both ``n_theorems`` and ``delta`` (checked
  at ``N=1`` where the additive per-rollout delta moves the cell outcome
  directly and the pass@N saturation that muddies large N is absent).
- **pass@N cell math**: ``N=1`` reduces to the per-rollout probability.
- **Calibration**: zero-delta power is ~ ``alpha`` (the test's type-I rate),
  and the marginal pass@1 equals ``--p1-base`` by construction.
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import lean_gate_power as gp  # noqa: E402


# ---------------------------------------------------------------------------
# pass@N cell math
# ---------------------------------------------------------------------------
def test_pass_at_n_one_is_identity():
    """N=1 pass@N is exactly the per-rollout probability (the old pass@1)."""
    for p in (0.0, 0.13, 0.5, 0.87, 1.0):
        assert gp.pass_at_n(p, 1) == pytest.approx(p)


def test_pass_at_n_formula_and_bounds():
    """1 - (1-p)^N, monotone increasing in N, in [p, 1]."""
    p = 0.2
    assert gp.pass_at_n(p, 2) == pytest.approx(1 - 0.8**2)
    vals = [gp.pass_at_n(p, n) for n in (1, 2, 4, 8, 16)]
    assert vals == sorted(vals)  # non-decreasing in N
    assert vals[0] == pytest.approx(p)
    assert all(p - 1e-12 <= v <= 1.0 for v in vals)
    # Impossible cell stays impossible for any N; certain cell stays certain.
    assert gp.pass_at_n(0.0, 8) == 0.0
    assert gp.pass_at_n(1.0, 8) == pytest.approx(1.0)


def test_pass_at_n_vectorized():
    arr = np.array([0.0, 0.25, 1.0])
    out = gp.pass_at_n(arr, 3)
    assert np.allclose(out, [0.0, 1 - 0.75**3, 1.0])


# ---------------------------------------------------------------------------
# McNemar exact p-value
# ---------------------------------------------------------------------------
def test_mcnemar_no_discordant_is_p_one():
    assert gp.mcnemar_exact_p(0, 0) == 1.0


def test_mcnemar_symmetric_and_bounded():
    """p is symmetric in (b, c) and always in (0, 1]."""
    for b, c in [(3, 7), (10, 2), (25, 25), (40, 3)]:
        p = gp.mcnemar_exact_p(b, c)
        assert gp.mcnemar_exact_p(c, b) == pytest.approx(p)
        assert 0.0 < p <= 1.0


def test_mcnemar_matches_closed_form_small():
    """Cross-check the log-space CDF against a direct binomial sum for small n
    (where 0.5**n does not underflow)."""
    from math import comb

    for b, c in [(1, 4), (2, 8), (0, 6), (3, 5)]:
        n, k = b + c, min(b, c)
        direct = min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) * 0.5**n)
        assert gp.mcnemar_exact_p(b, c) == pytest.approx(direct, rel=1e-9)


def test_mcnemar_large_n_no_overflow():
    """Large discordant totals (where naive 0.5**n underflows) still return a
    finite probability in (0, 1] -- the log-space path is exercised."""
    p = gp.mcnemar_exact_p(600, 500)
    assert 0.0 < p < 1.0
    # A big split (all discordance one way) is strongly significant.
    assert gp.mcnemar_exact_p(1100, 0) < 1e-6


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_power_point_is_deterministic():
    kw = dict(sims=300)
    a = gp.power_point(80, 0.05, 1, **kw)
    b = gp.power_point(80, 0.05, 1, **kw)
    assert a == b


def test_grid_is_deterministic():
    kw = dict(
        seed=gp.SEED, n_rungs=gp.N_RUNGS, frac_solvable=gp.FRAC_SOLVABLE,
        p1_base=gp.P1_BASE, beta_conc=gp.BETA_CONC, alpha=gp.ALPHA, sims=300,
    )
    g1 = gp.compute_grid((40, 80), (0.05, 0.10), 1, **kw)
    g2 = gp.compute_grid((40, 80), (0.05, 0.10), 1, **kw)
    assert g1 == g2


def test_point_seed_is_coordinate_derived():
    """Different grid points draw independent streams (no shared mutable rng):
    two distinct coordinates do not collide onto identical power values by
    construction, and a point is reproducible from its coordinates alone."""
    r1 = gp._point_rng(gp.SEED, 100, 0.05, 8)
    r2 = gp._point_rng(gp.SEED, 100, 0.05, 8)
    r3 = gp._point_rng(gp.SEED, 100, 0.05, 16)
    assert r1.random() == r2.random()          # same coords -> same stream
    assert gp._point_rng(gp.SEED, 100, 0.05, 8).random() != r3.random()


# ---------------------------------------------------------------------------
# Monotonicity (checked at N=1: unsaturated regime, clean signal)
# ---------------------------------------------------------------------------
def test_power_monotone_in_n_theorems():
    """More theorems -> at least as much power (small MC slack allowed)."""
    powers = [gp.power_point(nt, 0.10, 1, sims=800)[0] for nt in (30, 100, 200, 300)]
    for lo, hi in zip(powers, powers[1:]):
        assert hi >= lo - 0.03, powers
    # And the endpoints must show a real, non-marginal increase.
    assert powers[-1] > powers[0] + 0.1, powers


def test_power_monotone_in_delta():
    """Bigger treatment effect -> at least as much power."""
    powers = [gp.power_point(200, d, 1, sims=800)[0] for d in (0.02, 0.05, 0.10)]
    for lo, hi in zip(powers, powers[1:]):
        assert hi >= lo - 0.03, powers
    assert powers[-1] > powers[0] + 0.1, powers


def test_mean_discordant_scales_with_theorems():
    """Discordant-pair count grows with cell count (n_theorems * rungs)."""
    d100 = gp.power_point(100, 0.05, 1, sims=500)[1]
    d300 = gp.power_point(300, 0.05, 1, sims=500)[1]
    assert d300 > d100


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------
def test_zero_delta_power_near_alpha():
    """Under H0 (no treatment effect) the rejection rate must sit near alpha.

    Checked at N=1 where the exact McNemar test has enough discordant pairs to
    approach its nominal level; tolerance 0.03 as specified. (At large N the
    exact test is markedly conservative -- few discordant pairs -- which is a
    feature, not a miscalibration.)
    """
    power, _ = gp.power_point(200, 0.0, 1, sims=1500)
    assert power <= gp.ALPHA + 0.03
    # Not pathologically far below either (the test should still fire ~alpha).
    assert power >= gp.ALPHA - 0.04


def test_marginal_pass1_matches_p1_base():
    """The Beta mixture is calibrated so the marginal per-cell pass@1 equals
    --p1-base: frac_solvable * mean(solvable p) == p1_base. Verified on the
    simulated control-arm probabilities (delta=0, N=1)."""
    rng = np.random.default_rng(0)
    # Re-derive the control per-rollout probabilities the simulator draws.
    sims, nt, rungs = 400, 300, gp.N_RUNGS
    frac, p1 = gp.FRAC_SOLVABLE, gp.P1_BASE
    m = p1 / frac
    solvable = rng.random((sims, nt)) < frac
    solv_cell = np.repeat(solvable[:, :, None], rungs, axis=2)
    a, b = m * gp.BETA_CONC, (1 - m) * gp.BETA_CONC
    p_a = np.where(solv_cell, rng.beta(a, b, size=(sims, nt, rungs)), 0.0)
    # Marginal per-cell pass@1 = mean per-rollout prob over ALL cells.
    assert p_a.mean() == pytest.approx(p1, abs=0.01)


def test_invalid_calibration_raises():
    """p1_base > frac_solvable implies a solvable-cell mean > 1 -> reject."""
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        gp.simulate_discordant(10, 0.05, 1, rng, frac_solvable=0.1, p1_base=0.5, sims=5)


# ---------------------------------------------------------------------------
# CLI / report
# ---------------------------------------------------------------------------
def test_recommend_returns_smallest_passing():
    """recommend_n_theorems returns the smallest swept count above target, or
    None when none qualify. Forced high delta so the smallest count already
    passes; a threshold above the ceiling forces None."""
    kw = dict(
        seed=gp.SEED, n_rungs=gp.N_RUNGS, frac_solvable=gp.FRAC_SOLVABLE,
        p1_base=gp.P1_BASE, beta_conc=gp.BETA_CONC, alpha=gp.ALPHA, sims=600,
    )
    rec = gp.recommend_n_theorems((30, 60, 100, 300), 0.10, 1, target=0.10, **kw)
    assert rec == 30
    none = gp.recommend_n_theorems((30, 60), 0.05, 1, target=0.999, **kw)
    assert none is None


def test_main_runs_and_prints_table(capsys):
    """End-to-end: a tiny sweep prints tables + a RECOMMEND + cost line."""
    gp.main([
        "--sims", "150",
        "--n-theorems", "30", "100",
        "--delta", "0.05", "0.10",
        "--n-rollouts-sweep", "1",
        "--n-rollouts", "1",
    ])
    out = capsys.readouterr().out
    assert "pass@1" in out
    assert "RECOMMEND" in out
    assert "generations = n_theorems * n_rungs * n_arms * N" in out


def test_main_output_is_deterministic(capsys):
    args = ["--sims", "150", "--n-theorems", "30", "60", "--delta", "0.05",
            "--n-rollouts-sweep", "1", "--n-rollouts", "1"]
    gp.main(args)
    first = capsys.readouterr().out
    gp.main(args)
    second = capsys.readouterr().out
    assert first == second
