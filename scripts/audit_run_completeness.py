"""Content-level completeness audit -- catches SILENT data faults.

WHY THIS EXISTS
---------------
On 2026-08-14 the deduction leg was found to be missing 2,564 of 19,824 cells
(12.9%), concentrated in five lanes, one of which had lost 93.8% of its data.
Nothing flagged it. Every check that existed passed:

  * the fleet driver reported the lane COMPLETE (it had run to the end);
  * the shard merge gates passed (944 cells + 300 sanity = 1,244 rows -- the
    KEYS were all present);
  * the verification pass reported 0 tracebacks and uploaded 22/22 files.

The rows were there. They were just EMPTY -- ``candidate_proof: ""``,
``completion_tokens: 0`` -- because the generating box died mid-run and the
driver recorded the failure as an ordinary per-cell ``exception`` row. The
loss only surfaced when someone asked why one lane's verified output was 90%
``exception``.

The lesson, and the rule this script enforces: **a completeness check that
counts rows is not a completeness check.** Presence of a key proves an
attempt was made, not that data came back. Assert on CONTENT.

WHAT COUNTS AS A FAULT
----------------------
A cell is DEAD when no row for its key carries a non-empty candidate_proof.
Dead cells split into two populations that must NOT be conflated:

  INFRA   some row carries an infrastructure error (spot interruption, idle
          watchdog, unreachable endpoint, connection/timeout). This is LOST
          DATA and is recoverable by re-running -- runner._existing_keys()
          excludes ``exception`` rows from the resume skip set, so a plain
          relaunch regenerates exactly these.

  GENUINE no error anywhere: the model was asked and returned nothing. This
          is DATA, not loss (962 such cells exist across the study, e.g. 272
          in gemma-4-12b). Regenerating them would fabricate results by
          resampling until the model happens to answer. Never "repair" these.

Exit status is 1 when INFRA loss exists, so this can gate a pipeline. Genuine
empties are reported but never fail the run.

USAGE
    scripts/audit_run_completeness.py                  # all lanes, from S3
    scripts/audit_run_completeness.py --lane gemma-4-31b
    scripts/audit_run_completeness.py --local          # audit local run dirs
    scripts/audit_run_completeness.py --induction      # seed coverage too
"""

import argparse
import collections
import json
import pathlib
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

BUCKET = "smolbench-results-414266451290"
DEDUCTION_PREFIX = "deduction/runs/"
INDUCTION_PREFIX = "induction/"

#: Expected per-lane cell count for this study (4 rungs x 236 theorem-slots).
EXPECTED_CELLS = 944
#: Expected induction seeds per (model, arm): base_seed=0, R=30.
EXPECTED_SEEDS = 30

#: Substrings that mark a row's failure as INFRASTRUCTURE rather than model
#: behaviour. Deliberately broad: a false "infra" costs one re-run, a false
#: "genuine" silently keeps a hole in the dataset.
INFRA_PATTERNS = re.compile(
    r"spot interruption|shutting-down|idle watchdog|unreachable|Connection|"
    r"Timeout|RemoteDisconnected|RuntimeError|ProtocolError|Max retries",
    re.IGNORECASE,
)

#: Lanes that are not study data.
NON_DATA_LANES = {"scaling_canary"}


def _s3():
    import boto3

    return boto3.client("s3")


def iter_deduction_lanes(local: bool) -> Iterable[Tuple[str, str]]:
    """Yields (lane_name, all_rows_text) for every deduction lane."""
    if local:
        runs = REPO_ROOT / "notebooks/deduction/results/runs"
        for d in sorted(p for p in runs.iterdir() if p.is_dir()):
            rows = d / "all_rows.jsonl"
            if rows.exists():
                yield d.name, rows.read_text(errors="replace")
        return
    s3 = _s3()
    pages = s3.get_paginator("list_objects_v2").paginate(
        Bucket=BUCKET, Prefix=DEDUCTION_PREFIX, Delimiter="/"
    )
    for page in pages:
        for p in page.get("CommonPrefixes", []):
            lane = p["Prefix"].split("/")[-2]
            try:
                body = s3.get_object(
                    Bucket=BUCKET, Key=f"{DEDUCTION_PREFIX}{lane}/all_rows.jsonl"
                )["Body"].read()
            except Exception:  # noqa: BLE001 -- a lane with no rows is itself a finding
                yield lane, ""
                continue
            yield lane, body.decode("utf-8", "replace")


def audit_lane(text: str) -> Dict[str, object]:
    """Classifies one lane's cells into ok / infra-dead / genuine-empty."""
    rows_by_key: Dict[tuple, List[dict]] = collections.defaultdict(list)
    sanity: Dict[str, bool] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("kind") == "cell":
            key = (r.get("theorem_id"), r.get("rung"), r.get("k"), r.get("replicate_idx"))
            rows_by_key[key].append(r)
        elif r.get("kind") == "sanity":
            sanity[r.get("theorem_id")] = sanity.get(r.get("theorem_id"), False) or bool(
                r.get("verdict")
            )
    infra: List[tuple] = []
    genuine: List[tuple] = []
    for key, rows in rows_by_key.items():
        if any((r.get("candidate_proof") or "").strip() for r in rows):
            continue
        blob = " ".join(str(r.get("lean_error") or "") for r in rows)
        (infra if INFRA_PATTERNS.search(blob) else genuine).append(key)
    return {
        "cells": len(rows_by_key),
        "infra": len(infra),
        "genuine": len(genuine),
        "sanity_missing": sum(1 for v in sanity.values() if not v),
    }


def audit_induction(models: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
    """Reports induction (model, arm) pairs missing seeds.

    The induction analogue of an empty cell is a MISSING seed: the arm file is
    written only when a seed completes, so a lane that died mid-seed leaves no
    trace at all in S3 -- silent in a different way than deduction's empty rows.
    """
    s3 = _s3()
    seen: Dict[Tuple[str, str], set] = collections.defaultdict(set)
    pages = s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=INDUCTION_PREFIX)
    for page in pages:
        for o in page.get("Contents", []):
            m = re.match(
                rf"{INDUCTION_PREFIX}([^/]+)/seed=(\d+)/([a-z_]+)--", o["Key"]
            )
            if m:
                seen[(m.group(1), m.group(3))].add(int(m.group(2)))
    out: Dict[str, Dict[str, int]] = {}
    for (model, arm), seeds in sorted(seen.items()):
        if models and model not in models:
            continue
        missing = EXPECTED_SEEDS - len(seeds)
        if missing:
            out.setdefault(model, {})[arm] = missing
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lane", default="", help="Audit one lane (substring match).")
    ap.add_argument("--local", action="store_true", help="Audit local run dirs, not S3.")
    ap.add_argument("--induction", action="store_true", help="Also audit induction seed coverage.")
    ap.add_argument(
        "--expect-cells", type=int, default=EXPECTED_CELLS,
        help=f"Cells expected per lane (default {EXPECTED_CELLS}).",
    )
    args = ap.parse_args()

    print(f"{'lane':38s} {'cells':>6s} {'INFRA':>6s} {'genuine':>8s} {'status':>8s}")
    total_infra = total_genuine = 0
    failures: List[str] = []
    for lane, text in iter_deduction_lanes(args.local):
        if lane in NON_DATA_LANES or (args.lane and args.lane not in lane):
            continue
        a = audit_lane(text)
        short = a["cells"] < args.expect_cells
        bad = a["infra"] or short or a["sanity_missing"]
        status = "FAULT" if bad else "ok"
        if bad:
            failures.append(
                f"{lane}: {a['infra']} cells lost to infrastructure"
                + (f", {args.expect_cells - a['cells']} cell keys absent" if short else "")
                + (f", {a['sanity_missing']} sanity rows missing" if a["sanity_missing"] else "")
            )
        total_infra += int(a["infra"])
        total_genuine += int(a["genuine"])
        print(f"{lane:38s} {a['cells']:6d} {a['infra']:6d} {a['genuine']:8d} {status:>8s}")

    print(
        f"\nTOTAL: {total_infra} cell(s) lost to infrastructure, "
        f"{total_genuine} genuine empty completion(s) (DATA -- do not regenerate)"
    )

    if args.induction:
        gaps = audit_induction()
        print("\nINDUCTION seed coverage:")
        if gaps:
            for model, arms in gaps.items():
                worst = max(arms.values())
                failures.append(f"{model}: induction missing up to {worst} seed(s) {arms}")
                print(f"  FAULT {model}: missing seeds per arm -> {arms}")
        else:
            print(f"  ok: every (model, arm) has all {EXPECTED_SEEDS} seeds")

    if failures:
        print("\n*** COMPLETENESS FAULTS ***")
        for f in failures:
            print(f"  - {f}")
        print(
            "\nInfrastructure loss is RECOVERABLE: relaunch the lane. Dead cells carry\n"
            "verdict 'exception', which runner._existing_keys() excludes from the resume\n"
            "skip set, so only they regenerate. Genuine empty completions are DATA and\n"
            "must never be regenerated."
        )
        return 1
    print("\nAll audited lanes complete at the CONTENT level.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
