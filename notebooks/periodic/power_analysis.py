"""
Power analysis for the periodic induction eval.

Determines how many quiz REPLICATES (re-runs of the same n=9-harmonic quiz with
fresh PeriodicConfig seeds) are needed per condition to detect, at
Bonferroni-corrected alpha, the pairwise differences observed in the
preliminary results:

  1. between model archetypes (decode / cot / moe) within each information
     type, and
  2. between information types (intens / extens / noise_intens) within each
     model.

Design notes
------------
Each condition currently holds exactly one binary outcome per harmonic
k = 1..9 (numeric_count_query_gen yields one count question per period, in
ascending period order, so mark order recovers the harmonic). Difficulty
varies systematically with k, so the data are a stratified binomial with the
harmonic as the stratum -- NOT 9 iid Bernoulli draws. Power therefore scales
with replicates per harmonic, and the planned analysis-time test is the
Cochran-Mantel-Haenszel (CMH) test stratified by harmonic. Adding harmonics
instead would change task difficulty (and blow up lcm(1..n) context length),
confounding the comparison.

Assumed true per-harmonic rates for the simulation shrink the single observed
outcome y_k toward the condition mean p_bar:  p_k = (y_k + c * p_bar) / (1 + c)
with c = 1 (a harmonic failed once is not assumed failed with certainty). A
sensitivity pass with pure condition-mean rates (no per-harmonic structure)
is reported alongside.

Run:
    uv run --with scipy --with statsmodels python notebooks/periodic/power_analysis.py
"""

import re
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import chi2

RESULTS_DIR = Path(__file__).parent / "results"

MODELS = ("decode", "cot", "moe")
INFOS = ("intens", "extens", "noise_intens")
N_HARMONICS = 9

# Simulation parameters. The seed is fixed for reproducibility (repo rule:
# seeded generations everywhere).
SEED = 0
N_SIMS = 10_000
MAX_REPLICATES = 200
SHRINKAGE = 1.0  # c in p_k = (y_k + c * p_bar) / (1 + c)
ALPHA = 0.05
N_TESTS = 18  # 9 archetype contrasts + 9 info-type contrasts
ALPHA_CORRECTED = ALPHA / N_TESTS
POWER_TARGETS = (0.80, 0.90)


def load_outcomes() -> dict[tuple[str, str], np.ndarray]:
    """Per-condition harmonic outcome vectors, index k-1 = harmonic k.

    The result YAMLs carry !!python/object tags, so rather than unsafe-loading
    them we regex the per-mark `score:` lines; marks are serialized in the
    generator's ascending-period order, so position recovers the harmonic.
    """
    outcomes: dict[tuple[str, str], np.ndarray] = {}
    for model in MODELS:
        for info in INFOS:
            text = (RESULTS_DIR / f"{model}_{info}.yaml").read_text()
            scores = re.findall(r"^\s*score:\s*(\S+)", text, re.M)
            assert len(scores) == N_HARMONICS, (model, info, len(scores))
            # score 1 = correct; 0 or null (invalid) = failure.
            outcomes[(model, info)] = np.array(
                [1.0 if s == "1" else 0.0 for s in scores]
            )
    return outcomes


def shrunk_rates(y: np.ndarray, c: float = SHRINKAGE) -> np.ndarray:
    """Per-harmonic rates shrunk toward the condition mean."""
    return (y + c * y.mean()) / (1.0 + c)


def cmh_reject(
    succ_a: np.ndarray, succ_b: np.ndarray, n_per_stratum: int, alpha: float
) -> np.ndarray:
    """Vectorized CMH test (2 x 2 x K strata, continuity-corrected).

    succ_a, succ_b: (n_sims, K) success counts out of n_per_stratum per
    stratum. Returns a boolean (n_sims,) rejection mask.
    """
    n = n_per_stratum
    big_n = 2 * n  # total per stratum
    m1 = succ_a + succ_b  # successes per stratum
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.abs((succ_a - expect).sum(axis=1)) - 0.5
    num = np.clip(num, 0.0, None) ** 2
    denom = var.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        stat = np.where(denom > 0, num / denom, 0.0)
    return stat > chi2.isf(alpha, df=1)


def simulated_power(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    n_reps: int,
    rng: np.random.Generator,
    alpha: float = ALPHA_CORRECTED,
    n_sims: int = N_SIMS,
) -> float:
    """Power of the harmonic-stratified CMH test with n_reps per harmonic."""
    succ_a = rng.binomial(n_reps, rates_a, size=(n_sims, rates_a.size))
    succ_b = rng.binomial(n_reps, rates_b, size=(n_sims, rates_b.size))
    return cmh_reject(succ_a, succ_b, n_reps, alpha).mean()


def replicates_needed(
    rates_a: np.ndarray, rates_b: np.ndarray, rng: np.random.Generator
) -> tuple[dict[float, int | None], dict[int, float]]:
    """Smallest replicate count R reaching each power target.

    Returns ({target: R or None if > MAX_REPLICATES}, {R: power}) scanning
    R = 1, 2, ... and stopping once every target is met.
    """
    needed: dict[float, int | None] = {t: None for t in POWER_TARGETS}
    curve: dict[int, float] = {}
    for n_reps in range(1, MAX_REPLICATES + 1):
        power = simulated_power(rates_a, rates_b, n_reps, rng)
        curve[n_reps] = power
        for target in POWER_TARGETS:
            if needed[target] is None and power >= target:
                needed[target] = n_reps
        if all(needed[t] is not None for t in POWER_TARGETS):
            break
    return needed, curve


def fisher_check(
    rates_a: np.ndarray, rates_b: np.ndarray, n_reps: int, rng: np.random.Generator
) -> float:
    """Power cross-check: pooled (unstratified) two-sided Fisher exact test.

    Memoized on the discrete success counts so the scipy call count stays
    small despite N_SIMS simulations.
    """
    from scipy.stats import fisher_exact

    total = n_reps * N_HARMONICS
    succ_a = rng.binomial(n_reps, rates_a, size=(N_SIMS, rates_a.size)).sum(axis=1)
    succ_b = rng.binomial(n_reps, rates_b, size=(N_SIMS, rates_b.size)).sum(axis=1)
    cache: dict[tuple[int, int], bool] = {}
    rejections = 0
    for ka, kb in zip(succ_a, succ_b):
        key = (int(ka), int(kb))
        if key not in cache:
            _, p = fisher_exact([[ka, total - ka], [kb, total - kb]])
            cache[key] = p < ALPHA_CORRECTED
        rejections += cache[key]
    return rejections / N_SIMS


def equivalence_replicates(
    rates_a: np.ndarray,
    rates_b: np.ndarray,
    delta: float,
    rng: np.random.Generator,
    alpha: float = ALPHA,
    n_sims: int = N_SIMS,
) -> int | None:
    """Smallest R at which TOST shows equivalence with 80% power.

    Assumes the contrast is a TRUE tie: both conditions share per-harmonic
    rates equal to the mean of the two conditions' assumed rates. Equivalence
    is declared when the (1 - 2*alpha) Wald CI for the pooled accuracy
    difference lies inside (-delta, +delta) -- the standard two one-sided
    tests at alpha each. Pooled (unstratified) on purpose: under exact
    equality the stratified and pooled risk differences coincide.
    """
    from scipy.stats import norm

    common = (rates_a + rates_b) / 2.0
    z = norm.isf(alpha)
    for n_reps in range(1, MAX_REPLICATES + 1):
        total = n_reps * N_HARMONICS
        succ_a = rng.binomial(n_reps, common, size=(n_sims, common.size)).sum(axis=1)
        succ_b = rng.binomial(n_reps, common, size=(n_sims, common.size)).sum(axis=1)
        p_a, p_b = succ_a / total, succ_b / total
        diff = p_a - p_b
        se = np.sqrt(p_a * (1 - p_a) / total + p_b * (1 - p_b) / total)
        power = ((diff + z * se < delta) & (diff - z * se > -delta)).mean()
        if power >= 0.80:
            return n_reps
    return None


def omnibus_interaction_power(
    rates: dict[tuple[str, str], np.ndarray], n_reps: int, n_sims: int = 1000
) -> float:
    """Power of the archetype x info-type interaction (logit LR test).

    Fits Bernoulli GLMs with harmonic, model, and info fixed effects, with and
    without the model:info interaction, on simulated data with n_reps
    replicates per harmonic per condition; alpha = 0.05 (single planned
    omnibus test, not part of the 18-test family).
    """
    import statsmodels.api as sm
    from scipy.stats import chi2 as chi2_dist

    rng = np.random.default_rng(SEED + 1)
    # Design matrices are fixed across sims: one weighted row per
    # (model, info, harmonic) cell, n_reps trials each.
    cells = [(m, i, k) for m in MODELS for i in INFOS for k in range(N_HARMONICS)]

    def design(interaction: bool) -> np.ndarray:
        cols = [np.ones(len(cells))]
        for m in MODELS[1:]:
            cols.append(np.array([c[0] == m for c in cells], float))
        for i in INFOS[1:]:
            cols.append(np.array([c[1] == i for c in cells], float))
        for k in range(1, N_HARMONICS):
            cols.append(np.array([c[2] == k for c in cells], float))
        if interaction:
            for m in MODELS[1:]:
                for i in INFOS[1:]:
                    cols.append(
                        np.array([c[0] == m and c[1] == i for c in cells], float)
                    )
        return np.column_stack(cols)

    x_null, x_full = design(False), design(True)
    df_extra = x_full.shape[1] - x_null.shape[1]
    crit = chi2_dist.isf(ALPHA, df=df_extra)
    cell_rates = np.array([rates[(m, i)][k] for m, i, k in cells])

    rejections = 0
    for _ in range(n_sims):
        succ = rng.binomial(n_reps, cell_rates)
        endog = np.column_stack([succ, n_reps - succ])
        try:
            llf_null = sm.GLM(endog, x_null, family=sm.families.Binomial()).fit().llf
            llf_full = sm.GLM(endog, x_full, family=sm.families.Binomial()).fit().llf
        except Exception:  # perfect separation etc. at tiny n_reps
            continue
        if 2 * (llf_full - llf_null) > crit:
            rejections += 1
    return rejections / n_sims


def main() -> None:
    outcomes = load_outcomes()
    rates = {key: shrunk_rates(y) for key, y in outcomes.items()}
    pooled = {key: np.full(N_HARMONICS, y.mean()) for key, y in outcomes.items()}

    print("Observed accuracy (n=9, one question per harmonic k=1..9):")
    for model in MODELS:
        row = "  ".join(
            f"{info}={outcomes[(model, info)].mean():.3f}" for info in INFOS
        )
        print(f"  {model:7s} {row}")
    print()
    print(
        f"Test: CMH stratified by harmonic, two-sided, "
        f"alpha = {ALPHA}/{N_TESTS} = {ALPHA_CORRECTED:.5f} (Bonferroni over "
        f"{N_TESTS} pairwise tests). {N_SIMS} sims per point, seed={SEED}."
    )
    print(
        f"Assumed rates: per-harmonic outcomes shrunk toward condition mean "
        f"(c={SHRINKAGE}); 'pooled' column = sensitivity with condition-mean "
        f"rates only."
    )
    print()

    contrasts: list[tuple[str, tuple[str, str], tuple[str, str]]] = []
    for info in INFOS:
        for m_a, m_b in combinations(MODELS, 2):
            contrasts.append(
                (f"[{info}] {m_a} vs {m_b}", (m_a, info), (m_b, info))
            )
    for model in MODELS:
        for i_a, i_b in combinations(INFOS, 2):
            contrasts.append(
                (f"[{model}] {i_a} vs {i_b}", (model, i_a), (model, i_b))
            )

    header = (
        f"{'contrast':38s} {'rates':13s} {'R(80%)':>7s} {'R(90%)':>7s} "
        f"{'R80 pooled':>11s} {'extra runs':>11s}"
    )
    print(header)
    print("-" * len(header))
    results = []
    for name, key_a, key_b in contrasts:
        rng = np.random.default_rng(SEED)  # same stream per contrast
        needed, _ = replicates_needed(rates[key_a], rates[key_b], rng)
        rng_pooled = np.random.default_rng(SEED)
        needed_pooled, _ = replicates_needed(pooled[key_a], pooled[key_b], rng_pooled)
        results.append((name, key_a, key_b, needed))
        r80, r90 = needed[0.80], needed[0.90]
        fmt = lambda r: f">{MAX_REPLICATES}" if r is None else str(r)
        extra = "n/a" if r80 is None else f"{(r80 - 1) * N_HARMONICS}q"
        obs = (
            f"{outcomes[key_a].mean():.2f} vs {outcomes[key_b].mean():.2f}"
        )
        print(
            f"{name:38s} {obs:13s} {fmt(r80):>7s} {fmt(r90):>7s} "
            f"{fmt(needed_pooled[0.80]):>11s} {extra:>11s}"
        )

    # Fisher cross-check and omnibus at a representative replicate count: the
    # max R(80%) over contrasts that are powerable within the scan cap.
    feasible = [n[0.80] for *_, n in results if n[0.80] is not None]
    r_star = max(feasible)
    print()
    print(f"Recommended replicates per condition (max feasible R at 80%): {r_star}")
    print(
        f"  = {r_star - 1} additional quiz runs ({(r_star - 1) * N_HARMONICS} "
        f"more questions) per condition beyond the existing single run."
    )

    print()
    print(f"Cross-check at R={r_star} (pooled two-sided Fisher exact, same alpha):")
    for name, key_a, key_b, needed in results:
        if needed[0.80] is None:
            continue
        rng = np.random.default_rng(SEED)
        p_fisher = fisher_check(rates[key_a], rates[key_b], r_star, rng)
        print(f"  {name:38s} fisher power = {p_fisher:.3f}")

    # Equivalence (TOST) sizing for the near-tie contrasts, assuming they are
    # TRUE ties: how many replicates to show the difference is within +/-delta
    # at 80% power. Near-tie = pairwise difference test needed R > 20 (or
    # never powered) above.
    near_ties = [
        (name, key_a, key_b)
        for name, key_a, key_b, needed in results
        if needed[0.80] is None or needed[0.80] > 20
    ]
    deltas = (0.10, 0.15, 0.20)
    # The equivalence tests form their own planned family; Bonferroni-correct
    # the per-one-sided-test alpha across it.
    alpha_eq = ALPHA / len(near_ties)
    print()
    print(
        "Equivalence (TOST) sizing for near-tie contrasts, assuming a true "
        f"tie at the contrasts' mean rate (alpha={ALPHA}/{len(near_ties)} = "
        f"{alpha_eq:.4f} per one-sided test, Bonferroni over the "
        f"{len(near_ties)}-test family; 80% power):"
    )
    eq_header = f"{'contrast':38s} " + " ".join(
        f"{f'R(d={d:.2f})':>10s}" for d in deltas
    )
    print(eq_header)
    print("-" * len(eq_header))
    for name, key_a, key_b in near_ties:
        cells = []
        for delta in deltas:
            rng = np.random.default_rng(SEED)
            r_eq = equivalence_replicates(
                rates[key_a], rates[key_b], delta, rng, alpha=alpha_eq
            )
            cells.append(f">{MAX_REPLICATES}" if r_eq is None else str(r_eq))
        print(f"{name:38s} " + " ".join(f"{c:>10s}" for c in cells))

    print()
    p_omni = omnibus_interaction_power(rates, r_star)
    print(
        f"Omnibus archetype x info-type interaction (logit LR test, harmonic "
        f"fixed effects, alpha={ALPHA}) at R={r_star}: power = {p_omni:.3f}"
    )
    p_omni_1 = omnibus_interaction_power(rates, 1)
    print(f"  ... at the current R=1: power = {p_omni_1:.3f}")


if __name__ == "__main__":
    main()
