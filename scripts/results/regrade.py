"""Re-grade collected replicates with the compliance-aware parser.

Every mark stores its raw ``response``, so ``smolbench.evals.parsing`` re-scores
a whole study with no model, no GPU and no re-run -- use this to bring arms
graded under an older, stricter convention onto one convention. Per condition it
reports before/after accuracy, changed verdicts, invalid marks recovered, and
NONCOMPLIANCE (how often the model broke the output contract regardless of
correctness), which separates degraded instruction following from degraded
reasoning.

A regrade goes THROUGH the results store (``ResultsStore.regrade``) rather than
around it, so one pass serves either backend and lands where readers actually
read:

* S3-backed (``SMOLBENCH_RESULTS_S3`` set): the log is append-only, so nothing
  is ever edited in place. Each regraded replicate is APPENDED as a new run
  carrying ``regraded_from`` -- the ``run_ts`` of the run it replaces -- and a
  ``.superseded`` marker is written beside that prior run to retire it. The
  prior run's object survives byte for byte; retiring it is precisely what makes
  earliest-wins serve the regraded run instead of the stale one.
* Local tree: the replaced ``rep_<seed>.yaml`` is RENAMED to
  ``rep_<seed>.SUPERSEDED-<ts>.yaml`` and the regraded result is written back
  under the original name. Those retired bytes are the only undo this script has
  ever had -- ``.gitignore`` excludes ``notebooks/*/results/``, so there is no
  git safety net behind them.

Because a regrade now reaches S3, a local one is no longer clobbered by the next
``results_store.sync_down`` -- a one-way S3-to-local mirror that OVERWRITES the
local tree, and a score flip preserves byte length, so nothing would have caught
that loss.

``--write`` is still the gate. A dry run reads the store, prints the full tally
table, and writes nothing at all: no ``put_object``, no rename, no rewrite. The
tallies come from the authoritative store on both backends, so a dry run's
numbers are exactly what a ``--write`` would apply.

Run from the repo root:
    .venv/bin/python scripts/results/regrade.py [--study induction] [--write]
"""

import argparse
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from smolbench.evals import Marks  # noqa: E402
# Imported as a MODULE, not by name, for two reasons. (1) `results_store.utcnow`
# is this project's "now" seam: reading it through the module means a caller
# that repoints it (as the offline tests do) is honoured, where a
# `from ... import utcnow` binding would silently freeze the real clock into
# every regraded run's key. (2) Module scope is safe despite the house rule that
# importing a module must not require the AWS SDK -- `results_store` imports no
# boto3 itself, and `smolbench.evals._aws` defers its own `import boto3` into
# the call, so importing this script still costs nothing on a box without it.
from smolbench.evals import results_store as rs  # noqa: E402
from smolbench.evals.parsing import parse_numeric  # noqa: E402
from smolbench.evals.quiz import COMPLIANT  # noqa: E402
from smolbench.evals.study_config import roster_keys, tag_for  # noqa: E402
# The single declaration of the four info-arm names; restating them here would
# make this script a second place to update when an arm is added or renamed.
# `periodic` imports no AWS SDK and no tokenizers at module scope, so this stays
# a cheap import.
from smolbench.induction.periodic import CONDITIONS  # noqa: E402

STUDIES = {
    "induction": "notebooks/induction/results",
}

#: Operator-facing text recorded on every retirement this script causes: each S3
#: ``.superseded`` marker stores it under ``"reason"``, and
#: ``LocalResultsStore.supersede`` logs it. Named once rather than re-spelled at
#: each call site so every marker this script has ever written reads identically
#: and can be grepped for as one string.
REGRADE_REASON = "regraded with the compliance-aware parser (parse_numeric)"

#: Arm names ordered longest-first, which is the order a condition directory
#: name must be matched against. ``noise_intens`` ENDS WITH ``intens``, so a
#: shortest-first scan would split ``gemma4_e2b_noise_intens`` into tag
#: ``gemma4_e2b_noise`` and info ``intens`` -- a tag that names no checkpoint.
#: ``sorted`` is stable, so same-length arms (``intens``/``extens``) keep
#: ``CONDITIONS``'s declaration order and the result is deterministic.
ARMS_LONGEST_FIRST: Tuple[str, ...] = tuple(sorted(CONDITIONS, key=len, reverse=True))


def split_condition_dirname(name: str) -> Optional[Tuple[str, str]]:
    """Split a ``"<tag>_<info>"`` condition directory name into its two parts.

    Both halves may themselves contain ``_`` (analysis tags do: ``gemma4_e2b``;
    so does the ``noise_intens`` arm), so the name cannot be split on ``_``
    positionally. It is instead matched against the KNOWN arm names as a
    ``_<info>`` suffix, longest arm first (see `ARMS_LONGEST_FIRST`).

    Parameters
    ----------
    name : str
        A directory name from a local results tree; untrusted, since the tree
        may hold directories this study never wrote.

    Returns
    -------
    tuple of (str, str), or None
        ``(tag, info)`` when `name` ends in ``_<arm>`` for some arm in
        ``CONDITIONS`` and leaves a non-empty tag; ``None`` when it matches no
        arm, which the caller reports rather than swallows.
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

    Returns
    -------
    dict
        One entry per roster checkpoint. Well-defined as a dict because the tag
        mapping is injective -- ``study_config`` validates that at load, so no
        two checkpoints can collide onto one tag here.
    """
    return {tag_for(key): key for key in roster_keys()}


def roster_conditions(
    store: "rs.ResultsStore", arms: Optional[List[str]]
) -> List[Tuple[str, str, List["rs.ReplicateAddress"]]]:
    """Enumerate an S3-backed study's conditions from the committed roster.

    An S3-backed study has no local tree to walk -- the log IS the store -- so
    the addresses come from the study's own definition instead: every roster
    checkpoint crossed with every info arm. A model OUTSIDE the roster is
    therefore not regraded. That is the right scope, not a gap: the roster is
    what defines this study (the same single-source rule that already makes
    ``run_study`` and ``power_analysis`` derive their model lists from it), so
    an off-roster model's runs are not part of the study whose grading
    convention this pass exists to unify, and pulling them in would let this
    script rewrite results no analysis here reads.

    Parameters
    ----------
    store : ResultsStore
        An ``S3ResultsStore``; queried once per (model, arm) for its seeds.
    arms : list of str, or None
        ``--arm`` filter; ``None`` selects every arm. Applied BEFORE the seed
        listing, so an unselected arm costs no store calls at all.

    Returns
    -------
    list of (str, str, list of ReplicateAddress)
        ``(tag, info, addresses)`` per non-empty condition, in ladder order
        (the study's canonical order) crossed with ``CONDITIONS``'s order.

    Notes
    -----
    COST: one ``list_seeds`` call per (checkpoint, arm), so an unfiltered pass
    over the full study is 21 x 4 = 84 paginated ``list_objects_v2``
    traversals, and since ``list_seeds`` scans a whole ``<model>/`` prefix and
    filters to `info` itself, each model's prefix is walked four times over.
    That is deliberate: the cheap alternative is to list each prefix ONCE and
    sort the keys into arms with ``results_store._parse_log_entry``, which
    would make this script a second consumer of a PRIVATE key-shape parser and
    put the log's layout in two places. A one-shot CLI can afford 84 listings;
    a duplicated key format is a correctness liability for as long as it
    exists. ``--arm`` cuts the count proportionally, since the filter is
    applied before the call.
    """
    conditions = []
    for key in roster_keys():
        tag = tag_for(key)
        for info in CONDITIONS:
            label = f"{tag}_{info}"
            if arms and not any(label.endswith(arm) for arm in arms):
                continue
            # The S3 log is keyed by MODEL (the roster spec key), not by tag;
            # `tag` rides along on the address for the report label and for the
            # local layout's sake. See `ReplicateAddress.model`.
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

    The filesystem, not the roster, is the authority here: a local tree may
    legitimately hold condition directories from older archetype schemes the
    current roster no longer names, and those are exactly the results most in
    need of a regrade onto the current convention. Walking the tree keeps them
    in scope.

    Parameters
    ----------
    store : ResultsStore
        A ``LocalResultsStore`` rooted at `tree`; queried for each condition's
        seeds, so the retired-file exclusion stays the store's rule rather than
        a glob restated here.
    tree : Path
        The study's results directory; must exist (the caller checks).
    arms : list of str, or None
        ``--arm`` filter; ``None`` selects every arm. Applied BEFORE the seed
        listing, exactly as on the S3 path.

    Returns
    -------
    list of (str, str, list of ReplicateAddress)
        ``(tag, info, addresses)`` per non-empty condition, in sorted directory
        order -- the order this report has always printed.

    Notes
    -----
    A directory matching no known arm is SKIPPED with a printed warning naming
    it, never silently: it may be a stale scratch directory, or it may be a real
    condition whose arm was renamed, and only an operator can tell which.
    """
    conditions = []
    # Derived ONCE: the roster is fixed for the whole walk, so building the
    # 21-entry reverse mapping per directory would re-read the same config for
    # every condition.
    models = models_by_tag()
    # `{tag}_{info}` always contains at least one "_", so "*_*" is the cheapest
    # pre-filter that cannot exclude a real condition directory.
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
        # `None` for a tag no roster checkpoint carries. Harmless here:
        # `LocalResultsStore` ignores `addr.model` entirely (its layout has no
        # model dimension), and this branch only ever runs against that store.
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

    Parameters
    ----------
    store : ResultsStore
        The study's resolved store.
    tree : Path
        The study's local results directory. Used only on the local path; an
        S3-backed study need never have created it.
    arms : list of str, or None
        ``--arm`` filter, forwarded verbatim.

    Returns
    -------
    list of (str, str, list of ReplicateAddress)
        ``(tag, info, addresses)`` per non-empty condition.
    """
    if isinstance(store, rs.S3ResultsStore):
        return roster_conditions(store, arms)
    return tree_conditions(store, tree, arms)


def load_for_regrade(
    store: "rs.ResultsStore", addr: "rs.ReplicateAddress"
) -> Optional[Tuple[Marks, str]]:
    """Load the replicate at `addr` together with the ``run_ts`` it would replace.

    ``ResultsStore.regrade`` refuses a replacement that does not name what it
    replaces, so the two are resolved together here -- the stamp is not
    recoverable from the loaded `Marks`, which carry no ``run_ts`` field.

    Parameters
    ----------
    store : ResultsStore
        The study's resolved store.
    addr : ReplicateAddress
        The replicate to read.

    Returns
    -------
    tuple of (Marks, str), or None
        The stored result and the stamp it would supersede; ``None`` when
        nothing survives at `addr` to regrade, which the caller reports.

    Notes
    -----
    The two backends carry different provenance, so the stamp is sourced
    differently:

    * S3: the EARLIEST surviving run (``list_runs(addr)[0]``), which under
      earliest-wins is by definition the run ``load_marks`` is about to return.
      An empty listing means nothing was ever logged there, or everything logged
      there was already superseded; either way there is nothing to replace, so
      ``None`` is returned BEFORE ``load_marks``, which would otherwise raise.
    * Local: the layout stores no ``run_ts`` at all -- one file per address,
      overwritten in place -- so the collection date the file was stamped with
      is the only provenance it carries, and ``format_run_ts(marks.date)`` is
      what the replacement names.

    Resolved identically under ``--write`` and under a dry run, so the dry run
    accounts for exactly the addresses a write would touch, skips included.
    """
    if isinstance(store, rs.S3ResultsStore):
        survivors = store.list_runs(addr)
        if not survivors:
            return None
        return store.load_marks(addr), survivors[0]
    marks = store.load_marks(addr)
    return marks, rs.format_run_ts(marks.date)


def regrade_marks(marks: Marks, parse) -> Dict:
    """Re-parse one replicate's marks with `parse` (e.g. `parse_numeric`).

    Nothing is written; the caller decides whether to hand the new `Marks` to
    ``ResultsStore.regrade``.

    Parameters
    ----------
    marks : Marks
        The stored result, as returned by ``ResultsStore.load_marks``.
    parse : callable
        ``str -> ParseResult`` (fields ``value`` and ``violation``); applied to
        each mark's raw ``response``.

    Returns
    -------
    dict
        ``marks`` -- the SAME result as `marks`, with only the per-mark score
        and compliance re-parsed; every other field (``model``, ``date``,
        ``server_config``) is preserved unchanged. Also ``n``,
        ``before_correct``, ``before_invalid``, ``changed``, ``recovered``
        (invalid -> real verdict), ``broke`` (real verdict -> invalid),
        ``violations`` (`Counter` of output-contract violations).
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
        # A regrade is a PRODUCER of compliance labels, so it spells the
        # compliant case OUT rather than storing the pre-COMPLIANT
        # `compliance: null` that `Marks.loads`' read-compat shim exists to
        # translate on the way back IN. Written as an explicit `is None` test
        # and not `result.violation or COMPLIANT`: the latter would relabel any
        # future falsy violation label (an empty string, say) as compliant --
        # the exact inversion of what it means.
        compliance = COMPLIANT if result.violation is None else result.violation
        new_marks.append(replace(mark, score=score, compliance=compliance))

    return {
        # Design: `replace` instead of naming `model`/`marks`/`date` by hand --
        # a per-field re-construction silently drops any field added to
        # `Marks` later, and it already dropped `server_config` (the serving-
        # stack snapshot), so every --write blanked hardware provenance that
        # a re-fetch cannot restore.
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

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments, excluding the program name. ``None`` (the
        default) reads ``sys.argv``, matching normal CLI invocation; a list
        is used verbatim, which is how the offline tests drive this function.

    Returns
    -------
    int
        ``1`` if any mark regressed from a real verdict to invalid; ``0``
        otherwise. Whether a study is S3-backed or local no longer bears on the
        exit code -- both are regradable through the store.

    Notes
    -----
    Addresses are enumerated for the WHOLE study up front, before any write, so
    a seed listing can never observe the runs this same pass just appended.

    Each regrade is stamped with its own :func:`results_store.utcnow`: one new
    run per address. In the pathological case where that instant falls in the
    same whole second as the run being replaced, the new run's key equals the
    superseded one's and the replacement hides behind its own marker. The two
    stamps differ in practice -- a regrade always follows its collection by more
    than a second -- so this is documented rather than guarded.
    """
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--study", choices=sorted(STUDIES), action="append")
    argp.add_argument("--arm", action="append", help="only conditions ending in this arm")
    # NOT "rewrite YAMLs in place": nothing is rewritten in place on either
    # backend now, and this one sentence is the whole description an operator
    # reads before spending a write.
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
        # Resolved ONCE per study: `resolve_store` reads the environment at call
        # time, and every address below has to be read and written through the
        # same backend the enumeration was built from.
        store = rs.resolve_store(tree)
        # The missing-tree skip is a LOCAL-backend concern only. An S3-backed
        # study keeps nothing on disk -- the log is the store -- so a box that
        # has only ever read from S3 need never have created this directory, and
        # checking it unconditionally would silence every S3-backed study.
        if not isinstance(store, rs.S3ResultsStore) and not tree.is_dir():
            continue
        parse = parse_numeric
        print(f"\n{'=' * 92}\n### {study}{'  (DRY RUN)' if not args.write else '  (WRITING)'}\n{'=' * 92}")
        print(
            f"{'condition':26s} {'n':>6s} {'acc before':>11s} {'acc after':>10s} "
            f"{'inval b/a':>12s} {'recov':>6s} {'noncompliant':>13s}"
        )

        for tag, info, addrs in enumerate_conditions(store, tree, args.arm):
            # On a local tree this label is exactly the directory name this
            # report has always printed.
            cond = f"{tag}_{info}"
            n = before_c = before_i = after_c = after_i = 0
            recovered = broke = 0
            violations: Counter = Counter()
            pending: List = []

            # Phase 1: read and re-grade every replicate in this condition.
            # Nothing is written yet, under --write or otherwise.
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
                # `regraded_from` names the run this replacement retires;
                # `ResultsStore.regrade` refuses a replacement without it. Set
                # here, not inside `regrade_marks`, which knows only the marks.
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
                # Every address here was skipped, or every replicate was empty.
                # Reported rather than dropped, and returned from before the
                # rate columns below divide by `n`.
                print(f"  {cond:24s} -- no readable mark to regrade")
                continue

            # Phase 2: the per-condition report row, printed whether or not this
            # is a dry run -- its numbers come from the authoritative store, so
            # they are what a --write would apply.
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

            # Phase 3: the ONLY write path, and only under --write (`pending` is
            # left empty otherwise). `ResultsStore.regrade` owns the policy on
            # both backends -- retire every survivor, then append the
            # self-describing replacement -- so this loop never spells that
            # sequence out for itself.
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
