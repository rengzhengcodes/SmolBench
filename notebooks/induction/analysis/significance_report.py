"""Holm and Hochberg report for PRIMARY contrasts.

PRIMARY uses exact seed-level sign flips because harmonic marks within a seed are correlated.
Hochberg is sensitivity-only: its positive-dependence condition is unverified.
Collapsed cells are annotated, never excluded.

This study is exploratory end to end and makes no confirmatory claims;
`EXPLORATORY_NOTE` states that frame in the rendered report.
"""

import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import SEED, apply_corrections
from paired_analysis import CellMarks, labeled_rows, load_marks
from power_analysis import (
    ALPHA,
    ALPHA_OMNIBUS,
    FAMILIES,
    INFOS,
    MODELS,
    N_FAMILIES,
    N_HARMONICS,
    N_INFOS,
    N_RUNGS,
    RESULTS_DIR,
    build_primary_contrasts,
    gcmh_stat,
)
from scipy.stats import chi2

# Import the label so a rename cannot silently read empty values as zero.
from smolbench.evals.parsing import EMPTY
from smolbench.evals.quiz import COMPLIANT

#: Non-compliance rate requiring symmetric mechanism annotation.
COLLAPSE_THRESHOLD = 0.25

#: Near-total non-compliance: marks a census cell `<== total` and lets a failed
#: noise control be attributed to the pad (`fails_total`).
TOTAL_COLLAPSE = 0.95

#: Both arms at or above this accuracy are a ceiling pair, not a finding.
CEILING = 0.95

#: Monte-Carlo permutations per family gate: the plus-one floor 1/(N+1) = 2.5e-4 sits
#: ~29x under ALPHA_OMNIBUS = 7.1e-3 and the MC SE of a p near that threshold is
#: 1.3e-3, so the gate decision is not resolution-limited.
N_GATE_PERMS = 4000
if 1 / (N_GATE_PERMS + 1) >= ALPHA_OMNIBUS:
    raise RuntimeError("N_GATE_PERMS too small to resolve ALPHA_OMNIBUS")

#: Rendered twice: under the method note and again under the Tier-1 gate table.
EXPLORATORY_NOTE = (
    "This study is exploratory end to end (pilot-sized, sizing rests on an\n"
    "  independent-harmonic approximation, no confirmatory claims). The Tier-1 "
    "omnibus\n  gate and Holm/BH corrections order the evidence within that "
    "exploratory frame;\n  a gated ladder finding is a stronger exploratory "
    "signal, not a confirmed effect.\n"
)


def _gate_row(
    n_seeds: int, stat: Optional[float], p: Optional[float], p_perm: Optional[float]
) -> dict:
    """Build one `omnibus_gates` entry.

    Parameters
    ----------
    n_seeds : int
        Common seeds the family's rungs share.
    stat : Optional[float]
        Generalized CMH statistic, or None without data.
    p : Optional[float]
        Asymptotic chi-square p-value, or None without data.
    p_perm : Optional[float]
        Within-seed permutation p-value, or None without data.

    Returns
    -------
    dict
        ``n_seeds``, ``stat``, ``p``, ``p_perm``, ``p_gate = max(p, p_perm)`` and
        ``reject`` at `ALPHA_OMNIBUS`.
    """
    p_gate = None if p is None or p_perm is None else max(p, p_perm)
    return {
        "n_seeds": n_seeds,
        "stat": stat,
        "p": p,
        "p_perm": p_perm,
        "p_gate": p_gate,
        "reject": p_gate is not None and p_gate <= ALPHA_OMNIBUS,
    }


#: Row a missing-cell or empty-seed family reports under the omnibus gate.
GATE_NO_DATA = _gate_row(0, None, None, None)


def permutation_omnibus_p(
    marks_tensor: np.ndarray, stat_obs: float, rng: np.random.Generator
) -> float:
    """Within-seed rung-permutation p-value for the observed GCMH statistic.

    Under the null the three rungs' stratum vectors are exchangeable within a
    seed, so each seed's rung labels are permuted independently; the fraction
    of permuted statistics at or above the observed one is cluster-valid
    where the asymptotic chi2 is not.

    Parameters
    ----------
    marks_tensor : np.ndarray
        Correct marks shaped ``(n_seeds, N_RUNGS, K)``, strata ordered
        ``(info, k) for info in INFOS for k in range(N_HARMONICS)``.
    stat_obs : float
        Observed `power_analysis.gcmh_stat` value.
    rng : np.random.Generator
        Random-number generator for the permutations.

    Returns
    -------
    float
        Plus-one-corrected Monte-Carlo p-value over `N_GATE_PERMS` draws.
    """
    n_seeds = marks_tensor.shape[0]
    perms = np.argsort(rng.random((N_GATE_PERMS, n_seeds, N_RUNGS)), axis=2)
    permuted = np.take_along_axis(marks_tensor[None], perms[..., None], axis=2)
    succ = permuted.sum(axis=1)
    stats = gcmh_stat(succ, n_seeds)
    # The observed labelling is itself one permutation, so it must count as >=; the
    # slack absorbs last-bit differences between gcmh_stat's batched float sums and
    # stat_obs.
    return float((1 + np.count_nonzero(stats >= stat_obs - 1e-12)) / (N_GATE_PERMS + 1))


def omnibus_gates(marks: CellMarks) -> dict[str, dict]:
    """Compute the observed Tier-1 family omnibus gates.

    One generalized-CMH test per family across its rungs, stratified by
    ``(info, harmonic)`` like `power_analysis.omnibus_power`. The marks are
    the observed ones, so strata hold only the seeds all of the family's cells
    share; an absent cell or empty intersection yields the no-data entry.

    Under the gate's null the family's rungs are exchangeable within each
    seed. The gate rejects only when BOTH the asymptotic chi2 p-value and the
    within-seed permutation p-value (cluster-valid) clear `ALPHA_OMNIBUS` --
    ``p_gate`` is the stricter of the two.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `paired_analysis.load_marks`.

    Returns
    -------
    dict[str, dict]
        Family name -> ``n_seeds``, ``stat``, ``p``, ``p_perm``, ``p_gate``, ``reject``.
    """
    gates: dict[str, dict] = {}
    for i, (family, rungs) in enumerate(FAMILIES.items()):
        cells = [(rung, info) for rung in rungs for info in INFOS]
        seeds = (
            sorted(set.intersection(*(set(marks.correct[cell]) for cell in cells)))
            if all(cell in marks.correct for cell in cells)
            else []
        )
        if not seeds:
            gates[family] = dict(GATE_NO_DATA)
            continue
        marks_tensor = np.array(
            [
                [
                    np.concatenate(
                        [marks.correct[(rung, info)][seed] for info in INFOS]
                    )
                    for rung in rungs
                ]
                for seed in seeds
            ],
            dtype=np.int64,
        )
        succ = marks_tensor.sum(axis=0)[None]
        stat = float(gcmh_stat(succ, len(seeds))[0])
        p = float(chi2.sf(stat, df=N_RUNGS - 1))
        # Per-family stream off the analysis seed; the gate is deterministic.
        rng = np.random.default_rng([SEED, i])
        gates[family] = _gate_row(
            len(seeds), stat, p, permutation_omnibus_p(marks_tensor, stat, rng)
        )
    return gates


def compliance_census(marks: CellMarks) -> dict:
    """Measure non-compliance per parsed ``(model, info)`` cell.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `paired_analysis.load_marks`.

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


def collapse_note(key: tuple[str, str], rate: Optional[float], census: dict) -> str:
    """Return a mechanism annotation, or ``""`` below the collapse threshold.

    Parameters
    ----------
    key : tuple[str, str]
        Cell key.
    rate : Optional[float]
        Non-compliance rate over the compared seeds.
    census : dict
        Compliance census by cell.

    Returns
    -------
    str
        Mechanism annotation, or ``""`` below `COLLAPSE_THRESHOLD`.
    """
    cell = census.get(key)
    if cell is None or rate is None or rate < COLLAPSE_THRESHOLD:
        return ""
    # Whole-cell modes remain descriptive; the displayed rate uses compared seeds.
    top = cell["modes"].most_common(1)
    mode = f", mostly {top[0][0]}" if top else ""
    return f"{key[0]}/{key[1]} {rate:.1%} non-compliant{mode}"


def pad_crossing(rate_i: float, rate_n: float) -> bool:
    """Tell whether padding alone carries a lane over `COLLAPSE_THRESHOLD`.

    Parameters
    ----------
    rate_i : float
        Non-compliance rate of the unpadded (intens) arm.
    rate_n : float
        Non-compliance rate of the padded (noise) arm.

    Returns
    -------
    bool
        True when `rate_i` is below the threshold and `rate_n` at or above it.
    """
    return rate_i < COLLAPSE_THRESHOLD <= rate_n


def classify(key_a: tuple[str, str], key_b: tuple[str, str]) -> str:
    """Classify a contrast by its two ``(model, info)`` keys.

    Parameters
    ----------
    key_a : tuple[str, str]
        First cell key.
    key_b : tuple[str, str]
        Second cell key.

    Returns
    -------
    str
        Contrast bucket.

    Raises
    ------
    RuntimeError
        If `key_a` is the zero arm and `key_b` is informative.
    """
    za, zb = key_a[1] == "zero", key_b[1] == "zero"
    if za and zb:
        return "zero-vs-zero"
    if za:
        # build_primary_contrasts puts the informative arm in key_a; a
        # reversed pair would invert every arm-vs-floor reading below.
        raise RuntimeError(f"zero arm must be key_b, got {key_a} vs {key_b}")
    if zb:
        return "arm-vs-floor"
    return "finding"


def _print_signed(rows: list, sign: str, key: str) -> None:
    """Print one correction-cost block.

    Parameters
    ----------
    rows : list
        Contrast rows to print.
    sign : str
        Marker prefixed to every line.
    key : str
        Row field the block is sorted on.
    """
    for r in sorted(rows, key=lambda r: r[key]):
        print(
            f"   {sign}{r['label']:52s} item {r['p_item']:.3e} -> "
            f"cluster {r['p_cluster']:.3e}"
        )


def _step_boundary(rows: list, n_rej: int) -> None:
    """Print Holm ranks around its stopping boundary.

    Parameters
    ----------
    rows : list
        Contrast rows.
    n_rej : int
        Holm rejection count.
    """
    m = len(rows)
    ranked = sorted(rows, key=lambda r: r["p_cluster"])
    print("\nHolm step-down at the boundary (rank / p / own threshold):")
    for i in range(max(n_rej - 2, 0), min(n_rej + 2, m)):
        mark = "REJ " if i < n_rej else "stop"
        print(
            f"  {mark} rank {i + 1:3d}  p={ranked[i]['p_cluster']:.4e}  "
            f"thr={ALPHA / (m - i):.4e}   {ranked[i]['label']}"
        )


def gate_note(row: dict, gates: dict[str, dict]) -> str:
    """Return the ungated annotation for a ladder finding in a non-rejecting family.

    Parameters
    ----------
    row : dict
        Computed primary-contrast row.
    gates : dict[str, dict]
        Family omnibus gate results.

    Returns
    -------
    str
        Ungated annotation, or ``""`` when the row is not an ungated ladder finding.
    """
    if not row["kind_is_ladder"] or row["gated"]:
        return ""
    p_gate = gates[row["family"]]["p_gate"]
    if p_gate is None:
        return f"  [UNGATED: {row['family']} omnibus has no common-seed data]"
    return f"  [UNGATED: {row['family']} omnibus p={p_gate:.2e}]"


@dataclass(frozen=True)
class Report:
    """Computed significance-report quantities."""

    rows: list[dict]
    hp: np.ndarray
    rej_by_test: dict
    floor_bound: bool
    census: dict
    pad_rows: list[dict]
    pad_lanes: set[str]
    over: list[tuple[str, str]]
    findings: list[dict]
    n_pad: int
    passing: list[dict]
    reversed_: list[dict]
    fails: list[dict]
    fails_total: list[dict]
    fails_partial: list[dict]
    fails_unexplained: list[dict]
    zero_vs_zero: list[int]
    ceiling: list[dict]
    lost: list[dict]
    gained: list[dict]
    partial_compliance: str
    gates: dict[str, dict]
    hochberg_only: list[dict]


def render(report: Report) -> None:
    """Print the significance report; narrative claims stay conditional on shown counts.

    Parameters
    ----------
    report : Report
        Output of `compute`.
    """
    rows, census, hp = report.rows, report.census, report.hp
    m = len(rows)

    # ---- DEPTH GUARD: gating on the DEEPEST contrast asks whether ANYTHING is rejectable. ---
    depth_min = min(r["n_seeds"] for r in rows)
    depth_max = max(r["n_seeds"] for r in rows)
    floor_bound = report.floor_bound
    if floor_bound:
        print(
            f"\n{'!' * 78}\nINCOMPLETE SYNC -- the family sits below the "
            f"sign-flip resolution floor\n{'!' * 78}\n"
            f"  Deepest contrast: {depth_max} common seeds. The smallest p ANY "
            f"contrast can return is 2/2**{depth_max} = {2 / 2**depth_max:.3e}, "
            f"above Holm's first step\n  ALPHA/m = {ALPHA} / {m} = {ALPHA / m:.4e}. "
            "NO contrast is rejectable at this depth,\n"
            "  at ANY effect size -- including the arm-vs-floor positive controls. "
            "This is an\n  INCOMPLETE SYNC, not a finding: finish sync_down() and re-run.\n"
            f"  (Shallowest contrast: {depth_min} seeds, floor "
            f"{2 / 2 ** depth_min:.3e} -- quoted by the closing paragraph.)\n"
        )

    # Computed from the landed data so a short sync cannot print a depth the marks lack.
    item_min, item_max = min(r["n"] for r in rows), max(r["n"] for r in rows)
    print(
        f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}\n"
        f"Replicate depth: n = {item_min}-{item_max} matched items per contrast, "
        f"over {depth_min}-{depth_max} replicate seeds\n"
        "PRIMARY TEST: exact seed-level sign-flip randomization over the per-seed arm\n"
        "  differences. The seed is the unit the design randomizes -- one label alphabet\n"
        f"  and ONE SHARED ANSWER VECTOR per replicate, reused by all {N_HARMONICS} "
        f"harmonic items and\n  by all {N_INFOS} info arms -- so the {item_max} marks "
        f"are {depth_max} clusters of {N_HARMONICS}, not {item_max}\n  independent pairs. "
        f"Exact (2^{depth_max} assignments enumerated by DP), deterministic,\n"
        "  and equal to exact McNemar when every cluster is a singleton.\n"
        f"{EXPLORATORY_NOTE}"
        "  NULL ASSUMPTION: arms are exchangeable WITHIN a replicate. The collection "
        "guarantees\n  this, not a check here: `ReplicateHarness.run_replicates` builds "
        "a seed's arms from one\n  `make_quizzes(seed, model)` call and scores them in "
        "one pooled `provider.evaluate`\n  request, so arms differ only in prompt text. "
        "Only a partial re-collect of one seed\n  can break it.\n"
    )

    print(
        f"{'test':26s} {'procedure':10s} {'rejected':>9s}  "
        f"{f'uncorrected p<={ALPHA}':>19s}\n" + "-" * 70
    )
    for name, (pv, rej_by) in report.rej_by_test.items():
        for proc, rej in rej_by.items():
            print(
                f"{name:26s} {proc:10s} {int(rej.sum()):9d}  "
                f"{int((pv <= ALPHA).sum()):19d}"
            )

    lost, gained = report.lost, report.gained
    n_lad = sum(r["kind_is_ladder"] for r in lost)
    n_ladder = sum(r["kind_is_ladder"] for r in rows)
    n_ladder_rej = sum(rej for r, rej in zip(rows, hp) if r["kind_is_ladder"])
    print(
        f"\nPrimary rejections split over the whole family: "
        f"{n_ladder_rej} of {n_ladder} LADDER contrasts, "
        f"{hp.sum() - n_ladder_rej} of {m - n_ladder} INFO-ARM contrasts\n"
        "  (both counts include the zero-arm controls; the findings-only split is "
        "further down).\n"
        f"\nCost of the correction: Holm loses {len(lost)} and gains "
        f"{len(gained)} against the item-level p."
    )
    _print_signed(lost, "-", "p_item")
    _print_signed(gained, "+", "p_cluster")
    # Floor-bound losses carry no clustering information; n_lad==0 needs its own branch.
    if lost and floor_bound:
        print(
            "   Both counts are artifacts of the resolution floor: Holm rejects nothing at\n"
            f'   this depth, so all {len(lost)} "losses" are simply the item-level '
            "rejections and\n   the clustering correction is not what cost them -- see "
            "the INCOMPLETE SYNC\n   banner above."
        )
    elif lost and n_lad:
        print(
            f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- the "
            "clustering correction\n   bites the family-scaling story, not "
            "the info-arm story."
        )
    elif lost:
        print(
            f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- all "
            f"{len(lost)} are INFO-ARM\n   contrasts. The clustering correction bites "
            "the family-scaling story where the\n   contrasts it costs are ladder rungs "
            "and the info-arm story where they are not;\n   here it is the info-arm story."
        )

    extra = report.hochberg_only
    print(
        f"\nHolm vs Hochberg (primary): Hochberg rejects "
        f"{'the same set' if not extra else f'{len(extra)} MORE'}"
    )
    for r in extra:
        print(f"   +{r['label']:52s} p={r['p_cluster']:.3e}")

    _step_boundary(rows, int(hp.sum()))

    # ---- COLLAPSE CENSUS: a result, not a data-quality footnote -------------
    # pad_rows supplies the intro's denominator; `len(MODELS)` would over-count unpaired lanes.
    over, pad_rows, pad_lanes = report.over, report.pad_rows, report.pad_lanes
    crit = f"{COLLAPSE_THRESHOLD:.0%}"
    n_noise_over_lanes = sum(row["rate_n"] >= COLLAPSE_THRESHOLD for row in pad_rows)
    print(
        f"\n{'=' * 78}\nCOLLAPSE CENSUS -- padding robustness, stated as a "
        f"result\n{'=' * 78}\n"
        "The `noise_intens` arm is the compact rule form padded with WHITESPACE to exactly\n"
        "the extensional arm's token count under the model's own tokenizer. It adds no\n"
        "information and no content -- so a model that obeys the output contract on\n"
        f"`intens` should obey it here. In {n_noise_over_lanes} of {len(pad_rows)} "
        f"lanes with both arms measured it does not (noise arm >= {crit} non-compliant "
        "on the seeds both arms cover), and the\ntable below separates the lanes where "
        "the PAD is responsible from the lanes that were already failing the\ncontract "
        "unpadded. That is a finding about padding robustness in its own right,\nand it "
        "is reported here rather than used as grounds for exclusion.\n\n"
        # The causal claim is scoped to what is computed: matched seeds.
        f"PADDING EFFECT ON COMPLIANCE, over the {len(pad_rows)} lanes with both arms "
        "measured\n(`intens` is the same rule text, unpadded) -- so the delta is "
        "attributable to the\nwhitespace, ON THE SEEDS BOTH ARMS COVER. `n` is how many "
        "matched replicates\nthat is:\n\n"
        f"{'lane':13s} {'intens':>8s} {'noise':>8s} {'delta':>8s} "
        f"{'noise empty':>12s} {'n':>4s}  verdict\n" + "-" * 78
    )
    # delta descending, lane-name tiebreak for determinism.
    for row in sorted(pad_rows, key=lambda r: (-r["delta"], r["model"])):
        cn = row["cn"]
        # Mode share stays whole-cell: a descriptive column, not an input to the verdict.
        empty = cn["modes"].get(EMPTY, 0) / cn["n"]
        print(
            f"{row['model']:13s} {row['rate_i']:8.1%} {row['rate_n']:8.1%} "
            f"{row['delta']:+8.1%} {empty:12.1%} {row['n_common']:4d}  {row['verdict']}"
        )
    # The "not inert" result rests on at least one pad-crossing lane; without one it is unearned.
    if pad_lanes:
        verdict = (
            "This is a\n   RESULT: whitespace padding to a matched token count is not "
            "inert, it destroys\n   the output contract in a substantial minority of "
            "models. Every contrast that\n   touches such an arm stays in the findings, "
            "annotated."
        )
    else:
        verdict = (
            "On this tree no lane\n   crosses the criterion because of whitespace "
            "padding alone; the table above still\n   shows any changes in compliance "
            "below that threshold."
        )
    print(
        f"\n=> The pad itself pushes {len(pad_lanes)} of {len(pad_rows)} lanes over the "
        f"{crit} criterion. {verdict}\n\n"
        "ALL cells at or above the criterion, any arm:\n\n"
        f"{'lane':13s} {'arm':13s} {'non-compl.':>10s} {'n':>5s}  "
        "dominant failure modes\n" + "-" * 78
    )
    for key in over:
        cell = census[key]
        modes = ", ".join(
            f"{name} {cnt / cell['n']:.1%}"
            for name, cnt in cell["modes"].most_common(3)
        )
        star = " <== total" if cell["rate"] >= TOTAL_COLLAPSE else ""
        print(
            f"{key[0]:13s} {key[1]:13s} {cell['rate']:10.1%} {cell['n']:5d}  "
            f"{modes}{star}"
        )
    n_noise_over_cells = sum(key[1] == "noise_intens" for key in over)
    n_non_noise = len(over) - n_noise_over_cells
    print(
        f"\n{len(over)} of {len(census)} cells are at or above the {crit} criterion; "
        f"{n_noise_over_cells} of them are noise arms.\nThe criterion is applied "
        f"SYMMETRICALLY to all {N_INFOS} arms, so non-noise arms "
        + (
            "appear here beside the noise arms."
            if n_non_noise
            else "would appear here beside the noise arms; none does."
        )
    )
    zero_over = [key for key in over if key[1] == "zero"]
    if zero_over:
        print(
            f"{len(zero_over)} of them are `zero` baseline cells "
            f"({', '.join(k[0] for k in zero_over)}): those lanes are non-compliant\n"
            "even with an EMPTY context, so their collapse is not padding-specific."
        )

    sel, tot = report.findings, sum(r["kind"] == "finding" for r in rows)
    print(
        f"\n{'=' * 78}\nTIER 1 -- family omnibus gates (generalized CMH, "
        f"df={N_RUNGS - 1}; gate p = max(chi2 p, within-seed permutation p) <= "
        f"alpha = {ALPHA}/{N_FAMILIES} = {ALPHA_OMNIBUS:.5f})\n{'=' * 78}"
    )
    for family, gate in report.gates.items():
        if gate["p_gate"] is None:
            print(
                f"  {family:12s} n_seeds=  0 stat=     n/a p_chi2=      n/a "
                f"p_perm=      n/a  no data"
            )
        else:
            print(
                f"  {family:12s} n_seeds={gate['n_seeds']:3d} "
                f"stat={gate['stat']:8.3f} p_chi2={gate['p']:.3e} "
                f"p_perm={gate['p_perm']:.3e}  "
                f"{'REJECT' if gate['reject'] else 'no reject'}"
            )
    print(
        "\nThe gate is the pre-registered condition for reporting a family's ladder "
        "contrasts\nas gated rather than ungated. The chi2 p treats the "
        "(info, harmonic) strata as\nindependent and ignores within-seed "
        "clustering; the permutation p re-labels rungs\nwithin each seed "
        f"({N_GATE_PERMS} Monte-Carlo draws, fixed seed) and is cluster-valid. "
        "The\ngate takes the stricter of the two.\n"
        f"{EXPLORATORY_NOTE}\n"
        f"\n{'=' * 78}\nSIGNIFICANT FINDINGS (Holm, seed sign-flip): "
        f"{len(sel)} of {tot}\n{'=' * 78}\n"
        f"No contrast is excluded. Where an arm is at or above {crit} non-compliant the\n"
        "contrast carries a [COLLAPSE] annotation naming the measured rate and mode: the\n"
        "difference is real, and the mechanism may be format collapse rather than task\n"
        "difficulty. Both readings are stated; neither is filtered away.\n"
    )
    ladders = [r for r in sel if r["kind_is_ladder"]]
    infos = [r for r in sel if not r["kind_is_ladder"]]
    n_ladder_findings = sum(r["kind_is_ladder"] for r in rows if r["kind"] == "finding")
    n_ladder_ungated = sum(not r["gated"] for r in ladders)
    for title, bucket, denom in (
        ("LADDER contrasts (scaling within a family)", ladders, n_ladder_findings),
        ("INFO-ARM contrasts (within one model)", infos, tot - n_ladder_findings),
    ):
        print(f"\n-- {title}: {len(bucket)} of {denom}")
        for r in sorted(bucket, key=lambda r: r["p_cluster"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            note = gate_note(r, report.gates)
            print(
                f"{'* ' if note else '  '}{direction} {r['label']:52s} "
                f"{r['acc_a']:.3f} -> {r['acc_b']:.3f}   p={r['p_cluster']:.2e} "
                f"(item {r['p_item']:.2e}){r['collapse_tag']}{note}"
            )
        if bucket is ladders and n_ladder_ungated:
            print(
                f"  * {n_ladder_ungated} of {len(ladders)} ladder "
                "findings are in families whose Tier-1 omnibus gate did not "
                "reject (UNGATED); the gate ranks evidence within an "
                "exploratory study, it does not confer confirmatory status."
            )
    n_flag, n_pad = sum(bool(r["collapse_tag"]) for r in sel), report.n_pad
    # TWO-MECHANISM needs findings touching a collapsed cell; the branches separate that case.
    print(
        f"\n  [COLLAPSE] {n_flag} of {len(sel)} findings touch a cell at or "
        f"above {crit}\n      non-compliance.",
        end="",
    )
    if n_pad:
        print(
            f" {n_pad} of them are extens-vs-noise findings on a lane the pad "
            "itself pushed over the\n      criterion, so the extens-vs-noise "
            "story is TWO-MECHANISM: an information effect\n      where the "
            "noise arm stays well-formed, and a padding-robustness collapse "
            "where\n      it does not."
        )
    elif n_flag:
        print(
            " None is an extens-vs-noise finding on a lane the pad itself "
            "pushed over the\n      criterion: the annotation is a format "
            "caveat, and this report offers\n      no evidence for a second, "
            "padding-robustness mechanism."
        )
    elif sel:
        print(
            f" All {len(sel)} findings rest on two arms BELOW the criterion, "
            "so no broken output\n      contract is in play and this report "
            "offers no evidence for a second,\n      padding-robustness "
            "mechanism."
        )
    else:
        print(
            " No findings are significant, so the count is zero for want of "
            "findings, not of\n      collapses: this report is silent on a "
            "second mechanism."
        )

    # ---- zero-arm controls -------------------------------------------------
    zz, passing, reversed_ = report.zero_vs_zero, report.passing, report.reversed_
    fails = report.fails
    print(
        f"\n{'=' * 78}\nZERO-ARM CONTROLS\n{'=' * 78}\n"
        f"{len(passing) + len(reversed_) + len(fails)} arm-vs-floor positive controls "
        "(informative arm vs the "
        f"chance baseline): {len(passing)} significant with the "
        f"informative arm AHEAD, {len(reversed_)} significant\nbut REVERSED "
        f"(informative arm below the floor), {len(fails)} not rejected.\n"
        "Two-sided test: a non-rejection is an arm not shown to beat an empty "
        "context at this\ndepth -- not a broken pipeline and not a tie."
    )
    for r in sorted(reversed_, key=lambda r: -r["acc_a"]):
        print(
            f"  REVERSED {r['label']:52s} {r['acc_a']:.3f} vs floor "
            f"{r['acc_b']:.3f}   p={r['p_cluster']:.2e}{r['collapse_tag']}"
        )
    for r in sorted(fails, key=lambda r: -r["acc_a"]):
        print(
            f"  FAILS  {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
            f"   p={r['p_cluster']:.2e}{r['collapse_tag']}"
        )
    if fails and floor_bound:
        # Floor-bound failures are arithmetically forced and carry no information about padding.
        print(
            f"\n  All {len(fails)} failures are forced by the resolution floor "
            f"(see INCOMPLETE SYNC above):\n  at {depth_max} seeds no positive "
            "control could be rejected at any effect size. They are\n  "
            "evidence about the sync, not about padding or the models."
        )
    elif fails:
        # Partitioned: a fixed exoneration would misdescribe non-qualifying failures.
        total, partial = report.fails_total, report.fails_partial
        unexplained = report.fails_unexplained
        if total:
            print(
                f"\n  These {len(total)} of {len(fails)} failures are the "
                "collapse surfacing in the controls, not a\n  pipeline fault: "
                "each is a noise arm the whitespace padding drove to\n  "
                "near-total non-compliance, so it cannot outscore an empty prompt."
            )
        if partial:
            print(
                f"\n  {len(partial)} of {len(fails)} failures are noise arms on "
                f"a lane the pad carried over the {crit} "
                f"criterion, but the arm is still {report.partial_compliance} "
                f"compliant on the compared seeds, so the crossing is a "
                f"caveat, not a demonstrated cause of the failed control:"
            )
            for r in sorted(partial, key=lambda r: -r["acc_a"]):
                info_rate = r["rate_a"]
                if info_rate is None:
                    print(f"    {r['label']} (compared-seed rate unavailable)")
                else:
                    print(f"    {r['label']} ({1 - info_rate:.1%} compliant)")
        if unexplained:
            # Labels listed after the sentence so the section can be split on the claim.
            print(
                f"\n  {len(unexplained)} of {len(fails)} failures are NOT "
                "explained by padding: the informative arm is\n  not a noise "
                f"arm, or its lane was not carried over the {crit} criterion by the pad\n"
                "  (intens already over it, noise under it, or a rate unmeasured). Each "
                "is an arm not\n  shown to beat an empty context with no "
                "padding collapse to blame:"
            )
            for r in sorted(unexplained, key=lambda r: -r["acc_a"]):
                print(f"    {r['label']}")
    n_zero_sig = sum(hp[i] for i in zz)
    print(
        f"\n{len(zz)} zero-vs-zero ladder contrasts (one model's empty-context "
        f"baseline against\n  another's): {n_zero_sig} significant. "
        "A rejection is a real between-model difference at zero\n  information, not an "
        "error."
    )
    for r in sorted((rows[i] for i in zz if hp[i]), key=lambda r: r["p_cluster"]):
        print(
            f"  SIG    {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
            f"   p={r['p_cluster']:.2e}"
        )

    # ---- what is NOT significant, which is half the story -------------------
    ceiling = report.ceiling
    n_zero_disc = sum(r["b"] + r["c"] == 0 for r in ceiling)
    print(f"\n{'=' * 78}\nNOT significant: {tot - len(sel)} of {tot} findings")
    if ceiling:
        print(
            f"  of which CEILING pairs (both arms >= {CEILING}): {len(ceiling)}. "
            f"{n_zero_disc} of them have ZERO discordant items:\n  exact ties "
            "in this sample, which more replicates could still break (see the "
            f"+/-0.20\n  equivalence decision). The other {len(ceiling) - n_zero_disc} "
            "have discordant items and are UNRESOLVED at\n  this depth, not ties."
        )
    else:
        # States the standing alternative rather than printing a "0 -- these are ties" line.
        print(
            f"  of which CEILING pairs (both arms >= {CEILING}): {len(ceiling)} -- "
            f"none is a ceiling effect.\n  Every one has an arm below {CEILING}: "
            "contrasts the corrected test could not separate at\n  this depth, "
            "not pairs that agree."
        )
    print(
        f"  The cluster test also has a floor: with {depth_min} seeds it "
        f"cannot resolve any\n  contrast below 2/2^{depth_min} = "
        f"{2 / 2 ** depth_min:.3e}, and a contrast whose discordances all "
        f"live in\n  a handful of replicates cannot go below "
        f"2/2^(that handful)."
    )


def compute(results_dir: Path = RESULTS_DIR) -> Report:
    """Compute the significance report without printing.

    Parameters
    ----------
    results_dir : Path
        Results tree read by `paired_analysis.load_marks`.

    Returns
    -------
    Report
        Every quantity `render` prints.
    """
    marks = load_marks(results_dir)
    census = compliance_census(marks)
    gates = omnibus_gates(marks)
    family_of = {rung: family for family, rungs in FAMILIES.items() for rung in rungs}
    rows = labeled_rows(marks, build_primary_contrasts())
    for row in rows:
        key_a, key_b = row["key_a"], row["key_b"]
        is_ladder = key_a[0] != key_b[0]
        family = family_of.get(key_a[0]) if is_ladder else None
        rate_a, rate_b = (
            common_seed_rate(census[key], row["seeds"]) if key in census else None
            for key in (key_a, key_b)
        )
        hits = "; ".join(
            note
            for key, rate in ((key_a, rate_a), (key_b, rate_b))
            if (note := collapse_note(key, rate, census))
        )
        row.update(
            rate_a=rate_a,
            rate_b=rate_b,
            kind=classify(key_a, key_b),
            kind_is_ladder=is_ladder,
            family=family,
            gated=gates[family]["reject"] if is_ladder else False,
            collapse_tag=f"   [COLLAPSE: {hits}]" if hits else "",
        )
    rej_by_test = {}
    for name, field in (
        ("seed sign-flip (PRIMARY)", "p_cluster"),
        ("item McNemar (descript.)", "p_item"),
        ("unpaired CMH (descript.)", "p_unpaired"),
    ):
        pv = np.array([r[field] for r in rows])
        masks = apply_corrections(pv[None], ALPHA)
        # Procedure order is the rejection table's printed column order.
        rej_by_test[name] = (
            pv,
            {proc: masks[proc][0] for proc in ("Holm", "Hochberg", "Bonferroni")},
        )
    primary = rej_by_test["seed sign-flip (PRIMARY)"][1]
    hp, hb = primary["Holm"], primary["Hochberg"]
    h_item = rej_by_test["item McNemar (descript.)"][1]["Holm"]
    depth_max = max(r["n_seeds"] for r in rows)
    floor_bound = 2 / 2**depth_max > ALPHA / len(rows)
    over = sorted(
        (k for k, v in census.items() if v["rate"] >= COLLAPSE_THRESHOLD),
        key=lambda k: -census[k]["rate"],
    )
    pad_rows = []
    for model in MODELS:
        ci, cn = census.get((model, "intens")), census.get((model, "noise_intens"))
        if ci is None or cn is None:
            continue
        common = sorted(set(ci["per_seed"]) & set(cn["per_seed"]))
        rate_i, rate_n = common_seed_rate(ci, common), common_seed_rate(cn, common)
        if rate_i is None or rate_n is None:
            continue
        if rate_n < COLLAPSE_THRESHOLD:
            verdict = "contract holds"
        elif pad_crossing(rate_i, rate_n):
            verdict = "COLLAPSE"
        else:
            verdict = "collapsed, but not padding-specific"
        pad_rows.append(
            {
                "model": model,
                "delta": rate_n - rate_i,
                "rate_i": rate_i,
                "rate_n": rate_n,
                "n_common": len(common),
                "cn": cn,
                "verdict": verdict,
            }
        )
    pad_lanes = {r["model"] for r in pad_rows if pad_crossing(r["rate_i"], r["rate_n"])}
    findings = [r for r, rej in zip(rows, hp) if rej and r["kind"] == "finding"]
    floor = [(r, rej) for r, rej in zip(rows, hp) if r["kind"] == "arm-vs-floor"]
    passing = [r for r, rej in floor if rej and r["acc_a"] > r["acc_b"]]
    reversed_ = [r for r, rej in floor if rej and r["acc_a"] <= r["acc_b"]]
    fails = [r for r, rej in floor if not rej]
    # Floor-bound failures are arithmetically forced, so none is attributed to padding.
    fails_total, fails_partial, fails_unexplained = [], [], []
    for r in [] if floor_bound else fails:
        info_model, info_arm = r["key_a"]
        if info_arm != "noise_intens" or info_model not in pad_lanes:
            fails_unexplained.append(r)
        elif r["rate_a"] is not None and r["rate_a"] >= TOTAL_COLLAPSE:
            fails_total.append(r)
        else:
            fails_partial.append(r)
    partial_rates = [1 - r["rate_a"] for r in fails_partial if r["rate_a"] is not None]
    if not partial_rates:
        partial_compliance = "an unmeasured rate"
    elif len({round(rate, 10) for rate in partial_rates}) == 1:
        partial_compliance = f"{partial_rates[0]:.1%}"
    else:
        partial_compliance = f"{min(partial_rates):.1%}–{max(partial_rates):.1%}"
    zero_vs_zero = [i for i, r in enumerate(rows) if r["kind"] == "zero-vs-zero"]
    ceiling = [
        r
        for r, rej in zip(rows, hp)
        if not rej and r["kind"] == "finding" and min(r["acc_a"], r["acc_b"]) >= CEILING
    ]
    return Report(
        rows=rows,
        hp=hp,
        rej_by_test=rej_by_test,
        floor_bound=floor_bound,
        census=census,
        pad_rows=pad_rows,
        pad_lanes=pad_lanes,
        over=over,
        findings=findings,
        n_pad=sum(
            {r["key_a"][1], r["key_b"][1]} == {"extens", "noise_intens"}
            and r["key_a"][0] in pad_lanes
            for r in findings
        ),
        passing=passing,
        reversed_=reversed_,
        fails=fails,
        fails_total=fails_total,
        fails_partial=fails_partial,
        fails_unexplained=fails_unexplained,
        zero_vs_zero=zero_vs_zero,
        ceiling=ceiling,
        lost=[r for r, item, cl in zip(rows, h_item, hp) if item and not cl],
        gained=[r for r, item, cl in zip(rows, h_item, hp) if cl and not item],
        partial_compliance=partial_compliance,
        gates=gates,
        hochberg_only=[r for r, hoch, cl in zip(rows, hb, hp) if hoch and not cl],
    )


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Compute and render the significance report.

    Parameters
    ----------
    results_dir : Path
        Results tree to analyse.
    """
    render(compute(results_dir))


if __name__ == "__main__":
    main()
