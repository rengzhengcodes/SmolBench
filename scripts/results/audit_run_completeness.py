"""Audit content-level run completeness. Catches SILENT data faults.

A completeness check that counts rows is not a completeness check: a row can be
present and EMPTY (``candidate_proof: ""``, ``completion_tokens: 0``) when the
generating box died mid-run and the driver recorded the failure as an ordinary
per-cell ``exception`` row. Row counts, shard-merge gates and traceback counts
all pass on that data. Assert on CONTENT.

A cell is DEAD when no row for its key carries a non-empty candidate_proof. Dead
cells split into two populations that must never be conflated:

  INFRA   No attempt reached the model (no surviving row with prompt_tokens > 0)
          and some row carries an infrastructure error. This is LOST DATA, and
          exactly the set ``runner._existing_keys()`` re-runs, so a plain
          relaunch regenerates these cells and nothing else.

  GENUINE No error anywhere: the model was asked and returned nothing. This is
          DATA, not loss. Regenerating it resamples until the model happens to
          answer, which inflates the numerator. Never "repair" these cells.

Exits 1 on INFRA loss (also on short lanes, missing sanity rows, or a selection
that matched no lane) so a pipeline can gate on it. Genuine empties are reported
but never fail the run.

    scripts/results/audit_run_completeness.py [--lane L] [--local] [--induction]

    # Programmatic, per lane:
    #   sys.path.insert(0, "scripts/results"); from audit_run_completeness import audit_lane
    #   audit_lane(open(f"{run_dir}/all_rows.jsonl").read())["infra"]  # dead cells
"""

import argparse
import collections
import json
import pathlib
import re
from typing import Dict, Iterable, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

BUCKET = "smolbench-results-414266451290"
DEDUCTION_PREFIX = "deduction/runs/"
INDUCTION_PREFIX = "induction/"

#: Expected per-lane cell count for this study (4 rungs x 236 theorem-slots).
EXPECTED_CELLS = 944
#: Expected induction seeds per (model, arm): base_seed=0, R=30.
EXPECTED_SEEDS = 30

#: Substrings that mark a row's failure as INFRASTRUCTURE, not model
#: behavior. This pattern is deliberately broad. A false "infra" costs one
#: re-run; a false "genuine" silently keeps a hole in the dataset.
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
    """Yield ``(lane_name, all_rows_text)`` for every deduction lane.

    Reads local run directories when `local`, otherwise each lane's
    ``all_rows.jsonl`` from S3. The text is ``""`` when S3 holds no such object
    for a lane, which is itself a finding.
    """
    if local:
        runs = REPO_ROOT / "notebooks/deduction/results/runs"
        # Skip symlinks: the driver keeps a `latest -> scaling_<key>`
        # pointer, and following it double-counts that lane in the totals.
        for d in sorted(p for p in runs.iterdir() if p.is_dir() and not p.is_symlink()):
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
    """Classify one lane's cells into ok, infra-dead, or genuine-empty.

    `text` is the raw ``all_rows.jsonl`` yielded by `iter_deduction_lanes`.
    Returns counts keyed ``cells`` (distinct cell keys), ``infra`` (dead cells
    lost to infrastructure), ``genuine`` (dead cells the model answered emptily)
    and ``sanity_missing`` (sanity theorems with no passing verdict in any row).
    """
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
        # A cell is INFRA loss only if NO attempt ever reached the model.
        # `prompt_tokens > 0` means the server counted a prompt, so the
        # model WAS asked, and the empty result is its answer: data, not
        # loss.
        reached_model = any(int(r.get("prompt_tokens") or 0) > 0 for r in rows)
        blob = " ".join(str(r.get("lean_error") or "") for r in rows)
        if not reached_model and INFRA_PATTERNS.search(blob):
            infra.append(key)
        else:
            genuine.append(key)
    return {
        "cells": len(rows_by_key),
        "infra": len(infra),
        "genuine": len(genuine),
        "sanity_missing": sum(1 for v in sanity.values() if not v),
    }


def audit_induction(models: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
    """Report induction ``(model, arm)`` pairs missing seeds, as ``{model: {arm: n}}``.

    The induction analogue of an empty cell is a MISSING seed: the arm file is
    written only when a seed completes, so a lane that died mid-seed leaves no
    trace at all in S3. Only models with at least one gap are returned; `models`
    restricts the report, and ``None`` covers every model found in S3.
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
    audited = 0
    failures: List[str] = []
    for lane, text in iter_deduction_lanes(args.local):
        if lane in NON_DATA_LANES or (args.lane and args.lane not in lane):
            continue
        audited += 1
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

    if not audited:
        # An audit that examined NOTHING must never report success. That
        # would be the exact failure this script exists to catch, turned
        # on itself.
        where = "local run dirs" if args.local else "S3"
        print(
            f"\n*** AUDITED NOTHING: no lane in {where} matched "
            f"{args.lane!r} ***" if args.lane else
            f"\n*** AUDITED NOTHING: no lanes found in {where} ***"
        )
        print("An empty selection is not a pass. Check the name, or drop --local.")
        return 1

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
            "\nInfrastructure loss is RECOVERABLE: relaunch the lane. INFRA here means NO\n"
            "attempt ever reached the model (no surviving row with prompt_tokens > 0), which\n"
            "is exactly the set runner._existing_keys() re-runs. A cell the model answered --\n"
            "even emptily -- is DATA and is never re-run: generation is not deterministic\n"
            "across server processes, so retrying an empty answer until a proof appears is\n"
            "resampling, and it inflates the numerator. Re-audit after the relaunch: the\n"
            "driver printing 'DEDUCTION LANE COMPLETE' is not evidence, this exit status is."
        )
        return 1
    print("\nAll audited lanes complete at the CONTENT level.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
