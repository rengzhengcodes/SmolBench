"""Pre-registration power analysis for the Lean CoT-recipe improvement gate.

Before spending ~$300-600 on the paired pilot eval that decides whether the
chain-of-thought SFT arm (``cot-r128``) actually beats the bare-tactic control
(``bare-r128``), this script sizes the study: it picks ``(n_theorems,
n_rollouts)`` that give the McNemar test adequate power against a plausible
effect. The failure it exists to prevent is concrete and already happened --
the ORIGINAL pilot (30 theorems, ~77 pass@1 cells) could not distinguish
17/77 from 15/77, so the null result told us nothing about the recipe.

Statistical design (deliberately honest and simple)
---------------------------------------------------
- **Unit of observation = one (theorem, rung) cell.** The two arms A (control,
  ``bare-r128``) and B (treatment, ``cot-r128``) are evaluated on the SAME
  cells, so the comparison is paired and the natural test is McNemar's on the
  discordant cell pairs (cells where exactly one arm passes). This is the
  counterpart of the periodic/chromatic "replicate, don't change the task"
  principle -- here we add cells (theorems x rungs), never make the task easier.
- **Cell outcome = pass@N.** A cell "passes" for an arm if any of ``N`` rollouts
  verifies. Given a per-rollout success probability ``p`` for that cell,
  ``P(pass@N) = 1 - (1 - p)**N``. Rollouts are correlated ONLY through the
  shared cell probability ``p`` -- conditionally on ``p`` they are independent
  Bernoulli(``p``) draws (no per-rollout latent state, no cross-rollout memory).
  This is the modelling assumption; real rollouts may be more correlated (which
  would shrink the effective N), so the pass@N power here is an upper bound in
  that dimension and the sweep over ``N`` shows how quickly it saturates.
- **Theorem heterogeneity (the thing the flat 30-theorem pilot got wrong).**
  Most theorems in the val set are effectively impossible at these model sizes
  and rungs; a minority are solvable. We model this as a point-mass mixture at
  the THEOREM level: a fraction ``--frac-solvable`` of theorems are "solvable"
  and the rest have per-rollout probability exactly 0 (all four rungs). For a
  solvable theorem, each of its rung cells draws a per-rollout probability from
  a Beta with mean ``m = p1_base / frac_solvable`` and concentration
  ``--beta-conc`` (some solvable cells easy, some hard). The mixture is
  calibrated so the marginal per-cell pass@1 rate equals ``--p1-base``
  (default 0.20, the pilot's 15-17/77): ``frac_solvable * m = p1_base``.
- **Treatment.** Arm B applies the recipe as an additive bump ``--delta`` to the
  per-rollout probability of SOLVABLE cells only:
  ``p_B = clip(p_A + delta, 0, 1)``. Impossible theorems stay impossible (CoT
  does not rescue a theorem the model cannot touch) -- this is why raw
  theorem-count inflation without a solvable fraction would be misleading, and
  why the original pilot's power was so low.
- **Test.** McNemar's EXACT two-sided binomial test on the discordant counts
  ``(b, c)``: under H0 the ``b`` "A-only" successes are ``Binomial(b + c, 0.5)``;
  ``p = min(1, 2 * P(X <= min(b, c)))``. Reject at ``--alpha`` (0.05).
- **Power.** Monte-Carlo (``--sims``, ``--seed``) over the grid of
  ``--n-theorems`` x ``--delta`` x ``--n-rollouts-sweep``, each cell counting
  the fraction of simulated experiments that reject. Per grid point uses its own
  seeded generator (seed derived from ``--seed`` and the point's coordinates),
  so the whole table is reproducible and independent of iteration order -- the
  ``seed=[SEED, ...]`` idiom from ``notebooks/chromatic/power_analysis.py``.

Pure ``numpy`` + stdlib on purpose: neither project venv (`.venv`, `.venv-lean`)
ships scipy, so the exact-binomial McNemar p-value is computed in log space with
``math.lgamma`` rather than ``scipy.stats``. Outputs are printed tables only --
no files are written (nothing to anchor).

Run standalone:

    .venv/bin/python scripts/lean_gate_power.py --sims 200
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# Repo-root anchor (repo convention: __file__-anchored, cwd-independent). This
# script imports nothing from the package today, but the anchor keeps it
# consistent with the other scripts/ entrypoints and future-proofs local
# imports.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np  # noqa: E402

# ---------------------------------------------------------------------------
# Defaults (also the CLI defaults; kept as module constants so tests can import
# and reuse them without re-parsing argv).
# ---------------------------------------------------------------------------
SEED = 1776
N_RUNGS = 4          # context rungs per theorem (the eval's 4 rung ladder)
N_ARMS = 4           # base / real-only-r16 / bare-r128 / cot-r128 (cost only)
P1_BASE = 0.20       # target marginal per-cell pass@1 (pilot's 15-17/77)
FRAC_SOLVABLE = 0.35 # fraction of theorems that are solvable at all
BETA_CONC = 5.0      # Beta concentration (a + b) for solvable-cell probs
ALPHA = 0.05
COST_PER_1K = 3.0    # $ per 1000 generations (placeholder, printed in formula)

N_THEOREMS_SWEEP = (30, 60, 100, 150, 200, 300)
DELTA_SWEEP = (0.03, 0.05, 0.10)
N_ROLLOUTS_SWEEP = (1, 8, 16)
N_ROLLOUTS_HEADLINE = 8  # N used for the RECOMMEND line and the cost estimate
SIMS = 2000
POWER_TARGET = 0.80


# ---------------------------------------------------------------------------
# Core cell math
# ---------------------------------------------------------------------------
def pass_at_n(p: np.ndarray | float, n: int) -> np.ndarray | float:
    """Probability at least one of ``n`` conditionally-independent rollouts
    succeeds, given per-rollout success probability ``p``.

    ``1 - (1 - p)**n``. At ``n == 1`` this is exactly ``p`` (the sweep's N=1
    column reduces to the per-rollout regime -- the old pass@1 pilot).
    """
    return 1.0 - (1.0 - np.asarray(p, dtype=float)) ** n


def _log_binom_cdf_half(n: int, k: int) -> float:
    """log of ``sum_{i=0}^{k} C(n, i) * 0.5**n`` (Binomial(n, 0.5) CDF at k).

    Computed in log space via ``lgamma`` + log-sum-exp so it is stable for the
    large discordant totals (``n`` up to ~4*n_theorems) that would overflow a
    naive ``0.5**n`` in float. ``k`` is assumed in ``[0, n]``.
    """
    ln_half = math.log(0.5)
    ln_nfac = math.lgamma(n + 1)
    # log pmf(i) = lgamma(n+1) - lgamma(i+1) - lgamma(n-i+1) + n*log(0.5)
    log_terms = [
        ln_nfac - math.lgamma(i + 1) - math.lgamma(n - i + 1) + n * ln_half
        for i in range(k + 1)
    ]
    max_lt = max(log_terms)
    return max_lt + math.log(sum(math.exp(lt - max_lt) for lt in log_terms))


def mcnemar_exact_p(b: int, c: int) -> float:
    """McNemar's exact two-sided binomial p-value for discordant counts.

    Under H0 the ``b`` "A-only-passes" cells are ``Binomial(b + c, 0.5)``.
    Two-sided p = ``min(1, 2 * P(X <= min(b, c)))``. With no discordant pairs
    (``b + c == 0``) there is no evidence either way and p = 1.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * math.exp(_log_binom_cdf_half(n, k)))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def simulate_discordant(
    n_theorems: int,
    delta: float,
    n_rollouts: int,
    rng: np.random.Generator,
    *,
    n_rungs: int = N_RUNGS,
    frac_solvable: float = FRAC_SOLVABLE,
    p1_base: float = P1_BASE,
    beta_conc: float = BETA_CONC,
    sims: int = SIMS,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate ``sims`` paired experiments; return discordant counts (b, c).

    Each experiment: draw theorem solvability, per solvable cell a Beta
    per-rollout probability (mean ``p1_base / frac_solvable``), form arm B's
    bumped probability, convert to pass@N cell-success probabilities, draw the
    two arms' cell outcomes (conditionally independent given the cell prob),
    and count discordant cells ``b`` (A pass, B fail) and ``c`` (A fail, B pass)
    over all ``n_theorems * n_rungs`` cells. Returns two ``(sims,)`` arrays.
    """
    m = p1_base / frac_solvable
    if not 0.0 < m <= 1.0:
        raise ValueError(
            f"solvable-cell mean p1 = p1_base/frac_solvable = {m:.3f} must be in "
            f"(0, 1]; lower --p1-base or raise --frac-solvable."
        )
    # Theorem-level solvability point mass (shared across the theorem's rungs).
    solvable = rng.random((sims, n_theorems)) < frac_solvable
    solv_cell = np.repeat(solvable[:, :, None], n_rungs, axis=2)

    # Per-cell control per-rollout probability: Beta for solvable, 0 otherwise.
    a, b_param = m * beta_conc, (1.0 - m) * beta_conc
    p_a = rng.beta(a, b_param, size=(sims, n_theorems, n_rungs))
    p_a = np.where(solv_cell, p_a, 0.0)
    # Treatment: additive bump on solvable cells only, clipped to a probability.
    p_b = np.where(solv_cell, np.clip(p_a + delta, 0.0, 1.0), 0.0)

    # pass@N cell-success probabilities, then the two arms' outcomes.
    s_a = pass_at_n(p_a, n_rollouts)
    s_b = pass_at_n(p_b, n_rollouts)
    pass_a = rng.random(s_a.shape) < s_a
    pass_b = rng.random(s_b.shape) < s_b

    b = np.sum(pass_a & ~pass_b, axis=(1, 2))
    c = np.sum(~pass_a & pass_b, axis=(1, 2))
    return b, c


def _point_rng(seed: int, n_theorems: int, delta: float, n_rollouts: int) -> np.random.Generator:
    """Per-grid-point generator, seeded from the point's coordinates.

    Mirrors chromatic's ``seed=[SEED, ci, si]`` idiom: every grid point draws
    from an independent, reproducible stream, so the table is deterministic and
    invariant to iteration order (and monotonicity comparisons across points
    are honest -- neighbouring points do not share draws).
    """
    return np.random.default_rng([seed, n_theorems, int(round(delta * 1e6)), n_rollouts])


def power_point(
    n_theorems: int,
    delta: float,
    n_rollouts: int,
    *,
    seed: int = SEED,
    n_rungs: int = N_RUNGS,
    frac_solvable: float = FRAC_SOLVABLE,
    p1_base: float = P1_BASE,
    beta_conc: float = BETA_CONC,
    alpha: float = ALPHA,
    sims: int = SIMS,
) -> tuple[float, float]:
    """Monte-Carlo (power, mean discordant count) at one grid point."""
    rng = _point_rng(seed, n_theorems, delta, n_rollouts)
    b, c = simulate_discordant(
        n_theorems,
        delta,
        n_rollouts,
        rng,
        n_rungs=n_rungs,
        frac_solvable=frac_solvable,
        p1_base=p1_base,
        beta_conc=beta_conc,
        sims=sims,
    )
    # Exact p-value per sim, cached on (b+c, min(b,c)): the discrete discordant
    # pair takes few distinct values, so this is far cheaper than sims lgamma
    # sweeps.
    cache: dict[tuple[int, int], float] = {}
    rejections = 0
    for bi, ci in zip(b.tolist(), c.tolist()):
        key = (bi + ci, min(bi, ci))
        p = cache.get(key)
        if p is None:
            p = mcnemar_exact_p(bi, ci)
            cache[key] = p
        rejections += p < alpha
    power = rejections / sims
    mean_disc = float((b + c).mean())
    return power, mean_disc


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def compute_grid(
    n_theorems_sweep,
    delta_sweep,
    n_rollouts,
    *,
    seed,
    n_rungs,
    frac_solvable,
    p1_base,
    beta_conc,
    alpha,
    sims,
) -> dict[tuple[int, float], tuple[float, float]]:
    """(power, mean_disc) for every (n_theorems, delta) at a fixed N."""
    grid: dict[tuple[int, float], tuple[float, float]] = {}
    for nt in n_theorems_sweep:
        for delta in delta_sweep:
            grid[(nt, delta)] = power_point(
                nt,
                delta,
                n_rollouts,
                seed=seed,
                n_rungs=n_rungs,
                frac_solvable=frac_solvable,
                p1_base=p1_base,
                beta_conc=beta_conc,
                alpha=alpha,
                sims=sims,
            )
    return grid


def recommend_n_theorems(
    n_theorems_sweep,
    delta,
    n_rollouts,
    *,
    seed,
    n_rungs,
    frac_solvable,
    p1_base,
    beta_conc,
    alpha,
    sims,
    target=POWER_TARGET,
) -> int | None:
    """Smallest n_theorems reaching ``target`` power at ``delta`` and ``N``.

    Returns ``None`` if no swept theorem count reaches the target.
    """
    for nt in sorted(n_theorems_sweep):
        power, _ = power_point(
            nt,
            delta,
            n_rollouts,
            seed=seed,
            n_rungs=n_rungs,
            frac_solvable=frac_solvable,
            p1_base=p1_base,
            beta_conc=beta_conc,
            alpha=alpha,
            sims=sims,
        )
        if power >= target:
            return nt
    return None


def _print_table(grid, n_theorems_sweep, delta_sweep, n_rollouts) -> None:
    """Print one power table: rows = n_theorems, cols = delta."""
    print(f"pass@{n_rollouts}  (cell value = power; parenthetical = mean discordant pairs)")
    header = f"  {'n_thm':>6s} " + " ".join(f"{f'd={d:.2f}':>15s}" for d in delta_sweep)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for nt in n_theorems_sweep:
        cells = []
        for d in delta_sweep:
            power, disc = grid[(nt, d)]
            cells.append(f"{power:5.3f} ({disc:5.1f})")
        print(f"  {nt:>6d} " + " ".join(f"{c:>15s}" for c in cells))
    print()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    print("Lean CoT-recipe improvement gate -- pre-registration power analysis")
    print("=" * 78)
    m = args.p1_base / args.frac_solvable
    print(
        f"Unit = (theorem, rung) cell; {args.n_rungs} rungs/theorem. Arms A "
        f"(bare-r128) & B (cot-r128) paired on shared cells."
    )
    print(
        f"Test: McNemar exact two-sided binomial on discordant pairs, "
        f"alpha = {args.alpha}. Cell outcome = pass@N."
    )
    print(
        f"Theorem model: frac_solvable = {args.frac_solvable} solvable (rest "
        f"impossible, p=0); solvable-cell per-rollout p ~ Beta(mean = "
        f"p1_base/frac_solvable = {m:.3f}, conc = {args.beta_conc})."
    )
    print(
        f"Calibration: marginal pass@1 = frac_solvable * mean = "
        f"{args.frac_solvable * m:.3f} (target --p1-base = {args.p1_base})."
    )
    print(
        f"Treatment: +delta on solvable cells' per-rollout p. "
        f"{args.sims} sims/point, seed = {args.seed}."
    )
    print()

    for n_rollouts in args.n_rollouts_sweep:
        grid = compute_grid(
            args.n_theorems,
            args.delta,
            n_rollouts,
            seed=args.seed,
            n_rungs=args.n_rungs,
            frac_solvable=args.frac_solvable,
            p1_base=args.p1_base,
            beta_conc=args.beta_conc,
            alpha=args.alpha,
            sims=args.sims,
        )
        _print_table(grid, args.n_theorems, args.delta, n_rollouts)

    # Honest caveat about the pass@N sweep: with the default calibration the
    # solvable cells' per-rollout probability is high (mean p1_base/frac_solvable
    # ~ 0.57), so pass@N saturates toward 1 for BOTH arms as N grows -- solvable
    # cells become concordant and the discordant-pair count (hence McNemar power)
    # can FALL with N. The additive per-rollout delta moves the cell outcome most
    # where pass@N is unsaturated (small N, or a lower --frac-solvable that pushes
    # solvable-cell p down). Read the sweep as: the discriminating regime is where
    # the mean-discordant column is largest, not automatically the largest N.
    print(
        "NOTE: pass@N saturates solvable cells at the default calibration "
        "(mean\n"
        "      solvable p ~ p1_base/frac_solvable); power can fall with N as "
        "both arms\n"
        "      concordantly pass. Discrimination lives where mean-discordant is "
        "largest.\n"
    )

    # RECOMMEND: smallest n_theorems reaching target power at the MIDDLE delta
    # with the headline N (default pass@8). The middle delta is the planning
    # effect size; the flanking deltas are the sensitivity band.
    mid_delta = sorted(args.delta)[len(args.delta) // 2]
    rec = recommend_n_theorems(
        args.n_theorems,
        mid_delta,
        args.n_rollouts,
        seed=args.seed,
        n_rungs=args.n_rungs,
        frac_solvable=args.frac_solvable,
        p1_base=args.p1_base,
        beta_conc=args.beta_conc,
        alpha=args.alpha,
        sims=args.sims,
        target=args.power_target,
    )
    if rec is None:
        print(
            f"RECOMMEND: no swept n_theorems reaches {args.power_target:.0%} power at "
            f"delta = {mid_delta:.2f}, pass@{args.n_rollouts}; widen --n-theorems or "
            f"accept a larger MDE."
        )
        rec_for_cost = max(args.n_theorems)
    else:
        print(
            f"RECOMMEND: n_theorems = {rec} reaches >= {args.power_target:.0%} power at "
            f"delta = {mid_delta:.2f} (middle) with pass@{args.n_rollouts}."
        )
        rec_for_cost = rec

    # Cost: total generations = n_theorems * n_rungs * n_arms * N. Left as a
    # printed formula (the $/1k rate is provider-dependent and volatile).
    gens = rec_for_cost * args.n_rungs * args.n_arms * args.n_rollouts
    print()
    print(
        f"Estimated eval cost at n_theorems = {rec_for_cost}, pass@{args.n_rollouts}, "
        f"{args.n_arms} arms, {args.n_rungs} rungs:"
    )
    print(
        f"  generations = n_theorems * n_rungs * n_arms * N = "
        f"{rec_for_cost} * {args.n_rungs} * {args.n_arms} * {args.n_rollouts} = {gens}"
    )
    print(
        f"  cost = generations / 1000 * cost_per_1k = {gens / 1000:.1f}k * "
        f"${args.cost_per_1k:g} = ${gens / 1000.0 * args.cost_per_1k:,.0f}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Power analysis for the Lean CoT-recipe improvement gate.",
    )
    p.add_argument("--p1-base", type=float, default=P1_BASE,
                   help="target marginal per-cell pass@1 rate (default: pilot's ~0.20)")
    p.add_argument("--frac-solvable", type=float, default=FRAC_SOLVABLE,
                   help="fraction of theorems that are solvable at all (rest p=0)")
    p.add_argument("--beta-conc", type=float, default=BETA_CONC,
                   help="Beta concentration (a+b) for solvable-cell per-rollout probs")
    p.add_argument("--delta", type=float, nargs="+", default=list(DELTA_SWEEP),
                   help="treatment per-rollout probability bumps to sweep")
    p.add_argument("--n-theorems", type=int, nargs="+", default=list(N_THEOREMS_SWEEP),
                   help="theorem counts to sweep (rows of the power table)")
    p.add_argument("--n-rollouts", type=int, default=N_ROLLOUTS_HEADLINE,
                   help="headline N for the RECOMMEND line and cost estimate")
    p.add_argument("--n-rollouts-sweep", type=int, nargs="+", default=list(N_ROLLOUTS_SWEEP),
                   help="pass@N values to print a table for")
    p.add_argument("--n-rungs", type=int, default=N_RUNGS,
                   help="context rungs per theorem (cells per theorem)")
    p.add_argument("--n-arms", type=int, default=N_ARMS,
                   help="arms served (cost only): base/real-only/bare/cot")
    p.add_argument("--alpha", type=float, default=ALPHA, help="McNemar test alpha")
    p.add_argument("--sims", type=int, default=SIMS, help="Monte-Carlo sims per grid point")
    p.add_argument("--seed", type=int, default=SEED, help="base RNG seed")
    p.add_argument("--power-target", type=float, default=POWER_TARGET,
                   help="power threshold for the RECOMMEND line")
    p.add_argument("--cost-per-1k", type=float, default=COST_PER_1K,
                   help="$ per 1000 generations (printed in the cost formula)")
    return p.parse_args(argv)


if __name__ == "__main__":
    main()
