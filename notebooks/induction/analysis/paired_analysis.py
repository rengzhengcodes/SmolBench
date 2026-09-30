"""Paired re-analysis of the family-ladder induction study.

Seed-level sign-flips carry inference because items share seeds; CMH and McNemar are comparisons.
Also owns the parsed-marks views (`CellMarks`) and the compliance census both later reports read.
"""

import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from operator import itemgetter
from pathlib import Path
from typing import Optional

# Bare-name imports: sibling scripts from this directory, ``_power_common`` from ``notebooks/``.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import ALPHA, apply_corrections
from study_design import (
    ALPHA_PRIMARY,
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
    cmh_p,
    mcnemar_exact_p,
)

from smolbench.evals.quiz import COMPLIANT
from smolbench.evals.results_store import LocalResultsStore, ReplicateAddress

#: ``(model, info)`` naming one condition lane.
CellKey = tuple[str, str]

#: Longest GAINED/LOST listing per block; the count line above each block carries the totals.
MAX_LISTED = 20


@dataclass(frozen=True)
class CellMarks:
    """Three views of the parsed marks, each keyed ``(model, info)`` then seed."""

    correct: dict[CellKey, dict[int, np.ndarray]]
    valid: dict[CellKey, dict[int, np.ndarray]]
    compliance: dict[CellKey, dict[int, tuple[str, ...]]]


def load_marks(results_dir: Path = RESULTS_DIR) -> CellMarks:
    """Read replicates into per-condition maps.

    One parse supplies all views so reports cannot disagree about a replicate.

    Parameters
    ----------
    results_dir : Path, optional
        Root of the synced ``<model>_<info>/rep_<seed>.yaml`` tree.

    Returns
    -------
    CellMarks
        Correct, valid, and compliance maps for every roster cell.

    Raises
    ------
    SystemExit
        If a lane has no replicate seeds, an unexpected seed, or a replicate
        without exactly ``N_HARMONICS`` marks.
    """
    views = CellMarks({}, {}, {})
    store = LocalResultsStore(results_dir)
    expected = set(range(BASE_SEED, BASE_SEED + N_REPLICATES))
    for model in MODELS:
        for info in INFOS:
            seeds = store.list_seeds(None, model, info)
            lane = store.path(
                ReplicateAddress(tag=model, info=info, seed=BASE_SEED)
            ).parent
            if not seeds:
                # Gate on seeds: missing and empty lanes both lack usable data.
                raise SystemExit(
                    f"No replicates for ({model}, {info}); no rep_{{seed}}.yaml "
                    f"files in\n  {lane}\nCall "
                    "InductionExperiment.harness.sync_down() first."
                )
            unexpected = sorted(set(seeds) - expected)
            if unexpected:
                raise SystemExit(
                    f"Unexpected replicate seeds in {lane}: {unexpected}; "
                    f"expected {min(expected)}–{max(expected)}"
                )
            cell = (model, info)
            views.correct[cell], views.valid[cell], views.compliance[cell] = {}, {}, {}
            for seed in seeds:
                # Reuse one load for every view.
                addr = ReplicateAddress(tag=model, info=info, seed=seed)
                marks = store.load_marks(addr).marks
                scores = [m.score for m in marks]
                if len(scores) != N_HARMONICS:
                    raise SystemExit(
                        f"Replicate {store.path(addr)} has {len(scores)} marks, "
                        f"expected {N_HARMONICS}; collection failed"
                    )
                views.correct[cell][seed] = np.array([s == 1 for s in scores])
                views.valid[cell][seed] = np.array([s is not None for s in scores])
                views.compliance[cell][seed] = tuple(m.compliance for m in marks)
    return views


#: Non-compliance rate at or above which a census cell counts as collapsed; both reports annotate at it.
COLLAPSE_THRESHOLD = 0.25
#: The criterion as the reports print it.
COLLAPSE_CRITERION = f"{COLLAPSE_THRESHOLD:.0%}"


def compliance_census(marks: CellMarks) -> dict:
    """Measure non-compliance per parsed ``(model, info)`` cell.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `load_marks`.

    Returns
    -------
    dict
        Cell key -> ``rate`` (pooled non-compliance), ``n`` (marks), ``modes``
        (`Counter` of non-compliant labels) and ``per_seed``
        (seed -> ``(non_compliant, total)``), skipping cells without marks.
    """
    out = {}
    for key, by_seed in marks.compliance.items():
        per_seed = {
            seed: (sum(v != COMPLIANT for v in vals), len(vals))
            for seed, vals in by_seed.items()
        }
        n = sum(t for _nc, t in per_seed.values())
        if not n:
            continue
        out[key] = {
            "rate": sum(nc for nc, _t in per_seed.values()) / n,
            "n": n,
            "modes": Counter(
                v for vals in by_seed.values() for v in vals if v != COMPLIANT
            ),
            "per_seed": per_seed,
        }
    return out


def common_seed_rate(cell: dict, seeds: Iterable[int]) -> Optional[float]:
    """Return a census cell's non-compliance rate over ``seeds``.

    Pool counts before division so unequal seed sizes retain their weight.

    Parameters
    ----------
    cell : dict
        Census entry for one cell.
    seeds : Iterable[int]
        Replicate seeds to include.

    Returns
    -------
    Optional[float]
        ``None`` when the subset has no marks; otherwise its non-compliance rate.
    """
    counts = [cell["per_seed"][s] for s in seeds if s in cell["per_seed"]]
    total = sum(t for _nc, t in counts)
    if total == 0:
        return None
    return sum(nc for nc, _t in counts) / total


def common_seeds(marks: CellMarks, *keys: CellKey) -> list[int]:
    """Sorted replicate seeds every one of `keys` carries.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `load_marks`.
    *keys : CellKey
        Cells to intersect; at least one.

    Returns
    -------
    list[int]
        Seeds present in every cell, ascending.
    """
    return sorted(set.intersection(*(set(marks.correct[k]) for k in keys)))


def aligned(
    marks: CellMarks, key_a: CellKey, key_b: CellKey, drop_invalid: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build item-matched vectors for one contrast.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `load_marks`.
    key_a, key_b : CellKey
        The two cells being compared.
    drop_invalid : bool
        Drops item-pairs where either arm's mark is invalid (``score: null``).

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        Matched correct marks of each arm, then seed-index and harmonic-index arrays.

    Raises
    ------
    SystemExit
        If the two cells share no replicate seed.
    """
    seeds = common_seeds(marks, key_a, key_b)
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
        keep = np.array([marks.valid[key_a][s] & marks.valid[key_b][s] for s in seeds])
    # Carry the harmonic through the mask: a survivor's position is unrecoverable
    # from the retained count.
    seed_idx, harm_idx = np.indices(a.shape)
    return a[keep], b[keep], seed_idx[keep], harm_idx[keep]


def seed_diffs(a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray) -> list[int]:
    """Return one arm difference per seed.

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
    d = a.astype(np.int64) - b.astype(np.int64)
    return [int(d[seed_idx == s].sum()) for s in np.unique(seed_idx)]


def signflip_exact_p(diffs: Iterable[int]) -> float:
    """Compute an exact seed-level two-sided sign-flip p-value.

    Seeds, not marks, are independent because harmonic items share a seed.

    Parameters
    ----------
    diffs : Iterable[int]
        Per-seed arm differences.

    Returns
    -------
    float
        Exact two-sided sign-flip p-value.
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
    """Compute continuity-corrected CMH p-value by harmonic stratum.

    Parameters
    ----------
    a : np.ndarray
        First arm's matched marks.
    b : np.ndarray
        Second arm's matched marks.
    harm_idx : np.ndarray
        Harmonic index for each matched mark.

    Returns
    -------
    float
        P-value of the repo's continuity-corrected 2x2xK CMH.
    """
    strata = np.unique(harm_idx)
    if strata.size == 0:
        return 1.0
    counts = np.array([(harm_idx == k).sum() for k in strata])
    succ_a = np.array([a[harm_idx == k].sum() for k in strata])
    succ_b = np.array([b[harm_idx == k].sum() for k in strata])
    return float(cmh_p(succ_a, succ_b, counts))


def rejections(pvals: np.ndarray, method: str, level: float = ALPHA) -> np.ndarray:
    """Return one family's `apply_corrections` rejection mask.

    ``"Holm"`` (PRIMARY) permits arbitrary dependence among shared models, seeds and
    harmonics; ``"Hochberg"`` is sensitivity-only, its positive-dependence condition
    unverified; ``"BH"`` controls FDR and takes the `Q_SECONDARY` level owned by
    power_analysis.

    Parameters
    ----------
    pvals : np.ndarray
        P-values in the family.
    method : str
        ``"Holm"``, ``"Hochberg"``, ``"Bonferroni"`` or ``"BH"``.
    level : float, optional
        Familywise error rate, or the false-discovery rate for ``"BH"``.

    Returns
    -------
    np.ndarray
        Rejection mask in input order.
    """
    return apply_corrections(np.atleast_2d(np.asarray(pvals, float)), level)[method][0]


def design_effect(
    a: np.ndarray, b: np.ndarray, seed_idx: np.ndarray, harm_idx: np.ndarray
) -> Optional[float]:
    """Return observed over independence-assumed variance.

    ``None`` represents every unmeasurable case, preventing NaNs from passing filters.

    Parameters
    ----------
    a : np.ndarray
        First arm's matched marks.
    b : np.ndarray
        Second arm's matched marks.
    seed_idx : np.ndarray
        Replicate index for each matched mark.
    harm_idx : np.ndarray
        Harmonic index for each matched mark.

    Returns
    -------
    Optional[float]
        Observed / independence-assumed variance ratio.
    """
    diffs = seed_diffs(a, b, seed_idx)
    # A two-seed variance has one degree of freedom: the ratio would be noise,
    # not a measurement, so it is reported as unmeasurable.
    if len(diffs) < 3:
        return None
    observed = np.var(diffs, ddof=1)
    d = a.astype(float) - b.astype(float)
    assumed = float(np.sum([d[harm_idx == k].var(ddof=1) for k in np.unique(harm_idx)]))
    if not np.isfinite(assumed) or assumed <= 0:
        return None
    return float(observed / assumed)


def labeled_rows(
    marks: CellMarks, contrasts: Iterable[tuple], drop_invalid: bool = False
) -> list[dict]:
    """Compute every paired statistic the reports share, one row per contrast.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `load_marks`.
    contrasts : Iterable[tuple]
        ``(label, key_a, key_b)`` triples as built by `build_primary_contrasts`.
    drop_invalid : bool, optional
        Forwarded to `aligned`. Dropping pairs changes the per-seed statistic,
        so ``p_cluster`` is ``None`` in that mode.

    Returns
    -------
    list[dict]
        Per contrast: ``label``, ``key_a``, ``key_b``, ``n``, ``acc_a``, ``acc_b``,
        ``b``, ``c``, ``disc``, ``seeds`` (sorted common seeds), ``n_seeds``,
        ``p_item`` (exact McNemar), ``p_unpaired`` (harmonic-stratified CMH),
        ``p_cluster`` (seed sign-flip) and ``de`` (`design_effect`).
    """
    rows = []
    for label, key_a, key_b in contrasts:
        a, b, sidx, hidx = aligned(marks, key_a, key_b, drop_invalid)
        nb, nc = int((a & ~b).sum()), int((~a & b).sum())
        rows.append(
            {
                "label": label,
                "key_a": key_a,
                "key_b": key_b,
                "n": a.size,
                "acc_a": float(a.mean()) if a.size else None,
                "acc_b": float(b.mean()) if b.size else None,
                "b": nb,
                "c": nc,
                "disc": (nb + nc) / max(a.size, 1),
                "seeds": common_seeds(marks, key_a, key_b),
                "n_seeds": int(np.unique(sidx).size),
                "p_item": mcnemar_exact_p(nb, nc),
                "p_unpaired": cmh_unpaired_p(a, b, hidx),
                "p_cluster": (
                    None if drop_invalid else signflip_exact_p(seed_diffs(a, b, sidx))
                ),
                "de": design_effect(a, b, sidx, hidx),
            }
        )
    return rows


def _acc(x: Optional[float]) -> str:
    """Format an accuracy, including an empty-comparison marker."""
    return "  n/a" if x is None else f"{x:.3f}"


def _print_depth(marks: CellMarks) -> None:
    """Print replicate depth per lane and the incomplete-sync warning."""
    depths = {k: len(v) for k, v in marks.correct.items()}
    shallow, deep = min(depths.values()), max(depths.values())
    print(f"  {len(depths)} conditions; replicate depth min={shallow} max={deep}")
    short = sorted({m for (m, _), n in depths.items() if n < deep})
    if short:
        print(f"  still collecting (compared on their common seeds only): {short}")
    # The shallowest lane sets each shared-seed sign-flip resolution floor.
    if shallow < N_REPLICATES:
        print(
            f"  WARNING: shallowest lane has {shallow} replicates "
            f"and the deepest has {deep}, but the study "
            f"collects {N_REPLICATES}. A contrast is only as deep as its shorter "
            f"arm, so the sign-flip floor reaches 2/2^{shallow} "
            f"and Holm may be unable to reject ANYTHING (including the positive "
            f"controls) on the contrasts that touch a short lane. This is an "
            f"incomplete sync, not a null result.",
            file=sys.stderr,
        )


def _print_standing_question(rows: list[dict], rej_cl: np.ndarray) -> None:
    """Print the intens-vs-noise_intens row per model.

    Each row is flagged by the Holm (PRIMARY) decision in `rej_cl`.
    """
    hdr = (
        f"  {'model':14s} {'intens':>7s} {'noise':>7s} {'disc':>7s} "
        f"{'b/c':>9s} {'p_paired':>10s} {'p_unpaired':>11s} "
        f"{'p_signflip':>11s}"
    )
    print(
        "\nStanding question -- intens vs noise_intens, per model "
        f"(no prior study ever separated these):\n{hdr}\n  " + "-" * (len(hdr) - 2)
    )
    # The flag follows the PRIMARY procedure printed above (Holm), not
    # Bonferroni: Holm's step thresholds exceed ALPHA_PRIMARY, so a
    # Holm-rejected row must not print as merely uncorrected.
    for r, rej in zip(rows, rej_cl):
        if {r["key_a"][1], r["key_b"][1]} != {"intens", "noise_intens"}:
            continue
        model = r["key_a"][0]
        flag = ""
        if rej:
            flag = "  <== SEPARATES (Holm, PRIMARY)"
        elif r["p_cluster"] <= ALPHA:
            flag = f"  <== p<{ALPHA} uncorrected"
        print(
            f"  {model:14s} {r['acc_a']:7.3f} {r['acc_b']:7.3f} "
            f"{r['disc']:7.3f} {r['b']:4d}/{r['c']:<4d} "
            f"{r['p_item']:10.2e} {r['p_unpaired']:11.2e} "
            f"{r['p_cluster']:11.2e}{flag}"
        )


def _print_design_effects(des: np.ndarray) -> None:
    """Print the design-effect summary over the measurable PRIMARY contrasts.

    Prints the no-measurable line instead when `des` is empty.
    """
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


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Run the paired re-analysis report."""
    print("Loading marks ...", flush=True)
    marks = load_marks(results_dir)
    _print_depth(marks)

    contrasts = build_primary_contrasts()

    for drop_invalid, tag in (
        (False, "null == incorrect (pre-registered)"),
        (True, "DROP-INVALID pairs"),
    ):
        print(f"\n{'=' * 78}\nPRIMARY family, {tag}\n{'=' * 78}")
        rows = labeled_rows(marks, contrasts, drop_invalid)

        p_pair = np.array([r["p_item"] for r in rows])
        p_unp = np.array([r["p_unpaired"] for r in rows])
        rej_pair, rej_unp = rejections(p_pair, "Holm"), rejections(p_unp, "Holm")

        print(
            f"Rejections at FWER {ALPHA} over {N_PRIMARY} contrasts:\n"
            f"  unpaired CMH  + Bonferroni : {(p_unp <= ALPHA_PRIMARY).sum():3d}\n"
            f"  unpaired CMH  + Holm       : {rej_unp.sum():3d}\n"
            f"  paired McNemar+ Bonferroni : {(p_pair <= ALPHA_PRIMARY).sum():3d}\n"
            f"  paired McNemar+ Holm       : {rej_pair.sum():3d}"
        )
        if not drop_invalid:
            des = np.array([r["de"] for r in rows if r["de"] is not None])
            frac_pos = f"{(des > 1.0).mean():.0%}" if des.size else "n/a"
            p_cl = np.array([r["p_cluster"] for r in rows])
            rej_cl = rejections(p_cl, "Holm")
            print(
                f"  seed sign-flip+ Bonferroni : {int((p_cl <= ALPHA_PRIMARY).sum()):3d}\n"
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
            for r in sorted(sel, key=itemgetter(key))[:MAX_LISTED]:
                print(
                    f"    {word} {r['label']:52s} {_acc(r['acc_a']):>7s} vs "
                    f"{_acc(r['acc_b']):>7s}  "
                    f"disc={r['disc']:.3f}  p_pair={r['p_item']:.2e}  "
                    f"p_unpair={r['p_unpaired']:.2e}"
                )

        if not drop_invalid:
            _print_standing_question(rows, rej_cl)
            _print_design_effects(des)

    # --- Tier 3 (SECONDARY) gets the same treatment, for completeness --------
    sec = build_secondary_contrasts()
    sec_rows = labeled_rows(marks, sec)
    n_disc = {
        k: rejections(np.array([r[k] for r in sec_rows]), "BH", Q_SECONDARY).sum()
        for k in ("p_cluster", "p_unpaired", "p_item")
    }

    print(
        f"\n{'=' * 78}\nSECONDARY family ({len(sec)} cross-family size-matched "
        f"contrasts, intens only), Benjamini-Hochberg q={Q_SECONDARY}\n{'=' * 78}\n"
        f"  seed sign-flip (inferential) : {n_disc['p_cluster']:3d} discoveries\n"
        f"  unpaired CMH (descriptive)   : {n_disc['p_unpaired']:3d} discoveries\n"
        f"  paired McNemar (descriptive) : {n_disc['p_item']:3d} discoveries"
    )


if __name__ == "__main__":
    main()
