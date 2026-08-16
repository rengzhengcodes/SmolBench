"""Deferred VERIFICATION pass over Lean generation rows already collected in S3.

Two-phase split
---------------
Phase 1 (``notebooks/deduction/run_study.py`` / ``smolbench.deduction.lean.runner``,
already built, not touched by this file) runs GENERATION on the main
``.venv`` (Python 3.14) with a ``NullVerifier``: it calls a model, extracts a
candidate tactic block, and writes a cell row whose ``verdict`` is the
placeholder ``"unverified"`` and a per-theorem sanity row whose ``verdict``
is ``"skipped"`` -- neither is ever actually checked against Lean, because
``lean_dojo`` (the real verifier's dependency) pins ``python<3.13`` and
cannot live on the main venv (see ``smolbench/deduction/lean/verify.py``'s
import guard).

THIS file is phase 2. It runs on ``.venv-lean`` (Python 3.12, where
``lean_dojo`` is installed), downloads a run's ``all_rows.jsonl`` from S3,
replays every recorded candidate proof against real Lean, and uploads
``verified_rows.jsonl`` beside it. The two phases are decoupled entirely
through S3: generation can run anywhere with network access to a provider
API; verification needs a box with ``elan``/Lean toolchains and the traced
mathlib4 corpus, which is why splitting them this way (rather than requiring
every generation box to also carry ``.venv-lean``) is the whole point.

**The original ``all_rows.jsonl`` object is NEVER modified or re-uploaded.**
Every write this script makes goes to the sibling ``verified_rows.jsonl``
key -- the source-of-truth generation record stays exactly as phase 1 left
it, forever, so a verification bug can never corrupt or lose a candidate
proof that already cost real inference spend to collect.

Grouping and deduplication -- why (theorem_id, k), and why unique candidates
-----------------------------------------------------------------------------
``smolbench.deduction.lean.verify.open_at_step`` replays a theorem's recorded
tactic prefix ``0..k-1`` ONCE and yields a reusable Dojo session; many
``try_tail`` calls can then branch from that same checkpoint without
re-replaying the prefix (see that function's own docstring). Every cell row
sharing a ``(theorem_id, k)`` -- across every rung, model, and replicate --
can therefore share exactly one Dojo session, which is why
:func:`group_unverified` groups on that pair rather than on a full row key.
Within one group, many rows can additionally share the exact same
``candidate_proof`` string (the same model/rung emitting identical text
across replicates, or two different rungs happening to converge on the
same tail) -- Lean replay is deterministic, so :func:`unique_candidates`
collapses those to one real ``try_tail`` call, fanned back out to every row
that shares the text via :func:`fan_out_verdict`. On a run with heavy
duplication this is the difference between opening a Lean process per row
and opening one per distinct candidate.

Sanity replay: memoised per THEOREM, not per group (an approved refinement)
-----------------------------------------------------------------------------
The originating brief asked for "one sanity replay per group". This file
instead memoises ``replay_ground_truth`` per THEOREM, once per run, guarded
by a lock shared across every worker thread. Whenever the sweep's
``k.strategy`` is ``"last"`` (the configured case throughout this repo --
see ``smolbench.deduction.lean.runner._k_indices``) each theorem contributes
exactly one ``(theorem, k)`` group, so per-theorem and per-group
memoisation are IDENTICAL. Under any other k-strategy (``"first"``,
``"all"``) a theorem can contribute several groups, and per-theorem
memoisation is then STRICTLY CHEAPER -- the ground truth does not depend on
``k``, so replaying it once per theorem rather than once per (theorem, k)
avoids redundant, expensive Lean sessions with no loss of information. This
refinement was reviewed and approved before implementation.

Theorem lookup: rows do not carry enough to rebuild a BenchmarkTheorem
-----------------------------------------------------------------------
A cell row records ``theorem_id`` (the theorem's ``full_name``) and ``k``,
but NOT the theorem's traced-tactic PREFIX (``0..k-1``) that
``open_at_step`` needs to replay, nor the ``url``/``commit`` LeanDojo needs
to address it -- those never round-tripped through phase 1's row schema.
The only place that information still lives is the local LeanDojo Benchmark
4 corpus (``smolbench.deduction.lean.corpus``). :func:`_lookup_theorem`
resolves ``theorem_id`` back to its full ``BenchmarkTheorem`` by building a
``full_name -> BenchmarkTheorem`` index across every ``(kind, split)``
combination the corpus module defines (``random``/``novel_premises`` x
``train``/``val``/``test``) -- rows carry no ``kind``/``split`` of their
own, so searching the full Cartesian product (six files, each already
memoised by ``corpus.load_split``'s own ``lru_cache``) is the only
correct, general lookup that does not assume which split a theorem came
from. A ``(kind, split)`` combination whose dataset file was never
bootstrapped locally is skipped, not fatal -- see that function's docstring.

RAM budget and the worker cap
------------------------------
Each Dojo session holds a live Lean process plus its fully loaded
environment; empirically that costs about ``RAM_GB_PER_WORKER`` (6) GiB.
Oversubscribing ``--workers`` past what the host can actually hold does not
fail fast -- it fails hours into a pass, as an OOM kill that takes the whole
process (and every in-flight row) down with it. :func:`check_workers`
refuses up front instead, reading ``/proc/meminfo`` once in ``main`` and
passing its TEXT through a pure parser (:func:`available_ram_gb`) so the
budget math is fully unit-testable without a real ``/proc`` file.

The Dojo cache lock
--------------------
The first Dojo call on a box pulls (or reuses) a shared traced-repo BUILD
CACHE under ``DOJO_CACHE_DIR`` (``~/.cache/lean_dojo/``) -- see
``.claude/skills/run-smolbench/SKILL.md`` for the documented pull timings.
Two verification passes running concurrently on the same box race on that
shared cache (a half-written build directory read by a second process is
exactly the kind of transient failure ``verify.py``'s own
``_open_dojo_with_retry`` exists to paper over, not eliminate). This script
acquires an EXCLUSIVE, non-blocking ``fcntl.flock`` on a dedicated lock FILE
(``DOJO_CACHE_DIR / ".smolbench_verify.lock"`` -- never the cache directory
itself, which real Dojo runs read and write concurrently within a single
process's own worker threads) before touching any run, and holds it for the
rest of the process's life. A second concurrent invocation gets an
immediate, actionable ``SystemExit`` rather than a wedged wait or a
corrupted cache.

``--dry-run``'s exemptions (a documented, deliberate deviation)
-------------------------------------------------------------------
:func:`require_py312` is EXPLICITLY exempted under ``--dry-run`` per the
originating brief, specifically so an operator can inspect the verification
plan from the main venv (``.venv``, Python 3.14) without first building
``.venv-lean``. This file extends that same exemption to
:func:`check_workers` and the Dojo cache flock: both exist ONLY to protect
against real Dojo/Lean work (an oversubscribed worker pool, a racing build
cache) that ``--dry-run`` never performs -- it lists groups and exits before
ever resolving a verifier module. Requiring a RAM budget or an exclusive
lock merely to print a plan would fail a low-memory preview host for no
reason, and would needlessly block a dry-run alongside an already-running
live pass. This is a considered extension of the brief's own documented
exemption, not an oversight; it is called out here explicitly per this
repo's convention of flagging every non-obvious behavioral choice at the
point it is made.

Resume and checkpointing
--------------------------
``all_rows.jsonl`` never changes, so :func:`group_unverified` run against a
freshly downloaded copy ALWAYS returns the complete set of every cell group
phase 1 ever wrote, regardless of how much of it a prior verification pass
already finished. Resuming therefore only needs to know which of those
groups are already DONE: :func:`resume_done_groups`, computed from a prior
``verified_rows.jsonl`` (absent on a first pass), is subtracted from that
full set. Because one group is always processed to completion in a single
worker task (never partially, by construction), "at least one non
-``unverified`` cell row for this group" is a safe, sufficient completion
test. Progress is check-pointed by re-uploading the accumulated
``verified_rows.jsonl`` every :data:`UPLOAD_EVERY_GROUPS` completed groups
and once more at the very end, so a killed or interrupted pass loses at
most that many groups of work, never the whole run.

``verified_rows.jsonl``'s content invariant
----------------------------------------------
On every upload, ``verified_rows.jsonl`` holds EVERY row ``all_rows.jsonl``
ever had, in that same original order, with only ``unverified`` cell rows'
verdict-shaped fields overwritten in place; every other row -- including a
cell row that was never selected for verification and any row this pass
never touched -- passes through byte-for-byte. A sanity row this pass
creates for a theorem that had none (see the "Sanity replay" section above)
is the one exception: it is APPENDED at the end, never inserted, so the
prefix shared with ``all_rows.jsonl`` never shifts.

Import-safety: two lazy seams, exactly two
----------------------------------------------
This module's own test suite (and its ``--help``) must import cleanly on
BOTH the main ``.venv`` (Python 3.14, no ``lean_dojo``) and ``.venv-lean``
(Python 3.12). Exactly two imports are therefore deferred to call time,
never module scope and never function-definition scope:

- ``smolbench.deduction.lean.verify`` (needs ``lean_dojo``) -- see
  :func:`_default_verifier`, which copies the exact seam
  ``smolbench/deduction/lean/runner.py::_default_verifier`` already uses.
- ``boto3``/``botocore`` (no version conflict, but this repo's house
  convention -- see ``smolbench/evals/_aws.py`` and every ``scripts/*.py``
  file that touches S3 -- is that importing a module never requires the AWS
  SDK to be installed; only actually calling out to AWS does). This module
  reuses ``smolbench.evals._aws.fresh_client`` (itself already lazy) rather
  than importing ``boto3`` directly, and imports
  ``botocore.exceptions.ClientError`` lazily inside :func:`download_rows`,
  the one place this file inspects an AWS error code.

Everything else -- ``smolbench.evals._aws`` (for :func:`_aws.error_code`)
and ``smolbench.deduction.lean.corpus`` (``BenchmarkTheorem``,
``load_split``) -- imports fine on both interpreters and is therefore
imported at this module's top level, exactly as
``smolbench/deduction/lean/runner.py`` does for its own py3.14-safe
imports (``lean3``, ``.context``, ``.corpus``, ``.prompt``).

Run (repo root, ``.venv-lean``)::

    .venv-lean/bin/python scripts/lean_verify_rows.py --dry-run
    .venv-lean/bin/python scripts/lean_verify_rows.py --runs 'scaling_qwen*'
    .venv-lean/bin/python scripts/lean_verify_rows.py --theorem Nat.add_comm --workers 4

The plan can also be previewed from the main venv, since ``--dry-run`` is
exempt from the ``.venv-lean``/RAM/lock requirements above::

    .venv/bin/python scripts/lean_verify_rows.py --dry-run
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import fnmatch
import functools
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

# Design: `_error_code = _aws.error_code` (matching `smolbench/evals/ec2.py`'s own
# `_error_code = _aws.error_code` alias) -- one shared implementation for pulling
# `Error.Code` off a boto3/botocore exception, reused instead of re-derived here.
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

#: Basename of the dedicated lock file inside `DOJO_CACHE_DIR` that
#: `_dojo_cache_lock` acquires -- see the module docstring's "The Dojo
#: cache lock" section for why this is a file next to the cache, never the
#: cache directory itself.
_LOCK_FILENAME = ".smolbench_verify.lock"

#: Every `(kind, split)` combination `smolbench.deduction.lean.corpus` defines
#: (see that module's `SplitKind`/`Split` literals) -- the full search space
#: `_lookup_theorem` scans, since a row carries no `kind`/`split` of its own.
_CORPUS_KINDS: tuple[str, ...] = ("random", "novel_premises")
_CORPUS_SPLITS: tuple[str, ...] = ("train", "val", "test")


# ---------------------------------------------------------------------------
# Pure: S3 URI / key helpers
# ---------------------------------------------------------------------------
def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parses an ``s3://bucket[/key-prefix]`` URI into ``(bucket, key_prefix)``.

    Parameters
    ----------
    uri : str
        A candidate URI, e.g. ``"s3://my-bucket/deduction/runs"`` or bare
        ``"s3://my-bucket"``.

    Returns
    -------
    tuple of (str, str)
        ``(bucket, key_prefix)``. `key_prefix` has any trailing ``"/"``
        stripped, and is ``""`` when `uri` carries no path beyond the
        bucket.

    Raises
    ------
    ValueError
        `uri` does not start with the literal scheme ``"s3://"``, or the
        bucket segment (everything up to the first ``"/"`` after the
        scheme, or the whole remainder if there is no further ``"/"``) is
        empty. The message names the offending `uri`.

    Examples
    --------
    >>> parse_s3_uri("s3://my-bucket/deduction/runs")
    ('my-bucket', 'deduction/runs')
    >>> parse_s3_uri("s3://my-bucket/")
    ('my-bucket', '')
    """
    if not uri.startswith("s3://"):
        raise ValueError(f"parse_s3_uri: {uri!r} does not start with 's3://'")
    rest = uri[len("s3://"):]
    bucket, _, key_prefix = rest.partition("/")
    if not bucket:
        raise ValueError(f"parse_s3_uri: {uri!r} has an empty bucket")
    return bucket, key_prefix.rstrip("/")


def run_object_key(key_prefix: str, run: str, filename: str) -> str:
    """Builds one run's object key under a bucket's key prefix.

    Parameters
    ----------
    key_prefix : str
        Bucket-relative prefix under which every run lives (may be ``""``
        for a bucket with no prefix at all -- see :func:`parse_s3_uri`).
    run : str
        Run directory name, e.g. ``"scaling_qwen3.5-27b"``.
    filename : str
        Object basename within the run, e.g. `ROWS_FILENAME` or
        `VERIFIED_FILENAME`.

    Returns
    -------
    str
        ``f"{key_prefix}/{run}/{filename}"``, normalised so the result
        never has a leading ``"/"`` (when `key_prefix` is ``""``) or a
        doubled internal ``"/"`` (whichever segment carried stray leading
        or trailing slashes of its own).

    Examples
    --------
    >>> run_object_key("deduction/runs", "scaling_foo", "all_rows.jsonl")
    'deduction/runs/scaling_foo/all_rows.jsonl'
    >>> run_object_key("", "scaling_foo", "all_rows.jsonl")
    'scaling_foo/all_rows.jsonl'
    """
    segments = (key_prefix.strip("/"), run.strip("/"), filename.strip("/"))
    return "/".join(segment for segment in segments if segment)


# ---------------------------------------------------------------------------
# Pure: grouping, deduplication, fan-out, resume
# ---------------------------------------------------------------------------
def group_unverified(rows: list[dict]) -> dict[tuple[str, int], list[int]]:
    """Groups still-unverified cell rows by their ``(theorem_id, k)`` pair.

    Every cell row sharing a ``(theorem_id, k)`` pair can share exactly one
    Dojo session (see the module docstring's "Grouping and deduplication"
    section) -- this is the grouping :func:`verify_run` processes one Dojo
    session per.

    Parameters
    ----------
    rows : list of dict
        Rows exactly as parsed from ``all_rows.jsonl`` (or an in-progress
        ``verified_rows.jsonl``), in file order.

    Returns
    -------
    dict[tuple[str, int], list[int]]
        Maps ``(theorem_id, k)`` to the ascending-order list of INDICES
        into `rows` for every row with ``kind == "cell"`` and
        ``verdict == "unverified"``. Every other row (a different `kind`,
        or a cell whose verdict is anything else) is excluded. Key order
        is first-seen order (a plain ``dict``, populated in a single pass
        over `rows`); index order within a group is ascending, since rows
        are visited in their given order.

    Notes
    -----
    ``k`` is coerced to ``int`` via ``int(row["k"])`` -- JSON round-tripping
    already stores it as a number, but this guards against a stray
    string-typed value from a hand-edited fixture.
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
    """Groups row indices by their exact ``candidate_proof`` text.

    Lean replay is deterministic, so every row sharing the exact same
    candidate text needs exactly one real ``try_tail`` call -- see the
    module docstring's "Grouping and deduplication" section. No
    normalisation is applied (no whitespace trimming, no case-folding):
    two candidates that differ by so much as one character are, correctly,
    two distinct groups, since Lean itself would not necessarily treat them
    identically either.

    Parameters
    ----------
    rows : list of dict
        The full row list (any row shape; only `indices` are read).
    indices : list of int
        Indices into `rows` to group -- typically one :func:`group_unverified`
        value.

    Returns
    -------
    dict[str, list[int]]
        Maps each distinct ``candidate_proof`` string to the ascending
        -order list of indices (drawn from `indices`, in the order given)
        that share it. A row with a missing or ``None`` ``candidate_proof``
        is grouped under the empty string ``""``. Key order is first-seen
        order.
    """
    groups: dict[str, list[int]] = {}
    for index in indices:
        candidate = rows[index].get("candidate_proof") or ""
        groups.setdefault(candidate, []).append(index)
    return groups


def fan_out_verdict(rows: list[dict], indices: list[int], result: Mapping[str, Any]) -> None:
    """Applies one verification `result` to every row in `indices`, in place.

    This is the payoff of :func:`unique_candidates`'s deduplication: N rows
    that all submitted the same candidate text get ONE real Lean replay,
    whose single `result` is fanned back out to all N of them here.

    Parameters
    ----------
    rows : list of dict
        Mutated in place -- see Returns.
    indices : list of int
        Indices into `rows` to update.
    result : Mapping[str, Any]
        Must carry ``"verdict"``, ``"lean_error"``, ``"final_state_pp"``,
        and ``"verify_ms"``.

    Returns
    -------
    None
        For every ``i`` in `indices`, sets ``rows[i]["verdict"]``,
        ``rows[i]["lean_error"]``, ``rows[i]["final_state_pp"]``, and
        ``rows[i]["verify_ms"]`` from the matching key of `result`. No
        other key on any touched row is read or written -- in particular,
        `seed` and every other original field survive untouched (this repo
        never drops a recorded `seed`).
    """
    for index in indices:
        row = rows[index]
        row["verdict"] = result["verdict"]
        row["lean_error"] = result["lean_error"]
        row["final_state_pp"] = result["final_state_pp"]
        row["verify_ms"] = result["verify_ms"]


def resume_done_groups(verified_rows: list[dict]) -> set[tuple[str, int]]:
    """Finds which ``(theorem_id, k)`` groups a prior pass already finished.

    Parameters
    ----------
    verified_rows : list of dict
        A previously uploaded ``verified_rows.jsonl``'s parsed rows (``[]``
        on a first pass, with nothing to resume).

    Returns
    -------
    set[tuple[str, int]]
        Every ``(theorem_id, int(k))`` for which at least one
        ``kind == "cell"`` row's ``verdict`` is NOT ``"unverified"``. See
        the module docstring's "Resume and checkpointing" section for why
        "at least one" is a sufficient completeness test: one worker task
        always finishes a whole group before any of its rows are updated,
        so a group is never observed half-done.
    """
    done: set[tuple[str, int]] = set()
    for row in verified_rows:
        if row.get("kind") != "cell":
            continue
        if row.get("verdict") == "unverified":
            continue
        done.add((row["theorem_id"], int(row["k"])))
    return done


# ---------------------------------------------------------------------------
# Pure: RAM budget / worker cap
# ---------------------------------------------------------------------------
def available_ram_gb(meminfo_text: str) -> float:
    """Extracts ``MemAvailable`` from a ``/proc/meminfo`` file's TEXT, in GiB.

    Parameters
    ----------
    meminfo_text : str
        The full body of ``/proc/meminfo``, as text -- passed in rather
        than read from disk by this function, so it is testable with a
        literal fixture string and no real ``/proc`` filesystem.

    Returns
    -------
    float
        ``MemAvailable`` (kB, per the kernel's own accounting of
        reclaimable-plus-free memory) divided by ``1024 * 1024`` to give
        GiB.

    Raises
    ------
    ValueError
        No line starting with ``"MemAvailable:"`` is present in
        `meminfo_text`.
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
    """Caps worker count by available RAM, at `RAM_GB_PER_WORKER` GiB each.

    Parameters
    ----------
    meminfo_text : str
        Forwarded to :func:`available_ram_gb`.

    Returns
    -------
    int
        ``int(available_ram_gb(meminfo_text) // RAM_GB_PER_WORKER)``,
        floored at 1 -- a host with less than one worker's RAM budget still
        gets a usable cap (so :func:`check_workers` can compare against it
        and refuse cleanly) rather than a confusing 0.
    """
    return max(int(available_ram_gb(meminfo_text) // RAM_GB_PER_WORKER), 1)


def check_workers(requested: int, meminfo_text: str) -> None:
    """Refuses an oversubscribed (or non-positive) ``--workers`` value up front.

    Design: each Dojo session holds a live Lean process plus its fully
    loaded environment -- `RAM_GB_PER_WORKER` (6) GiB is the empirical
    per-worker budget. Oversubscribing does not fail immediately; it fails
    hours into a pass as an OOM kill that takes the whole process (and
    every row still in flight) down with it. Refusing here, before a single
    worker thread or Dojo session is created, trades that failure mode for
    an immediate, actionable one.

    Parameters
    ----------
    requested : int
        The operator's ``--workers`` value.
    meminfo_text : str
        Forwarded to :func:`max_workers_allowed` / :func:`available_ram_gb`.

    Returns
    -------
    None
        `requested` is within budget (and at least 1).

    Raises
    ------
    SystemExit
        `requested` is less than 1, or exceeds
        :func:`max_workers_allowed`\\ (`meminfo_text`) -- the message names
        `requested`, the computed cap, and the observed available RAM.
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
def require_py312() -> None:
    """Refuses to proceed on an interpreter without ``lean_dojo`` available.

    Returns
    -------
    None
        ``sys.version_info < (3, 13)`` -- ``lean_dojo`` (and therefore this
        script's actual verification work) can be imported.

    Raises
    ------
    SystemExit
        ``sys.version_info >= (3, 13)``, naming the ``.venv-lean`` remedy
        and the exact ``uv sync`` command from
        ``smolbench/deduction/lean/verify.py``'s own import-guard message.
    """
    if sys.version_info >= (3, 13):
        raise SystemExit(
            "lean_verify_rows: this is the deferred VERIFICATION pass and needs "
            "'lean_dojo', which only installs under the dedicated '.venv-lean' "
            "environment (the upstream package pins python<3.13). Re-run with "
            "'.venv-lean/bin/python scripts/lean_verify_rows.py ...' instead of the "
            "main venv's python. Build it once with:\n"
            "    UV_PROJECT_ENVIRONMENT=.venv-lean uv sync --python 3.12 "
            "--extra lean --extra notebook --extra dev\n"
            "(--dry-run works on any interpreter, including this one, if you only "
            "need to preview the plan.)"
        )


def dojo_failure_hint(exc: BaseException) -> str:
    """Builds actionable operator guidance for a Dojo-init-class failure.

    Parameters
    ----------
    exc : BaseException
        The exception ``open_at_step`` (or the retry loop underneath it)
        raised while trying to open a Dojo session.

    Returns
    -------
    str
        `exc`'s own text, followed by guidance grounded in what is actually
        true of this pipeline: `verify.py`'s ``_open_dojo_with_retry``
        already retried 3 times with backoff before this exception ever
        reached the caller; the FIRST Dojo call on a given host pulls a
        ~2.4 GB traced corpus from LeanDojo's S3 cache into
        `DOJO_CACHE_DIR`, credential-free (cold ~2-4 minutes, warm ~10
        seconds); `elan` must be installed for that pull (and the Lean
        toolchain it fetches) to succeed at all; and a corrupt or
        partially-written cache is cleared by removing `DOJO_CACHE_DIR`
        entirely and letting the next run refetch it from scratch. Points
        at ``.claude/skills/run-smolbench/SKILL.md`` for the documented
        cache-pull timings and the `elan` install command -- deliberately
        NOT at a build-log-style changelog file, since none exists in this
        repo and none ships with the Lean verifier's dependency either; an
        earlier draft of this guidance cited one and was corrected before
        implementation.
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
    """Builds a ``full_name -> BenchmarkTheorem`` index over the WHOLE local corpus.

    See the module docstring's "Theorem lookup" section for why this full
    scan is necessary: a row records only `theorem_id` (a `full_name`) and
    `k`, never which ``(kind, split)`` it came from, so there is no
    narrower correct lookup than searching every combination
    `smolbench.deduction.lean.corpus` defines.

    Returns
    -------
    dict[str, BenchmarkTheorem]
        Every theorem from every ``(kind, split)`` combination whose
        dataset file is present locally, keyed by `full_name`
        (first-seen wins on a name collision across combinations -- none
        is expected in practice, since a theorem's `full_name` is a
        mathlib4 declaration name and belongs to exactly one
        `random`/`novel_premises` partition at a time).

    Notes
    -----
    Memoised for the life of the process (`functools.lru_cache` on a
    zero-argument function) -- this index is built at most once no matter
    how many runs or groups this invocation processes. Each underlying
    `load_split(kind, split)` call is itself `lru_cache`-memoised by
    `corpus.py`, so re-running this function (which does not happen, given
    the cache here, but would be safe if it did) would not re-read any file
    twice either.

    A ``(kind, split)`` combination whose dataset file was never
    bootstrapped locally (``FileNotFoundError`` from `load_split`) is
    skipped, not fatal: an operator may only have bootstrapped the splits
    they actually swept against, and a combination this run's rows never
    reference should not block verification of the ones they do.
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
    """Resolves a row's `theorem_id` to its full `BenchmarkTheorem`.

    Parameters
    ----------
    theorem_id : str
        A cell or sanity row's ``theorem_id`` (== `BenchmarkTheorem.full_name`).

    Returns
    -------
    BenchmarkTheorem
        The matching theorem, complete with the traced-tactic prefix
        `open_at_step` needs and the `url`/`commit` LeanDojo needs to
        address it.

    Raises
    ------
    LookupError
        `theorem_id` is not present in any locally bootstrapped
        ``(kind, split)`` combination -- see :func:`_theorem_index`.
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
    """Lazily resolves the real Lean verifier module.

    Deferred (call-time, not module-top) import of
    `smolbench.deduction.lean.verify`, which requires `lean_dojo` and
    therefore only works under `.venv-lean`. Copies the exact seam
    `smolbench/deduction/lean/runner.py::_default_verifier` uses, per this
    file's brief.

    Returns
    -------
    ModuleType
        The `smolbench.deduction.lean.verify` module, exposing
        `open_at_step`, `try_tail`, `replay_ground_truth`.

    Raises
    ------
    ImportError
        Propagated from `smolbench.deduction.lean.verify` when `lean_dojo`
        is not installed in the current interpreter.
    """
    from smolbench.deduction.lean import verify

    return verify


def _build_s3_client() -> Any:
    """Builds a fresh boto3 S3 client bound to `S3_REGION`.

    Uses `smolbench.evals._aws.fresh_client` -- a brand-new boto3 Session
    per call, this repo's established convention (see that function's
    docstring: a rotated credentials file is picked up rather than
    silently signing with a stale one) -- rather than `boto3.client(...)`
    directly. `_aws` itself is imported at this module's top level (it is
    boto3-free at import time; `boto3` is only pulled in inside
    `fresh_client`), so THIS call, not the import, is the actual boto3
    opt-in.
    """
    return _aws.fresh_client("s3", S3_REGION)


# ---------------------------------------------------------------------------
# Impure: S3 I/O (client is always injected -- real or a test fake)
# ---------------------------------------------------------------------------
def list_runs(
    client: Any, bucket: str, key_prefix: str, pattern: str = DEFAULT_RUNS_GLOB
) -> list[str]:
    """Lists run directory names directly under `key_prefix`, filtered by `pattern`.

    Parameters
    ----------
    client : Any
        An S3 client exposing ``get_paginator("list_objects_v2")``.
    bucket : str
        Bucket to list.
    key_prefix : str
        Prefix under which every run's own sub-prefix lives (may be
        ``""``).
    pattern : str, default DEFAULT_RUNS_GLOB
        `fnmatch.fnmatch` pattern a run's directory NAME (not its full key)
        must match.

    Returns
    -------
    list of str
        Every run directory name found via one ``Delimiter="/"`` listing
        (reading `CommonPrefixes`, across every page) whose name matches
        `pattern`, sorted ascending.
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
    """Downloads one JSONL object to `dest` and returns its parsed rows.

    Parameters
    ----------
    client : Any
        An S3 client exposing ``get_object(Bucket=..., Key=...)``.
    bucket : str
        Bucket to read from.
    key : str
        Object key.
    dest : Path
        Local path the raw bytes are written to (parent directories
        created as needed).

    Returns
    -------
    list of dict
        One entry per non-blank line of the object, `json.loads`-parsed,
        in file order. ``[]`` when the object does not exist -- ABSENCE IS
        NORMAL for an optional, not-yet-created ``verified_rows.jsonl``,
        not an error (see :func:`verify_run`).

    Raises
    ------
    Exception
        Any S3 failure other than "object not found" (a permissions
        failure, a malformed bucket name, ...) propagates unhandled -- such
        a failure must never be silently read as "nothing to verify yet".

    Notes
    -----
    Imports `botocore.exceptions.ClientError` lazily (this repo's house
    convention -- see the module docstring's "Import-safety" section).
    Absence is detected via a ``ClientError`` whose ``Error.Code`` is
    ``"NoSuchKey"`` or ``"404"`` (the two shapes a missing-key
    ``get_object`` is documented to raise across boto3/test-fake
    implementations in this repo -- see ``tests/test_results_store.py``'s
    ``FakeS3Client``, which raises a real ``ClientError`` with code
    ``"NoSuchKey"``).
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
    """Serialises `rows` to a scratch file under `workdir`, then uploads it to `key`.

    Parameters
    ----------
    client : Any
        An S3 client exposing ``upload_file(filename, bucket, key)``.
    rows : list of dict
        Rows to serialise, in order.
    bucket : str
        Destination bucket.
    key : str
        Destination object key.
    workdir : Path
        Directory the scratch file (named `VERIFIED_FILENAME`) is written
        under; created if it does not already exist. Safe to call
        repeatedly against the same `workdir` (each call overwrites the
        scratch file with the current full row set -- see
        :func:`verify_run`'s checkpoint uploads).

    Returns
    -------
    None
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
    """Holds an exclusive, non-blocking flock on a dedicated file inside `DOJO_CACHE_DIR`.

    Acquired once, held for the process's remaining lifetime (the caller
    wraps the entire multi-run processing loop in this context manager),
    released on the way out however the block exits.

    Yields
    ------
    None

    Raises
    ------
    SystemExit
        Another process already holds the lock (``BlockingIOError`` from
        the non-blocking `fcntl.flock` call) -- the message names the lock
        file and explains that concurrent passes race on the shared
        traced-repo build cache.

    Notes
    -----
    Locks a DEDICATED FILE (`DOJO_CACHE_DIR / ".smolbench_verify.lock"`),
    never `DOJO_CACHE_DIR` itself -- a real Dojo session reads and writes
    inside that directory from multiple worker threads within ONE process,
    so locking the directory would make this process contend with its own
    workers.
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
    """Updates `theorem_id`'s sanity row in `out_rows`, appending one if absent.

    Parameters
    ----------
    out_rows : list of dict
        Mutated in place.
    theorem_id : str
        Which theorem's sanity row to update.
    payload : Mapping[str, Any]
        Must carry ``"verdict"``, ``"tactics_applied"``, ``"tactics_total"``,
        ``"error"``.
    ms : int
        Wall-clock milliseconds the replay took; written as `"ms"`.

    Returns
    -------
    None
        If a ``kind == "sanity"`` row for `theorem_id` already exists (the
        placeholder phase 1 wrote), its `verdict`/`tactics_applied`/
        `tactics_total`/`error`/`ms` fields are overwritten in place.
        Otherwise a brand-new sanity row is APPENDED to the end of
        `out_rows` -- never inserted -- so the shared prefix with
        ``all_rows.jsonl`` never shifts (see the module docstring's
        "content invariant" section).
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
    """Verifies one run's unverified cell groups; uploads `VERIFIED_FILENAME`.

    See the module docstring's "Resume and checkpointing" and "content
    invariant" sections for the exact semantics this function implements.

    Parameters
    ----------
    client : Any
        Injected S3 client (real, or a test fake) -- see :func:`list_runs`
        / :func:`download_rows` / :func:`upload_rows`.
    bucket, key_prefix : str
        Where this run's objects live -- see :func:`run_object_key`.
    run : str
        Run directory name (e.g. ``"scaling_qwen3.5-27b"``).
    workers : int
        `ThreadPoolExecutor` worker count -- one group is processed per
        task; see the module docstring's "Grouping and deduplication"
        section for why a group, not a row, is the unit of work.
    theorem : str or None, optional
        When given, only groups whose `theorem_id` equals this are
        processed.
    limit : int, default 0
        Caps the number of groups processed THIS call (0 = no cap).
    workdir : Path
        This run's private scratch subdirectory is created under here
        (``workdir / run``) -- never shared with another run's scratch
        files.
    dry_run : bool, default False
        When True, groups are selected and reported but neither Lean nor
        S3 upload machinery is touched -- see the module docstring's
        ``--dry-run`` section.
    verifier : ModuleType or None, optional
        Verifier module exposing `open_at_step`, `try_tail`,
        `replay_ground_truth`. `None` (the default) lazily resolves the
        real module via :func:`_default_verifier` -- but ONLY when there is
        at least one group to actually process (an empty pending set, or
        `dry_run`, never imports it at all).

    Returns
    -------
    int
        ``0`` on success (including "nothing to do"); ``1`` if
        ``all_rows.jsonl`` does not exist for this run (a warning is
        logged and the run is skipped entirely -- there is nothing else to
        verify against).
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
        # Verify every group again from the CURRENT all_rows.jsonl, discarding
        # the prior pass's verdicts.
        #
        # Needed because resume is keyed on (theorem_id, k) GROUPS, not on the
        # candidate proofs inside them. If phase 1 regenerated a lane after a
        # verification pass, every group still looks "done" while the proofs
        # under it are completely different -- so the pass reports success,
        # verifies nothing, and leaves verified_rows.jsonl describing text that
        # no longer exists. Six lanes were in exactly that state on 2026-08-16
        # after the day's repairs and re-runs; nemotron-3-nano-4b had had all
        # 944 of its cells regenerated.
        #
        # The caller is responsible for archiving the superseded
        # verified_rows.jsonl first -- this flag overwrites it.
        logging.warning(
            f"lean_verify_rows[{run}]: --no-resume: discarding {len(verified_rows)} "
            "row(s) from the prior verification pass and re-verifying every group."
        )
        verified_rows = []
    done = resume_done_groups(verified_rows)

    # Seed the OUTPUT row list: a prior partial pass's own output (which
    # already carries every original row, in order -- see the module
    # docstring's content invariant) when one exists, otherwise a fresh
    # copy of the immutable source. Either way, indices computed below
    # against `rows` (the immutable all_rows.jsonl download) stay valid
    # against `out_rows`'s shared prefix, since a prior upload never
    # reorders or removes anything -- it only overwrites verdict-shaped
    # fields in place and appends new sanity rows at the very end.
    out_rows: list[dict] = verified_rows if verified_rows else list(rows)

    # `group_unverified` runs against `rows` (the immutable source), NOT
    # `out_rows`: all_rows.jsonl's cell verdicts never change, so this
    # always returns the COMPLETE set of every group phase 1 ever wrote --
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
        """Does the real work for one (theorem_id, k) group. Never raises -- see `_process_group`."""
        lookup_error: Optional[BaseException] = None
        try:
            bt = _lookup_theorem(theorem_id)
        except Exception as exc:  # noqa: BLE001 -- recorded below, not swallowed
            bt = None
            lookup_error = exc

        # Sanity gate: replay the full ground-truth proof once per THEOREM
        # (not once per group) -- see the module docstring's "Sanity
        # replay" design note for why this refinement is correct.
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
                # Dojo opened fine; the recorded ground-truth PREFIX itself
                # didn't replay as expected (open_at_step's own explicit
                # RuntimeError shape). Not a Dojo/cache infra problem, so
                # dojo_failure_hint's guidance would mislead -- leave the
                # message as-is.
                lean_error = f"{type(exc).__name__}: {exc}"
            else:
                # Dojo itself never opened (connection/EOF/subprocess
                # failure, even after verify.py's own 3x retry) --
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

        `_verify_one_group` already maps every documented failure onto a
        row (open_at_step-class -> "replay_failed", try_tail-class ->
        "exception", theorem-lookup failure -> "replay_failed"). This outer
        catch-all exists only so a genuinely unanticipated bug (e.g. a
        malformed row missing an expected key) still lands on every row in
        the group as an "exception" verdict, per this file's "never
        swallow an exception without recording it on a row" contract,
        rather than crashing the worker thread silently.
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
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    """Builds this script's `argparse.ArgumentParser`.

    Notes
    -----
    Help text uses "replicates" throughout, per this repo's current
    terminology for the replication axis -- see
    `smolbench.deduction.lean.runner`'s row schema, keyed by
    `replicate_idx`. The retired name for that axis is not used anywhere
    in this file.
    """
    parser = argparse.ArgumentParser(
        prog="lean_verify_rows.py",
        description=(
            "Phase 2 of the two-phase Lean theorem-proving eval: replay recorded "
            "candidate proofs against real Lean and write verified_rows.jsonl "
            "alongside each run's all_rows.jsonl in S3. Requires .venv-lean "
            "(lean_dojo needs python<3.13) except under --dry-run."
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
    """Entry point: verifies every run matching ``--runs`` under ``--s3-prefix``.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector; forwarded to `argparse.ArgumentParser.parse_args`.
        ``None`` (the default) parses ``sys.argv[1:]``.

    Returns
    -------
    int
        ``0`` if every matching run's ``all_rows.jsonl`` was found and
        processed (even if a run had nothing left to verify); the COUNT of
        runs whose ``all_rows.jsonl`` could not be found otherwise (see
        :func:`verify_run`'s return value) -- a non-zero count either way
        signals "at least one run failed to load".

    Notes
    -----
    Step order (see the module docstring's ``--dry-run`` section for why
    `require_py312`, `check_workers`, and the Dojo cache lock are ALL
    skipped together under ``--dry-run``, not just the first):

    1. `require_py312` (skipped under ``--dry-run``).
    2. `check_workers` against a live read of ``/proc/meminfo`` (skipped
       under ``--dry-run``).
    3. The exclusive Dojo cache lock, held for the rest of this call
       (skipped under ``--dry-run``).
    4. `list_runs`, then `verify_run` per matching run.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.dry_run:
        require_py312()

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
