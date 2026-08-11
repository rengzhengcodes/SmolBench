"""Pre-registered McNemar gate for the lean_cot_gate run.

Implements exactly the decision rule in the run dir's PREREGISTRATION.md
(registered 2026-07-13, before the run): unit = (theorem, k, rung) group,
outcome = pass@4 over rollout_idx 0-3, arms base / bare-r128 / cot-r128;
GREEN iff cot > bare AND cot > base, each by a one-sided exact McNemar test
on discordant pairs at alpha = 0.05; effect size (b - c) / n_pairs with a
95% paired-difference CI reported for both comparisons.

Scoring rules from the pre-registration, made operational:

- Sanity gate: a theorem whose ground-truth replay row (kind == "sanity") is
  anything but success is dropped for ALL arms (this includes the known
  core-namespace DojoInitError theorems -- symmetric drop).
- Exceptions are MISSING, never failures: a group with >= 1 success rollout
  is a pass regardless of exceptions (missingness cannot un-verify a
  verified proof); a group with no success AND >= 1 exception rollout is
  missing (the exception could have been the pass); a group with < 4
  recorded non-exception rollouts and no success is likewise missing. A
  missing group drops the PAIR only in comparisons involving that arm.
- The cot arm's 07-13 calibration ran 8 rollouts/group in this same run dir;
  the gate uses rollout_idx < 4 uniformly so every arm is scored on the
  same four seeds (1776 + idx).

Usage:
    .venv-lean/bin/python scripts/lean_gate_mcnemar.py \
        notebooks/lean/results/runs/lean_cot_gate
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ARM_BASE = "qwen3-235b-a22b-base"
ARM_BARE = "qwen3-lean-bare-r128"
ARM_COT = "qwen3-lean-cot-r128"
N_ROLLOUTS = 4
ALPHA = 0.05


def binom_sf_onesided(b: int, n: int) -> float:
    """P(X >= b) for X ~ Binomial(n, 0.5) -- the one-sided exact McNemar p."""
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2**n


def paired_diff_ci(b: int, c: int, n: int, z: float = 1.959964) -> tuple:
    """95% Wald CI for the paired proportion difference (b - c) / n."""
    if n == 0:
        return (float("nan"), float("nan"))
    d = (b - c) / n
    se = math.sqrt(max(b + c - (b - c) ** 2 / n, 0.0)) / n
    return (d - z * se, d + z * se)


def load(run_dir: Path):
    """Returns (group_outcomes, dropped_theorems, counters) from all_rows.

    group_outcomes: {(theorem, k, rung): {arm: True/False/None}} with None =
    missing per the exception rule; sanity-dropped theorems excluded.
    """
    sanity_ok, sanity_bad = set(), set()
    cells = defaultdict(dict)  # (thm,k,rung) -> arm -> {idx: verdict}
    with open(run_dir / "all_rows.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if r.get("kind") == "sanity":
                (sanity_ok if r.get("verdict") == "success" else sanity_bad).add(
                    r["theorem_id"]
                )
            elif r.get("kind") == "cell":
                if r.get("rollout_idx", 0) >= N_ROLLOUTS:
                    continue  # calibration extras (8-rollout groups)
                key = (r["theorem_id"], r["k"], r["rung"])
                cells[key].setdefault(r["model"], {})[r["rollout_idx"]] = r["verdict"]
    # A theorem with any bad sanity row is dropped even if a later replay
    # succeeded -- conservative and symmetric across arms.
    dropped = sanity_bad
    outcomes = {}
    for key, arms in cells.items():
        if key[0] in dropped:
            continue
        out = {}
        for arm, rollouts in arms.items():
            verdicts = list(rollouts.values())
            if any(v == "success" for v in verdicts):
                out[arm] = True
            elif any(v == "exception" for v in verdicts) or len(
                [v for v in verdicts if v != "exception"]
            ) < N_ROLLOUTS:
                out[arm] = None  # missing
            else:
                out[arm] = False
        outcomes[key] = out
    return outcomes, dropped


def mcnemar(outcomes, treat: str, control: str):
    b = c = both = neither = 0
    for out in outcomes.values():
        t, u = out.get(treat), out.get(control)
        if t is None or u is None:
            continue
        if t and not u:
            b += 1
        elif u and not t:
            c += 1
        elif t and u:
            both += 1
        else:
            neither += 1
    n = b + c + both + neither
    p = binom_sf_onesided(b, b + c)
    lo, hi = paired_diff_ci(b, c, n)
    return dict(b=b, c=c, both=both, neither=neither, n_pairs=n,
                effect=(b - c) / n if n else float("nan"), ci=(lo, hi), p=p)


def main() -> None:
    run_dir = Path(sys.argv[1])
    outcomes, dropped = load(run_dir)
    print(f"groups scored: {len(outcomes)}; sanity-dropped theorems: {len(dropped)}")
    for arm in (ARM_BASE, ARM_BARE, ARM_COT):
        vals = [o.get(arm) for o in outcomes.values() if arm in o]
        n_missing = sum(v is None for v in vals)
        n_pass = sum(v is True for v in vals)
        print(f"  {arm}: groups={len(vals)} pass@4={n_pass} "
              f"({n_pass / max(len(vals) - n_missing, 1):.3f}) missing={n_missing}")
    verdicts = {}
    for label, control in (("cot_vs_bare", ARM_BARE), ("cot_vs_base", ARM_BASE)):
        m = mcnemar(outcomes, ARM_COT, control)
        verdicts[label] = m
        print(f"\n{label}: b={m['b']} c={m['c']} both={m['both']} neither={m['neither']} "
              f"n={m['n_pairs']}")
        print(f"  effect (b-c)/n = {m['effect']:+.4f}  95% CI [{m['ci'][0]:+.4f}, {m['ci'][1]:+.4f}]")
        print(f"  one-sided exact McNemar p = {m['p']:.4f}  -> "
              f"{'SIGNIFICANT' if m['p'] < ALPHA else 'not significant'} at {ALPHA}")
    green = all(m["p"] < ALPHA and m["effect"] > 0 for m in verdicts.values())
    print(f"\nGATE: {'GREEN' if green else 'RED'}")


if __name__ == "__main__":
    main()
