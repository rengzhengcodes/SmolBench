"""Publish an analysis-ready family-ladder snapshot to S3.

Copy into ``<dest>/<leg>/<model>/...`` without modifying sources; matching-size
objects resume safely. Server-side copying keeps ~4.5 GB across ~55k objects
off this host. Include superseded, stale, and broken files as the repair audit trail.
Write ``<dest>/MANIFEST.json`` with computed counts only, no prose.
    scripts/results/snapshot_analysis_data.py [--dry-run] [--dest analysis/2026-08-16]
"""

import argparse
import collections
import concurrent.futures
import json
import logging
import pathlib
from typing import Any, Dict, List, Tuple

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


def _s3() -> Any:
    import boto3

    return boto3.client("s3")


def iter_source_keys(client: Any, *, bucket: str) -> List[Tuple[str, str, str, int]]:
    """Return ``(leg, model, source_key, size)`` per study object, minus `SKIP_SUBSTRINGS`.

    Strip deduction's ``scaling_`` prefix so both legs share a model name. Keep
    `bucket` parameterized for redirects and derive the prefix from `runner.spool_prefix()`.

    Parameters
    ----------
    client : Any
        S3 client.
    bucket : str
        Study-object bucket.

    Returns
    -------
    List[Tuple[str, str, str, int]]
        Leg, model, source key, and size tuples.
    """
    from smolbench.deduction.lean import runner

    deduction_prefix = runner.spool_prefix() + "/"
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


def copy_one(client: Any, bucket: str, src_key: str, dest_key: str, size: int) -> str:
    """Copy one object server-side within `bucket`, and verify its size.

    Skip an existing destination only when its size matches the source.

    Parameters
    ----------
    client : Any
        S3 client.
    bucket : str
        Source and destination bucket.
    src_key : str
        Source key.
    dest_key : str
        Destination key.
    size : int
        Expected source size.

    Returns
    -------
    str
        ``"skipped"`` or ``"copied"``.

    Raises
    ------
    RuntimeError
        Copied size differs from source.
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
    """Copy the analysis snapshot and write its computed manifest."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default="analysis/2026-08-16",
                    help="destination prefix inside the study bucket")
    ap.add_argument("--workers", type=int, default=32,
                    help="concurrent copies; the work is pure network wait (default 32)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Keep --help cheap: runner transitively imports lean3, corpus, context, and provider.
    from smolbench.deduction.lean import runner

    deduction_prefix = runner.spool_prefix() + "/"

    # Source and destination are the same bucket (a within-bucket server-side
    # copy), resolved here so a redirected SMOLBENCH_RESULTS_S3 isn't missed.
    bucket, _base_prefix = resolve_results_location()

    client = _s3()
    rows = iter_source_keys(client, bucket=bucket)
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

    def _one(item: Tuple[str, str, str, int]) -> str:
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
