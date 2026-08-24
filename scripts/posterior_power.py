"""Check posterior power: at the R already collected, what is still undecided?

The ``notebooks/*/power_analysis.py`` scripts size a study from its pilot
data. They refuse to read the completed replicates on purpose: feeding the
finished block back into the sizing analysis would be circular. Their
docstrings say so, and they name this script as the separate analysis to
write if you ever want a posterior check. This is that analysis.

It answers one question: after you collect R replicates, which planned
contrasts are settled, and which need more data?

WHY THIS IS NOT "OBSERVED POWER"
--------------------------------
It is tempting to compute the power of the test you just ran, at the effect
you just observed. This move is a known fallacy. Observed power is a
monotone function of the p-value, so it carries no information beyond the
p-value: a non-significant result always yields low observed power. A
report of "we were underpowered" only restates "p was large," but it
sounds like independent evidence. It is not independent evidence.

Instead, this script sorts each contrast into one of three states:

  DECIDED     The CMH test rejects at the Bonferroni-corrected alpha. The
              result is settled; more replicates cannot unsettle it.
  EQUIVALENT  The test is not significant, and the bootstrap CI for the
              accuracy difference lies entirely inside +-MEI. The contrast
              is a demonstrated near-tie, not an absence of evidence. The
              result is settled.
  UNDECIDED   The test is not significant, and the CI still spans MEI. Only
              this state means more replicates would help. This script
              quotes a required R only for this state.

MEI is a PRE-SPECIFIED minimum effect of interest, not the observed effect.
This keeps the equivalence claim honest: a claim of "no difference worth
caring about" must state in advance how big "worth caring about" is.

For UNDECIDED contrasts, this script simulates the required R at the MEI
(the effect we do not want to miss). It also reports the observed-effect
sizing, clearly labeled, because sizing from an observed effect is biased:
the same selection that made the effect look interesting also biases its
estimated power upward.

DESIGN
------
Each replicate produces one binary outcome per harmonic. This makes the
data a stratified binomial, with the harmonic as the stratum, not iid
Bernoulli draws, because difficulty varies systematically with the
harmonic. The planned test is therefore Cochran-Mantel-Haenszel, stratified
by harmonic, to match the sibling sizing scripts. Confidence intervals
bootstrap over REPLICATES, the independent unit. Harmonics within a
replicate are strata, not draws, so this script does not resample them.

Invalid marks (``score: null``) count as failures. This matches the
convention in notebooks/induction/power_analysis.py. This script reports
the invalid count separately, so a truncation problem cannot hide inside
an accuracy number.

Run this script from the repo root, in the main venv:
    .venv/bin/python scripts/posterior_power.py <study> [--mei 0.05]

``study`` is a notebook directory name, for example ``periodic_divisor``.
"""

import argparse
import re
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

NOTEBOOKS = Path(__file__).resolve().parent.parent / "notebooks"

MODELS = ("gptoss", "nemotron3", "qwen35")
INFOS = ("intens", "extens", "noise_intens", "zero")
SEED = 0
ALPHA = 0.05
#: 12 model-within-info contrasts plus 18 info-within-model contrasts. This
#: family includes the chance-floor `zero` contrasts on purpose. Those
#: contrasts have a huge effect and are trivially significant, but dropping
#: them from the correction after seeing the data would be exactly the
#: multiplicity abuse the correction exists to prevent.
N_TESTS = len(INFOS) * len(list(combinations(MODELS, 2))) + len(MODELS) * len(
    list(combinations(INFOS, 2))
)
ALPHA_CORRECTED = ALPHA / N_TESTS
N_BOOT = 4000
N_SIMS = 2000
TARGET_POWER = 0.80
#: Minimum replicates per side before this script allows an EQUIVALENT
#: verdict. A bootstrap over 2 agreeing replicates has near-zero width, so
#: its CI fits inside any MEI and manufactures an equivalence claim from
#: almost no data. Equivalence is a positive claim: it needs enough
#: replicates to have been able to refute itself. Below this threshold,
#: this script reports the contrast as UNDECIDED (insufficient data), which
#: is the honest state.
MIN_R_FOR_EQUIVALENCE = 5


def load_study(study: str) -> dict[tuple[str, str], np.ndarray]:
    """Load every replicate as an (R, n_harmonics) 0/1 outcome matrix.

    The result YAML files carry ``!!python/object`` tags that
    ``yaml.safe_load`` refuses to load. An unsafe load of
    repository-generated files just to avoid a regex is not a trade
    worth making, so, like the sibling scripts, this function scans the
    ``score:`` lines as text. The generator serializes marks in
    ascending-period order, so the column index recovers the harmonic.

    Parameters
    ----------
    study : str
        Notebook directory name under ``notebooks/``, for example
        ``"periodic_divisor"``.

    Returns
    -------
    dict[tuple[str, str], numpy.ndarray]
        Maps each ``(model, info)`` condition to an ``(R, n_harmonics)``
        float array, where 1.0 marks a correct answer and 0.0 marks a
        wrong or invalid answer.

    Raises
    ------
    SystemExit
        If the study has no ``results`` directory, if a condition's
        replicates disagree on harmonic count, or if no replicates exist
        for the study.
    """
    results = NOTEBOOKS / study / "results"
    if not results.is_dir():
        raise SystemExit(f"no results directory at {results}")
    out: dict[tuple[str, str], np.ndarray] = {}
    width = None
    for model in MODELS:
        for info in INFOS:
            arm = results / f"{model}_{info}"
            if not arm.is_dir():
                continue
            rows = []
            for rep in sorted(arm.glob("rep_*.yaml")):
                scores = re.findall(r"^\s*score:\s*(\S+)", rep.read_text(), re.M)
                # score 1 = correct; 0 and null (invalid) both count as failure.
                rows.append([1.0 if s == "1" else 0.0 for s in scores])
            if not rows:
                continue
            widths = {len(r) for r in rows}
            if len(widths) != 1:
                raise SystemExit(f"{arm}: ragged replicates, harmonic counts {sorted(widths)}")
            if width is None:
                width = widths.pop()
            out[(model, info)] = np.asarray(rows, dtype=float)
    if not out:
        raise SystemExit(f"{results}: no replicates found")
    return out


def invalid_counts(study: str) -> dict[tuple[str, str], int]:
    """Count ``score: null`` marks per condition.

    This script folds invalid marks into the accuracy as failures. That is
    the right conservative default, but it also makes a truncation problem
    look like a competence problem. This separate count keeps the two
    distinguishable.

    Parameters
    ----------
    study : str
        Notebook directory name under ``notebooks/``.

    Returns
    -------
    dict[tuple[str, str], int]
        Maps each ``(model, info)`` condition to its count of
        ``score: null`` marks across all replicates.
    """
    results = NOTEBOOKS / study / "results"
    out: dict[tuple[str, str], int] = {}
    for model in MODELS:
        for info in INFOS:
            arm = results / f"{model}_{info}"
            if not arm.is_dir():
                continue
            n = 0
            for rep in arm.glob("rep_*.yaml"):
                n += len(re.findall(r"^\s*score:\s*null\s*$", rep.read_text(), re.M))
            out[(model, info)] = n
    return out


def cmh(a: np.ndarray, b: np.ndarray) -> float:
    """Compute the Cochran-Mantel-Haenszel chi-square (1 df) for two conditions.

    Each harmonic (column) is a stratum. Within stratum k, the 2x2 table is
    correct/wrong by condition, pooled over replicates. This function
    applies the Yates-style continuity correction the sibling scripts use.
    A stratum that contributes zero variance (both conditions all-correct
    or all-wrong) drops out. This is correct: such a stratum carries no
    information about a difference.

    Parameters
    ----------
    a, b : numpy.ndarray
        (R, n_harmonics) 0/1 outcome matrices for the two conditions to
        compare. The replicate count R may differ between `a` and `b`.

    Returns
    -------
    float
        The CMH chi-square statistic with 1 degree of freedom.

    Notes
    -----
    On a SINGLE stratum, this function returns the Pearson chi-square value
    times (N-1)/N, not the plain Pearson value. This is not a bug: the
    hypergeometric variance here carries an (N-1) denominator, which is
    what makes the statistic Mantel-Haenszel rather than Pearson. A manual
    check confirms this: an 18/20-vs-10/20 table gives 5.6875 here, against
    a Yates-corrected Pearson value of 5.8333, and 5.8333 * 39/40 equals
    5.6875 exactly.

    A simulation over heterogeneous strata checked the null calibration:
    the false-positive rate is 0.0453 at alpha=0.05. The test is correctly
    sized, and very slightly conservative.
    """
    num = 0.0
    var = 0.0
    for k in range(a.shape[1]):
        ak, bk = a[:, k], b[:, k]
        n1, n2 = len(ak), len(bk)
        s1, s2 = ak.sum(), bk.sum()
        n = n1 + n2
        if n < 2:
            continue
        col1 = s1 + s2           # total correct in this stratum
        col2 = n - col1          # total wrong
        num += s1 - n1 * col1 / n
        v = n1 * n2 * col1 * col2 / (n * n * (n - 1))
        var += v
    if var <= 0:
        return 0.0
    return (abs(num) - 0.5) ** 2 / var


def chi2_sf_1df(x: float) -> float:
    """Compute the upper tail of the chi-square distribution with 1 df.

    chi2(1) is the square of a standard normal variable, so
    P(X > x) = 2 * (1 - Phi(sqrt(x))). This function computes that value
    from ``math.erfc``, to keep this script free of a scipy dependency.
    This matches the numpy-only footprint of the sibling scripts.

    Parameters
    ----------
    x : float
        The chi-square statistic.

    Returns
    -------
    float
        The upper-tail probability P(X > x). Returns 1.0 when `x` is
        non-positive.
    """
    from math import erfc, sqrt
    if x <= 0:
        return 1.0
    return erfc(sqrt(x / 2.0))


def boot_ci(a: np.ndarray, b: np.ndarray, rng, level: float) -> tuple[float, float, float]:
    """Bootstrap a confidence interval for the accuracy difference.

    This function resamples REPLICATES, the independent unit. Harmonics are
    strata within a replicate, so this function does not resample them:
    treating strata of differing difficulty as exchangeable draws would
    understate the variance. This function resamples the two conditions
    independently, because they are separate runs, not paired measurements
    of one draw.

    Parameters
    ----------
    a, b : numpy.ndarray
        (R, n_harmonics) 0/1 outcome matrices for the two conditions to
        compare.
    rng : numpy.random.Generator
        Random number generator used for the resampling.
    level : float
        Confidence level of the interval, in (0, 1).

    Returns
    -------
    tuple[float, float, float]
        ``(diff, lo, hi)``: the observed accuracy difference ``a - b``, and
        the lower and upper bounds of the bootstrap confidence interval.
    """
    ra, rb = a.shape[0], b.shape[0]
    ia = rng.integers(0, ra, size=(N_BOOT, ra))
    ib = rng.integers(0, rb, size=(N_BOOT, rb))
    da = a.mean(axis=1)[ia].mean(axis=1)
    db = b.mean(axis=1)[ib].mean(axis=1)
    diffs = da - db
    lo = float(np.percentile(diffs, 100 * (1 - level) / 2))
    hi = float(np.percentile(diffs, 100 * (1 + level) / 2))
    return float(a.mean() - b.mean()), lo, hi


def replicates_needed(rates_a: np.ndarray, rates_b: np.ndarray, rng, cap: int = 400) -> int | None:
    """Find the smallest R that reaches TARGET_POWER against the CMH test.

    This function simulates per-harmonic binomial outcomes at the given
    rate vectors. This preserves the difficulty structure across strata,
    instead of assuming a flat rate, matching the modeling choice the
    sizing scripts make.

    Parameters
    ----------
    rates_a, rates_b : numpy.ndarray
        Per-harmonic success-rate vectors for the two simulated conditions.
    rng : numpy.random.Generator
        Random number generator used for the simulation.
    cap : int, default 400
        Largest R this function tries before it gives up.

    Returns
    -------
    int or None
        The smallest R in the search ladder that reaches TARGET_POWER, or
        None if no R up to `cap` reaches it.
    """
    for r in _ladder(cap):
        hits = 0
        for _ in range(N_SIMS // 4):
            sa = (rng.random((r, len(rates_a))) < rates_a).astype(float)
            sb = (rng.random((r, len(rates_b))) < rates_b).astype(float)
            if chi2_sf_1df(cmh(sa, sb)) < ALPHA_CORRECTED:
                hits += 1
        if hits / (N_SIMS // 4) >= TARGET_POWER:
            return r
    return None


def _ladder(cap: int) -> list[int]:
    """Build a coarse-to-fine ladder of R values up to `cap`.

    The ladder keeps common, small-R answers cheap to compute.

    Parameters
    ----------
    cap : int
        Largest R value to include in the ladder.

    Returns
    -------
    list[int]
        Candidate R values in increasing order, all at most `cap`.
    """
    return [r for r in (5, 10, 15, 20, 25, 30, 40, 50, 65, 80, 100, 130, 160, 200, 260, 320, 400)
            if r <= cap]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("study", help="notebook directory name, e.g. periodic_divisor")
    ap.add_argument("--mei", type=float, default=0.05,
                    help="minimum effect of interest, absolute accuracy difference "
                         "(default 0.05). Pre-specify it; do not tune it to the data.")
    args = ap.parse_args()

    data = load_study(args.study)
    invalids = invalid_counts(args.study)
    rng = np.random.default_rng(SEED)

    reps = {k: v.shape[0] for k, v in data.items()}
    harmonics = next(iter(data.values())).shape[1]
    print(f"study: {args.study}")
    print(f"harmonics per replicate: {harmonics}   conditions: {len(data)}")
    print(f"MEI: {args.mei:.3f} absolute accuracy   alpha: {ALPHA}/{N_TESTS} = "
          f"{ALPHA_CORRECTED:.2e}\n")

    print("condition accuracy (invalids counted as failures)")
    print(f"  {'condition':>28} {'R':>4} {'acc':>7} {'invalid':>8}")
    for key in sorted(data):
        acc = data[key].mean()
        print(f"  {key[0] + '/' + key[1]:>28} {reps[key]:>4} {acc:>7.4f} {invalids.get(key, 0):>8}")

    contrasts = []
    for info in INFOS:
        for m_a, m_b in combinations(MODELS, 2):
            contrasts.append((f"[{info}] {m_a} vs {m_b}", (m_a, info), (m_b, info)))
    for model in MODELS:
        for i_a, i_b in combinations(INFOS, 2):
            contrasts.append((f"[{model}] {i_a} vs {i_b}", (model, i_a), (model, i_b)))

    print(f"\n{'contrast':>34} {'diff':>8} {'95% CI':>18} {'p (CMH)':>10}  state")
    print("-" * 96)
    undecided = []
    tally = {"DECIDED": 0, "EQUIVALENT": 0, "UNDECIDED": 0, "SKIPPED": 0}
    for label, ka, kb in contrasts:
        if ka not in data or kb not in data:
            tally["SKIPPED"] += 1
            continue
        a, b = data[ka], data[kb]
        p = chi2_sf_1df(cmh(a, b))
        # The equivalence CI uses 1-2*alpha (the TOST convention). A
        # (1-2a) interval inside +-MEI gives the same result as two
        # one-sided tests that both reject at alpha.
        diff, lo, hi = boot_ci(a, b, rng, level=1 - 2 * ALPHA_CORRECTED)
        enough = min(a.shape[0], b.shape[0]) >= MIN_R_FOR_EQUIVALENCE
        if p < ALPHA_CORRECTED:
            state = "DECIDED"
        elif lo > -args.mei and hi < args.mei and enough:
            state = "EQUIVALENT"
        else:
            state = "UNDECIDED"
            undecided.append((label, ka, kb, diff))
        tally[state] += 1
        print(f"{label:>34} {diff:>+8.4f} [{lo:>+7.4f},{hi:>+7.4f}] {p:>10.2e}  {state}")

    print("-" * 96)
    print(f"DECIDED {tally['DECIDED']}   EQUIVALENT {tally['EQUIVALENT']}   "
          f"UNDECIDED {tally['UNDECIDED']}" +
          (f"   SKIPPED {tally['SKIPPED']} (missing conditions)" if tally["SKIPPED"] else ""))

    if not undecided:
        print(
            f"\nNOTHING FURTHER NEEDED at MEI={args.mei:.3f}. Every contrast is either "
            "resolved\nor demonstrated equivalent; more replicates would not change a "
            "conclusion."
        )
        return 0

    print(f"\n{len(undecided)} contrast(s) undecided -- CI still spans +-{args.mei:.3f}. "
          "Replicates needed:")
    print(f"\n{'contrast':>34} {'R now':>6} {'R for MEI':>10} {'R at observed':>14}")
    print("-" * 68)
    for label, ka, kb, diff in undecided:
        a, b = data[ka], data[kb]
        base = a.mean(axis=0)
        shifted = np.clip(base - args.mei, 0.0, 1.0)
        r_mei = replicates_needed(base, shifted, rng)
        r_obs = replicates_needed(a.mean(axis=0), b.mean(axis=0), rng)
        now = min(reps[ka], reps[kb])
        print(f"{label:>34} {now:>6} {str(r_mei or '>400'):>10} {str(r_obs or '>400'):>14}")
    print(
        "\n'R for MEI' is the honest target: the replicates needed to detect an effect\n"
        "of the pre-specified size. 'R at observed' is shown for context only -- sizing\n"
        "from an observed effect is biased, because the same noise that made the effect\n"
        "look large is what selected it into this list."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
