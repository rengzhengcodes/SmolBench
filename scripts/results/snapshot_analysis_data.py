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
    <dest>/provenance/*.md                          # incl. SNAPSHOT_NOTES.md: how to read the rows
    <dest>/MANIFEST.json                            # purely computed -- byte counts, no prose notes

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

from smolbench.evals.results_store import resolve_results_location

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# NOTE: no bucket literal here. `main` resolves the bucket at call time via
# `resolve_results_location()` (the same seam `provision_results_bucket.py`
# and `audit_run_completeness.py` use), so a redirected `SMOLBENCH_RESULTS_S3`
# is honored instead of silently missing this script. `iter_source_keys` and
# `copy_one` each take `bucket` explicitly rather than reaching for a module
# global.
#: Prefixes that are not study data: smoke-test canaries and verifier scratch.
SKIP_SUBSTRINGS = ("canary", "/_verify/", "live_smoke")
#: Provenance documents copied alongside the data, so the snapshot explains
#: itself: README.md indexes the tree, ARCHIVE.md locates the archived docs,
#: and SNAPSHOT_NOTES.md documents how to READ the rows (verdict semantics,
#: the earliest-surviving-row rule, and this dataset's measured counts). That
#: last doc replaces the manifest's old `notes` field: it is a dated,
#: version-controlled document that gets copied next to the data, instead of
#: one dataset's measured counts being re-emitted as literal prose on every
#: run regardless of `--dest`/`--spool-prefix`.
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
    of a model share one name.

    Parameters
    ----------
    bucket : str
        Bucket to list, keyword-only alongside `deduction_prefix` so a caller
        cannot pass it positionally and mix it up with `client`. Read from a
        parameter, not a module constant, so `main`'s
        ``resolve_results_location()`` result (which may point at a
        redirected ``SMOLBENCH_RESULTS_S3`` bucket) is what actually gets
        listed.
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

    Parameters
    ----------
    bucket : str
        Bucket holding both `src_key` and `dest_key`. Positional, right after
        `client`: it mirrors the ``(Bucket, Key)`` argument order of every S3
        call it wraps below, and this function has exactly one call site
        (inside `main`), so there is no ambiguity to buy back with a keyword.
        This is a WITHIN-BUCKET copy -- source and destination are the SAME
        resolved bucket, which is why one resolved name serves both
        `CopySource` and the destination `Bucket`.
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

    # Resolved at call time, same as `runner.spool_prefix()` above: this is
    # the study bucket (via SMOLBENCH_RESULTS_S3, or the account default), and
    # source/destination are the SAME bucket -- a within-bucket server-side
    # copy -- so one resolved name threads through every call below instead of
    # a module-level literal that would silently miss a redirected bucket.
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

    # Each copy is two S3 round trips (copy, then verify), so 55k objects
    # serially would be ~5 hours of pure latency; the work is entirely network
    # wait, so threads are the right tool.
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

    # Track the provenance keys we actually WROTE, not `PROVENANCE_DOCS` itself:
    # the copy loop below already skips a doc that doesn't exist on disk, and
    # the manifest must agree with what was actually copied -- so a missing
    # doc is visible in MANIFEST.json rather than silently claimed as present.
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

    # NOTE: no `notes` field. Every other field here is computed from the
    # walk this run actually did; the previous `notes` list instead asserted
    # one specific dataset's measured multi-attempt-cell and
    # verification-failure counts verbatim for any `--dest`/`--spool-prefix`,
    # which is wrong for any snapshot other than the one they were measured
    # on. The reading rules -- both the parts that are invariant rules and the
    # parts that are that dataset's measured findings -- now live in a dated,
    # version-controlled document (`notebooks/deduction/analysis/
    # SNAPSHOT_NOTES.md`) that is copied next to the data via
    # `PROVENANCE_DOCS`/`provenance_keys` above, instead of being re-emitted
    # as literals here.
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
