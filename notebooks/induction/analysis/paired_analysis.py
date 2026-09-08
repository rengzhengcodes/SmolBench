"""Paired re-analysis of the family-ladder induction study.

Seed-level sign-flips carry inference because items share seeds; CMH and McNemar are comparisons.
"""

import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

# Required when loaded by path rather than as ``__main__``.
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
    cmh_stat,
    # Descriptive only: inference uses seed-level sign-flips.
    mcnemar_exact_p,
)

#: Absolute depth detects uniform shortfalls that raise the sign-flip floor.
EXPECTED_R = 30


def load_marks() -> tuple[dict, dict, dict]:
    """Read replicates into per-condition maps.

    One parse supplies all views so reports cannot disagree about a replicate.

    Raises
    ------
    SystemExit
        If a condition has no replicate seeds.
    """
    correct: dict = {}
    valid: dict = {}
    compliance: dict = {}
    store = LocalResultsStore(RESULTS_DIR)
    for model in MODELS:
        for info in INFOS:
            # Local storage keys by tag; model is unused.
            def addr_of(seed: int, _m: str = model, _i: str = info) -> ReplicateAddress:
                """Address the current cell's replicate.

                Defaults prevent capture of a later loop cell.

                Parameters
                ----------
                seed : int
                    Seed.
                _m : str, optional
                    Current model.
                _i : str, optional
                    Current info value.

                Returns
                -------
                ReplicateAddress
                    Replicate address.
                """
                return ReplicateAddress(tag=_m, info=_i, seed=seed)

            seeds = store.list_seeds(None, model, info)
            if not seeds:
                # Gate on seeds: missing and empty lanes both lack usable data.
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
                # Reuse one load for every view.
                marks = store.load_marks(addr_of(seed)).marks
                scores = [m.score for m in marks]
                if len(scores) != N_HARMONICS:
                    # Skip partial replicates to preserve harmonic alignment.
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
    """Build item-matched vectors for one contrast.

    Parameters
    ----------
    correct : dict
        Per-cell correct-mark mappings.
    valid : dict
        Per-cell valid-mark mappings.
    key_a : tuple[str, str]
        First cell.
    key_b : tuple[str, str]
        Second cell.
    drop_invalid : bool
        Drop pairs with invalid marks.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Matched marks and replicate indices.
    """
    seeds = sorted(set(correct[key_a]) & set(correct[key_b]))
    if not seeds:
        # Empty overlap is a data failure, not a NumPy error.
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
    """Return one arm difference per seed.

    Parameters
    ----------
    a : np.ndarray
        First-arm marks.
    b : np.ndarray
        Second-arm marks.
    seed_idx : np.ndarray
        Replicate indices.

    Returns
    -------
    list[int]
        Arm differences.
    """
    a_i, b_i = a.astype(np.int64), b.astype(np.int64)
    return [
        int(a_i[seed_idx == s].sum() - b_i[seed_idx == s].sum())
        for s in np.unique(seed_idx)
    ]


def signflip_exact_p(diffs: Iterable[int]) -> float:
    """Compute an exact seed-level two-sided sign-flip p-value.

    Seeds, not marks, are independent because harmonic items share a seed.

    Parameters
    ----------
    diffs : Iterable[int]
        Per-seed differences.

    Returns
    -------
    float
        Exact p-value; 1.0 for empty input.
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
    """Compute continuity-corrected CMH p-value by harmonic stratum.

    Parameters
    ----------
    a : np.ndarray
        First-arm marks.
    b : np.ndarray
        Second-arm marks.
    seed_idx : np.ndarray
        Replicate indices.

    Returns
    -------
    float
        P-value; 1.0 with no contributing stratum.
    """
    # Invalid drops can shift harmonic offsets but preserve pairing.
    order = np.concatenate([np.arange((seed_idx == s).sum()) for s in np.unique(seed_idx)])
    strata = np.unique(order)
    if strata.size == 0:
        return 1.0
    counts = np.array([(order == k).sum() for k in strata])
    succ_a = np.array([a[order == k].sum() for k in strata])
    succ_b = np.array([b[order == k].sum() for k in strata])
    return float(chi2.sf(cmh_stat(succ_a, succ_b, counts), df=1))


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Return Holm's FWER rejection mask.

    Holm permits arbitrary dependence among shared models, seeds, and harmonics.

    Parameters
    ----------
    pvals : np.ndarray
        Family p-values.
    alpha : float, optional
        FWER level.

    Returns
    -------
    np.ndarray
        Rejection mask.
    """
    # Monotone thresholds make unstable ordering of ties harmless.
    reject, _pvals_corrected, _alphac_sidak, _alphac_bonf = multipletests(
        pvals, alpha=alpha, method="holm"
    )
    return np.asarray(reject, dtype=bool)


def bh(pvals: np.ndarray, q: float = Q_SECONDARY) -> np.ndarray:
    """Return Benjamini-Hochberg FDR rejection mask.

    The imported default keeps this secondary-tier level owned by power_analysis.

    Parameters
    ----------
    pvals : np.ndarray
        Family p-values.
    q : float, optional
        FDR level.

    Returns
    -------
    np.ndarray
        Rejection mask.
    """
    # Monotone thresholds make unstable ordering of ties harmless.
    reject, _pvals_corrected, _alphac_sidak, _alphac_bonf = multipletests(
        pvals, alpha=q, method="fdr_bh"
    )
    return np.asarray(reject, dtype=bool)


def design_effect(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> float | None:
    """Return observed over independence-assumed variance.

    ``None`` represents every unmeasurable case, preventing NaNs from passing filters.

    Parameters
    ----------
    a : np.ndarray
        First-arm marks.
    b : np.ndarray
        Second-arm marks.
    seed_idx : np.ndarray
        Replicate indices.

    Returns
    -------
    float | None
        Variance ratio or ``None``.
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
    """Run the paired re-analysis report."""
    print("Loading marks ...", flush=True)
    # Load all views from one parse for the census consumer.
    correct, valid, _compliance = load_marks()
    depths = {k: len(v) for k, v in correct.items()}
    print(
        f"  {len(correct)} conditions; replicate depth "
        f"min={min(depths.values())} max={max(depths.values())}"
    )
    short = sorted({m for (m, _), n in depths.items() if n < max(depths.values())})
    if short:
        print(f"  still collecting (compared on their common seeds only): {short}")
    # The shallowest lane sets each shared-seed sign-flip resolution floor.
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
        # This local list sets correction denominators and must survive ``-O``.
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
            # Dropping invalid pairs changes the per-seed statistic.
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
