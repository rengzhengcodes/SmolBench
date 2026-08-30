"""Publish an analysis-ready snapshot of the family-ladder study to S3.

Every byte already lives in S3, but in the layout the RUNNERS wanted
(``induction/<model>/seed=<s>/<arm>--<ts>.yaml`` versus
``<deduction-prefix>/scaling_<model>/...``, where ``<deduction-prefix>``
defaults to the re-collection's `runner.spool_prefix()` and is overridable via
``--spool-prefix`` -- the published pre-cutoff study lives at
``deduction/runs``), so a model's two legs sit under different names,
deduction a level deeper. Republished as analysis reads them:

    <dest>/induction/<model>/seed=<s>/<arm>--<ts>.yaml
    <dest>/deduction/<model>/verified_rows.jsonl    # the analysis input
    <dest>/deduction/<model>/all_rows.jsonl         # raw candidates, pre-verification
    <dest>/deduction/<model>/server_config.yaml     # hardware provenance
    <dest>/deduction/<model>/theorems/...           # prompts + per-theorem outputs
    <dest>/provenance/*.md                          # how to read the data
    <dest>/MANIFEST.json                            # what was copied, with byte counts

A SNAPSHOT, NOT A MOVE: no source object is ever modified or deleted (the study
bucket is an append-only experiment log); everything is written under ``--dest``.
Re-runs resume, skipping any destination object already present at a matching
size, and every copy's size is verified against its source before being counted.
Copies run SERVER-SIDE, so ~4.5 GB across ~55k objects never transits this host.

``*_SUPERSEDED-*``, ``*_STALE-*`` and ``*_BROKEN-*`` files are copied on purpose:
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

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

BUCKET = "smolbench-results-414266451290"
#: Prefixes that are not study data: smoke-test canaries and verifier scratch.
SKIP_SUBSTRINGS = ("canary", "/_verify/", "live_smoke")
#: Provenance documents copied alongside the data, so the snapshot explains
#: itself: README.md indexes the tree, ARCHIVE.md locates the archived docs.
PROVENANCE_DOCS = (
    "notebooks/README.md",
    "notebooks/ARCHIVE.md",
    "notebooks/deduction/README.md",
)


def _s3():
    import boto3

    return boto3.client("s3")


def iter_source_keys(
    client, *, deduction_prefix: Optional[str] = None
) -> List[Tuple[str, str, str, int]]:
    """Return ``(leg, model, source_key, size)`` per study object, minus `SKIP_SUBSTRINGS`.

    The deduction leg carries a ``scaling_`` prefix, stripped here so both legs
    of a model share one name.

    Parameters
    ----------
    deduction_prefix : str, optional
        S3 key prefix the deduction leg lives under, WITH a trailing "/".
        ``None`` (the default) resolves it lazily via `runner.spool_prefix()`
        -- a key prefix is CONFIGURATION, not audited logic, so importing the
        single source of truth for it here is not a hazard; `main` always
        resolves it once (also via a lazy import) and passes it down
        explicitly, so a caller reading the published pre-cutoff study passes
        ``"deduction/runs/"`` explicitly. This default only backstops a
        direct caller that omits it.
    """
    if deduction_prefix is None:
        from smolbench.deduction.lean.runner import spool_prefix

        deduction_prefix = spool_prefix() + "/"
    out: List[Tuple[str, str, str, int]] = []
    paginator = client.get_paginator("list_objects_v2")
    for prefix, leg in (("induction/", "induction"), (deduction_prefix, "deduction")):
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
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


def copy_one(client, src_key: str, dest_key: str, size: int) -> str:
    """Copy one object server-side within `BUCKET`, and verify its size.

    Parameters
    ----------
    size : int
        Expected source size in bytes: decides whether an already-present
        destination object can be skipped.

    Returns
    -------
    str
        ``"skipped"`` or ``"copied"``.

    Raises
    ------
    RuntimeError
        The copied object's size does not match `size`.
    """
    try:
        head = client.head_object(Bucket=BUCKET, Key=dest_key)
        if head["ContentLength"] == size:
            return "skipped"
    except Exception:  # noqa: BLE001 -- an absent destination is the normal case
        pass
    client.copy_object(
        Bucket=BUCKET, Key=dest_key,
        CopySource={"Bucket": BUCKET, "Key": src_key},
        # REPLACE, not the default COPY: the default reads the source's tags,
        # needing s3:GetObjectTagging, which the scoped operator key lacks.
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
    ap.add_argument("--workers", type=int, default=32,
                    help="concurrent copies; the work is pure network wait (default 32)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--spool-prefix", default=None,
        help="S3 key prefix the deduction leg spooled under (default: the "
             "re-collection prefix -- LEAN_SPOOL_PREFIX, or "
             "deduction_postcutoff/runs if unset). The published pre-cutoff "
             "study lives at deduction/runs; pass that explicitly to "
             "snapshot it (no env opt-in needed on this read-only path).",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Resolved AFTER parse_args, not at import or parser-build time -- a
    # module-level `spool_prefix()` call, or an eagerly-evaluated argparse
    # default, would make `LEAN_SPOOL_PREFIX=deduction/runs --help` explode.
    from smolbench.deduction.lean.runner import spool_prefix

    deduction_prefix = (args.spool_prefix or spool_prefix()) + "/"

    client = _s3()
    rows = iter_source_keys(client, deduction_prefix=deduction_prefix)
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

    # Each copy is two S3 round trips (copy, then verify), so 55k objects
    # serially would be ~5 hours of pure latency; the work is entirely network
    # wait, so threads are the right tool.
    counts = collections.Counter()
    done = 0

    def _one(item):
        leg, model, key, size = item
        prefix = "induction/" if leg == "induction" else deduction_prefix
        tail = key[len(prefix):].split("/", 1)[1]
        return copy_one(client, key, f"{args.dest}/{leg}/{model}/{tail}", size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(_one, rows):
            counts[result] += 1
            done += 1
            if done % 5000 == 0:
                logging.info(f"  {done}/{total_objects} ... ({dict(counts)})")

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
            "'replay_failed' means VERIFICATION could not be set up -- LeanDojo "
            "could not open the theorem, or the ground-truth prefix would not "
            "replay. It is the SAME 232 cells in every lane (151 DojoInit + 81 "
            "prefix), so no model was ever tested on them. Exclude, never score "
            "0: doing so deflates every marginal rate by up to 24.6%. The "
            "measurable denominator is 944 - 232 = 712 cells per lane.",
            "'incomplete' IS model-dependent (68/30/50 across three lanes) and "
            "stays in the denominator as a genuine failure.",
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
