"""Holm and Hochberg report for PRIMARY contrasts.

PRIMARY uses exact seed-level sign flips because harmonic marks within a seed are correlated.
Hochberg is sensitivity-only: its positive-dependence condition is unverified.
Collapsed cells are annotated, never excluded.
"""

import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from _power_common import apply_corrections  # noqa: E402
from paired_analysis import CellMarks, contrast_row, holm, load_marks  # noqa: E402
from power_analysis import (  # noqa: E402
    ALPHA,
    ALPHA_OMNIBUS,
    FAMILIES,
    INFOS,
    MODELS,
    N_FAMILIES,
    N_HARMONICS,
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

#: Near-total parse failure threshold; census wording only.
TOTAL_COLLAPSE = 0.95

#: Both arms at or above this accuracy are a ceiling pair, not a finding.
CEILING = 0.95


#: Row key a missing-cell or empty-seed family reports under the omnibus gate.
GATE_NO_DATA = {"n_seeds": 0, "stat": None, "p": None, "reject": False}


def omnibus_gates(marks: CellMarks) -> dict[str, dict]:
    """Compute the observed Tier-1 family omnibus gates.

    One generalized-CMH test per family across its rungs, stratified by
    ``(info, harmonic)`` like `power_analysis.omnibus_power`. The marks are
    the observed ones, so strata hold only the seeds all of the family's cells
    share; an absent cell or empty intersection yields the no-data entry.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `paired_analysis.load_marks`.

    Returns
    -------
    dict[str, dict]
        Family name -> ``n_seeds``, ``stat``, ``p``, ``reject``.
    """
    gates: dict[str, dict] = {}
    for family, rungs in FAMILIES.items():
        cells = [(rung, info) for rung in rungs for info in INFOS]
        if any(cell not in marks.correct for cell in cells):
            gates[family] = dict(GATE_NO_DATA)
            continue
        seeds = sorted(set.intersection(*(set(marks.correct[cell]) for cell in cells)))
        if not seeds:
            gates[family] = dict(GATE_NO_DATA)
            continue
        succ = np.array(
            [
                [
                    sum(marks.correct[(rung, info)][seed][k] for seed in seeds)
                    for info in INFOS
                    for k in range(N_HARMONICS)
                ]
                for rung in rungs
            ],
            dtype=np.int64,
        )[None, :, :]
        stat = float(gcmh_stat(succ, len(seeds))[0])
        p = float(chi2.sf(stat, df=2))
        gates[family] = {
            "n_seeds": len(seeds),
            "stat": stat,
            "p": p,
            "reject": p <= ALPHA_OMNIBUS,
        }
    return gates


def hochberg(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Return Hochberg step-up rejections at familywise level ``alpha``.

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
    return apply_corrections(np.atleast_2d(np.asarray(pvals, float)), alpha)[
        "Hochberg"
    ][0]


def compliance_census(marks: CellMarks) -> dict:
    """Measure non-compliance per parsed ``(model, info)`` cell.

    Parameters
    ----------
    marks : CellMarks
        Parsed marks from `paired_analysis.load_marks`.

    Returns
    -------
    dict
        Cell key -> ``rate``.
    """
    out = {}
    for key, by_seed in marks.compliance.items():
        vals = [v for seed_vals in by_seed.values() for v in seed_vals]
        if not vals:
            continue
        per_seed = {
            seed: (sum(1 for v in seed_vals if v != COMPLIANT), len(seed_vals))
            for seed, seed_vals in by_seed.items()
        }
        out[key] = {
            "rate": sum(v != COMPLIANT for v in vals) / len(vals),
            "n": len(vals),
            "modes": Counter(v for v in vals if v != COMPLIANT),
            "per_seed": per_seed,
        }
    return out


def common_seed_rate(cell: dict, seeds: Iterable[int]) -> float | None:
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
    float | None
        ``None`` when the subset has no marks; otherwise its non-compliance rate.
    """
    counts = [cell["per_seed"][s] for s in seeds if s in cell["per_seed"]]
    total = sum(t for _nc, t in counts)
    if total == 0:
        return None
    return sum(nc for nc, _t in counts) / total


def collapse_note(key: tuple[str, str], rate: float | None, census: dict) -> str:
    """Return a mechanism annotation, or ``""`` below the collapse threshold.

    Parameters
    ----------
    key : tuple[str, str]
        Cell key.
    rate : float | None
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
    """True when padding alone carries a lane over ``COLLAPSE_THRESHOLD``.

    The unpadded rate is below the threshold and the padded rate is at or above.
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
    """Print one correction-cost block, sorted on `key` and marked with `sign`."""
    for r in sorted(rows, key=lambda r: r[key]):
        print(
            f"   {sign}{r['label']:52s} item {r['p_item']:.3e} -> "
            f"cluster {r['p_cluster']:.3e}"
        )


def _step_boundary(pvals: np.ndarray, rows: list, m: int, n_rej: int) -> None:
    """Print Holm ranks around its stopping boundary.

    Parameters
    ----------
    pvals : np.ndarray
        P-values in `rows` order.
    rows : list
        Contrast rows.
    m : int
        Number of hypotheses.
    n_rej : int
        Holm rejection count.
    """
    order = np.argsort(pvals, kind="stable")
    print("\nHolm step-down at the boundary (rank / p / own threshold):")
    for i in range(max(n_rej - 2, 0), min(n_rej + 2, m)):
        idx = order[i]
        mark = "REJ " if i < n_rej else "stop"
        print(
            f"  {mark} rank {i + 1:3d}  p={pvals[idx]:.4e}  "
            f"thr={ALPHA / (m - i):.4e}   {rows[idx]['label']}"
        )


def collapse_tag(row: dict, census: dict) -> str:
    """Return collapse annotations for a contrast row."""
    hits = [
        h
        for h in (
            collapse_note(row["key_a"], row["rate_a"], census),
            collapse_note(row["key_b"], row["rate_b"], census),
        )
        if h
    ]
    return ("   [COLLAPSE: " + "; ".join(hits) + "]") if hits else ""


@dataclass(frozen=True)
class Report:
    """Computed significance-report quantities."""

    rows: list[dict]
    m: int
    hp: np.ndarray
    hb: np.ndarray
    h_item: np.ndarray
    rej_by_test: dict
    depth_min: int
    depth_max: int
    floor_bound: bool
    census: dict
    pad_rows: list[dict]
    pad_lanes: set[str]
    over: list[tuple[str, str]]
    findings: list[dict]
    n_findings_total: int
    n_flag: int
    n_pad: int
    passing: list[dict]
    reversed_: list[dict]
    fails: list[dict]
    fails_total: list[dict]
    fails_partial: list[dict]
    fails_unexplained: list[dict]
    zero_vs_zero: list[int]
    not_significant: list[dict]
    ceiling: list[dict]
    n_zero_discordant: int
    lost: list[dict]
    gained: list[dict]
    n_ladder: int
    n_noise_over_cells: int
    n_noise_over_lanes: int
    zero_over: list[tuple[str, str]]
    total_cells: set[tuple[str, str]]
    n_ladder_findings: int
    n_info_findings: int
    n_zero_significant: int
    partial_compliance: str
    item_min: int
    item_max: int
    n_floor: int
    n_lost_ladder: int
    gates: dict[str, dict]
    n_ladder_ungated: int
    hochberg_only: list[dict]
    n_ladder_rejections: int
    n_info_rejections: int


def render(report: Report) -> None:
    """Run and print the significance report.

    Narrative claims remain conditional on displayed counts.
    """
    rows = report.rows
    census = report.census
    p_cl = np.array([r["p_cluster"] for r in rows])
    m = report.m
    hp, hb, h_item = report.hp, report.hb, report.h_item
    rej_by_test = report.rej_by_test

    # ---- DEPTH GUARD: gating on the DEEPEST contrast asks whether ANYTHING is rejectable. ---
    depth_min, depth_max = report.depth_min, report.depth_max
    holm_first_step = ALPHA / m
    floor_deepest = 2 / 2**depth_max
    floor_bound = report.floor_bound
    if floor_bound:
        print(
            f"\n{'!' * 78}\nINCOMPLETE SYNC -- the family sits below the "
            f"sign-flip resolution floor\n{'!' * 78}"
        )
        print(
            f"  Deepest contrast: {depth_max} common seeds. The smallest p ANY "
            f"contrast can return is 2/2**{depth_max} = {floor_deepest:.3e}, "
            f"above Holm's first step\n  ALPHA/m = {ALPHA} / {m} = "
            f"{holm_first_step:.4e}. NO contrast is rejectable at this depth,\n"
            f"  at ANY effect size -- including the arm-vs-floor positive "
            f"controls. This is an\n  INCOMPLETE SYNC, not a finding: finish "
            f"sync_down() and re-run.\n"
            f"  (Shallowest contrast: {depth_min} seeds, floor "
            f"{2 / 2 ** depth_min:.3e} -- quoted by the closing paragraph.)\n"
        )

    print(f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}")
    print(
        f"Replicate depth: n = {report.item_min}-{report.item_max} "
        f"matched items per contrast, over "
        f"{report.depth_min}-{report.depth_max} replicate seeds"
    )
    # Computed from the landed data so a short sync cannot print a depth the marks lack.
    mx_n, mx_s = report.item_max, report.depth_max
    print(
        "PRIMARY TEST: exact seed-level sign-flip randomization over the "
        "per-seed arm\n  differences. The seed is the unit the design "
        "randomizes -- one label alphabet\n  and ONE SHARED ANSWER VECTOR per "
        f"replicate, reused by all {N_HARMONICS} harmonic items and\n  by "
        f"all {len(INFOS)} info "
        f"arms -- so the {mx_n} marks are {mx_s} clusters of {N_HARMONICS}, "
        f"not {mx_n}\n  "
        f"independent pairs. Exact (2^{mx_s} assignments enumerated by DP), "
        "deterministic,\n  and equal to exact McNemar when every cluster is a "
        "singleton.\n"
        "  NULL ASSUMPTION: arms are exchangeable WITHIN a replicate. The "
        "collection guarantees\n  this, not a check here: "
        "`ReplicateHarness.run_replicates` builds a seed's arms from one\n  "
        "`make_quizzes(seed, model)` call and scores them in one pooled "
        "`provider.evaluate`\n  request, so arms differ only in prompt text. "
        "Only a partial re-collect of one seed\n  can break it.\n"
    )

    print(
        f"{'test':26s} {'procedure':10s} {'rejected':>9s}  "
        f"{f'uncorrected p<={ALPHA}':>19s}"
    )
    print("-" * 70)
    for name, (pv, rej_by) in rej_by_test.items():
        for proc, rej in (*rej_by.items(), ("Bonferroni", pv <= ALPHA / m)):
            print(
                f"{name:26s} {proc:10s} {int(rej.sum()):9d}  "
                f"{int((pv <= ALPHA).sum()):19d}"
            )

    print(
        f"\nPrimary rejections split over the whole family: "
        f"{report.n_ladder_rejections} of "
        f"{report.n_ladder} LADDER contrasts, "
        f"{report.n_info_rejections} of "
        f"{m - report.n_ladder} INFO-ARM contrasts\n  (both counts include the "
        f"zero-arm controls; the findings-only split is further down)."
    )

    lost, gained = report.lost, report.gained
    print(
        f"\nCost of the correction: Holm loses {len(lost)} and gains "
        f"{len(gained)} against the item-level p."
    )
    _print_signed(lost, "-", "p_item")
    _print_signed(gained, "+", "p_cluster")
    n_lad = report.n_lost_ladder
    # Floor-bound losses carry no clustering information; n_lad==0 needs its own branch.
    if lost and floor_bound:
        print(
            f"   Both counts are artifacts of the resolution floor: Holm "
            f'rejects nothing at\n   this depth, so all {len(lost)} "losses" '
            f"are simply the item-level rejections and\n   the clustering "
            f"correction is not what cost them -- see the INCOMPLETE SYNC\n"
            f"   banner above."
        )
    elif lost and n_lad:
        print(
            f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- the "
            f"clustering correction\n   bites the family-scaling story, not "
            f"the info-arm story."
        )
    elif lost:
        print(
            f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- all "
            f"{len(lost)} are INFO-ARM\n   contrasts. The clustering "
            f"correction bites the family-scaling story where the\n   "
            f"contrasts it costs are ladder rungs and the info-arm story "
            f"where they are not;\n   here it is the info-arm story."
        )

    extra = report.hochberg_only
    print(
        f"\nHolm vs Hochberg (primary): Hochberg rejects "
        f"{'the same set' if not extra else f'{len(extra)} MORE'}"
    )
    for r in extra:
        print(f"   +{r['label']:52s} p={r['p_cluster']:.3e}")

    _step_boundary(p_cl, rows, m, int(hp.sum()))

    # ---- COLLAPSE CENSUS: a result, not a data-quality footnote -------------
    over = report.over
    print(
        f"\n{'=' * 78}\nCOLLAPSE CENSUS -- padding robustness, stated as a "
        f"result\n{'=' * 78}"
    )

    # pad_rows supplies the intro's denominator; `len(MODELS)` would over-count unpaired lanes.
    pad_rows = report.pad_rows
    pad_lanes = report.pad_lanes
    noise_over = report.n_noise_over_lanes
    print(
        "The `noise_intens` arm is the compact rule form padded with "
        "WHITESPACE to exactly\nthe extensional arm's token count under the "
        "model's own tokenizer. It adds no\ninformation and no content -- so a "
        "model that obeys the output contract on\n`intens` should obey it "
        "here. In "
        f"{noise_over} of {len(pad_rows)} lanes with both arms measured it "
        f"does not (noise arm >= "
        f"{COLLAPSE_THRESHOLD:.0%} non-compliant on the seeds both arms "
        f"cover), and the\ntable below separates the lanes where the PAD is "
        f"responsible from the "
        f"lanes that were already failing the\ncontract unpadded. That is a "
        f"finding about padding robustness in its own right,\nand it is "
        f"reported here rather than used as grounds for exclusion.\n"
    )

    # The causal claim is scoped to what is computed: matched seeds.
    print(
        f"PADDING EFFECT ON COMPLIANCE, over the {len(pad_rows)} lanes with "
        "both arms measured\n(`intens` is the same rule text, unpadded) -- so "
        "the delta is attributable to the\nwhitespace, ON THE SEEDS BOTH ARMS "
        "COVER. `n` is how many matched replicates\nthat is:\n"
    )
    print(
        f"{'lane':13s} {'intens':>8s} {'noise':>8s} {'delta':>8s} "
        f"{'noise empty':>12s} {'n':>4s}  verdict"
    )
    print("-" * 78)
    # delta descending, lane-name tiebreak for determinism.
    for row in sorted(pad_rows, key=lambda r: (-r["delta"], r["model"])):
        cn, delta = row["cn"], row["delta"]
        # Mode share stays whole-cell: a descriptive column, not an input to the verdict.
        empty = cn["modes"].get(EMPTY, 0) / cn["n"]
        verdict = row["verdict"]
        print(
            f"{row['model']:13s} {row['rate_i']:8.1%} {row['rate_n']:8.1%} "
            f"{delta:+8.1%} {empty:12.1%} {row['n_common']:4d}  {verdict}"
        )
    n_pad_lanes = len(pad_lanes)
    print(
        f"\n=> The pad itself pushes {n_pad_lanes} of {len(pad_rows)} lanes over the "
        f"{COLLAPSE_THRESHOLD:.0%} criterion. This is a\n   RESULT: "
        f"whitespace padding to a matched token count is not inert, it "
        f"destroys\n   the output contract in a substantial minority of "
        f"models. Every contrast that\n   touches such an arm stays in the "
        f"findings, annotated.\n"
    )

    print("ALL cells at or above the criterion, any arm:\n")
    print(
        f"{'lane':13s} {'arm':13s} {'non-compl.':>10s} {'n':>5s}  "
        f"dominant failure modes"
    )
    print("-" * 78)
    for key in over:
        cell = census[key]
        modes = ", ".join(
            f"{name} {cnt / cell['n']:.1%}"
            for name, cnt in cell["modes"].most_common(3)
        )
        star = " <== total" if key in report.total_cells else ""
        print(
            f"{key[0]:13s} {key[1]:13s} {cell['rate']:10.1%} {cell['n']:5d}  "
            f"{modes}{star}"
        )
    print(
        f"\n{len(over)} of {len(census)} cells are at or above the "
        f"{COLLAPSE_THRESHOLD:.0%} criterion; {report.n_noise_over_cells} of them are "
        f"noise arms.\nThe criterion is applied SYMMETRICALLY to all four arms, "
        f"so non-noise arms appear here beside the noise arms."
    )
    zero_over = report.zero_over
    if zero_over:
        print(
            f"{len(zero_over)} of them are `zero` baseline cells "
            f"({', '.join(k[0] for k in zero_over)}): those lanes are "
            f"non-compliant\neven with an EMPTY context, so their collapse is "
            f"not padding-specific."
        )

    sel = report.findings
    tot = report.n_findings_total
    print(
        f"\n{'=' * 78}\nTIER 1 -- family omnibus gates (generalized CMH, "
        f"df=2, alpha = {ALPHA}/{N_FAMILIES} = {ALPHA_OMNIBUS:.5f})\n"
        f"{'=' * 78}"
    )
    for family, gate in report.gates.items():
        if gate["p"] is None:
            print(f"  {family:12s} n_seeds=  0 stat=     n/a p=      n/a  no data")
        else:
            verdict = "REJECT" if gate["reject"] else "no reject"
            print(
                f"  {family:12s} n_seeds={gate['n_seeds']:3d} "
                f"stat={gate['stat']:8.3f} p={gate['p']:.3e}  {verdict}"
            )
    print(
        "\nThe gate is the pre-registered condition for reporting a family's "
        "ladder contrasts\nas more than exploratory. It is an unpaired "
        "harmonic-stratified test (independent-\nharmonic assumption, like the "
        "descriptive CMH column), so it gates but does not\nreplace the "
        "seed-level sign-flip.\n"
    )
    print(
        f"\n{'=' * 78}\nSIGNIFICANT FINDINGS (Holm, seed sign-flip): "
        f"{len(sel)} of {tot}\n{'=' * 78}"
    )
    print(
        "No contrast is excluded. Where an arm is at or above "
        f"{COLLAPSE_THRESHOLD:.0%} non-compliant the\ncontrast carries a "
        "[COLLAPSE] annotation naming the measured rate and mode: the\n"
        "difference is real, and the mechanism may be format collapse rather "
        "than task\ndifficulty. Both readings are stated; neither is filtered "
        "away.\n"
    )
    ladders = [r for r in sel if r["kind_is_ladder"]]
    infos = [r for r in sel if not r["kind_is_ladder"]]
    for title, bucket in (
        ("LADDER contrasts (scaling within a family)", ladders),
        ("INFO-ARM contrasts (within one model)", infos),
    ):
        denom = (
            report.n_ladder_findings if bucket is ladders else report.n_info_findings
        )
        print(f"\n-- {title}: {len(bucket)} of {denom}")
        for r in sorted(bucket, key=lambda r: r["p_cluster"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            lead = "  " if bucket is not ladders or r["gated"] else "* "
            gate_note = (
                ""
                if bucket is not ladders or r["gated"]
                else (
                    f"  [EXPLORATORY: {r['family']} omnibus "
                    f"p={report.gates[r['family']]['p']:.2e}]"
                )
            )
            print(
                f"{lead}{direction} {r['label']:52s} {r['acc_a']:.3f} -> "
                f"{r['acc_b']:.3f}   p={r['p_cluster']:.2e} "
                f"(item {r['p_item']:.2e}){r['collapse_tag']}{gate_note}"
            )
        if bucket is ladders and report.n_ladder_ungated:
            print(
                f"  * {report.n_ladder_ungated} of {len(ladders)} ladder "
                "findings are in families whose omnibus gate did not reject: "
                "reported as EXPLORATORY, not confirmed scaling effects."
            )
    n_flag, n_pad = report.n_flag, report.n_pad
    # TWO-MECHANISM needs findings touching a collapsed cell; the branches separate that case.
    print(
        f"\n  [COLLAPSE] {n_flag} of {len(sel)} findings touch a cell at or "
        f"above {COLLAPSE_THRESHOLD:.0%}\n      non-compliance.",
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
    zz = report.zero_vs_zero
    passing, reversed_ = report.passing, report.reversed_
    fails = report.fails
    print(f"\n{'=' * 78}\nZERO-ARM CONTROLS\n{'=' * 78}")
    print(
        f"{report.n_floor} arm-vs-floor positive controls (informative arm vs the "
        f"chance baseline): {len(passing)} significant with the "
        f"informative arm AHEAD, {len(reversed_)} significant\nbut REVERSED "
        f"(informative arm below the floor), {len(fails)} not rejected.\n"
        "Two-sided test: a non-rejection is an arm not shown to beat an empty "
        "context at this\ndepth -- not a broken pipeline and not a tie."
    )
    for r in sorted(reversed_, key=lambda r: -r["acc_a"]):
        info_acc, zero_acc = r["acc_a"], r["acc_b"]
        note = r["collapse_tag"]
        print(
            f"  REVERSED {r['label']:52s} {info_acc:.3f} vs floor "
            f"{zero_acc:.3f}   p={r['p_cluster']:.2e}{note}"
        )
    for r in sorted(fails, key=lambda r: -r["acc_a"]):
        note = r["collapse_tag"]
        print(
            f"  FAILS  {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
            f"   p={r['p_cluster']:.2e}{note}"
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
        total = report.fails_total
        partial = report.fails_partial
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
                f"a lane the pad carried over the {COLLAPSE_THRESHOLD:.0%} "
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
                "arm, or its lane was not carried over the "
                f"{COLLAPSE_THRESHOLD:.0%} criterion by the pad\n  (intens "
                "already over it, noise under it, or a rate unmeasured). Each "
                "is an arm not\n  shown to beat an empty context with no "
                "padding collapse to blame:"
            )
            for r in sorted(unexplained, key=lambda r: -r["acc_a"]):
                print(f"    {r['label']}")
    print(
        f"\n{len(zz)} zero-vs-zero ladder contrasts (one model's empty-context "
        f"baseline against\n  another's): {report.n_zero_significant} significant. A rejection "
        "is a real between-model difference at zero\n  information, not an "
        "error."
    )
    for i in sorted(zz, key=lambda i: rows[i]["p_cluster"]):
        if hp[i]:
            r = rows[i]
            print(
                f"  SIG    {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
                f"   p={r['p_cluster']:.2e}"
            )

    # ---- what is NOT significant, which is half the story -------------------
    ns = report.not_significant
    ceiling = report.ceiling
    n_zero_disc = report.n_zero_discordant
    print(f"\n{'=' * 78}\nNOT significant: {len(ns)} of {tot} findings")
    if ceiling:
        print(
            f"  of which CEILING pairs (both arms >= {CEILING}): "
            f"{len(ceiling)}. "
            f"{n_zero_disc} of them have ZERO discordant items:\n  exact ties "
            "in this sample, which more replicates could still break (see the "
            f"+/-0.20\n  equivalence decision). The other {len(ceiling) - n_zero_disc} "
            "have discordant items and are UNRESOLVED at\n  this depth, not ties."
        )
    else:
        # States the standing alternative rather than printing a "0 -- these are ties" line.
        print(
            f"  of which CEILING pairs (both arms >= {CEILING}): "
            f"{len(ceiling)} -- "
            f"none is a ceiling effect.\n  Every one has an arm below {CEILING}: "
            "contrasts the corrected test could not separate at\n  this depth, "
            "not pairs that agree."
        )
    print(
        f"  The cluster test also has a floor: with {report.depth_min} seeds it "
        f"cannot resolve any\n  contrast below 2/2^{report.depth_min} = "
        f"{2 / 2 ** report.depth_min:.3e}, and a contrast whose discordances all "
        f"live in\n  a handful of replicates cannot go below "
        f"2/2^(that handful)."
    )


def compute(results_dir: Path = RESULTS_DIR) -> Report:
    """Compute the significance report without printing."""
    marks = load_marks(results_dir)
    census = compliance_census(marks)
    gates = omnibus_gates(marks)
    family_of = {rung: family for family, rungs in FAMILIES.items() for rung in rungs}
    rows = []
    for label, key_a, key_b in build_primary_contrasts():
        row = contrast_row(marks, key_a, key_b)
        rows.append(
            {
                "label": label,
                **row,
                "rate_a": (
                    common_seed_rate(census[key_a], row["seeds"])
                    if key_a in census
                    else None
                ),
                "rate_b": (
                    common_seed_rate(census[key_b], row["seeds"])
                    if key_b in census
                    else None
                ),
                "kind": classify(key_a, key_b),
                "kind_is_ladder": key_a[0] != key_b[0],
                "family": family_of.get(key_a[0]) if key_a[0] != key_b[0] else None,
                "gated": (
                    gates[family_of[key_a[0]]]["reject"]
                    if key_a[0] != key_b[0]
                    else False
                ),
            }
        )
    p_cl = np.array([r["p_cluster"] for r in rows])
    p_item = np.array([r["p_item"] for r in rows])
    p_unp = np.array([r["p_unpaired"] for r in rows])
    m = len(rows)
    hp = holm(p_cl, ALPHA)
    hb = hochberg(p_cl, ALPHA)
    h_item = holm(p_item, ALPHA)
    rej_by_test = {
        "seed sign-flip (PRIMARY)": (p_cl, {"Holm": hp, "Hochberg": hb}),
        "item McNemar (descript.)": (
            p_item,
            {"Holm": h_item, "Hochberg": hochberg(p_item, ALPHA)},
        ),
        "unpaired CMH (descript.)": (
            p_unp,
            {"Holm": holm(p_unp, ALPHA), "Hochberg": hochberg(p_unp, ALPHA)},
        ),
    }
    depth_min = min(r["n_seeds"] for r in rows)
    depth_max = max(r["n_seeds"] for r in rows)
    floor_bound = 2 / 2**depth_max > ALPHA / m
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
        pad_rows.append(
            {
                "model": model,
                "delta": rate_n - rate_i,
                "rate_i": rate_i,
                "rate_n": rate_n,
                "n_common": len(common),
                "cn": cn,
                "verdict": (
                    "COLLAPSE"
                    if rate_n >= COLLAPSE_THRESHOLD and pad_crossing(rate_i, rate_n)
                    else (
                        "collapsed, but not padding-specific"
                        if rate_n >= COLLAPSE_THRESHOLD
                        else "contract holds"
                    )
                ),
            }
        )
    pad_lanes = {r["model"] for r in pad_rows if pad_crossing(r["rate_i"], r["rate_n"])}
    findings = [r for i, r in enumerate(rows) if hp[i] and r["kind"] == "finding"]
    n_findings_total = sum(r["kind"] == "finding" for r in rows)
    for row in rows:
        row["collapse_tag"] = collapse_tag(row, census)
    n_flag = sum(bool(r["collapse_tag"]) for r in findings)
    n_pad = sum(
        {r["key_a"][1], r["key_b"][1]} == {"extens", "noise_intens"}
        and r["key_a"][0] in pad_lanes
        for r in findings
    )
    floor = [i for i, r in enumerate(rows) if r["kind"] == "arm-vs-floor"]
    zero_vs_zero = [i for i, r in enumerate(rows) if r["kind"] == "zero-vs-zero"]
    passing, reversed_ = [], []
    fails = [rows[i] for i in floor if not hp[i]]
    for i in floor:
        r = rows[i]
        if hp[i]:
            (passing if r["acc_a"] > r["acc_b"] else reversed_).append(r)
    fails_total, fails_partial, fails_unexplained = [], [], []
    if fails and not floor_bound:
        for r in fails:
            info_key = r["key_a"]
            if info_key[1] == "noise_intens" and info_key[0] in pad_lanes:
                info_rate = r["rate_a"]
                if info_rate is not None and info_rate >= TOTAL_COLLAPSE:
                    fails_total.append(r)
                else:
                    fails_partial.append(r)
            else:
                fails_unexplained.append(r)
    not_significant = [
        r for i, r in enumerate(rows) if not hp[i] and r["kind"] == "finding"
    ]
    ceiling = [r for r in not_significant if min(r["acc_a"], r["acc_b"]) >= CEILING]
    n_zero_discordant = sum(r["b"] + r["c"] == 0 for r in ceiling)
    n_ladder = sum(r["kind_is_ladder"] for r in rows)
    n_noise_over_cells = sum(1 for key in over if key[1] == "noise_intens")
    n_noise_over_lanes = sum(row["rate_n"] >= COLLAPSE_THRESHOLD for row in pad_rows)
    zero_over = [key for key in over if key[1] == "zero"]
    total_cells = {
        key for key, cell in census.items() if cell["rate"] >= TOTAL_COLLAPSE
    }
    n_ladder_findings = sum(r["kind_is_ladder"] for r in rows if r["kind"] == "finding")
    n_info_findings = n_findings_total - n_ladder_findings
    n_zero_significant = sum(hp[i] for i in zero_vs_zero)
    partial_rates = [1 - r["rate_a"] for r in fails_partial if r["rate_a"] is not None]
    if not partial_rates:
        partial_compliance = "an unmeasured rate"
    elif len({round(rate, 10) for rate in partial_rates}) == 1:
        partial_compliance = f"{partial_rates[0]:.1%}"
    else:
        partial_compliance = f"{min(partial_rates):.1%}–{max(partial_rates):.1%}"
    lost = [rows[i] for i in range(m) if h_item[i] and not hp[i]]
    gained = [rows[i] for i in range(m) if hp[i] and not h_item[i]]
    return Report(
        rows=rows,
        m=m,
        hp=hp,
        hb=hb,
        h_item=h_item,
        rej_by_test=rej_by_test,
        depth_min=depth_min,
        depth_max=depth_max,
        floor_bound=floor_bound,
        census=census,
        pad_rows=pad_rows,
        pad_lanes=pad_lanes,
        over=over,
        findings=findings,
        n_findings_total=n_findings_total,
        n_flag=n_flag,
        n_pad=n_pad,
        passing=passing,
        reversed_=reversed_,
        fails=fails,
        fails_total=fails_total,
        fails_partial=fails_partial,
        fails_unexplained=fails_unexplained,
        zero_vs_zero=zero_vs_zero,
        not_significant=not_significant,
        ceiling=ceiling,
        n_zero_discordant=n_zero_discordant,
        lost=lost,
        gained=gained,
        n_ladder=n_ladder,
        n_noise_over_cells=n_noise_over_cells,
        n_noise_over_lanes=n_noise_over_lanes,
        zero_over=zero_over,
        total_cells=total_cells,
        n_ladder_findings=n_ladder_findings,
        n_info_findings=n_info_findings,
        n_zero_significant=n_zero_significant,
        partial_compliance=partial_compliance,
        item_min=min(r["n"] for r in rows),
        item_max=max(r["n"] for r in rows),
        n_floor=len(floor),
        n_lost_ladder=sum(r["kind_is_ladder"] for r in lost),
        gates=gates,
        n_ladder_ungated=sum(
            1 for r in findings if r["kind_is_ladder"] and not r["gated"]
        ),
        hochberg_only=[rows[i] for i in range(m) if hb[i] and not hp[i]],
        n_ladder_rejections=sum(hp[i] for i in range(m) if rows[i]["kind_is_ladder"]),
        n_info_rejections=sum(hp[i] for i in range(m) if not rows[i]["kind_is_ladder"]),
    )


def main(results_dir: Path = RESULTS_DIR) -> None:
    """Compute and render the significance report."""
    render(compute(results_dir))


if __name__ == "__main__":
    main()
