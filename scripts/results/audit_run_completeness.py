"""Audit content-level run completeness.

INFRA empty cells are lost data; genuine empty answers are retained to avoid
inflating results by resampling and do not fail the run. Exits 1 for loss,
short lanes, missing sanity, or empty selection.
"""

import argparse
import collections
import functools
import importlib.util
import json
import os
import pathlib
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

from smolbench.evals.results_store import S3ResultsStore, resolve_results_location

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Induction study ``S3ResultsStore.experiment`` segment.
INDUCTION_EXPERIMENT = "induction"

#: Deliberately broad: a false "genuine" silently keeps a hole in the dataset.
INFRA_PATTERNS = re.compile(
    r"spot interruption|shutting-down|idle watchdog|unreachable|Connection|"
    r"Timeout|RemoteDisconnected|RuntimeError|ProtocolError|Max retries",
    re.IGNORECASE,
)

NON_DATA_LANES = {"scaling_canary"}


def _s3() -> Any:
    import boto3

    return boto3.client("s3")


def iter_deduction_lanes(local: bool) -> Iterable[Tuple[str, str]]:
    """Yield ``(lane_name, all_rows_text)`` for every deduction lane.

    Missing S3 rows yield ``""`` so a missing lane remains a finding.

    Parameters
    ----------
    local : bool
        Read local run directories.

    Yields
    ------
    Tuple[str, str]
        Lane name and rows text.
    """
    if local:
        runs = REPO_ROOT / "notebooks/deduction/results/runs"
        # Skip `latest` symlink to avoid double-counting its lane.
        for d in sorted(p for p in runs.iterdir() if p.is_dir() and not p.is_symlink()):
            rows = d / "all_rows.jsonl"
            if rows.exists():
                yield d.name, rows.read_text(errors="replace")
        return
    from smolbench.deduction.lean import runner

    deduction_prefix = runner.spool_prefix() + "/"
    # Deduction uses its own spool prefix.
    bucket, _base_prefix = resolve_results_location()
    s3 = _s3()
    pages = s3.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=deduction_prefix, Delimiter="/"
    )
    for page in pages:
        for p in page.get("CommonPrefixes", []):
            lane = p["Prefix"].split("/")[-2]
            try:
                body = s3.get_object(
                    Bucket=bucket, Key=f"{deduction_prefix}{lane}/all_rows.jsonl"
                )["Body"].read()
            except Exception:  # noqa: BLE001 -- a lane with no rows is itself a finding
                yield lane, ""
                continue
            yield lane, body.decode("utf-8", "replace")


def audit_lane(text: str) -> Dict[str, object]:
    """Classify one lane's cells into ok, infra-dead, or genuine-empty.

    Parameters
    ----------
    text : str
        Raw ``all_rows.jsonl``.

    Returns
    -------
    Dict[str, object]
        ``cells``, ``infra``, ``genuine``, and ``sanity_missing`` counts.
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
        # A counted prompt makes an empty result data, not loss.
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


@functools.lru_cache(maxsize=1)
def _induction_driver() -> Any:
    """Load ``notebooks/induction/run_study.py`` by file path; cached.

    Load lazily so ``--local`` needs no induction environment; path loading
    avoids deduction's same-named module.
    """
    path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
    spec = importlib.util.spec_from_file_location("induction_run_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _induction_store() -> S3ResultsStore:
    """Build the ``S3ResultsStore`` `audit_induction` reads real seeds from.

    Region follows ``SMOLBENCH_RESULTS_S3_REGION``, then ``AWS_REGION``.
    """
    bucket, base_prefix = resolve_results_location()
    region = os.environ.get("SMOLBENCH_RESULTS_S3_REGION") or os.environ.get("AWS_REGION") or None
    return S3ResultsStore(
        bucket=bucket, base_prefix=base_prefix, experiment=INDUCTION_EXPERIMENT, region=region
    )


def audit_induction(
    models: Optional[List[str]] = None, *, store: Any = None
) -> Tuple[Dict[str, Dict[str, Dict[str, List[int]]]], int]:
    """Report induction ``(model, arm)`` seed-set mismatches against the pinned grid.

    Walk the expected grid so absent S3 cells are reported; backend errors
    propagate rather than reading as zero seeds.

    Parameters
    ----------
    models : Optional[List[str]], optional
        Model keys to audit.
    store : Any, optional
        Store providing ``list_seeds``.

    Returns
    -------
    Tuple[Dict[str, Dict[str, Dict[str, List[int]]]], int]
        Mismatches by model and arm, plus grid cells examined.
    """
    driver = _induction_driver()
    roster: Dict[str, str] = driver.MODELS
    info_types: Tuple[str, ...] = tuple(driver.INFO_TYPES)
    base_seed: int = driver.BASE_SEED
    n_replicates: int = driver.N_REPLICATES

    selected = list(roster) if models is None else list(models)
    bad = [m for m in selected if m not in roster]
    if bad:
        raise SystemExit(
            f"audit_induction: unknown induction model key(s) {bad!r} -- valid "
            f"MODELS keys are {sorted(roster)!r}"
        )

    if store is None:
        store = _induction_store()

    expected = set(range(base_seed, base_seed + n_replicates))
    out: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
    for model in selected:
        tag = roster[model]
        for info in info_types:
            # Propagate backend errors; never read them as empty seeds.
            landed = set(store.list_seeds(model, tag, info))
            missing = sorted(expected - landed)
            unexpected = sorted(landed - expected)
            if missing or unexpected:
                out.setdefault(model, {})[info] = {
                    "missing": missing,
                    "unexpected": unexpected,
                }
    return out, len(selected) * len(info_types)


def main() -> int:
    """Run the deduction and optional induction completeness audits."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lane", default="", help="Audit one lane (substring match).")
    ap.add_argument("--local", action="store_true", help="Audit local run dirs, not S3.")
    ap.add_argument("--induction", action="store_true", help="Also audit induction seed coverage.")
    ap.add_argument(
        "--expect-cells", type=int, required=True,
        help="Cells expected per lane (the post-cutoff pool's size is not a constant).",
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
        # Never report success when nothing was examined.
        where = "local run dirs" if args.local else "S3"
        print(
            f"\n*** AUDITED NOTHING: no lane in {where} matched "
            f"{args.lane!r} ***" if args.lane else
            f"\n*** AUDITED NOTHING: no lanes found in {where} ***"
        )
        print("An empty selection is not a pass. Check the name, or drop --local.")
        return 1

    if args.induction:
        gaps, examined = audit_induction()
        print("\nINDUCTION seed coverage:")
        if examined == 0:
            # Never pass an empty induction grid.
            print("\n*** AUDITED NOTHING: the induction model/arm grid was empty ***")
            print("An empty grid is not a pass. Check --induction model selection.")
            failures.append("induction: audited 0 (model, arm) cells")
        elif gaps:
            for model, arms in sorted(gaps.items()):
                worst_missing = max(len(a["missing"]) for a in arms.values())
                unexpected_seeds = sorted({s for a in arms.values() for s in a["unexpected"]})
                failures.append(
                    f"{model}: induction missing up to {worst_missing} seed(s) per arm"
                    + (f", unexpected seed(s) {unexpected_seeds}" if unexpected_seeds else "")
                )
                print(f"  FAULT {model}: missing/unexpected seeds per arm -> {arms}")
        else:
            driver = _induction_driver()
            base_seed, n_replicates = driver.BASE_SEED, driver.N_REPLICATES
            print(
                f"  ok: every (model, arm) of the {examined} examined has seeds "
                f"{base_seed}..{base_seed + n_replicates - 1}"
            )

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
