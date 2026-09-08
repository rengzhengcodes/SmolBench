r"""Merge a sharded deduction lane's run directories into the canonical run.

``run_study.py`` can run a lane as N theorem-stride shards, each writing a
NON-canonical ``runs/scaling_<key>_shard<i>of<n>`` under ``--no-s3``: shard
dirs must never reach the canonical S3 prefix. This folds them into one
canonical ``runs/scaling_<key>``, regenerates ``analysis.txt``, and under
``--spool`` uploads via the driver's verified two-phase ``spool_to_s3`` before
pruning the shard dirs. Merge gates (SystemExit) run before anything is
written; see the per-gate messages in ``merge_shards``.

Run from the repo root after the shard drivers have exited::

    .venv/bin/python scripts/deduction/merge_lean_shards.py ministral-3-14b --n 3 \
        --expect-cells <N> --expect-sanity <N> --spool
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
    """Fold ``n`` shard run directories into the canonical ``scaling_<key>`` directory.

    Never touches the shard dirs -- only ``main`` prunes those, after a verified
    S3 spool.

    Parameters
    ----------
    key : str
        Scaling-run key.
    n : int
        Number of shard run directories.
    runs_root : Path
        Directory containing shard and canonical run directories.
    expect_cells : int
        Expected number of merged cell rows.
    expect_sanity : int
        Expected number of merged sanity rows.

    Returns
    -------
    Path
        Canonical merged run directory.

    Raises
    ------
    SystemExit
        On any failed gate (see module docstring); may leave the canonical dir absent or
        partial.
    """
    canonical = runs_root / f"scaling_{key}"
    shard_dirs = [runs_root / f"scaling_{key}_shard{i}of{n}" for i in range(n)]

    for d in shard_dirs:
        for required in ("all_rows.jsonl", "manifest.json"):
            if not (d / required).is_file():
                raise SystemExit(f"shard dir {d} is missing {required} -- shard incomplete?")
    if (canonical / "all_rows.jsonl").exists():
        raise SystemExit(f"{canonical / 'all_rows.jsonl'} already exists -- refusing to clobber.")

    # Rows are gathered by key across all shards first: the duplicate-vs-resume
    # judgment below needs every row for a key in hand.
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

    # At most one SURVIVING row per cell key: runner._existing_keys re-runs a
    # cell whose only row is "exception", so one surviving row plus exception
    # rows is an ordinary resume, not the double-run stride-disjoint shards
    # could never otherwise produce. Anchored on the literal "exception" to
    # match _existing_keys, not the other verdict taxonomies.
    # `cell_key`, not `key`, to avoid shadowing this function's `key` param.
    grouped = runner.group_cell_rows(cell_rows, runner._cell_key)
    for cell_key, rows in grouped.items():
        surviving = [r for r in rows if r.get("verdict") != "exception"]
        if len(surviving) >= 2:
            raise SystemExit(
                f"duplicate cell across shards: {cell_key} has {len(surviving)} "
                f"surviving rows (verdicts {[r.get('verdict') for r in surviving]})"
            )
    n_cells = len(runner.dedupe_cell_rows(cell_rows))
    if n_cells != expect_cells:
        raise SystemExit(f"merged distinct cell count {n_cells} != expected {expect_cells}")
    if n_sanity != expect_sanity:
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

    canonical.mkdir(parents=True, exist_ok=True)
    for rows in per_shard_rows:
        runner.write_jsonl(rows, canonical / "all_rows.jsonl")

    for rel, d in sorted(seen_rel.items()):
        dst = canonical / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / rel, dst)

    # Each server_config.yaml is already a YAML list of timestamped snapshots
    # (the driver appends), so plain concatenation stays valid YAML.
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

    # Per-shard analysis.txt files are partial and were not copied; regenerate.
    from smolbench.deduction.lean import runner
    runner.write_run_analysis(canonical)

    if args.spool:
        # Reuse the driver's verified two-phase spool instead of re-deriving
        # bucket/prefix/verify semantics; loaded by path like the driver itself.
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
