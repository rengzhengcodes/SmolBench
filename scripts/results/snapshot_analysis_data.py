"""Publish an analysis-ready snapshot of the family-ladder study to S3.

Every byte already lives in S3, but under the layout the runners wanted, with
induction and deduction legs named differently and deduction a level deeper.
Republished under one shared ``<dest>/<leg>/<model>/...`` layout that analysis
reads, plus ``<dest>/provenance/*.md`` (how to read the rows) and
``<dest>/MANIFEST.json`` (computed counts only, no prose).

A snapshot, not a move: no source object is modified or deleted. Re-runs
resume, skipping a destination object already present at a matching size, and
every copy is verified against its source size. Copies run server-side, so
~4.5 GB across ~55k objects never transits this host.

``*_SUPERSEDED-*``/``*_STALE-*``/``*_BROKEN-*`` files are copied on purpose:
they are the repair audit trail, and their names say they are not current data.

    scripts/results/snapshot_analysis_data.py [--dry-run] [--dest analysis/2026-08-16]
"""

import argparse
import collections
import concurrent.futures
import json
import logging
import pathlib
from typing import Dict, List, Optional, Tuple

from smolbench.evals.results_store import resolve_results_location

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# No bucket literal here: `main` resolves it at call time via
# `resolve_results_location()`, so a redirected `SMOLBENCH_RESULTS_S3` is
# honored instead of silently missed. `iter_source_keys`/`copy_one` take
# `bucket` explicitly rather than reaching for a module global.
#: Prefixes that are not study data: smoke-test canaries and verifier scratch.
SKIP_SUBSTRINGS = ("canary", "/_verify/", "live_smoke")
#: Provenance documents copied alongside the data, so the snapshot explains
#: itself. Kept as documents rather than `MANIFEST.json` fields: dataset-specific
#: measured counts belong in a dated, version-controlled document, not code.
PROVENANCE_DOCS = (
    "notebooks/README.md",
    "notebooks/ARCHIVE.md",
    "notebooks/deduction/README.md",
    "notebooks/deduction/analysis/SNAPSHOT_NOTES.md",
)


def _s3():
    import boto3

    return boto3.client("s3")


def iter_source_keys(
    client, *, bucket: str, deduction_prefix: Optional[str] = None
) -> List[Tuple[str, str, str, int]]:
    """Return ``(leg, model, source_key, size)`` per study object, minus `SKIP_SUBSTRINGS`.

    The deduction leg carries a ``scaling_`` prefix, stripped here so both legs
    of a model share one name. `bucket` is a parameter, not a module constant,
    so a redirected ``SMOLBENCH_RESULTS_S3`` is honored. `deduction_prefix`
    defaults to `runner.spool_prefix()`; `main` always passes it explicitly.
    """
    if deduction_prefix is None:
        from smolbench.deduction.lean.runner import spool_prefix

        deduction_prefix = spool_prefix() + "/"
    out: List[Tuple[str, str, str, int]] = []
    paginator = client.get_paginator("list_objects_v2")
    for prefix, leg in (("induction/", "induction"), (deduction_prefix, "deduction")):
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if any(s in key for s in SKIP_SUBSTRINGS):
                    continue
                rest = key[len(prefix):]
                model = rest.split("/", 1)[0]
                if leg == "deduction":
                    # 'scaling_qwen3.5-27b' -> 'qwen3.5-27b'
                    model = model[len("scaling_"):] if model.startswith("scaling_") else model
                if "/" not in rest:
                    continue  # skip a stray object directly under the prefix
                out.append((leg, model, key, obj["Size"]))
    return out


def copy_one(client, bucket: str, src_key: str, dest_key: str, size: int) -> str:
    """Copy one object server-side within `bucket`, and verify its size.

    A within-bucket copy: source and destination are the same resolved bucket.
    `size` (the expected source size) decides whether an already-present
    destination object can be skipped. Returns ``"skipped"`` or ``"copied"``;
    raises `RuntimeError` if the copied object's size doesn't match.
    """
    try:
        head = client.head_object(Bucket=bucket, Key=dest_key)
        if head["ContentLength"] == size:
            return "skipped"
    except Exception:  # noqa: BLE001 -- an absent destination is the normal case
        pass
    client.copy_object(
        Bucket=bucket, Key=dest_key,
        CopySource={"Bucket": bucket, "Key": src_key},
        # REPLACE, not the default COPY: the default reads the source's tags,
        # needing s3:GetObjectTagging, which the scoped operator key lacks.
        TaggingDirective="REPLACE",
    )
    got = client.head_object(Bucket=bucket, Key=dest_key)["ContentLength"]
    if got != size:
        raise RuntimeError(f"size mismatch copying {src_key}: {got} != {size}")
    return "copied"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default="analysis/2026-08-16",
                    help="destination prefix inside the study bucket")
    ap.add_argument("--workers", type=int, default=32,
                    help="concurrent copies; the work is pure network wait (default 32)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--spool-prefix", default=None,
        help="S3 key prefix the deduction leg spooled under (default: "
             "LEAN_SPOOL_PREFIX, or deduction_postcutoff/runs if unset).",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Resolved after parse_args, so `--help` never has to run `spool_prefix()`.
    from smolbench.deduction.lean.runner import spool_prefix

    deduction_prefix = (args.spool_prefix or spool_prefix()) + "/"

    # Source and destination are the same bucket (a within-bucket server-side
    # copy), resolved here so a redirected SMOLBENCH_RESULTS_S3 isn't missed.
    bucket, _base_prefix = resolve_results_location()

    client = _s3()
    rows = iter_source_keys(client, bucket=bucket, deduction_prefix=deduction_prefix)
    per_model: Dict[Tuple[str, str], Dict[str, int]] = collections.defaultdict(
        lambda: {"objects": 0, "bytes": 0}
    )
    for leg, model, _key, size in rows:
        per_model[(leg, model)]["objects"] += 1
        per_model[(leg, model)]["bytes"] += size

    total_objects = len(rows)
    total_bytes = sum(r[3] for r in rows)
    logging.info(
        f"{total_objects} object(s), {total_bytes/1e9:.2f} GB across "
        f"{len({m for _l, m in per_model})} model(s), 2 legs -> s3://{bucket}/{args.dest}/"
    )
    for (leg, model), agg in sorted(per_model.items()):
        logging.info(f"  {leg:<10} {model:<30} {agg['objects']:>6} obj  {agg['bytes']/1e6:>9.1f} MB")

    if args.dry_run:
        logging.info("--dry-run: nothing written.")
        return 0

    # Two S3 round trips per copy (copy, then verify) is pure network wait, so
    # threads are the right tool for 55k objects.
    counts = collections.Counter()
    done = 0

    def _one(item):
        leg, model, key, size = item
        prefix = "induction/" if leg == "induction" else deduction_prefix
        tail = key[len(prefix):].split("/", 1)[1]
        return copy_one(client, bucket, key, f"{args.dest}/{leg}/{model}/{tail}", size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(_one, rows):
            counts[result] += 1
            done += 1
            if done % 5000 == 0:
                logging.info(f"  {done}/{total_objects} ... ({dict(counts)})")

    # Tracks keys actually written, not `PROVENANCE_DOCS` itself, so a doc
    # missing from disk is visible in MANIFEST.json instead of claimed present.
    provenance_keys: List[str] = []
    for doc in PROVENANCE_DOCS:
        path = REPO_ROOT / doc
        if path.exists():
            dest_key = f"{args.dest}/provenance/{path.name}"
            client.put_object(
                Bucket=bucket, Key=dest_key,
                Body=path.read_bytes(),
            )
            counts["provenance"] += 1
            provenance_keys.append(dest_key)

    # No `notes` field: every field here is computed from this run's walk.
    # Dataset-specific measured counts belong in SNAPSHOT_NOTES.md (copied via
    # PROVENANCE_DOCS above), not hardcoded here for every future snapshot.
    manifest = {
        "snapshot_prefix": args.dest,
        "source_bucket": bucket,
        "total_objects": total_objects,
        "total_bytes": total_bytes,
        "copied": counts["copied"],
        "skipped_already_present": counts["skipped"],
        "provenance_docs": counts["provenance"],
        "per_model": {f"{leg}/{model}": agg for (leg, model), agg in sorted(per_model.items())},
        "provenance_keys": provenance_keys,
    }
    client.put_object(
        Bucket=bucket, Key=f"{args.dest}/MANIFEST.json",
        Body=json.dumps(manifest, indent=2).encode(),
    )
    logging.info(f"done: {dict(counts)}; MANIFEST.json written to {args.dest}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
