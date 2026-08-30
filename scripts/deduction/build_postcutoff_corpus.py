"""Turn a LeanDojo-v2 mathlib4 export into a post-cutoff theorem corpus.

Input is what ``scripts/deduction/trace_mathlib_ec2.sh`` produces -- a
``generate_benchmark`` export of mathlib4 at a NEW commit -- plus the
declaration-name JSON that ``scripts/deduction/postcutoff_names.py`` computes as
a name-set difference against an OLD commit. Output is a corpus in exactly the
layout ``smolbench.deduction.lean.corpus`` loads, containing only theorems whose
declaration provably entered mathlib4 after the roster's knowledge cutoff, each
row carrying ``"postcutoff": true`` and the provenance that justifies it.

The point of the exercise is contamination: the 2024-03-24 corpus the original
deduction study used predates every roster model's cutoff, so a model may have
memorised its proofs. This builder keeps only theorems that cannot have been in
any roster model's training data, at the cost of a much smaller pool.

Design
------
* **Stdlib only.** This script must run on the trace box, which has lean-dojo
  and nothing else installed -- so it never imports ``smolbench``, exactly like
  ``scripts/deduction/merge_lean_shards.py``'s duplicated ``_cell_key``. The
  corpus contract it writes against is mirrored from
  ``smolbench/deduction/lean/corpus.py``, not imported.
* **Splits are re-derived, not inherited.** A row's output split is
  ``sha256(full_name)[:8] % 100``: ``< 80`` train, ``< 90`` val, else test. The
  export's own splits are discarded because they partition a pool ~4 orders of
  magnitude larger, so their proportions do not survive the post-cutoff filter;
  keying on the declaration name alone makes the assignment reproducible across
  re-traces and independent of which files a row happened to appear in.
* **Both split families are written.** ``random`` and ``novel_premises`` are two
  partitions of the same theorem universe upstream; here they hold identical
  rows (real copies, not symlinks). The study reads ``random``/``val``, but
  writing all six files means no loader path 404s.
* **Refusals are loud and total.** Every inconsistency raises ``SystemExit``
  with a message naming the offending object, and nothing is written until every
  check has passed. A silently smaller pool is the failure mode this study
  cannot detect after the fact.

Run from anywhere::

    python scripts/deduction/build_postcutoff_corpus.py \\
        --export /mnt/data/export-2ca39e62 --names postcutoff_names.json \\
        --out notebooks/deduction/data \\
        --new-commit-date 2026-08-30 --old-commit-date 2026-04-30
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

#: Canonical upstream URL. The export's ``from_repo.url`` is the trace box's
#: LOCAL checkout path (lean-dojo-v2's local-checkout mode), which is meaningless
#: anywhere else, so every consumer-visible URL is rewritten to this.
DEFAULT_REPO_URL = "https://github.com/leanprover-community/mathlib4"
DEFAULT_DATASET_NAME = "SmolBench post-cutoff mathlib4 (LeanDojo-v2 trace)"

#: A theorem with fewer traced tactics than this is not a usable eval item: the
#: progressive-context eval needs at least one prefix step plus one held-out
#: next tactic.
DEFAULT_MIN_TACTICS = 2

#: Non-split files an export must carry. ``corpus.jsonl`` and
#: ``traced_files.jsonl`` are the premise universe and are copied unfiltered.
REQUIRED_EXPORT_FILES = ("metadata.json", "corpus.jsonl", "traced_files.jsonl")

SPLIT_KINDS = ("random", "novel_premises")
SPLITS = ("train", "val", "test")

#: Fixed read order for the six split files. Load-bearing: dedup keeps the FIRST
#: occurrence of a ``full_name``, so this order alone decides which of a
#: theorem's two copies survives, and therefore the built corpus's bytes.
SOURCE_ORDER = tuple(f"{kind}/{split}.json" for kind in SPLIT_KINDS for split in SPLITS)

#: Human-readable form of `assign_split`, recorded in BUILD_SUMMARY.json so the
#: rule travels with the artefact rather than living only in this file.
SPLIT_RULE = (
    "int(sha256(full_name)[:8], 16) % 100: <80 -> train, <90 -> val, else test "
    "(deterministic 80/10/10 keyed only on the declaration name)"
)


def validate_export(export: Path) -> list[str]:
    """Check that ``export`` looks like a LeanDojo-v2 ``generate_benchmark`` output.

    Parameters
    ----------
    export : Path
        The export directory.

    Returns
    -------
    list of str
        The relative names of the split files that exist, in `SOURCE_ORDER`.
        Never empty.

    Raises
    ------
    SystemExit
        A file in `REQUIRED_EXPORT_FILES` is missing (message names its absolute
        path), or not one split file exists. An individual missing split file is
        NOT an error -- v2 exports legitimately omit empty splits -- but an
        export with no split file at all carries no theorems and can only be a
        wrong directory or a half-finished trace.
    """
    for name in REQUIRED_EXPORT_FILES:
        path = export / name
        if not path.is_file():
            raise SystemExit(f"export is missing {path} -- not a LeanDojo-v2 export directory?")

    present = [rel for rel in SOURCE_ORDER if (export / rel).is_file()]
    if not present:
        raise SystemExit(
            f"export {export} contains none of {list(SOURCE_ORDER)} -- no theorems to build from"
        )
    return present


def load_names(path: Path, export_commit: str) -> dict:
    """Load the post-cutoff name set and check it was computed at ``export_commit``.

    Parameters
    ----------
    path : Path
        ``postcutoff_names.json`` as emitted by ``postcutoff_names.py``.
    export_commit : str
        The export metadata's ``from_repo.commit``.

    Returns
    -------
    dict
        The parsed JSON: ``new_commit``, ``old_commit``, ``target_date``,
        ``method``, ``n_new_decls``, ``n_old_decls``, ``n_postcutoff`` and
        ``decls``.

    Raises
    ------
    SystemExit
        The file's ``new_commit`` differs from ``export_commit``. A name-set
        difference computed at one commit says nothing about a tree traced at
        another: names may have been renamed, moved or deleted in between, so
        every post-cutoff claim in the output would be unfounded.
    """
    names = json.loads(path.read_text())
    if export_commit != names["new_commit"]:
        raise SystemExit(
            f"the export was traced at a different commit than the name-set difference was "
            f"computed at: export from_repo.commit={export_commit!r} but "
            f"{path}'s new_commit={names['new_commit']!r} -- rebuild one of them"
        )
    return names


def read_source_rows(export: Path, present: list[str]) -> tuple[list[dict], dict[str, int]]:
    """Read every theorem row from the export's split files, in `SOURCE_ORDER`.

    Parameters
    ----------
    export : Path
        The export directory.
    present : list of str
        Relative split-file names known to exist, from `validate_export`.

    Returns
    -------
    rows : list of dict
        All rows, concatenated in read order; the same theorem appears once per
        split family, so this list double-counts (see `dedup_by_full_name`).
    rows_per_source_file : dict
        ``{relative name: row count}`` for the files that exist, in read order.
    """
    rows: list[dict] = []
    rows_per_source_file: dict[str, int] = {}
    for rel in present:
        file_rows = json.loads((export / rel).read_text())
        rows_per_source_file[rel] = len(file_rows)
        rows.extend(file_rows)
    return rows, rows_per_source_file


def dedup_by_full_name(rows: list[dict]) -> tuple[list[dict], int]:
    """Collapse the two split families' overlapping rows, keeping the first seen.

    ``random`` and ``novel_premises`` partition the SAME theorem universe
    differently, so their union contains each theorem twice. First-wins in
    `SOURCE_ORDER` rather than any merge of the two copies: they are byte-equal
    upstream, and picking deterministically means a disagreement (a foreign
    ``commit``, say) is caught by the later gates instead of being averaged away.

    Parameters
    ----------
    rows : list of dict
        Rows in read order.

    Returns
    -------
    unique : list of dict
        One row per ``full_name``, in first-seen order.
    duplicates_dropped : int
        ``len(rows) - len(unique)``.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for row in rows:
        name = row["full_name"]
        if name in seen:
            continue
        seen.add(name)
        unique.append(row)
    return unique, len(rows) - len(unique)


def assign_split(full_name: str) -> str:
    """Map a declaration name to its output split.

    Deterministic 80/10/10 over ``int(sha256(full_name)[:8], 16) % 100``. Keyed
    only on the name, so the assignment is stable across re-traces and across
    machines, and reviewers can recompute it by hand.

    Parameters
    ----------
    full_name : str
        The declaration's fully-qualified Lean name.

    Returns
    -------
    str
        ``"train"``, ``"val"`` or ``"test"``.

    Examples
    --------
    >>> assign_split("Mini.postB")
    'val'
    """
    bucket = int(hashlib.sha256(full_name.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "val"
    return "test"


def build_provenance(full_name: str, decl: dict) -> dict:
    """Extract the four provenance fields that justify a theorem's post-cutoff claim.

    Parameters
    ----------
    full_name : str
        The declaration name, used only in error messages.
    decl : dict
        The name JSON's ``decls[full_name]`` entry.

    Returns
    -------
    dict
        ``{"introduced_commit", "pr_number", "pr_created_at", "reason"}``.
        ``pr_number`` and ``pr_created_at`` default to None when absent, and a
        null value for either is legal: ``postcutoff_names.py`` emits
        ``reason="commit-date"`` rows for declarations whose introducing PR it
        could not find. ``reason`` is free-form and is passed through verbatim,
        never validated against an enum -- new heuristics add new reasons, and a
        builder that rejected unknown ones would silently shrink the pool.

    Raises
    ------
    SystemExit
        ``introduced_commit`` or ``reason`` is missing or null. Those two ARE the
        evidence; without them the row asserts "post-cutoff" on no grounds.
    """
    for key in ("introduced_commit", "reason"):
        if decl.get(key) is None:
            raise SystemExit(
                f"decl {full_name!r} has a missing or null {key!r} in the names JSON -- "
                "its post-cutoff claim is unsupported; re-run postcutoff_names.py"
            )
    return {
        "introduced_commit": decl["introduced_commit"],
        "pr_number": decl.get("pr_number"),
        "pr_created_at": decl.get("pr_created_at"),
        "reason": decl["reason"],
    }


def build_rows(rows: list[dict], names: dict, repo_url: str) -> list[dict]:
    """Rewrite surviving export rows into post-cutoff corpus rows.

    Every key of the input row is preserved verbatim (LeanDojo adds fields
    between versions and the loader tolerates unknown ones), with three changes:
    ``url`` is rewritten to ``repo_url``, ``postcutoff`` is set True, and
    ``postcutoff_provenance`` is added.

    Parameters
    ----------
    rows : list of dict
        Deduplicated rows that already passed the name-set and tactic-floor
        filters.
    names : dict
        The loaded names JSON.
    repo_url : str
        Canonical repository URL replacing the export's local checkout path.

    Returns
    -------
    list of dict
        Output rows, in the input order.

    Raises
    ------
    SystemExit
        A row's ``commit`` differs from ``names["new_commit"]`` (the row was
        traced against another tree, so the whole export is mixed), or its decl
        entry fails `build_provenance`.
    """
    new_commit = names["new_commit"]
    out: list[dict] = []
    for row in rows:
        if row["commit"] != new_commit:
            raise SystemExit(
                f"theorem {row['full_name']!r} carries commit {row['commit']!r}, not the "
                f"export's {new_commit!r} -- this pool mixes traces and cannot be used"
            )
        provenance = build_provenance(row["full_name"], names["decls"][row["full_name"]])
        # Shallow copy: only top-level keys are replaced, and the nested values
        # (start/end lists, traced_tactics) are never mutated, so they can be
        # shared with the input row.
        new_row = dict(row)
        new_row["url"] = repo_url
        new_row["postcutoff"] = True
        new_row["postcutoff_provenance"] = provenance
        out.append(new_row)
    return out


def build_metadata(export_metadata: dict, names: dict, args: argparse.Namespace) -> dict:
    """Copy the export's metadata and add the ``postcutoff`` block.

    ``from_repo.commit`` is deliberately left untouched:
    ``corpus.postcutoff_metadata`` refuses a corpus whose ``from_repo.commit``
    disagrees with ``postcutoff.new_commit``, and `load_names` has already proved
    the two are equal.

    Parameters
    ----------
    export_metadata : dict
        The export's ``metadata.json``, parsed.
    names : dict
        The loaded names JSON.
    args : argparse.Namespace
        Parsed CLI arguments; supplies ``repo_url``, ``dataset_name`` and the two
        commit dates.

    Returns
    -------
    dict
        A new metadata dict; the input is not mutated.
    """
    # Deep copy: from_repo is nested and is rewritten below.
    meta = copy.deepcopy(export_metadata)
    meta["from_repo"]["url"] = args.repo_url
    meta["dataset_name"] = args.dataset_name
    # Key set and the n_postcutoff -> n_postcutoff_decls rename are the corpus
    # contract; see `postcutoff_metadata` in smolbench/deduction/lean/corpus.py.
    meta["postcutoff"] = {
        "method": names["method"],
        "new_commit": names["new_commit"],
        "new_commit_date": args.new_commit_date,
        "old_commit": names["old_commit"],
        "old_commit_date": args.old_commit_date,
        "target_date": names["target_date"],
        "n_new_decls": names["n_new_decls"],
        "n_old_decls": names["n_old_decls"],
        "n_postcutoff_decls": names["n_postcutoff"],
    }
    return meta


def write_corpus(
    out_root: Path, export: Path, rows: list[dict], metadata: dict
) -> dict[str, int]:
    """Write the ``leandojo_benchmark_4`` tree under ``out_root``.

    All six split files are always written, empty ones as ``[]``, so that every
    ``load_split(kind, split)`` call reaches a file. ``novel_premises`` receives
    the same rows as ``random``.

    Parameters
    ----------
    out_root : Path
        Output root; ``<out_root>/leandojo_benchmark_4`` is created.
    export : Path
        Source export, for the two premise files.
    rows : list of dict
        Output rows from `build_rows`.
    metadata : dict
        Output metadata from `build_metadata`.

    Returns
    -------
    dict
        ``{"train": n, "val": n, "test": n}`` -- rows written per split. Each
        count applies to BOTH families, which hold identical rows.

    Notes
    -----
    ``corpus.jsonl`` and ``traced_files.jsonl`` are copied with `shutil.copyfile`
    rather than being read and re-serialised: the real ``corpus.jsonl`` is
    hundreds of MB, and premise lookup needs the whole library, so there is
    nothing to filter anyway.
    """
    dest = out_root / "leandojo_benchmark_4"
    dest.mkdir(parents=True, exist_ok=True)

    # Sort within each split by full_name so the files are byte-reproducible
    # regardless of the export's row order.
    per_split: dict[str, list[dict]] = {split: [] for split in SPLITS}
    for row in rows:
        per_split[assign_split(row["full_name"])].append(row)
    for split_rows in per_split.values():
        split_rows.sort(key=lambda r: r["full_name"])

    for kind in SPLIT_KINDS:
        (dest / kind).mkdir(parents=True, exist_ok=True)
        for split in SPLITS:
            # indent=1 / ensure_ascii=False matches LeanDojo's own export style,
            # so a diff against an upstream benchmark stays readable and the
            # Unicode in theorem statements survives as text.
            (dest / kind / f"{split}.json").write_text(
                json.dumps(per_split[split], indent=1, ensure_ascii=False)
            )

    (dest / "metadata.json").write_text(json.dumps(metadata, indent=1, ensure_ascii=False))
    for name in ("corpus.jsonl", "traced_files.jsonl"):
        shutil.copyfile(export / name, dest / name)

    return {split: len(per_split[split]) for split in SPLITS}


def main(argv: list[str] | None = None) -> int:
    """Build a post-cutoff corpus from an export plus a post-cutoff name set.

    Parameters
    ----------
    argv : list of str or None
        Command-line arguments; None reads ``sys.argv[1:]``.

    Returns
    -------
    int
        0 on success. Every failure path raises `SystemExit` with a message
        rather than returning a code, so the reason survives into the caller's
        traceback instead of only reaching a terminal.

    Raises
    ------
    SystemExit
        Any failed gate: a malformed export, an export/name-set commit
        disagreement, a row traced at a foreign commit, an unsupported
        post-cutoff claim, or an empty surviving pool. Nothing is written unless
        every gate passes.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--export", type=Path, required=True,
                        help="LeanDojo-v2 generate_benchmark export directory")
    parser.add_argument("--names", type=Path, required=True,
                        help="postcutoff_names.json from postcutoff_names.py")
    parser.add_argument("--out", type=Path, required=True,
                        help="output root; the corpus lands in <out>/leandojo_benchmark_4")
    # The two dates are CLI arguments because the names JSON does not carry
    # them: postcutoff_names.py works from commit SHAs and a target date, and
    # never resolves a SHA to its author date.
    parser.add_argument("--new-commit-date", required=True, help="YYYY-MM-DD of the new commit")
    parser.add_argument("--old-commit-date", required=True, help="YYYY-MM-DD of the old commit")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL,
                        help="canonical URL replacing the export's local checkout path")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--min-tactics", type=int, default=DEFAULT_MIN_TACTICS,
                        help="drop theorems with fewer traced tactics (default 2)")
    args = parser.parse_args(argv)

    # -- Read and gate the inputs; nothing is written in this section. --------
    present = validate_export(args.export)
    export_metadata = json.loads((args.export / "metadata.json").read_text())
    names = load_names(args.names, export_metadata["from_repo"]["commit"])

    rows, rows_per_source_file = read_source_rows(args.export, present)
    unique, duplicates_dropped = dedup_by_full_name(rows)

    decls = names["decls"]
    postcutoff_named = [row for row in unique if row["full_name"] in decls]
    with_min_tactics = [
        row for row in postcutoff_named if len(row["traced_tactics"]) >= args.min_tactics
    ]

    if not with_min_tactics:
        # Which filter emptied the pool decides what to do next: no name overlap
        # means the export and the name set describe different trees, whereas a
        # tactic-floor wipeout means the post-cutoff material exists but is all
        # one-liners.
        culprit = (
            f"the post-cutoff name set ({len(decls)} declarations) matched none of the "
            f"{len(unique)} theorems in the export"
            if not postcutoff_named
            else f"the --min-tactics {args.min_tactics} floor dropped all "
                 f"{len(postcutoff_named)} post-cutoff theorems"
        )
        raise SystemExit(f"refusing to write an empty corpus: {culprit}")

    out_rows = build_rows(with_min_tactics, names, args.repo_url)

    # -- All gates passed; write the corpus. ---------------------------------
    per_split = write_corpus(
        args.out, args.export, out_rows, build_metadata(export_metadata, names, args)
    )

    full_names = sorted(row["full_name"] for row in out_rows)
    # Same digest recipe as the `sha256_of_sorted_full_names` emitted by
    # scripts/results/audit_lean_pinning.py's --reproduce branch, so this pool
    # pin is directly comparable with the 2024-03-24 study's.
    digest = hashlib.sha256("\n".join(full_names).encode()).hexdigest()
    summary = {
        "export": str(args.export.resolve()),
        "names": str(args.names.resolve()),
        "out": str(args.out.resolve()),
        "new_commit": names["new_commit"],
        "old_commit": names["old_commit"],
        "target_date": names["target_date"],
        "min_traced_tactics": args.min_tactics,
        "split_rule": SPLIT_RULE,
        "rows_per_source_file": rows_per_source_file,
        "counts": {
            "rows_read": len(rows),
            "unique_theorems": len(unique),
            "duplicates_dropped": duplicates_dropped,
            "postcutoff_named": len(postcutoff_named),
            "with_min_tactics": len(with_min_tactics),
            "written": len(out_rows),
            "per_split": per_split,
        },
        "sha256_of_sorted_full_names": digest,
        "full_names": full_names,
    }
    # Sibling of leandojo_benchmark_4/, not inside it: the loader treats the
    # corpus directory as a fixed file set and this is build provenance, not
    # data. Must stay AFTER write_corpus, which is what creates <out>.
    (args.out / "BUILD_SUMMARY.json").write_text(json.dumps(summary, indent=2))

    print(
        f"post-cutoff corpus written to {args.out / 'leandojo_benchmark_4'}\n"
        f"  read {len(rows)} rows -> {len(unique)} unique "
        f"(-{duplicates_dropped} cross-family duplicates)\n"
        f"  post-cutoff named: {len(postcutoff_named)}  "
        f">= {args.min_tactics} tactics: {len(with_min_tactics)}\n"
        f"  written: {len(out_rows)}  "
        f"(train {per_split['train']} / val {per_split['val']} / test {per_split['test']})\n"
        f"  pool sha256: {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
