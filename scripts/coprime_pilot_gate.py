"""Gate the coprime study's full R=30 run on its pilot.

The pilot exists to answer one question that cannot be reasoned about, only
measured: at ~2x the prompt length of ``periodic_moe``, is a 65,536-token
completion budget still enough? Every one of periodic_moe's 21 invalids was
``compliance=empty`` -- a zero-length response, the signature of a model
whose reasoning consumed the whole budget before it emitted an answer. If
any of those appear here, scaling to R=30 would buy 30x more of them.

The gate is deliberately strict on that one failure mode and permissive
about everything else. Wrong answers are a RESULT, not a failure -- the
whole point of lengthening the extensional listing was to move models off
ceiling, so incorrect marks in the extens arm mean the study is working.
Only empties block, because only empties mean the harness failed to give
the model room to answer.

Exit status is the contract: 0 = pass (safe to scale R), 1 = blocked.

Run (repo root, main venv):
    .venv/bin/python scripts/coprime_pilot_gate.py
"""

import sys
from collections import Counter
from pathlib import Path

import yaml

RESULTS = Path(__file__).resolve().parent.parent / "notebooks" / "periodic_coprime" / "results"

#: Completion budget the pilot ran with; only used for the diagnosis message.
BUDGET = 65_536


def tally(arm_dir: Path) -> tuple[int, int, int, Counter]:
    """Returns (correct, incorrect, invalid, compliance-label counts) for one arm."""
    correct = incorrect = invalid = 0
    labels: Counter = Counter()
    for rep in sorted(arm_dir.glob("rep_*.yaml")):
        for mark in yaml.safe_load(rep.read_text())["marks"]:
            if mark["compliance"]:
                labels[mark["compliance"]] += 1
            if mark["score"] is None:
                invalid += 1
            elif mark["score"]:
                correct += 1
            else:
                incorrect += 1
    return correct, incorrect, invalid, labels


def main() -> int:
    if not RESULTS.is_dir():
        print(f"BLOCKED: no results directory at {RESULTS}")
        return 1

    arms = sorted(p for p in RESULTS.iterdir() if p.is_dir())
    if not arms:
        print(f"BLOCKED: {RESULTS} has no arms; the pilot produced nothing")
        return 1

    empties = 0
    total = 0
    print(f"{'arm':>26} {'n':>4} {'correct':>8} {'wrong':>6} {'invalid':>8}  compliance")
    print("-" * 78)
    for arm in arms:
        c, i, inv, labels = tally(arm)
        n = c + i + inv
        total += n
        empties += labels.get("empty", 0)
        flags = ", ".join(f"{k}={v}" for k, v in sorted(labels.items())) or "-"
        print(f"{arm.name:>26} {n:>4} {c:>8} {i:>6} {inv:>8}  {flags}")

    print("-" * 78)
    print(f"{'TOTAL':>26} {total:>4} marks across {len(arms)} arms")

    # The one blocking condition. `empty` is the truncation signature: the
    # model returned nothing at all, which at these prompt lengths means the
    # completion budget ran out mid-reasoning rather than the model failing
    # the task.
    if empties:
        print(
            f"\nBLOCKED: {empties} mark(s) came back EMPTY at a {BUDGET:,}-token budget.\n"
            "That is truncation, not a wrong answer -- the model never got to emit\n"
            "an integer. Raise max_completion_tokens (there is headroom: the worst\n"
            "prompt is ~55.5k against a 131,072 context) or shorten the period set,\n"
            "then re-run the pilot. Do NOT scale R with empties outstanding."
        )
        return 1

    if total == 0:
        print("\nBLOCKED: zero marks collected.")
        return 1

    print(
        f"\nPASS: no empty completions at {BUDGET:,} tokens, {total} marks collected.\n"
        "Safe to scale to R=30. Wrong answers below are a result, not a fault:\n"
        "moving models off ceiling is what the longer listing was for."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
