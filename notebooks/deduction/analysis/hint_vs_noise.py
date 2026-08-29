"""Deduction analogue of the induction `extens` vs `noise_intens` contrast.

Both legs ask the same basic question: does the model do better because the
context carries INFORMATION, or merely because the context is longer? The two
legs vary DIFFERENT things to test this question. The scope note below states
exactly what this leg varies, before you read any comparison.

  induction:  `extens`  (fully enumerated position -> label listing)
              vs `noise_intens` (the compact rule, whitespace-padded to exactly
              the same TOKEN count under the model's own tokenizer)

  deduction:  `hint:3` vs `noise:3` -- see the scope note below

Both contrasts hold the context size fixed and vary only its content. So a
significant `hint:3` > `noise:3` result shows the model uses the hint's
content, not just its bulk.

Scope of the deduction arm -- narrower than the induction one
-------------------------------------------------------------
`hint:3` and `noise:3` are byte-identical through the
current goal, the full tactic state, the proof so far, and the premises used
in the next tactic, including their signatures and full source. The two rungs
differ in ONE block only. `hint:3` ends with a trailing 1-hop TRANSITIVE
premise-closure block. `noise:3` replaces that block with padding of the same
token count. So this leg asks one narrow question: does 1-hop transitive
background help, ON TOP OF an already-complete direct-premise context? It
does NOT ask whether the context carries information at all. This is NOT the
deduction analogue of the induction extens-vs-noise contrast: that contrast
swaps the ENCODING of the whole evidence set. The two legs manipulate
different things, so their results do not carry over between legs.

Pairing: this leg matches cells on ``(theorem_id, k)`` WITHIN one model. So
each model acts as its own control, and the two rungs compare identical
theorems at identical prefix depth. Exact McNemar is the right test HERE, and it stays
the primary test. This differs from the two family-ladder families, which
need a cluster test: this contrast contributes exactly ONE
cell per theorem per model, so the pairs are truly independent. No cluster
correction applies here.

Multiplicity: this leg uses Holm-Bonferroni over the 21 models at FWER 0.05,
matching the directive for the induction leg. Holm stays valid under
arbitrary dependence, which this family needs, because the 21 tests share
one theorem set.

Run:
    uv run --no-project --with numpy --with scipy python \
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


def load_rungs(path: Path, model: str) -> dict:
    """Map each ``(theorem_id, k)`` cell to its rung outcomes.

    Read one model's row file and group its replicate-0 cell rows by
    ``(theorem_id, k)``. Each cell maps a rung label (`RUNG_INFO` or
    `RUNG_NOISE`) to a 0/1 outcome, taken from the earliest surviving row
    for that cell and rung.

    This function reads rows through ``power_analysis.grade_verdicts``, the
    single implementation of this study's two row rules. The FIRST row
    whose verdict is a measurement wins: a later retry is an independent
    draw, and a last-wins rule would report pass@N as pass@1. A cell with
    no measurable row stays ABSENT, not scored 0.

    This function calls `reject_unverified_verdicts` at INGESTION, before
    the rung filter below. That call refuses any row that still carries the
    generation-time ``"unverified"`` sentinel in its ``"verdict"`` field. An
    ungraded row may sit in a rung this comparison does not even read. Even
    so, it shows that the verification pass on this file did not finish.
    Without this check, such a row could hide in an unrelated rung and go
    unnoticed.

    Parameters
    ----------
    path : Path
        Path to one model's ``verified_rows.jsonl`` row file.
    model : str
        Model name. This function does not read it.

    Returns
    -------
    dict
        A ``defaultdict(dict)`` keyed by ``(theorem_id, k)``. Each value maps
        a rung label (`RUNG_INFO` or `RUNG_NOISE`) to its graded outcome
        (``1`` for success, ``0`` for a real failure).
    """
    reject_superseded([path])
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    reject_unverified_verdicts(rows, "verdict", path)
    out: dict = defaultdict(dict)
    for row in rows:
        if row.get("kind") != "cell" or row.get("replicate_idx", 0) != 0:
            continue
        if row.get("rung") not in (RUNG_INFO, RUNG_NOISE):
            continue
        # None means this row is not a measurement. It does not score the
        # cell or claim it, so the next row still gets its chance.
        grade = grade_verdicts([row.get("verdict")])
        if grade is None:
            continue
        cell = (row["theorem_id"], row["k"])
        if row["rung"] in out[cell]:
            continue  # earliest surviving attempt already recorded
        out[cell][row["rung"]] = grade
    return out


def _power_pi(n_disc: int, k_crit: int, target: float = 0.80) -> float:
    """Find the smallest pi whose exact power reaches `target`.

    Use bisection to find the smallest pi >= 0.5 whose exact power, at the
    given rejection region, reaches `target`.

    The rejection region is ``{b <= k_crit} U {b >= n_disc - k_crit}``. This
    is the two-sided exact-McNemar region at threshold `k_crit`.
    Under a true discordant-favour probability pi, the count b follows a
    Binomial(n_disc, pi) distribution. So exact power has a CLOSED FORM, and
    this function uses deterministic bisection instead of simulation. It
    needs no seed, carries no Monte Carlo error, and returns the same number
    on every run.

    Parameters
    ----------
    n_disc : int
        Total discordant pair count (``b + c`` in the McNemar table).
    k_crit : int
        Rejection threshold. The region rejects when ``b <= k_crit`` or
        ``b >= n_disc - k_crit``.
    target : float, default 0.80
        Target power level to reach or exceed.

    Returns
    -------
    float
        The smallest pi in ``[0.5, 1.0]`` whose exact binomial power, at
        this rejection region, reaches at least `target`.

    Notes
    -----
    Runs a fixed 200-step bisection over ``[0.5, 1.0]``. The loop count is
    fixed, so the function needs no convergence check.
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
        pairs = load_rungs(args.rows_dir / model / "verified_rows.jsonl", model)
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

    # A null result means nothing without the effect it could have caught.
    # So this report states the MINIMUM DETECTABLE EFFECT. It does not let
    # the reader assume the test had enough power.
    #
    # This report tracks TWO different quantities. An earlier version of
    # this report conflated them: it called the first one "the MDE".
    #
    #   boundary  -- the most balanced discordant split that still clears
    #                Holm's FIRST (strictest) threshold, at the model's
    #                OBSERVED discordant total. This is the smallest effect
    #                that WOULD HAVE BEEN significant, had it landed exactly
    #                at the boundary. It is a ~50%-power figure, not a
    #                design's MDE.
    #   mde80     -- the smallest TRUE effect this design detects 80% of the
    #                time: the smallest pi = P(a discordant pair favours
    #                hint:3) whose exact binomial power, at that same
    #                threshold, reaches 0.80, converted back to accuracy
    #                points.
    #
    # Both quantities condition on the observed discordant total. That total
    # is itself random, so an unconditional MDE would be larger still.
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
        print("So this null rules out LARGE effects of 1-hop transitive premise "
              "background,\nnot small ones. For scale, the induction leg's five "
              "well-formed extens-vs-noise\neffects run 0.155-0.866 -- far above "
              "either column here.")
    n_neg = sum(1 for r in rows if r["acc_i"] < r["acc_n"])
    n_pos = sum(1 for r in rows if r["acc_i"] > r["acc_n"])
    print(f"\nDirection of the point estimates, ignoring significance: "
          f"{n_pos} favour hint:3,\n  {n_neg} favour noise:3, "
          f"{len(rows) - n_pos - n_neg} exactly tied -- consistent with no "
          f"effect rather than\n  a real effect this design cannot resolve.")
    print(f"\nNot significant: {len(rows) - len(sig)} -- listed so a null is not "
          f"mistaken for an untested contrast:")
    for i, r in enumerate(rows):
        if not rej[i]:
            print(f"  {r['model']:30s} {r['acc_i']:.3f} vs {r['acc_n']:.3f}  "
                  f"p={r['p']:.2e}  (discordant {r['b'] + r['c']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
