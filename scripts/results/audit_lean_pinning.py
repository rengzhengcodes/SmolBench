"""Audit that all 21 deduction lanes ran the SAME pinned theorems.

Every cross-model claim of the family-ladder study (ladder contrasts, paired
McNemar, block bootstrap) assumes the lanes are paired, and nothing in the
pipeline enforces it. Five S3 checks run weakest to strongest, comparing
rendered prompts by S3 ETag rather than downloading them, so a mismatch is
still caught if it slips past an earlier check. A pass means the lanes were
ASKED the same questions, not that their surviving data is identical, and it
does not vouch for the corpus itself. Read-only, with ambient AWS
credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

from smolbench.evals.study_config import load_study_config, roster_keys

#: From the committed ``study_config.toml`` -- the same file the study writes
#: to, so this can't check the wrong bucket. Safe at module scope: pure file
#: I/O, no env vars, so it can't break ``--help`` the way an import-time
#: `spool_prefix()` call would.
_RESULTS = load_study_config().results
BUCKET = _RESULTS.bucket
REGION = _RESULTS.region
RECOVERY_RUN = "dojoinit_recovery_2026-08-18"

#: Flip-rate re-runs as ``(run_name, lane)``: own prefix, not folded into
#: headline pools, but still gated against the pin.
FLIP_RUNS = [("flip_nemotron-3-nano-4b", "nemotron-3-nano-4b"),
             ("flip2_nemotron-3-nano-4b", "nemotron-3-nano-4b")]

#: The 21 lane spec keys, read from the committed study config so the audit
#: and the audited lanes agree BY CONSTRUCTION, not via a hand-maintained
#: copy that could silently drop a lane the study actually ran.
LANES = list(roster_keys())

def slug_theorem(name: str) -> str:
    """Filesystem-safe theorem name; mirrors `runner.slug_theorem` exactly.

    Duplicated rather than imported, so this audit can't inherit a bug from
    the module it audits; a mismatch here misreports ~18 phantom out-of-set
    cells per lane. Kept in step by ``tests/deduction/test_lean_pinning_audit.py``.

    Parameters
    ----------
    name : str
        Theorem name to make filesystem-safe.

    Returns
    -------
    str
        Filesystem-safe theorem name.
    """
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


def _client() -> Any:
    import boto3

    return boto3.client("s3", region_name=REGION)


def _read(s3: Any, key: str) -> str:
    return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()


def _default_run_prefix() -> str:
    """Resolve the fetch_* helpers' ``run_prefix`` when a caller passes none.

    A key prefix is CONFIGURATION, not audited logic, so importing it here
    is not the duplication hazard `slug_theorem` guards against. Only
    backstops a direct caller (e.g. a test); `main()` resolves it once and
    passes it explicitly to every fetch_* call.
    """
    from smolbench.deduction.lean.runner import spool_prefix

    return spool_prefix()


def fetch_manifests(s3: Any, *, run_prefix: str | None = None) -> dict[str, dict]:
    """Per-lane as-run ``manifest.json`` (the config actually launched)."""
    run_prefix = run_prefix if run_prefix is not None else _default_run_prefix()
    return {k: json.loads(_read(s3, f"{run_prefix}/scaling_{k}/manifest.json")) for k in LANES}


def fetch_spool_index(
    s3: Any, *, run_prefix: str | None = None
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    """List each lane's output-cell keys and prompt ETags in one pass.

    Small single-part uploads make the ETag the object's MD5, so comparing
    ETags across lanes checks byte equality without downloading ~19 MB x 21
    of spool.

    Parameters
    ----------
    s3 : Any
        S3 client.
    run_prefix : str | None, optional
        Prefix for the audited run.

    Returns
    -------
    tuple[dict[str, set[str]], dict[str, dict[str, str]]]
        Per-lane output-cell keys and prompt ETags.
    """
    run_prefix = run_prefix if run_prefix is not None else _default_run_prefix()
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


def _is_missing_key(exc: Exception) -> bool:
    """True only for S3's "that object does not exist".

    Read off the error response, not ``s3.exceptions.NoSuchKey``, so a test
    double needs no botocore. Deliberately narrow: an expired credential or
    throttle must not read as "this lane recovered nothing", which would
    silently pass layer 5.

    Parameters
    ----------
    exc : Exception
        Exception returned by S3.

    Returns
    -------
    bool
        Whether the exception denotes a missing S3 object.
    """
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    code = str((response.get("Error") or {}).get("Code", ""))
    status = (response.get("ResponseMetadata") or {}).get("HTTPStatusCode")
    return code in {"NoSuchKey", "NotFound", "404"} or status == 404


def fetch_recovery(s3: Any, *, run_prefix: str | None = None) -> dict[str, set[str]]:
    """Cell keys touched by the additive dojoinit recovery, per lane.

    A lane with no recovery object contributes ``set()``; every other S3 error
    propagates (`_is_missing_key`).

    Parameters
    ----------
    s3 : Any
        S3 client.
    run_prefix : str | None, optional
        Prefix for the audited run.

    Returns
    -------
    dict[str, set[str]]
        Recovered cell keys by lane.
    """
    run_prefix = run_prefix if run_prefix is not None else _default_run_prefix()
    out: dict[str, set[str]] = {}
    for lane in LANES:
        key = f"{run_prefix}/{RECOVERY_RUN}/{lane}/recovered_rows.jsonl"
        try:
            body = _read(s3, key)
        except Exception as exc:  # noqa: BLE001 -- narrowed, and re-raised
            if not _is_missing_key(exc):
                raise
            out[lane] = set()
            continue
        out[lane] = {
            f"{slug_theorem(r['theorem_id'])}|{r['rung'].replace(':', '-')}"
            for r in (json.loads(x) for x in body.splitlines() if x.strip())
        }
    return out


def fetch_flip_cells(s3: Any, *, run_prefix: str | None = None) -> dict[str, set[str]]:
    """Cell keys reached by the flip-rate side-runs, per run name.

    These spool in the normal ``theorems/<slug>/outputs/`` layout, not the
    recovery run's flat ``recovered_rows.jsonl``.

    Parameters
    ----------
    s3 : Any
        S3 client.
    run_prefix : str | None, optional
        Prefix for the audited run.

    Returns
    -------
    dict[str, set[str]]
        Reached cell keys by flip-rate run.
    """
    run_prefix = run_prefix if run_prefix is not None else _default_run_prefix()
    out: dict[str, set[str]] = {}
    for run, _lane in FLIP_RUNS:
        pref = f"{run_prefix}/{run}/theorems/"
        cells: set[str] = set()
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=pref):
            for obj in page.get("Contents", []):
                parts = obj["Key"][len(pref):].split("/")
                if len(parts) == 3 and parts[1] == "outputs":
                    cells.add(f"{parts[0]}|{parts[2].split('__')[0]}")
        out[run] = cells
    return out


def divergent_prompt_cells(
    cell_keys: set[str], prompts: dict[str, dict[str, str]]
) -> set[str]:
    """Cells whose ``prompts/<rung>.md`` is not one shared ETag across `LANES`.

    A missing artifact contributes ``None``, which counts as divergent --
    otherwise a cell no lane spooled a prompt for would be certified
    byte-identical on absent evidence.

    Parameters
    ----------
    cell_keys : set[str]
        Cell keys to compare.
    prompts : dict[str, dict[str, str]]
        Prompt ETags by lane and cell key.

    Returns
    -------
    set[str]
        Cell keys with divergent prompt ETags.
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
    """Re-derive a pinned theorem set from its documented recipe.

    Mirrors `runner._select_theorems`: keep, in split order, the theorems
    whose ground-truth proof replays, then sample `limit` of them with
    ``random.Random(seed).sample`` only when ``0 < limit < len(pool)`` --
    otherwise the whole pool is kept unsampled. Split order is load-bearing,
    since ``rng.sample`` is order-sensitive.

    Parameters
    ----------
    val_json : Path
        Benchmark validation JSON file.
    replay_jsonl : Path
        Replay results JSONL file.
    limit : int
        Maximum number of passing theorems to sample.
    seed : int
        Random-sampling seed.

    Returns
    -------
    tuple[list[str], int]
        ``(names, pool_size)``, with ``pool_size`` measured before sampling.
    """
    val = json.loads(val_json.read_text())
    passing = {
        json.loads(line)["full_name"]
        for line in replay_jsonl.read_text().splitlines()
        if line.strip() and json.loads(line).get("verdict") == "success"
    }
    pool = [t for t in val if t["full_name"] in passing]
    pool_size = len(pool)
    selected = random.Random(seed).sample(pool, limit) if 0 < limit < pool_size else pool
    return [t["full_name"] for t in selected], pool_size


def main(argv: list[str] | None = None) -> int:
    """Run the configured S3 pinning audit and optional reproduction."""
    # Lazy import: a key prefix is CONFIGURATION, not audited logic, so this
    # doesn't reintroduce the duplication hazard `slug_theorem`/`LANES` guard against.
    from smolbench.deduction.lean import runner

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reproduce", action="store_true",
                    help="also re-derive the pin from corpus data (needs --val-json/--replay-jsonl)")
    ap.add_argument("--val-json", type=Path,
                    default=Path("notebooks/deduction/data/leandojo_benchmark_4/novel_premises/val.json"))
    ap.add_argument("--replay-jsonl", type=Path,
                    default=Path("notebooks/deduction/data/replay_passing_novel_premises_val.jsonl"))
    ap.add_argument(
        "--metadata", type=Path, default=None,
        help="corpus metadata.json to embed verbatim in the emitted manifest's "
             "'corpus' block (default: <val-json's split dir>/../metadata.json "
             "-- the corpus root is the split file's grandparent)",
    )
    ap.add_argument("--emit-manifest", type=Path, default=None,
                    help="write the reproduced pin to this path as pinned_theorems.json")
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
        help="skip the five S3 audit layers entirely -- no boto3 client is "
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
    # No inherited pinned shape: each mode makes the operator state its own.
    if not args.offline and (args.expect_theorems is None or args.expect_cells is None):
        ap.error("--expect-theorems and --expect-cells are required without --offline")
    if (args.reproduce or args.emit_manifest) and args.limit is None:
        ap.error("--limit is required with --reproduce/--emit-manifest")

    # Corpus root = split file's grandparent; resolved after parsing so an
    # explicit --metadata always wins.
    if args.metadata is None:
        args.metadata = args.val_json.parent.parent / "metadata.json"

    failures: list[str] = []
    inter: set[str] | None = None

    if args.offline:
        print("[offline] --offline set: skipping all five S3 audit layers "
              "(no boto3 client constructed, no AWS call made)")
    else:
        run_prefix = args.spool_prefix or runner.spool_prefix()
        s3 = _client()

        # -- Layer 1: as-run config --------------------------------------
        mans = fetch_manifests(s3, run_prefix=run_prefix)
        blocks = {k: json.dumps(m["config"]["theorems"], sort_keys=True) for k, m in mans.items()}
        seeds = {k: m["config"]["seed"] for k, m in mans.items()}
        if len(set(blocks.values())) != 1:
            failures.append(f"theorems blocks differ across lanes: {sorted(set(blocks.values()))}")
        if len(set(seeds.values())) != 1:
            failures.append(f"base seeds differ across lanes: {sorted(set(seeds.values()))}")
        print(f"[1/5] config      : {len(set(blocks.values()))} distinct theorems block, "
              f"{len(set(seeds.values()))} distinct seed  -> {next(iter(blocks.values()))}")

        # -- Layers 2-4: what actually landed in the spool ----------------
        cells, prompts = fetch_spool_index(s3, run_prefix=run_prefix)
        thm_sets = {k: {c.split("|")[0] for c in v} for k, v in cells.items()}
        inter, union = set.intersection(*thm_sets.values()), set.union(*thm_sets.values())
        if not (len(inter) == len(union) == args.expect_theorems):
            failures.append(f"theorem sets differ: intersection={len(inter)} union={len(union)}")
        print(f"[2/5] theorem sets: intersection={len(inter)} union={len(union)} "
              f"(expected {args.expect_theorems} == {args.expect_theorems})")

        cinter, cunion = set.intersection(*cells.values()), set.union(*cells.values())
        if not (len(cinter) == len(cunion) == args.expect_cells):
            failures.append(f"cell key sets differ: intersection={len(cinter)} union={len(cunion)}")
        print(f"[3/5] cell keys   : intersection={len(cinter)} union={len(cunion)} "
              f"(expected {args.expect_cells} == {args.expect_cells})")

        divergent = divergent_prompt_cells(cunion, prompts)
        if divergent:
            failures.append(f"{len(divergent)} cells have model-dependent or missing "
                            f"prompt bytes: {sorted(divergent)[:5]}")
        print(f"[4/5] prompt bytes: {len(cunion) - len(divergent)}/{len(cunion)} cells "
              f"byte-identical across all {len(LANES)} lanes")

        # -- Layer 5: side-runs stay inside the pinned set -----------------
        rec = fetch_recovery(s3, run_prefix=run_prefix)
        outside = {k: v - cells[k] for k, v in rec.items()}
        if any(outside.values()):
            failures.append(f"recovery rows outside the pinned cell set: "
                            f"{ {k: len(v) for k, v in outside.items() if v} }")
        flips = fetch_flip_cells(s3, run_prefix=run_prefix)
        flip_outside = {r: v - cells[lane] for (r, lane), v in
                        ((rl, flips[rl[0]]) for rl in FLIP_RUNS)}
        if any(flip_outside.values()):
            failures.append(f"flip-run cells outside the pinned cell set: "
                            f"{ {k: len(v) for k, v in flip_outside.items() if v} }")
        print(f"[5/5] side-runs   : recovery {sum(len(v) for v in rec.values())} cells "
              f"(additive), flip {sum(len(v) for v in flips.values())} cells "
              f"(not folded into headlines); "
              f"{sum(len(v) for v in outside.values()) + sum(len(v) for v in flip_outside.values())}"
              f" outside the pinned set")

    # -- Optional: rederive the pin from its documented recipe --------
    if args.reproduce or args.emit_manifest:
        names, pool_size = reproduce_pin(
            args.val_json, args.replay_jsonl, limit=args.limit, seed=args.seed)
        digest = hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()
        if args.offline:
            print("[+  ] reproduce   : --offline set, skipping the reproduced-pin-vs-"
                  f"spooled-set comparison (no spool to compare against); sha256={digest[:16]}")
        else:
            slugged = {slug_theorem(n) for n in names}
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
