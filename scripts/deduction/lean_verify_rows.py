"""Verify recorded Lean rows in a deferred pass.
Phase 1 (``run_study.py``/``runner`` with ``NullVerifier``) records ``"unverified"``/``"skipped"`` rows; replay ``all_rows.jsonl`` into sibling ``verified_rows.jsonl``.
Generation needs a provider API; verification needs ``elan`` and traced mathlib.
Never alter ``all_rows.jsonl``: a verification bug must not lose paid proofs.
Lazy ``lean_interact`` and boto imports keep ``--dry-run`` dependency-free.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import contextlib
import fnmatch
import functools
import importlib.util
import itertools
import json
import logging
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional

import fcntl  # POSIX-only; verification hosts are Linux.

from smolbench.deduction.lean.corpus import BenchmarkTheorem, load_split
from smolbench.deduction.lean.runner import (
    NEVER_MEASURED_VERDICTS as _NEVER_MEASURED_VERDICTS,
)
from smolbench.deduction.lean.runner import (
    _default_verifier,
    group_cell_rows,
    jsonl_line,
    read_jsonl_tolerating_torn_tail,
)
from smolbench.evals import _aws
from smolbench.evals.results_store import parse_s3_uri
from smolbench.evals.spool import spool_prefix

logging.basicConfig(level=logging.INFO)

_error_code = _aws.error_code


#: Shared deduction spool bucket; prefix comes from `spool_prefix()` at call time.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
DEFAULT_RUNS_GLOB: str = "scaling_*"
S3_REGION: str = "us-west-2"
ROWS_FILENAME: str = "all_rows.jsonl"
VERIFIED_FILENAME: str = "verified_rows.jsonl"
UPLOAD_EVERY_GROUPS: int = 10
RAM_GB_PER_WORKER: int = 6
DOJO_CACHE_DIR: Path = Path.home() / ".cache" / "lean_dojo"

#: Lock beside, never inside, the worker-shared cache directory.
_LOCK_FILENAME = ".smolbench_verify.lock"

_CORPUS_SPLITS: tuple[str, ...] = ("train", "val", "test")

def run_object_key(key_prefix: str, run: str, filename: str) -> str:
    """Build one run's object key ``f"{key_prefix}/{run}/{filename}"``.

    Strip segments and drop empties so keys have no leading or doubled ``"/"``.

    Parameters
    ----------
    key_prefix : str
        Prefix for the run object.
    run : str
        Run name.
    filename : str
        Object filename.

    Returns
    -------
    str
        Normalized object key.
    """
    segments = (key_prefix.strip("/"), run.strip("/"), filename.strip("/"))
    return "/".join(segment for segment in segments if segment)


def group_unverified(rows: list[dict]) -> dict[tuple[str, int], list[int]]:
    """Group still-unverified cell rows by their ``(theorem_id, k)`` pair.

    Rows sharing a pair share one Dojo session.

    Parameters
    ----------
    rows : list[dict]
        Rows to filter and group.

    Returns
    -------
    dict[tuple[str, int], list[int]]
        Unverified cell-row indices by ``(theorem_id, k)``.
    """
    groups: dict[tuple[str, int], list[int]] = {}
    for index, row in enumerate(rows):
        if row.get("kind") != "cell":
            continue
        if row.get("verdict") != "unverified":
            continue
        groups.setdefault((row["theorem_id"], row["k"]), []).append(index)
    return groups


def unique_candidates(rows: list[dict], indices: list[int]) -> dict[str, list[int]]:
    """Group `indices` by their exact ``candidate_proof`` text.

    Replay is deterministic, so equal text needs one ``try_tail`` call.
    Do not normalize: one-character differences can change Lean's result.

    Parameters
    ----------
    rows : list[dict]
        Rows containing candidate proofs.
    indices : list[int]
        Indices of rows to group.

    Returns
    -------
    dict[str, list[int]]
        Row indices by candidate; missing candidates use ``""``.
    """
    groups: dict[str, list[int]] = {}
    for index in indices:
        candidate = rows[index].get("candidate_proof") or ""
        groups.setdefault(candidate, []).append(index)
    return groups


def fan_out_verdict(rows: list[dict], indices: list[int], result: Mapping[str, Any]) -> None:
    """Apply one verification `result` to every row in `indices`, in place.

    ``result`` must contain the four verification fields; preserve all others.

    Parameters
    ----------
    rows : list[dict]
        Rows updated in place.
    indices : list[int]
        Indices of rows to update.
    result : Mapping[str, Any]
        Verification fields.
    """
    for index in indices:
        row = rows[index]
        row["verdict"] = result["verdict"]
        row["lean_error"] = result["lean_error"]
        row["final_state_pp"] = result["final_state_pp"]
        row["verify_ms"] = result["verify_ms"]


def _group_cell_rows_by_key(rows: list[dict]) -> dict[tuple[str, int], list[dict]]:
    """Group ``kind == "cell"`` `rows` by ``(theorem_id, k)``, in `rows` order.

    Shared with the never-measured diagnostic so both use the same groups.

    Parameters
    ----------
    rows : list[dict]
        Rows containing cell records.

    Returns
    -------
    dict[tuple[str, int], list[dict]]
        Cell rows by ``(theorem_id, k)``.
    """
    return group_cell_rows(
        (r for r in rows if r.get("kind") == "cell"),
        lambda r: (r["theorem_id"], r["k"]),
    )


def _never_measured(cell_rows: list[dict]) -> bool:
    """Whether no row in ``cell_rows`` was tested against Lean.

    Parameters
    ----------
    cell_rows : list[dict]
        Cell rows in one group.

    Returns
    -------
    bool
        Whether all verdicts are never-measured.
    """
    return all(row.get("verdict") in _NEVER_MEASURED_VERDICTS for row in cell_rows)


def resume_done_groups(verified_rows: list[dict]) -> set[tuple[str, int]]:
    """Find the ``(theorem_id, k)`` groups a later pass should NOT re-attempt.

    Use paired, all cells: later phase-1 cells are absent from ``verified_rows``
    alone and would stay ``"unverified"`` under an any-cell rule. Retry
    never-measured groups because rows cannot distinguish a transient REPL failure
    from an unopenable theorem, matching ``runner._existing_keys``; one attempt
    per group/pass.
    ``"no_answer"`` is measured because no candidate remains to retry.

    Parameters
    ----------
    verified_rows : list[dict]
        Paired output rows from the current and prior passes.

    Returns
    -------
    set[tuple[str, int]]
        Completed groups.
    """
    groups = _group_cell_rows_by_key(verified_rows)
    return {
        key
        for key, cell_rows in groups.items()
        if all(row.get("verdict") != "unverified" for row in cell_rows)
        and not _never_measured(cell_rows)
    }


def row_identity(row: dict) -> tuple:
    """Extract a row's identity: ``(kind, model, theorem_id, k, rung, replicate_idx)``.

    Missing sanity fields yield ``None``; ``kind`` extends ``runner._row_key``
    to prevent cell/sanity collisions.

    Parameters
    ----------
    row : dict
        Row whose identity is extracted.

    Returns
    -------
    tuple
        Row identity tuple.
    """
    return (
        row.get("kind"),
        row.get("model"),
        row.get("theorem_id"),
        row.get("k"),
        row.get("rung"),
        row.get("replicate_idx"),
    )


def seed_out_rows(rows: list[dict], verified_rows: list[dict]) -> tuple[list[dict], int]:
    """Pair a prior pass's rows onto the current rows, by identity and occurrence order.

    Pair by identity and occurrence: positional pairing breaks when rows move,
    and a map aliases repeated identities, which real lanes repeat up to 16 times.
    Keep matched rows whole; use ``--no-resume`` after regeneration. Append
    orphans in original order so current-row indices and order stay valid.

    Parameters
    ----------
    rows : list[dict]
        Current-pass rows.
    verified_rows : list[dict]
        Prior verified rows.

    Returns
    -------
    tuple[list[dict], int]
        Output rows and unmatched-prior count.
    """
    prior_by_identity: dict[tuple, collections.deque[tuple[int, dict]]] = (
        collections.defaultdict(collections.deque)
    )
    for original_index, prior_row in enumerate(verified_rows):
        prior_by_identity[row_identity(prior_row)].append((original_index, prior_row))

    out_rows: list[dict] = []
    for row in rows:
        bucket = prior_by_identity.get(row_identity(row))
        if bucket:
            _, prior_row = bucket.popleft()
            out_rows.append(prior_row)
        else:
            out_rows.append(row)

    # Sort by original index so repeated orphan identities retain prior order.
    orphans = sorted(
        (
            (original_index, prior_row)
            for bucket in prior_by_identity.values()
            for original_index, prior_row in bucket
        ),
        key=lambda pair: pair[0],
    )
    out_rows.extend(prior_row for _, prior_row in orphans)

    return out_rows, len(orphans)


def available_ram_gb(meminfo_text: str) -> float:
    """Extract ``MemAvailable`` (kB in the file) from ``/proc/meminfo`` TEXT, in GiB.

    Accept text so budget math is fixture-testable.

    Parameters
    ----------
    meminfo_text : str
        Contents of ``/proc/meminfo``.

    Returns
    -------
    float
        Available GiB.

    Raises
    ------
    ValueError
        Missing ``"MemAvailable:"``.
    """
    for line in meminfo_text.splitlines():
        if line.startswith("MemAvailable:"):
            fields = line.split()
            kb = float(fields[1])
            return kb / 1024 / 1024
    raise ValueError(
        "available_ram_gb: no 'MemAvailable:' line found in the given /proc/meminfo text"
    )


def max_workers_allowed(meminfo_text: str) -> int:
    """Cap worker count by available RAM at `RAM_GB_PER_WORKER` GiB each.

    Never return below 1 so :func:`check_workers` can give a useful refusal.

    Parameters
    ----------
    meminfo_text : str
        Contents of ``/proc/meminfo``.

    Returns
    -------
    int
        RAM-budgeted cap.
    """
    return max(int(available_ram_gb(meminfo_text) // RAM_GB_PER_WORKER), 1)


def check_workers(requested: int, meminfo_text: str) -> None:
    """Refuse an oversubscribed (or non-positive) ``--workers`` value up front.

    Each Dojo session costs 6 GiB empirically; oversubscription can OOM hours later.

    Parameters
    ----------
    requested : int
        Requested worker count.
    meminfo_text : str
        Contents of ``/proc/meminfo``.
    """
    if requested < 1:
        raise SystemExit(f"check_workers: --workers must be >= 1, got {requested}")
    cap = max_workers_allowed(meminfo_text)
    if requested > cap:
        available = available_ram_gb(meminfo_text)
        raise SystemExit(
            f"check_workers: --workers={requested} exceeds the RAM-budgeted cap of "
            f"{cap} (observed {available:.1f} GiB available / {RAM_GB_PER_WORKER} GiB "
            "per worker). Each Dojo session holds a live Lean process plus its loaded "
            "environment; oversubscribing risks an OOM kill hours into the pass rather "
            "than a clean refusal now. Lower --workers or free up RAM."
        )


def require_lean_interact() -> None:
    """Raise ``SystemExit`` if ``lean_interact`` (the ``lean`` extra) is not importable."""
    if importlib.util.find_spec("lean_interact") is None:
        raise SystemExit(
            "lean_verify_rows: this is the deferred VERIFICATION pass and needs "
            "'lean_interact' (the `lean` extra). Install it into the project venv "
            "with `uv sync --all-extras` and re-run via .venv/bin/python. "
            "The pass also needs SMOLBENCH_MATHLIB_ROOT pointing at a mathlib4 "
            "checkout that has been built with elan/lake. "
            "(--dry-run works without it if you only need to preview the plan.)"
        )


def require_mathlib_root() -> None:
    """Exit if ``SMOLBENCH_MATHLIB_ROOT`` does not resolve.

    Otherwise every session fails, misreporting configuration as 944 bad truths.
    """
    from smolbench.deduction.lean.replbackend import mathlib_root  # lazy: import-safe module
    try:
        mathlib_root()
    except RuntimeError as exc:
        raise SystemExit(f"lean_verify_rows: {exc}") from exc


def dojo_failure_hint(exc: BaseException) -> str:
    """Build guidance for a session-open failure after ``replbackend`` retries.

    Parameters
    ----------
    exc : BaseException
        Session-open failure.

    Returns
    -------
    str
        Failure guidance.
    """
    return (
        f"Lean REPL session failed to open: {type(exc).__name__}: {exc}\n"
        "This is usually infrastructure, not a broken candidate proof. Confirm "
        "SMOLBENCH_MATHLIB_ROOT points at a mathlib4 checkout at the corpus commit "
        "whose oleans are built (`lake exe cache get` inside it), that 'elan' is "
        "installed (curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y "
        "--default-toolchain none) and on PATH, and that the lean-interact REPL for "
        "that toolchain built (first use compiles it; see "
        ".claude/skills/run-smolbench/SKILL.md)."
    )


@functools.lru_cache(maxsize=1)
def _theorem_index() -> dict[str, BenchmarkTheorem]:
    """Index the local corpus by ``full_name``.

    Rows lack ``(kind, split)``, so scan all combinations. First seen wins a
    collision because declarations belong to one partition. Skip ``load_split``
    ``FileNotFoundError`` combinations because operators may bootstrap only swept
    splits; cache per process.
    """
    index: dict[str, BenchmarkTheorem] = {}
    for split in _CORPUS_SPLITS:
        try:
            theorems = load_split("random", split)  # type: ignore[arg-type]
        except FileNotFoundError:
            continue
        for theorem in theorems:
            index.setdefault(theorem.full_name, theorem)
    return index


def _lookup_theorem(theorem_id: str) -> BenchmarkTheorem:
    """Resolve a row's `theorem_id` (== ``BenchmarkTheorem.full_name``) to its theorem.

    Parameters
    ----------
    theorem_id : str
        Theorem full name.

    Returns
    -------
    BenchmarkTheorem
        The matching theorem.

    Raises
    ------
    LookupError
        No local ``(kind, split)`` contains ``theorem_id``.
    """
    index = _theorem_index()
    if theorem_id not in index:
        raise LookupError(
            f"{theorem_id!r} not found in any local (kind, split) combination of "
            "the LeanDojo Benchmark 4 corpus"
        )
    return index[theorem_id]


# Lazy imports keep this module importable without lean_interact or boto3.
def _build_s3_client() -> Any:
    """Build a fresh boto3 S3 client bound to `S3_REGION` via ``_aws.fresh_client``.

    A fresh session picks up rotated credentials; this is the boto3 opt-in.
    """
    return _aws.fresh_client("s3", S3_REGION)


# S3 I/O; client is injected for real and test clients.
def list_runs(
    client: Any, bucket: str, key_prefix: str, pattern: str = DEFAULT_RUNS_GLOB
) -> list[str]:
    """List run directory names directly under `key_prefix`, filtered by `pattern`.

    ``pattern`` matches a run name, not its full key.

    Parameters
    ----------
    client : Any
        S3 client.
    bucket : str
        S3 bucket name.
    key_prefix : str
        Prefix containing run directories.
    pattern : str, optional
        Pattern for run names.

    Returns
    -------
    list[str]
        Sorted matching delimiter-listing names.
    """
    prefix = f"{key_prefix}/" if key_prefix else ""
    names: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for common in page.get("CommonPrefixes", []):
            name = common["Prefix"][len(prefix):].rstrip("/")
            if name and fnmatch.fnmatch(name, pattern):
                names.append(name)
    return sorted(names)


def download_rows(client: Any, bucket: str, key: str, dest: Path) -> list[dict]:
    """Download one JSONL object to `dest` (parents created) and return its parsed rows.

    Write full body bytes verbatim; never repair the object or local copy.

    Parameters
    ----------
    client : Any
        S3 client.
    bucket : str
        S3 bucket name.
    key : str
        Object key.
    dest : Path
        Local destination path.

    Returns
    -------
    list[dict]
        Rows, or ``[]`` only for ``"NoSuchKey"``/``"404"``; propagate other failures
        so they never look like nothing to verify.
    """
    from botocore.exceptions import ClientError  # lazy: importing must not need boto3

    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except ClientError as err:
        if _error_code(err) in ("NoSuchKey", "404"):
            return []
        raise
    body = obj["Body"].read()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)

    return read_jsonl_tolerating_torn_tail(dest)


def upload_rows(client: Any, rows: list[dict], bucket: str, key: str, workdir: Path) -> None:
    """Serialize rows under ``workdir`` and upload them to ``key``.

    Rewrite the full scratch file so repeated checkpoints are safe.

    Parameters
    ----------
    client : Any
        S3 client.
    rows : list[dict]
        Rows to serialize and upload.
    bucket : str
        S3 bucket name.
    key : str
        Destination object key.
    workdir : Path
        Scratch directory.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    scratch = workdir / VERIFIED_FILENAME
    with scratch.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(jsonl_line(row))
    client.upload_file(str(scratch), bucket, key)


@contextlib.contextmanager
def _dojo_cache_lock() -> Iterator[None]:
    """Hold an exclusive non-blocking flock on `_LOCK_FILENAME` in `DOJO_CACHE_DIR`.

    Hold it for all runs: concurrent passes race on the shared build cache.
    """
    DOJO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = DOJO_CACHE_DIR / _LOCK_FILENAME
    lock_file = open(lock_path, "a+")
    try:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit(
                f"lean_verify_rows: another verification pass already holds the "
                f"exclusive lock at {lock_path} -- concurrent passes race on the "
                f"shared traced-repo build cache under {DOJO_CACHE_DIR}. Wait for "
                "the other pass to finish, or (if it is confirmed stale/dead) "
                "remove the lock file by hand."
            ) from exc
        yield
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


def _update_sanity_row(out_rows: list[dict], theorem_id: str, payload: Mapping[str, Any], ms: int) -> None:
    """Update `theorem_id`'s sanity row in `out_rows` in place, appending one if absent.

    Write payload fields and wall-clock ``ms``. Append missing rows so shared
    ``all_rows.jsonl`` indices never shift.

    Parameters
    ----------
    out_rows : list[dict]
        Output rows updated in place.
    theorem_id : str
        Theorem identifier for the sanity row.
    payload : Mapping[str, Any]
        Sanity fields.
    ms : int
        Replay milliseconds.
    """
    for row in out_rows:
        if row.get("kind") == "sanity" and row.get("theorem_id") == theorem_id:
            row["verdict"] = payload["verdict"]
            row["tactics_applied"] = payload["tactics_applied"]
            row["tactics_total"] = payload["tactics_total"]
            row["error"] = payload["error"]
            row["ms"] = ms
            return
    out_rows.append(
        {
            "kind": "sanity",
            "theorem_id": theorem_id,
            "verdict": payload["verdict"],
            "tactics_applied": payload["tactics_applied"],
            "tactics_total": payload["tactics_total"],
            "ms": ms,
            "error": payload["error"],
        }
    )


def verify_run(
    *,
    client: Any,
    bucket: str,
    key_prefix: str,
    run: str,
    workers: int,
    theorem: Optional[str] = None,
    limit: int = 0,
    workdir: Path,
    dry_run: bool = False,
    no_resume: bool = False,
    verifier: Any = None,
) -> int:
    """Verify one run's unverified cell groups; upload `VERIFIED_FILENAME`.

    ``workdir`` is the parent of the private ``workdir / run`` scratch dir.
    Resolve ``verifier=None`` only for pending groups so ``dry_run`` avoids imports.

    Parameters
    ----------
    client : Any
        S3 client.
    bucket : str
        S3 bucket name.
    key_prefix : str
        Prefix containing the run.
    run : str
        Run name.
    workers : int
        Number of verification workers.
    theorem : Optional[str], optional
        Restrict verification to this theorem identifier.
    limit : int, optional
        Maximum number of groups to process.
    workdir : Path
        Parent scratch directory.
    dry_run : bool, optional
        Preview groups without importing the verifier.
    no_resume : bool, optional
        Discard prior verification rows.
    verifier : Any, optional
        Verifier instance.

    Returns
    -------
    int
        ``0`` success/partial pass, ``1`` missing rows, ``2`` surviving full-pass sentinel;
        always upload before reporting so the gate never withholds output.
    """
    run_dir = workdir / run
    rows_key = run_object_key(key_prefix, run, ROWS_FILENAME)
    rows = download_rows(client, bucket, rows_key, run_dir / ROWS_FILENAME)
    if not rows:
        logging.warning(
            f"lean_verify_rows[{run}]: {ROWS_FILENAME} not found at "
            f"s3://{bucket}/{rows_key}; skipping this run."
        )
        return 1

    verified_key = run_object_key(key_prefix, run, VERIFIED_FILENAME)
    verified_rows = download_rows(client, bucket, verified_key, run_dir / VERIFIED_FILENAME)
    if no_resume:
        # Resume keys groups, not proofs; regenerated lanes otherwise look done.
        logging.warning(
            f"lean_verify_rows[{run}]: --no-resume: discarding {len(verified_rows)} "
            "row(s) from the prior verification pass and re-verifying every group."
        )
        verified_rows = []

    # Appended orphans keep indices from immutable `rows` valid in `out_rows`.
    out_rows, n_orphans = seed_out_rows(rows, verified_rows)
    if n_orphans:
        logging.warning(
            f"lean_verify_rows[{run}]: {n_orphans} row(s) from the prior "
            f"verification pass have no counterpart in {ROWS_FILENAME}; "
            f"appended to the end of {VERIFIED_FILENAME} rather than dropped."
        )

    # Use paired `out_rows`: all-cells resume must see newly appended cells.
    done = resume_done_groups(out_rows)

    # Immutable `rows` gives phase 1's complete groups; subtract `done` to resume.
    all_groups = group_unverified(rows)
    pending = {key: indices for key, indices in all_groups.items() if key not in done}
    if theorem is not None:
        pending = {key: indices for key, indices in pending.items() if key[0] == theorem}
    if limit > 0 and len(pending) > limit:
        pending = dict(itertools.islice(pending.items(), limit))

    n_pending_rows = sum(len(indices) for indices in pending.values())
    logging.info(
        f"lean_verify_rows[{run}]: {len(all_groups)} group(s) total, {len(done)} "
        f"already resumed-done, {len(pending)} to process this pass "
        f"({n_pending_rows} cell row(s))."
    )

    if dry_run:
        for (theorem_id, k), indices in pending.items():
            print(f"  [{run}] {theorem_id}  k={k}  -- {len(indices)} unverified row(s)")
        return 0

    if not pending:
        return 0

    if verifier is None:
        verifier = _default_verifier()

    write_lock = threading.Lock()
    sanity_lock = threading.Lock()
    sanity_done_this_run: set[str] = set()

    def _verify_one_group(theorem_id: str, k: int, indices: list[int]) -> None:
        """Verify one ``(theorem_id, k)`` group; ``_process_group`` catches escapes."""
        lookup_error: Optional[BaseException] = None
        try:
            bt = _lookup_theorem(theorem_id)
        except Exception as exc:  # noqa: BLE001 -- recorded below, not swallowed
            bt = None
            lookup_error = exc

        # Replay sanity once per theorem under `sanity_lock`.
        with sanity_lock:
            first_time_this_theorem = theorem_id not in sanity_done_this_run
            sanity_done_this_run.add(theorem_id)
        if first_time_this_theorem:
            t0 = time.monotonic()
            if bt is None:
                sanity_payload = {
                    "verdict": "exception",
                    "tactics_applied": 0,
                    "tactics_total": 0,
                    "error": (
                        f"theorem not found in local corpus: "
                        f"{type(lookup_error).__name__}: {lookup_error}"
                    ),
                }
            else:
                replay = verifier.replay_ground_truth(bt)
                sanity_payload = {
                    "verdict": replay.verdict,
                    "tactics_applied": replay.tactics_applied,
                    "tactics_total": replay.tactics_total,
                    "error": replay.error,
                }
            sanity_ms = int((time.monotonic() - t0) * 1000)
            with write_lock:
                _update_sanity_row(out_rows, theorem_id, sanity_payload, sanity_ms)

        if bt is None:
            payload = {
                "verdict": "replay_failed",
                "lean_error": (
                    f"theorem {theorem_id!r} not found in local corpus: "
                    f"{type(lookup_error).__name__}: {lookup_error}"
                ),
                "final_state_pp": None,
                "verify_ms": 0,
            }
            with write_lock:
                fan_out_verdict(out_rows, indices, payload)
            return

        try:
            with verifier.open_at_step(bt, k) as (dojo, state_at_k):
                for candidate_text, candidate_indices in unique_candidates(out_rows, indices).items():
                    t0 = time.monotonic()
                    try:
                        result = verifier.try_tail(dojo, state_at_k, candidate_text, theorem_id)
                        payload = {
                            "verdict": result.verdict,
                            "lean_error": result.error,
                            "final_state_pp": result.final_state_pp,
                            "verify_ms": int((time.monotonic() - t0) * 1000),
                        }
                    except Exception as exc:  # noqa: BLE001 -- recorded on the row, never swallowed
                        payload = {
                            "verdict": "exception",
                            "lean_error": f"{type(exc).__name__}: {exc}",
                            "final_state_pp": None,
                            "verify_ms": int((time.monotonic() - t0) * 1000),
                        }
                    with write_lock:
                        fan_out_verdict(out_rows, candidate_indices, payload)
        except Exception as exc:  # noqa: BLE001 -- Record open-session failures on rows.
            message = str(exc)
            if isinstance(exc, RuntimeError) and message.startswith("prefix tactic "):
                # Dojo opened but its prefix failed; infrastructure guidance misleads.
                lean_error = f"{type(exc).__name__}: {exc}"
            else:
                # Dojo never opened after verify.py's three retries.
                lean_error = dojo_failure_hint(exc)
            payload = {
                "verdict": "replay_failed",
                "lean_error": lean_error,
                "final_state_pp": None,
                "verify_ms": 0,
            }
            with write_lock:
                fan_out_verdict(out_rows, indices, payload)

    def _process_group(key: tuple[str, int]) -> tuple[str, int]:
        """Executor entry point: last-resort net around `_verify_one_group`.

        Catch unexpected failures so every group row gets ``"exception"`` and
        the executor never raises.

        Parameters
        ----------
        key : tuple[str, int]
            ``(theorem_id, k)`` group key.

        Returns
        -------
        tuple[str, int]
            Processed group key.
        """
        theorem_id, k = key
        try:
            _verify_one_group(theorem_id, k, pending[key])
        except Exception as exc:  # noqa: BLE001 -- Last-resort per-group failure record.
            payload = {
                "verdict": "exception",
                "lean_error": f"{type(exc).__name__}: {exc}",
                "final_state_pp": None,
                "verify_ms": 0,
            }
            with write_lock:
                fan_out_verdict(out_rows, pending[key], payload)
        return key

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_process_group, key): key for key in pending}
        for future in concurrent.futures.as_completed(futures):
            future.result()  # `_process_group` records failures instead of raising.
            completed += 1
            if completed % UPLOAD_EVERY_GROUPS == 0:
                upload_rows(client, out_rows, bucket, verified_key, run_dir)
                logging.info(
                    f"lean_verify_rows[{run}]: checkpoint upload after "
                    f"{completed}/{len(pending)} group(s)."
                )

    # The final checkpoint already has these rows.
    if completed % UPLOAD_EVERY_GROUPS:
        upload_rows(client, out_rows, bucket, verified_key, run_dir)
    logging.info(f"lean_verify_rows[{run}]: done -- {completed} group(s) processed.")

    # Only --limit/--theorem/--dry-run are partial; done groups have no sentinels.
    # A sentinel means an unwritten verdict or an ungraded orphan not selectable from rows.
    full_pass = limit <= 0 and theorem is None
    if full_pass:
        n_sentinel = sum(
            1 for row in out_rows
            if row.get("kind") == "cell" and row.get("verdict") == "unverified"
        )
        if n_sentinel:
            logging.error(
                f"lean_verify_rows[{run}]: FULL PASS LEFT {n_sentinel} CELL ROW(S) "
                'ON THE GENERATION-TIME "unverified" SENTINEL. This was a full '
                "pass -- no --limit, no --theorem -- so every cell row should "
                "have been graded (resume cannot legitimately leave sentinels: "
                "a done group has none by construction). The output above was "
                "still uploaded in full (this gate reports, it never discards), "
                "but every downstream analysis loader scores an \"unverified\" "
                "cell as a FAILURE: left uncorrected, this run reads as \"the "
                "model proved nothing,\" a complete, plausible, and wrong result. "
                "Investigate the verifier before trusting this run's numbers."
            )
            return 2

        # Keep this diagnostic separate: ``power_analysis.UNMEASURABLE_VERDICTS``
        # covers corpus-stable failures across 21 models, which must not make every
        # healthy full pass nonzero.
        # Restrict to attempted groups; rc=2 separately covers unattempted orphans.
        never_measured_groups = {
            key
            for key, cell_rows in _group_cell_rows_by_key(out_rows).items()
            if key in pending and _never_measured(cell_rows)
        }
        if never_measured_groups:
            affected = sorted(never_measured_groups)
            logging.warning(
                f"lean_verify_rows[{run}]: {len(affected)} (theorem_id, k) GROUP(S) "
                'ENDED THIS FULL PASS WITH EVERY CELL ON "replay_failed"/'
                '"exception". A verdict WAS written for each of these -- this is '
                "NOT the rc=2 sentinel gate above -- and what it says is that Lean "
                "verification could not even be SET UP for that group (the REPL "
                "session never opened). This code cannot tell you whether that is "
                "a broken box (SMOLBENCH_MATHLIB_ROOT unset or wrong, elan "
                "missing, a wedged host -- see dojo_failure_hint()) or a "
                "PERMANENT property of the corpus (no *.ast.json for that theorem "
                "in the traced mathlib4 cache): nothing recorded on a row "
                "distinguishes the two. The discriminator: diff THIS pass's "
                "affected (theorem_id, k) set, listed at the end of this message, "
                "against a PRIOR pass's. A box problem MOVES the set -- different "
                "theorems fail depending on what broke this time -- while a corpus "
                "property does NOT: the same theorems fail on every pass. See "
                "notebooks/deduction/analysis/power_analysis.UNMEASURABLE_VERDICTS "
                "for why cells confirmed corpus-stable are excluded from analysis "
                f"entirely rather than scored 0. Affected groups: {affected}"
            )

    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build this script's `argparse.ArgumentParser`."""
    parser = argparse.ArgumentParser(
        prog="lean_verify_rows.py",
        description=(
            "Phase 2 of the two-phase Lean theorem-proving eval: replay recorded "
            "candidate proofs against real Lean and write verified_rows.jsonl "
            "alongside each run's all_rows.jsonl in S3. Requires lean_interact "
            "installed (uv sync --all-extras) except under --dry-run."
        ),
    )
    parser.add_argument(
        "--s3-prefix", default=f"s3://{SPOOL_BUCKET}/{spool_prefix()}",
        help="s3://bucket/key-prefix under which every run lives (default: %(default)s)",
    )
    parser.add_argument(
        "--runs", default=DEFAULT_RUNS_GLOB,
        help=f"fnmatch glob over run directory names (default: {DEFAULT_RUNS_GLOB!r})",
    )
    parser.add_argument(
        "--workers", type=int, default=2,
        help="parallel worker threads, each owning its own Dojo session per group (default: 2)",
    )
    parser.add_argument(
        "--theorem", default=None,
        help="only verify groups for this theorem_id; a group still bundles every "
             "rung/model/replicate sharing that theorem's (theorem, k) Dojo session",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="cap the number of (theorem, k) groups processed per run (0 = no limit); "
             "a group can bundle many replicates, so this bounds Dojo sessions, not rows",
    )
    parser.add_argument(
        "--workdir", default=None,
        help="transient scratch directory (default: a fresh tempfile.mkdtemp())",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        default=False,
        help=(
            "Re-verify every group from the CURRENT all_rows.jsonl, discarding "
            "the prior pass's verdicts. Required when phase 1 REGENERATED a "
            "lane after it was verified: resume is keyed on (theorem_id, k) "
            "groups, not on the candidate proofs inside them, so a regenerated "
            "lane looks entirely 'done' while its proofs are completely "
            "different. Archive the superseded verified_rows.jsonl first -- "
            "this overwrites it."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="list which groups' replicates would be verified for each matching run, "
             "then exit without opening Lean -- works on any interpreter",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Verify every matching run under ``--s3-prefix``.

    Otherwise require Lean/root, check RAM, lock the cache, then list and verify
    runs; ``--dry-run`` skips the first three.

    Parameters
    ----------
    argv : Optional[list[str]], optional
        Command-line arguments.

    Returns
    -------
    int
        Failed-run count; isolate runs so one exception does not abort later lanes.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    s3_prefix = args.s3_prefix

    if not args.dry_run:
        require_lean_interact()
        require_mathlib_root()

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="lean_verify_rows_"))
    workdir.mkdir(parents=True, exist_ok=True)

    bucket, key_prefix = parse_s3_uri(s3_prefix)
    client = _build_s3_client()
    runs = list_runs(client, bucket, key_prefix, args.runs)
    if not runs:
        logging.warning(
            f"lean_verify_rows: no runs under s3://{bucket}/{key_prefix} matched "
            f"{args.runs!r}."
        )
        return 0

    def _verify_every_run() -> int:
        """Verify each run without aborting later lanes after one failure (for example, lane 3)."""
        n_failed = 0
        for run in runs:
            try:
                rc = verify_run(
                    client=client,
                    bucket=bucket,
                    key_prefix=key_prefix,
                    run=run,
                    workers=args.workers,
                    theorem=args.theorem,
                    limit=args.limit,
                    workdir=workdir,
                    dry_run=args.dry_run,
                    no_resume=args.no_resume,
                )
            except Exception as exc:  # noqa: BLE001 -- Isolate one failed run.
                # Do not catch BaseException: Ctrl-C must stop the pass.
                logging.exception(
                    f"lean_verify_rows[{run}]: verify_run raised "
                    f"{type(exc).__name__}: {exc} -- counting this run as FAILED "
                    "and continuing with the remaining runs."
                )
                n_failed += 1
                continue
            if rc != 0:
                n_failed += 1
        return n_failed

    if args.dry_run:
        return _verify_every_run()

    check_workers(args.workers, Path("/proc/meminfo").read_text())
    with _dojo_cache_lock():
        return _verify_every_run()


if __name__ == "__main__":
    sys.exit(main())
