"""Holm and Hochberg significance report over the PRIMARY contrast family.

Applies step-down Holm (1979) at FWER = 0.05 to the 210 pre-registered
PRIMARY contrasts, using the exact seed-level sign-flip test
(``paired_analysis.signflip_exact_p``) as PRIMARY: the independent unit is
the replicate seed, not the mark, so a collapsed arm's 9 correlated harmonic
items count as one piece of evidence, not nine. Item-level McNemar and
unpaired CMH stay descriptive columns; their gap to the cluster p is the
design effect. Hochberg (1988) is a sensitivity check only, since its
positive-dependence requirement (MTP2, Sarkar 1998) is unverified for 210
statistics sharing models, seeds and harmonics. Nothing is excluded: cells
at or above COLLAPSE_THRESHOLD non-compliance are annotated, never removed.

Run:
    .venv/bin/python notebooks/induction/analysis/significance_report.py
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from statsmodels.stats.multitest import multipletests

from smolbench.evals.quiz import COMPLIANT
# EMPTY is imported rather than spelled "empty" here, because a literal would
# keep parsing cleanly and silently read 0 if parsing.py ever renamed the
# label -- turning a padding collapse into an apparently empty-free arm.
from smolbench.evals.parsing import EMPTY

from power_analysis import (  # noqa: E402
    ALPHA,
    MODELS,
    build_primary_contrasts,
)
from paired_analysis import (  # noqa: E402
    aligned,
    cmh_unpaired_p,
    holm,
    load_marks,
    mcnemar_exact_p,
    seed_diffs,
    signflip_exact_p,
)

#: A cell at or above this share of non-compliant completions gets a mechanism
#: annotation on every contrast it touches, applied symmetrically to all arms.
COLLAPSE_THRESHOLD = 0.25

#: Above this share the arm has stopped emitting parseable answers at all,
#: not merely degraded. Used only to word the census, never to fence.
TOTAL_COLLAPSE = 0.95


def hochberg(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Hochberg (1988) step-up rejections at familywise level `alpha`.

    Thin wrapper over ``statsmodels.stats.multitest.multipletests`` with
    ``method="simes-hochberg"``, uniformly at least as powerful as Holm
    where its positive-dependence condition holds (see module docstring).
    """
    # Unstable sort is safe here for the same tie-monotonicity reason as
    # paired_analysis.holm.
    reject, _pvals_corrected, _alphac_sidak, _alphac_bonf = multipletests(
        pvals, alpha=alpha, method="simes-hochberg"
    )
    return np.asarray(reject, dtype=bool)


def compliance_census(compliance: dict) -> dict:
    """Measure non-compliance per ``(model, info)`` cell, from an already-parsed tree.

    Consumes `paired_analysis.load_marks`'s third return value rather than
    re-walking and re-parsing the tree, so the census and the contrasts can
    never disagree about which replicates a cell contains.

    Returns
    -------
    dict
        Cell key -> ``rate``, ``n``, ``modes`` (Counter of violation labels),
        and ``per_seed`` (so a caller can re-take the rate over any seed
        subset, as the padding table does). Cells with no marks at all are
        omitted -- an unmeasured cell must never read as compliant or
        collapsed.
    """
    out = {}
    # Iterates the loader's own mapping, so cell order follows MODELS x INFOS.
    for key, by_seed in compliance.items():
        vals = [v for seed_vals in by_seed.values() for v in seed_vals]
        if not vals:
            continue
        per_seed = {
            seed: (sum(1 for v in seed_vals if v != COMPLIANT), len(seed_vals))
            for seed, seed_vals in by_seed.items()
        }
        out[key] = dict(
            rate=sum(v != COMPLIANT for v in vals) / len(vals),
            n=len(vals), modes=Counter(v for v in vals if v != COMPLIANT),
            per_seed=per_seed,
        )
    return out


def common_seed_rate(cell: dict, seeds) -> float | None:
    """Non-compliance rate of one census `cell` (from `compliance_census`), restricted to `seeds`.

    Pools the counts before dividing -- ``sum(noncompliant) / sum(marks)`` --
    rather than averaging per-seed rates, so a seed with 2 marks does not
    weigh the same as one with 9. Returns `None`, not 0.0, when the subset
    has no marks at all, so an unmeasured subset cannot publish as perfectly
    compliant.
    """
    counts = [cell["per_seed"][s] for s in seeds if s in cell["per_seed"]]
    total = sum(t for _nc, t in counts)
    if total == 0:
        return None
    return sum(nc for nc, _t in counts) / total


def collapse_note(key, census: dict) -> str:
    """One-line mechanism annotation for a cell; ``""`` below `COLLAPSE_THRESHOLD`.

    Carries the measured rate and dominant failure mode -- "99.6%
    multiple-values" vs "28.5% empty" are different results a bare COLLAPSE
    label would erase. Also ``""`` for a cell missing from `census`.
    """
    cell = census.get(key)
    if cell is None or cell["rate"] < COLLAPSE_THRESHOLD:
        return ""
    top = cell["modes"].most_common(1)
    mode = f", mostly {top[0][0]}" if top else ""
    return f"{key[0]}/{key[1]} {cell['rate']:.1%} non-compliant{mode}"


def classify(key_a, key_b) -> str:
    """Bucket a contrast from its two ``(model, info)`` keys.

    ``"finding"`` (two informative arms), ``"arm-vs-floor"`` (one
    informative arm against the chance baseline, a positive control), or
    ``"zero-vs-zero"`` (two baseline arms, null by construction). The last
    two are jointly the zero-arm controls.
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
        print(f"   {sign}{r['label']:52s} item {r['p_item']:.3e} -> "
              f"cluster {r['p_cluster']:.3e}")


def _step_boundary(pvals: np.ndarray, rows: list, m: int, n_rej: int) -> None:
    """Print the Holm step-down around where it stopped (rank / p / own threshold).

    A count alone hides how close the decision was; the two ranks either side of
    the boundary show whether the family is comfortably separated or resting on
    one contrast. `pvals` is in `rows` order, `n_rej` the Holm rejection count.
    """
    order = np.argsort(pvals, kind="stable")
    print("\nHolm step-down at the boundary (rank / p / own threshold):")
    for i in range(max(n_rej - 2, 0), min(n_rej + 2, m)):
        idx = order[i]
        mark = "REJ " if i < n_rej else "stop"
        print(f"  {mark} rank {i + 1:3d}  p={pvals[idx]:.4e}  "
              f"thr={ALPHA / (m - i):.4e}   {rows[idx]['label']}")


def main() -> None:
    """Run the significance report and print it.

    Every narrative conclusion below is conditional on the counts beside it
    (see the depth guard and its floor_bound branches), rather than a
    sentence printed unconditionally regardless of what the data shows.
    """
    # ONE walk of the tree: the census reads the same parse as the contrasts.
    correct, valid, compliance = load_marks()
    contrasts = build_primary_contrasts()
    census = compliance_census(compliance)

    rows = []
    for label, key_a, key_b in contrasts:
        a, b, sidx = aligned(correct, valid, key_a, key_b, drop_invalid=False)
        nb, nc = int((a & ~b).sum()), int((~a & b).sum())
        rows.append(dict(
            label=label, key_a=key_a, key_b=key_b,
            acc_a=a.mean(), acc_b=b.mean(), n=a.size,
            # Discordance counts kept under `paired_analysis`'s row spelling (`b`/`c`):
            # the NOT-significant section counts ceiling pairs with zero discordant items.
            b=nb, c=nc,
            n_seeds=int(np.unique(sidx).size),
            p_cluster=signflip_exact_p(seed_diffs(a, b, sidx)),
            p_item=mcnemar_exact_p(nb, nc),
            p_unpaired=cmh_unpaired_p(a, b, sidx),
            kind=classify(key_a, key_b),
            kind_is_ladder="ladder" in label,
        ))

    p_cl = np.array([r["p_cluster"] for r in rows])
    p_item = np.array([r["p_item"] for r in rows])
    p_unp = np.array([r["p_unpaired"] for r in rows])
    m = len(rows)

    hp = holm(p_cl, ALPHA)
    hb = hochberg(p_cl, ALPHA)
    # Every correction pass this report needs, taken ONCE: each is O(m log m)
    # and the summary table below would otherwise re-run three of them.
    h_item = holm(p_item, ALPHA)
    rej_by_test = {
        "seed sign-flip (PRIMARY)": (p_cl, {"Holm": hp, "Hochberg": hb}),
        "item McNemar (descript.)": (p_item, {"Holm": h_item,
                                              "Hochberg": hochberg(p_item, ALPHA)}),
        "unpaired CMH (descript.)": (p_unp, {"Holm": holm(p_unp, ALPHA),
                                             "Hochberg": hochberg(p_unp, ALPHA)}),
    }

    # ---- DEPTH GUARD: is any rejection arithmetically reachable at all? -----
    # Depths come from `rows`, not the census or the loader: a contrast is
    # sign-flipped over the seeds its two arms share, so its own `n_seeds` is
    # the only depth that bounds its p.
    #
    # Gates on the DEEPEST contrast, not the shallowest: the smallest p any
    # contrast in the family can attain is the floor of the deepest one
    # (2/2**S at depth S), and Holm rejects nothing unless that smallest p
    # clears ALPHA/m. Gating on the shallowest instead would fire the banner
    # on a family where every other contrast is perfectly resolvable -- an
    # unearned conclusion. The shallowest depth is still printed, since it
    # bounds the contrasts that touch it.
    depth_min = min(r["n_seeds"] for r in rows)
    depth_max = max(r["n_seeds"] for r in rows)
    holm_first_step = ALPHA / m
    floor_deepest = 2 / 2 ** depth_max
    floor_bound = floor_deepest > holm_first_step
    if floor_bound:
        print(f"\n{'!' * 78}\nINCOMPLETE SYNC -- the family sits below the "
              f"sign-flip resolution floor\n{'!' * 78}")
        print(f"  Deepest contrast: {depth_max} common replicate seeds. The "
              f"exact sign-flip test\n  enumerates 2^S assignments, so the "
              f"smallest p ANY contrast in this family can\n  return is "
              f"2/2**{depth_max} = {floor_deepest:.3e}. Holm's first-step "
              f"threshold is\n  ALPHA/m = {ALPHA} / {m} = "
              f"{holm_first_step:.4e}, and "
              f"{floor_deepest:.3e} > {holm_first_step:.4e}.\n"
              f"  NO contrast is rejectable at this depth, at ANY effect size "
              f"-- including the\n  arm-vs-floor positive controls, which will "
              f"all read as FAILS below. A null\n  result here is an INCOMPLETE "
              f"SYNC, not a finding: every count printed below is\n  a "
              f"statement about replicate depth, not about the models. The fix "
              f"is to finish\n  sync_down() and re-run, not to read the "
              f"sections that follow.\n"
              f"  (Shallowest contrast: {depth_min} seeds, floor 2/2**"
              f"{depth_min} = {2 / 2 ** depth_min:.3e} -- that is\n  the "
              f"depth the closing NOT-significant paragraph quotes, so the two "
              f"floors differ\n  by design on a ragged tree: this banner asks "
              f"whether ANYTHING is rejectable, so\n  it takes the most "
              f"favourable depth in the family.)\n")

    seeds = {r["n_seeds"] for r in rows}
    print(f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}")
    print(f"Replicate depth: n = {min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} "
          f"matched items per contrast, over "
          f"{min(seeds)}-{max(seeds)} replicate seeds")
    # Computed from the landed data, not hard-coded, so a short sync cannot
    # print a depth the marks do not have (at full depth: 270 / 30 / 2^30).
    mx_n, mx_s = max(r["n"] for r in rows), max(seeds)
    print("PRIMARY TEST: exact seed-level sign-flip randomization over the "
          "per-seed arm\n  differences. The seed is the unit the design "
          "randomizes -- one label alphabet\n  and ONE SHARED ANSWER VECTOR per "
          f"replicate, reused by all 9 harmonic items and\n  by all four info "
          f"arms -- so the {mx_n} marks are {mx_s} clusters of 9, not {mx_n}\n  "
          f"independent pairs. Exact (2^{mx_s} assignments enumerated by DP), "
          "deterministic,\n  and equal to exact McNemar when every cluster is a "
          "singleton.\n")

    print(f"{'test':26s} {'procedure':10s} {'rejected':>9s}  "
          f"{'uncorrected p<0.05':>19s}")
    print("-" * 70)
    for name, (pv, rej_by) in rej_by_test.items():
        for proc, rej in (*rej_by.items(), ("Bonferroni", pv <= ALPHA / m)):
            print(f"{name:26s} {proc:10s} {int(rej.sum()):9d}  "
                  f"{int((pv < ALPHA).sum()):19d}")

    n_lad_all = sum(1 for r in rows if r["kind_is_ladder"])
    print(f"\nPrimary rejections split over the whole family: "
          f"{sum(hp[i] for i in range(m) if rows[i]['kind_is_ladder'])} of "
          f"{n_lad_all} LADDER contrasts, "
          f"{sum(hp[i] for i in range(m) if not rows[i]['kind_is_ladder'])} of "
          f"{m - n_lad_all} INFO-ARM contrasts\n  (both counts include the "
          f"zero-arm controls; the findings-only split is further down).")

    lost = [rows[i] for i in range(m) if h_item[i] and not hp[i]]
    gained = [rows[i] for i in range(m) if hp[i] and not h_item[i]]
    print(f"\nCost of the correction: Holm loses {len(lost)} and gains "
          f"{len(gained)} against the item-level p.")
    _print_signed(lost, "-", "p_item")
    _print_signed(gained, "+", "p_cluster")
    n_lad = sum(1 for r in lost if r["kind_is_ladder"])
    # Three cases, because the loss set means different things in each: (1)
    # floor-bound, where Holm rejects nothing so `lost` carries no clustering
    # information at all; (2) ladder-dominated, where ladder contrasts are
    # genuinely among the ones the correction costs; (3) no ladder loss,
    # stated as its own branch rather than printed unconditionally, since (2)
    # would otherwise assert the inverse of the data whenever n_lad is 0.
    if lost and floor_bound:
        print(f"   Both counts are artifacts of the resolution floor: Holm "
              f"rejects nothing at\n   this depth, so all {len(lost)} \"losses\" "
              f"are simply the item-level rejections and\n   the clustering "
              f"correction is not what cost them -- see the INCOMPLETE SYNC\n"
              f"   banner above.")
    elif lost and n_lad:
        print(f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- the "
              f"clustering correction\n   bites the family-scaling story, not "
              f"the info-arm story.")
    elif lost:
        print(f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- all "
              f"{len(lost)} are INFO-ARM\n   contrasts. The clustering "
              f"correction bites the family-scaling story where the\n   "
              f"contrasts it costs are ladder rungs and the info-arm story "
              f"where they are not;\n   here it is the info-arm story.")

    extra = [rows[i] for i in range(m) if hb[i] and not hp[i]]
    print(f"\nHolm vs Hochberg (primary): Hochberg rejects "
          f"{'the same set' if not extra else f'{len(extra)} MORE'}")
    for r in extra:
        print(f"   +{r['label']:52s} p={r['p_cluster']:.3e}")

    _step_boundary(p_cl, rows, m, int(hp.sum()))

    # ---- COLLAPSE CENSUS: a result, not a data-quality footnote -------------
    over = sorted(
        (k for k, v in census.items() if v["rate"] >= COLLAPSE_THRESHOLD),
        key=lambda k: -census[k]["rate"],
    )
    noise_over = [k for k in over if k[1] == "noise_intens"]
    print(f"\n{'=' * 78}\nCOLLAPSE CENSUS -- padding robustness, stated as a "
          f"result\n{'=' * 78}")

    # Built before the prose below, since the intro sentence's denominator is
    # taken from these rows: a lane needs a census cell for BOTH arms, so
    # `len(MODELS)` would count lanes this comparison cannot make.
    pad_rows = []
    for model in MODELS:
        ci = census.get((model, "intens"))
        cn = census.get((model, "noise_intens"))
        if ci is None or cn is None:
            continue
        # Rates over the seeds the two arms SHARE, matching how every other
        # contrast in this chain is aligned (`paired_analysis.aligned`) --
        # the two cells are censused independently and can otherwise cover
        # different seed sets, differencing two disjoint samples.
        common = sorted(set(ci["per_seed"]) & set(cn["per_seed"]))
        rate_i = common_seed_rate(ci, common)
        rate_n = common_seed_rate(cn, common)
        if rate_i is None or rate_n is None:
            # No marks on the shared seeds: never published as 0% on a 0-seed
            # basis, so the lane is skipped as a missing census cell is.
            continue
        pad_rows.append(dict(model=model, delta=rate_n - rate_i, rate_i=rate_i,
                             rate_n=rate_n, n_common=len(common), cn=cn))

    # Mixed basis: `len(noise_over)` counts noise cells over the criterion on
    # their whole-cell census rate, while the denominator is the matched-arm
    # row count -- the two can disagree, so this is not a claim about the
    # table below it.
    print("The `noise_intens` arm is the compact rule form padded with "
          "WHITESPACE to exactly\nthe extensional arm's token count under the "
          "model's own tokenizer. It adds no\ninformation and no content -- so a "
          "model that obeys the output contract on\n`intens` should obey it "
          "here. In "
          f"{len(noise_over)} of {len(pad_rows)} lanes it does not, and the table "
          f"below separates the\nlanes where the PAD is responsible from the "
          f"lanes that were already failing the\ncontract unpadded. That is a "
          f"finding about padding robustness in its own right,\nand it is "
          f"reported here rather than used as grounds for exclusion.\n")

    # The causal claim is scoped to what is actually computed: matched seeds.
    print(f"PADDING EFFECT ON COMPLIANCE, over the {len(pad_rows)} lanes with "
          "both arms measured\n(`intens` is the same rule text, unpadded) -- so "
          "the delta is attributable to the\nwhitespace, ON THE SEEDS BOTH ARMS "
          "COVER. `n` is how many matched replicates\nthat is:\n")
    print(f"{'lane':13s} {'intens':>8s} {'noise':>8s} {'delta':>8s} "
          f"{'noise empty':>12s} {'n':>4s}  verdict")
    print("-" * 78)
    # delta descending, ties broken by lane name so the order is deterministic.
    for row in sorted(pad_rows, key=lambda r: (-r["delta"], r["model"])):
        cn, delta = row["cn"], row["delta"]
        # Mixed basis: the two rates above are common-seed, but this mode
        # share stays whole-cell -- a descriptive "what broke" column, not an
        # input to the delta or verdict, so it is left un-decomposed.
        empty = cn["modes"].get(EMPTY, 0) / cn["n"]
        if row["rate_n"] >= COLLAPSE_THRESHOLD:
            verdict = "COLLAPSE" if delta >= COLLAPSE_THRESHOLD else \
                      "collapsed, but not padding-specific"
        else:
            verdict = "contract holds"
        print(f"{row['model']:13s} {row['rate_i']:8.1%} {row['rate_n']:8.1%} "
              f"{delta:+8.1%} {empty:12.1%} {row['n_common']:4d}  {verdict}")
    n_pad = sum(1 for r in pad_rows
                if r["rate_n"] >= COLLAPSE_THRESHOLD
                and r["delta"] >= COLLAPSE_THRESHOLD)
    print(f"\n=> The pad itself pushes {n_pad} of {len(pad_rows)} lanes over the "
          f"{COLLAPSE_THRESHOLD:.0%} criterion. This is a\n   RESULT: "
          f"whitespace padding to a matched token count is not inert, it "
          f"destroys\n   the output contract in a substantial minority of "
          f"models. Every contrast that\n   touches such an arm stays in the "
          f"findings, annotated.\n")

    print("ALL cells at or above the criterion, any arm:\n")
    print(f"{'lane':13s} {'arm':13s} {'non-compl.':>10s} {'n':>5s}  "
          f"dominant failure modes")
    print("-" * 78)
    for key in over:
        cell = census[key]
        modes = ", ".join(f"{name} {cnt / cell['n']:.1%}"
                          for name, cnt in cell["modes"].most_common(3))
        star = " <== total" if cell["rate"] >= TOTAL_COLLAPSE else ""
        print(f"{key[0]:13s} {key[1]:13s} {cell['rate']:10.1%} {cell['n']:5d}  "
              f"{modes}{star}")
    print(f"\n{len(over)} of {len(census)} cells are at or above the "
          f"{COLLAPSE_THRESHOLD:.0%} criterion; {len(noise_over)} of them are "
          f"noise arms.\nThe criterion is applied SYMMETRICALLY to all four arms, "
          f"so non-noise arms appear here beside the noise arms.")
    zero_over = [k for k in over if k[1] == "zero"]
    if zero_over:
        print(f"{len(zero_over)} of them are `zero` baseline cells "
              f"({', '.join(k[0] for k in zero_over)}): those lanes are "
              f"non-compliant\neven with an EMPTY context, so their collapse is "
              f"not padding-specific.")

    # ---- the findings ------------------------------------------------------
    def tag(r):
        hits = [h for h in (collapse_note(r["key_a"], census),
                            collapse_note(r["key_b"], census)) if h]
        return ("   [COLLAPSE: " + "; ".join(hits) + "]") if hits else ""

    sel = [r for i, r in enumerate(rows) if hp[i] and r["kind"] == "finding"]
    tot = sum(1 for r in rows if r["kind"] == "finding")
    print(f"\n{'=' * 78}\nSIGNIFICANT FINDINGS (Holm, seed sign-flip): "
          f"{len(sel)} of {tot}\n{'=' * 78}")
    print("No contrast is excluded. Where an arm is at or above "
          f"{COLLAPSE_THRESHOLD:.0%} non-compliant the\ncontrast carries a "
          "[COLLAPSE] annotation naming the measured rate and mode: the\n"
          "difference is real, and the mechanism may be format collapse rather "
          "than task\ndifficulty. Both readings are stated; neither is filtered "
          "away.\n")
    ladders = [r for r in sel if r["kind_is_ladder"]]
    infos = [r for r in sel if not r["kind_is_ladder"]]
    for title, bucket in (("LADDER contrasts (scaling within a family)", ladders),
                          ("INFO-ARM contrasts (within one model)", infos)):
        denom = sum(1 for r in rows if r["kind"] == "finding"
                    and r["kind_is_ladder"] == (bucket is ladders))
        print(f"\n-- {title}: {len(bucket)} of {denom}")
        for r in sorted(bucket, key=lambda r: r["p_cluster"]):
            direction = "^" if r["acc_b"] > r["acc_a"] else "v"
            print(f"  {direction} {r['label']:52s} {r['acc_a']:.3f} -> "
                  f"{r['acc_b']:.3f}   p={r['p_cluster']:.2e} "
                  f"(item {r['p_item']:.2e}){tag(r)}")
    n_flag = sum(1 for r in sel if tag(r))
    # TWO-MECHANISM needs at least one finding that touches a collapsed cell;
    # printed unconditionally it would read as a conclusion drawn from zero
    # findings and zero collapses. The branches below separate that case from
    # significant findings none of which is collapse-adjacent (evidence
    # against a second mechanism, not merely absence of data).
    print(f"\n  [COLLAPSE] {n_flag} of {len(sel)} findings touch a cell at or "
          f"above {COLLAPSE_THRESHOLD:.0%}\n      non-compliance.", end="")
    if n_flag:
        print(f" Read together with the census above: the "
              f"extens-vs-noise\n      story is TWO-MECHANISM -- an information "
              f"/ label-density effect where the noise\n      arm stays "
              f"well-formed, and a padding-robustness collapse (mechanically\n  "
              f"    extens-higher) where it does not.")
    elif sel:
        print(f" Every one of the {len(sel)} findings rests on two arms\n      "
              f"BELOW the criterion, so nothing here is mechanically forced by "
              f"a broken\n      output contract, and this report offers no "
              f"evidence for a second,\n      padding-robustness mechanism among "
              f"them.")
    else:
        print(" There are no significant findings at all, so the\n      count "
              "is zero for want of findings rather than for want of collapses: "
              "this\n      report is silent on whether a second mechanism "
              "exists.")

    # ---- zero-arm controls -------------------------------------------------
    floor = [i for i, r in enumerate(rows) if r["kind"] == "arm-vs-floor"]
    zz = [i for i, r in enumerate(rows) if r["kind"] == "zero-vs-zero"]
    fails = [rows[i] for i in floor if not hp[i]]
    print(f"\n{'=' * 78}\nZERO-ARM CONTROLS\n{'=' * 78}")
    print(f"{len(floor)} arm-vs-floor positive controls (an informative arm "
          f"against the chance\nbaseline): {sum(hp[i] for i in floor)} "
          f"significant. A failure here is not a broken pipeline -- it is an "
          f"arm\nthat scores no better than an empty context.")
    for r in sorted(fails, key=lambda r: -r["acc_a"]):
        note = tag(r)
        print(f"  FAILS  {r['label']:52s} {r['acc_a']:.3f} vs {r['acc_b']:.3f}"
              f"   p={r['p_cluster']:.2e}{note}")
    if fails and floor_bound:
        # At a floor-bound depth every positive control fails arithmetically
        # regardless of effect size or compliance, so these failures carry no
        # information about padding -- attributing them to the pad would be
        # the same unearned conclusion the partition below exists to prevent.
        print(f"\n  All {len(fails)} of these failures are forced by the "
              f"resolution floor (see the\n  INCOMPLETE SYNC banner at the top "
              f"of this report): at {depth_max} replicate seeds no\n  positive "
              f"control could have been rejected whatever its effect size. They "
              f"are\n  evidence about the sync, not about padding and not about "
              f"the models.")
    elif fails:
        # Partitioned rather than one blanket paragraph: a fixed exoneration
        # would misdescribe whichever failures do not actually qualify (e.g.
        # a fully compliant `intens` arm the pad cannot explain).
        qualifying, unexplained = [], []
        for r in fails:
            # An arm-vs-floor contrast pairs one informative arm against the
            # `zero` baseline, but `build_primary_contrasts` does not
            # guarantee which side the baseline lands on, so the informative
            # arm is identified by its own info label rather than position.
            info_key = r["key_b"] if r["key_a"][1] == "zero" else r["key_a"]
            cell = census.get(info_key)
            # An unmeasured arm cannot support the padding explanation, so an
            # explicit None test rather than a `.get(...)["rate"]` chain.
            if (info_key[1] == "noise_intens" and cell is not None
                    and cell["rate"] >= COLLAPSE_THRESHOLD):
                qualifying.append(r)
            else:
                unexplained.append(r)
        if qualifying:
            print(f"\n  These {len(qualifying)} of {len(fails)} failures are the "
                  f"collapse result surfacing in the controls,\n  not a pipeline "
                  f"fault: each is a noise arm the whitespace padding drove to\n"
                  f"  near-total non-compliance, so it cannot outscore an empty "
                  f"prompt. Reported\n  plainly, as part of the "
                  f"padding-robustness finding.")
        if unexplained:
            # Labels are listed after this sentence, not woven into it, so the
            # section can be split on the claim and the rows found below it.
            print(f"\n  {len(unexplained)} of {len(fails)} failures are NOT "
                  f"explained by padding: the informative arm\n  is either not a "
                  f"noise arm, or is a noise arm measured BELOW the "
                  f"{COLLAPSE_THRESHOLD:.0%} criterion,\n  or was never measured "
                  f"at all. Each is an arm that scores no better than an\n  empty "
                  f"context while the census has no collapse to blame it on:")
            for r in sorted(unexplained, key=lambda r: -r["acc_a"]):
                print(f"    {r['label']}")
    print(f"\n{len(zz)} zero-vs-zero ladder contrasts (baseline against "
          f"baseline): {sum(hp[i] for i in zz)} significant\n  -- null by "
          f"construction, and they come out null.")

    # ---- what is NOT significant, which is half the story -------------------
    ns = [r for i, r in enumerate(rows) if not hp[i] and r["kind"] == "finding"]
    ceiling = [r for r in ns if min(r["acc_a"], r["acc_b"]) >= 0.95]
    # Measured, not asserted: `b`/`c` are carried on every row, so this count
    # and the ceiling count above are kept on one output line and cannot
    # drift apart across a wrap.
    n_zero_disc = sum(1 for r in ceiling if r["b"] + r["c"] == 0)
    print(f"\n{'=' * 78}\nNOT significant: {len(ns)} of {tot} findings")
    if ceiling:
        print(f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)} -- "
              f"these are ties by\n  construction, not underpowered: "
              f"{n_zero_disc} of them have ZERO discordant items, where\n  no "
              f"replicate count can separate them (see the +/-0.20 equivalence "
              f"decision).")
    else:
        # No ceiling pairs: the earned reading (ties by construction) is exactly
        # what the data does NOT show, so the branch states the alternative it
        # leaves standing rather than printing a "0 -- these are ties" line.
        print(f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)} -- "
              f"so none of these\n  non-rejections is a ceiling effect. Every one "
              f"has at least one arm below 0.95:\n  they are contrasts the "
              f"family-corrected test could not separate at this depth,\n  not "
              f"pairs that agree.")
    print(f"  The cluster test also has a floor: with {min(seeds)} seeds it "
          f"cannot resolve any\n  contrast below 2/2^{min(seeds)} = "
          f"{2 / 2 ** min(seeds):.3e}, and a contrast whose discordances all "
          f"live in\n  a handful of replicates cannot go below "
          f"2/2^(that handful).")


if __name__ == "__main__":
    main()
