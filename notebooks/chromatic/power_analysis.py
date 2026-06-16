"""
Power analysis for the chromatic induction eval (quiz-level / conservative).

Counterpart to ``notebooks/periodic/power_analysis.py``, but the chromatic task
has a different statistical structure that forces a different design.

Design notes
------------
Each chromatic quiz is ~120 True/False direct-succession questions
("Has color A handed the sceptre to color B?"): ~60 real consecutive pairs
(answer True) plus ~60 randomly-sampled non-pairs (answer False). Unlike the
periodic harmonics, the questions are NOT one-per-difficulty-stratum -- they all
share a single context, and the preliminary data show the responses are
dominated by a near-global response bias (e.g. decode under extens answers
~always-False: 1.7% correct on True pairs, 100% on False pairs). So the ~120
questions in a quiz are far from independent, and the natural stratum is answer
polarity (True/False), not difficulty.

Per the user's choice, the analysis is therefore **quiz-level / conservative**:
the unit of observation is one fresh-seed quiz, summarised to per-quiz rates
(p_true, p_false, p_overall); a "replicate" re-runs the quiz under a new
``ChromaticIntervalsConfig`` seed (same n / intervals / colors), exactly the
periodic "replicate, don't change the task" principle. Two conditions are
compared with a quiz-level two-sample Welch t-test across R replicate quizzes
(primary outcome = p_overall; behavioural breakdown on p_true = discrimination
and p_false = bias). The family is the same 18 pairwise contrasts as periodic
(9 archetype + 9 info-type), Bonferroni alpha = 0.05/18.

The required R is driven by the **between-quiz variance** (seed-to-seed), which
cannot be estimated from a single run. The script therefore:

  1. sweeps the between-quiz SD (sigma_between, on the accuracy scale) and prints
     required R at each level -- the sensitivity axis;
  2. anchors that sweep with git history -- same-seed reruns vary by only
     ~0.01-0.03 (pure inference noise) while a documented seed change
     (commit 5f8df82, "strange results given new seed") swung overall accuracy
     by 0.10-0.16 and per-polarity discrimination by up to 0.5 (confounded with
     model-version drift) -- strong evidence the between-quiz term is large; and
     re-runs the analysis under two historical model trios as alternative
     effect-size scenarios;
  3. auto-finalises after pilots -- with >=2 replicate quizzes per condition it
     estimates sigma_between empirically and reports a firm R; with 1 run it
     reports the sweep + scenarios + a pilot recommendation.

Run (ephemeral env, leaves .venv untouched):
    uv run --no-project --with numpy --with scipy python notebooks/chromatic/power_analysis.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import expit, logit

RESULTS_DIR = Path(__file__).parent / "results"

MODELS = ("decode", "cot", "moe")
INFOS = ("intens", "extens", "noise_intens")

# Simulation parameters. SEED is fixed for reproducibility (repo rule: seeded
# generations everywhere); run the script twice -> identical output.
SEED = 0
N_SIMS = 8_000          # sims per power estimate in the R scans
N_SIMS_OMNI = 20_000    # sims for the (vectorised) omnibus / reported points
MAX_REPLICATES = 80
ALPHA = 0.05
N_TESTS = 18            # 9 archetype contrasts + 9 info-type contrasts
ALPHA_CORRECTED = ALPHA / N_TESTS
POWER_TARGETS = (0.80, 0.90)

# Between-quiz SD sweep, expressed on the probability (accuracy) scale at
# p = 0.5. Applied as a logit-scale random effect tau = 4 * sigma per polarity
# (dp/d eta = 0.25 at p = 0.5), which keeps simulated rates inside (0, 1) even
# for the boundary conditions. The realised SD shrinks toward the 0/1 ends.
SIGMA_SWEEP = (0.00, 0.03, 0.06, 0.10, 0.15)
REP_SIGMA = 0.06        # representative level for the breakdown / equivalence / omnibus
DELTAS = (0.10, 0.15, 0.20)  # equivalence margins (accuracy points)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Quiz:
    """Per-polarity correct/total counts for one quiz run."""

    k_true: int
    n_true: int
    k_false: int
    n_false: int

    @property
    def p_true(self) -> float:
        return self.k_true / self.n_true

    @property
    def p_false(self) -> float:
        return self.k_false / self.n_false

    @property
    def p_overall(self) -> float:
        return (self.k_true + self.k_false) / (self.n_true + self.n_false)


_MARK_SPLIT = re.compile(r"!!python/object:smolbench\.evals\.Mark")
_ANSWER_RE = re.compile(r"^\s*answer:\s*(true|false)\b", re.I | re.M)
_SCORE_RE = re.compile(r"^\s*score:\s*(\S+?)\s*$", re.M)


def parse_quiz(text: str) -> Quiz:
    """Recover per-polarity counts from one result YAML's text.

    The files carry ``!!python/object`` tags, so rather than unsafe-loading we
    split on the per-mark tag and, within each mark, read the first ``answer:``
    (the ground-truth polarity, the first field) and the last ``score:`` (the
    1/0 correctness, the last field -- any ``score:`` inside the reasoning/
    response text appears earlier and is ignored).
    """
    k_true = n_true = k_false = n_false = 0
    for chunk in _MARK_SPLIT.split(text)[1:]:
        ans = _ANSWER_RE.search(chunk)
        scores = _SCORE_RE.findall(chunk)
        if ans is None or not scores:
            continue
        correct = scores[-1].strip() == "1"
        if ans.group(1).lower() == "true":
            n_true += 1
            k_true += correct
        else:
            n_false += 1
            k_false += correct
    if n_true == 0 or n_false == 0:
        raise ValueError(f"parsed {n_true} True / {n_false} False marks (expected ~60/60)")
    return Quiz(k_true, n_true, k_false, n_false)


def load_condition(model: str, info: str) -> list[Quiz]:
    """All replicate quizzes for a condition.

    Supports the current flat ``{model}_{info}.yaml`` layout and the
    forward-compatible per-replicate ``{model}_{info}/rep_*.yaml`` layout (so the
    same script finalises the firm R once pilots are run).
    """
    nested_dir = RESULTS_DIR / f"{model}_{info}"
    if nested_dir.is_dir():
        paths = sorted(nested_dir.glob("rep_*.yaml"))
    else:
        flat = RESULTS_DIR / f"{model}_{info}.yaml"
        paths = [flat] if flat.exists() else []
    return [parse_quiz(p.read_text()) for p in paths]


# ---------------------------------------------------------------------------
# Assumed rates
# ---------------------------------------------------------------------------

def jeffreys(k: int, n: int) -> float:
    """Jeffreys posterior-mean rate (k + 1/2)/(n + 1).

    Keeps assumed rates off the 0/1 boundary so the logit random effect and the
    within-quiz binomial are both non-degenerate (mirrors periodic's shrinkage).
    """
    return (k + 0.5) / (n + 1.0)


@dataclass(frozen=True)
class Rates:
    """Assumed per-polarity rates + sizes for one condition (pooled over reps)."""

    mu_true: float
    mu_false: float
    n_true: int
    n_false: int


def pooled_rates(quizzes: list[Quiz]) -> Rates:
    kt = sum(q.k_true for q in quizzes)
    nt = sum(q.n_true for q in quizzes)
    kf = sum(q.k_false for q in quizzes)
    nf = sum(q.n_false for q in quizzes)
    return Rates(jeffreys(kt, nt), jeffreys(kf, nf), quizzes[0].n_true, quizzes[0].n_false)


def counts_to_rates(kt: int, nt: int, kf: int, nf: int) -> Rates:
    return Rates(jeffreys(kt, nt), jeffreys(kf, nf), nt, nf)


# ---------------------------------------------------------------------------
# Quiz-level simulation + tests
# ---------------------------------------------------------------------------

def simulate(r: Rates, sigma: float, reps: int, rng: np.random.Generator, n_sims: int) -> dict[str, np.ndarray]:
    """Simulate ``reps`` per-quiz rates for a condition, shape (n_sims, reps).

    Between-quiz variability is a logit-scale Normal random effect (tau =
    4*sigma) drawn independently per polarity; within-quiz variability is the
    binomial draw of correct answers. Returns p_overall / p_true / p_false.
    """
    tau = 4.0 * sigma
    qt = expit(logit(r.mu_true) + tau * rng.standard_normal((n_sims, reps)))
    qf = expit(logit(r.mu_false) + tau * rng.standard_normal((n_sims, reps)))
    kt = rng.binomial(r.n_true, qt)
    kf = rng.binomial(r.n_false, qf)
    return {
        "overall": (kt + kf) / (r.n_true + r.n_false),
        "true": kt / r.n_true,
        "false": kf / r.n_false,
    }


def _welch(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Welch two-sample statistic per sim. Returns (mean_diff, se, df)."""
    reps = a.shape[1]
    md = a.mean(1) - b.mean(1)
    va, vb = a.var(1, ddof=1), b.var(1, ddof=1)
    se2 = va / reps + vb / reps
    with np.errstate(divide="ignore", invalid="ignore"):
        df = se2 ** 2 / ((va / reps) ** 2 / (reps - 1) + (vb / reps) ** 2 / (reps - 1))
    return md, np.sqrt(se2), df


def welch_power(a: np.ndarray, b: np.ndarray, alpha: float) -> float:
    """Power of the two-sided Welch t-test at ``alpha`` over the sims."""
    md, se, df = _welch(a, b)
    safe = se > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(safe, md / np.where(safe, se, 1.0), 0.0)
        pval = 2.0 * stats.t.sf(np.abs(t), np.where(safe, df, 1.0))
    # Degenerate (zero within-condition variance): reject iff the means differ.
    reject = np.where(safe, pval < alpha, np.abs(md) > 1e-9)
    return float(reject.mean())


def power_at(ra: Rates, rb: Rates, sigma: float, reps: int, stat: str,
             rng: np.random.Generator, alpha: float = ALPHA_CORRECTED,
             n_sims: int = N_SIMS) -> float:
    a = simulate(ra, sigma, reps, rng, n_sims)[stat]
    b = simulate(rb, sigma, reps, rng, n_sims)[stat]
    return welch_power(a, b, alpha)


def replicates_needed(ra: Rates, rb: Rates, sigma: float, stat: str, seed,
                      target: float = 0.80, alpha: float = ALPHA_CORRECTED) -> int | None:
    """Smallest R in [2, MAX] reaching ``target`` power (None if > MAX).

    Power is monotone in R in expectation; a binary search keeps the near-tie
    contrasts (which run to MAX) cheap. A single rng per call -> reproducible.
    """
    rng = np.random.default_rng(seed)
    if power_at(ra, rb, sigma, MAX_REPLICATES, stat, rng, alpha) < target:
        return None
    lo, hi = 2, MAX_REPLICATES
    while lo < hi:
        mid = (lo + hi) // 2
        if power_at(ra, rb, sigma, mid, stat, rng, alpha) >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def equivalence_needed(ra: Rates, rb: Rates, delta: float, sigma: float, seed,
                       alpha_eq: float, stat: str = "overall") -> int | None:
    """Smallest R at which TOST shows equivalence within +/-delta at 80% power.

    Assumes a true tie: both conditions share the per-polarity mean of the two.
    Equivalence is declared when the (1 - 2*alpha_eq) Welch CI for the mean
    difference lies inside (-delta, +delta).
    """
    common = Rates((ra.mu_true + rb.mu_true) / 2, (ra.mu_false + rb.mu_false) / 2,
                   ra.n_true, ra.n_false)
    rng = np.random.default_rng(seed)
    for reps in range(2, MAX_REPLICATES + 1):
        a = simulate(common, sigma, reps, rng, N_SIMS)[stat]
        b = simulate(common, sigma, reps, rng, N_SIMS)[stat]
        md, se, df = _welch(a, b)
        with np.errstate(invalid="ignore"):
            tcrit = stats.t.isf(alpha_eq, df)
            declared = (md + tcrit * se < delta) & (md - tcrit * se > -delta)
        if np.nanmean(declared) >= 0.80:
            return reps
    return None


def omnibus_power(rates: dict[tuple[str, str], Rates], sigma: float, reps: int,
                  seed, alpha: float = ALPHA, n_sims: int = N_SIMS_OMNI) -> float:
    """Power of the archetype x info-type interaction (quiz-level two-way ANOVA).

    Balanced 3x3 design, ``reps`` quizzes per cell; the interaction F (4 df) is
    computed vectorised across sims. alpha = 0.05 (single planned omnibus test).
    """
    rng = np.random.default_rng(seed)
    cells = [(m, i) for m in MODELS for i in INFOS]
    y = np.stack([simulate(rates[c], sigma, reps, rng, n_sims)["overall"] for c in cells], axis=1)
    cell_mean = y.mean(2)                                   # (n_sims, 9)
    cm = cell_mean.reshape(n_sims, len(MODELS), len(INFOS))
    row = cm.mean(2, keepdims=True)
    col = cm.mean(1, keepdims=True)
    grand = cm.mean((1, 2), keepdims=True)
    inter = cm - row - col + grand
    ss_inter = reps * (inter ** 2).sum((1, 2))
    ss_err = ((y - cell_mean[:, :, None]) ** 2).sum((1, 2))
    df_err = len(cells) * (reps - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        f = (ss_inter / 4.0) / (ss_err / df_err)
        reject = stats.f.sf(f, 4, df_err) < alpha
    return float(np.mean(reject))


def min_detectable_effect(sigma: float, reps: int, seed, base: float = 0.60,
                          target: float = 0.80, alpha: float = ALPHA_CORRECTED) -> float | None:
    """Smallest overall-accuracy gap detectable at ``target`` power.

    Reference operating point: two conditions symmetric about ``base`` with no
    response bias (p_true = p_false = overall), n = 120. Binary search on the gap.
    """
    n = 120
    rng = np.random.default_rng(seed)

    def powered(delta: float) -> bool:
        ra = Rates(base + delta / 2, base + delta / 2, n // 2, n // 2)
        rb = Rates(base - delta / 2, base - delta / 2, n // 2, n // 2)
        return power_at(ra, rb, sigma, reps, "overall", rng, alpha) >= target

    if not powered(0.50):
        return None
    lo, hi = 0.0, 0.50
    for _ in range(14):  # ~0.5/2^14 resolution
        mid = (lo + hi) / 2
        if powered(mid):
            hi = mid
        else:
            lo = mid
    return hi


# ---------------------------------------------------------------------------
# Historical effect-size scenarios (documented, commit-sourced; n_true=n_false=60)
# ---------------------------------------------------------------------------
# (k_true, n_true, k_false, n_false) per condition, recovered via `git show`.
HISTORY: dict[str, dict[tuple[str, str], tuple[int, int, int, int]]] = {
    "ec2-draft  (8d540c9: gemma-3-27b-it / devstral-small / qwen3-30b-a3b-instruct)": {
        ("decode", "intens"): (27, 60, 51, 60),
        ("decode", "extens"): (15, 60, 55, 60),
        ("decode", "noise_intens"): (1, 60, 60, 60),
        ("cot", "intens"): (37, 60, 49, 60),
        ("cot", "extens"): (54, 60, 25, 60),
        ("cot", "noise_intens"): (45, 60, 28, 60),
        ("moe", "intens"): (34, 60, 47, 60),
        ("moe", "extens"): (19, 60, 55, 60),
        ("moe", "noise_intens"): (33, 60, 40, 60),
    },
    "new-seed   (5f8df82: r1-distill-qwen-32b / devstral-small-2505 / qwen3-30b-a3b)": {
        ("decode", "intens"): (50, 60, 42, 60),
        ("decode", "extens"): (45, 60, 44, 60),
        ("decode", "noise_intens"): (37, 60, 37, 60),
        ("cot", "intens"): (59, 60, 60, 60),
        ("cot", "extens"): (37, 60, 55, 60),
        ("cot", "noise_intens"): (44, 60, 58, 60),
        ("moe", "intens"): (32, 60, 47, 60),
        ("moe", "extens"): (16, 60, 56, 60),
        ("moe", "noise_intens"): (31, 60, 44, 60),
    },
}


# ---------------------------------------------------------------------------
# Contrasts
# ---------------------------------------------------------------------------

def build_contrasts() -> list[tuple[str, tuple[str, str], tuple[str, str]]]:
    """The 18 pairwise contrasts: 9 archetype (within info) + 9 info (within model)."""
    contrasts = []
    for info in INFOS:
        for m_a, m_b in combinations(MODELS, 2):
            contrasts.append((f"[{info}] {m_a} vs {m_b}", (m_a, info), (m_b, info)))
    for model in MODELS:
        for i_a, i_b in combinations(INFOS, 2):
            contrasts.append((f"[{model}] {i_a} vs {i_b}", (model, i_a), (model, i_b)))
    return contrasts


def fmt_r(r: int | None) -> str:
    return f">{MAX_REPLICATES}" if r is None else str(r)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def main() -> None:
    quizzes = {(m, i): load_condition(m, i) for m in MODELS for i in INFOS}
    obs = {key: qs[0] for key, qs in quizzes.items()}  # representative observed quiz
    rates = {key: pooled_rates(qs) for key, qs in quizzes.items()}
    n_reps = min(len(qs) for qs in quizzes.values())
    contrasts = build_contrasts()

    print("Chromatic induction eval -- quiz-level power analysis")
    print("=" * 78)
    print(f"Replicate quizzes per condition currently available: {n_reps}")
    print("Observed (current trio: olmo-3.1-instruct / olmo-3.1-think / granite-4.0-h-small)")
    print(f"  {'condition':22s} {'overall':>8s} {'p_true(disc)':>13s} {'p_false(bias)':>14s}")
    for m in MODELS:
        for i in INFOS:
            q = obs[(m, i)]
            print(f"  {m + '/' + i:22s} {q.p_overall:8.3f} {q.p_true:13.3f} {q.p_false:14.3f}")
    print()
    print("Overall accuracy is BIAS-CONFOUNDED: e.g. decode/extens sits at chance")
    print("(.508) but is ~always-False (p_true=.017, p_false=1.0). decode & cot lean")
    print("False; moe leans True. Polarity is the stratum; the ~120 questions per quiz")
    print("are bias-correlated, so the unit of observation is the QUIZ.")
    print()
    print(f"Test: quiz-level two-sample Welch t across R replicate quizzes, two-sided,")
    print(f"alpha = {ALPHA}/{N_TESTS} = {ALPHA_CORRECTED:.5f} (Bonferroni over {N_TESTS} contrasts).")
    print(f"{N_SIMS} sims/point, seed={SEED}. R is the replicate quizzes per condition")
    print("(each ~120 questions); a quiz-level test needs R >= 2.")
    print()

    if n_reps < 2:
        single_run_report(rates, obs, contrasts)
    else:
        empirical_report(quizzes, rates, obs, contrasts, n_reps)


def single_run_report(rates, obs, contrasts) -> None:
    print("MODE: single preliminary run per condition.")
    print("=> between-quiz variance is NOT estimable; R is reported as a function of")
    print("   the assumed between-quiz SD (sigma_between), to be pinned by pilots.")
    print()

    # --- Section 1: primary R(80%) across the sigma_between sweep -------------
    print("[1] Required R for 80% power -- primary outcome = overall accuracy, current trio")
    print(f"    sigma_between sweep (accuracy-scale SD at p=0.5); '>{MAX_REPLICATES}' = near-tie -> see [3]")
    head = f"    {'contrast':26s} {'gap':>5s} " + " ".join(f"s={s:<4.2f}" for s in SIGMA_SWEEP)
    print(head)
    print("    " + "-" * (len(head) - 4))
    sec1: dict[int, list[int | None]] = {}
    for ci, (name, ka, kb) in enumerate(contrasts):
        gap = abs(obs[ka].p_overall - obs[kb].p_overall)
        row = [replicates_needed(rates[ka], rates[kb], sigma, "overall", seed=[SEED, ci, si])
               for si, sigma in enumerate(SIGMA_SWEEP)]
        sec1[ci] = row
        print(f"    {name:26s} {gap:5.2f} " + " ".join(f"{fmt_r(r):>6s}" for r in row))
    print()

    # --- Section 2: behavioural breakdown (discrimination vs bias) ------------
    print(f"[2] Behavioural breakdown at sigma_between={REP_SIGMA}: R(80%) for p_true")
    print("    (discrimination) and p_false (bias). Reveals differences that an overall")
    print("    accuracy tie hides (a flat overall gap with opposite bias still differs).")
    print(f"    {'contrast':26s} {'d_disc':>7s} {'R_disc':>7s} {'d_bias':>7s} {'R_bias':>7s}")
    print("    " + "-" * 58)
    sec2: dict[int, tuple[int | None, int | None]] = {}
    for ci, (name, ka, kb) in enumerate(contrasts):
        d_disc = abs(obs[ka].p_true - obs[kb].p_true)
        d_bias = abs(obs[ka].p_false - obs[kb].p_false)
        r_disc = replicates_needed(rates[ka], rates[kb], REP_SIGMA, "true", seed=[SEED, ci, 100])
        r_bias = replicates_needed(rates[ka], rates[kb], REP_SIGMA, "false", seed=[SEED, ci, 200])
        sec2[ci] = (r_disc, r_bias)
        print(f"    {name:26s} {d_disc:7.2f} {fmt_r(r_disc):>7s} {d_bias:7.2f} {fmt_r(r_bias):>7s}")
    print("    (discrimination and bias are two separate 18-contrast families, each at")
    print(f"     alpha={ALPHA_CORRECTED:.5f}; overall accuracy in [1] is the primary family.)")
    print()

    # --- Section 3: equivalence (TOST) for near-ties -------------------------
    rep_idx = SIGMA_SWEEP.index(REP_SIGMA)
    near_ties = [ci for ci in range(len(contrasts)) if sec1[ci][rep_idx] is None]
    alpha_eq = ALPHA / max(1, len(near_ties))
    print(f"[3] Aggregate-accuracy equivalence (TOST) for the {len(near_ties)} overall near-ties")
    print(f"    at sigma_between={REP_SIGMA}, assuming a true tie; family Bonferroni alpha = "
          f"{ALPHA}/{len(near_ties)} = {alpha_eq:.4f}; 80% power.")
    print(f"    {'contrast':26s} " + " ".join(f"R(d={d:.2f})" for d in DELTAS) + "  behavioural status")
    print("    " + "-" * 76)
    n_artifact = 0
    for ci in near_ties:
        name, ka, kb = contrasts[ci]
        cells = []
        for di, delta in enumerate(DELTAS):
            r = equivalence_needed(rates[ka], rates[kb], delta, REP_SIGMA,
                                   seed=[SEED, ci, 300 + di], alpha_eq=alpha_eq)
            cells.append(f"{fmt_r(r):>8s}")
        r_disc, r_bias = sec2[ci]
        artifact = (r_disc is not None) or (r_bias is not None)
        n_artifact += artifact
        status = "ARTIFACT: differs on a component [2]" if artifact else "true tie on both components"
        print(f"    {name:26s} " + " ".join(cells) + f"  {status}")
    print(f"    => {n_artifact}/{len(near_ties)} aggregate ties are aggregation ARTIFACTS: equal on")
    print("       overall accuracy but differing on discrimination and/or bias (see [2]). An")
    print("       overall-accuracy equivalence claim would mislead about behaviour for these.")
    print()

    # --- Section 4: omnibus interaction --------------------------------------
    print(f"[4] Omnibus archetype x info-type interaction (quiz-level two-way ANOVA, "
          f"alpha={ALPHA}):")
    for reps in (3, 5, 10, 20):
        p = omnibus_power(rates, REP_SIGMA, reps, seed=[SEED, 7, reps])
        print(f"    R={reps:2d} quizzes/cell, sigma_between={REP_SIGMA}: power = {p:.3f}")
    print()

    # --- Section 5: history effect-size scenarios ----------------------------
    print(f"[5] History effect-size scenarios at sigma_between={REP_SIGMA} (max R(80%) over the")
    print("    18 contrasts; how the answer shifts if the true effects look like another trio):")
    for label, table in HISTORY.items():
        hrates = {key: counts_to_rates(*table[key]) for key in table}
        rs = [replicates_needed(hrates[ka], hrates[kb], REP_SIGMA, "overall", seed=[SEED, hi, 400])
              for hi, (_, ka, kb) in enumerate(contrasts)]
        powered = [r for r in rs if r is not None]
        worst = max(powered) if powered else None
        print(f"    {label}")
        print(f"        powered contrasts: {len(powered)}/18  |  near-ties: {18 - len(powered)}"
              f"  |  max R(80%) = {fmt_r(worst)}")
    print()

    # --- Section 6: minimum detectable effect --------------------------------
    print("[6] Minimum detectable overall-accuracy gap at 80% power (reference: bias-free")
    print("    conditions about p=0.60). Answers 'what gap can R replicates resolve?'")
    grid_r = (3, 5, 8, 12, 20, 30)
    print(f"    {'sigma_b':>8s} " + " ".join(f"R={r:<2d}" for r in grid_r))
    print("    " + "-" * (9 + 6 * len(grid_r)))
    for si, sigma in enumerate(SIGMA_SWEEP):
        cells = []
        for ri, reps in enumerate(grid_r):
            mde = min_detectable_effect(sigma, reps, seed=[SEED, 500 + si, ri])
            cells.append("  >.50" if mde is None else f"{mde:6.2f}")
        print(f"    {sigma:8.2f} " + " ".join(cells))
    print()

    # --- key findings --------------------------------------------------------
    print("KEY FINDINGS:")
    print("  * Overall accuracy is bias-confounded; several contrasts are tested far more")
    print("    powerfully on the component that actually differs (discrimination or bias,")
    print("    see [2]) than on overall accuracy [1].")
    if near_ties:
        tie_word = "every" if n_artifact == len(near_ties) else f"{n_artifact} of the {len(near_ties)}"
        print(f"  * {tie_word.capitalize()} aggregate near-tie in [3] is an aggregation artifact --")
        print("    apparent overall-accuracy ties mask real discrimination/bias differences.")
    print("  * The archetype x info-type interaction (the headline 'behaviour differs'")
    print("    question) is powered at ~R=5 quizzes/cell at sigma_between=0.06; see [4].")
    print()

    # --- sigma_between calibration + recommendation --------------------------
    print("=" * 78)
    print("sigma_between calibration (from git history):")
    print("  * same-seed reruns (gemma trio, results/ vs result2/): overall delta ~0.01-0.03")
    print("    -> inference noise is small (~ the within-quiz binomial term, sigma_b ~ 0).")
    print("  * documented seed change (5f8df82, 'strange results given new seed'): overall")
    print("    swung 0.10-0.16 and per-polarity discrimination up to ~0.5 (confounded with")
    print("    model-version drift) -> the between-quiz term is the dominant, large unknown.")
    print("  => plan toward the upper sweep (sigma_between ~ 0.06-0.15), not sigma_b ~ 0.")
    print()
    print("RECOMMENDATION:")
    print("  No firm R follows from one run (the conservative quiz-level choice). Run ~5")
    print("  pilot replicate quizzes per condition (fresh ChromaticIntervalsConfig seeds),")
    print("  re-run this script (it auto-detects >=2 reps, estimates sigma_between, and")
    print("  prints the firm R), then top up sequentially to the required R. The pilots")
    print("  count toward the final R -- nothing is wasted. Read R off section [1] at the")
    print("  pilot-estimated sigma_between; near-ties fall to the equivalence sizing in [3].")


def empirical_report(quizzes, rates, obs, contrasts, n_reps) -> None:
    """Firm R once >=2 replicate quizzes per condition exist."""
    sig = {key: float(np.std([q.p_overall for q in qs], ddof=1)) for key, qs in quizzes.items()}
    sigma_hat = float(np.mean(list(sig.values())))
    print(f"MODE: empirical ({n_reps} reps/condition).")
    print(f"  Estimated between-quiz SD (mean over conditions) sigma_between = {sigma_hat:.3f}")
    print(f"  (per-condition range {min(sig.values()):.3f}-{max(sig.values()):.3f}).")
    print()
    print(f"[1] Firm R for 80%/90% power at the estimated sigma_between, overall accuracy:")
    print(f"    {'contrast':26s} {'gap':>5s} {'R(80%)':>7s} {'R(90%)':>7s}")
    print("    " + "-" * 50)
    for ci, (name, ka, kb) in enumerate(contrasts):
        gap = abs(obs[ka].p_overall - obs[kb].p_overall)
        r80 = replicates_needed(rates[ka], rates[kb], sigma_hat, "overall", seed=[SEED, ci, 0], target=0.80)
        r90 = replicates_needed(rates[ka], rates[kb], sigma_hat, "overall", seed=[SEED, ci, 1], target=0.90)
        print(f"    {name:26s} {gap:5.2f} {fmt_r(r80):>7s} {fmt_r(r90):>7s}")
    feasible = [
        replicates_needed(rates[ka], rates[kb], sigma_hat, "overall", seed=[SEED, ci, 0])
        for ci, (_, ka, kb) in enumerate(contrasts)
    ]
    feasible = [r for r in feasible if r is not None]
    if feasible:
        print()
        print(f"    Recommended R (max over powerable contrasts): {max(feasible)} quizzes/condition.")
    print()
    p = omnibus_power(rates, sigma_hat, max(feasible) if feasible else 10, seed=[SEED, 7, 0])
    print(f"[2] Omnibus archetype x info interaction power at that R: {p:.3f}")


if __name__ == "__main__":
    main()
