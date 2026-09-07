"""Paired re-analysis of the family-ladder induction study (no new data).

``power_analysis.py::cmh_reject`` treats the arms as independent binomials,
but every model answers the same seeds with byte-identical prompts and the
four info arms at a seed reuse one query/answer set, so all 210 PRIMARY
contrasts are matched item-for-item. Each is recomputed three ways -- unpaired
CMH, item-level exact McNemar (descriptive only), and `signflip_exact_p` over
whole replicates (which carries the inference) -- and the change in Holm
rejection status reported. `design_effect` measures the variance CMH omits
by summing the 9 harmonic strata as if independent.

Reads the local tree via ``LocalResultsStore``'s own reader (``Marks.load``),
so a ``score:``-shaped line inside a CoT trace can never be scraped as a
phantom mark. A drop-invalid sensitivity pass accompanies every headline,
since a few percent of marks are ``null`` (scored as incorrect).

Run (repo root):
    .venv/bin/python notebooks/induction/analysis/paired_analysis.py
"""

import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

# The analysis dir itself: needed when this module is loaded by path (only
# __main__ gets it for free); power_analysis inserts notebooks/ itself.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy.stats import chi2
from statsmodels.stats.multitest import multipletests

from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress

from power_analysis import (  # noqa: E402  (path shim must precede the import)
    ALPHA,
    INFOS,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    Q_SECONDARY,
    RESULTS_DIR,
    build_primary_contrasts,
    build_secondary_contrasts,
    # DESCRIPTIVE only (it treats the 270 marks as 270 independent pairs, which
    # they are not); `signflip_exact_p` carries the inference and collapses
    # onto this test at singleton clusters.
    mcnemar_exact_p,
)

#: run_study.N_REPLICATES (user-locked). Depth is gated against this absolute
#: number, not the tree's own deepest lane, because a uniform shortfall would
#: otherwise leave no lane looking "short" relative to its neighbours while
#: silently raising the sign-flip floor (2/2^S) above every Holm threshold.
EXPECTED_R = 30


def results_store() -> LocalResultsStore:
    """Return a store over the CURRENT `RESULTS_DIR`, rooted at this module's global.

    A fresh store on every call, reading `RESULTS_DIR` at call time rather
    than a module-level singleton -- `RESULTS_DIR` is rebindable (tests
    repoint it per fixture tree), and a store built at import would keep
    reading the tree it captured regardless of later rebinding. Constructing
    one is free (a frozen dataclass holding a `Path`), so the per-call
    rebuild costs nothing next to the YAML parsing.
    """
    return LocalResultsStore(RESULTS_DIR)


def load_marks() -> tuple[dict, dict, dict]:
    """Read every landed replicate into per-condition (seed -> 9-vector) maps.

    Each replicate is opened exactly once; `correct` (score==1), `valid`
    (score is not ``null``) and `compliance` are three views of that one
    parse, so ``significance_report.compliance_census`` reads the same parse
    the contrasts do rather than re-walking the tree. A replicate skipped as
    short is skipped from all three maps at once.

    Raises
    ------
    SystemExit
        If a condition yields no replicate seeds at all (call.
        ``InductionExperiment.harness.sync_down()`` first).
    """
    correct: dict = {}
    valid: dict = {}
    compliance: dict = {}
    store = results_store()
    for model in MODELS:
        for info in INFOS:
            # tag=model: this study's local directory key is the model id.
            # model=None: LocalResultsStore ignores addr.model entirely since
            # this chain never talks to S3, so the field is left unset rather
            # than filled with a value nothing would read.
            def addr_of(seed: int, _m: str = model, _i: str = info) -> ReplicateAddress:
                """Address one replicate of the cell this iteration is on.

                `_m`/`_i` are default-bound rather than closed over, so the
                function cannot capture a later iteration's cell.

                Parameters
                ----------
                seed : int
                    Replicate seed.
                _m : str, optional
                    Model for the current cell.
                _i : str, optional
                    Info value for the current cell.

                Returns
                -------
                ReplicateAddress
                    Address for the replicate.
                """
                return ReplicateAddress(tag=_m, info=_i, seed=seed)

            # list_seeds globs rep_*.yaml and skips any name whose seed
            # segment does not parse as an int.
            seeds = store.list_seeds(None, model, info)
            if not seeds:
                # Gate on the seed list, not the directory: list_seeds
                # returns [] for a missing directory too, so this also
                # catches an existing-but-empty one before `aligned` would
                # otherwise die on the vaguer "no common seeds" message.
                #
                # store._path is the store's own renderer of the layout, used
                # here read-only just to name a directory for a human. (Seed 0
                # is arbitrary -- only the parent is used.)
                cdir = store._path(addr_of(0)).parent
                raise SystemExit(
                    f"No replicates for ({model}, {info}); expected "
                    f"rep_{{seed}}.yaml files in\n  {cdir}\n"
                    f"(the directory is missing, empty, or holds no file whose "
                    f"name parses as a seed).\n"
                    f"Call InductionExperiment.harness.sync_down() to pull the "
                    f"S3-backed log into the local rep_{{seed}}.yaml layout."
                )
            c_by_seed, v_by_seed, k_by_seed = {}, {}, {}
            for seed in seeds:
                # ONE load per replicate, reused for all three maps: reloading
                # per view is what made the census cost a second full walk.
                marks = store.load_marks(addr_of(seed)).marks
                scores = [m.score for m in marks]
                if len(scores) != N_HARMONICS:
                    # A partially-written replicate: skip it rather than
                    # silently misaligning the harmonic axis for this seed.
                    print(
                        f"  WARNING: {store._path(addr_of(seed))} has "
                        f"{len(scores)} scores, expected {N_HARMONICS} "
                        f"-- skipping this replicate",
                        file=sys.stderr,
                    )
                    continue
                c_by_seed[seed] = np.array([s == 1 for s in scores])
                v_by_seed[seed] = np.array([s is not None for s in scores])
                k_by_seed[seed] = tuple(m.compliance for m in marks)
            correct[(model, info)] = c_by_seed
            valid[(model, info)] = v_by_seed
            compliance[(model, info)] = k_by_seed
    return correct, valid, compliance


def aligned(
    correct: dict, valid: dict, key_a: tuple[str, str], key_b: tuple[str, str], drop_invalid: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build item-matched mark vectors for one contrast: ``(a, b, seed_index)``.

    Intersects `key_a`'s and `key_b`'s seeds (a still-collecting lane is
    compared only on the seeds it has), then flattens seed x harmonic into
    one item axis, preserving the pairing.

    Parameters
    ----------
    correct : dict
        Per-cell correct-mark mappings.
    valid : dict
        Per-cell valid-mark mappings.
    key_a : tuple[str, str]
        First cell key.
    key_b : tuple[str, str]
        Second cell key.
    drop_invalid : bool
        Drops item-pairs where either arm's mark is invalid (``score: null``).

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Matched marks for both arms; `seed_index` records each item's.
        replicate, needed to resample whole replicates.
    """
    seeds = sorted(set(correct[key_a]) & set(correct[key_b]))
    if not seeds:
        # Content gate: an empty intersection means one lane contributed
        # nothing usable -- fail with the cause, not a downstream numpy error.
        raise SystemExit(
            f"No common seeds between {key_a} and {key_b}; one lane has no "
            "usable replicates. Check the load warnings above and re-run "
            "sync_down()."
        )
    a = np.array([correct[key_a][s] for s in seeds])          # (n_seeds, 9)
    b = np.array([correct[key_b][s] for s in seeds])
    keep = np.ones_like(a, dtype=bool)
    if drop_invalid:
        keep = np.array([valid[key_a][s] for s in seeds]) & np.array(
            [valid[key_b][s] for s in seeds]
        )
    seed_idx = np.repeat(np.arange(len(seeds)), N_HARMONICS).reshape(a.shape)
    return a[keep], b[keep], seed_idx[keep]


def seed_diffs(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> list[int]:
    """Per-replicate arm difference, one integer per unique seed in `seed_idx`.

    The per-cluster summary `signflip_exact_p` permutes. ``sum(d_s) == b - c``
    exactly (the McNemar discordance margin), so both tests read the same
    signal and differ only in what they treat as exchangeable.

    Parameters
    ----------
    a : np.ndarray
        First arm's matched marks.
    b : np.ndarray
        Second arm's matched marks.
    seed_idx : np.ndarray
        Replicate index for each matched mark.

    Returns
    -------
    list[int]
        Arm differences, one per unique seed.
    """
    a_i, b_i = a.astype(np.int64), b.astype(np.int64)
    return [
        int(a_i[seed_idx == s].sum() - b_i[seed_idx == s].sum())
        for s in np.unique(seed_idx)
    ]


def signflip_exact_p(diffs: Iterable[int]) -> float:
    """Exact two-sided seed-level sign-flip p over per-seed `diffs` from `seed_diffs`.

    The independent unit is the replicate seed, not the mark: a seed draws
    one label alphabet and one answer vector, shared by its 9 harmonic items.
    ``p = P(|T*| >= |T_obs|)`` over the 2^S sign assignments of ``T = sum_s
    d_s`` is exact, enumerated by dynamic programming over attainable totals
    (S dict passes, not 2^S draws), so it is deterministic and needs no seed.

    The resolution floor is ``2 / 2^S``; contrasts that saturate it are
    reported at the floor, not at a fabricated smaller number.

    Parameters
    ----------
    diffs : Iterable[int]
        Per-seed arm differences.

    Returns
    -------
    float
        Exact two-sided sign-flip p-value. 1.0 for empty `diffs`.
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

    Mirrors ``power_analysis.py::cmh_reject`` (same continuity correction,
    same hypergeometric variance), so the paired-vs-unpaired comparison
    isolates the pairing. Rebuilt from `aligned`'s flat item arrays, the
    harmonic index recovered as position-within-seed.

    Parameters
    ----------
    a : np.ndarray
        First arm's matched marks.
    b : np.ndarray
        Second arm's matched marks.
    seed_idx : np.ndarray
        Replicate index for each matched mark.

    Returns
    -------
    float
        P-value of the repo's continuity-corrected 2x2xK CMH. 1.0 if no.
        stratum has enough items to contribute variance.
    """
    # An item's offset inside its own seed block is its harmonic, since items
    # stay in ascending harmonic order within a replicate. Under drop_invalid
    # a short replicate shifts later offsets, mislabeling the stratum an item
    # lands in, but leaves the pairing untouched.
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

    Thin wrapper over ``statsmodels.stats.multitest.multipletests`` with
    ``method="holm"``. Holm controls FWER under arbitrary dependence, which
    is why it carries the headline here: the 210 PRIMARY contrasts share
    models, seeds and harmonics, so no positive-dependence assumption is
    available to buy the extra power of a step-up procedure
    (`significance_report.hochberg` is a labelled sensitivity check only).

    Parameters
    ----------
    pvals : np.ndarray
        P-values in the family.
    alpha : float, optional
        Familywise error-rate level.

    Returns
    -------
    np.ndarray
        Rejection mask.
    """
    # multipletests sorts with a bare np.argsort rather than a stable sort,
    # which is safe despite pervasive ties (the sign-flip test's hard
    # resolution floor at 2/2^S, and 1.0 returned verbatim for any contrast
    # with no discordant pairs): Holm's per-rank threshold alpha/(m-i) is
    # monotone increasing in rank, so a tied group can never straddle the
    # accept/reject boundary and tie order cannot move the rejection set.
    # Executed, not just asserted, by
    # test_rejection_sets_do_not_depend_on_contrast_build_order.
    reject, _pvals_corrected, _alphac_sidak, _alphac_bonf = multipletests(
        pvals, alpha=alpha, method="holm"
    )
    return np.asarray(reject, dtype=bool)


def bh(pvals: np.ndarray, q: float = Q_SECONDARY) -> np.ndarray:
    """Benjamini-Hochberg step-up mask over one family, controlling FDR at `q`.

    Thin wrapper over ``statsmodels.stats.multitest.multipletests`` with
    ``method="fdr_bh"``. BH controls the false discovery rate -- the expected
    share of rejections that are null -- at `q`, not the familywise rate,
    and that weaker guarantee is the pre-registered choice for the
    SECONDARY (Tier 3) family only; the PRIMARY family stays on `holm`.

    `q` defaults to `Q_SECONDARY`, imported from ``power_analysis`` (which
    owns the SECONDARY tier's level) rather than re-spelled as a literal, so
    a re-registration of the tier cannot move `ALPHA_SECONDARY` while
    leaving this default behind.

    Parameters
    ----------
    pvals : np.ndarray
        P-values in the family.
    q : float, optional
        False discovery-rate level.

    Returns
    -------
    np.ndarray
        Rejection mask.
    """
    # Same tie argument as `holm`: q*i/m is monotone increasing in rank, so a
    # tied group cannot straddle the accept/reject boundary and the unstable
    # sort cannot move the rejection set.
    reject, _pvals_corrected, _alphac_sidak, _alphac_bonf = multipletests(
        pvals, alpha=q, method="fdr_bh"
    )
    return np.asarray(reject, dtype=bool)


def design_effect(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float | None:
    """Observed / independence-assumed variance of the per-seed arm difference.

    The cross-stratum covariance term the CMH denominator omits: >1 means
    the denominator is too small (anticonservative), <1 too large. ``None``
    uniformly means "no measurable ratio" (fewer than 3 seeds, identical
    arms, or a stratum too thin for ddof=1), so a NaN never slips past an
    ``is not None`` filter.

    Parameters
    ----------
    a : np.ndarray
        First arm's matched marks.
    b : np.ndarray
        Second arm's matched marks.
    seed_idx : np.ndarray
        Replicate index for each matched mark.

    Returns
    -------
    float | None
        Observed / independence-assumed variance ratio, or ``None`` when no.
        measurable ratio exists.
    """
    d = a.astype(float) - b.astype(float)
    seeds = np.unique(seed_idx)
    if seeds.size < 3:
        return None
    order = np.concatenate([np.arange((seed_idx == s).sum()) for s in seeds])
    per_seed_total = np.array([d[seed_idx == s].sum() for s in seeds])
    observed = per_seed_total.var(ddof=1)
    assumed = float(np.sum([d[order == k].var(ddof=1) for k in np.unique(order)]))
    if not np.isfinite(assumed) or assumed <= 0:
        return None
    return float(observed / assumed)


def main() -> None:
    """Run the paired re-analysis and print the report.

    Over the 210-contrast PRIMARY family, for both the pre-registered pass
    (null == incorrect) and a DROP-INVALID sensitivity pass: rejection counts
    for unpaired CMH, paired McNemar and (pre-registered pass only) seed
    sign-flip; contrasts that change status under pairing; the standing
    intens-vs-noise question per model; the design-effect summary. Then
    SECONDARY (Benjamini-Hochberg) discoveries under both tests.
    """
    print("Loading marks ...", flush=True)
    # The compliance view is unused here (this report makes no census); still
    # loaded, one parse three views, for significance_report's benefit.
    correct, valid, _compliance = load_marks()
    depths = {k: len(v) for k, v in correct.items()}
    print(
        f"  {len(correct)} conditions; replicate depth "
        f"min={min(depths.values())} max={max(depths.values())}"
    )
    short = sorted({m for (m, _), n in depths.items() if n < max(depths.values())})
    if short:
        print(f"  still collecting (compared on their common seeds only): {short}")
    # Gates on the SHALLOWEST lane, not `max`: a contrast is sign-flipped over
    # the seeds its two arms share, so its resolution floor 2/2^S is set by
    # the shorter arm, and gating on `max` would let one full-depth lane
    # suppress this warning for every short lane beside it. Both ends of the
    # spread are reported, so a uniform shortfall (invisible to `short` above)
    # can be told apart from a ragged one.
    if min(depths.values()) < EXPECTED_R:
        print(
            f"  WARNING: shallowest lane has {min(depths.values())} replicates "
            f"and the deepest has {max(depths.values())}, but the study "
            f"collects {EXPECTED_R}. A contrast is only as deep as its shorter "
            f"arm, so the sign-flip floor reaches 2/2^{min(depths.values())} "
            f"and Holm may be unable to reject ANYTHING (including the positive "
            f"controls) on the contrasts that touch a short lane. This is an "
            f"incomplete sync, not a null result.",
            file=sys.stderr,
        )

    contrasts = build_primary_contrasts()
    if len(contrasts) != N_PRIMARY:
        # Not a restatement of power_analysis.check_design_invariants (already
        # run at import): this guards the LOCAL list driving the row loop
        # below, whose Bonferroni columns divide ALPHA by N_PRIMARY rather
        # than len(contrasts). A raise, not an assert, so it survives python -O.
        raise RuntimeError(
            f"build_primary_contrasts() returned {len(contrasts)} contrasts "
            f"but N_PRIMARY is {N_PRIMARY}. This report's Bonferroni columns "
            f"are taken at ALPHA/N_PRIMARY and its Holm passes are sized by "
            f"the length of this list, so a mismatch means every correction "
            f"printed below was computed at the wrong threshold."
        )

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
            # Cluster test only on the pre-registered pass: dropping invalid
            # pairs makes the per-seed sum a sum over a VARIABLE number of
            # items, i.e. a different statistic.
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

    print(
        f"\n{'=' * 78}\nSECONDARY family ({len(sec)} cross-family size-matched "
        f"contrasts, intens only), Benjamini-Hochberg q=0.05\n{'=' * 78}\n"
        f"  unpaired CMH   : {bh(p_unp_s).sum():3d} discoveries\n"
        f"  paired McNemar : {bh(p_pair_s).sum():3d} discoveries"
    )


if __name__ == "__main__":
    main()
