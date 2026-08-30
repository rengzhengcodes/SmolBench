"""Re-grade collected replicates with the compliance-aware parser.

Every mark stores its raw ``response``, so ``smolbench.evals.parsing`` re-scores
a whole results tree with no model, no GPU and no re-run -- use this to bring
arms graded under an older, stricter convention onto one convention. Per
condition it reports before/after accuracy, changed verdicts, invalid marks
recovered, and NONCOMPLIANCE: how often the model broke the output contract
regardless of correctness, which separates degraded instruction following from
degraded reasoning.

Dry run by default; ``--write`` rewrites the YAMLs in place with NO git safety
net, since ``.gitignore`` excludes ``notebooks/*/results/``. Only a re-fetch
undoes a bad ``--write`` (``InductionExperiment.harness.sync_down()``) -- and
that same call silently DISCARDS a good one.

S3-backed results guard: this script edits ``rep_*.yaml`` on the LOCAL
filesystem only, while ``results_store.sync_down`` is a one-way S3-to-local
mirror that OVERWRITES the local tree, so a local-only regrade is clobbered back
to the stale S3 copy on the next sync -- invisibly, since a score flip preserves
byte length. `main` therefore refuses -- before touching a file, and regardless
of ``--write`` -- if `_s3_backed_studies` finds any requested study resolving to
an ``S3ResultsStore``, printing the recovery sequence instead.

Run from the repo root:
    .venv/bin/python scripts/results/regrade.py [--study induction] [--write]
"""

import argparse
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from smolbench.evals import Marks  # noqa: E402
from smolbench.evals.parsing import parse_numeric  # noqa: E402

STUDIES = {
    # The family-ladder scaling study (notebooks/induction) is S3-backed
    # (SMOLBENCH_RESULTS_S3), so the guard in `main` refuses a local regrade
    # until the operator syncs down and unsets the env var; see the module
    # docstring's "S3-backed results guard".
    "induction": "notebooks/induction/results",
}


def _s3_backed_studies(studies) -> List:
    """Return ``(study, tree, store.describe())`` for each S3-backed study in `studies`.

    `studies` are `STUDIES` keys; `tree` is ``REPO / STUDIES[study]``, the exact
    directory `main` would read or write. Empty whenever every study resolves
    locally, i.e. whenever ``SMOLBENCH_RESULTS_S3`` is unset. Studies are
    resolved one at a time rather than short-circuiting on that env var, so the
    refusal names each offending tree by its own ``describe()`` value.
    ``results_store`` is imported lazily, per the house convention that
    importing a module must not require the AWS SDK.
    """
    from smolbench.evals.results_store import S3ResultsStore, resolve_store

    offending = []
    for study in studies:
        tree = REPO / STUDIES[study]
        store = resolve_store(tree)
        if isinstance(store, S3ResultsStore):
            offending.append((study, tree, store.describe()))
    return offending


def regrade_file(path: Path, parse) -> Dict:
    """Re-parse one ``rep_*.yaml`` replicate with `parse` (e.g. `parse_numeric`).

    Nothing is written; the caller decides whether to dump the new `Marks`.

    Returns
    -------
    dict
        ``marks`` (a new `Marks` carrying the re-parsed score and compliance per
        mark), ``n``, ``before_correct``, ``before_invalid``, ``changed``
        (verdict changed), ``recovered`` (invalid -> real verdict), ``broke``
        (real verdict -> invalid), ``violations`` (`Counter` of output-contract
        violations).
    """
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
    """Re-grade every requested study and return a process exit code.

    Returns ``1`` if any requested study is S3-backed (see the module
    docstring's "S3-backed results guard") or if any mark regressed from a real
    verdict to invalid; ``0`` otherwise.
    """
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--study", choices=sorted(STUDIES), action="append")
    argp.add_argument("--arm", action="append", help="only conditions ending in this arm")
    argp.add_argument("--write", action="store_true", help="rewrite YAMLs in place")
    args = argp.parse_args()
    studies = args.study or sorted(STUDIES)

    # Guard (see the module docstring's "S3-backed results guard"). It fires
    # regardless of --write: once SMOLBENCH_RESULTS_S3 is set, a dry run's
    # tallies come from a local tree that is not authoritative, which would
    # mislead rather than inform the operator's --write decision.
    offending = _s3_backed_studies(studies)
    if offending:
        print("REFUSING to regrade: the following stud(y/ies) are S3-backed, not local:")
        for study, tree, description in offending:
            print(f"  {study}: {tree} -> {description}")
        print(
            "\nThis script rewrites rep_*.yaml on the LOCAL filesystem only. "
            "smolbench.evals.results_store.sync_down is a ONE-WAY mirror "
            "(S3 -> local) that OVERWRITES the local tree, so a local-only "
            "regrade would be silently clobbered back to the stale S3 copy "
            "on the next sync_down -- a score flip is byte-length "
            "preserving, so nothing would catch the loss."
        )
        print(
            "\nTo proceed:\n"
            "  1. Sync down: python -m smolbench.evals.results_store <results_dir>\n"
            "  2. Unset SMOLBENCH_RESULTS_S3\n"
            "  3. Re-run this regrade"
        )
        return 1

    total_broke = 0
    for study in studies:
        results = REPO / STUDIES[study]
        if not results.is_dir():
            continue
        parse = parse_numeric
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
