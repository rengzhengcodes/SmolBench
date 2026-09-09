"""Audit that all 21 deduction lanes used the same pinned theorems.

Paired cross-model claims require identical prompts; ETags avoid downloading spool data.
A pass checks asked questions, not surviving data or corpus validity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

from smolbench.evals._aws import fresh_client
from smolbench.evals.spool import spool_prefix
from smolbench.evals.study_config import load_study_config, roster_keys

#: Committed config prevents auditing the wrong bucket; pure I/O keeps `--help` safe.
_RESULTS = load_study_config().results
BUCKET = _RESULTS.bucket
REGION = _RESULTS.region
#: Read lane keys from config so a maintained copy cannot silently omit a lane.
LANES = list(roster_keys())

def _read(s3: Any, key: str) -> str:
    return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()


def fetch_manifests(s3: Any, *, run_prefix: str) -> dict[str, dict]:
    """Per-lane as-run ``manifest.json`` (the config actually launched)."""
    return {k: json.loads(_read(s3, f"{run_prefix}/scaling_{k}/manifest.json")) for k in LANES}


def fetch_spool_index(
    s3: Any, *, run_prefix: str
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    """List lane output keys and prompt ETags; ETags avoid downloading ~19 MB × 21.

    Parameters
    ----------
    s3 : Any
        S3 client.
    run_prefix : str
        Audited run prefix.

    Returns
    -------
    tuple[dict[str, set[str]], dict[str, dict[str, str]]]
        Output keys and prompt ETags by lane.
    """
    cells: dict[str, set[str]] = {}
    prompts: dict[str, dict[str, str]] = {}
    for lane in LANES:
        pref = f"{run_prefix}/scaling_{lane}/theorems/"
        c: set[str] = set()
        p: dict[str, str] = {}
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=pref):
            for obj in page.get("Contents", []):
                parts = obj["Key"][len(pref):].split("/")
                if len(parts) != 3:
                    continue
                thm, kind, leaf = parts
                if kind == "outputs":
                    c.add(f"{thm}|{leaf.split('__')[0]}")
                elif kind == "prompts" and leaf.endswith(".md"):
                    p[f"{thm}|{leaf[:-3]}"] = obj["ETag"].strip('"')
        cells[lane], prompts[lane] = c, p
    return cells, prompts


def divergent_prompt_cells(
    cell_keys: set[str], prompts: dict[str, dict[str, str]]
) -> set[str]:
    """Return cells without one shared prompt ETag; missing artifacts diverge.

    Parameters
    ----------
    cell_keys : set[str]
        Cell keys.
    prompts : dict[str, dict[str, str]]
        Prompt ETags by lane and cell.

    Returns
    -------
    set[str]
        Cells with divergent ETags.
    """
    out: set[str] = set()
    for key in cell_keys:
        etags = {prompts.get(lane, {}).get(key) for lane in LANES}
        if len(etags) != 1 or None in etags:
            out.add(key)
    return out


def reproduce_pin(
    val_json: Path, replay_jsonl: Path, *, limit: int, seed: int
) -> tuple[list[str], int]:
    """Re-derive a pin in split order because seeded sampling is order-sensitive.

    Parameters
    ----------
    val_json : Path
        Validation JSON.
    replay_jsonl : Path
        Replay JSONL.
    limit : int
        Maximum passing theorems.
    seed : int
        Sampling seed.

    Returns
    -------
    tuple[list[str], int]
        Names and pre-sampling pool size.
    """
    val = json.loads(val_json.read_text())
    rows = (json.loads(line) for line in replay_jsonl.read_text().splitlines() if line.strip())
    passing = {row["full_name"] for row in rows if row.get("verdict") == "success"}
    pool = [t for t in val if t["full_name"] in passing]
    pool_size = len(pool)
    selected = random.Random(seed).sample(pool, limit) if 0 < limit < pool_size else pool
    return [t["full_name"] for t in selected], pool_size


def main(argv: list[str] | None = None) -> int:
    """Run the configured S3 pinning audit and optional reproduction."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reproduce", action="store_true",
                    help="also re-derive the pin from corpus data (needs --val-json/--replay-jsonl)")
    ap.add_argument("--val-json", type=Path, default=None)
    ap.add_argument("--replay-jsonl", type=Path, default=None)
    ap.add_argument(
        "--metadata", type=Path, default=None,
        help="corpus metadata.json to embed verbatim in the emitted manifest's "
             "'corpus' block (default: <val-json's split dir>/../metadata.json "
             "-- the corpus root is the split file's grandparent)",
    )
    ap.add_argument("--emit-manifest", type=Path, default=None,
                    help="write the reproduced pin JSON to this path")
    ap.add_argument(
        "--limit", type=int, default=None,
        help="theorems to sample (required with --reproduce/--emit-manifest)",
    )
    ap.add_argument(
        "--seed", type=int, default=0,
        help="random.Random seed for --reproduce/--emit-manifest's sample (default: %(default)s)",
    )
    ap.add_argument(
        "--offline", action="store_true",
        help="skip the four S3 audit layers entirely -- no boto3 client is "
             "constructed and no AWS call is made. Only meaningful with "
             "--emit-manifest/--reproduce, which then also skip the "
             "'reproduced pin == spooled set' comparison (there is no spool "
             "to compare against).",
    )
    ap.add_argument(
        "--expect-theorems", type=int, default=None,
        help="expected theorem-set size for layer [2/5] (required without --offline)",
    )
    ap.add_argument(
        "--expect-cells", type=int, default=None,
        help="expected cell-set size for layer [3/5] (required without --offline)",
    )
    ap.add_argument(
        "--spool-prefix", default=None,
        help="S3 key prefix the 21 lanes spooled under (default: the re-collection "
             "prefix -- LEAN_SPOOL_PREFIX, or deduction_postcutoff/runs if unset).",
    )
    args = ap.parse_args(argv)
    # Require each mode's expected shape; inherited values could audit the wrong run.
    if not args.offline and (args.expect_theorems is None or args.expect_cells is None):
        ap.error("--expect-theorems and --expect-cells are required without --offline")
    if (args.reproduce or args.emit_manifest) and args.limit is None:
        ap.error("--limit is required with --reproduce/--emit-manifest")
    if (args.reproduce or args.emit_manifest) and (
        args.val_json is None or args.replay_jsonl is None
    ):
        ap.error("--val-json and --replay-jsonl are required with --reproduce/--emit-manifest")

    # Resolve after parsing so explicit `--metadata` wins.
    if args.metadata is None and args.val_json is not None:
        args.metadata = args.val_json.parent.parent / "metadata.json"

    failures: list[str] = []
    inter: set[str] | None = None

    if args.offline:
        print("[offline] --offline set: skipping all four S3 audit layers "
              "(no boto3 client constructed, no AWS call made)")
    else:
        run_prefix = args.spool_prefix or spool_prefix()
        s3 = fresh_client("s3", REGION)

        # As-run config.
        mans = fetch_manifests(s3, run_prefix=run_prefix)
        blocks = {k: json.dumps(m["config"]["theorems"], sort_keys=True) for k, m in mans.items()}
        seeds = {k: m["config"]["seed"] for k, m in mans.items()}
        if len(set(blocks.values())) != 1:
            failures.append(f"theorems blocks differ across lanes: {sorted(set(blocks.values()))}")
        if len(set(seeds.values())) != 1:
            failures.append(f"base seeds differ across lanes: {sorted(set(seeds.values()))}")
        print(f"[1/4] config      : {len(set(blocks.values()))} distinct theorems block, "
              f"{len(set(seeds.values()))} distinct seed  -> {next(iter(blocks.values()))}")

        # What landed in the spool.
        cells, prompts = fetch_spool_index(s3, run_prefix=run_prefix)
        thm_sets = {k: {c.split("|")[0] for c in v} for k, v in cells.items()}
        inter, union = set.intersection(*thm_sets.values()), set.union(*thm_sets.values())
        if not (len(inter) == len(union) == args.expect_theorems):
            failures.append(f"theorem sets differ: intersection={len(inter)} union={len(union)}")
        print(f"[2/4] theorem sets: intersection={len(inter)} union={len(union)} "
              f"(expected {args.expect_theorems} == {args.expect_theorems})")

        cinter, cunion = set.intersection(*cells.values()), set.union(*cells.values())
        if not (len(cinter) == len(cunion) == args.expect_cells):
            failures.append(f"cell key sets differ: intersection={len(cinter)} union={len(cunion)}")
        print(f"[3/4] cell keys   : intersection={len(cinter)} union={len(cunion)} "
              f"(expected {args.expect_cells} == {args.expect_cells})")

        divergent = divergent_prompt_cells(cunion, prompts)
        if divergent:
            failures.append(f"{len(divergent)} cells have model-dependent or missing "
                            f"prompt bytes: {sorted(divergent)[:5]}")
        print(f"[4/4] prompt bytes: {len(cunion) - len(divergent)}/{len(cunion)} cells "
              f"byte-identical across all {len(LANES)} lanes")

    # Optional pin reproduction.
    if args.reproduce or args.emit_manifest:
        names, pool_size = reproduce_pin(
            args.val_json, args.replay_jsonl, limit=args.limit, seed=args.seed)
        digest = hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()
        if args.offline:
            print("[+  ] reproduce   : --offline set, skipping the reproduced-pin-vs-"
                  f"spooled-set comparison (no spool to compare against); sha256={digest[:16]}")
        else:
            # Use the production slug to compare like-for-like artifacts.
            from smolbench.deduction.lean import runner

            slugged = {runner.slug_theorem(n) for n in names}
            if slugged != inter:
                failures.append(f"reproduced pin != spooled set "
                                f"(missing {len(inter - slugged)}, extra {len(slugged - inter)})")
            print(f"[+  ] reproduce   : seeded sample matches spool={slugged == inter} sha256={digest[:16]}")
        if args.emit_manifest:
            kind, split = args.val_json.parent.name, args.val_json.stem
            sampled = 0 < args.limit < pool_size
            recipe = (
                f"random.Random({args.seed}).sample(list(corpus.iter_replay_passing"
                f"({kind!r},{split!r})), {args.limit})"
                if sampled else
                f"list(corpus.iter_replay_passing({kind!r},{split!r}))"
                f"  # limit={args.limit} did not shrink the {pool_size}-theorem pool"
            )
            corpus = json.loads(args.metadata.read_text())
            args.emit_manifest.write_text(json.dumps({
                "_comment": (
                    "Pinned theorem set for a deduction study lane. Every lane sharing "
                    "this manifest was evaluated on exactly these theorems. Generated "
                    "by scripts/results/audit_lean_pinning.py --emit-manifest; "
                    "re-derive with the same --val-json/--replay-jsonl/--limit/--seed "
                    "(and, online, verify against the as-run S3 spool via --reproduce)."
                ),
                "corpus": corpus,
                "derivation": {
                    "source": "replay_passing",
                    "kind": kind,
                    "split": split,
                    "pool_size": pool_size,
                    "limit": args.limit,
                    "seed": args.seed,
                    "recipe": recipe,
                },
                "sha256_of_sorted_full_names": digest,
                "count": len(names),
                "full_names": sorted(names),
            }, indent=2))
            print(f"        wrote {args.emit_manifest}")

    print()
    if failures:
        print("PINNING AUDIT FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    if args.offline:
        print("OFFLINE RUN: S3 audit layers were skipped (--offline); "
              "only --reproduce/--emit-manifest ran, if requested.")
    else:
        print(f"PINNING AUDIT PASSED: all {len(LANES)} lanes ran the identical "
              f"{args.expect_theorems} theorems / {args.expect_cells} cells, byte-identical prompts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
