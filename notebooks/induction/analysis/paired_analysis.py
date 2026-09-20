"""Paired re-analysis of the family-ladder induction study.

Seed-level sign-flips carry inference because items share seeds; CMH and McNemar are comparisons.
"""

import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# Required when loaded by path rather than as ``__main__``.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import apply_corrections
from power_analysis import (  # noqa: E402
    ALPHA,
    BASE_SEED,
    INFOS,
    MODELS,
    N_HARMONICS,
    N_PRIMARY,
    N_REPLICATES,
    Q_SECONDARY,
    RESULTS_DIR,
    build_primary_contrasts,
    build_secondary_contrasts,
    cmh_stat,
    mcnemar_exact_p,
)
from scipy.stats import chi2

from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress


@dataclass(frozen=True)
class CellMarks:
    """One map per `(model, info)` cell keyed by seed."""

    correct: dict[tuple[str, str], dict[int, np.ndarray]]
    valid: dict[tuple[str, str], dict[int, np.ndarray]]
    compliance: dict[tuple[str, str], dict[int, tuple[str, ...]]]


def load_marks(results_dir: Path = RESULTS_DIR) -> CellMarks:
    """Read replicates into per-condition maps.

    One parse supplies all views so reports cannot disagree about a replicate.

    Raises
    ------
    SystemExit
        If a condition yields no replicate seeds at all.
    """
    correct: dict[tuple[str, str], dict[int, np.ndarray]] = {}
    valid: dict[tuple[str, str], dict[int, np.ndarray]] = {}
    compliance: dict[tuple[str, str], dict[int, tuple[str, ...]]] = {}
    store = LocalResultsStore(results_dir)
    expected = set(range(BASE_SEED, BASE_SEED + N_REPLICATES))
    for model in MODELS:
        for info in INFOS:
            seeds = store.list_seeds(None, model, info)
            if not seeds:
                # Gate on seeds: missing and empty lanes both lack usable data.
                cdir = store.path(
                    ReplicateAddress(tag=model, info=info, seed=BASE_SEED)
                ).parent
                raise SystemExit(
                    f"No replicates for ({model}, {info}); no rep_{{seed}}.yaml "
                    f"files in\n  {cdir}\nCall "
                    "InductionExperiment.harness.sync_down() first."
                )
            unexpected = sorted(set(seeds) - expected)
            if unexpected:
                lane = store.path(
                    ReplicateAddress(tag=model, info=info, seed=unexpected[0])
                ).parent
                raise SystemExit(
                    f"Unexpected replicate seeds in {lane}: {unexpected}; "
                    f"expected {min(expected)}–{max(expected)}"
                )
            c_by_seed, v_by_seed, k_by_seed = {}, {}, {}
            for seed in seeds:
                # Reuse one load for every view.
                addr = ReplicateAddress(tag=model, info=info, seed=seed)
                path = store.path(addr)
                marks = store.load_marks(addr).marks
                scores = [m.score for m in marks]
                if len(scores) != N_HARMONICS:
                    raise SystemExit(
                        f"Replicate {path} has {len(scores)} marks, expected "
                        f"{N_HARMONICS}; collection failed"
                    )
                c_by_seed[seed] = np.array([s == 1 for s in scores])
                v_by_seed[seed] = np.array([s is not None for s in scores])
                k_by_seed[seed] = tuple(m.compliance for m in marks)
            correct[(model, info)] = c_by_seed
            valid[(model, info)] = v_by_seed
            compliance[(model, info)] = k_by_seed
    return CellMarks(correct, valid, compliance)


def aligned(
    marks: CellMarks,
    key_a: tuple[str, str],
    key_b: tuple[str, str],
    drop_invalid: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build item-matched vectors for one contrast.

    ``drop_invalid`` drops item-pairs where either arm's mark is invalid
    (``score: null``). Returns matched correct-a, correct-b, seed-index and
    harmonic-index arrays.
    """
    seeds = sorted(set(marks.correct[key_a]) & set(marks.correct[key_b]))
    if not seeds:
        # Empty overlap is a data failure, not a NumPy error.
        raise SystemExit(
            f"No common seeds between {key_a} and {key_b}; one lane has no "
            "usable replicates -- re-run sync_down()."
        )
    a = np.array([marks.correct[key_a][s] for s in seeds])
    b = np.array([marks.correct[key_b][s] for s in seeds])
    keep = np.ones_like(a, dtype=bool)
    if drop_invalid:
        keep = np.array([marks.valid[key_a][s] for s in seeds]) & np.array(
            [marks.valid[key_b][s] for s in seeds]
        )
    seed_idx = np.repeat(np.arange(len(seeds)), N_HARMONICS).reshape(a.shape)
    # Carry the harmonic through the mask: a survivor's position is unrecoverable from the retained count.
    harm_idx = np.tile(np.arange(N_HARMONICS), (len(seeds), 1))
    return a[keep], b[keep], seed_idx[keep], harm_idx[keep]


def seed_diffs(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> list[int]:
    """Return one arm difference (a minus b) per unique seed in ``seed_idx``."""
    a_i, b_i = a.astype(np.int64), b.astype(np.int64)
    return [
        int(a_i[seed_idx == s].sum() - b_i[seed_idx == s].sum())
        for s in np.unique(seed_idx)
    ]


def signflip_exact_p(diffs: Iterable[int]) -> float:
    """Compute an exact seed-level two-sided sign-flip p-value.

    Seeds, not marks, are independent because harmonic items share a seed.
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


def cmh_unpaired_p(a: np.ndarray, b: np.ndarray, harm_idx: np.ndarray) -> float:
    """Return the repo's continuity-corrected 2x2xK CMH p-value, stratified by harmonic."""
    strata = np.unique(harm_idx)
    if strata.size == 0:
        return 1.0
    counts = np.array([(harm_idx == k).sum() for k in strata])
    succ_a = np.array([a[harm_idx == k].sum() for k in strata])
    succ_b = np.array([b[harm_idx == k].sum() for k in strata])
    return float(chi2.sf(cmh_stat(succ_a, succ_b, counts), df=1))


def rejection_mask(pvals: np.ndarray, level: float, method: str) -> np.ndarray:
    """Return one `apply_corrections` mask for a single family of p-values."""
    return apply_corrections(np.atleast_2d(np.asarray(pvals, float)), level)[method][0]


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Return Holm's FWER rejection mask.

    Holm permits arbitrary dependence among shared models, seeds, and harmonics.
    """
    return rejection_mask(pvals, alpha, "Holm")


def bh(pvals: np.ndarray, q: float = Q_SECONDARY) -> np.ndarray:
    """Return the Benjamini-Hochberg FDR rejection mask.

    The imported default keeps this secondary-tier level owned by power_analysis.
    """
    return rejection_mask(pvals, q, "BH")


def design_effect(
    a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray, harm_idx: np.ndarray
) -> float | None:
    """Return observed over independence-assumed variance.

    ``None`` represents every unmeasurable case, preventing NaNs from passing filters.
    """
    d = a.astype(float) - b.astype(float)
    seeds = np.unique(seed_idx)
    if seeds.size < 3:
        return None
    per_seed_total = np.array([d[seed_idx == s].sum() for s in seeds])
    observed = per_seed_total.var(ddof=1)
    assumed = float(np.sum([d[harm_idx == k].var(ddof=1) for k in np.unique(harm_idx)]))
    if not np.isfinite(assumed) or assumed <= 0:
        return None
    return float(observed / assumed)


def contrast_row(
    marks: CellMarks,
    key_a: tuple[str, str],
    key_b: tuple[str, str],
    drop_invalid: bool = False,
) -> dict:
    """Compute every paired statistic the reports share for one contrast.

    ``drop_invalid`` is forwarded to `aligned`; dropping pairs changes the
    per-seed statistic, so ``p_cluster`` is ``None`` in that mode. Returns
    ``key_a``, ``key_b``, ``n``, ``acc_a``, ``acc_b``, ``b``, ``c``, ``disc``,
    ``seeds`` (sorted common seeds), ``n_seeds``, ``p_item`` (exact McNemar),
    ``p_unpaired`` (harmonic-stratified CMH), ``p_cluster`` (seed sign-flip)
    and ``de`` (`design_effect`).
    """
    a, b, sidx, hidx = aligned(marks, key_a, key_b, drop_invalid)
    nb, nc = int((a & ~b).sum()), int((~a & b).sum())
    return {
        "key_a": key_a,
        "key_b": key_b,
        "n": a.size,
        "acc_a": float(a.mean()) if a.size else None,
        "acc_b": float(b.mean()) if b.size else None,
        "b": nb,
        "c": nc,
        "disc": (nb + nc) / max(a.size, 1),
        "seeds": sorted(set(marks.correct[key_a]) & set(marks.correct[key_b])),
        "n_seeds": int(np.unique(sidx).size),
        "p_item": mcnemar_exact_p(nb, nc),
        "p_unpaired": cmh_unpaired_p(a, b, hidx),
        "p_cluster": None if drop_invalid else signflip_exact_p(seed_diffs(a, b, sidx)),
        "de": design_effect(a, b, sidx, hidx),
    }


def labeled_rows(
    marks: CellMarks, contrasts: Iterable[tuple], drop_invalid: bool = False
) -> list[dict]:
    """Return one `contrast_row` per ``(label, key_a, key_b)``, with its label."""
    return [
        {"label": label, **contrast_row(marks, key_a, key_b, drop_invalid)}
        for label, key_a, key_b in contrasts
    ]


def _acc(x: float | None) -> str:
    """Format an accuracy, including an empty-comparison marker."""
    return "  n/a" if x is None else f"{x:.3f}"


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Run the paired re-analysis report."""
    print("Loading marks ...", flush=True)
    marks = load_marks(results_dir)
    depths = {k: len(v) for k, v in marks.correct.items()}
    print(
        f"  {len(marks.correct)} conditions; replicate depth "
        f"min={min(depths.values())} max={max(depths.values())}"
    )
    short = sorted({m for (m, _), n in depths.items() if n < max(depths.values())})
    if short:
        print(f"  still collecting (compared on their common seeds only): {short}")
    # The shallowest lane sets each shared-seed sign-flip resolution floor.
    if min(depths.values()) < N_REPLICATES:
        print(
            f"  WARNING: shallowest lane has {min(depths.values())} replicates "
            f"and the deepest has {max(depths.values())}, but the study "
            f"collects {N_REPLICATES}. A contrast is only as deep as its shorter "
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
            f"but N_PRIMARY is {N_PRIMARY}; every correction below would be "
            "sized at the wrong threshold."
        )

    for drop_invalid in (False, True):
        tag = (
            "DROP-INVALID pairs"
            if drop_invalid
            else "null == incorrect (pre-registered)"
        )
        print(f"\n{'=' * 78}\nPRIMARY family, {tag}\n{'=' * 78}")
        rows = labeled_rows(marks, contrasts, drop_invalid)

        p_pair = np.array([r["p_item"] for r in rows])
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
            des = np.array([r["de"] for r in rows if r["de"] is not None])
            frac_pos = f"{(des > 1.0).mean():.0%}" if des.size else "n/a"
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
                f"(item-level p is anticonservative where the seed x arm "
                f"interaction is positive: {frac_pos} of measurable contrasts here)"
            )
        gained = [r for r, gp, gu in zip(rows, rej_pair, rej_unp) if gp and not gu]
        lost = [r for r, gp, gu in zip(rows, rej_pair, rej_unp) if gu and not gp]
        print(
            f"  => pairing changes status on {len(gained) + len(lost)} contrasts "
            f"(+{len(gained)} gained, -{len(lost)} lost)"
        )
        for word, sel, key in (
            ("GAINED", gained, "p_item"),
            ("LOST  ", lost, "p_unpaired"),
        ):
            for r in sorted(sel, key=lambda r: r[key])[:20]:
                print(
                    f"    {word} {r['label']:52s} {_acc(r['acc_a']):>7s} vs "
                    f"{_acc(r['acc_b']):>7s}  "
                    f"disc={r['disc']:.3f}  p_pair={r['p_item']:.2e}  "
                    f"p_unpair={r['p_unpaired']:.2e}"
                )

        if not drop_invalid:
            # --- the standing question: does intens ever separate from noise? --
            hdr = (
                f"  {'model':14s} {'intens':>7s} {'noise':>7s} {'disc':>7s} "
                f"{'b/c':>9s} {'p_paired':>10s} {'p_unpaired':>11s} "
                f"{'p_signflip':>11s}"
            )
            print(
                "\nStanding question -- intens vs noise_intens, per model "
                f"(no prior study ever separated these):\n{hdr}\n  "
                + "-" * (len(hdr) - 2)
            )
            for r in rows:
                if {r["key_a"][1], r["key_b"][1]} != {"intens", "noise_intens"}:
                    continue
                model = r["key_a"][0]
                flag = ""
                if r["p_cluster"] <= ALPHA / N_PRIMARY:
                    flag = "  <== SEPARATES (Bonferroni)"
                elif r["p_cluster"] <= ALPHA:
                    flag = "  <== p<0.05 uncorrected"
                print(
                    f"  {model:14s} {r['acc_a']:7.3f} {r['acc_b']:7.3f} "
                    f"{r['disc']:7.3f} {r['b']:4d}/{r['c']:<4d} "
                    f"{r['p_item']:10.2e} {r['p_unpaired']:11.2e} "
                    f"{r['p_cluster']:11.2e}{flag}"
                )

            # --- clustering sign ---
            if des.size == 0:
                print(
                    "Clustering / cross-stratum covariance: no measurable PRIMARY "
                    "contrasts (every contrast has zero independence-assumed "
                    "variance), so no design effect is reported."
                )
            else:
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
    sec_rows = labeled_rows(marks, sec)
    n_disc = {
        k: bh(np.array([r[k] for r in sec_rows])).sum()
        for k in ("p_cluster", "p_unpaired", "p_item")
    }

    print(
        f"\n{'=' * 78}\nSECONDARY family ({len(sec)} cross-family size-matched "
        f"contrasts, intens only), Benjamini-Hochberg q=0.05\n{'=' * 78}\n"
        f"  seed sign-flip (inferential) : {n_disc['p_cluster']:3d} discoveries\n"
        f"  unpaired CMH (descriptive)   : {n_disc['p_unpaired']:3d} discoveries\n"
        f"  paired McNemar (descriptive) : {n_disc['p_item']:3d} discoveries"
    )


if __name__ == "__main__":
    main()
