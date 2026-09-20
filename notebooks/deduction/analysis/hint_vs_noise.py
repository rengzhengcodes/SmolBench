"""Compare hint:3 with length-matched noise:3.

Only the trailing 1-hop premise closure differs, so this tests supplementary
background over direct premises. Pair cells within models; use exact McNemar
and Holm over 21 models at FWER 0.05 (`ALPHA`).

Run: ``.venv/bin/python notebooks/deduction/analysis/hint_vs_noise.py --s3``.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rows_source  # noqa: E402 -- bare sibling off the sys.path insert; pylint: disable=import-error
from error_bars import holm  # noqa: E402  # pylint: disable=import-error
from power_analysis import (  # noqa: E402  # pylint: disable=import-error
    ALPHA,
    MODELS,
    grade_verdicts,
    mcnemar_exact_p,
    reject_unverified_verdicts,
)

#: Informative rung and length-matched control.
RUNG_INFO, RUNG_NOISE = "hint:3", "noise:3"


def load_rungs(path: Path) -> dict:
    """Map one model's cells to two rung outcomes.

    Use the earliest measurable ``replicate_idx == 0`` row. Later replicates
    are dropped, not aggregated, because this study collects R=1; warn when
    that would silently grade a future multi-replicate run at R=1.

    Parameters
    ----------
    path : Path
        Model ``verified_rows.jsonl`` file.

    Returns
    -------
    dict
        Cell outcomes; unmeasurable cells are absent.

    Raises
    ------
    SystemExit
        Retired or ungraded input; validate before filtering.
    """
    rows_source.reject_superseded([path])
    rows, cells, dropped_replicates = rows_source.read_cell_rows(path)
    reject_unverified_verdicts(rows, "verdict", path)
    out: dict = defaultdict(dict)
    for row in cells:
        if row.get("rung") not in (RUNG_INFO, RUNG_NOISE):
            continue
        # None is not a measurement, so it cannot score the cell.
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
    """Return the smallest pi with exact power at least `target`.

    Fixed 200-step bisection is deterministic because power is closed-form.

    Parameters
    ----------
    n_disc : int
    k_crit : int
    target : float, optional

    Returns
    -------
    float
        Minimum pi at the rejection region.
    """
    lo, hi = 0.5, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        power = binom.cdf(k_crit, n_disc, mid) + binom.sf(
            n_disc - k_crit - 1, n_disc, mid
        )
        if power >= target:
            hi = mid
        else:
            lo = mid
    return hi


def main(argv: list[str] | None = None) -> int:
    """Run and print the per-model hint:3/noise:3 comparison.

    `rows_source.resolve_rows_dir` makes ``--s3`` and ``--rows-dir`` one local
    layout. Missing or unverified lanes raise.

    Parameters
    ----------
    argv : list[str] | None, optional

    Returns
    -------
    int
        Zero.

    Raises
    ------
    SystemExit
        Source, retired, or ungraded-input failure.
    FileNotFoundError
        Missing lane.
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
        b = int((info & ~noise).sum())  # hint solved, noise not
        c = int((~info & noise).sum())  # noise solved, hint not
        rows.append(
            {
                "model": model,
                "n": info.size,
                "acc_i": info.mean(),
                "acc_n": noise.mean(),
                "b": b,
                "c": c,
                "p": mcnemar_exact_p(b, c),
            }
        )

    rej = holm(np.array([r["p"] for r in rows]), ALPHA)

    print("DEDUCTION: hint:3 vs noise:3, per model")
    print(
        "The two rungs are byte-identical except for hint:3's trailing 1-HOP "
        "TRANSITIVE\npremise-closure block, which noise:3 replaces with "
        "token-matched padding. So this\ntests supplementary background on top "
        "of an already-complete direct-premise\ncontext -- NOT the same "
        "manipulation as the induction extens-vs-noise contrast."
    )
    print(
        "Paired exact McNemar on cells matched by (theorem, k) within each "
        "model -- one cell\nper theorem per model, so no cluster correction "
        "applies here."
    )
    print(f"Holm-Bonferroni over m = {len(rows)} models at FWER {ALPHA}.\n")
    hdr = (
        f"{'model':30s} {'n':>5s} {'hint:3':>7s} {'noise:3':>8s} {'diff':>7s} "
        f"{'b/c':>9s} {'p':>10s} {'Holm':>5s}"
    )
    print(hdr)
    print("-" * len(hdr))
    if tuple(r["model"] for r in rows) != tuple(MODELS):
        raise ValueError("report rows must follow the configured MODELS order")
    for r, rejected in zip(rows, rej):
        print(
            f"{r['model']:30s} {r['n']:5d} {r['acc_i']:7.3f} {r['acc_n']:8.3f} "
            f"{r['acc_i'] - r['acc_n']:+7.3f} {r['b']:4d}/{r['c']:<4d} "
            f"{r['p']:10.2e} {' yes ' if rejected else '  .  '}"
        )

    sig = [rows[i] for i in range(len(rows)) if rej[i]]
    up = [r for r in sig if r["acc_i"] > r["acc_n"]]
    print(f"\nSignificant under Holm: {len(sig)} of {len(rows)}")
    print(f"  hint:3 HIGHER (information helps): {len(up)}")
    print(f"  noise:3 HIGHER:                    {len(sig) - len(up)}")

    # Conditional MDE uses observed discordance; unconditional MDE is larger.
    print(
        "\n"
        + rows_source.banner(
            "MINIMUM DETECTABLE EFFECT -- what this null actually rules out",
            char="-",
        )
    )
    print(
        f"Both columns are evaluated at each model's OBSERVED discordant "
        f"total, against\nHolm's strictest step (alpha/{len(rows)} = "
        f"{ALPHA / len(rows):.2e}), in accuracy points.\n"
        f"  boundary = smallest effect that would have REACHED significance "
        f"(~50% power)\n  mde80    = smallest TRUE effect this design catches "
        f"80% of the time\n"
    )
    print(
        f"{'model':30s} {'disc':>5s} {'needed split':>13s} {'boundary':>9s} "
        f"{'mde80':>7s} {'observed':>9s}"
    )
    print("-" * 80)
    boundaries, mde80s = [], []
    thresh = ALPHA / len(rows)
    for r in rows:
        model = r["model"]
        nd = r["b"] + r["c"]
        need = None
        for k in range(nd // 2, -1, -1):
            if mcnemar_exact_p(nd - k, k) <= thresh:
                need = k
                break
        if need is None:
            print(
                f"{model:30s} {nd:5d} {'IMPOSSIBLE':>13s} {'--':>9s} {'--':>7s} "
                f"{r['acc_i'] - r['acc_n']:+9.3f}"
            )
            continue
        boundary = (nd - 2 * need) / r["n"]
        pi = _power_pi(nd, need, target=0.80)
        mde80 = nd * (2 * pi - 1) / r["n"]
        boundaries.append(boundary)
        mde80s.append(mde80)
        print(
            f"{model:30s} {nd:5d} {f'{nd - need}/{need}':>13s} {boundary:9.3f} "
            f"{mde80:7.3f} {r['acc_i'] - r['acc_n']:+9.3f}"
        )
    if boundaries:
        print(
            f"\nMedian significance boundary (~50% power): "
            f"{np.median(boundaries):.3f} accuracy points."
        )
        print(
            f"Median 80%-power MDE:                      "
            f"{np.median(mde80s):.3f} accuracy points "
            f"(range {min(mde80s):.3f}-{max(mde80s):.3f})."
        )
        print(
            "  Provenance: mde80 is a deterministic bisection on the CLOSED-FORM binomial power,\n  so it does not move between runs."
        )
        print(
            f"Largest observed |difference|: "
            f"{max(abs(r['acc_i'] - r['acc_n']) for r in rows):.3f}."
        )
        # A nonempty `sig` means this is not a null result.
        if not sig:
            print(
                "So this null rules out LARGE effects of 1-hop transitive "
                "premise background,\nnot small ones."
            )
        else:
            print(
                f"{len(sig)} of {len(rows)} model(s) already reached "
                f"significance under Holm (see above), so this leg is not a "
                f"null\nresult overall -- the MDE numbers above describe the "
                f"sensitivity of only the\n{len(rows) - len(sig)} model(s) "
                f"that did not reach significance."
            )
    n_neg = sum(1 for r in rows if r["acc_i"] < r["acc_n"])
    n_pos = sum(1 for r in rows if r["acc_i"] > r["acc_n"])
    print(
        f"\nDirection of the point estimates, ignoring significance: "
        f"{n_pos} favour hint:3,\n  {n_neg} favour noise:3, "
        f"{len(rows) - n_pos - n_neg} exactly tied."
    )
    # `sig` controls this wording: any rejection means a real effect exists.
    if not sig:
        print(
            "  -- consistent with no effect rather than a real effect this "
            "design cannot\n  resolve."
        )
    else:
        majority = (
            "hint:3"
            if n_pos > n_neg
            else "noise:3" if n_neg > n_pos else "neither rung"
        )
        print(
            f"  -- {len(sig)} of {len(rows)} model(s) already reject the "
            f"null under Holm (see above), so\n  a real effect is present in "
            f"at least those models; the unsigned split above leans\n  "
            f"toward {majority}."
        )
    print(
        f"\nNot significant: {len(rows) - len(sig)} -- listed so a null is not "
        f"mistaken for an untested contrast:"
    )
    for i, r in enumerate(rows):
        if not rej[i]:
            print(
                f"  {r['model']:30s} {r['acc_i']:.3f} vs {r['acc_n']:.3f}  "
                f"p={r['p']:.2e}  (discordant {r['b'] + r['c']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
