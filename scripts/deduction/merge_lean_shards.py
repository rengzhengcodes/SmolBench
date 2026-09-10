"""Merge sharded deduction lanes into their canonical run directory.

Shard directories must never reach the canonical S3 prefix; prune only after verified spool.
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


def merge_shards(
    key: str,
    n: int,
    *,
    runs_root: Path,
    expect_cells: int,
    expect_sanity: int,
) -> Path:
    """Merge shard directories without pruning them.

    Parameters
    ----------
    key : str
        Scaling-run key.
    n : int
        Shard count.
    runs_root : Path
        Run-directory root.
    expect_cells : int
        Expected merged cells.
    expect_sanity : int
        Expected merged sanity rows.

    Returns
    -------
    Path
        Canonical run directory.

    Raises
    ------
    SystemExit
        Failed validation; canonical output may be absent or partial.
    """
    canonical = runs_root / f"scaling_{key}"
    shard_dirs = [runs_root / f"scaling_{key}_shard{i}of{n}" for i in range(n)]

    for d in shard_dirs:
        for required in ("all_rows.jsonl", "manifest.json"):
            if not (d / required).is_file():
                raise SystemExit(f"shard dir {d} is missing {required} -- shard incomplete?")
    if (canonical / "all_rows.jsonl").exists():
        raise SystemExit(f"{canonical / 'all_rows.jsonl'} already exists -- refusing to clobber.")

    # Group after reading all shards so duplicate rows can be distinguished from resumes.
    cell_rows: list[dict] = []
    sanity_ids: set[str] = set()
    per_shard_rows: list[list[dict]] = []
    n_sanity = 0
    from smolbench.deduction.lean import runner

    for d in shard_dirs:
        try:
            kept = runner.read_jsonl_tolerating_torn_tail(d / "all_rows.jsonl")
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{d / 'all_rows.jsonl'}: {exc} -- aborting") from exc
        per_shard_rows.append(kept)
        for row in kept:
            if row.get("kind") == "cell":
                cell_rows.append(row)
            elif row.get("kind") == "sanity":
                n_sanity += 1
                t = row.get("theorem_id")
                if t in sanity_ids:
                    raise SystemExit(f"duplicate sanity row across shards: {t}")
                sanity_ids.add(t)

    # Match `_existing_keys`: exception plus retry is a resume, not a duplicate shard cell.
    grouped = runner.group_cell_rows(cell_rows, runner._cell_key)
    for cell_key, rows in grouped.items():
        surviving = [r for r in rows if r.get("verdict") != "exception"]
        if len(surviving) >= 2:
            raise SystemExit(
                f"duplicate cell across shards: {cell_key} has {len(surviving)} "
                f"surviving rows (verdicts {[r.get('verdict') for r in surviving]})"
            )
    n_resumed = sum(len(rows) > 1 for rows in grouped.values())
    if n_resumed:
        logging.info("%d cell key(s) keep exception rows plus a resumed retry", n_resumed)
    # Count exception+retry once; otherwise a valid resume reads as 945 rows for 944 cells.
    n_cells = len(runner.dedupe_cell_rows(cell_rows))
    if n_cells != expect_cells:
        raise SystemExit(f"merged distinct cell count {n_cells} != expected {expect_cells}")
    if n_sanity != expect_sanity:
        raise SystemExit(f"merged sanity count {n_sanity} != expected {expect_sanity}")

    # Theorem-stride shard trees must be disjoint.
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

    canonical.mkdir(parents=True, exist_ok=True)
    for rows in per_shard_rows:
        runner.write_jsonl(rows, canonical / "all_rows.jsonl")

    for rel, d in sorted(seen_rel.items()):
        dst = canonical / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / rel, dst)

    # Snapshot lists concatenate as valid YAML.
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
    """Merge a sharded lane and optionally spool its canonical run to S3."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("key", help="spec key of the lane (e.g. ministral-3-14b)")
    parser.add_argument("--n", type=int, required=True, help="number of shards")
    parser.add_argument(
        "--expect-cells", type=int, required=True,
        help="expected merged cell count",
    )
    parser.add_argument(
        "--expect-sanity", type=int, required=True,
        help="expected merged sanity-row count",
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
        expect_cells=args.expect_cells,
        expect_sanity=args.expect_sanity,
    )

    # Shard analyses are partial, so regenerate.
    from smolbench.deduction.lean import runner
    runner.write_run_analysis(canonical)

    if args.spool:
        # Reuse verified spool semantics instead of re-deriving bucket and verification.
        spec = importlib.util.spec_from_file_location(
            "merge_lean_shards_driver",
            REPO_ROOT / "notebooks" / "deduction" / "run_study.py",
        )
        driver = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = driver
        spec.loader.exec_module(driver)
        uploaded = driver.spool_to_s3(canonical, args.key)
        logging.info(f"spooled {uploaded} file(s) for scaling_{args.key}")
        # Prune only after every upload is verified.
        for i in range(args.n):
            shard_dir = RESULTS_RUNS / f"scaling_{args.key}_shard{i}of{args.n}"
            shutil.rmtree(shard_dir)
            logging.info(f"pruned shard dir {shard_dir}")

    print(f"MERGE COMPLETE: scaling_{args.key} ({args.n} shards)", flush=True)


if __name__ == "__main__":
    main()
