"""Re-grades collected replicates with the compliance-aware parser.

Why this is needed
------------------
Grading semantics changed: ``smolbench.evals.parsing`` now recovers an answer
that is correct but wrongly formatted, and records HOW the response broke the
prompt's output contract, instead of scoring it as a plain failure. Replicates
collected before that change were graded strictly, so a results tree can hold
two different grading conventions at once -- which would make an arm collected
today incomparable with the arm it is supposed to be contrasted against.

Every mark stores its raw ``response``, so the fix needs no model, no GPU and
no re-run: re-parse what is already on disk and every arm ends up under one
convention.

What it reports
---------------
Per condition, before vs after:

* accuracy, and how many marks change verdict;
* invalid count -- how many unreadable marks the parser recovers;
* NONCOMPLIANCE, the new signal: how often the model disobeyed the output
  contract regardless of whether it got the answer right. That is the number
  that shows whether a condition degrades instruction following rather than
  reasoning, which is precisely the question the induction ``noise_intens``
  arm raised.

Dry-run by default. ``--write`` rewrites the YAMLs in place; they are
git-tracked, so a bad pass is recoverable with ``git checkout``.

Run (repo root, main venv):
    .venv/bin/python scripts/regrade.py                     # report only
    .venv/bin/python scripts/regrade.py --study chromatic
    .venv/bin/python scripts/regrade.py --write
"""

import argparse
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from smolbench.evals import Marks, Numeric, ToF  # noqa: E402
from smolbench.evals.parsing import parse_numeric, parse_tof  # noqa: E402

STUDIES = {
    "periodic": "notebooks/periodic/results",
    "chromatic": "notebooks/chromatic/results",
    "periodic_moe": "notebooks/periodic_moe/results",
}


def parser_for(study: str):
    """Chromatic asks True/False; both periodic studies ask for an integer."""
    return parse_tof if study == "chromatic" else parse_numeric


def regrade_file(path: Path, parse) -> Dict:
    """Re-parses one replicate. Returns a summary and the new Marks."""
    marks = Marks.load(path)
    new_marks = []
    changed = recovered = broke = 0
    violations: Counter = Counter()

    for mark in marks.marks:
        result = parse(mark.response)
        if result.value is None:
            score = None
        else:
            score = int(result.value == mark.answer)
        if result.violation is not None:
            violations[result.violation] += 1
        if score != mark.score:
            changed += 1
            if mark.score is None and score is not None:
                recovered += 1
            elif mark.score is not None and score is None:
                broke += 1
        new_marks.append(replace(mark, score=score, compliance=result.violation))

    return {
        "marks": Marks(model=marks.model, marks=tuple(new_marks), date=marks.date),
        "n": len(marks.marks),
        "before_correct": marks.correct,
        "before_invalid": marks.invalid,
        "changed": changed,
        "recovered": recovered,
        "broke": broke,
        "violations": violations,
    }


def main() -> int:
    """Re-grades every requested study; returns a process exit code."""
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--study", choices=sorted(STUDIES), action="append")
    argp.add_argument("--arm", action="append", help="only conditions ending in this arm")
    argp.add_argument("--write", action="store_true", help="rewrite YAMLs in place")
    args = argp.parse_args()
    studies = args.study or sorted(STUDIES)

    total_broke = 0
    for study in studies:
        results = REPO / STUDIES[study]
        if not results.is_dir():
            continue
        parse = parser_for(study)
        print(f"\n{'=' * 92}\n### {study}{'  (DRY RUN)' if not args.write else '  (WRITING)'}\n{'=' * 92}")
        print(
            f"{'condition':26s} {'n':>6s} {'acc before':>11s} {'acc after':>10s} "
            f"{'inval b/a':>12s} {'recov':>6s} {'noncompliant':>13s}"
        )

        for cond_dir in sorted(p for p in results.glob("*_*") if p.is_dir()):
            cond = cond_dir.name
            if args.arm and not any(cond.endswith(a) for a in args.arm):
                continue
            reps = sorted(cond_dir.glob("rep_*.yaml"))
            if not reps:
                continue
            n = before_c = before_i = after_c = after_i = 0
            recovered = broke = 0
            violations: Counter = Counter()
            pending: List = []

            for rep in reps:
                summary = regrade_file(rep, parse)
                n += summary["n"]
                before_c += summary["before_correct"]
                before_i += summary["before_invalid"]
                after_c += summary["marks"].correct
                after_i += summary["marks"].invalid
                recovered += summary["recovered"]
                broke += summary["broke"]
                violations.update(summary["violations"])
                if args.write:
                    pending.append((rep, summary["marks"]))

            noncompliant = sum(violations.values())
            print(
                f"  {cond:24s} {n:6d} {before_c / n:11.3f} {after_c / n:10.3f} "
                f"{before_i:5d}/{after_i:<5d} {recovered:6d} "
                f"{noncompliant:6d} ({noncompliant / n:5.1%})"
            )
            if violations:
                detail = "  ".join(f"{k}={v}" for k, v in violations.most_common())
                print(f"      violations: {detail}")
            if broke:
                total_broke += broke
                print(f"      !! {broke} marks became UNREADABLE that were readable before")

            for rep, marks in pending:
                marks.dump(rep)

        if args.write:
            print("\n  written.")

    print(f"\n{'=' * 92}")
    if total_broke:
        print(f"WARNING: {total_broke} marks regressed to invalid -- investigate before trusting this pass.")
        return 1
    print("No mark that was readable before became unreadable.")
    if not args.write:
        print("Dry run only. Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
