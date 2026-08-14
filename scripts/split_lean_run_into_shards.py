"""Split an UNSHARDED deduction run's outputs into pre-seeded shard run dirs.

WHY THIS EXISTS
---------------
A deduction lane launched unsharded can be resharded MID-FLIGHT to finish
faster: kill the driver, split what it already banked into n theorem-stride
shard run dirs (``runs/scaling_<key>_shard<i>of<n>``), then relaunch n shard
drivers (``LEAN_SHARD=i/n``) whose resume mechanism skips every pre-seeded
cell and generates only what is missing. ``scripts/merge_lean_shards.py``
later folds the completed shards back into the canonical run. The shard
assignment is computed by calling ``runner._select_theorems`` with the run's
own theorems spec plus ``shard: "i/n"`` -- the EXACT code path the relaunched
shards execute -- so the split can never disagree with the shards about
which theorem belongs where.

SAFETY PROPERTIES
-----------------
- The source run dir is READ, never mutated or deleted: rows are copied into
  shard files and ``theorems/`` subtrees are copied (not moved). The caller
  renames the source out of the canonical path first (see the runbook in the
  epilogue of this docstring) and deletes it only after the eventual merge's
  verified S3 spool -- same never-prune-before-verify rule as the spool.
- Every row must partition: a cell/sanity row whose theorem_id maps to no
  shard, an unknown ``kind``, or a duplicate cell key aborts BEFORE any
  shard dir is written. A torn FINAL line (SIGKILL mid-write) is tolerated
  and reported -- its cell simply regenerates on resume; a torn middle line
  aborts (that is corruption, not a torn tail).
- ``server_config.yaml`` and ``manifest.json`` go to shard 0 as
  ``server_config.yaml`` (shard 0 is relaunched against the ORIGINAL box via
  the original state file, so the sidecar chain stays one box's history) and
  ``manifest_prelude.json`` (provenance of the unsharded phase; the shard's
  own sweep writes a fresh ``manifest.json``). At merge time, copy the
  prelude into the canonical dir before spooling.

Runbook (gemma-4-12b mid-flight reshard, 2026-08-14)::

    kill -9 <driver-pid>                       # NOT SIGINT/SIGTERM: the
                                               # --teardown finally block must
                                               # never run against the live box
    mv results/runs/scaling_<key> results/runs/scaling_<key>_presplit
    .venv/bin/python scripts/split_lean_run_into_shards.py <key> --n 4 \
        --source results/runs/scaling_<key>_presplit
    bash scripts/launch_gemma12b_deduction_shards.sh   # within 30 min of the
                                               # kill (idle watchdog) for shard 0
"""

import argparse
import json
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
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
    """Partitions `source`'s rows and theorem artifacts into n shard dirs.

    Returns the shard dir paths. Pure filesystem writer past its gates: all
    validation happens on in-memory structures before the first shard dir is
    created, so a failed gate leaves the tree untouched.
    """
    from smolbench.deduction.lean import runner  # heavy import chain; local

    if not (source / "all_rows.jsonl").is_file():
        raise SystemExit(f"{source} has no all_rows.jsonl -- wrong --source?")
    shard_dirs = [runs_root / f"scaling_{key}_shard{i}of{n}" for i in range(n)]
    for d in shard_dirs:
        if d.exists():
            raise SystemExit(f"{d} already exists -- refusing to re-split over it.")

    # Shard assignment via the shards' own selection code path.
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

    # Partition rows (gates before any write).
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

    # Theorem artifact dirs partition by slug.
    theorem_subdirs = []
    tdir = source / "theorems"
    if tdir.is_dir():
        for sub in sorted(tdir.iterdir()):
            if sub.name not in slug_owner:
                raise SystemExit(f"theorems/{sub.name} maps to no shard -- wrong spec?")
            theorem_subdirs.append((sub, slug_owner[sub.name]))

    # All gates passed -- write.
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

    # The study's user-locked theorems spec -- must match the shards' config
    # (notebooks/deduction/run_study.py build_config) or the split disagrees
    # with the relaunched shards about theorem ownership.
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
