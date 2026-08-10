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
    .venv/bin/python scripts/coprime_pilot_gate.py [study]

``study`` is a notebook directory name and defaults to ``periodic_coprime``;
pass ``periodic_divisor`` (or any sibling) to gate that study instead. The
check is study-agnostic -- it only ever looks for empty completions -- so it
is worth pointing at any run whose completion budget is unproven.
"""

import sys
from collections import Counter
from pathlib import Path

import yaml

NOTEBOOKS = Path(__file__).resolve().parent.parent / "notebooks"
DEFAULT_STUDY = "periodic_coprime"



def tally(arm_dir: Path) -> tuple[int, int, int, Counter, list[int]]:
    """Tally one arm in a single pass over its replicates.

    Returns ``(correct, incorrect, invalid, compliance-label counts,
    empty-query lengths)``. The last element holds the character length of
    the query behind each ``compliance=empty`` mark -- characters, not
    tokens, deliberately, so the gate stays import-light and offline and can
    run before anything is provisioned. The absolute number is not the point;
    the *ranking* against the study's other arms is, and that ranking is what
    separates the two causes of an empty completion (see ``main``).
    """
    correct = incorrect = invalid = 0
    labels: Counter = Counter()
    empty_lengths: list[int] = []
    for rep in sorted(arm_dir.glob("rep_*.yaml")):
        for mark in yaml.safe_load(rep.read_text())["marks"]:
            if mark["compliance"]:
                labels[mark["compliance"]] += 1
                if mark["compliance"] == "empty":
                    empty_lengths.append(len(mark["query"]))
            if mark["score"] is None:
                invalid += 1
            elif mark["score"]:
                correct += 1
            else:
                incorrect += 1
    return correct, incorrect, invalid, labels, empty_lengths


def main() -> int:
    study = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STUDY
    results = NOTEBOOKS / study / "results"
    print(f"gating study: {study}\n")
    if not results.is_dir():
        print(f"BLOCKED: no results directory at {results}")
        return 1

    arms = sorted(p for p in results.iterdir() if p.is_dir())
    if not arms:
        print(f"BLOCKED: {results} has no arms; the run produced nothing")
        return 1

    empties = 0
    total = 0
    empty_lengths: list[int] = []
    print(f"{'arm':>26} {'n':>4} {'correct':>8} {'wrong':>6} {'invalid':>8}  compliance")
    print("-" * 78)
    for arm in arms:
        c, i, inv, labels, arm_empty_lengths = tally(arm)
        n = c + i + inv
        total += n
        empties += labels.get("empty", 0)
        empty_lengths += arm_empty_lengths
        flags = ", ".join(f"{k}={v}" for k, v in sorted(labels.items())) or "-"
        print(f"{arm.name:>26} {n:>4} {c:>8} {i:>6} {inv:>8}  {flags}")

    print("-" * 78)
    print(f"{'TOTAL':>26} {total:>4} marks across {len(arms)} arms")

    # The one blocking condition. An `empty` mark means the model emitted
    # neither an answer nor reasoning, so the harness has no integer to score.
    #
    # Two very different causes produce it, and the fix differs:
    #
    #   (a) the completion budget ran out mid-reasoning -- a HARNESS fault,
    #       fixed by raising max_completion_tokens or shortening the prompt;
    #   (b) the model never terminated its reasoning at all -- a MODEL
    #       behaviour, which no budget fixes and which is a result to report.
    #
    # The prompt length behind each empty separates them. Under (a) empties
    # concentrate in the study's LONGEST-prompt arm, because that is where
    # completion headroom is scarcest. Empties on the SHORTEST prompts, with
    # the long arm clean, are (b). The gate blocks either way -- deciding
    # between them is a judgement call on the evidence, not a threshold -- but
    # it prints the evidence rather than asserting a cause.
    if empties:
        longest = max(empty_lengths)
        shortest = min(empty_lengths)
        print(
            f"\nBLOCKED: {empties} mark(s) came back EMPTY -- no answer and no reasoning.\n"
            f"Their prompts run {shortest:,}-{longest:,} characters.\n\n"
            "Diagnose before acting. Compare that range against the arms above:\n"
            "  * empties in the LONGEST-prompt arm -> the completion budget is\n"
            "    too tight. Raise it or shorten the period set, then re-run.\n"
            "    Do NOT scale R with budget-driven empties outstanding.\n"
            "  * empties on the SHORTEST prompts while the long arm is clean ->\n"
            "    non-termination, not truncation. No budget fixes it; report the\n"
            "    rate as a finding about the model at that prompt length.\n\n"
            "The run's derived completion budget is printed by the driver at\n"
            "startup ('-> completion budget N'); read it from that run's log\n"
            "rather than assuming, since it is derived per study and per model."
        )
        return 1

    if total == 0:
        print("\nBLOCKED: zero marks collected.")
        return 1

    print(
        f"\nPASS: no empty completions, {total} marks collected.\n"
        "Safe to scale to R=30. Wrong answers below are a result, not a fault:\n"
        "moving models off ceiling is what the longer listing was for."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
