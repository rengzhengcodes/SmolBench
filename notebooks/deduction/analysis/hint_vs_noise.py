"""Deduction leg of the "information or just length?" question: hint:3 vs noise:3.

hint:3 and noise:3 are byte-identical except a trailing block: hint:3 adds a
1-hop transitive premise closure, noise:3 replaces it with token-matched
padding. So this leg tests only whether that background helps on top of an
already-complete direct-premise context -- not the induction extens-vs-noise
contrast, which swaps the whole evidence encoding; results do not carry
between legs.

Cells pair on (theorem_id, k) within a model, one cell per theorem, so pairs
are independent: exact McNemar is the primary test with no cluster correction
(unlike the family-ladder contrasts), Holm-Bonferroni over the 21 models at
FWER 0.05 (`ALPHA`).

Run:
    .venv/bin/python \
        notebooks/deduction/analysis/hint_vs_noise.py --s3
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

import rows_source  # noqa: E402
from error_bars import holm  # noqa: E402
from power_analysis import (  # noqa: E402
    ALPHA,
    FAMILIES,
    MODELS,
    grade_verdicts,
    mcnemar_exact_p,
    reject_unverified_verdicts,
)

#: The informative rung and its length-matched uninformative twin.
RUNG_INFO, RUNG_NOISE = "hint:3", "noise:3"


def load_rungs(path: Path) -> dict:
    """Map each ``(theorem_id, k)`` cell of one model to its two rung outcomes.

    Reads `path` (a model's ``verified_rows.jsonl``): only ``kind == "cell"``,
    ``replicate_idx == 0`` rows in the `RUNG_INFO` / `RUNG_NOISE` rungs, graded
    through ``power_analysis.grade_verdicts`` (the earliest measurable row for
    a cell+rung wins). ``replicate_idx == 0`` is an assumption that this study
    collects R=1, not a harmless filter: any row past it is dropped, not
    aggregated, so a future run that collects real replicates would silently
    be graded at R=1 -- this prints one stderr warning per call naming the
    dropped-row count when that happens.

    Parameters
    ----------
    path : Path
        Model's ``verified_rows.jsonl`` file.

    Returns
    -------
    dict
        ``{(theorem_id, k): {rung: 1 success | 0 real failure}}``; a cell with
        no measurable row stays absent, never scored 0.

    Raises
    ------
    SystemExit
        From `rows_source.reject_superseded`, or from
        `reject_unverified_verdicts` (which runs at ingestion, before the rung
        filter, so an ungraded row in a rung this comparison never reads still
        raises).
    """
    rows_source.reject_superseded([path])
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

    Power has a closed form here (b is Binomial(`n_disc`, pi) under a true
    discordant-favour probability pi), so the fixed 200-step bisection needs
    no convergence check: deterministic, same result every run.

    Parameters
    ----------
    n_disc : int
        Number of discordant pairs.
    k_crit : int
        Critical discordant-pair count.
    target : float, optional
        Target exact power.

    Returns
    -------
    float
        Smallest pi >= 0.5 whose exact power reaches `target` at this rejection
        region.
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


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the per-model hint:3 vs noise:3 comparison, print it.

    Rows come from `rows_source.resolve_rows_dir`, so ``--s3`` and
    ``--rows-dir`` are interchangeable: everything below reads one resolved
    local directory of ``<model>/verified_rows.jsonl``, one lane per model.

    There is no failure exit here -- a missing or unverified lane raises
    instead (`SystemExit` from `resolve_rows_dir` or `load_rungs`'s
    retired/ungraded checks; `FileNotFoundError` for a lane missing from the
    resolved directory).

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments to parse.

    Returns
    -------
    int
        Always 0.

    Raises
    ------
    SystemExit
        From `resolve_rows_dir` or `load_rungs`'s retired/ungraded checks.
    FileNotFoundError
        If a lane is missing from the resolved directory.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    rows_source.add_source_args(ap)
    args = ap.parse_args(argv)

    rows_dir = rows_source.resolve_from_args(args)

    rows = []
    for model in MODELS:
        pairs = load_rungs(rows_dir / model / "verified_rows.jsonl")
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

    # boundary/mde80 both condition on each model's OBSERVED discordant total,
    # itself random; an unconditional MDE would be larger still.
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
        # "rules out large effects" is only true of a null result: gated on
        # `sig` rather than printed unconditionally, since a non-empty `sig`
        # means at least one model already cleared Holm.
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
    # Whether this reads as "no effect" is computed from `sig`, not a constant
    # string: with sig empty, a lopsided split is exactly what pure noise
    # produces; with sig non-empty, at least one model already shows a real
    # effect, so "no effect" would misdescribe the leg regardless of which
    # way the unsigned split leans.
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
