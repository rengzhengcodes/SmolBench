"""Audit content-level run completeness. Catches SILENT data faults.

A check that counts rows is not a completeness check: a row can be present and
EMPTY (``candidate_proof: ""``, ``completion_tokens: 0``) when the generating box
died mid-run and the driver recorded the failure as an ordinary per-cell
``exception`` row. Row counts, shard-merge gates and traceback counts all pass on
that data. Assert on CONTENT.

A cell is DEAD when no row for its key carries a non-empty candidate_proof, and
dead cells split into two populations that must never be conflated. INFRA: no
attempt reached the model (no surviving row with prompt_tokens > 0) and some row
carries an infrastructure error -- LOST DATA, exactly the set
``runner._existing_keys()`` re-runs, so a plain relaunch regenerates these and
nothing else. GENUINE: no error anywhere, the model was asked and returned
nothing -- DATA, not loss; regenerating resamples until the model happens to
answer, inflating the numerator, so never "repair" these.

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

#: The induction study's ``S3ResultsStore.experiment`` key segment -- the same
#: ``induction/`` prefix the old hand-rolled-regex walk named via
#: ``INDUCTION_PREFIX`` (removed with FINDING 14-04's fix; see `audit_induction`
#: and `_induction_store`). Kept as a constant, not re-derived per call, since
#: it is the study's fixed notebook directory name
#: (``results_store.experiment_name``'s output for ``notebooks/induction/results``),
#: not something that varies with environment the way the bucket/prefix do.
INDUCTION_EXPERIMENT = "induction"

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


def iter_deduction_lanes(
    local: bool, *, deduction_prefix: Optional[str] = None
) -> Iterable[Tuple[str, str]]:
    """Yield ``(lane_name, all_rows_text)`` for every deduction lane.

    Parameters
    ----------
    local : bool
        Read local run directories instead of each lane's ``all_rows.jsonl``
        from S3.
    deduction_prefix : str, optional
        S3 key prefix the lanes spool under, WITH a trailing "/". ``None``
        (the default) resolves it lazily via `runner.spool_prefix()` -- a key
        prefix is CONFIGURATION, not audited logic, so importing the single
        source of truth for it here is not a hazard; `main` already resolves
        this once (also via a lazy import) and passes it down explicitly,
        this default only backstops a direct caller that omits it. Ignored
        when `local` is set, so a local audit never needs S3 credentials or a
        resolvable prefix.

    Yields
    ------
    tuple of (str, str)
        Lane name and its raw rows text, ``""`` when S3 holds no such object for
        a lane -- itself a finding.

    Notes
    -----
    The S3 BUCKET (as opposed to `deduction_prefix`, the key prefix inside it)
    is resolved here at CALL time via `resolve_results_location`, i.e. from
    ``SMOLBENCH_RESULTS_S3``, falling back to
    `smolbench.evals.results_store.DEFAULT_RESULTS_BUCKET` when that env var is
    unset/empty -- replacing a module-level ``BUCKET`` literal so a redirected
    results store reaches this auditor too. `deduction_prefix` is a DIFFERENT,
    orthogonal axis: the deduction spool has its own independent
    ``LEAN_SPOOL_PREFIX``/`spool_prefix` key-prefix scheme inside that bucket,
    unrelated to `resolve_results_location`'s ``base_prefix``.
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
    if deduction_prefix is None:
        from smolbench.deduction.lean.runner import spool_prefix

        deduction_prefix = spool_prefix() + "/"
    # Bucket resolved HERE, at call time (see docstring Notes), not a
    # module-level literal; `base_prefix` is discarded on purpose -- the
    # deduction spool's own `deduction_prefix` above is an independent
    # key-prefix scheme, not layered under `resolve_results_location`'s prefix.
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
        Raw ``all_rows.jsonl``, as yielded by `iter_deduction_lanes`.

    Returns
    -------
    dict
        Counts keyed ``cells`` (distinct cell keys), ``infra`` (dead cells lost
        to infrastructure), ``genuine`` (dead cells the model answered emptily),
        ``sanity_missing`` (sanity theorems with no passing verdict).
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
        # `prompt_tokens > 0` means the server counted a prompt, so the model
        # WAS asked and the empty result is its answer -- data, not loss.
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

    LAZY BY DESIGN -- call this only from inside a function body, never at
    module import time. Executing the driver module runs its OWN
    ``load_dotenv(notebooks/induction/keys.env)`` (and, under
    ``INDUCTION_SHARD``, mutates ``EC2_EXPERIMENT_TAG``); this script's
    ``--local`` deduction path must stay usable with no induction environment
    configured at all, which a module-scope call here would break.

    Loaded BY FILE PATH, exactly as ``scripts/fleet/lane_env.py`` does at its
    own module scope (see that file's "the induction driver import" comment):
    a bare ``import run_study`` is ambiguous once the DEDUCTION study's
    same-named ``notebooks/deduction/run_study.py`` is ALSO importable on
    ``sys.path`` (this same file's `main` already imports
    ``smolbench.deduction.lean.runner``, so both trees are live in one
    process). The module is registered in ``sys.modules`` under a distinct
    name (``"induction_run_study"``) BEFORE ``exec_module`` runs, matching
    ``lane_env.py``'s ordering, so any import inside the driver that looks
    itself up by that name mid-exec finds a (partially-initialized) module
    object rather than re-triggering this load.

    Returns
    -------
    module
        The executed driver module, exposing ``MODELS``, ``INFO_TYPES``,
        ``BASE_SEED`` and ``N_REPLICATES``. Memoized via ``lru_cache``, so a
        second call is a cache hit, not a second ``load_dotenv``/import-time
        side effect.
    """
    path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
    spec = importlib.util.spec_from_file_location("induction_run_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _induction_store() -> S3ResultsStore:
    """Build the ``S3ResultsStore`` `audit_induction` reads real seeds from.

    Split out from `audit_induction` so the S3 construction step alone is
    small, testable and independently patchable; the audit function's default
    seam is "call `_induction_store()` when `store` is not supplied".

    Bucket and base prefix come from `resolve_results_location`, i.e. from
    ``SMOLBENCH_RESULTS_S3`` (falling back to
    `smolbench.evals.results_store.DEFAULT_RESULTS_BUCKET`) -- the SAME
    resolution `iter_deduction_lanes` now uses for the deduction bucket, so one
    redirected results store reaches both audits. Region mirrors
    `smolbench.evals.results_store.resolve_store`'s own resolution rule (see
    that function's docstring, step 4-6): ``SMOLBENCH_RESULTS_S3_REGION``,
    else ``AWS_REGION``, else ``None`` (boto3's own credential/region chain
    decides).
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

    FINDING 14-04 fix: the previous implementation built its report ONLY from
    S3 listing hits, so a ``(model, arm)`` with ZERO objects in S3 (an absent
    model, or a wholly empty bucket) never entered its ``seen`` dict and was
    never reported -- a vacuous pass, exactly the failure mode this file's
    module docstring says an audit must never exhibit. This version walks the
    EXPECTED grid instead -- every model in `models` (or, by default, every key
    of the driver's ``MODELS``) crossed with every arm in ``INFO_TYPES`` -- so
    a cell with nothing landed is EXAMINED and reported like any other, not
    silently absent.

    Parameters
    ----------
    models : list of str, optional
        Induction roster SPEC KEYS (``MODELS`` keys, e.g. ``"deepseek-v4-pro"``)
        to restrict the audit to. ``None`` (the default) audits every model in
        the roster. A name that is not a ``MODELS`` key is treated as a
        caller typo, not a deliberately narrow selection -- see Raises: an
        unrecognized model must fail loudly, not silently audit nothing (the
        same vacuous-pass failure mode this function exists to remove, just
        moved to the caller's side).
    store : object, optional
        Duck-typed provider of ``list_seeds(model, tag, info) -> list[int]``,
        the same shape as ``smolbench.evals.results_store.ResultsStore
        .list_seeds`` (`S3ResultsStore` satisfies it directly). ``None`` (the
        default) builds the real store via `_induction_store`. THIS is the
        seam the offline test suite injects a fake through, so `audit_induction`
        is exercised with no AWS credentials, no network call and no boto3
        client construction.

    Returns
    -------
    tuple of (dict, int)
        ``({model: {arm: {"missing": [...], "unexpected": [...]}}}, examined)``.
        Only a ``(model, arm)`` whose seed set does not exactly match the
        expected range appears in the mapping -- an exact match is omitted,
        matching `audit_lane`'s "report only faults" shape. Per cell:

        - ``"missing"`` is ``sorted(expected - landed)``: seeds in
          ``range(BASE_SEED, BASE_SEED + N_REPLICATES)`` never collected.
        - ``"unexpected"`` is ``sorted(landed - expected)``: seeds landed
          OUTSIDE that range (e.g. a 31st seed) -- the case the old
          ``EXPECTED_SEEDS - len(seeds)`` subtraction turned into a
          nonsensical ``-1`` instead of naming the seed.

        ``examined`` is ``len(models or MODELS) * len(INFO_TYPES)``, the
        number of cells the grid walk actually visited -- so a caller can
        refuse to call a zero-cell grid a pass (see `main`'s ``--induction``
        block, which does exactly that).

    Raises
    ------
    SystemExit
        One or more `models` entries is not a key of the driver's ``MODELS``;
        names the bad key(s) and the full valid roster.
    Exception
        Whatever `store.list_seeds` raises (a credentials failure, throttling,
        ...) propagates UNCHANGED -- never caught and read as "0 seeds
        landed", which would just relocate the vacuous-pass bug this function
        replaces into a new hiding place.
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
            # Not wrapped in try/except: a real backend error must propagate
            # (see Raises), never read as an empty seed set.
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
    # Lazy import, at the TOP of main(): the expected-cells default below is
    # CONFIGURATION (the study's pinned shape), read from the single source
    # of truth in `runner` rather than duplicated here as a local constant.
    # It is a plain int and cannot raise, so using it straight as an argparse
    # default is safe -- unlike `runner.spool_prefix()` below, which is
    # resolved only AFTER parse_args (see that call site's comment).
    from smolbench.deduction.lean import runner

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lane", default="", help="Audit one lane (substring match).")
    ap.add_argument("--local", action="store_true", help="Audit local run dirs, not S3.")
    ap.add_argument("--induction", action="store_true", help="Also audit induction seed coverage.")
    ap.add_argument(
        "--expect-cells", type=int, default=runner.EXPECTED_CELLS,
        help="Cells expected per lane (default: %(default)s).",
    )
    ap.add_argument(
        "--spool-prefix", default=None,
        help="S3 key prefix the deduction lanes spooled under (default: the "
             "re-collection prefix -- LEAN_SPOOL_PREFIX, or "
             "deduction_postcutoff/runs if unset). The published pre-cutoff "
             "study lives at deduction/runs; pass that explicitly to audit "
             "it (no env opt-in needed on this read-only path).",
    )
    args = ap.parse_args()

    # Resolved AFTER parse_args, not at import or parser-build time: a
    # module-level `spool_prefix()` call, or an eagerly-evaluated argparse
    # default, would make `LEAN_SPOOL_PREFIX=deduction/runs --help` explode
    # (see `iter_deduction_lanes`'s docstring for the same lazy-import
    # rationale).
    deduction_prefix = (args.spool_prefix or runner.spool_prefix()) + "/"

    print(f"{'lane':38s} {'cells':>6s} {'INFRA':>6s} {'genuine':>8s} {'status':>8s}")
    total_infra = total_genuine = 0
    audited = 0
    failures: List[str] = []
    for lane, text in iter_deduction_lanes(args.local, deduction_prefix=deduction_prefix):
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
        # An audit that examined NOTHING must never report success: that is
        # the exact failure this script exists to catch, turned on itself.
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
            # This is the induction analogue of the `if not audited:` guard
            # above -- but that guard counts DEDUCTION lanes and runs BEFORE
            # this block, so it cannot see an empty induction grid. Without
            # this check, an empty selection would report a clean (empty)
            # `gaps` mapping and read as a pass -- the exact vacuous-pass bug
            # FINDING 14-04 removed from `audit_induction` itself, relocated
            # into `main` if left unguarded here.
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
