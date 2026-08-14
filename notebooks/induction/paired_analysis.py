"""PAIRED re-analysis of the family-ladder induction study.

Implements the two corrections specified in ``MULTIPLICITY_PLAN.md`` sections
2.1 and 2.2, against the marks already collected (no new data collection):

  1. PAIRED pairwise tests. Every model answers the SAME seeds with
     byte-identical prompts, and the four info arms at a given seed reuse the
     same queries and answers (``get_periodic_zero_info_numeric_quiz`` empties
     only the context), so all 210 PRIMARY contrasts are matched item-for-item.
     ``power_analysis.py::cmh_reject`` nevertheless treats the two arms as
     independent binomials. This script computes, for every contrast, BOTH the
     unpaired harmonic-stratified CMH p-value (what the current code would
     give) and the exact McNemar p-value on the matched marks, and reports how
     many contrasts change rejection status under Holm over the 210-test
     PRIMARY family.

  2. The CLUSTERING SIGN. Each replicate seed contributes exactly one unit to
     each of the 9 harmonic strata, and CMH sums those strata's variances as if
     independent -- dropping the cross-stratum covariance. Whether that makes
     the test anticonservative or conservative is an empirical question about
     the sign of the seed x arm interaction, and it is measurable from these
     data: compare the observed variance of the per-seed total arm difference
     against the sum of the per-harmonic variances. The ratio IS the design
     effect the CMH denominator is missing (>1 anticonservative, <1
     conservative).

Marks are read from the local results tree that
``InductionExperiment.harness.sync_down()`` produces
(``{model}_{info}/rep_{seed}.yaml``). The YAMLs carry ``!!python/object`` tags,
so -- following the same reasoning as ``power_analysis.py`` -- we regex the
per-mark ``score:`` lines rather than unsafe-loading repository-generated
files. Marks are serialized in the generator's ascending-period order, so
position recovers the harmonic.

Scoring convention: ``score: 1`` is correct; ``0`` and ``null`` (an invalid /
uncompliant completion) are both failures. That matches
``power_analysis.py::load_outcomes`` exactly. Because ~4% of marks are ``null``
and their treatment is a live methodological question in this project, a
sensitivity pass that DROPS item-pairs where either arm is invalid is reported
alongside every headline.

Run (ephemeral env via --no-project, per repo convention):
    uv run --no-project --with numpy --with scipy python notebooks/induction/paired_analysis.py
"""

import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from scipy.stats import binom, chi2

from power_analysis import (  # noqa: E402  (path shim must precede the import)
    ALPHA,
    FAMILIES,
    INFOS,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    RESULTS_DIR,
    build_primary_contrasts,
    build_secondary_contrasts,
)

SCORE_RE = re.compile(r"^\s*score:\s*(\S+)", re.M)


def load_marks() -> tuple[dict, dict]:
    """Read every landed replicate into per-condition (seed -> 9-vector) maps.

    Returns
    -------
    (correct, valid) : two dicts keyed ``(model, info)``
        ``correct[key][seed]`` is a length-9 bool array (True == score 1).
        ``valid[key][seed]`` is a length-9 bool array (False == score null).
        Seeds are whatever ``rep_*.yaml`` files exist, so a lane that is still
        collecting (min3_14b at the time of writing) simply contributes fewer
        seeds and is handled by the per-contrast seed intersection below.
    """
    correct: dict = {}
    valid: dict = {}
    for model in MODELS:
        for info in INFOS:
            cdir = RESULTS_DIR / f"{model}_{info}"
            if not cdir.is_dir():
                raise SystemExit(
                    f"No results directory for ({model}, {info}); expected\n  {cdir}\n"
                    f"Call InductionExperiment.harness.sync_down() to pull the "
                    f"S3-backed log into the local rep_{{seed}}.yaml layout."
                )
            c_by_seed, v_by_seed = {}, {}
            for path in cdir.glob("rep_*.yaml"):
                seed = int(path.stem.split("_")[1])
                scores = SCORE_RE.findall(path.read_text())
                if len(scores) != N_HARMONICS:
                    # A partially-written replicate: skip it rather than
                    # silently misaligning the harmonic axis for this seed.
                    print(
                        f"  WARNING: {path} has {len(scores)} scores, "
                        f"expected {N_HARMONICS} -- skipping this replicate",
                        file=sys.stderr,
                    )
                    continue
                c_by_seed[seed] = np.array([s == "1" for s in scores])
                v_by_seed[seed] = np.array([s != "null" for s in scores])
            correct[(model, info)] = c_by_seed
            valid[(model, info)] = v_by_seed
    return correct, valid


def aligned(correct, valid, key_a, key_b, drop_invalid: bool):
    """Item-matched mark vectors for one contrast.

    Intersects the two conditions' seeds (so a still-collecting lane is
    compared only on the seeds it has) and flattens seed x harmonic into a
    single item axis, preserving the pairing.

    Returns ``(a, b, seed_index)`` as 1-D arrays over matched items, where
    ``seed_index`` records which replicate each item came from -- needed by the
    clustering measurement, which must resample whole replicates.
    """
    seeds = sorted(set(correct[key_a]) & set(correct[key_b]))
    a = np.array([correct[key_a][s] for s in seeds])          # (n_seeds, 9)
    b = np.array([correct[key_b][s] for s in seeds])
    keep = np.ones_like(a, dtype=bool)
    if drop_invalid:
        keep = np.array([valid[key_a][s] for s in seeds]) & np.array(
            [valid[key_b][s] for s in seeds]
        )
    seed_idx = np.repeat(np.arange(len(seeds)), N_HARMONICS).reshape(a.shape)
    return a[keep], b[keep], seed_idx[keep]


def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact conditional (binomial) McNemar p-value.

    ``b``/``c`` are the discordant counts. With no discordant pairs there is no
    evidence of a difference, so p = 1.
    """
    nd = b + c
    if nd == 0:
        return 1.0
    return float(min(1.0, 2.0 * binom.cdf(min(b, c), nd, 0.5)))


def cmh_unpaired_p(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float:
    """p-value of the repo's continuity-corrected 2x2xK CMH, strata = harmonic.

    This deliberately mirrors ``power_analysis.py::cmh_reject`` (same
    continuity correction, same hypergeometric variance) so the paired-vs-
    unpaired comparison isolates the PAIRING, not incidental differences in
    the statistic. Rebuilt from the flat item arrays: the harmonic index is
    recovered as position-within-seed.
    """
    # `seed_idx` groups items by replicate, and within a replicate items stay in
    # ascending harmonic order, so an item's offset within its own seed block IS
    # its harmonic. (Under drop_invalid a replicate can be short, which shifts
    # later offsets; that only mislabels which stratum an item lands in, never
    # breaks the pairing, and the pre-registered pass does not drop anything.)
    num_terms, den_terms = [], []
    order = np.concatenate([np.arange((seed_idx == s).sum()) for s in np.unique(seed_idx)])
    for k in np.unique(order):
        sel = order == k
        na, nb = sel.sum(), sel.sum()
        sa, sb = a[sel].sum(), b[sel].sum()
        big_n = na + nb
        if big_n < 2:
            continue
        m1 = sa + sb
        m0 = big_n - m1
        num_terms.append(sa - m1 * na / big_n)
        den_terms.append((na * nb * m1 * m0) / (big_n * big_n * (big_n - 1)))
    if not den_terms:
        return 1.0
    den = float(np.sum(den_terms))
    if den <= 0:
        return 1.0
    num = max(abs(float(np.sum(num_terms))) - 0.5, 0.0) ** 2
    return float(chi2.sf(num / den, df=1))


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Holm (1979) step-down rejections at familywise level `alpha`.

    Controls FWER under ARBITRARY dependence and is uniformly more powerful
    than single-step Bonferroni -- see MULTIPLICITY_PLAN.md section 1.
    """
    m = pvals.size
    order = np.argsort(pvals)
    reject = np.zeros(m, dtype=bool)
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


def design_effect(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float | None:
    """Observed / independence-assumed variance of the per-seed arm difference.

    The quantity the CMH denominator omits. Let d_(s,k) = a - b be the per-item
    arm difference and T_s = sum_k d_(s,k) the per-replicate total. Summing
    per-stratum variances (what CMH does) assumes Var(T_s) = sum_k Var(d_(.,k));
    the truth adds 2*sum_(k<k') Cov(d_(.,k), d_(.,k')). This returns the ratio
    of the two, i.e. the design effect: >1 means the statistic's denominator is
    too small (anticonservative), <1 means too large (conservative).

    Returns None when the contrast has no variance to measure (identical arms).
    """
    d = a.astype(float) - b.astype(float)
    seeds = np.unique(seed_idx)
    if seeds.size < 3:
        return None
    order = np.concatenate([np.arange((seed_idx == s).sum()) for s in seeds])
    per_seed_total = np.array([d[seed_idx == s].sum() for s in seeds])
    observed = per_seed_total.var(ddof=1)
    assumed = float(np.sum([d[order == k].var(ddof=1) for k in np.unique(order)]))
    if assumed <= 0:
        return None
    return float(observed / assumed)


def main() -> None:
    print("Loading marks ...", flush=True)
    correct, valid = load_marks()
    depths = {k: len(v) for k, v in correct.items()}
    print(
        f"  {len(correct)} conditions; replicate depth "
        f"min={min(depths.values())} max={max(depths.values())}"
    )
    short = sorted({m for (m, _), n in depths.items() if n < max(depths.values())})
    if short:
        print(f"  still collecting (compared on their common seeds only): {short}")

    contrasts = build_primary_contrasts()
    assert len(contrasts) == N_PRIMARY

    for drop_invalid in (False, True):
        tag = "DROP-INVALID pairs" if drop_invalid else "null == incorrect (pre-registered)"
        print(f"\n{'=' * 78}\nPRIMARY family, {tag}\n{'=' * 78}")
        rows = []
        for label, key_a, key_b in contrasts:
            a, b, sidx = aligned(correct, valid, key_a, key_b, drop_invalid)
            nb = int((a & ~b).sum())
            nc = int((~a & b).sum())
            p_paired = mcnemar_exact_p(nb, nc)
            p_unpaired = cmh_unpaired_p(a, b, sidx)
            rows.append(
                dict(
                    label=label, n=a.size, acc_a=a.mean(), acc_b=b.mean(),
                    disc=(nb + nc) / max(a.size, 1), b=nb, c=nc,
                    p_paired=p_paired, p_unpaired=p_unpaired,
                    de=design_effect(a, b, sidx),
                )
            )

        p_pair = np.array([r["p_paired"] for r in rows])
        p_unp = np.array([r["p_unpaired"] for r in rows])
        rej_pair, rej_unp = holm(p_pair), holm(p_unp)
        bonf_pair, bonf_unp = p_pair <= ALPHA / N_PRIMARY, p_unp <= ALPHA / N_PRIMARY

        print(
            f"Rejections at FWER {ALPHA} over {N_PRIMARY} contrasts:\n"
            f"  unpaired CMH  + Bonferroni : {bonf_unp.sum():3d}\n"
            f"  unpaired CMH  + Holm       : {rej_unp.sum():3d}\n"
            f"  paired McNemar+ Bonferroni : {bonf_pair.sum():3d}\n"
            f"  paired McNemar+ Holm       : {rej_pair.sum():3d}"
        )
        gained = [r for r, gp, gu in zip(rows, rej_pair, rej_unp) if gp and not gu]
        lost = [r for r, gp, gu in zip(rows, rej_pair, rej_unp) if gu and not gp]
        print(
            f"  => pairing changes status on {len(gained) + len(lost)} contrasts "
            f"(+{len(gained)} gained, -{len(lost)} lost)"
        )
        for r in sorted(gained, key=lambda r: r["p_paired"])[:20]:
            print(
                f"    GAINED {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}  "
                f"disc={r['disc']:.3f}  p_pair={r['p_paired']:.2e}  "
                f"p_unpair={r['p_unpaired']:.2e}"
            )
        for r in sorted(lost, key=lambda r: r["p_unpaired"])[:20]:
            print(
                f"    LOST   {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}  "
                f"disc={r['disc']:.3f}  p_pair={r['p_paired']:.2e}  "
                f"p_unpair={r['p_unpaired']:.2e}"
            )

        if not drop_invalid:
            # --- the standing question: does intens ever separate from noise? --
            print(
                "\nStanding question -- intens vs noise_intens, per model "
                "(no prior study ever separated these):"
            )
            hdr = f"  {'model':14s} {'intens':>7s} {'noise':>7s} {'disc':>7s} {'b/c':>9s} {'p_paired':>10s} {'p_unpaired':>11s}"
            print(hdr)
            print("  " + "-" * (len(hdr) - 2))
            for r in rows:
                if "] intens vs noise_intens" not in r["label"]:
                    continue
                model = r["label"].split("]")[0].strip("[")
                flag = ""
                if r["p_paired"] <= ALPHA / N_PRIMARY:
                    flag = "  <== SEPARATES (Bonferroni)"
                elif r["p_paired"] <= ALPHA:
                    flag = "  <== p<0.05 uncorrected"
                print(
                    f"  {model:14s} {r['acc_a']:7.3f} {r['acc_b']:7.3f} "
                    f"{r['disc']:7.3f} {r['b']:4d}/{r['c']:<4d} "
                    f"{r['p_paired']:10.2e} {r['p_unpaired']:11.2e}{flag}"
                )

            # --- clustering sign (MULTIPLICITY_PLAN.md 2.2) -------------------
            des = np.array([r["de"] for r in rows if r["de"] is not None])
            print(
                f"\nClustering / cross-stratum covariance, over {des.size} measurable "
                f"PRIMARY contrasts:\n"
                f"  design effect = Var(per-seed total diff) / sum_k Var_k  "
                f"(>1 anticonservative, <1 conservative)\n"
                f"    median {np.median(des):.3f}   mean {des.mean():.3f}   "
                f"p10 {np.percentile(des, 10):.3f}   p90 {np.percentile(des, 90):.3f}   "
                f"max {des.max():.3f}\n"
                f"    fraction > 1.0 : {(des > 1.0).mean():.3f}   "
                f"fraction > 1.5 : {(des > 1.5).mean():.3f}"
            )

    # --- Tier 3 (SECONDARY) gets the same treatment, for completeness --------
    sec = build_secondary_contrasts()
    p_pair_s, p_unp_s = [], []
    for _label, key_a, key_b in sec:
        a, b, sidx = aligned(correct, valid, key_a, key_b, False)
        p_pair_s.append(mcnemar_exact_p(int((a & ~b).sum()), int((~a & b).sum())))
        p_unp_s.append(cmh_unpaired_p(a, b, sidx))
    p_pair_s, p_unp_s = np.array(p_pair_s), np.array(p_unp_s)

    def bh(p, q=0.05):
        m = p.size
        order = np.argsort(p)
        thresh = q * (np.arange(1, m + 1)) / m
        passed = p[order] <= thresh
        k = np.max(np.nonzero(passed)[0]) + 1 if passed.any() else 0
        rej = np.zeros(m, dtype=bool)
        rej[order[:k]] = True
        return rej

    print(
        f"\n{'=' * 78}\nSECONDARY family ({len(sec)} cross-family size-matched "
        f"contrasts, intens only), Benjamini-Hochberg q=0.05\n{'=' * 78}\n"
        f"  unpaired CMH   : {bh(p_unp_s).sum():3d} discoveries\n"
        f"  paired McNemar : {bh(p_pair_s).sum():3d} discoveries"
    )


if __name__ == "__main__":
    main()
