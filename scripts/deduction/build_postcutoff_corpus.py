"""Turn a LeanDojo-v2 mathlib4 export into a post-cutoff theorem corpus.

This stdlib-only script runs on the trace box; it re-splits filtered rows by
``sha256(full_name)`` because export splits cover a pool ~4 orders larger.
It raises before writing on inconsistency because a smaller pool is silent.
The 2024-03-24 corpus predates roster cutoffs, so its proofs may be memorized.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

#: Replace the trace box's local URL with a usable repository URL.
DEFAULT_REPO_URL = "https://github.com/leanprover-community/mathlib4"
DEFAULT_DATASET_NAME = "SmolBench post-cutoff mathlib4 (LeanDojo-v2 trace)"

#: Two tactics provide a prefix and a held-out next tactic.
DEFAULT_MIN_TACTICS = 2

#: Required metadata plus the unfiltered premise universe.
REQUIRED_EXPORT_FILES = ("metadata.json", "corpus.jsonl", "traced_files.jsonl")

SPLITS = ("train", "val", "test")

#: Deterministic split-file order.
SOURCE_ORDER = tuple(f"random/{split}.json" for split in SPLITS)

#: Recorded with the artefact so its split rule travels with it.
SPLIT_RULE = (
    "int(sha256(full_name)[:8], 16) % 100: <80 -> train, <90 -> val, else test "
    "(deterministic 80/10/10 keyed only on the declaration name)"
)


def validate_export(export: Path) -> list[str]:
    """Validate a LeanDojo-v2 export.

    A missing individual split is not an error because v2 exports omit empty
    splits; zero split files means no theorems to build from.

    Parameters
    ----------
    export : Path

    Returns
    -------
    list[str]
        Existing split files in source order.
    """
    for name in REQUIRED_EXPORT_FILES:
        path = export / name
        if not path.is_file():
            raise SystemExit(
                f"export is missing {path} -- not a LeanDojo-v2 export directory?"
            )

    present = [rel for rel in SOURCE_ORDER if (export / rel).is_file()]
    if not present:
        raise SystemExit(
            f"export {export} contains none of {list(SOURCE_ORDER)} -- no theorems to build from"
        )
    return present


def load_names(path: Path, export_commit: str) -> dict:
    """Load names matching the export commit.

    A name difference for another commit cannot support a post-cutoff claim.

    Parameters
    ----------
    path : Path
    export_commit : str

    Returns
    -------
    dict
        Name-set data.
    """
    names = json.loads(path.read_text())
    if export_commit != names["new_commit"]:
        raise SystemExit(
            f"the export was traced at a different commit than the name-set difference was "
            f"computed at: export from_repo.commit={export_commit!r} but "
            f"{path}'s new_commit={names['new_commit']!r} -- rebuild one of them"
        )
    return names


def read_source_rows(
    export: Path, present: list[str]
) -> tuple[list[dict], dict[str, int]]:
    """Read theorem rows in source order.

    Parameters
    ----------
    export : Path
    present : list[str]

    Returns
    -------
    tuple[list[dict], dict[str, int]]
        Rows and per-file counts.
    """
    rows: list[dict] = []
    rows_per_source_file: dict[str, int] = {}
    for rel in present:
        file_rows = json.loads((export / rel).read_text())
        rows_per_source_file[rel] = len(file_rows)
        rows.extend(file_rows)
    return rows, rows_per_source_file


def assign_split(full_name: str) -> str:
    """Assign a declaration to a split.

    The name-keyed 80/10/10 hash is stable across traces and machines.

    Parameters
    ----------
    full_name : str

    Returns
    -------
    str
        Split name.
    """
    bucket = int(hashlib.sha256(full_name.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "val"
    return "test"


def build_provenance(full_name: str, decl: dict) -> dict:
    """Extract post-cutoff provenance.

    Preserve unknown reasons because rejecting new heuristics would silently
    shrink the pool; ``reason="commit-date"`` has no introducing PR.

    Parameters
    ----------
    full_name : str
    decl : dict

    Returns
    -------
    dict
        Provenance fields.

    Raises
    ------
    SystemExit
        Missing ``introduced_commit`` or ``reason`` evidence.
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
    """Rewrite export rows for the post-cutoff corpus.

    Preserve unknown fields because LeanDojo adds fields and the loader accepts
    them; only ``url``, ``postcutoff``, and ``postcutoff_provenance`` change.

    Parameters
    ----------
    rows : list[dict]
    names : dict
    repo_url : str

    Returns
    -------
    list[dict]
        Corpus rows.

    Raises
    ------
    SystemExit
        Mixed traced commits.
    """
    new_commit = names["new_commit"]
    out: list[dict] = []
    for row in rows:
        if row["commit"] != new_commit:
            raise SystemExit(
                f"theorem {row['full_name']!r} carries commit {row['commit']!r}, not the "
                f"export's {new_commit!r} -- this pool mixes traces and cannot be used"
            )
        provenance = build_provenance(
            row["full_name"], names["decls"][row["full_name"]]
        )
        new_row = dict(row)
        new_row["url"] = repo_url
        new_row["postcutoff"] = True
        new_row["postcutoff_provenance"] = provenance
        out.append(new_row)
    return out


def build_metadata(
    export_metadata: dict, names: dict, args: argparse.Namespace
) -> dict:
    """Copy metadata and add post-cutoff fields.

    Keep ``from_repo.commit`` because `corpus.postcutoff_metadata` requires it
    to match ``postcutoff.new_commit``; `load_names` verifies that match.

    Parameters
    ----------
    export_metadata : dict
    names : dict
    args : argparse.Namespace

    Returns
    -------
    dict
        Corpus metadata.
    """
    meta = copy.deepcopy(export_metadata)
    meta["from_repo"]["url"] = args.repo_url
    meta["dataset_name"] = args.dataset_name
    # `postcutoff_metadata` defines this key set and rename.
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
    """Write the ``leandojo_benchmark_4`` tree.

    Write all three splits, including empty ones, so every loader finds a file;
    copy the unfiltered, hundreds-of-MB premise files instead of reserializing.

    Parameters
    ----------
    out_root : Path
    export : Path
    rows : list[dict]
    metadata : dict

    Returns
    -------
    dict[str, int]
        Per-split row counts.
    """
    dest = out_root / "leandojo_benchmark_4"
    dest.mkdir(parents=True, exist_ok=True)

    # Sort for byte-reproducible output regardless of export order.
    per_split: dict[str, list[dict]] = {split: [] for split in SPLITS}
    for row in rows:
        per_split[assign_split(row["full_name"])].append(row)
    for split_rows in per_split.values():
        split_rows.sort(key=lambda r: r["full_name"])

    (dest / "random").mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        # Preserve readable theorem text and upstream diff style.
        (dest / "random" / f"{split}.json").write_text(
            json.dumps(per_split[split], indent=1, ensure_ascii=False)
        )

    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=1, ensure_ascii=False)
    )
    for name in ("corpus.jsonl", "traced_files.jsonl"):
        shutil.copyfile(export / name, dest / name)

    return {split: len(per_split[split]) for split in SPLITS}


def main(argv: list[str] | None = None) -> int:
    """Build a post-cutoff corpus.

    Failures raise `SystemExit`; gate all inputs before writing so they cannot
    leave partial output.

    Parameters
    ----------
    argv : list[str] | None, optional

    Returns
    -------
    int
        Exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--export",
        type=Path,
        required=True,
        help="LeanDojo-v2 generate_benchmark export directory",
    )
    parser.add_argument(
        "--names",
        type=Path,
        required=True,
        help="postcutoff_names.json from postcutoff_names.py",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="output root; the corpus lands in <out>/leandojo_benchmark_4",
    )
    # Dates are CLI inputs because postcutoff_names.py uses SHAs and a target date, not author dates.
    parser.add_argument(
        "--new-commit-date", required=True, help="YYYY-MM-DD of the new commit"
    )
    parser.add_argument(
        "--old-commit-date", required=True, help="YYYY-MM-DD of the old commit"
    )
    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPO_URL,
        help="canonical URL replacing the export's local checkout path",
    )
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument(
        "--min-tactics",
        type=int,
        default=DEFAULT_MIN_TACTICS,
        help="drop theorems with fewer traced tactics (default 2)",
    )
    args = parser.parse_args(argv)

    present = validate_export(args.export)
    export_metadata = json.loads((args.export / "metadata.json").read_text())
    names = load_names(args.names, export_metadata["from_repo"]["commit"])

    rows, rows_per_source_file = read_source_rows(args.export, present)
    decls = names["decls"]
    postcutoff_named = [row for row in rows if row["full_name"] in decls]
    with_min_tactics = [
        row
        for row in postcutoff_named
        if len(row["traced_tactics"]) >= args.min_tactics
    ]

    if not with_min_tactics:
        # Identify incompatible trees separately from post-cutoff one-liners.
        culprit = (
            f"the post-cutoff name set ({len(decls)} declarations) matched none of the "
            f"{len(rows)} theorems in the export"
            if not postcutoff_named
            else f"the --min-tactics {args.min_tactics} floor dropped all "
            f"{len(postcutoff_named)} post-cutoff theorems"
        )
        raise SystemExit(f"refusing to write an empty corpus: {culprit}")

    out_rows = build_rows(with_min_tactics, names, args.repo_url)

    per_split = write_corpus(
        args.out, args.export, out_rows, build_metadata(export_metadata, names, args)
    )

    full_names = sorted(row["full_name"] for row in out_rows)
    # Match audit_lean_pinning.py's recipe for 2024-03-24 comparability.
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
            "postcutoff_named": len(postcutoff_named),
            "with_min_tactics": len(with_min_tactics),
            "written": len(out_rows),
            "per_split": per_split,
        },
        "sha256_of_sorted_full_names": digest,
        "full_names": full_names,
    }
    # Keep provenance beside the fixed corpus file set. Must follow write_corpus, which creates <out>.
    (args.out / "BUILD_SUMMARY.json").write_text(json.dumps(summary, indent=2))

    print(
        f"post-cutoff corpus written to {args.out / 'leandojo_benchmark_4'}\n"
        f"  read {len(rows)} rows\n"
        f"  post-cutoff named: {len(postcutoff_named)}  "
        f">= {args.min_tactics} tactics: {len(with_min_tactics)}\n"
        f"  written: {len(out_rows)}  "
        f"(train {per_split['train']} / val {per_split['val']} / test {per_split['test']})\n"
        f"  pool sha256: {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
