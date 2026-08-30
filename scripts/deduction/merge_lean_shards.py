"""Merge a sharded deduction lane's run directories into the canonical run.

``notebooks/deduction/run_study.py`` can run one lane as N theorem-stride shards
(``LEAN_SHARD=i/n``; ``runner._select_theorems``'s ``shard`` key), each writing a
NON-canonical ``runs/scaling_<key>_shard<i>of<n>`` under ``--no-s3``: shard dirs
must never reach the canonical S3 prefix, whose sole ``all_rows.jsonl`` is what
``scripts/deduction/lean_verify_rows.py`` and the analysis read. This script folds
the shards into one canonical ``runs/scaling_<key>``, regenerates ``analysis.txt``
and, under ``--spool``, uploads via the driver's verified two-phase ``spool_to_s3``
and only then prunes the shard dirs, so no run data accumulates locally.

Merge gates (hard failures; nothing is written past a failed one): every shard dir
has ``all_rows.jsonl`` and ``manifest.json``; no duplicate cell key
(model, theorem_id, k, rung, replicate_idx) or sanity theorem across shards
(stride shards are disjoint, so a duplicate means a mis-sharded/double-run lane);
merged totals equal ``--expect-cells``/``--expect-sanity``; no ``theorems/`` path
collides; the canonical ``all_rows.jsonl`` does not already exist (never overwritten).

Run from the repo root after the shard drivers have exited::

    .venv/bin/python scripts/deduction/merge_lean_shards.py ministral-3-14b --n 3 --spool
"""

import argparse
import importlib.util
import json
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
RESULTS_RUNS: Path = REPO_ROOT / "notebooks" / "deduction" / "results" / "runs"

#: Model-independent full-lane row counts for this study's fixed 300-theorem set
#: and 4 rungs; they do not vary by model because skip_trivial depends only on
#: theorem structure.
EXPECT_CELLS: int = 944
EXPECT_SANITY: int = 300


def _cell_key(row: dict) -> tuple:
    return (
        row.get("model"),
        row.get("theorem_id"),
        row.get("k"),
        row.get("rung"),
        row.get("replicate_idx"),
    )


def merge_shards(
    key: str,
    n: int,
    *,
    runs_root: Path,
    expect_cells: int | None,
    expect_sanity: int | None,
) -> Path:
    """Fold ``n`` shard run directories into the canonical ``scaling_<key>`` directory.

    Parameters
    ----------
    runs_root : Path
        Holds both the shard run dirs and the canonical run dir.
    expect_cells, expect_sanity : int or None
        Merged row-count gates; ``None`` disables either.

    Returns
    -------
    Path
        The canonical run directory.

    Raises
    ------
    SystemExit
        On any failed gate (see the module docstring). May leave the canonical dir
        absent or partial; never touches the shard dirs, which only ``main`` prunes
        after a verified S3 spool.
    """
    canonical = runs_root / f"scaling_{key}"
    shard_dirs = [runs_root / f"scaling_{key}_shard{i}of{n}" for i in range(n)]

    for d in shard_dirs:
        for required in ("all_rows.jsonl", "manifest.json"):
            if not (d / required).is_file():
                raise SystemExit(f"shard dir {d} is missing {required} -- shard incomplete?")
    if (canonical / "all_rows.jsonl").exists():
        raise SystemExit(f"{canonical / 'all_rows.jsonl'} already exists -- refusing to clobber.")

    # Gates run before anything is written.
    cell_keys: set[tuple] = set()
    sanity_ids: set[str] = set()
    per_shard_rows: list[list[str]] = []
    n_cells = n_sanity = 0
    for d in shard_dirs:
        lines = (d / "all_rows.jsonl").read_text().splitlines()
        per_shard_rows.append(lines)
        for line in lines:
            row = json.loads(line)
            if row.get("kind") == "cell":
                n_cells += 1
                k = _cell_key(row)
                if k in cell_keys:
                    raise SystemExit(f"duplicate cell across shards: {k}")
                cell_keys.add(k)
            elif row.get("kind") == "sanity":
                n_sanity += 1
                t = row.get("theorem_id")
                if t in sanity_ids:
                    raise SystemExit(f"duplicate sanity row across shards: {t}")
                sanity_ids.add(t)
    if expect_cells is not None and n_cells != expect_cells:
        raise SystemExit(f"merged cell count {n_cells} != expected {expect_cells}")
    if expect_sanity is not None and n_sanity != expect_sanity:
        raise SystemExit(f"merged sanity count {n_sanity} != expected {expect_sanity}")

    # Gate: the theorems/ trees must be disjoint (theorem-stride shards are).
    seen_rel: dict[str, Path] = {}
    for d in shard_dirs:
        tdir = d / "theorems"
        if tdir.is_dir():
            for p in tdir.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(d))
                    if rel in seen_rel:
                        raise SystemExit(f"theorems/ collision: {rel} in both {seen_rel[rel]} and {d}")
                    seen_rel[rel] = d

    # All gates passed. Write the canonical directory.
    canonical.mkdir(parents=True, exist_ok=True)
    with (canonical / "all_rows.jsonl").open("w") as sink:
        for lines in per_shard_rows:
            for line in lines:
                sink.write(line + "\n")

    for rel, d in sorted(seen_rel.items()):
        dst = canonical / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / rel, dst)

    # Each shard's server_config.yaml is already a YAML list of timestamped
    # snapshots (the driver appends), so plain concatenation in shard order stays
    # valid YAML and preserves the three-box provenance the study requires.
    with (canonical / "server_config.yaml").open("w") as sink:
        for d in shard_dirs:
            sc = d / "server_config.yaml"
            if sc.is_file():
                sink.write(sc.read_text())

    manifests = []
    for i, d in enumerate(shard_dirs):
        manifest = json.loads((d / "manifest.json").read_text())
        manifests.append(manifest)
        shutil.copy2(d / "manifest.json", canonical / f"manifest_shard{i}of{n}.json")
    synthesized = dict(manifests[0])
    synthesized["run_name"] = f"scaling_{key}"
    config = dict(synthesized.get("config") or {})
    theorems = dict(config.get("theorems") or {})
    theorems.pop("shard", None)  # the union of shards IS the unsharded selection
    config["theorems"] = theorems
    config["run_name"] = f"scaling_{key}"
    synthesized["config"] = config
    synthesized["counts"] = {
        c: sum((m.get("counts") or {}).get(c, 0) for m in manifests)
        for c in ("written", "skipped", "success")
    }
    synthesized["merged_from_shards"] = [
        {
            "run_name": (m.get("config") or {}).get("run_name") or m.get("run_name"),
            "shard": ((m.get("config") or {}).get("theorems") or {}).get("shard"),
            "started_at": m.get("started_at"),
            "finished_at": m.get("finished_at"),
            "counts": m.get("counts"),
        }
        for m in manifests
    ]
    (canonical / "manifest.json").write_text(json.dumps(synthesized, indent=2) + "\n")

    logging.info(
        f"merged {n} shard(s) -> {canonical}: {n_cells} cells + {n_sanity} sanity rows"
    )
    return canonical


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("key", help="spec key of the lane (e.g. ministral-3-14b)")
    parser.add_argument("--n", type=int, required=True, help="number of shards")
    parser.add_argument("--expect-cells", type=int, default=EXPECT_CELLS)
    parser.add_argument("--expect-sanity", type=int, default=EXPECT_SANITY)
    parser.add_argument(
        "--no-expect", action="store_true",
        help="skip the merged-total gates (uniqueness gates always apply)",
    )
    parser.add_argument(
        "--spool", action="store_true",
        help="after merging, spool the canonical dir to S3 via the driver's "
        "spool_to_s3 and, on verified success, DELETE the shard run dirs",
    )
    args = parser.parse_args(argv)

    canonical = merge_shards(
        args.key,
        args.n,
        runs_root=RESULTS_RUNS,
        expect_cells=None if args.no_expect else args.expect_cells,
        expect_sanity=None if args.no_expect else args.expect_sanity,
    )

    # Per-shard analysis.txt files are partial and were not copied; regenerate.
    from smolbench.deduction.lean import runner  # late: heavy import chain

    runner.write_run_analysis(canonical)

    if args.spool:
        # Reuse the driver's verified two-phase spool rather than re-deriving
        # bucket/prefix/verify semantics; loaded by file path like the driver itself.
        spec = importlib.util.spec_from_file_location(
            "merge_lean_shards_driver",
            REPO_ROOT / "notebooks" / "deduction" / "run_study.py",
        )
        driver = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = driver
        spec.loader.exec_module(driver)
        uploaded = driver.spool_to_s3(canonical, args.key)
        logging.info(f"spooled {uploaded} file(s) for scaling_{args.key}")
        # The spool verified every upload; only now prune the shard dirs.
        for i in range(args.n):
            shard_dir = RESULTS_RUNS / f"scaling_{args.key}_shard{i}of{args.n}"
            shutil.rmtree(shard_dir)
            logging.info(f"pruned shard dir {shard_dir}")

    print(f"MERGE COMPLETE: scaling_{args.key} ({args.n} shards)", flush=True)


if __name__ == "__main__":
    main()
