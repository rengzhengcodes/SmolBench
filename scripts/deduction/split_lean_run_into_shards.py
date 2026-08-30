"""Split an UNSHARDED deduction run's outputs into pre-seeded shard run dirs.

Reshards a mid-flight lane so it finishes faster: kill the driver, split what it
already banked into n theorem-stride shard dirs
(``runs/scaling_<key>_shard<i>of<n>``), then relaunch n drivers with
``LEAN_SHARD=i/n`` -- each one's resume skips the pre-seeded cells and generates
only what is missing. ``scripts/deduction/merge_lean_shards.py`` folds them back
into the canonical run. Shard assignment goes through
``runner._select_theorems`` with ``shard: "i/n"``, the exact code path the
relaunched shards use, so split and shards can never disagree about ownership.

The source dir is only READ (rows copied out, ``theorems/`` subtrees copied not
moved); the caller renames it out of the canonical path first and deletes it only
after the merge's verified S3 spool. Every row must land in exactly one shard, so
the script aborts BEFORE writing any shard dir on an unmapped ``theorem_id``, an
unknown ``kind``, a duplicate cell key, or a torn MIDDLE line (corruption), while
a torn FINAL line (SIGKILL mid-write) is dropped with a warning and regenerates
on resume. ``server_config.yaml`` and ``manifest.json`` go to shard 0 (the latter
as ``manifest_prelude.json``, the unsharded phase's provenance; the shard's own
sweep writes a fresh ``manifest.json``), because shard 0 relaunches against the
ORIGINAL box through the original state file, keeping the sidecar chain as one
box's history -- copy the prelude into the canonical dir before spooling.

Runbook: ``kill -9`` the driver -- NOT SIGINT/SIGTERM, whose ``--teardown``
finally block must never run against the live box -- rename
``runs/scaling_<key>`` aside, run this script against that copy, then relaunch
one driver per shard with ``LEAN_SHARD=i/n``, within 30 minutes of the kill
(shard 0's idle watchdog).
"""

import argparse
import json
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
RESULTS_RUNS: Path = REPO_ROOT / "notebooks" / "deduction" / "results" / "runs"


def _cell_key(row: dict) -> tuple:
    return (
        row.get("model"),
        row.get("theorem_id"),
        row.get("k"),
        row.get("rung"),
        row.get("replicate_idx"),
    )


def split_run(
    key: str,
    n: int,
    *,
    source: Path,
    runs_root: Path,
    theorems_spec: dict,
) -> list[Path]:
    """Partition `source`'s rows and theorem artifacts into n shard directories.

    Every gate runs on in-memory structures before the first shard directory is
    created, so a failed gate leaves the tree untouched. `theorems_spec` must NOT
    carry a ``shard`` key: this function adds ``shard: "i/n"`` per shard before
    calling ``runner._select_theorems``. Returns the shard directory paths in
    shard order.

    Raises
    ------
    SystemExit
        On any failed gate (see the module docstring), or if `source` has no
        ``all_rows.jsonl``, or if a target shard directory already exists.
    """
    from smolbench.deduction.lean import runner  # heavy import chain; local

    if not (source / "all_rows.jsonl").is_file():
        raise SystemExit(f"{source} has no all_rows.jsonl -- wrong --source?")
    shard_dirs = [runs_root / f"scaling_{key}_shard{i}of{n}" for i in range(n)]
    for d in shard_dirs:
        if d.exists():
            raise SystemExit(f"{d} already exists -- refusing to re-split over it.")

    # Assign shards through the shards' own selection code path.
    owner: dict[str, int] = {}
    slug_owner: dict[str, int] = {}
    for i in range(n):
        names = [
            t.full_name
            for t in runner._select_theorems({**theorems_spec, "shard": f"{i}/{n}"})
        ]
        for name in names:
            if name in owner:
                raise SystemExit(f"theorem {name} in two shards ({owner[name]} and {i})")
            owner[name] = i
            slug_owner[runner.slug_theorem(name)] = i

    # Partition rows. This function gates every row before it writes anything.
    lines = (source / "all_rows.jsonl").read_text().splitlines()
    per_shard: list[list[str]] = [[] for _ in range(n)]
    seen_cells: set[tuple] = set()
    torn_tail = False
    for lineno, line in enumerate(lines):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if lineno == len(lines) - 1:
                torn_tail = True
                logging.warning("torn final line dropped (regenerates on resume)")
                continue
            raise SystemExit(f"corrupt row mid-file at line {lineno + 1} -- aborting")
        kind = row.get("kind")
        if kind not in ("cell", "sanity"):
            raise SystemExit(f"unknown row kind {kind!r} at line {lineno + 1}")
        if kind == "cell":
            ck = _cell_key(row)
            if ck in seen_cells:
                raise SystemExit(f"duplicate cell in source run: {ck}")
            seen_cells.add(ck)
        theorem = row.get("theorem_id")
        if theorem not in owner:
            raise SystemExit(f"row theorem {theorem!r} maps to no shard -- wrong spec?")
        per_shard[owner[theorem]].append(line)

    # Partition theorem artifact directories by slug.
    theorem_subdirs = []
    tdir = source / "theorems"
    if tdir.is_dir():
        for sub in sorted(tdir.iterdir()):
            if sub.name not in slug_owner:
                raise SystemExit(f"theorems/{sub.name} maps to no shard -- wrong spec?")
            theorem_subdirs.append((sub, slug_owner[sub.name]))

    # All gates passed. Write the shard directories.
    for i, d in enumerate(shard_dirs):
        d.mkdir(parents=True)
        with (d / "all_rows.jsonl").open("w") as sink:
            for line in per_shard[i]:
                sink.write(line + "\n")
    for sub, i in theorem_subdirs:
        shutil.copytree(sub, shard_dirs[i] / "theorems" / sub.name)
    if (source / "server_config.yaml").is_file():
        shutil.copy2(source / "server_config.yaml", shard_dirs[0] / "server_config.yaml")
    if (source / "manifest.json").is_file():
        shutil.copy2(source / "manifest.json", shard_dirs[0] / "manifest_prelude.json")

    for i, d in enumerate(shard_dirs):
        n_cell = sum(1 for line in per_shard[i] if json.loads(line).get("kind") == "cell")
        logging.info(f"shard {i}/{n}: {len(per_shard[i])} rows ({n_cell} cells) -> {d}")
    if torn_tail:
        logging.info("note: one torn final line was dropped; that cell regenerates.")
    return shard_dirs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("key", help="spec key of the lane (e.g. gemma-4-12b)")
    parser.add_argument("--n", type=int, required=True, help="number of shards")
    parser.add_argument(
        "--source", type=Path, required=True,
        help="the unsharded run dir (rename it OUT of runs/scaling_<key> first)",
    )
    args = parser.parse_args(argv)

    # The study's user-locked theorems spec. It must match the shards'
    # config (notebooks/deduction/run_study.py build_config), or the split
    # disagrees with the relaunched shards about theorem ownership.
    theorems_spec = {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }
    split_run(
        args.key, args.n,
        source=args.source.resolve(),
        runs_root=RESULTS_RUNS,
        theorems_spec=theorems_spec,
    )
    print(f"SPLIT COMPLETE: {args.key} -> {args.n} shards", flush=True)


if __name__ == "__main__":
    main()
