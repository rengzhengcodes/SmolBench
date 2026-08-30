"""Verify recorded Lean generation rows against real Lean, in a deferred pass.

Phase 2 of the two-phase deduction eval: phase 1 (``notebooks/deduction/run_study.py``
+ ``smolbench.deduction.lean.runner`` with a ``NullVerifier``) writes cell rows with
``verdict == "unverified"`` and per-theorem sanity rows with ``"skipped"``. This script
downloads a run's ``all_rows.jsonl`` from S3, replays every recorded candidate against
real Lean, and uploads the sibling ``verified_rows.jsonl``. S3 decouples the phases:
generation needs only a provider API, verification needs ``elan``/Lean plus the traced
mathlib4 corpus (``.venv`` with the ``lean`` extra). **``all_rows.jsonl`` is NEVER
modified or re-uploaded**, so a verification bug can never lose a candidate proof that
already cost inference spend.

- Unit of work is a ``(theorem_id, k)`` group: ``verify.open_at_step`` replays the
  prefix ``0..k-1`` once into a Dojo session every rung/model/replicate at that pair
  reuses, and identical ``candidate_proof`` text within a group collapses to one
  ``try_tail`` call, fanned back out.
- Ground-truth sanity replay is memoised per THEOREM per run, under a shared lock:
  identical to per-group memoisation under this repo's configured
  ``k.strategy == "last"`` (``runner._k_indices``), strictly cheaper otherwise. A row
  carries no ``(kind, split)``, so ``_lookup_theorem`` rebuilds its
  ``BenchmarkTheorem`` by scanning the whole local corpus.
- ``verified_rows.jsonl``'s row order is EXACTLY ``all_rows.jsonl``'s -- a hard
  downstream invariant upheld by :func:`seed_out_rows`; orphans are appended, never
  inserted. Resume is :func:`resume_done_groups`'s ALL-cells rule, evaluated against
  the PAIRED output and never a prior ``verified_rows.jsonl`` alone, and progress
  check-points every :data:`UPLOAD_EVERY_GROUPS` groups plus once at the end.
- :func:`verify_run` returns 1 for a run with no ``all_rows.jsonl``, and 2 when a FULL
  pass (no ``--limit``/``--theorem``) leaves a cell on the ``"unverified"`` sentinel:
  downstream loaders score such a cell as a failure, so a work-free pass would read as
  "the model proved nothing".
- ``--dry-run`` skips :func:`require_lean_dojo`, :func:`check_workers` and the Dojo
  cache flock, which guard real Lean work only; requiring them would fail a low-memory
  preview host, or block a dry run alongside a live pass.
- Two lazy import seams keep this module importable without ``lean_dojo``:
  ``smolbench.deduction.lean.verify`` (:func:`_default_verifier`) and
  ``boto3``/``botocore`` (house convention -- importing never requires the AWS SDK).
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
from smolbench.evals import _aws

logging.basicConfig(level=logging.INFO)

_error_code = _aws.error_code


# ---------------------------------------------------------------------------
# Constants (exact names/values -- pinned by the caller's test suite)
# ---------------------------------------------------------------------------
DEFAULT_S3_PREFIX: str = "s3://smolbench-results-414266451290/deduction/runs"
DEFAULT_RUNS_GLOB: str = "scaling_*"
S3_REGION: str = "us-west-2"
ROWS_FILENAME: str = "all_rows.jsonl"
VERIFIED_FILENAME: str = "verified_rows.jsonl"
UPLOAD_EVERY_GROUPS: int = 10
RAM_GB_PER_WORKER: int = 6
DOJO_CACHE_DIR: Path = Path.home() / ".cache" / "lean_dojo"

#: Basename of the dedicated lock file `_dojo_cache_lock` acquires inside
#: `DOJO_CACHE_DIR`. See the module docstring's "The Dojo cache lock"
#: section for why this is a file next to the cache, never the cache
#: directory itself.
_LOCK_FILENAME = ".smolbench_verify.lock"

#: Every `(kind, split)` combination `smolbench.deduction.lean.corpus`
#: defines (see that module's `SplitKind`/`Split` literals). This is the
#: full search space `_lookup_theorem` scans, since a row carries no
#: `kind`/`split` of its own.
_CORPUS_KINDS: tuple[str, ...] = ("random", "novel_premises")
_CORPUS_SPLITS: tuple[str, ...] = ("train", "val", "test")


# ---------------------------------------------------------------------------
# Pure: S3 URI / key helpers
# ---------------------------------------------------------------------------
def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an ``s3://bucket[/key-prefix]`` URI into ``(bucket, key_prefix)``.

    `key_prefix` has any trailing ``"/"`` stripped, and is ``""`` for a bare
    ``s3://bucket``. Raises ``ValueError``, naming `uri`, if it does not start with
    ``"s3://"`` or its bucket segment (everything up to the next ``"/"``) is empty.
    """
    if not uri.startswith("s3://"):
        raise ValueError(f"parse_s3_uri: {uri!r} does not start with 's3://'")
    rest = uri[len("s3://"):]
    bucket, _, key_prefix = rest.partition("/")
    if not bucket:
        raise ValueError(f"parse_s3_uri: {uri!r} has an empty bucket")
    return bucket, key_prefix.rstrip("/")


def run_object_key(key_prefix: str, run: str, filename: str) -> str:
    """Build one run's object key under a bucket's key prefix:
    ``f"{key_prefix}/{run}/{filename}"`` with empty segments dropped and stray slashes
    stripped, so the result never has a leading or a doubled ``"/"`` (`key_prefix` may
    be ``""`` -- see :func:`parse_s3_uri`).
    """
    segments = (key_prefix.strip("/"), run.strip("/"), filename.strip("/"))
    return "/".join(segment for segment in segments if segment)


# ---------------------------------------------------------------------------
# Pure: grouping, deduplication, fan-out, resume
# ---------------------------------------------------------------------------
def group_unverified(rows: list[dict]) -> dict[tuple[str, int], list[int]]:
    """Group still-unverified cell rows by their ``(theorem_id, k)`` pair -- the unit
    of work, since every cell row sharing it can share one Dojo session.

    `rows` are ``all_rows.jsonl``'s rows in file order. Returns
    ``(theorem_id, int(k))`` -> ascending indices into `rows`, for rows with
    ``kind == "cell"`` AND ``verdict == "unverified"`` only, in first-seen key order.
    ``k`` is coerced with ``int()`` to tolerate a string-typed value from a
    hand-edited fixture.
    """
    groups: dict[tuple[str, int], list[int]] = {}
    for index, row in enumerate(rows):
        if row.get("kind") != "cell":
            continue
        if row.get("verdict") != "unverified":
            continue
        key = (row["theorem_id"], int(row["k"]))
        groups.setdefault(key, []).append(index)
    return groups


def unique_candidates(rows: list[dict], indices: list[int]) -> dict[str, list[int]]:
    """Group `indices` (typically one :func:`group_unverified` value) by their exact
    ``candidate_proof`` text.

    Lean replay is deterministic, so rows sharing candidate text need exactly one
    ``try_tail`` call. No normalisation is applied: a one-character difference is
    correctly two groups, since Lean need not treat them identically either. Returns
    each distinct candidate -> its indices in the order given, first-seen key order; a
    missing or ``None`` candidate groups under ``""``.
    """
    groups: dict[str, list[int]] = {}
    for index in indices:
        candidate = rows[index].get("candidate_proof") or ""
        groups.setdefault(candidate, []).append(index)
    return groups


def fan_out_verdict(rows: list[dict], indices: list[int], result: Mapping[str, Any]) -> None:
    """Apply one verification `result` to every row in `indices`, in place.

    Sets ``verdict``, ``lean_error``, ``final_state_pp`` and ``verify_ms`` (all
    required keys of `result`) on each row. No other key is read or written, so `seed`
    and every other recorded field survive untouched.
    """
    for index in indices:
        row = rows[index]
        row["verdict"] = result["verdict"]
        row["lean_error"] = result["lean_error"]
        row["final_state_pp"] = result["final_state_pp"]
        row["verify_ms"] = result["verify_ms"]


def resume_done_groups(verified_rows: list[dict]) -> set[tuple[str, int]]:
    """Find the ``(theorem_id, k)`` groups where every cell row is fully graded.

    `verified_rows` must be the PAIRED output of :func:`seed_out_rows`, never a prior
    ``verified_rows.jsonl`` in isolation: a cell phase 1 appended to an already-graded
    group exists nowhere in that file by itself. Returns every
    ``(theorem_id, int(k))`` whose ``kind == "cell"`` rows ALL carry a
    non-``"unverified"`` verdict; non-cell rows are ignored and can never make a group
    done, and ``k`` is coerced with ``int()`` to tolerate a string-typed value from a
    hand-edited fixture.

    The ALL-cells rule (rather than ANY) is what holds ACROSS passes:
    ``all_rows.jsonl`` grows by appending, so a group a prior pass finished can gain
    new sentinel cells, and an ANY rule would leave them ``"unverified"`` forever.
    """
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in verified_rows:
        if row.get("kind") != "cell":
            continue
        key = (row["theorem_id"], int(row["k"]))
        groups.setdefault(key, []).append(row)

    return {
        key
        for key, cell_rows in groups.items()
        if all(row.get("verdict") != "unverified" for row in cell_rows)
    }


def row_identity(row: dict) -> tuple:
    """Extract a row's identity: ``(kind, model, theorem_id, k, rung, replicate_idx)``.

    Every field is read via ``row.get``, so a sanity row -- which carries no
    `model`/`k`/`rung`/`replicate_idx` -- still yields a well-formed key with ``None``
    in those slots instead of raising. The trailing five fields mirror
    ``runner._row_key`` exactly, with `kind` prepended, so a cell row and a sanity row
    for the same `theorem_id` can never collide. `k` is read RAW here, unlike
    :func:`resume_done_groups`'s ``int()`` coercion: both files are written by the same
    writer, and a hand-edited string-typed `k` would merely fail to pair (surfacing as
    an orphan plus a redundant re-verification), never mis-assign a verdict.
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

    This is what keeps the output's row order identical to ``all_rows.jsonl``, whatever
    order or length a prior pass's own output had. `rows` is the freshly downloaded
    ``all_rows.jsonl`` in file order; `verified_rows` is a prior
    ``verified_rows.jsonl`` in that file's own order (``[]`` on a first pass, or under
    ``--no-resume``). Returns ``(out_rows, n_orphans)``: for each entry of `rows`, in
    order, the matching PRIOR row object at that identity's next unclaimed occurrence
    else the current row itself, then every unmatched prior row (an "orphan") appended
    in its original order.

    Pairing is by :func:`row_identity` plus occurrence ordinal, never by list position
    -- a positional seed raises ``IndexError`` once ``all_rows.jsonl`` grows between
    passes, and mis-pairs silently once the two lists merely differ in order -- and
    never through a ``dict[identity] -> row`` map, because repeated identities are the
    norm here: real lanes carry up to 16 occurrences of one identity, and a map would
    seed the single survivor into every one of that identity's slots. Matched rows are
    carried over WHOLESALE, never field-merged; ``--no-resume`` is the remedy for a
    regenerated lane.

    Orphans are APPENDED, never inserted and never dropped. Appending keeps the prefix
    shared with `rows` intact, which keeps every index computed against `rows`
    (:func:`group_unverified`, hence every :func:`fan_out_verdict` /
    :func:`unique_candidates` call) valid against `out_rows`. Dropping them is never
    safe: :func:`_update_sanity_row` legitimately appends a sanity row for a theorem
    ``all_rows.jsonl`` has none for, and on the next pass that row has no counterpart
    there at all.
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

    # Flatten whatever every bucket still holds: prior rows `rows` never
    # claimed. Sort by ORIGINAL index, not by identity and not by insertion
    # order across different identities. A multi-orphan identity's own
    # relative order then survives the reseed exactly as it was in
    # `verified_rows`.
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
    """Extract ``MemAvailable`` (kB in the file) from a ``/proc/meminfo`` file's TEXT,
    returned in GiB.

    Takes the text rather than reading ``/proc`` itself, so the budget math is
    unit-testable against a literal fixture. Raises ``ValueError`` if `meminfo_text`
    has no line starting with ``"MemAvailable:"``.
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
    """Cap worker count by available RAM at `RAM_GB_PER_WORKER` GiB each: the floored
    quotient, but never below 1, so a host under one worker's budget still yields a
    comparable cap :func:`check_workers` can refuse against rather than a confusing 0.
    """
    return max(int(available_ram_gb(meminfo_text) // RAM_GB_PER_WORKER), 1)


def check_workers(requested: int, meminfo_text: str) -> None:
    """Refuse an oversubscribed (or non-positive) ``--workers`` value up front.

    Each Dojo session holds a live Lean process plus its fully loaded environment --
    `RAM_GB_PER_WORKER` (6) GiB empirically. Oversubscribing does not fail fast: it
    fails hours into a pass, as an OOM kill that takes every in-flight row down with
    it. Raises ``SystemExit`` -- naming `requested`, the computed cap and the observed
    available RAM -- if `requested` is below 1 or exceeds :func:`max_workers_allowed`,
    before a single worker thread or Dojo session exists.
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
def require_lean_dojo() -> None:
    """Raise ``SystemExit`` if ``lean_dojo`` (the ``lean`` extra) is not importable in
    this interpreter.
    """
    if importlib.util.find_spec("lean_dojo") is None:
        raise SystemExit(
            "lean_verify_rows: this is the deferred VERIFICATION pass and needs "
            "'lean_dojo' (the `lean` extra). Install it into the project venv "
            "with `uv sync --all-extras` and re-run via .venv/bin/python. "
            "(--dry-run works without it if you only need to preview the plan.)"
        )


def dojo_failure_hint(exc: BaseException) -> str:
    """Build actionable operator guidance for a Dojo-init-class failure.

    Returns `exc`'s own text plus guidance grounded in this pipeline: ``verify.py``'s
    ``_open_dojo_with_retry`` already retried 3x with backoff before `exc` surfaced;
    the FIRST Dojo call on a host pulls a ~2.4 GB traced corpus from LeanDojo's S3
    cache into `DOJO_CACHE_DIR`, credential-free (cold ~2-4 min, warm ~10s), which
    needs ``elan`` installed; a corrupt or partial cache is cleared by removing
    `DOJO_CACHE_DIR` entirely. The text points at
    ``.claude/skills/run-smolbench/SKILL.md`` for the pull timings and the ``elan``
    install command.
    """
    return (
        f"Dojo failed to open: {type(exc).__name__}: {exc}\n"
        "This is usually infrastructure, not a broken candidate proof. "
        "verify.py's _open_dojo_with_retry already retried 3x with backoff "
        "(5s / 15s / 45s) before this surfaced. The FIRST Dojo call on a fresh "
        f"host pulls a ~2.4 GB traced corpus from LeanDojo's S3 cache into "
        f"{DOJO_CACHE_DIR} (credential-free; cold ~2-4 min, warm ~10s) -- confirm "
        "'elan' is installed (curl -sSf "
        "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | "
        "sh -s -- -y --default-toolchain none) and that a prior pull actually "
        f"completed. If the cache looks corrupt or partial, remove {DOJO_CACHE_DIR} "
        "entirely and let the next run refetch it from scratch. See "
        ".claude/skills/run-smolbench/SKILL.md for the documented cache-pull "
        "timings."
    )


# ---------------------------------------------------------------------------
# Theorem corpus lookup (private -- reconstructs what a row cannot carry)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _theorem_index() -> dict[str, BenchmarkTheorem]:
    """Build a ``full_name -> BenchmarkTheorem`` index over the WHOLE local corpus.

    A row records only `theorem_id` (a `full_name`) and `k`, never its
    ``(kind, split)``, so scanning every combination
    ``smolbench.deduction.lean.corpus`` defines is the only correct lookup. First-seen
    wins on a name collision -- not expected in practice, since a mathlib4 declaration
    belongs to one ``random``/``novel_premises`` partition at a time. A combination
    whose dataset file was never bootstrapped locally (``FileNotFoundError`` from
    `load_split`) is skipped, not fatal: an operator may only have bootstrapped the
    splits they actually swept. Memoised for the life of the process, over
    ``lru_cache``-memoised `load_split` calls, so no file is read twice.
    """
    index: dict[str, BenchmarkTheorem] = {}
    for kind in _CORPUS_KINDS:
        for split in _CORPUS_SPLITS:
            try:
                theorems = load_split(kind, split)  # type: ignore[arg-type]
            except FileNotFoundError:
                continue
            for theorem in theorems:
                index.setdefault(theorem.full_name, theorem)
    return index


def _lookup_theorem(theorem_id: str) -> BenchmarkTheorem:
    """Resolve a row's `theorem_id` (== ``BenchmarkTheorem.full_name``) to its theorem.

    The result carries the traced-tactic prefix `open_at_step` needs and the
    ``url``/``commit`` LeanDojo needs to address it. Raises ``LookupError`` if
    `theorem_id` is in no locally bootstrapped ``(kind, split)`` combination -- see
    :func:`_theorem_index`.
    """
    index = _theorem_index()
    if theorem_id not in index:
        raise LookupError(
            f"{theorem_id!r} not found in any local (kind, split) combination of "
            "the LeanDojo Benchmark 4 corpus"
        )
    return index[theorem_id]


# ---------------------------------------------------------------------------
# Lazy import seams (see the module docstring's "Import-safety" section)
# ---------------------------------------------------------------------------
def _default_verifier():
    """Lazily import and return ``smolbench.deduction.lean.verify``, which exposes
    `open_at_step`, `try_tail` and `replay_ground_truth`.

    That module requires `lean_dojo`, so the import is deferred to call time -- the
    same seam ``runner._default_verifier`` uses -- and its `ImportError` propagates
    when the ``lean`` extra is absent.
    """
    from smolbench.deduction.lean import verify

    return verify


def _build_s3_client() -> Any:
    """Build a fresh boto3 S3 client bound to `S3_REGION`, via ``_aws.fresh_client``.

    That builds a brand-new boto3 Session per call (repo convention), so a rotated
    credentials file is picked up rather than silently signed with a stale one. THIS
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

    `client` need only expose ``get_paginator("list_objects_v2")``; `key_prefix` -- the
    prefix under which each run's own sub-prefix lives -- may be ``""``; `pattern` is
    an `fnmatch` pattern matched against a run's NAME, not its full key. Returns the
    matching ``CommonPrefixes`` names of one ``Delimiter="/"`` listing, across every
    page, sorted ascending.
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
    """Download one JSONL object to `dest` and return its parsed rows.

    Returns one `json.loads`-parsed dict per non-blank line, in file order, and ``[]``
    when the object does not exist -- absence is NORMAL for a not-yet-created
    ``verified_rows.jsonl``, and is detected as a ``ClientError`` whose ``Error.Code``
    is ``"NoSuchKey"`` or ``"404"`` (the two shapes boto3 and this repo's fakes raise;
    see ``tests/evals/test_results_store.py``'s ``FakeS3Client``). Every other S3
    failure (permissions, malformed bucket, ...) propagates unhandled: it must never be
    read as "nothing to verify yet". `dest`'s parent directories are created as needed.
    """
    from botocore.exceptions import ClientError  # lazy -- see module docstring

    try:
        obj = client.get_object(Bucket=bucket, Key=key)
    except ClientError as err:
        if _error_code(err) in ("NoSuchKey", "404"):
            return []
        raise
    body = obj["Body"].read()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)

    rows: list[dict] = []
    for line in body.decode("utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def upload_rows(client: Any, rows: list[dict], bucket: str, key: str, workdir: Path) -> None:
    """Serialise `rows` to a scratch file under `workdir`, then upload it to `key`.

    `workdir` is created if absent, and its scratch file (named `VERIFIED_FILENAME`) is
    overwritten with the full current row set on every call, so :func:`verify_run`'s
    repeated checkpoint uploads against one `workdir` are safe.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    scratch = workdir / VERIFIED_FILENAME
    with scratch.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    client.upload_file(str(scratch), bucket, key)


# ---------------------------------------------------------------------------
# The Dojo cache lock (see the module docstring's "The Dojo cache lock" section)
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def _dojo_cache_lock() -> Iterator[None]:
    """Hold an exclusive, non-blocking flock on a dedicated file inside
    `DOJO_CACHE_DIR`.

    Acquired once and held for the process's remaining life (the caller wraps the whole
    multi-run loop), released however the block exits; concurrent verification passes
    would otherwise race on the shared traced-repo build cache. The lock is on a
    DEDICATED FILE, never `DOJO_CACHE_DIR` itself, which one process's own worker
    threads read and write concurrently. Raises ``SystemExit``, naming the lock file,
    when another process already holds it (``BlockingIOError`` from the non-blocking
    `fcntl.flock`).
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
# Sanity-row update (private helper -- shared by the fresh-row and
# append-new-row cases described in the module docstring)
# ---------------------------------------------------------------------------
def _update_sanity_row(out_rows: list[dict], theorem_id: str, payload: Mapping[str, Any], ms: int) -> None:
    """Update `theorem_id`'s sanity row in `out_rows` in place, appending one if absent.

    Overwrites an existing ``kind == "sanity"`` row's ``verdict``, ``tactics_applied``,
    ``tactics_total`` and ``error`` (all required keys of `payload`) plus ``ms`` (from
    `ms`, wall-clock milliseconds). Otherwise a fresh sanity row is APPENDED to the end
    of `out_rows` -- never inserted -- so the prefix shared with ``all_rows.jsonl``
    never shifts.
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

    `client` is an injected S3 client (real, or a test fake) and `bucket`/`key_prefix`
    locate this run's objects -- see :func:`run_object_key`. `workers` sizes the
    `ThreadPoolExecutor`, one ``(theorem_id, k)`` group per task. `theorem` restricts
    processing to groups with that `theorem_id`; `limit` caps groups processed THIS
    call (0 = no cap); `dry_run` reports the selected groups and returns, touching
    neither Lean nor the S3 upload machinery. `workdir` is the PARENT of this run's
    private scratch dir ``workdir / run``, never shared with another run's scratch
    files. `verifier` is a module exposing `open_at_step`, `try_tail` and
    `replay_ground_truth`; ``None`` resolves the real one via
    :func:`_default_verifier`, but ONLY when at least one group is pending -- an empty
    pending set, or `dry_run`, never imports it.

    Returns ``0`` on success, including "nothing to do" and every partial pass
    (``--limit``, ``--theorem``, ``--dry-run``); ``1`` if this run has no
    ``all_rows.jsonl`` (logged, run skipped); ``2`` if a FULL pass still left at least
    one ``kind == "cell"`` row on the ``"unverified"`` sentinel after its final upload.
    Resume is not an exemption: a `done` group has zero sentinel cells by construction,
    so a survivor means either a pending group's verdict was never written back (a
    swallowed per-cell failure) or an ungraded ORPHAN absent from the current
    ``all_rows.jsonl``, which :func:`group_unverified` can never select. Downstream
    loaders score an ``"unverified"`` cell as a failure, so such a pass would read as
    "the model proved nothing". The graded output is uploaded either way: this gates
    the RESULT, it is never a reason to withhold it.
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
        # Verify every group again from the CURRENT all_rows.jsonl. Discard
        # the prior pass's verdicts.
        #
        # This is needed because resume is keyed on (theorem_id, k) GROUPS,
        # not on the candidate proofs inside them. If phase 1 regenerated a
        # lane after a verification pass, every group still looks "done"
        # while the proofs under it are completely different. The pass then
        # reports success, verifies nothing, and leaves verified_rows.jsonl
        # describing text that no longer exists.
        #
        # The caller is responsible for archiving the superseded
        # verified_rows.jsonl first. This flag overwrites it.
        logging.warning(
            f"lean_verify_rows[{run}]: --no-resume: discarding {len(verified_rows)} "
            "row(s) from the prior verification pass and re-verifying every group."
        )
        verified_rows = []

    # Seed the OUTPUT row list by IDENTITY plus occurrence ordinal, never by
    # list position -- see :func:`seed_out_rows` and the module docstring's
    # "content invariant" section. `out_rows` always has exactly `rows`'s
    # shape (plus any appended orphans). Every index computed below against
    # `rows` (the immutable all_rows.jsonl download) therefore stays valid
    # against it, regardless of what length or order a prior pass's own
    # output happened to have. An orphaned prior row -- one with no
    # counterpart anywhere in the current `rows` -- is kept, not dropped.
    # See :func:`seed_out_rows`'s docstring for the real (not hypothetical)
    # shape that produces one.
    out_rows, n_orphans = seed_out_rows(rows, verified_rows)
    if n_orphans:
        logging.warning(
            f"lean_verify_rows[{run}]: {n_orphans} row(s) from the prior "
            f"verification pass have no counterpart in {ROWS_FILENAME}; "
            f"appended to the end of {VERIFIED_FILENAME} rather than dropped."
        )

    # Resume completeness is evaluated against the PAIRED `out_rows`, never
    # against `verified_rows` in isolation. `resume_done_groups`'s ALL-cells
    # rule needs to see every CURRENT cell of a group, including one phase 1
    # appended to a group a prior pass already finished. That cell exists
    # nowhere in `verified_rows` by itself, so evaluating completeness
    # against that file alone can never see it. See the module docstring's
    # "Resume and checkpointing" section.
    done = resume_done_groups(out_rows)

    # `group_unverified` runs against `rows` (the immutable source), NOT
    # `out_rows`. all_rows.jsonl's cell verdicts never change, so this
    # always returns the COMPLETE set of every group phase 1 ever wrote.
    # `done` (above) is what actually implements resume, subtracted next.
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
        """Do the real work for one ``(theorem_id, k)`` group; never raises -- see
        `_process_group`.
        """
        lookup_error: Optional[BaseException] = None
        try:
            bt = _lookup_theorem(theorem_id)
        except Exception as exc:  # noqa: BLE001 -- recorded below, not swallowed
            bt = None
            lookup_error = exc

        # Sanity gate: replay the full ground-truth proof once per THEOREM,
        # not once per group. See the module docstring's "Sanity replay"
        # design note for why this refinement is correct.
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
                # Dojo opened fine. The recorded ground-truth PREFIX itself
                # did not replay as expected (open_at_step's own explicit
                # RuntimeError shape). This is not a Dojo/cache infra
                # problem, so dojo_failure_hint's guidance would mislead.
                # Leave the message as-is.
                lean_error = f"{type(exc).__name__}: {exc}"
            else:
                # Dojo itself never opened: a connection/EOF/subprocess
                # failure, even after verify.py's own 3x retry. Give
                # actionable infra guidance.
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
        """Executor entry point: last-resort safety net around `_verify_one_group`.

        That function already maps every documented failure onto a row
        (open_at_step-class -> "replay_failed", try_tail-class -> "exception", lookup
        failure -> "replay_failed"), so this catch-all exists only for a genuinely
        unanticipated bug, e.g. a malformed row missing an expected key. It still lands
        an "exception" verdict on every row in the group, per this file's "never
        swallow an exception without recording it on a row" contract, rather than
        silently killing the worker thread.
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

    upload_rows(client, out_rows, bucket, verified_key, run_dir)
    logging.info(f"lean_verify_rows[{run}]: done -- {completed} group(s) processed, final upload.")

    # Full-pass sentinel gate. Three flags ask for PARTIAL work:
    # --limit, --theorem, --dry-run (the last already returned above). These
    # are the only legitimate ways to leave a cell row ungraded. Resume is
    # deliberately NOT among them. Under the ALL-cells rule above,
    # `resume_done_groups` puts a (theorem_id, k) pair into `done` only once
    # EVERY one of its cell rows already carries a non-"unverified" verdict,
    # so a done group holds zero sentinel cells by construction. Every group
    # `group_unverified` marks pending gets graded this pass (see
    # `_verify_one_group`'s fan-out).
    #
    # So on a pass with no --limit and no --theorem, there is no legitimate
    # state -- resumed or not -- in which a sentinel survives. A `not done`
    # term here would silence the gate in precisely the scenario that
    # motivated it: a RESUMED completion pass over a partially-verified
    # file, where `done` is non-empty by design. A sentinel surviving
    # anyway means one of two faults, both alarm-worthy:
    #   - a pending group was "verified" but the verdict written back is
    #     still the sentinel (a no-op or swallowed per-cell failure); or
    #   - a sentinel-carrying ORPHAN -- an ungraded prior row with no
    #     counterpart in the current all_rows.jsonl. `group_unverified`
    #     reads all_rows, so an orphan is never pending and never gets
    #     graded; without this gate it sits in the output as a silently
    #     failure-scored cell forever.
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
            "alongside each run's all_rows.jsonl in S3. Requires lean_dojo "
            "installed (uv sync --all-extras) except under --dry-run."
        ),
    )
    parser.add_argument(
        "--s3-prefix", default=DEFAULT_S3_PREFIX,
        help=f"s3://bucket/key-prefix under which every run lives (default: {DEFAULT_S3_PREFIX})",
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

    Step order: :func:`require_lean_dojo`, then :func:`check_workers` against a live
    ``/proc/meminfo`` read, then the exclusive Dojo cache lock held for the rest of the
    call -- all three skipped together under ``--dry-run`` -- then :func:`list_runs`
    and :func:`verify_run` per matching run. `argv` defaults to ``sys.argv[1:]``.

    Returns ``0`` when every matching run was found and processed, even if a run had
    nothing left to verify; otherwise the COUNT of runs :func:`verify_run` returned
    non-zero for.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.dry_run:
        require_lean_dojo()

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="lean_verify_rows_"))
    workdir.mkdir(parents=True, exist_ok=True)

    bucket, key_prefix = parse_s3_uri(args.s3_prefix)
    client = _build_s3_client()
    runs = list_runs(client, bucket, key_prefix, args.runs)
    if not runs:
        logging.warning(
            f"lean_verify_rows: no runs under s3://{bucket}/{key_prefix} matched "
            f"{args.runs!r}."
        )
        return 0

    def _verify_every_run() -> int:
        n_failed = 0
        for run in runs:
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
