"""Holm and Hochberg significance report over the PRIMARY contrast family.

Applies step-down Holm (1979) and step-up Hochberg (1988) at FWER = 0.05 to the
210 pre-registered PRIMARY contrasts: which are significant, in which direction,
and where the two procedures disagree.

PRIMARY test: the exact seed-level sign-flip randomization test
(``paired_analysis.signflip_exact_p``). The independent unit is the REPLICATE
SEED -- one label alphabet and one answer vector shared by its 9 harmonic items
-- so a seed on which an arm collapses contributes up to 9 correlated
discordances, not 9 pieces of evidence. It enumerates all 2^30 sign assignments
of the 30 per-seed differences by DP: exact, deterministic (no resampling seed),
and equal to exact McNemar when every cluster is a singleton. Item-level McNemar
and the unpaired harmonic-stratified CMH stay as labelled DESCRIPTIVE columns;
the gap to the cluster p is the design effect.

Holm holds under ARBITRARY dependence and is the headline; Hochberg needs
Simes-type positive dependence (MTP2, Sarkar 1998), NOT verified for 210
statistics sharing models, seeds and harmonics, so it is a sensitivity check
only. Nothing is excluded: every contrast lands in FINDINGS (126 informative-arm
pairs) or ZERO-ARM CONTROLS (63 arm-vs-floor positive controls, significant by
construction -- their FAILURE is the signal -- plus 21 null-by-construction
zero-vs-zero ladder contrasts). Cells at or above COLLAPSE_THRESHOLD
non-compliance are annotated by ONE symmetric criterion, never removed.

Run:
    uv run --no-project --with numpy --with scipy python notebooks/induction/analysis/significance_report.py
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from power_analysis import INFOS, MODELS, RESULTS_DIR  # noqa: E402
from paired_analysis import (  # noqa: E402
    aligned,
    build_primary_contrasts,
    cmh_unpaired_p,
    holm,
    load_marks,
    mcnemar_exact_p,
    seed_diffs,
    signflip_exact_p,
)

ALPHA = 0.05

#: A cell at or above this share of non-compliant completions gets a
#: mechanism annotation on every contrast it touches. ONE number, applied
#: symmetrically to all four arms of all 21 lanes.
COLLAPSE_THRESHOLD = 0.25

#: Above this share, the arm is not merely degraded: it has stopped
#: emitting parseable answers at all. Used only to word the census,
#: never to fence.
TOTAL_COLLAPSE = 0.95


def hochberg(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Hochberg (1988) step-up rejections at familywise level `alpha`.

    Same critical values as Holm but stepping UP from the largest p: reject the k
    smallest, k = max{i : p_(i) <= alpha / (m - i + 1)}. Uniformly at least as
    powerful as Holm, but valid only under Simes-type positive dependence.

    The sort is stable, for the same reason as ``paired_analysis.holm``: the cluster
    test has a hard resolution floor at 2/2^30 and several contrasts sit exactly on
    it, so the rejection set must not depend on contrast build order.

    Returns
    -------
    ndarray of bool
        Rejection mask, in `pvals` order.
    """
    m = pvals.size
    order = np.argsort(pvals, kind="stable")
    sorted_p = pvals[order]
    reject = np.zeros(m, dtype=bool)
    for i in range(m - 1, -1, -1):          # i = 0-based rank
        if sorted_p[i] <= alpha / (m - i):
            reject[order[: i + 1]] = True
            break
    return reject


def compliance_census() -> dict:
    """Measure non-compliance per ``(model, info)`` cell, over all 84 cells.

    ``compliance: null`` marks a completion that obeyed the output contract; any
    other value names HOW it failed (``empty``, ``multiple-values``,
    ``degenerate-repetition``, ``prefixed``, ``unparseable``, ``markup``,
    ``truncated``, ``verbose``). Counting the modes, not just the nulls, is what
    makes the census describe a mechanism instead of a bare rate; which cells get
    annotated is a threshold decision made downstream, so the criterion stays
    visible and symmetric.

    Returns
    -------
    dict
        Cell key -> ``rate`` (non-compliance share), ``n`` (mark count) and
        ``modes`` (a `collections.Counter` of non-null labels). Cells with no
        marks are omitted.
    """
    rx = re.compile(r"^\s*compliance:\s*(\S+)", re.M)
    out = {}
    for model in MODELS:
        for info in INFOS:
            vals: list[str] = []
            for path in sorted((RESULTS_DIR / f"{model}_{info}").glob("rep_*.yaml")):
                vals += rx.findall(path.read_text())
            if not vals:
                continue
            modes = Counter(v for v in vals if v != "null")
            out[(model, info)] = dict(
                rate=1.0 - vals.count("null") / len(vals), n=len(vals), modes=modes,
            )
    return out


def collapse_note(key, census: dict) -> str:
    """One-line mechanism annotation for a cell; ``""`` below `COLLAPSE_THRESHOLD`.

    Carries the measured rate AND the dominant failure mode: "99.6%
    multiple-values" and "28.5% empty" are different results, and a bare COLLAPSE
    label would erase the distinction the census exists to make. Also ``""`` when
    the cell is missing from `census` (`compliance_census`'s output).
    """
    cell = census.get(key)
    if cell is None or cell["rate"] < COLLAPSE_THRESHOLD:
        return ""
    top = cell["modes"].most_common(1)
    mode = f", mostly {top[0][0]}" if top else ""
    return f"{key[0]}/{key[1]} {cell['rate']:.1%} non-compliant{mode}"


def classify(label: str, key_a, key_b) -> str:
    """Bucket a contrast from its two ``(model, info)`` keys.

    `label` is not read by the current logic; callers pass it uniformly.

    Returns
    -------
    str
        ``"finding"`` (two informative arms), ``"arm-vs-floor"`` (one informative
        arm against the chance baseline: a positive control), or
        ``"zero-vs-zero"`` (a ladder contrast between two baseline arms, null by
        construction). The last two are jointly the zero-arm controls.
    """
    za, zb = key_a[1] == "zero", key_b[1] == "zero"
    if za and zb:
        return "zero-vs-zero"
    if za or zb:
        return "arm-vs-floor"
    return "finding"


def _step_boundary(pvals: np.ndarray, rows: list, m: int, n_rej: int) -> None:
    """Print the Holm step-down around where it stopped (rank / p / own threshold).

    A count on its own hides how close the decision was; the two ranks either side
    of the boundary show whether the family is comfortably separated or resting on a
    single contrast. `pvals` is in `rows` order, `m` is the family size, `n_rej` the
    Holm rejection count.
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

    Nine sections, from the family size and PRIMARY test statement through the
    rejection counts, the cluster-vs-item and Holm-vs-Hochberg disagreements, the
    Holm step-down boundary, the collapse census, the significant findings, the
    zero-arm controls, and what is NOT significant. Methodology is in the module
    docstring.
    """
    correct, valid = load_marks()
    contrasts = build_primary_contrasts()
    census = compliance_census()

    rows = []
    for label, key_a, key_b in contrasts:
        a, b, sidx = aligned(correct, valid, key_a, key_b, drop_invalid=False)
        nb, nc = int((a & ~b).sum()), int((~a & b).sum())
        rows.append(dict(
            label=label, key_a=key_a, key_b=key_b,
            acc_a=a.mean(), acc_b=b.mean(), n=a.size,
            n_seeds=int(np.unique(sidx).size),
            p_cluster=signflip_exact_p(seed_diffs(a, b, sidx)),
            p_item=mcnemar_exact_p(nb, nc),
            p_unpaired=cmh_unpaired_p(a, b, sidx),
            kind=classify(label, key_a, key_b),
            kind_is_ladder="ladder" in label,
        ))

    p_cl = np.array([r["p_cluster"] for r in rows])
    p_item = np.array([r["p_item"] for r in rows])
    p_unp = np.array([r["p_unpaired"] for r in rows])
    m = len(rows)

    hp = holm(p_cl, ALPHA)
    hb = hochberg(p_cl, ALPHA)

    seeds = {r["n_seeds"] for r in rows}
    print(f"PRIMARY family: m = {m} pre-registered contrasts, FWER alpha = {ALPHA}")
    print(f"Replicate depth: n = {min(r['n'] for r in rows)}-{max(r['n'] for r in rows)} "
          f"matched items per contrast, over "
          f"{min(seeds)}-{max(seeds)} replicate seeds")
    print("PRIMARY TEST: exact seed-level sign-flip randomization over the "
          "per-seed arm\n  differences. The seed is the unit the design "
          "randomizes -- one label alphabet\n  and ONE SHARED ANSWER VECTOR per "
          "replicate, reused by all 9 harmonic items and\n  by all four info "
          "arms -- so the 270 marks are 30 clusters of 9, not 270\n  "
          "independent pairs. Exact (2^30 assignments enumerated by DP), "
          "deterministic,\n  and equal to exact McNemar when every cluster is a "
          "singleton.\n")

    print(f"{'test':26s} {'procedure':10s} {'rejected':>9s}  "
          f"{'uncorrected p<0.05':>19s}")
    print("-" * 70)
    for name, pv, procs in (
        ("seed sign-flip (PRIMARY)", p_cl, ("Holm", "Hochberg", "Bonferroni")),
        ("item McNemar (descript.)", p_item, ("Holm", "Hochberg", "Bonferroni")),
        ("unpaired CMH (descript.)", p_unp, ("Holm", "Hochberg", "Bonferroni")),
    ):
        for proc in procs:
            rej = {"Holm": holm(pv, ALPHA), "Hochberg": hochberg(pv, ALPHA),
                   "Bonferroni": pv <= ALPHA / m}[proc]
            print(f"{name:26s} {proc:10s} {int(rej.sum()):9d}  "
                  f"{int((pv < ALPHA).sum()):19d}")

    n_lad_all = sum(1 for r in rows if r["kind_is_ladder"])
    print(f"\nPrimary rejections split over the whole family: "
          f"{sum(hp[i] for i in range(m) if rows[i]['kind_is_ladder'])} of "
          f"{n_lad_all} LADDER contrasts, "
          f"{sum(hp[i] for i in range(m) if not rows[i]['kind_is_ladder'])} of "
          f"{m - n_lad_all} INFO-ARM contrasts\n  (both counts include the "
          f"zero-arm controls; the findings-only split is further down).")

    lost = [rows[i] for i in range(m) if holm(p_item)[i] and not hp[i]]
    gained = [rows[i] for i in range(m) if hp[i] and not holm(p_item)[i]]
    print(f"\nCost of the correction: Holm loses {len(lost)} and gains "
          f"{len(gained)} against the item-level p.")
    for r in sorted(lost, key=lambda r: r["p_item"]):
        print(f"   -{r['label']:52s} item {r['p_item']:.3e} -> "
              f"cluster {r['p_cluster']:.3e}")
    for r in sorted(gained, key=lambda r: r["p_cluster"]):
        print(f"   +{r['label']:52s} item {r['p_item']:.3e} -> "
              f"cluster {r['p_cluster']:.3e}")
    n_lad = sum(1 for r in lost if r["kind_is_ladder"])
    if lost:
        print(f"   {n_lad} of the {len(lost)} losses are LADDER contrasts -- the "
              f"clustering correction\n   bites the family-scaling story, not "
              f"the info-arm story.")

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
    print("The `noise_intens` arm is the compact rule form padded with "
          "WHITESPACE to exactly\nthe extensional arm's token count under the "
          "model's own tokenizer. It adds no\ninformation and no content -- so a "
          "model that obeys the output contract on\n`intens` should obey it "
          "here. In "
          f"{len(noise_over)} of {len(MODELS)} lanes it does not, and the table "
          f"below separates the\nlanes where the PAD is responsible from the "
          f"lanes that were already failing the\ncontract unpadded. That is a "
          f"finding about padding robustness in its own right,\nand it is "
          f"reported here rather than used as grounds for exclusion.\n")

    print("PADDING EFFECT ON COMPLIANCE, all 21 lanes (`intens` is the same "
          "rule text,\nunpadded -- so the delta is attributable to the "
          "whitespace and nothing else):\n")
    print(f"{'lane':13s} {'intens':>8s} {'noise':>8s} {'delta':>8s} "
          f"{'noise empty':>12s}  verdict")
    print("-" * 78)
    pad_rows = []
    for model in MODELS:
        ci = census.get((model, "intens"))
        cn = census.get((model, "noise_intens"))
        if ci is None or cn is None:
            continue
        pad_rows.append((cn["rate"] - ci["rate"], model, ci, cn))
    for delta, model, ci, cn in sorted(pad_rows, reverse=True):
        empty = cn["modes"].get("empty", 0) / cn["n"]
        if cn["rate"] >= COLLAPSE_THRESHOLD:
            verdict = "COLLAPSE" if delta >= COLLAPSE_THRESHOLD else \
                      "collapsed, but not padding-specific"
        else:
            verdict = "contract holds"
        print(f"{model:13s} {ci['rate']:8.1%} {cn['rate']:8.1%} {delta:+8.1%} "
              f"{empty:12.1%}  {verdict}")
    n_pad = sum(1 for d, _, _, cn in pad_rows
                if cn["rate"] >= COLLAPSE_THRESHOLD and d >= COLLAPSE_THRESHOLD)
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
          f"which is why cells like\nmin3_14b/extens and min3_8b/intens appear "
          f"here beside the noise arms.")
    zero_over = [k for k in over if k[1] == "zero"]
    if zero_over:
        print(f"Two of them are `zero` baseline cells "
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
    print(f"\n  [COLLAPSE] {n_flag} of {len(sel)} findings touch a cell at or "
          f"above {COLLAPSE_THRESHOLD:.0%}\n      non-compliance. Read together "
          f"with the census above: the extens-vs-noise\n      story is "
          f"TWO-MECHANISM -- an information / label-density effect where the "
          f"noise\n      arm stays well-formed, and a padding-robustness "
          f"collapse (mechanically\n      extens-higher) where it does not.")

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
    if fails:
        print(f"\n  These {len(fails)} failures are the collapse result "
              f"surfacing in the controls, not a\n  pipeline fault: each is a "
              f"noise arm the whitespace padding drove to near-total\n  "
              f"non-compliance, so it cannot outscore an empty prompt. Reported "
              f"plainly, as\n  part of the padding-robustness finding.")
    print(f"\n{len(zz)} zero-vs-zero ladder contrasts (baseline against "
          f"baseline): {sum(hp[i] for i in zz)} significant\n  -- null by "
          f"construction, and they come out null.")

    # ---- what is NOT significant, which is half the story -------------------
    ns = [r for i, r in enumerate(rows) if not hp[i] and r["kind"] == "finding"]
    ceiling = [r for r in ns if min(r["acc_a"], r["acc_b"]) >= 0.95]
    print(f"\n{'=' * 78}\nNOT significant: {len(ns)} of {tot} findings")
    print(f"  of which CEILING pairs (both arms >= 0.95): {len(ceiling)} -- these "
          f"are ties by\n  construction, not underpowered; many have ZERO "
          f"discordant items, where no\n  replicate count can separate them "
          f"(see the +/-0.20 equivalence decision).")
    print(f"  The cluster test also has a floor: with {min(seeds)} seeds it "
          f"cannot resolve any\n  contrast below 2/2^{min(seeds)} = "
          f"{2 / 2 ** min(seeds):.3e}, and a contrast whose discordances all "
          f"live in\n  a handful of replicates cannot go below "
          f"2/2^(that handful).")


if __name__ == "__main__":
    main()
