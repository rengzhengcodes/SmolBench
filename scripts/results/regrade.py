"""Re-grade collected replicates with the compliance-aware parser.

Every mark stores its raw ``response``, so this re-scores a whole study with no
model, no GPU and no re-run. Per condition it reports before/after accuracy,
changed verdicts, and NONCOMPLIANCE (the model broke the output contract),
separating degraded instruction following from degraded reasoning.

Goes THROUGH ``ResultsStore.regrade`` rather than editing in place: old runs
stay recoverable (S3 appends and marks the old run ``.superseded``; a local
tree renames the replaced file aside instead of overwriting it -- there is no
git safety net under gitignored ``notebooks/*/results/``). ``--write`` is the
gate: a dry run's tally table is exactly what ``--write`` would apply.

    .venv/bin/python scripts/results/regrade.py [--study induction] [--write]
"""

import argparse
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from smolbench.evals import Marks  # noqa: E402
# Imported as a module, not by name: `results_store.utcnow` is this project's
# "now" seam, and a `from ... import utcnow` binding would freeze the real
# clock into every regraded run's key instead of honoring a repointed clock.
from smolbench.evals import results_store as rs  # noqa: E402
from smolbench.evals.parsing import ParseResult, parse_numeric  # noqa: E402
from smolbench.evals.quiz import COMPLIANT  # noqa: E402
from smolbench.evals.study_config import roster_keys, tag_for  # noqa: E402
from smolbench.induction.periodic import CONDITIONS  # noqa: E402

STUDIES = {
    "induction": "notebooks/induction/results",
}

#: Recorded as the "reason" on every S3 ``.superseded`` marker and logged by
#: ``LocalResultsStore.supersede``. Named once so every marker reads identically
#: and is grep-able as one string.
REGRADE_REASON = "regraded with the compliance-aware parser (parse_numeric)"

#: Longest-first so `noise_intens` isn't mis-split by a shorter arm name that is
#: also its suffix (``intens`` inside ``gemma4_e2b_noise_intens``). `sorted` is
#: stable, so equal-length arms keep `CONDITIONS`'s order.
ARMS_LONGEST_FIRST: Tuple[str, ...] = tuple(sorted(CONDITIONS, key=len, reverse=True))


def split_condition_dirname(name: str) -> Optional[Tuple[str, str]]:
    """Split a ``"<tag>_<info>"`` condition directory name into its two parts.

    Both halves may themselves contain ``_`` (``gemma4_e2b``; also the
    ``noise_intens`` arm), so this matches against the known arm names as a
    ``_<info>`` suffix, longest arm first, instead of splitting positionally.
    Returns ``None`` when no arm matches, which the caller reports.
    """
    for arm in ARMS_LONGEST_FIRST:
        suffix = f"_{arm}"
        # `>` not `>=`: a directory literally named "_intens" leaves an empty
        # tag, which addresses nothing, so it is not a match.
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)], arm
    return None


def models_by_tag() -> Dict[str, str]:
    """Return the ``{analysis_tag: roster_spec_key}`` reverse of `tag_for`.

    Well-defined as a dict: `study_config` validates the tag mapping injective
    at load, so no two checkpoints collide onto one tag.
    """
    return {tag_for(key): key for key in roster_keys()}


def roster_conditions(
    store: "rs.ResultsStore", arms: Optional[List[str]]
) -> List[Tuple[str, str, List["rs.ReplicateAddress"]]]:
    """Enumerate an S3-backed study's conditions from the committed roster.

    No local tree to walk -- the log is the store -- so addresses come from
    every roster checkpoint crossed with every info arm, not from a listing.
    An off-roster model is never regraded: the roster is this study's single
    source of truth for its model list everywhere else. Costs one
    ``list_seeds`` call per (checkpoint, arm) rather than listing each model
    prefix once and sorting keys with the private
    `results_store._parse_log_entry`, which would duplicate the log's key
    format in a second place.
    """
    conditions = []
    for key in roster_keys():
        tag = tag_for(key)
        for info in CONDITIONS:
            label = f"{tag}_{info}"
            if arms and not any(label.endswith(arm) for arm in arms):
                continue
            # The S3 log is keyed by model (roster spec key); `tag` rides along
            # for the report label and the local layout.
            seeds = store.list_seeds(key, tag, info)
            if not seeds:
                continue
            conditions.append((
                tag,
                info,
                [rs.ReplicateAddress(tag=tag, info=info, seed=s, model=key) for s in seeds],
            ))
    return conditions


def tree_conditions(
    store: "rs.ResultsStore", tree: Path, arms: Optional[List[str]]
) -> List[Tuple[str, str, List["rs.ReplicateAddress"]]]:
    """Enumerate a local study's conditions by walking its results tree.

    The filesystem, not the roster, is the authority: a local tree may hold
    condition directories from older schemes the roster no longer names, which
    are exactly the results most needing a regrade. A directory matching no
    known arm is skipped with a printed warning, not silently, since only an
    operator can tell a stale scratch directory from a renamed-arm condition.
    """
    conditions = []
    # Derived once: the roster is fixed for the whole walk.
    models = models_by_tag()
    # `{tag}_{info}` always contains "_", so "*_*" can't exclude a real match.
    for cond_dir in sorted(p for p in tree.glob("*_*") if p.is_dir()):
        split = split_condition_dirname(cond_dir.name)
        if split is None:
            print(
                f"  !! skipping {cond_dir.name}: its name ends in no known info arm "
                f"({', '.join(CONDITIONS)}), so it addresses no condition"
            )
            continue
        tag, info = split
        if arms and not any(cond_dir.name.endswith(arm) for arm in arms):
            continue
        # `None` for a tag with no roster checkpoint is harmless here:
        # `LocalResultsStore` ignores `addr.model` (its layout has no model
        # dimension).
        model = models.get(tag)
        seeds = store.list_seeds(None, tag, info)
        if not seeds:
            continue
        conditions.append((
            tag,
            info,
            [rs.ReplicateAddress(tag=tag, info=info, seed=s, model=model) for s in seeds],
        ))
    return conditions


def enumerate_conditions(
    store: "rs.ResultsStore", tree: Path, arms: Optional[List[str]]
) -> List[Tuple[str, str, List["rs.ReplicateAddress"]]]:
    """Enumerate the conditions to regrade, by whichever route `store` supports.

    Dispatches to :func:`roster_conditions` (S3) or :func:`tree_conditions`
    (local); see each for why the two backends enumerate from different
    authorities.
    """
    if isinstance(store, rs.S3ResultsStore):
        return roster_conditions(store, arms)
    return tree_conditions(store, tree, arms)


def load_for_regrade(
    store: "rs.ResultsStore", addr: "rs.ReplicateAddress"
) -> Optional[Tuple[Marks, str]]:
    """Load the replicate at `addr` together with the ``run_ts`` it would replace.

    ``ResultsStore.regrade`` refuses a replacement that does not name what it
    replaces, and the stamp is not recoverable from `Marks` alone, which carries
    no ``run_ts`` field. Returns ``None`` when nothing survives at `addr`.

    S3 uses the earliest surviving run, the one earliest-wins makes
    `load_marks` return; an empty listing means nothing to replace, checked
    before calling `load_marks`, which would otherwise raise. A local tree has
    no ``run_ts`` (one file per address, overwritten in place), so the file's
    collection date names the replacement instead.
    """
    if isinstance(store, rs.S3ResultsStore):
        survivors = store.list_runs(addr)
        if not survivors:
            return None
        return store.load_marks(addr), survivors[0]
    marks = store.load_marks(addr)
    return marks, rs.format_run_ts(marks.date)


def regrade_marks(marks: Marks, parse: Callable[[str], ParseResult]) -> Dict:
    """Re-parse one replicate's marks with `parse` (e.g. `parse_numeric`).

    Nothing is written; the caller decides whether to hand the new `Marks` to
    ``ResultsStore.regrade``. Returns a dict: the re-scored ``marks``, plus
    tallies (``n``, ``before_correct``, ``before_invalid``, ``changed``,
    ``recovered`` invalid->real, ``broke`` real->invalid, ``violations``).
    """
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
        # An explicit `is None` test, not `result.violation or COMPLIANT`: the
        # latter would relabel any future falsy violation label (an empty
        # string, say) as compliant -- the exact inversion of what it means.
        compliance = COMPLIANT if result.violation is None else result.violation
        new_marks.append(replace(mark, score=score, compliance=compliance))

    return {
        # `replace`, not naming fields by hand: a per-field reconstruction
        # already once dropped `server_config`, blanking hardware provenance
        # a re-fetch can't restore.
        "marks": replace(marks, marks=tuple(new_marks)),
        "n": len(marks.marks),
        "before_correct": marks.correct,
        "before_invalid": marks.invalid,
        "changed": changed,
        "recovered": recovered,
        "broke": broke,
        "violations": violations,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Re-grade every requested study and return a process exit code.

    Returns 1 if any mark regressed from a real verdict to invalid, 0
    otherwise, regardless of backend. Addresses are enumerated for the whole
    study up front, before any write, so a seed listing can never observe the
    runs this same pass just appended.

    Each regrade is stamped with its own :func:`results_store.utcnow`. If that
    instant falls in the same whole second as the run it replaces, the new
    run's key collides with the superseded one's; not guarded against, since
    in practice a regrade always follows its collection by more than a second.
    """
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--study", choices=sorted(STUDIES), action="append")
    argp.add_argument("--arm", action="append", help="only conditions ending in this arm")
    # Not "rewrite YAMLs in place": nothing is rewritten in place on either backend.
    argp.add_argument(
        "--write",
        action="store_true",
        help=(
            "apply the regrade through the results store, retiring each run it "
            "replaces (on S3 a new run is appended and the old one marked "
            "superseded; on a local tree the replaced file is renamed aside). "
            "See the module docstring for the per-backend detail."
        ),
    )
    args = argp.parse_args(argv)
    studies = args.study or sorted(STUDIES)

    total_broke = 0
    for study in studies:
        tree = REPO / STUDIES[study]
        # Resolved once per study so every address below is read and written
        # through the same backend the enumeration was built from.
        store = rs.resolve_store(tree)
        # Local-backend concern only: an S3-backed study keeps nothing on disk,
        # so requiring the tree would silence every S3-backed study.
        if not isinstance(store, rs.S3ResultsStore) and not tree.is_dir():
            continue
        parse = parse_numeric
        print(f"\n{'=' * 92}\n### {study}{'  (DRY RUN)' if not args.write else '  (WRITING)'}\n{'=' * 92}")
        print(
            f"{'condition':26s} {'n':>6s} {'acc before':>11s} {'acc after':>10s} "
            f"{'inval b/a':>12s} {'recov':>6s} {'noncompliant':>13s}"
        )

        for tag, info, addrs in enumerate_conditions(store, tree, args.arm):
            cond = f"{tag}_{info}"
            n = before_c = before_i = after_c = after_i = 0
            recovered = broke = 0
            violations: Counter = Counter()
            pending: List = []

            # Read and re-grade every replicate; nothing is written yet.
            for addr in addrs:
                loaded = load_for_regrade(store, addr)
                if loaded is None:
                    print(
                        f"  !! skipping {cond} seed {addr.seed}: no surviving logged "
                        "run to regrade (everything logged there is superseded)"
                    )
                    continue
                marks, replaced_run_ts = loaded
                summary = regrade_marks(marks, parse)
                # Set here, not inside `regrade_marks` (which knows only the
                # marks): `ResultsStore.regrade` refuses a replacement with no
                # `regraded_from`.
                regraded = replace(summary["marks"], regraded_from=replaced_run_ts)
                n += summary["n"]
                before_c += summary["before_correct"]
                before_i += summary["before_invalid"]
                after_c += regraded.correct
                after_i += regraded.invalid
                recovered += summary["recovered"]
                broke += summary["broke"]
                violations.update(summary["violations"])
                if args.write:
                    pending.append((addr, regraded))

            if not n:
                # Returned before the rate columns below divide by `n`.
                print(f"  {cond:24s} -- no readable mark to regrade")
                continue

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

            # The only write path; `pending` is empty unless --write.
            for addr, regraded in pending:
                store.regrade(regraded, addr, rs.utcnow(), reason=REGRADE_REASON)

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
