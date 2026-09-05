"""Deduction leg of the "information or just length?" question: hint:3 vs noise:3.

The rungs are byte-identical through goal, tactic state, proof so far, and the
premises the next tactic uses; hint:3 then adds a trailing 1-hop TRANSITIVE
premise-closure block that noise:3 replaces with token-matched padding. So this leg
asks only whether that background helps ON TOP OF an already-complete direct-premise
context -- NOT the induction extens-vs-noise contrast, which swaps the encoding of the
whole evidence set; results do not carry between legs.

Cells are paired on (theorem_id, k) WITHIN one model, contributing exactly ONE cell per
theorem: the pairs are independent, so exact McNemar is the primary test and no cluster
correction applies (unlike the family-ladder contrasts). Holm-Bonferroni over the 21
models at FWER 0.05 (`ALPHA`), valid under arbitrary dependence.

Run:
    .venv/bin/python \
        notebooks/deduction/analysis/hint_vs_noise.py --rows-dir <dir>
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent))

from error_bars import holm  # noqa: E402
from power_analysis import (  # noqa: E402
    ALPHA,
    FAMILIES,
    MODELS,
    grade_verdicts,
    mcnemar_exact_p,
    reject_superseded,
    reject_unverified_verdicts,
)

#: The informative rung and its length-matched uninformative twin.
RUNG_INFO, RUNG_NOISE = "hint:3", "noise:3"


def load_rungs(path: Path) -> dict:
    """Map each ``(theorem_id, k)`` cell of one model to its two rung outcomes.

    Reads `path` (a model's ``verified_rows.jsonl``): only ``kind == "cell"``,
    ``replicate_idx == 0`` rows in the `RUNG_INFO` / `RUNG_NOISE` rungs, graded through
    ``power_analysis.grade_verdicts``, the single implementation of this study's row
    rules -- in particular the EARLIEST measurable row for a cell+rung wins.

    The ``replicate_idx == 0`` restriction is an ASSUMPTION that this study
    collects R=1, not a harmless filter: any row with ``replicate_idx > 0`` is
    DROPPED here, not aggregated with the cell+rung's other replicate(s). If a
    later run starts writing real replicates, this still grades only the first
    attempt per cell+rung and discards the rest silently unless warned (see
    below). ``power_analysis.N_REPLICATES_GRID`` / ``needed_replicates`` size
    how many replicates a FUTURE experiment would need for a target power --
    they do not give this function the ability to analyse replicates once
    collected; that would be a separate follow-up. Because the drop would
    otherwise be invisible, this function prints one stderr WARNING per call
    naming the dropped-row count and `path` whenever it fires.

    Returns
    -------
    dict
        ``{(theorem_id, k): {rung: 1 success | 0 real failure}}``; a cell with no
        measurable row stays ABSENT, never scored 0.

    Raises
    ------
    SystemExit
        From `reject_superseded`, or from `reject_unverified_verdicts`, which runs at
        INGESTION before the rung filter -- an ungraded row in a rung this comparison
        never reads still raises, since it proves verification did not finish.
    """
    reject_superseded([path])
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    reject_unverified_verdicts(rows, "verdict", path)
    out: dict = defaultdict(dict)
    dropped_replicates = 0
    for row in rows:
        if row.get("kind") != "cell":
            continue
        if row.get("replicate_idx", 0) != 0:
            dropped_replicates += 1
            continue
        if row.get("rung") not in (RUNG_INFO, RUNG_NOISE):
            continue
        # None = not a measurement: neither scores nor claims the cell.
        grade = grade_verdicts([row.get("verdict")])
        if grade is None:
            continue
        cell = (row["theorem_id"], row["k"])
        if row["rung"] in out[cell]:
            continue  # earliest surviving attempt already recorded
        out[cell][row["rung"]] = grade
    if dropped_replicates:
        print(
            f"WARNING: load_rungs dropped {dropped_replicates} row(s) with "
            f"replicate_idx > 0 from {path} (this study collects R=1; rows "
            f"past replicate_idx == 0 are DISCARDED, not aggregated).",
            file=sys.stderr,
        )
    return out


def _power_pi(n_disc: int, k_crit: int, target: float = 0.80) -> float:
    """Smallest pi >= 0.5 whose exact power reaches `target` at this rejection region.

    The region is the two-sided exact-McNemar one, ``{b <= k_crit} U {b >= n_disc -
    k_crit}`` for a discordant total `n_disc` (``b + c``); under a true
    discordant-favour probability pi, b is Binomial(`n_disc`, pi), so power has a
    CLOSED FORM. The fixed 200-step bisection over ``[0.5, 1.0]`` on it needs no
    convergence check: no seed, no Monte Carlo error, same number every run.
    """
    lo, hi = 0.5, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        power = binom.cdf(k_crit, n_disc, mid) + binom.sf(n_disc - k_crit - 1,
                                                          n_disc, mid)
        if power >= target:
            hi = mid
        else:
            lo = mid
    return hi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows-dir", type=Path, required=True)
    args = ap.parse_args(argv)

    rows = []
    for model in MODELS:
        pairs = load_rungs(args.rows_dir / model / "verified_rows.jsonl")
        both = [v for v in pairs.values() if RUNG_INFO in v and RUNG_NOISE in v]
        info = np.array([v[RUNG_INFO] for v in both], dtype=bool)
        noise = np.array([v[RUNG_NOISE] for v in both], dtype=bool)
        b = int((info & ~noise).sum())   # hint solved, noise not
        c = int((~info & noise).sum())   # noise solved, hint not
        rows.append(dict(model=model, n=info.size, acc_i=info.mean(),
                         acc_n=noise.mean(), b=b, c=c,
                         p=mcnemar_exact_p(b, c)))

    rej = holm(np.array([r["p"] for r in rows]), ALPHA)

    print("DEDUCTION: hint:3 vs noise:3, per model")
    print("The two rungs are byte-identical except for hint:3's trailing 1-HOP "
          "TRANSITIVE\npremise-closure block, which noise:3 replaces with "
          "token-matched padding. So this\ntests supplementary background on top "
          "of an already-complete direct-premise\ncontext -- NOT the same "
          "manipulation as the induction extens-vs-noise contrast.")
    print("Paired exact McNemar on cells matched by (theorem, k) within each "
          "model -- one cell\nper theorem per model, so no cluster correction "
          "applies here.")
    print(f"Holm-Bonferroni over m = {len(rows)} models at FWER {ALPHA}.\n")
    hdr = (f"{'model':30s} {'n':>5s} {'hint:3':>7s} {'noise:3':>8s} {'diff':>7s} "
           f"{'b/c':>9s} {'p':>10s} {'Holm':>5s}")
    print(hdr)
    print("-" * len(hdr))
    order = [m for fam in FAMILIES.values() for m in fam]
    idx = {r["model"]: i for i, r in enumerate(rows)}
    for m in order:
        r = rows[idx[m]]
        print(f"{r['model']:30s} {r['n']:5d} {r['acc_i']:7.3f} {r['acc_n']:8.3f} "
              f"{r['acc_i'] - r['acc_n']:+7.3f} {r['b']:4d}/{r['c']:<4d} "
              f"{r['p']:10.2e} {' yes ' if rej[idx[m]] else '  .  '}")

    sig = [rows[i] for i in range(len(rows)) if rej[i]]
    up = [r for r in sig if r["acc_i"] > r["acc_n"]]
    print(f"\nSignificant under Holm: {len(sig)} of {len(rows)}")
    print(f"  hint:3 HIGHER (information helps): {len(up)}")
    print(f"  noise:3 HIGHER:                    {len(sig) - len(up)}")

    # A null means nothing without the effect it could have caught, so the report
    # below states the MINIMUM DETECTABLE EFFECT and defines its two columns. What
    # it does not say: boundary is the most balanced discordant split still clearing
    # Holm's strictest threshold, and mde80 is the smallest pi = P(a discordant pair
    # favours hint:3) whose exact binomial power reaches 0.80, converted back to
    # accuracy points. Both condition on the observed discordant total, itself
    # random, so an unconditional MDE would be larger still.
    print(f"\n{'-' * 78}\nMINIMUM DETECTABLE EFFECT -- what this null actually rules out")
    print(f"{'-' * 78}")
    print(f"Both columns are evaluated at each model's OBSERVED discordant "
          f"total, against\nHolm's strictest step (alpha/{len(rows)} = "
          f"{ALPHA / len(rows):.2e}), in accuracy points.\n"
          f"  boundary = smallest effect that would have REACHED significance "
          f"(~50% power)\n  mde80    = smallest TRUE effect this design catches "
          f"80% of the time\n")
    print(f"{'model':30s} {'disc':>5s} {'needed split':>13s} {'boundary':>9s} "
          f"{'mde80':>7s} {'observed':>9s}")
    print("-" * 80)
    boundaries, mde80s = [], []
    thresh = ALPHA / len(rows)
    for m in order:
        r = rows[idx[m]]
        nd = r["b"] + r["c"]
        need = None
        for k in range(nd // 2, -1, -1):
            if mcnemar_exact_p(nd - k, k) <= thresh:
                need = k
                break
        if need is None:
            print(f"{m:30s} {nd:5d} {'IMPOSSIBLE':>13s} {'--':>9s} {'--':>7s} "
                  f"{r['acc_i'] - r['acc_n']:+9.3f}")
            continue
        boundary = (nd - 2 * need) / r["n"]
        pi = _power_pi(nd, need, target=0.80)
        mde80 = nd * (2 * pi - 1) / r["n"]
        boundaries.append(boundary)
        mde80s.append(mde80)
        print(f"{m:30s} {nd:5d} {f'{nd - need}/{need}':>13s} {boundary:9.3f} "
              f"{mde80:7.3f} {r['acc_i'] - r['acc_n']:+9.3f}")
    if boundaries:
        print(f"\nMedian significance boundary (~50% power): "
              f"{np.median(boundaries):.3f} accuracy points.")
        print(f"Median 80%-power MDE:                      "
              f"{np.median(mde80s):.3f} accuracy points "
              f"(range {min(mde80s):.3f}-{max(mde80s):.3f}).")
        print("  Provenance: mde80 is a deterministic bisection on the CLOSED-FORM binomial power,\n  so it does not move between runs.")
        print(f"Largest observed |difference|: "
              f"{max(abs(r['acc_i'] - r['acc_n']) for r in rows):.3f}.")
        # Design: "this null rules out large effects" is only a true reading of a
        # NULL result. Gate it on `sig` (the Holm-significant rows, computed at
        # :149) instead of printing it unconditionally: with sig non-empty at
        # least one model already cleared Holm, so the leg as a whole is not a
        # null, even though the MDE numbers above are still valid sensitivity
        # figures for the models that did not reach significance.
        #
        # NOTE: this paragraph used to close by quoting the induction leg's
        # extens-vs-noise effect-size range as a for-scale comparison. That
        # literal is deleted: it is a different manipulation (the induction
        # contrast swaps the encoding of the WHOLE evidence set; this leg only
        # adds a trailing block on top of an already-complete direct-premise
        # context, see the module docstring), measured on different rows, and it
        # was never computed by this script -- a hard-coded number copied from
        # another study's report can go stale here with nothing to catch it. It
        # could come back if the induction leg starts writing a machine-readable
        # summary (e.g. a results manifest with a per-contrast effect-size field,
        # checked at analysis time) that this script could load and cite by path;
        # no such file exists in the repo today (checked notebooks/induction/ and
        # smolbench/induction/ -- only analysis *scripts*, no saved results).
        if not sig:
            print("So this null rules out LARGE effects of 1-hop transitive "
                  "premise background,\nnot small ones.")
        else:
            print(f"{len(sig)} of {len(rows)} model(s) already reached "
                  f"significance under Holm (see above), so this leg is not a "
                  f"null\nresult overall -- the MDE numbers above describe the "
                  f"sensitivity of only the\n{len(rows) - len(sig)} model(s) "
                  f"that did not reach significance.")
    n_neg = sum(1 for r in rows if r["acc_i"] < r["acc_n"])
    n_pos = sum(1 for r in rows if r["acc_i"] > r["acc_n"])
    print(f"\nDirection of the point estimates, ignoring significance: "
          f"{n_pos} favour hint:3,\n  {n_neg} favour noise:3, "
          f"{len(rows) - n_pos - n_neg} exactly tied.")
    # Design: whether this split reads as "no effect" is a conclusion computed
    # from `sig` (whether ANY model already rejects the null under Holm), not a
    # constant string. With sig empty, no model rejects the null, so the split
    # above -- however lopsided -- is the kind pure noise produces just as
    # easily as a real, undetectable effect would; with sig non-empty, at least
    # one model already demonstrates a real effect, so "no effect" would
    # misdescribe the leg even if the unsigned point-estimate split still leans
    # the other way.
    if not sig:
        print("  -- consistent with no effect rather than a real effect this "
              "design cannot\n  resolve.")
    else:
        majority = ("hint:3" if n_pos > n_neg else
                    "noise:3" if n_neg > n_pos else "neither rung")
        print(f"  -- {len(sig)} of {len(rows)} model(s) already reject the "
              f"null under Holm (see above), so\n  a real effect is present in "
              f"at least those models; the unsigned split above leans\n  "
              f"toward {majority}.")
    print(f"\nNot significant: {len(rows) - len(sig)} -- listed so a null is not "
          f"mistaken for an untested contrast:")
    for i, r in enumerate(rows):
        if not rej[i]:
            print(f"  {r['model']:30s} {r['acc_i']:.3f} vs {r['acc_n']:.3f}  "
                  f"p={r['p']:.2e}  (discordant {r['b'] + r['c']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
