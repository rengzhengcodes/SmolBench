"""Publish an analysis-ready snapshot of the family-ladder study to S3.

WHY THIS EXISTS
---------------
Every byte of this study already lives in S3 -- nothing is only on the operating
host. But it lives in the layout the RUNNERS wanted, which is not the layout an
analyst wants:

    induction/<model>/seed=<s>/<arm>--<ts>.yaml     # keyed by model already
    deduction/runs/scaling_<model>/...              # 'runs/', and a 'scaling_' prefix

so the two legs of the same model do not sit under a common name, and the
deduction leg is buried a level deeper. This publishes a snapshot keyed the way
analysis reads it -- leg, then model:

    <dest>/induction/<model>/seed=<s>/<arm>--<ts>.yaml
    <dest>/deduction/<model>/verified_rows.jsonl    # the analysis input
    <dest>/deduction/<model>/all_rows.jsonl         # raw candidates, pre-verification
    <dest>/deduction/<model>/server_config.yaml     # hardware provenance
    <dest>/deduction/<model>/theorems/...           # prompts + per-theorem outputs
    <dest>/provenance/*.md                          # how to read the data
    <dest>/MANIFEST.json                            # what was copied, with byte counts

A SNAPSHOT, NOT A MOVE
----------------------
Sources are never modified or deleted. The study bucket is an append-only
experiment log and stays exactly as it is; this only ever writes under `--dest`.
Re-running is safe: an object already present at the destination with a matching
size is skipped, so an interrupted run resumes.

Copies are SERVER-SIDE (`copy_object` with ``TaggingDirective="REPLACE"`` --
the plain default needs ``s3:GetObjectTagging``, which the scoped operator key
deliberately lacks), so ~4.5 GB across ~55k objects never transits the host.
Every copy is size-verified against its source before being counted.

SUPERSEDED FILES ARE INCLUDED ON PURPOSE
----------------------------------------
Files named ``*_SUPERSEDED-*``, ``*_STALE-*`` and ``*_BROKEN-*`` are copied too.
They are the audit trail for the 2026-08-15/16 repairs: the mixed-hardware rows
that nemotron-3-nano-4b's re-run replaced, and the verification output that
predates six lanes being regenerated. An analyst who wants to check what changed
needs them; their names say plainly that they are not the current data.

USAGE
    scripts/snapshot_analysis_data.py --dry-run
    scripts/snapshot_analysis_data.py --dest analysis/2026-08-16
"""

import argparse
import collections
import json
import logging
import pathlib
import sys
from typing import Dict, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

BUCKET = "smolbench-results-414266451290"
#: Prefixes that are not study data: smoke-test canaries and verifier scratch.
SKIP_SUBSTRINGS = ("canary", "/_verify/", "live_smoke")
#: Provenance documents copied alongside the data so the snapshot explains itself.
PROVENANCE_DOCS = (
    "notebooks/CONTAMINATION_INVENTORY_2026-08-15.md",
    "notebooks/induction/CONFOUND_AUDIT_2026-08-13.md",
    "notebooks/deduction/README.md",
)


def _s3():
    import boto3

    return boto3.client("s3")


def iter_source_keys(client) -> List[Tuple[str, str, str, int]]:
    """Returns [(leg, model, source_key, size)] for every study object.

    The two legs are keyed differently at the source, so the model name is
    recovered differently for each -- that asymmetry is the whole reason this
    script exists.
    """
    out: List[Tuple[str, str, str, int]] = []
    paginator = client.get_paginator("list_objects_v2")
    for prefix, leg in (("induction/", "induction"), ("deduction/runs/", "deduction")):
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if any(s in key for s in SKIP_SUBSTRINGS):
                    continue
                rest = key[len(prefix):]
                model = rest.split("/", 1)[0]
                if leg == "deduction":
                    # 'scaling_qwen3.5-27b' -> 'qwen3.5-27b', so both legs of one
                    # model land under the same directory name.
                    model = model[len("scaling_"):] if model.startswith("scaling_") else model
                if "/" not in rest:
                    continue  # a stray object directly under the prefix
                tail = rest.split("/", 1)[1]
                out.append((leg, model, key, obj["Size"]))
    return out


def copy_one(client, src_key: str, dest_key: str, size: int) -> str:
    """Server-side copy with size verification. Returns 'copied'|'skipped'."""
    try:
        head = client.head_object(Bucket=BUCKET, Key=dest_key)
        if head["ContentLength"] == size:
            return "skipped"
    except Exception:  # noqa: BLE001 -- absent destination is the normal case
        pass
    client.copy_object(
        Bucket=BUCKET, Key=dest_key,
        CopySource={"Bucket": BUCKET, "Key": src_key},
        # REPLACE, not the default COPY: the default reads the source's tags and
        # so requires s3:GetObjectTagging, which the operator key does not have.
        TaggingDirective="REPLACE",
    )
    got = client.head_object(Bucket=BUCKET, Key=dest_key)["ContentLength"]
    if got != size:
        raise RuntimeError(f"size mismatch copying {src_key}: {got} != {size}")
    return "copied"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default="analysis/2026-08-16",
                    help="destination prefix inside the study bucket")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    client = _s3()
    rows = iter_source_keys(client)
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
        f"{len({m for _l, m in per_model})} model(s), 2 legs -> s3://{BUCKET}/{args.dest}/"
    )
    for (leg, model), agg in sorted(per_model.items()):
        logging.info(f"  {leg:<10} {model:<30} {agg['objects']:>6} obj  {agg['bytes']/1e6:>9.1f} MB")

    if args.dry_run:
        logging.info("--dry-run: nothing written.")
        return 0

    counts = collections.Counter()
    for i, (leg, model, key, size) in enumerate(rows, 1):
        prefix = "induction/" if leg == "induction" else "deduction/runs/"
        tail = key[len(prefix):].split("/", 1)[1]
        dest_key = f"{args.dest}/{leg}/{model}/{tail}"
        counts[copy_one(client, key, dest_key, size)] += 1
        if i % 2000 == 0:
            logging.info(f"  {i}/{total_objects} ... ({dict(counts)})")

    for doc in PROVENANCE_DOCS:
        path = REPO_ROOT / doc
        if path.exists():
            client.put_object(
                Bucket=BUCKET, Key=f"{args.dest}/provenance/{path.name}",
                Body=path.read_bytes(),
            )
            counts["provenance"] += 1

    manifest = {
        "snapshot_prefix": args.dest,
        "source_bucket": BUCKET,
        "total_objects": total_objects,
        "total_bytes": total_bytes,
        "copied": counts["copied"],
        "skipped_already_present": counts["skipped"],
        "provenance_docs": counts["provenance"],
        "per_model": {f"{leg}/{model}": agg for (leg, model), agg in sorted(per_model.items())},
        "notes": [
            "Snapshot of an append-only experiment log; sources unmodified.",
            "deduction/<model>/verified_rows.jsonl is the ANALYSIS INPUT; "
            "all_rows.jsonl is pre-verification candidates.",
            "Take the EARLIEST SURVIVING (non-exception) row per cell: 74 cells "
            "across 3 lanes hold more than one surviving attempt, and last-wins "
            "inflates ministral-3-3b by 5.9 points.",
            "'exception' verdicts mean the attempt never reached the model "
            "(infrastructure), not a model failure -- exclude, never score 0.",
            "*_SUPERSEDED-*/*_STALE-*/*_BROKEN-* are the repair audit trail, not current data.",
        ],
    }
    client.put_object(
        Bucket=BUCKET, Key=f"{args.dest}/MANIFEST.json",
        Body=json.dumps(manifest, indent=2).encode(),
    )
    logging.info(f"done: {dict(counts)}; MANIFEST.json written to {args.dest}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
