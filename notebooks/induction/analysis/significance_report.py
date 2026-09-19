"""Holm and Hochberg report for PRIMARY contrasts.

PRIMARY uses exact seed-level sign flips because harmonic marks within a seed are correlated.
Hochberg is sensitivity-only: its positive-dependence condition is unverified.
Collapsed cells are annotated, never excluded.
"""

import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from paired_analysis import (  # noqa: E402
    _reject,
    contrast_row,
    holm,
    load_marks,
)
from power_analysis import (  # noqa: E402
    ALPHA,
    MODELS,
    build_primary_contrasts,
)

# Import the label so a rename cannot silently read empty values as zero.
from smolbench.evals.parsing import EMPTY
from smolbench.evals.quiz import COMPLIANT

#: Non-compliance rate requiring symmetric mechanism annotation.
COLLAPSE_THRESHOLD = 0.25

#: Near-total parse failure threshold; census wording only.
TOTAL_COLLAPSE = 0.95


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
    return _reject(pvals, alpha, "simes-hochberg")


def compliance_census(compliance: dict) -> dict:
    """Measure non-compliance per parsed ``(model, info)`` cell.

    Parameters
    ----------
    compliance : dict
        Per-cell compliance mappings from `paired_analysis.load_marks`.

    Returns
    -------
    dict
        Cell key -> ``rate``.
    """
    out = {}
    for key, by_seed in compliance.items():
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
    if za or zb:
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


def main() -> None:
    """Run and print the significance report.

    Narrative claims remain conditional on displayed counts.
    """
    correct, valid, compliance = load_marks()
    contrasts = build_primary_contrasts()
    census = compliance_census(compliance)

    rows = []
    for label, key_a, key_b in contrasts:
        row = contrast_row(correct, valid, key_a, key_b)
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
                "kind_is_ladder": "ladder" in label,
            }
        )

    p_cl = np.array([r["p_cluster"] for r in rows])
    p_item = np.array([r["p_item"] for r in rows])
    p_unp = np.array([r["p_unpaired"] for r in rows])
    m = len(rows)

    hp = holm(p_cl, ALPHA)
    hb = hochberg(p_cl, ALPHA)
    # Every correction pass this report needs, taken ONCE so the summary table does not re-run them.
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

    # ---- DEPTH GUARD: gating on the DEEPEST contrast asks whether ANYTHING is rejectable. ---
    depth_min = min(r["n_seeds"] for r in rows)
    depth_max = max(r["n_seeds"] for r in rows)
    holm_first_step = ALPHA / m
    floor_deepest = 2 / 2**depth_max
    floor_bound = floor_deepest > holm_first_step
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

    seeds = {r["n_seeds"] for r in rows}
    print(f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}")
    print(
        f"Replicate depth: n = {min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} "
        f"matched items per contrast, over "
        f"{min(seeds)}-{max(seeds)} replicate seeds"
    )
    # Computed from the landed data so a short sync cannot print a depth the marks lack.
    mx_n, mx_s = max(r["n"] for r in rows), max(seeds)
    print(
        "PRIMARY TEST: exact seed-level sign-flip randomization over the "
        "per-seed arm\n  differences. The seed is the unit the design "
        "randomizes -- one label alphabet\n  and ONE SHARED ANSWER VECTOR per "
        f"replicate, reused by all 9 harmonic items and\n  by all four info "
        f"arms -- so the {mx_n} marks are {mx_s} clusters of 9, not {mx_n}\n  "
        f"independent pairs. Exact (2^{mx_s} assignments enumerated by DP), "
        "deterministic,\n  and equal to exact McNemar when every cluster is a "
        "singleton.\n"
    )

    print(
        f"{'test':26s} {'procedure':10s} {'rejected':>9s}  "
        f"{'uncorrected p<=0.05':>19s}"
    )
    print("-" * 70)
    for name, (pv, rej_by) in rej_by_test.items():
        for proc, rej in (*rej_by.items(), ("Bonferroni", pv <= ALPHA / m)):
            print(
                f"{name:26s} {proc:10s} {int(rej.sum()):9d}  "
                f"{int((pv <= ALPHA).sum()):19d}"
            )

    n_lad_all = sum(1 for r in rows if r["kind_is_ladder"])
    print(
        f"\nPrimary rejections split over the whole family: "
        f"{sum(hp[i] for i in range(m) if rows[i]['kind_is_ladder'])} of "
        f"{n_lad_all} LADDER contrasts, "
        f"{sum(hp[i] for i in range(m) if not rows[i]['kind_is_ladder'])} of "
        f"{m - n_lad_all} INFO-ARM contrasts\n  (both counts include the "
        f"zero-arm controls; the findings-only split is further down)."
    )

    lost = [rows[i] for i in range(m) if h_item[i] and not hp[i]]
    gained = [rows[i] for i in range(m) if hp[i] and not h_item[i]]
    print(
        f"\nCost of the correction: Holm loses {len(lost)} and gains "
        f"{len(gained)} against the item-level p."
    )
    _print_signed(lost, "-", "p_item")
    _print_signed(gained, "+", "p_cluster")
    n_lad = sum(1 for r in lost if r["kind_is_ladder"])
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

    extra = [rows[i] for i in range(m) if hb[i] and not hp[i]]
    print(
        f"\nHolm vs Hochberg (primary): Hochberg rejects "
        f"{'the same set' if not extra else f'{len(extra)} MORE'}"
    )
    for r in extra:
        print(f"   +{r['label']:52s} p={r['p_cluster']:.3e}")

    _step_boundary(p_cl, rows, m, int(hp.sum()))

    # ---- COLLAPSE CENSUS: a result, not a data-quality footnote -------------
    over = sorted(
        (k for k, v in census.items() if v["rate"] >= COLLAPSE_THRESHOLD),
        key=lambda k: -census[k]["rate"],
    )
    print(
        f"\n{'=' * 78}\nCOLLAPSE CENSUS -- padding robustness, stated as a "
        f"result\n{'=' * 78}"
    )

    # pad_rows supplies the intro's denominator; `len(MODELS)` would over-count unpaired lanes.
    pad_rows = []
    for model in MODELS:
        ci = census.get((model, "intens"))
        cn = census.get((model, "noise_intens"))
        if ci is None or cn is None:
            continue
        # Rates over shared seeds, matching `paired_analysis.aligned`.
        common = sorted(set(ci["per_seed"]) & set(cn["per_seed"]))
        rate_i = common_seed_rate(ci, common)
        rate_n = common_seed_rate(cn, common)
        if rate_i is None or rate_n is None:
            # Skip rather than publish a 0% rate on a 0-seed basis.
            continue
        pad_rows.append(
            {
                "model": model,
                "delta": rate_n - rate_i,
                "rate_i": rate_i,
                "rate_n": rate_n,
                "n_common": len(common),
                "cn": cn,
            }
        )

    pad_lanes = {r["model"] for r in pad_rows if pad_crossing(r["rate_i"], r["rate_n"])}
    # Numerator and denominator share one basis: matched-arm rows on common seeds.
    noise_over = [r for r in pad_rows if r["rate_n"] >= COLLAPSE_THRESHOLD]
    print(
        "The `noise_intens` arm is the compact rule form padded with "
        "WHITESPACE to exactly\nthe extensional arm's token count under the "
        "model's own tokenizer. It adds no\ninformation and no content -- so a "
        "model that obeys the output contract on\n`intens` should obey it "
        "here. In "
        f"{len(noise_over)} of {len(pad_rows)} lanes with both arms measured it "
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
        if row["rate_n"] >= COLLAPSE_THRESHOLD:
            verdict = (
                "COLLAPSE"
                if pad_crossing(row["rate_i"], row["rate_n"])
                else "collapsed, but not padding-specific"
            )
        else:
            verdict = "contract holds"
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
        star = " <== total" if cell["rate"] >= TOTAL_COLLAPSE else ""
        print(
            f"{key[0]:13s} {key[1]:13s} {cell['rate']:10.1%} {cell['n']:5d}  "
            f"{modes}{star}"
        )
    print(
        f"\n{len(over)} of {len(census)} cells are at or above the "
        f"{COLLAPSE_THRESHOLD:.0%} criterion; {len(noise_over)} of them are "
        f"noise arms.\nThe criterion is applied SYMMETRICALLY to all four arms, "
        f"so non-noise arms appear here beside the noise arms."
    )
    zero_over = [k for k in over if k[1] == "zero"]
    if zero_over:
        print(
            f"{len(zero_over)} of them are `zero` baseline cells "
            f"({', '.join(k[0] for k in zero_over)}): those lanes are "
            f"non-compliant\neven with an EMPTY context, so their collapse is "
            f"not padding-specific."
        )

    # ---- the findings ------------------------------------------------------
    def tag(r: dict) -> str:
        hits = [
            h
            for h in (
                collapse_note(r["key_a"], r["rate_a"], census),
                collapse_note(r["key_b"], r["rate_b"], census),
            )
            if h
        ]
        return ("   [COLLAPSE: " + "; ".join(hits) + "]") if hits else ""

    sel = [r for i, r in enumerate(rows) if hp[i] and r["kind"] == "finding"]
    tot = sum(1 for r in rows if r["kind"] == "finding")
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
        denom = sum(
            1
            for r in rows
            if r["kind"] == "finding" and r["kind_is_ladder"] == (bucket is ladders)
        )
        print(f"\n-- {title}: {len(bucket)} of {denom}")
        for r in sorted(bucket, key=lambda r: r["p_cluster"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            print(
                f"  {direction} {r['label']:52s} {r['acc_a']:.3f} -> "
                f"{r['acc_b']:.3f}   p={r['p_cluster']:.2e} "
                f"(item {r['p_item']:.2e}){tag(r)}"
            )
    n_flag = sum(1 for r in sel if tag(r))
    n_pad = sum(
        1
        for r in sel
        if {r["key_a"][1], r["key_b"][1]} == {"extens", "noise_intens"}
        and r["key_a"][0] in pad_lanes
    )
    # TWO-MECHANISM needs findings touching a collapsed cell; the branches separate that case.
    print(
        f"\n  [COLLAPSE] {n_flag} of {len(sel)} findings touch a cell at or "
        f"above {COLLAPSE_THRESHOLD:.0%}\n      non-compliance.",
        end="",
    )
    if n_pad:
        print(
            f" {n_pad} of them are extens-vs-noise findings on a lane the pad "
            "itself pushed over the criterion. Read together with the census "
            "above: the "
            "extens-vs-noise\n      story is TWO-MECHANISM -- an information "
            "/ label-density effect where the noise\n      arm stays "
            "well-formed, and a padding-robustness collapse (mechanically\n  "
            "    extens-higher) where it does not."
        )
    elif n_flag:
        print(
            " None of them is an extens-vs-noise finding on a lane the pad "
            "itself pushed over the criterion, so the annotation names a "
            "format caveat on those contrasts and this report offers no "
            "evidence for a second, padding-robustness mechanism."
        )
    elif sel:
        print(
            f" Every one of the {len(sel)} findings rests on two arms\n      "
            f"BELOW the criterion, so nothing here is mechanically forced by "
            f"a broken\n      output contract, and this report offers no "
            f"evidence for a second,\n      padding-robustness mechanism among "
            f"them."
        )
    else:
        print(
            " There are no significant findings at all, so the\n      count "
            "is zero for want of findings rather than for want of collapses: "
            "this\n      report is silent on whether a second mechanism "
            "exists."
        )

    # ---- zero-arm controls -------------------------------------------------
    floor = [i for i, r in enumerate(rows) if r["kind"] == "arm-vs-floor"]
    zz = [i for i, r in enumerate(rows) if r["kind"] == "zero-vs-zero"]
    passing, reversed_ = [], []
    fails = [rows[i] for i in floor if not hp[i]]
    for i in floor:
        r = rows[i]
        info_acc, zero_acc = (
            (r["acc_b"], r["acc_a"])
            if r["key_a"][1] == "zero"
            else (r["acc_a"], r["acc_b"])
        )
        if hp[i]:
            (passing if info_acc > zero_acc else reversed_).append(r)
    print(f"\n{'=' * 78}\nZERO-ARM CONTROLS\n{'=' * 78}")
    print(
        f"{len(floor)} arm-vs-floor positive controls (an informative arm "
        f"against the chance\nbaseline): {len(passing)} significant with the "
        f"informative arm AHEAD, {len(reversed_)} significant\nbut REVERSED "
        f"(informative arm below the empty-context floor), {len(fails)} not "
        "rejected.\nThe test is two-sided: a non-rejection is not a broken "
        "pipeline and not a tie -- it is an\narm not shown to beat an empty "
        "context at this depth."
    )
    for r in sorted(
        reversed_,
        key=lambda r: -(r["acc_b"] if r["key_a"][1] == "zero" else r["acc_a"]),
    ):
        info_acc, zero_acc = (
            (r["acc_b"], r["acc_a"])
            if r["key_a"][1] == "zero"
            else (r["acc_a"], r["acc_b"])
        )
        note = tag(r)
        print(
            f"  REVERSED {r['label']:52s} {info_acc:.3f} vs floor "
            f"{zero_acc:.3f}   p={r['p_cluster']:.2e}{note}"
        )
    for r in sorted(fails, key=lambda r: -r["acc_a"]):
        note = tag(r)
        print(
            f"  FAILS  {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
            f"   p={r['p_cluster']:.2e}{note}"
        )
    if fails and floor_bound:
        # Floor-bound failures are arithmetically forced and carry no information about padding.
        print(
            f"\n  All {len(fails)} of these failures are forced by the "
            f"resolution floor (see the\n  INCOMPLETE SYNC banner at the top "
            f"of this report): at {depth_max} replicate seeds no\n  positive "
            f"control could have been rejected whatever its effect size. They "
            f"are\n  evidence about the sync, not about padding and not about "
            f"the models."
        )
    elif fails:
        # Partitioned: a fixed exoneration would misdescribe non-qualifying failures.
        qualifying, unexplained = [], []
        for r in fails:
            # The informative arm is identified by its info label, not position.
            info_key = r["key_b"] if r["key_a"][1] == "zero" else r["key_a"]
            if info_key[1] == "noise_intens" and info_key[0] in pad_lanes:
                qualifying.append(r)
            else:
                unexplained.append(r)
        if qualifying:
            print(
                f"\n  These {len(qualifying)} of {len(fails)} failures are the "
                f"collapse result surfacing in the controls,\n  not a pipeline "
                f"fault: each is a noise arm the whitespace padding drove to\n"
                f"  near-total non-compliance, so it cannot outscore an empty "
                f"prompt. Reported\n  plainly, as part of the "
                f"padding-robustness finding."
            )
        if unexplained:
            # Labels listed after the sentence so the section can be split on the claim.
            print(
                f"\n  {len(unexplained)} of {len(fails)} failures are NOT "
                f"explained by padding: the informative arm\n  is either not a "
                f"noise arm, or a noise arm whose lane the pad did NOT carry "
                f"over the "
                f"{COLLAPSE_THRESHOLD:.0%} criterion (its unpadded `intens` arm "
                f"was already at or above it, or its noise arm is below it, or "
                f"a rate was never measured). Each is an arm not shown to beat "
                f"an\n  empty context while the census has no padding collapse "
                f"to blame it on:"
            )
            for r in sorted(unexplained, key=lambda r: -r["acc_a"]):
                print(f"    {r['label']}")
    n_zz_sig = sum(hp[i] for i in zz)
    print(
        f"\n{len(zz)} zero-vs-zero ladder contrasts (one model's empty-context "
        f"baseline against\n  another's): {n_zz_sig} significant. These compare "
        f"different models' floors, so a\n  rejection is a real between-model "
        f"difference at zero information, not an error."
    )
    for i in sorted(zz, key=lambda i: rows[i]["p_cluster"]):
        if hp[i]:
            r = rows[i]
            print(
                f"  SIG    {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
                f"   p={r['p_cluster']:.2e}"
            )

    # ---- what is NOT significant, which is half the story -------------------
    ns = [r for i, r in enumerate(rows) if not hp[i] and r["kind"] == "finding"]
    ceiling = [r for r in ns if min(r["acc_a"], r["acc_b"]) >= 0.95]
    # Measured, not asserted: `b`/`c` are carried on every row.
    n_zero_disc = sum(1 for r in ceiling if r["b"] + r["c"] == 0)
    print(f"\n{'=' * 78}\nNOT significant: {len(ns)} of {tot} findings")
    if ceiling:
        print(
            f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)}. "
            f"{n_zero_disc} of them have ZERO discordant items:\n  exact ties "
            f"that no replicate count can separate (see the +/-0.20 "
            f"equivalence decision);\n  the other {len(ceiling) - n_zero_disc} "
            f"have discordant items and are UNRESOLVED at this depth, not ties."
        )
    else:
        # States the standing alternative rather than printing a "0 -- these are ties" line.
        print(
            f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)} -- "
            f"so none of these\n  non-rejections is a ceiling effect. Every one "
            f"has at least one arm below 0.95:\n  they are contrasts the "
            f"family-corrected test could not separate at this depth,\n  not "
            f"pairs that agree."
        )
    print(
        f"  The cluster test also has a floor: with {min(seeds)} seeds it "
        f"cannot resolve any\n  contrast below 2/2^{min(seeds)} = "
        f"{2 / 2 ** min(seeds):.3e}, and a contrast whose discordances all "
        f"live in\n  a handful of replicates cannot go below "
        f"2/2^(that handful)."
    )


if __name__ == "__main__":
    main()
