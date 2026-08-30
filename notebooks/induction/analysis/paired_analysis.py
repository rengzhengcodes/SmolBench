"""Paired re-analysis of the family-ladder induction study (no new data).

``power_analysis.py::cmh_reject`` treats the arms as independent binomials,
but every model answers the SAME seeds with byte-identical prompts and the
four info arms at a seed reuse one query/answer set, so all 210 PRIMARY
contrasts are matched item-for-item. Each contrast is recomputed three ways
and the change in Holm rejection status reported: unpaired CMH; item-level
exact McNemar (DESCRIPTIVE only -- marks within a replicate are not
independent); and `signflip_exact_p` over whole replicates, which carries the
inference here as it does in `significance_report.py` and
`extens_vs_noise.py`. `design_effect` measures the variance CMH omits by
summing the 9 harmonic strata as if independent (>1 anticonservative, <1
conservative).

Reads the local tree ``InductionExperiment.harness.sync_down()`` produces
(``{model}_{info}/rep_{seed}.yaml``). Those YAMLs carry ``!!python/object``
tags, so, as in ``power_analysis.py``, per-mark ``score:`` lines are regexed
rather than unsafe-loaded; marks are serialized in ascending-period order, so
position recovers the harmonic. Scoring matches
``power_analysis.py::load_outcomes``: ``score: 1`` is correct, ``0`` and
``null`` (an invalid completion) both fail. About 4% of marks are ``null``, so
a sensitivity pass that DROPS item-pairs where either arm is invalid
accompanies every headline.

Run (ephemeral env via --no-project, per repo convention):
    uv run --no-project --with numpy --with scipy python notebooks/induction/analysis/paired_analysis.py
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from scipy.stats import binom, chi2

from power_analysis import (  # noqa: E402  (path shim must precede the import)
    ALPHA,
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

    Returns ``(correct, valid)``, both keyed ``(model, info)``:
    ``correct[key][seed]`` is a length-9 bool array (True == score 1),
    ``valid[key][seed]`` is False where the score is ``null``. Seeds are
    whatever ``rep_*.yaml`` files exist, so a still-collecting lane simply
    contributes fewer; `aligned` intersects seeds per contrast. Raises
    ``SystemExit`` if a condition's results directory is missing -- call
    ``InductionExperiment.harness.sync_down()`` first.
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
    """Build item-matched mark vectors for one contrast.

    Intersects `key_a`'s and `key_b`'s seeds (a still-collecting lane is
    compared only on the seeds it has), then flattens seed x harmonic into a
    single item axis, preserving the pairing. `drop_invalid` drops item-pairs
    where either arm's mark is invalid (``score: null``). Returns
    ``(a, b, seed_index)`` over matched items; `seed_index` records each item's
    replicate, which the clustering measurements need in order to resample
    whole replicates.
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
    """Two-sided exact conditional (binomial) McNemar p for discordant counts `b`, `c`.

    Returns 1.0 when there are no discordant pairs. Treats the 270 marks as
    270 independent pairs, which they are not: DESCRIPTIVE only, while
    `signflip_exact_p` carries the inference and collapses onto this test when
    every cluster is a singleton.
    """
    nd = b + c
    if nd == 0:
        return 1.0
    return float(min(1.0, 2.0 * binom.cdf(min(b, c), nd, 0.5)))


def seed_diffs(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> list[int]:
    """Per-replicate arm difference, one integer per unique seed in `seed_idx`.

    ``d_s`` = (# correct in arm A at seed s) - (# correct in arm B at seed s),
    over the items `aligned` kept for that seed; the per-cluster summary
    `signflip_exact_p` permutes. ``sum(d_s) == b - c`` exactly (the McNemar
    discordance margin), so the two tests read the same signal and differ only
    in what they treat as exchangeable.
    """
    a_i, b_i = a.astype(np.int64), b.astype(np.int64)
    return [
        int(a_i[seed_idx == s].sum() - b_i[seed_idx == s].sum())
        for s in np.unique(seed_idx)
    ]


def signflip_exact_p(diffs) -> float:
    """EXACT two-sided seed-level sign-flip p over per-seed `diffs` from `seed_diffs`.

    The independent unit is the REPLICATE SEED, not the mark: a seed draws one
    label alphabet and one answer vector, shared by its 9 harmonic items. Under
    the null "the arms are exchangeable WITHIN a replicate" every seed's
    difference is equally likely to have come out with the opposite sign, so
    ``p = P(|T*| >= |T_obs|)`` over the 2^S sign assignments of
    ``T = sum_s d_s`` is exact. Enumerated by dynamic programming over
    attainable totals (S dict passes, not 2^S draws), so the value is
    deterministic and needs no seed. Returns 1.0 for empty `diffs`.

    With one item per cluster the test IS exact McNemar, and Studentizing is a
    provable no-op (``sum_s d_s^2`` is sign-flip invariant), so the unweighted
    seed sum is the natural member of the cluster-permutation family. The
    resolution floor is ``2 / 2^S`` (the observed assignment and its global
    negation always qualify) = 1.86e-09 at S = 30; contrasts that saturate it
    are reported at the floor, not at a fabricated smaller number.
    """
    diffs = [int(d) for d in diffs]
    if not diffs:
        return 1.0
    dist: dict[int, int] = {0: 1}
    for d in diffs:
        nxt: dict[int, int] = defaultdict(int)
        for total, weight in dist.items():
            nxt[total + d] += weight
            nxt[total - d] += weight
        dist = nxt
    observed = abs(sum(diffs))
    tail = sum(w for total, w in dist.items() if abs(total) >= observed)
    return tail / 2 ** len(diffs)


def cmh_unpaired_p(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float:
    """p-value of the repo's continuity-corrected 2x2xK CMH, strata = harmonic.

    Deliberately mirrors ``power_analysis.py::cmh_reject`` (same continuity
    correction, same hypergeometric variance), so the paired-vs-unpaired
    comparison isolates the PAIRING. Rebuilt from `aligned`'s flat item arrays,
    recovering the harmonic index as position-within-seed. Returns 1.0 if no
    stratum has enough items to contribute variance.
    """
    # `seed_idx` groups items by replicate, and within a replicate items
    # stay in ascending harmonic order, so an item's offset within its
    # own seed block IS its harmonic. (Under drop_invalid a replicate
    # can be short, which shifts later offsets. That only mislabels
    # which stratum an item lands in; it never breaks the pairing, and
    # the pre-registered pass does not drop anything.)
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
    """Holm (1979) step-down rejection mask over one family, at FWER `alpha`.

    Controls FWER under ARBITRARY dependence. The sort is STABLE because ties
    are pervasive here -- the sign-flip test has a hard resolution floor at
    2/2^30 and three lanes sit exactly on it -- and the rejection set must not
    depend on the order the contrasts happen to be built in.
    """
    m = pvals.size
    order = np.argsort(pvals, kind="stable")
    reject = np.zeros(m, dtype=bool)
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


def design_effect(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float | None:
    """Observed / independence-assumed variance of the per-seed arm difference.

    The term the CMH denominator omits: with per-item difference
    d_(s,k) = a - b and per-replicate total T_s = sum_k d_(s,k), CMH assumes
    Var(T_s) = sum_k Var(d_(.,k)) while the truth adds
    2*sum_(k<k') Cov(d_(.,k), d_(.,k')). >1 means the denominator is too small
    (anticonservative), <1 too large. ``None`` when there is no variance to
    measure (identical arms, or fewer than 3 seeds).
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
    """Run the paired re-analysis and print the report.

    Over the 210-contrast PRIMARY family, for both the pre-registered pass
    (null == incorrect) and a DROP-INVALID sensitivity pass: rejection counts
    for unpaired CMH, paired McNemar and (pre-registered pass only) seed
    sign-flip; the contrasts that change status under pairing; the standing
    intens-vs-noise question per model; and the design-effect summary. Then
    SECONDARY-family (Benjamini-Hochberg) discoveries under both tests.
    """
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
            # The cluster test is only meaningful on the pre-registered
            # pass. If invalid pairs are dropped, the per-seed sum
            # becomes a sum over a VARIABLE number of items, which is a
            # different statistic.
            p_cluster = (
                signflip_exact_p(seed_diffs(a, b, sidx)) if not drop_invalid else None
            )
            rows.append(
                dict(
                    label=label, n=a.size, acc_a=a.mean(), acc_b=b.mean(),
                    disc=(nb + nc) / max(a.size, 1), b=nb, c=nc,
                    p_paired=p_paired, p_unpaired=p_unpaired,
                    p_cluster=p_cluster,
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
        if not drop_invalid:
            p_cl = np.array([r["p_cluster"] for r in rows])
            rej_cl = holm(p_cl)
            print(
                f"  seed sign-flip+ Bonferroni : "
                f"{int((p_cl <= ALPHA / N_PRIMARY).sum()):3d}\n"
                f"  seed sign-flip+ Holm       : {int(rej_cl.sum()):3d}   "
                f"<== PRIMARY\n"
                f"  => vs item-level McNemar: "
                f"{int((rej_pair & ~rej_cl).sum())} lost, "
                f"{int((rej_cl & ~rej_pair).sum())} gained "
                f"(item-level p is anticonservative wherever\n     the seed x "
                f"arm interaction is positive, which is the majority here)"
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

            # --- clustering sign ---
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
