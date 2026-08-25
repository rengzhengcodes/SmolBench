"""Re-grade collected replicates with the compliance-aware parser.

Why this is needed
------------------
Grading semantics changed. ``smolbench.evals.parsing`` now recovers an
answer that is correct but wrongly formatted, and records HOW the response
broke the prompt's output contract, instead of scoring it as a plain
failure. Replicates collected before that change were graded strictly. So
a results tree can hold two different grading conventions at once, which
would make an arm collected today incomparable with the arm it should be
contrasted against.

Every mark stores its raw ``response``, so the fix needs no model, no GPU,
and no re-run. This script re-parses what is already on disk, so every arm
ends up under one convention.

What it reports
---------------
Per condition, before vs after:

* accuracy, and how many marks change verdict;
* invalid count: how many unreadable marks the parser recovers;
* NONCOMPLIANCE, the new signal: how often the model disobeyed the output
  contract, regardless of whether it got the answer right. This number
  shows whether a condition degrades instruction following rather than
  reasoning. This is exactly the question the induction ``noise_intens``
  arm raised.

This script runs as a dry run by default. ``--write`` rewrites the YAMLs
in place. There is NO git safety net: ``.gitignore`` ignores
``notebooks/*/results/`` for every study, so git tracks no result YAML,
and ``git checkout`` recovers nothing (verified 2026-08-14: ``git
ls-files 'notebooks/*/results/*'`` returns 0). You can recover a bad
``--write`` pass ONLY by re-fetching the results: for S3-backed studies,
through ``InductionExperiment.harness.sync_down()``. That same sync_down
call also silently DISCARDS a good pass; see the guard below.

S3-backed results guard
------------------------
This script edits ``rep_*.yaml`` files directly on the LOCAL filesystem.
It does not know that ``smolbench.evals.results_store`` (S3-backed
results) exists. That is fine as long as a study's results live only
locally, but it becomes actively dangerous once ``SMOLBENCH_RESULTS_S3``
is in play. ``smolbench.evals.results_store.sync_down`` is a ONE-WAY
mirror, S3 to local only: it never uploads, and it OVERWRITES whatever is
already in the local tree. A local-only edit this script makes
(``--write``) never reaches S3, so the very next ``sync_down`` silently
clobbers it back to the stale, pre-regrade S3 copy. This is not a loud
failure: a regrade's typical edit is a score flip (for example ``1 ->
0``), which preserves the file's byte length. A direct measurement
confirmed this: 147 bytes before and after, with only the content (and
its MD5) different. So nothing about file size or presence would tip the
operator off that the regrade was ever lost.

Before it does ANY work, this script checks every study it would touch
(respecting ``--study``) through
``smolbench.evals.results_store.resolve_store``. It REFUSES outright if
any of them resolves to an ``S3ResultsStore``: it prints which studies are
S3-backed and returns a nonzero exit code, without reading or writing a
single file. This refusal fires regardless of ``--write``. A dry run is
not safe either: with an S3-backed store, the local tree is not
authoritative. A dry run's before/after tallies, computed from an
absent or stale local tree, would mislead the operator at exactly the
moment they decide whether to write. See `_s3_backed_studies` and the
guard block at the top of `main` for the implementation, and see the
printed message for the exact recovery sequence (sync down, unset the
env var, re-run, re-seed).

Run this script from the repo root, in the main venv:
    .venv/bin/python scripts/regrade.py                     # report only
    .venv/bin/python scripts/regrade.py --study induction
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

from smolbench.evals import Marks  # noqa: E402
from smolbench.evals.parsing import parse_numeric, parse_tof  # noqa: E402

STUDIES = {
    # The family-ladder scaling study (notebooks/induction) is S3-backed
    # (SMOLBENCH_RESULTS_S3). So the S3 guard below refuses a local regrade
    # until the operator deliberately syncs down, unsets the env var, and
    # re-seeds; see the module docstring. Retired studies (periodic,
    # chromatic, periodic_moe, and others) live in archive_2026-08-11.zip
    # and in git history. This script can no longer regrade them in place.
    "induction": "notebooks/induction/results",
}


def parser_for(study: str):
    """Return the response parser for `study`.

    Every study currently in `STUDIES` asks for an integer verdict. This
    function keeps the ``"chromatic"`` branch (True/False verdicts) for a
    retired study that once lived in `STUDIES`; see the module docstring.

    Parameters
    ----------
    study : str
        Study name, a key of `STUDIES`.

    Returns
    -------
    callable
        ``parse_tof`` for ``study == "chromatic"``, otherwise
        ``parse_numeric``.
    """
    return parse_tof if study == "chromatic" else parse_numeric


def _s3_backed_studies(studies) -> List:
    """Return which of ``studies`` resolve to an S3-backed results store.

    Parameters
    ----------
    studies : iterable of str
        Study names (keys of `STUDIES`) that a run would touch. `main`
        already computes this same set from ``--study`` (or from every
        study, when ``--study`` is absent).

    Returns
    -------
    list of (str, pathlib.Path, str)
        One ``(study, tree, description)`` tuple per offending study.
        ``tree`` is ``REPO / STUDIES[study]``, the exact path `main` would
        read or write. ``description`` is that tree's resolved store's
        ``describe()`` value (for example
        ``"s3://smolbench-results-.../notebooks/..."``). This list is
        empty when every study in ``studies`` resolves locally, which is
        the common case whenever ``SMOLBENCH_RESULTS_S3`` is unset.

    Notes
    -----
    This function imports ``smolbench.evals.results_store`` lazily, inside
    the function body. This matches this repo's house convention: a
    module does not need to depend on the AWS SDK merely by being
    imported. ``resolve_store`` itself only *might* need boto3, to build
    a client, but never at the point this function calls it, because
    deciding WHICH store class a directory maps to needs no network I/O
    at all.

    ``REPO / STUDIES[study]`` is always repo-anchored: both ``REPO`` here
    and ``results_store.repo_root()`` reduce to the same checkout root.
    So in practice, whenever ``SMOLBENCH_RESULTS_S3`` is set at all, EVERY
    study in ``studies`` resolves to ``S3ResultsStore``. There is no
    "some local, some S3" split for this script's own trees: only "the
    env var is set" or "it isn't". This function still checks each study
    individually, instead of short-circuiting on the env var, so the
    printed refusal names every offending tree by its own resolved
    ``describe()`` value, not by a guess.
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
    """Re-parse one replicate file with `parse`.

    Parameters
    ----------
    path : Path
        Path to a ``rep_*.yaml`` replicate file.
    parse : callable
        Response parser to apply to each mark's raw ``response``, for
        example ``parse_numeric`` or ``parse_tof``.

    Returns
    -------
    dict
        A summary with these keys: ``marks`` (the new `Marks` object,
        with the re-parsed score and compliance recorded on each mark),
        ``n`` (mark count), ``before_correct``, ``before_invalid``,
        ``changed`` (marks whose verdict changed), ``recovered`` (marks
        that changed from invalid to a real verdict), ``broke`` (marks
        that changed from a real verdict to invalid), and ``violations``
        (a `Counter` of output-contract violations).
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

    Returns
    -------
    int
        ``0`` on success. ``1`` if any requested study is S3-backed (see
        the module docstring's S3-backed results guard), or if any mark
        regressed from a real verdict to invalid during regrading.
    """
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--study", choices=sorted(STUDIES), action="append")
    argp.add_argument("--arm", action="append", help="only conditions ending in this arm")
    argp.add_argument("--write", action="store_true", help="rewrite YAMLs in place")
    args = argp.parse_args()
    studies = args.study or sorted(STUDIES)

    # Guard (see the module docstring's "S3-backed results guard" section).
    # Refuse OUTRIGHT, before this function touches a single file, if any
    # study this run would touch is S3-backed. This guard fires regardless
    # of --write: a dry run's tallies would themselves come from a local
    # tree that is not authoritative once SMOLBENCH_RESULTS_S3 is set,
    # which would mislead rather than inform the operator's --write
    # decision.
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
            "  3. Re-run this regrade\n"
            "  4. Deliberately re-seed the regraded trees back to S3"
        )
        return 1

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
