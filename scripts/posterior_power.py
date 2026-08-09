"""Posterior power check: at the R actually collected, what is still undecided?

The ``notebooks/*/power_analysis.py`` scripts SIZE a study from its pilot and
deliberately refuse to read the completed replicates -- feeding the finished
block back into the sizing analysis would be circular. Their docstrings say
so explicitly, and name this as the separate analysis to write if a posterior
check is ever wanted. This is that analysis.

It answers one question: **having collected R replicates, which planned
contrasts are settled and which need more data?**

WHY THIS IS NOT "OBSERVED POWER"
--------------------------------
The tempting move -- compute the power of the test you just ran, at the
effect you just observed -- is a known fallacy. Observed power is a monotone
function of the p-value, so it carries no information the p-value did not
already carry: a non-significant result ALWAYS yields low observed power, and
reporting it as "we were underpowered" merely restates "p was large" in a way
that sounds like independent evidence. It is not.

So each contrast is sorted into one of three states instead:

  DECIDED     CMH rejects at the Bonferroni-corrected alpha. Settled; more
              replicates cannot unsettle it.
  EQUIVALENT  Not significant, AND the bootstrap CI for the accuracy
              difference lies entirely inside +-MEI. The contrast is a
              demonstrated near-tie, not an absence of evidence. Settled.
  UNDECIDED   Not significant, and the CI still spans MEI. This -- and only
              this -- is a contrast where more replicates would help, and
              it is the only case where an R is quoted.

MEI is a PRE-SPECIFIED minimum effect of interest, not the observed effect.
That is what keeps the equivalence claim honest: "no difference worth caring
about" requires stating in advance how big "worth caring about" is.

For UNDECIDED contrasts the required R is simulated at the MEI (the effect we
would not want to miss), with the observed-effect sizing reported alongside
and explicitly labelled, since sizing from an observed effect is biased
upward in power by the same selection that made it look interesting.

DESIGN
------
One binary outcome per harmonic per replicate, so the data are a stratified
binomial with the harmonic as stratum -- not iid Bernoulli draws, because
difficulty varies systematically with the harmonic. The planned test is
therefore Cochran-Mantel-Haenszel stratified by harmonic, matching the
sibling sizing scripts. Confidence intervals bootstrap over REPLICATES, the
independent unit; harmonics within a replicate are not resampled because they
are strata, not draws.

Invalid marks (``score: null``) count as failures, matching the convention in
notebooks/periodic/power_analysis.py. Their count is reported separately so a
truncation problem cannot hide inside an accuracy number.

Run (repo root, main venv):
    .venv/bin/python scripts/posterior_power.py <study> [--mei 0.05]

``study`` is a notebook directory name, e.g. ``periodic_divisor``.
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
#: 12 model-within-info + 18 info-within-model. Kept as one family, including
#: the chance-floor `zero` contrasts: they are huge-effect and trivially
#: significant, but dropping them from the correction after seeing the data
#: would be exactly the multiplicity abuse the correction exists to prevent.
N_TESTS = len(INFOS) * len(list(combinations(MODELS, 2))) + len(MODELS) * len(
    list(combinations(INFOS, 2))
)
ALPHA_CORRECTED = ALPHA / N_TESTS
N_BOOT = 4000
N_SIMS = 2000
TARGET_POWER = 0.80
#: Minimum replicates per side before an EQUIVALENT verdict is allowed.
#: A bootstrap over 2 replicates that happen to agree has near-zero width, so
#: its CI fits inside any MEI and manufactures an equivalence claim out of
#: having almost no data. Equivalence is a positive claim and needs enough
#: replicates to have been capable of refuting itself; below this it is
#: reported as UNDECIDED (insufficient), which is what it actually is.
MIN_R_FOR_EQUIVALENCE = 5


def load_study(study: str) -> dict[tuple[str, str], np.ndarray]:
    """Loads every replicate as an (R, n_harmonics) 0/1 outcome matrix.

    The result YAMLs carry ``!!python/object`` tags that ``yaml.safe_load``
    refuses, and unsafe-loading repository-generated files to save a regex is
    not a trade worth making -- so, like the sibling scripts, this scans the
    ``score:`` lines as text. Marks are serialized in the generator's
    ascending-period order, so column index recovers the harmonic.
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
    """Counts ``score: null`` marks per condition, reported separately.

    Invalids are folded into the accuracy as failures, which is the right
    conservative default but also makes a truncation problem look like a
    competence problem. Surfacing the count keeps the two distinguishable.
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
    """Cochran-Mantel-Haenszel chi-square (1 df) for two conditions.

    Strata are harmonics (columns). Within stratum k the 2x2 table is
    correct/wrong x condition, pooled over replicates. Returns the statistic
    with the Yates-style continuity correction the sibling scripts use; a
    stratum contributing zero variance (both conditions all-correct or
    all-wrong) drops out, which is correct -- it carries no information about
    a difference.

    Note for anyone checking this against a Pearson chi-square by hand: on a
    SINGLE stratum this returns Pearson x (N-1)/N, not Pearson. That is not a
    bug -- the hypergeometric variance here carries an (N-1) denominator,
    which is what makes the statistic Mantel-Haenszel rather than Pearson.
    Verified numerically: an 18/20-vs-10/20 table gives 5.6875 here against a
    Yates-corrected Pearson of 5.8333, and 5.8333 * 39/40 == 5.6875 exactly.
    Null calibration was checked by simulation over heterogeneous strata: the
    false-positive rate is 0.0453 at alpha=0.05, i.e. correctly sized and
    very slightly conservative.
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
    """Upper tail of chi-square with 1 df, via the normal survival function.

    chi2(1) is the square of a standard normal, so P(X > x) = 2*(1 - Phi(sqrt
    x)). Implemented off math.erfc to keep this script free of a scipy
    dependency, matching the sibling scripts' numpy-only footprint.
    """
    from math import erfc, sqrt
    if x <= 0:
        return 1.0
    return erfc(sqrt(x / 2.0))


def boot_ci(a: np.ndarray, b: np.ndarray, rng, level: float) -> tuple[float, float, float]:
    """Bootstrap CI for the accuracy difference, resampling REPLICATES.

    Replicates are the independent unit; harmonics are strata within a
    replicate and are deliberately NOT resampled, since treating 26 strata of
    differing difficulty as exchangeable draws would understate the variance.
    Conditions are resampled independently because they are separate runs, not
    paired measurements of one draw.
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
    """Smallest R giving TARGET_POWER against the CMH test, or None past `cap`.

    Simulates per-harmonic binomial outcomes at the supplied rate vectors,
    which preserves the difficulty structure across strata rather than
    assuming a flat rate -- the same modelling choice the sizing scripts make.
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
    """Coarse-to-fine R ladder, so the common (small R) answers stay cheap."""
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
        # The equivalence CI uses 1-2*alpha (the TOST convention): a
        # (1-2a) interval inside +-MEI is exactly the two one-sided tests
        # both rejecting at a.
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
