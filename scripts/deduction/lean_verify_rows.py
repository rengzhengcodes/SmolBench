"""Verify recorded Lean generation rows against real Lean, in a deferred pass.

Phase 2 of the two-phase deduction eval: phase 1 (``run_study.py`` +
``runner`` with a ``NullVerifier``) writes cell rows with ``verdict ==
"unverified"`` and sanity rows with ``"skipped"``. This downloads a run's
``all_rows.jsonl`` from S3, replays every recorded candidate against real
Lean, and uploads the sibling ``verified_rows.jsonl``. S3 decouples the
phases: generation needs only a provider API, verification needs
``elan``/Lean plus the traced mathlib4 corpus (the ``lean`` extra).
``all_rows.jsonl`` is NEVER modified or re-uploaded, so a verification bug
cannot lose a candidate proof that already cost inference spend. Per-decision
rationale (grouping, resume, locking, exit codes) lives on the functions that
implement it, not here.

``lean_interact`` and ``boto3``/``botocore`` import lazily: the module imports
without either, and ``--dry-run`` needs neither Lean nor the lock.
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

import fcntl  # POSIX-only; every host this script runs on is Linux (EC2 / dev boxes).

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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
#: Same bucket every other deduction spool writer/reader in this study uses.
#: The key prefix comes from `spool_prefix()`, read at call time.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
DEFAULT_RUNS_GLOB: str = "scaling_*"
S3_REGION: str = "us-west-2"
ROWS_FILENAME: str = "all_rows.jsonl"
VERIFIED_FILENAME: str = "verified_rows.jsonl"
UPLOAD_EVERY_GROUPS: int = 10
RAM_GB_PER_WORKER: int = 6
DOJO_CACHE_DIR: Path = Path.home() / ".cache" / "lean_dojo"

#: Lock file `_dojo_cache_lock` flocks inside `DOJO_CACHE_DIR` -- a file NEXT TO the
#: cache, never the cache dir itself, which this process's worker threads read/write.
_LOCK_FILENAME = ".smolbench_verify.lock"

_CORPUS_SPLITS: tuple[str, ...] = ("train", "val", "test")

# ---------------------------------------------------------------------------
# Pure: S3 key helpers
# ---------------------------------------------------------------------------
def run_object_key(key_prefix: str, run: str, filename: str) -> str:
    """Build one run's object key ``f"{key_prefix}/{run}/{filename}"``.

    Empty segments are dropped and stray slashes stripped, so the key never
    has a leading or doubled ``"/"`` (`key_prefix` may be ``""``).

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
        The normalized S3 object key.
    """
    segments = (key_prefix.strip("/"), run.strip("/"), filename.strip("/"))
    return "/".join(segment for segment in segments if segment)


# ---------------------------------------------------------------------------
# Pure: grouping, deduplication, fan-out, resume
# ---------------------------------------------------------------------------
def group_unverified(rows: list[dict]) -> dict[tuple[str, int], list[int]]:
    """Group still-unverified cell rows by their ``(theorem_id, k)`` pair.

    That pair is the unit of work: every cell row sharing it can share one
    Dojo session.

    Parameters
    ----------
    rows : list[dict]
        Rows to filter and group.

    Returns
    -------
    dict[tuple[str, int], list[int]]
        ``(theorem_id, k) -> ascending indices into rows``, first-seen key order,
        restricted to ``kind == "cell"`` and ``verdict == "unverified"``.
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

    Lean replay is deterministic, so rows sharing candidate text need exactly
    one ``try_tail`` call. No normalisation: a one-character difference is
    correctly two groups, since Lean need not treat them identically either.

    Parameters
    ----------
    rows : list[dict]
        Rows containing candidate proofs.
    indices : list[int]
        Indices of rows to group.

    Returns
    -------
    dict[str, list[int]]
        Candidate text mapped to row indices; a missing or ``None`` candidate groups under
        ``""``.
    """
    groups: dict[str, list[int]] = {}
    for index in indices:
        candidate = rows[index].get("candidate_proof") or ""
        groups.setdefault(candidate, []).append(index)
    return groups


def fan_out_verdict(rows: list[dict], indices: list[int], result: Mapping[str, Any]) -> None:
    """Apply one verification `result` to every row in `indices`, in place.

    `result` must carry ``verdict``, ``lean_error``, ``final_state_pp`` and
    ``verify_ms``; nothing else on the row is read or written, so `seed` and
    every other recorded field survives untouched.

    Parameters
    ----------
    rows : list[dict]
        Rows updated in place.
    indices : list[int]
        Indices of rows to update.
    result : Mapping[str, Any]
        Verification fields to copy to each row.
    """
    for index in indices:
        row = rows[index]
        row["verdict"] = result["verdict"]
        row["lean_error"] = result["lean_error"]
        row["final_state_pp"] = result["final_state_pp"]
        row["verify_ms"] = result["verify_ms"]


def _group_cell_rows_by_key(rows: list[dict]) -> dict[tuple[str, int], list[dict]]:
    """Group ``kind == "cell"`` `rows` by ``(theorem_id, k)``, in `rows` order.

    Shared by :func:`resume_done_groups` and :func:`verify_run`'s never-measured
    diagnostic, so the two agree on what a "group" is by construction.

    Parameters
    ----------
    rows : list[dict]
        Rows containing cell records.

    Returns
    -------
    dict[tuple[str, int], list[dict]]
        Cell rows grouped by ``(theorem_id, k)``.
    """
    return group_cell_rows(
        (r for r in rows if r.get("kind") == "cell"),
        lambda r: (r["theorem_id"], r["k"]),
    )


def _never_measured(cell_rows: list[dict]) -> bool:
    """True iff every row in `cell_rows` carries a :data:`_NEVER_MEASURED_VERDICTS`
    verdict -- i.e. NOTHING in this group was ever actually tested against Lean,
    as opposed to tested and failed.

    Parameters
    ----------
    cell_rows : list[dict]
        Cell rows in one group.

    Returns
    -------
    bool
        Whether every row has a never-measured verdict.
    """
    return all(row.get("verdict") in _NEVER_MEASURED_VERDICTS for row in cell_rows)


def resume_done_groups(verified_rows: list[dict]) -> set[tuple[str, int]]:
    """Find the ``(theorem_id, k)`` groups a later pass should NOT re-attempt.

    ALL-cells, not ANY: ``all_rows.jsonl`` grows by appending, so a group a
    prior pass finished can gain new sentinel cells, and an ANY rule would
    leave them ``"unverified"`` forever. `verified_rows` must be the PAIRED
    output of :func:`seed_out_rows`, never a prior ``verified_rows.jsonl``
    alone -- a cell phase 1 appended to an already-graded group exists
    nowhere in that file by itself.

    A group counts as done when its cell rows all carry a non-``"unverified"``
    verdict AND are not all in :data:`_NEVER_MEASURED_VERDICTS`
    (:func:`_never_measured`): a group whose REPL session never opened is
    retried, matching phase 1's own resume (`runner._existing_keys` also
    re-runs an exception-only cell). ``"no_answer"`` counts as measured, not
    pending -- there's nothing left to retry for an empty candidate.

    Nothing recorded on a row distinguishes a permanently unopenable theorem
    from a transient REPL hiccup, so such a group is re-attempted on every
    subsequent full pass, forever -- bounded to one REPL-open attempt per
    pending group per pass. See :func:`verify_run`'s never-measured diagnostic.

    Parameters
    ----------
    verified_rows : list[dict]
        Paired output rows from the current and prior passes.

    Returns
    -------
    set[tuple[str, int]]
        Groups a later pass should not re-attempt.
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

    ``row.get`` throughout, so a sanity row (no `model`/`k`/`rung`/`replicate_idx`)
    yields ``None`` there instead of raising. The trailing five fields mirror
    ``runner._row_key`` with `kind` prepended, so a cell and sanity row for one
    theorem never collide.

    Parameters
    ----------
    row : dict
        Row whose identity is extracted.

    Returns
    -------
    tuple
        ``(kind, model, theorem_id, k, rung, replicate_idx)``.
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

    Pairing is by :func:`row_identity` plus occurrence ordinal: a positional
    seed breaks once ``all_rows.jsonl`` grows or reorders between passes, and
    a ``dict[identity] -> row`` map would seed one survivor into every slot of
    an identity real lanes repeat up to 16 times. Matched rows carry over
    wholesale, never field-merged; ``--no-resume`` is the remedy for a
    regenerated lane. Orphans are appended, never inserted or dropped: the
    prefix shared with `rows` stays intact, so indices computed against
    `rows` stay valid against `out_rows`.

    Parameters
    ----------
    rows : list[dict]
        Current-pass rows.
    verified_rows : list[dict]
        Prior verified rows.

    Returns
    -------
    tuple[list[dict], int]
        ``(out_rows, n_orphans)``: for each entry of `rows`, in order, the matching PRIOR row
        at that identity's next unclaimed occurrence, else the current row; then every unmatched
        prior row ("orphan") appended in its original order. This keeps the output's row order
        identical to ``all_rows.jsonl`` regardless of a prior pass's own order or length.
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

    # Orphans = prior rows `rows` never claimed. Sort by ORIGINAL index (not identity
    # or bucket order) so a multi-orphan identity keeps its `verified_rows` order.
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


# ---------------------------------------------------------------------------
# Pure: RAM budget / worker cap
# ---------------------------------------------------------------------------
def available_ram_gb(meminfo_text: str) -> float:
    """Extract ``MemAvailable`` (kB in the file) from ``/proc/meminfo`` TEXT, in GiB.

    Takes the text rather than reading ``/proc`` itself, so the budget math is
    unit-testable against a literal fixture.

    Parameters
    ----------
    meminfo_text : str
        Contents of ``/proc/meminfo``.

    Returns
    -------
    float
        Available RAM in GiB.

    Raises
    ------
    ValueError
        If there is no ``"MemAvailable:"`` line.
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

    Floored quotient, never below 1, so a host under one worker's budget still
    yields a comparable cap :func:`check_workers` can refuse against, not a
    confusing 0.

    Parameters
    ----------
    meminfo_text : str
        Contents of ``/proc/meminfo``.

    Returns
    -------
    int
        RAM-budgeted worker cap.
    """
    return max(int(available_ram_gb(meminfo_text) // RAM_GB_PER_WORKER), 1)


def check_workers(requested: int, meminfo_text: str) -> None:
    """Refuse an oversubscribed (or non-positive) ``--workers`` value up front.

    A Dojo session (live Lean process + loaded environment) costs
    `RAM_GB_PER_WORKER` (6) GiB empirically; oversubscription otherwise fails
    hours in as an OOM kill, not fast.

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


# ---------------------------------------------------------------------------
# Pure: interpreter guard, Dojo-failure operator guidance
# ---------------------------------------------------------------------------
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
    """Exit before any work if ``SMOLBENCH_MATHLIB_ROOT`` does not resolve.

    Without it every session open fails and every cell would be recorded as
    ``replay_failed`` -- a configuration error masquerading as 944 broken
    ground truths.
    """
    from smolbench.deduction.lean.replbackend import mathlib_root  # lazy: import-safe module
    try:
        mathlib_root()
    except RuntimeError as exc:
        raise SystemExit(f"lean_verify_rows: {exc}") from exc


def dojo_failure_hint(exc: BaseException) -> str:
    """Build operator guidance for a session-open-class failure: `exc`'s text plus
    the toolchain/checkout remedies (``replbackend`` has already retried server
    start and imports).

    Parameters
    ----------
    exc : BaseException
        Session-open failure.

    Returns
    -------
    str
        Operator guidance for the failure.
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


# ---------------------------------------------------------------------------
# Theorem corpus lookup (private -- reconstructs what a row cannot carry)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _theorem_index() -> dict[str, BenchmarkTheorem]:
    """Build a ``full_name -> BenchmarkTheorem`` index over the WHOLE local corpus.

    A row records only `theorem_id` (a `full_name`) and `k`, never ``(kind, split)``,
    so every combination is scanned. First-seen wins on a name collision (not expected:
    a declaration belongs to one partition at a time). A combination never bootstrapped
    locally (``FileNotFoundError`` from `load_split`) is skipped, not fatal -- an
    operator may only have bootstrapped the splits they swept. Memoised per process.
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
        If `theorem_id` is in no locally bootstrapped ``(kind, split)`` combination
        (:func:`_theorem_index`).
    """
    index = _theorem_index()
    if theorem_id not in index:
        raise LookupError(
            f"{theorem_id!r} not found in any local (kind, split) combination of "
            "the LeanDojo Benchmark 4 corpus"
        )
    return index[theorem_id]


# ---------------------------------------------------------------------------
# Lazy import seams -- this module must import without lean_interact or boto3
# ---------------------------------------------------------------------------
def _build_s3_client() -> Any:
    """Build a fresh boto3 S3 client bound to `S3_REGION` via ``_aws.fresh_client``.

    A new Session per call (repo convention) picks up a rotated credentials file. THIS
    call, not the top-level ``_aws`` import, is the actual boto3 opt-in.
    """
    return _aws.fresh_client("s3", S3_REGION)


# ---------------------------------------------------------------------------
# Impure: S3 I/O (client is always injected -- real or a test fake)
# ---------------------------------------------------------------------------
def list_runs(
    client: Any, bucket: str, key_prefix: str, pattern: str = DEFAULT_RUNS_GLOB
) -> list[str]:
    """List run directory names directly under `key_prefix`, filtered by `pattern`.

    `pattern` is an `fnmatch` pattern against a run's NAME, not its full key.

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
        Matching ``CommonPrefixes`` names of a ``Delimiter="/"`` listing, all pages,
        sorted ascending.
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

    `dest` is always written the full `body` bytes verbatim -- this function reads,
    it never "repairs" the S3 object or the local copy.

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
        ``[]`` when the object does not exist (NORMAL for a not-yet-created
        ``verified_rows.jsonl``), detected as a ``ClientError`` with ``Error.Code``
        ``"NoSuchKey"`` or ``"404"``; any other S3 failure propagates, since it must
        never read as "nothing to verify yet".
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
    """Serialise `rows` to a scratch file under `workdir`, then upload it to `key`.

    `workdir`'s `VERIFIED_FILENAME` scratch file is rewritten with the full
    row set each call, so repeated checkpoint uploads are safe.

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


# ---------------------------------------------------------------------------
# The Dojo cache lock
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def _dojo_cache_lock() -> Iterator[None]:
    """Hold an exclusive non-blocking flock on `_LOCK_FILENAME` in `DOJO_CACHE_DIR`.

    Acquired once around the whole multi-run loop; concurrent passes would
    otherwise race on the shared traced-repo build cache. Raises SystemExit,
    naming the lock file, if another process already holds it.
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


# ---------------------------------------------------------------------------
# Sanity-row update (private helper)
# ---------------------------------------------------------------------------
def _update_sanity_row(out_rows: list[dict], theorem_id: str, payload: Mapping[str, Any], ms: int) -> None:
    """Update `theorem_id`'s sanity row in `out_rows` in place, appending one if absent.

    Writes `payload`'s required ``verdict``/``tactics_applied``/``tactics_total``/
    ``error`` plus ``ms`` (wall-clock). A fresh row is APPENDED, never inserted, so the
    prefix shared with ``all_rows.jsonl`` never shifts.

    Parameters
    ----------
    out_rows : list[dict]
        Output rows updated in place.
    theorem_id : str
        Theorem identifier for the sanity row.
    payload : Mapping[str, Any]
        Sanity replay fields.
    ms : int
        Wall-clock replay duration in milliseconds.
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


# ---------------------------------------------------------------------------
# Orchestration: one run
# ---------------------------------------------------------------------------
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

    `workdir` is the PARENT of this run's private scratch dir ``workdir / run``.
    `verifier=None` resolves :func:`_default_verifier`, but only once a group
    is pending -- an empty pending set or `dry_run` never imports it.

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
        Parent of this run's private scratch directory ``workdir / run``.
    dry_run : bool, optional
        Whether to preview pending groups without importing the verifier.
    no_resume : bool, optional
        Whether to discard prior verification rows.
    verifier : Any, optional
        Verifier instance; `verifier=None` resolves :func:`_default_verifier`, but only once a
        group is pending -- an empty pending set or `dry_run` never imports it.

    Returns
    -------
    int
        ``0`` on success, including "nothing to do", partial passes (``--limit``,
        ``--theorem``, ``--dry-run``), and a full pass whose only unresolved groups ended
        entirely on :data:`_NEVER_MEASURED_VERDICTS` (that's a separate diagnostic, not folded
        into ``2`` -- see the gate comment in the body for why a corpus-stable population must
        not flip the return code); ``1`` if the run has no ``all_rows.jsonl``; ``2`` if a full
        pass left a cell on the ``"unverified"`` sentinel after its final upload (the output is
        still uploaded -- the gate reports, never withholds).
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
        # Resume is keyed on (theorem_id, k) GROUPS, not candidate text, so a lane
        # phase 1 regenerated looks "done" with different proofs; see --no-resume help.
        logging.warning(
            f"lean_verify_rows[{run}]: --no-resume: discarding {len(verified_rows)} "
            "row(s) from the prior verification pass and re-verifying every group."
        )
        verified_rows = []

    # `out_rows` = `rows`'s shape plus appended orphans, so every index computed
    # below against `rows` (the immutable download) stays valid (see seed_out_rows).
    out_rows, n_orphans = seed_out_rows(rows, verified_rows)
    if n_orphans:
        logging.warning(
            f"lean_verify_rows[{run}]: {n_orphans} row(s) from the prior "
            f"verification pass have no counterpart in {ROWS_FILENAME}; "
            f"appended to the end of {VERIFIED_FILENAME} rather than dropped."
        )

    # Resume is judged on the PAIRED `out_rows` (ALL-cells rule must see cells phase 1
    # appended to a finished group), never on `verified_rows` alone.
    done = resume_done_groups(out_rows)

    # Grouped from `rows`, whose verdicts never change: the COMPLETE set of groups
    # phase 1 ever wrote. Subtracting `done` is what implements resume.
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
        """Do the real work for one ``(theorem_id, k)`` group; `_process_group` nets any escape."""
        lookup_error: Optional[BaseException] = None
        try:
            bt = _lookup_theorem(theorem_id)
        except Exception as exc:  # noqa: BLE001 -- recorded below, not swallowed
            bt = None
            lookup_error = exc

        # Sanity replay once per THEOREM, not per group (memoised under `sanity_lock`).
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
        except Exception as exc:  # noqa: BLE001 -- open_at_step-class failure, recorded below
            message = str(exc)
            if isinstance(exc, RuntimeError) and message.startswith("prefix tactic "):
                # open_at_step's own shape: Dojo opened but the ground-truth PREFIX did
                # not replay -- not infra, so dojo_failure_hint would mislead.
                lean_error = f"{type(exc).__name__}: {exc}"
            else:
                # Dojo never opened (connection/EOF/subprocess, after verify.py's 3x retry).
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

        That function already records every documented failure on its rows, so
        this only catches an unanticipated bug, still landing an "exception"
        verdict on every row of the group and never raising into the executor.

        Parameters
        ----------
        key : tuple[str, int]
            ``(theorem_id, k)`` group key.

        Returns
        -------
        tuple[str, int]
            The processed group key.
        """
        theorem_id, k = key
        try:
            _verify_one_group(theorem_id, k, pending[key])
        except Exception as exc:  # noqa: BLE001 -- last-resort net, see docstring above
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
            future.result()  # `_process_group` never raises -- see its docstring
            completed += 1
            if completed % UPLOAD_EVERY_GROUPS == 0:
                upload_rows(client, out_rows, bucket, verified_key, run_dir)
                logging.info(
                    f"lean_verify_rows[{run}]: checkpoint upload after "
                    f"{completed}/{len(pending)} group(s)."
                )

    # A checkpoint on the last group already uploaded these exact rows.
    if completed % UPLOAD_EVERY_GROUPS:
        upload_rows(client, out_rows, bucket, verified_key, run_dir)
    logging.info(f"lean_verify_rows[{run}]: done -- {completed} group(s) processed.")

    # Full-pass sentinel gate. Only --limit/--theorem/--dry-run make this partial;
    # resume is deliberately not a `full_pass` term, since a `done` group has zero
    # sentinel cells by construction. A surviving sentinel means either a pending
    # group's verdict was never written back, or an ungraded orphan absent from
    # all_rows.jsonl (which `group_unverified` never selects).
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

        # Never-measured diagnostic: deliberately separate from the sentinel gate
        # and does not change the return code. `power_analysis.py` documents
        # "replay_failed" as a stable population across the whole study (every one
        # of 21 models) -- a property of the CORPUS (theorems no REPL session can
        # open), not a symptom of this pass, so it must not flip an otherwise
        # healthy full pass to non-zero on every run, forever.
        # Restricted to `pending` (this pass's attempted groups): an all-never-
        # measured ORPHAN (see seed_out_rows) was never attempted this pass, and
        # the rc=2 gate above already accounts for it separately.
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
    """Entry point: verify every run matching ``--runs`` under ``--s3-prefix``.

    Order: :func:`require_lean_interact`, :func:`check_workers` on a live
    ``/proc/meminfo`` read, the Dojo cache lock held for the rest of the call
    (all three skipped under ``--dry-run``), then :func:`verify_run` per
    :func:`list_runs` match.

    Parameters
    ----------
    argv : Optional[list[str]], optional
        Command-line arguments to parse.

    Returns
    -------
    int
        ``0`` when every matching run was processed (even with nothing to verify); otherwise the
        count of runs that either returned non-zero or raised (`_verify_every_run` isolates each
        run so one lane's exception doesn't abort the runs after it).
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
        """Run :func:`verify_run` over every matched run, isolating one run's failure.

        Each run gets its own try/except, logged and counted as failed, so an
        unattended overnight pass over many lanes doesn't abort on lane 3 and
        leave the rest unchecked.
        """
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
            except Exception as exc:  # noqa: BLE001 -- isolate this run; never abort the pass.
                # `Exception`, not `BaseException`: an operator's Ctrl-C (KeyboardInterrupt)
                # must still stop the whole pass, not be swallowed as a per-run failure.
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
