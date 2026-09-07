"""The live 21-lane supervision loop: launch, monitor, restart, gate, spool.

Owns everything after an operator commits to a real launch: pre-flight budget
derivation, staggered launch, the FAMILY GATE behind `GATE_MODELS`, the
per-tick monitor and its alerts, the shared restart policy, the CoT-ON
assertion, phase advance, the S3 spool and shutdown. `_run_fleet` is the one
entry point.

Roster/env live in `lane_env.py`, the restart vocabulary in `policy.py`
(shared with `run_shards.py` so one spot reclaim gets one answer regardless of
which supervisor is watching), and the CLI in `run_fleet.py`.

`save_fleet_state`/`load_fleet_state` keep every lane's state in one file
(`fleet_state_path`) so a replacement supervisor resumes instead of
re-granting 21 already-billing boxes a fresh relaunch budget.

No AWS SDK is imported at module scope here or in `lane_env.py`, so loading
this module after `lane_env`'s `load_dotenv` cannot freeze a stale env value.

Loaded by file path via `_config.load_fleet_module`, never a bare `import
supervisor`: `scripts/fleet` has no `__init__.py`.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional, Sequence

from smolbench.evals.results_store import ReplicateAddress, resolve_store

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config() -> ModuleType:
    # By hand, and only for `_config` itself: `load_module_by_path` is a
    # function ON that module, and `scripts/fleet` is not a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Eager, at module scope: LANES is needed on the first `_run_fleet` call, and
# loading it here also runs lane_env's import-time roster `_drift_guard`
# before any subprocess launches. Via `_config.load_fleet_module`, so this
# module and `run_fleet.py` share one module object -- one roster per process.
_lane_env = _config.load_fleet_module("lane_env")

# Shared with `run_shards.py` via `_config.load_fleet_module` so one spot
# reclaim gets one answer regardless of which supervisor is watching. Loaded
# eagerly (unlike `_deduction_driver`): policy.py only imports `re` and
# `dataclasses`, so it cannot fail or read the environment.
_policy = _config.load_fleet_module("policy")


# Anchored on `lane_env.REPO_ROOT`, never cwd-relative, since the entry point
# may launch from any working directory; the tree is gitignored so lane logs
# never enter a commit.
LOG_DIR: Path = _lane_env.REPO_ROOT / "notebooks" / "induction" / "results" / "fleet_logs"

#: Byte budget `_tail_log` reads from the end of a lane's log file: generous
#: rather than tight because under-reading could push a `_policy.RECLAIM_PATTERNS`
#: match outside the window and misclassify a reclaim as a crash.
TAIL_MAX_BYTES = 262144


def _tail_log(log_dir: Path, key: str, n: int = 40, *, max_bytes: int = TAIL_MAX_BYTES) -> str:
    """Return the last `n` lines of lane `key`'s log file, or ``""`` if unreadable.

    Parameters
    ----------
    log_dir : Path
        Directory containing lane log files.
    key : str
        Lane key identifying the log file.
    n : int, optional
        Number of trailing lines to return.
    max_bytes : int, optional
        At most this many bytes are read from the end of the file, never the whole file.

    Returns
    -------
    str
        The requested trailing log lines, or ``""`` if unreadable.
    """
    path = log_dir / f"{key}.log"
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start)
            chunk = f.read()
    except OSError:
        return ""
    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]  # likely a partial line (seek landed mid-line); could spuriously match a pattern
    return "\n".join(lines[-n:])


# Matches `ec2.serve_model`'s healthy-serve log line, not its earlier
# in-flight line -- the family gate waits to stop seeing the latter.
SERVE_HEALTHY_RE = re.compile(r"serve_model: '.+?' is up at http://\S+")


def is_serve_healthy(line: str) -> bool:
    """Check whether `line` (logging prefix allowed) is ec2.py's healthy-serve log line."""
    return SERVE_HEALTHY_RE.search(line) is not None


# A dead toggle measures ~0-11% (bare integers); a working soft protocol
# measures 78-100%. 0.5 cleanly separates the two regimes without a 0.9
# threshold misfiring on one or two direct answers among only 9 intens marks.
COT_MIN_FRACTION = 0.5
#: A response longer than this counts as a reasoning chain carried in content,
#: since the quiz contract asks for a single bare integer.
COT_CONTENT_REASONING_MIN_CHARS = 200


def reasoning_fraction(
    store: Any,
    model: str,
    tag: str,
    seed: Optional[int] = None,
    infos: Optional[Sequence[str]] = None,
) -> Optional[float]:
    """Measure the fraction of a model's landed marks that carry reasoning evidence.

    Response length also
    counts as evidence because some soft thinking protocols (Ministral's
    [THINK] prompt, EXAONE's `enable_thinking`) leave 40-60% of chains in
    plain `response` rather than think markup.

    Parameters
    ----------
    store : Any
        Results store containing landed marks.
    model : str
        Model whose marks are measured.
    tag : str
        Experiment tag for the marks.
    seed : Optional[int], optional
        Replicate seed to measure.
    infos : Optional[Sequence[str]], optional
        Information arms to pool.

    Returns
    -------
    Optional[float]
        The fraction of landed marks with reasoning evidence, or None when no arm has landed yet
        for (model, seed).
    """
    if seed is None:
        seed = _lane_env.run_study.BASE_SEED
    if infos is None:
        infos = _lane_env.run_study.INFO_TYPES

    pooled = []
    for info in infos:
        addr = ReplicateAddress(tag=tag, info=info, seed=seed, model=model)
        if not store.exists(addr):
            continue
        pooled.extend(store.load_marks(addr).marks)

    if not pooled:
        return None
    return sum(
        1
        for mark in pooled
        if mark.reasoning
        or len(mark.response or "") > COT_CONTENT_REASONING_MIN_CHARS
    ) / len(pooled)


def build_results_store() -> Any:
    """Build the production ``ResultsStore`` for this study's results directory.

    Kept out of `reasoning_fraction` so that function stays fake-able in tests.
    """
    return resolve_store(_lane_env.run_study.EXPERIMENT.results_dir)


# ---------------------------------------------------------------------------
# Loop constants (exact names/values -- pinned by tests/tooling/test_run_fleet.py)
# ---------------------------------------------------------------------------
GATE_MODELS = ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b")
LAUNCH_STAGGER_SECONDS = 30
MONITOR_INTERVAL_SECONDS = 60
DESCRIBE_EVERY_N_TICKS = 5


# ---------------------------------------------------------------------------
# Pre-flight (before any subprocess.Popen)
# ---------------------------------------------------------------------------
def preflight(lanes: Sequence[_lane_env.Lane]) -> dict[str, int]:
    """Warm every lane's tokenizer and derive its completion budget.

    Runs before any subprocess or EC2 provisioning, so a tokenizer-fetch
    failure or an under-budget verdict cannot surface between a live GPU box
    and its first request.

    Parameters
    ----------
    lanes : Sequence[_lane_env.Lane]
        Lanes whose tokenizers and completion budgets are checked.

    Returns
    -------
    dict[str, int]
        Completion budgets keyed by lane key.

    Raises
    ------
    SystemExit
        If any lane failed, listing every failed lane at once.
    """
    run_study = _lane_env.run_study
    budgets: dict[str, int] = {}
    failures: list[tuple[str, str, str]] = []
    seeds = range(run_study.BASE_SEED, run_study.BASE_SEED + run_study.N_REPLICATES)
    for lane in lanes:
        try:
            budgets[lane.key] = run_study.completion_budget(lane.key, seeds)
        except (Exception, SystemExit) as exc:  # noqa: BLE001 -- SystemExit isn't an Exception; both collected
            failures.append((lane.key, type(exc).__name__, str(exc)))

    if failures:
        header = f"{'lane':<32}{'exception':<20}message"
        lines = [header, "-" * len(header)]
        for key, exc_type, message in failures:
            lines.append(f"{key:<32}{exc_type:<20}{message}")
        raise SystemExit(
            f"run_fleet: preflight failed for {len(failures)} lane(s); aborting before any "
            "subprocess is launched (no billing box was ever touched):\n" + "\n".join(lines)
        )
    logging.info(f"run_fleet: preflight OK for {len(budgets)} lane(s).")
    return budgets


def fleet_image_digest() -> Optional[str]:
    """Look up a best-effort ``docker manifest inspect`` digest for ``lane_env.FLEET_IMAGE``.

    That image is already digest-pinned, so this is only a resolvability
    check for the run banner; it never raises, since it must not block a
    launch. Returns None (logged at INFO) when docker is missing, the
    inspect call fails, or the JSON has no digest field.
    """
    if shutil.which("docker") is None:
        logging.info("fleet_image_digest: docker not found on PATH; skipping digest lookup.")
        return None
    try:
        result = subprocess.run(
            ["docker", "manifest", "inspect", _lane_env.FLEET_IMAGE],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort banner info only, never fatal
        logging.info(f"fleet_image_digest: 'docker manifest inspect' failed: {exc}")
        return None

    try:
        manifest = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logging.info(f"fleet_image_digest: could not parse manifest JSON: {exc}")
        return None

    digest = manifest.get("config", {}).get("digest")
    if not digest:
        # A multi-arch image returns a manifest list, not a single manifest;
        # the per-architecture digest here will not match the index digest.
        entries = manifest.get("manifests") or []
        if entries:
            digest = entries[0].get("digest")
    if not digest:
        logging.info("fleet_image_digest: manifest JSON had no recognisable digest field.")
        return None
    return digest


# ---------------------------------------------------------------------------
# Live orchestration: launch, monitor, restart, phase-advance, gate, shutdown
# ---------------------------------------------------------------------------
# Nothing below runs at import time except `_phase_sequence`, which the
# `--dry-run` plan also calls.


def _deduction_driver() -> ModuleType:
    """Load ``notebooks/deduction/run_study.py``, lazily -- never at module scope.

    That module pulls `tiktoken` and, at module scope, runs env-dependent
    setup keyed on variables only set in a lane subprocess, not this process.
    Called only from `_advance_finished`.
    """
    return _config.load_module_by_path(
        "run_fleet_deduction_run_study_dep",
        _lane_env.REPO_ROOT / "notebooks" / "deduction" / "run_study.py",
    )


@dataclass
class _Presence:
    """Last describe sweep's lane set, plus whether any lane has ever been seen.

    Distinguishes "not yet provisioned" from "confirmed empty": both present
    as an empty list from `fleet_status.fleet_rows()` (so does every region's
    `describe_instances` raising), and treating either as "everything is
    gone" would turn every lane's exit into an unlimited-retry reclaim before
    a single box had been described successfully.
    """

    lanes: Optional[set] = None
    ever_seen: bool = False

    def observe(self, swept: set) -> None:
        """Update presence from one sweep's raw lane set (call only if the sweep did not raise)."""
        if swept:
            self.lanes = set(swept)
            self.ever_seen = True
        elif self.ever_seen:
            self.lanes = set()
        # else: nothing has ever been seen and this sweep was also empty --
        # leave `lanes` unchanged (unknown).

    def present(self, key: str) -> bool:
        """Whether lane `key` should be treated as present right now.

        Keys off `ever_seen`, not merely `lanes is None`: until a sweep has
        actually seen this fleet non-empty once, presence is unknown and
        defaults to True rather than reclassifying an unchecked lane as
        reclaimed.

        Parameters
        ----------
        key : str
            Lane key to look up in the most recent sweep.

        Returns
        -------
        bool
            Whether the lane is present or presence is still unknown.
        """
        if not self.ever_seen:
            return True
        return self.lanes is None or key in self.lanes


@dataclass
class _LaneRun:
    """Mutable per-lane runtime state, carried across monitor-loop ticks."""

    lane: _lane_env.Lane
    #: Ordered subprocess phases this invocation runs for this lane.
    phases: tuple[str, ...]
    phase_index: int = 0
    proc: Optional[subprocess.Popen] = None
    #: Most recent (re)launch; not persisted, since a resumed supervisor
    #: relaunches the current phase anyway, making the stored value stale.
    started_at: float = 0.0
    #: First launch only, never reset by a relaunch: `_monitor_tick`'s
    #: 2x-budget alert keys on this so it can still fire for a lane stuck
    #: relaunching over and over.
    lane_started_at: float = 0.0
    #: Bounded by `_policy.MAX_CRASH_RELAUNCHES`; incremented before
    #: `_policy.decide_relaunch` is asked for a verdict.
    crash_relaunches: int = 0
    #: Bounded by `_policy.MAX_RECLAIM_RELAUNCHES`; incremented before the
    #: decision, like `crash_relaunches`.
    reclaim_relaunches: int = 0
    #: `time.monotonic()` deadline for a pending backed-off reclaim relaunch;
    #: None means nothing is pending.
    pending_relaunch_at: Optional[float] = None
    cot_checked: bool = False
    #: Latches True once the healthy-serve line is found, so later gate
    #: checks are an O(1) no-I/O return.
    gate_passed: bool = False
    #: Byte offset already scanned, so each call reads only new bytes; reset
    #: to 0 if the log file is found shorter than this (truncated/replaced).
    gate_scan_offset: int = 0
    halted: bool = False
    halt_reason: str = ""
    done: bool = False
    #: Non-empty when this lane's post-deduction S3 spool failed. Does not
    #: halt the lane -- its data is already collected -- only reported.
    spool_error: str = ""

    @property
    def current_phase(self) -> Optional[str]:
        """The phase this lane runs now, or None once `phases` is exhausted."""
        if self.phase_index >= len(self.phases):
            return None
        return self.phases[self.phase_index]


# One file, rewritten every tick: without it a replaced supervisor re-grants
# every lane a full crash and reclaim budget while 21 GPU boxes keep billing.
FLEET_STATE_FILENAME = "fleet_state.json"

#: The `_LaneRun` fields carried verbatim, declared once so `save_fleet_state`
#: and `load_fleet_state` cannot drift into writing a field neither reads back.
_STATE_PLAIN_FIELDS = (
    "phase_index",
    "crash_relaunches",
    "reclaim_relaunches",
    "cot_checked",
    "gate_passed",
    "gate_scan_offset",
    "halted",
    "halt_reason",
    "done",
    "spool_error",
)

#: The two fields that are `time.monotonic()` in memory and wall-clock on
#: disk; named with an `_epoch` suffix so nobody reads one back into a
#: monotonic field without noticing the conversion (see `_monotonic_to_epoch`).
_STATE_CLOCK_FIELDS = ("lane_started_at_epoch", "pending_relaunch_at_epoch")


def fleet_state_path(log_dir: Path) -> Path:
    """Return the supervisor state file's path for a run logging to `log_dir`.

    The file lives beside the lane logs it describes, not at a fixed
    repo-root location: a supervisor restarted with the same `--log-dir`
    resumes, one started with a different `--log-dir` correctly starts fresh.

    Parameters
    ----------
    log_dir : Path
        Directory containing the lane logs.

    Returns
    -------
    Path
        The supervisor state file path.
    """
    return log_dir / FLEET_STATE_FILENAME


def _monotonic_to_epoch(
    value: Optional[float], *, monotonic_now: float, epoch_now: float
) -> Optional[float]:
    """Convert an in-memory `time.monotonic` value to a persistable wall-clock one.

    `time.monotonic()`'s epoch is arbitrary and per-process, so persisting the
    raw number and reading it back in a replacement supervisor would measure
    it against an unrelated origin; wall clock is the only clock both
    processes share. `monotonic_now`/`epoch_now` are sampled once by the
    caller so every lane in one save converts against the same reference pair.

    Parameters
    ----------
    value : Optional[float]
        Monotonic timestamp to convert.
    monotonic_now : float
        Current monotonic timestamp in the caller's reference pair.
    epoch_now : float
        Current wall-clock timestamp in the caller's reference pair.

    Returns
    -------
    Optional[float]
        The equivalent wall-clock timestamp, or None.
    """
    if value is None:
        return None
    return epoch_now - (monotonic_now - value)


def _epoch_to_monotonic(
    value: Optional[float], *, monotonic_now: float, epoch_now: float
) -> Optional[float]:
    """Convert a persisted wall-clock value back into this process's monotonic frame.

    The exact inverse of `_monotonic_to_epoch`. A wall-clock step (NTP, a
    manual set) between save and load shifts the recovered age by that step;
    accepted since the alternative is no resume at all.

    Parameters
    ----------
    value : Optional[float]
        Persisted wall-clock timestamp to convert.
    monotonic_now : float
        Current monotonic timestamp in the caller's reference pair.
    epoch_now : float
        Current wall-clock timestamp in the caller's reference pair.

    Returns
    -------
    Optional[float]
        The equivalent monotonic timestamp, or None.
    """
    if value is None:
        return None
    return monotonic_now - (epoch_now - value)


def save_fleet_state(runs: dict[str, _LaneRun], log_dir: Path) -> None:
    """Write every lane's resumable state to `log_dir`'s one supervisor state file.

    Atomic: serialised to a sibling ``.tmp`` file and `os.replace`d into
    position, so a reader never observes a torn file. `_LaneRun.started_at`,
    `.proc`, `.lane` and `.phases` are not persisted -- they're either stale
    the instant they'd be read back or rebuilt fresh by `_run_fleet`. The
    `lanes` map is keyed by spec key, the same string
    `fleet_status.fleet_rows` derives from the `smolbench:experiment` tag, so
    lane identity comes from the tag and a describe sweep names the same
    lanes as this file.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state keyed by lane key.
    log_dir : Path
        Directory in which to write the supervisor state file.
    """
    # Sampled once, not per lane, so every lane converts against one reference pair.
    monotonic_now = time.monotonic()
    epoch_now = time.time()

    lanes: dict[str, dict[str, Any]] = {}
    for key, run in runs.items():
        entry: dict[str, Any] = {name: getattr(run, name) for name in _STATE_PLAIN_FIELDS}
        # 0.0 ("never launched") and None ("nothing pending") both become
        # JSON null rather than passing through the conversion.
        entry["lane_started_at_epoch"] = _monotonic_to_epoch(
            run.lane_started_at if run.lane_started_at else None,
            monotonic_now=monotonic_now,
            epoch_now=epoch_now,
        )
        entry["pending_relaunch_at_epoch"] = _monotonic_to_epoch(
            run.pending_relaunch_at, monotonic_now=monotonic_now, epoch_now=epoch_now
        )
        lanes[key] = entry

    document = {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "lanes": lanes,
    }

    log_dir.mkdir(parents=True, exist_ok=True)
    path = fleet_state_path(log_dir)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as state_file:
        json.dump(document, state_file, indent=2, sort_keys=True)
        state_file.write("\n")
    os.replace(tmp, path)


def load_fleet_state(runs: dict[str, _LaneRun], log_dir: Path) -> int:
    """Restore `log_dir`'s persisted lane state into `runs`, in place.

    Does not recover a running process: `_LaneRun.proc` cannot be
    serialised, so a resumed supervisor relaunches the lane's current phase
    regardless, and the driver's own `ResultsStore.exists` resume-skip (not
    this file) is what stops already-landed work from being re-billed.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state to restore in place.
    log_dir : Path
        Directory containing the supervisor state file.

    Returns
    -------
    int
        How many lanes were resumed (0 if there is no file: a first run, not an error).

    Raises
    ------
    ValueError
        Naming the path and telling the operator to delete it, if the file exists but is unreadable,
        invalid JSON, or the wrong shape -- loud rather than a silent reset, since quietly restarting
        21 lanes from zero counters re-grants relaunch budget a lane may have already burned through.
    """
    path = fleet_state_path(log_dir)
    if not path.exists():
        logging.info(
            f"run_fleet: no supervisor state file at {path}; treating this as a first run "
            "(every lane starts with a clean phase index and relaunch budget)."
        )
        return 0

    # A refusal must name the file and the remedy: the operator is looking at
    # a stalled 21-box fleet, not a traceback to interpret.
    remedy = f"Delete {path} to start fresh (every lane's counters restart from zero)."
    try:
        raw = path.read_text()
    except OSError as exc:
        raise ValueError(
            f"run_fleet: could not read the supervisor state file {path}: {exc}. {remedy}"
        ) from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Re-raised (though JSONDecodeError is already a ValueError) since on
        # its own it names a line and column, not the file to delete.
        raise ValueError(
            f"run_fleet: the supervisor state file {path} is not valid JSON: {exc}. {remedy}"
        ) from exc

    # Checks the file's own structure only, never agreement with the
    # in-memory roster: a stored `phase_index` legitimately exceeds this
    # invocation's phase count when resuming `--phase induction` over a
    # `--phase both` run.
    if not isinstance(document, dict):
        raise ValueError(
            f"run_fleet: the supervisor state file {path} is not a JSON object "
            f"(found {type(document).__name__}). {remedy}"
        )
    stored = document.get("lanes")
    if not isinstance(stored, dict):
        raise ValueError(
            f"run_fleet: the supervisor state file {path} has no 'lanes' object "
            f"(found {type(stored).__name__}). {remedy}"
        )

    for key in sorted(set(stored) - set(runs)):
        logging.info(
            f"run_fleet: lane {key!r} is in {path} but not in this invocation's lanes; "
            "ignoring its persisted state (a --lanes subset, or a rung removed since)."
        )

    monotonic_now = time.monotonic()
    epoch_now = time.time()
    resumed = 0
    for key in sorted(runs):
        entry = stored.get(key)
        if entry is None:
            logging.info(
                f"run_fleet: lane {key!r} has no entry in {path}; starting it clean "
                "(a --lanes subset last time, or a rung added since)."
            )
            continue
        if not isinstance(entry, dict):
            raise ValueError(
                f"run_fleet: lane {key!r} in the supervisor state file {path} is not a "
                f"JSON object (found {type(entry).__name__}). {remedy}"
            )
        missing = [
            name for name in _STATE_PLAIN_FIELDS + _STATE_CLOCK_FIELDS if name not in entry
        ]
        if missing:
            # Partial application isn't an option: a lane restored with some
            # counters and not others is neither resumed nor clean.
            raise ValueError(
                f"run_fleet: lane {key!r} in the supervisor state file {path} is missing "
                f"{', '.join(missing)}. {remedy}"
            )

        run = runs[key]
        for name in _STATE_PLAIN_FIELDS:
            setattr(run, name, entry[name])
        # 0.0 and None are each field's own "unset" sentinel and are not
        # interchangeable: `_apply_restart_policy` branches on
        # `pending_relaunch_at is not None`, so a stray 0.0 there would read
        # as an expired deadline and relaunch every resumed lane at once.
        restored_start = _epoch_to_monotonic(
            entry["lane_started_at_epoch"], monotonic_now=monotonic_now, epoch_now=epoch_now
        )
        run.lane_started_at = 0.0 if restored_start is None else restored_start
        run.pending_relaunch_at = _epoch_to_monotonic(
            entry["pending_relaunch_at_epoch"],
            monotonic_now=monotonic_now,
            epoch_now=epoch_now,
        )
        resumed += 1

    logging.info(f"run_fleet: resumed {resumed} lane(s) from {path}.")
    return resumed


def _phase_sequence(phase: str) -> tuple[str, ...]:
    """Map a ``--phase`` CLI value onto the ordered subprocess phases each lane runs.

    A lane's instance shuts down (`_advance_finished`) only once its last
    scheduled phase exits successfully and that phase was "deduction", so an
    induction-only invocation never shuts its boxes down.

    Parameters
    ----------
    phase : str
        CLI phase value to map.

    Returns
    -------
    tuple[str, ...]
        Ordered subprocess phases for each lane.
    """
    if phase == "induction":
        return ("induction",)
    if phase == "deduction":
        return ("deduction",)
    if phase == "both":
        return ("induction", "deduction")
    raise ValueError(f"run_fleet: unknown --phase {phase!r}; expected induction/deduction/both")


def _start_phase(run: "_LaneRun", log_dir: Path) -> None:
    """Launch `run`'s CURRENT phase as a subprocess; append its log to ``<key>.log``."""
    phase = run.current_phase
    if phase is None or phase == "shutdown":
        raise RuntimeError(f"_start_phase: lane {run.lane.key} has no runnable current phase")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run.lane.key}.log"
    cmd = _lane_env.lane_command(run.lane, phase)
    env = _lane_env.lane_env(run.lane, phase)
    logging.info(f"run_fleet[{run.lane.key}]: launching phase={phase!r}: {' '.join(cmd)}")
    # Append mode: a truncating mode would lose the family gate's one-time
    # healthy-serve line the moment a relaunch or later phase started.
    with open(log_path, "a") as log_file:
        run.proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)
    run.started_at = time.monotonic()
    if not run.lane_started_at:
        run.lane_started_at = run.started_at  # first launch only


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launch each lane in `keys` at its current phase, ``LAUNCH_STAGGER_SECONDS`` apart."""
    for i, key in enumerate(keys):
        if i:
            time.sleep(LAUNCH_STAGGER_SECONDS)
        _start_phase(runs[key], log_dir)


def _lane_gate_passed(run: _LaneRun, log_dir: Path) -> bool:
    """Check whether `run`'s log has ever produced a healthy-serve line.

    Sticky and incremental, not a bounded `_tail_log` read: the healthy-serve
    line is a one-time event near the start of a lane's log that would
    scroll out of any fixed byte window under gigabytes of later chatter.
    Once found it latches; until then only bytes appended since
    `gate_scan_offset` are scanned, advancing only over whole lines so a
    line split across two reads isn't half-consumed then missed.

    Parameters
    ----------
    run : _LaneRun
        Lane runtime state whose log and gate state are checked.
    log_dir : Path
        Directory containing lane log files.

    Returns
    -------
    bool
        Whether a healthy-serve line has been found.
    """
    if run.gate_passed:
        return True

    path = log_dir / f"{run.lane.key}.log"
    try:
        size = path.stat().st_size
    except OSError:
        return False

    offset = run.gate_scan_offset
    if size < offset:
        offset = 0  # file shrank (truncated/replaced) -- rescan from the start

    try:
        with open(path, "rb") as f:
            f.seek(offset)
            chunk = f.read()
    except OSError:
        return False

    if not chunk:
        run.gate_scan_offset = offset
        return False

    consumed = len(chunk)
    if not chunk.endswith(b"\n"):
        last_newline = chunk.rfind(b"\n")
        if last_newline == -1:
            # No complete line yet at all; do not advance the offset -- the
            # next call re-reads this same (still-growing) partial line.
            run.gate_scan_offset = offset
            return False
        consumed = last_newline + 1
        chunk = chunk[:consumed]

    run.gate_scan_offset = offset + consumed
    text = chunk.decode("utf-8", errors="replace")
    if any(is_serve_healthy(line) for line in text.splitlines()):
        run.gate_passed = True
        return True
    return False


def _monitor_tick(
    runs: dict[str, _LaneRun], log_dir: Path, tick: int, presence: _Presence
) -> None:
    """Run one polling pass over every lane: refresh presence, print the table, alert.

    A sweep that raises is logged and skipped, leaving `presence` untouched (a failed sweep tells
    you nothing); one that returns, even empty, updates `presence` since that is real information
    (see `_Presence`).

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state for every lane.
    log_dir : Path
        Directory containing lane log files.
    tick : int
        1-based; the describe sweep runs on tick 1 and every
        ``DESCRIBE_EVERY_N_TICKS``-th tick after.
    presence : _Presence
        Presence state updated by successful describe sweeps.
    """
    if tick == 1 or tick % DESCRIBE_EVERY_N_TICKS == 0:
        try:
            rows = _config.load_fleet_module("fleet_status").fleet_rows()
        except Exception as exc:  # noqa: BLE001 -- one bad sweep must not crash the monitor
            logging.warning(f"run_fleet: describe_instances sweep failed this tick: {exc}")
        else:
            presence.observe({row["lane"] for row in rows})

    print(f"\n=== fleet tick {tick} ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    for key in sorted(runs):
        run = runs[key]
        alive = run.proc is not None and run.proc.poll() is None
        status = "halted" if run.halted else ("done" if run.done else (run.current_phase or "?"))
        # _tail_log drops its first line when it seeks: a newline-free 4 KiB window blanked this.
        last_line = _tail_log(log_dir, key, n=1, max_bytes=65536)
        print(f"{key:<28} status={status:<10} alive={str(alive):<5} last: {last_line[-120:]}")

        if run.proc is not None and not alive and not run.halted and not run.done:
            rc = run.proc.returncode
            if rc not in (0, None):
                print(f"ALERT [{key}]: process exited non-zero (rc={rc}).")

        if presence.lanes is not None and alive and key not in presence.lanes:
            print(f"ALERT [{key}]: subprocess is still running but its instance is "
                  "gone or shutting down.")

        if run.lane_started_at:
            # Keys on cumulative age since first launch, not the latest relaunch.
            age_hours = (time.monotonic() - run.lane_started_at) / 3600
            budget = 2 * run.lane.budget_hours
            if age_hours > budget:
                print(f"ALERT [{key}]: wall clock {age_hours:.1f}h exceeds 2x budget "
                      f"({budget}h).")


def _apply_restart_policy(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence) -> None:
    """Relaunch or halt every lane whose subprocess exited non-zero this tick.

    Applies `_policy.classify_exit`'s verdict through `_policy.decide_relaunch`
    (the one place either supervisor's relaunch cap is enforced, shared with
    `run_shards.py`). This function owns only the tick-driven half: it never
    sleeps, since blocking in one lane's backoff would stall the other
    twenty, so a non-zero `decision.delay_seconds` becomes a
    `pending_relaunch_at` deadline re-checked on later ticks instead
    (`run_shards.py` sleeps the same delay; only the scheduling differs).

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state for every lane.
    log_dir : Path
        Directory containing lane log files.
    presence : _Presence
        Latest instance-presence state for reclaim classification.
    """
    now = time.monotonic()
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue

        if run.pending_relaunch_at is not None:
            if now < run.pending_relaunch_at:
                continue  # still backing off; do not touch this lane this tick
            run.pending_relaunch_at = None
            _start_phase(run, log_dir)
            continue

        rc = run.proc.poll()
        if rc is None or rc == 0:
            continue  # still running, or a clean exit (handled by _advance_finished)

        decision = _policy.count_and_decide(
            run, _tail_log(log_dir, key), presence.present(key), rc)

        if decision.action == "halt":
            run.halted = True
            run.halt_reason = decision.reason
            logging.error(f"run_fleet[{key}]: HALTED -- {run.halt_reason}")
            continue

        logging.warning(f"run_fleet[{key}]: {decision.reason}")
        if decision.delay_seconds:
            run.pending_relaunch_at = now + decision.delay_seconds  # deadline, not a sleep
        else:
            _start_phase(run, log_dir)


def _check_cot(runs: dict[str, _LaneRun], store_factory: Callable[[], Any] = build_results_store) -> None:
    """Run the CoT-ON assertion once per lane; halt any lane below `COT_MIN_FRACTION`."""
    pending = [
        (key, run) for key, run in runs.items()
        if not (run.cot_checked or run.halted or run.done
                or run.current_phase != "induction")
    ]
    if not pending:
        return
    try:
        store = store_factory()  # once per tick, not once per unchecked lane
    except Exception as exc:  # noqa: BLE001 -- a store failure must not crash the monitor
        logging.warning(f"run_fleet: reasoning_fraction store unavailable: {exc}")
        return
    for key, run in pending:
        try:
            # intens only: a wiring check ("did the toggle reach the model"),
            # not a quality check -- an all-arms pool would halt lanes that
            # collapse on the long extens listing, which the study measures.
            fraction = reasoning_fraction(
                store, run.lane.key, run.lane.tag, infos=("intens",)
            )
        except Exception as exc:  # noqa: BLE001 -- a store failure must not crash the monitor
            logging.warning(f"run_fleet[{key}]: reasoning_fraction check failed: {exc}")
            continue
        if fraction is None:
            continue  # nothing landed yet -- check again next tick
        run.cot_checked = True
        if fraction < COT_MIN_FRACTION:
            run.halted = True
            run.halt_reason = f"CoT-ON check failed: {fraction:.1%} < {COT_MIN_FRACTION:.0%}"
            if run.proc is not None and run.proc.poll() is None:
                run.proc.terminate()
            logging.error(
                "\n".join(
                    [
                        "=" * 72,
                        f"run_fleet[{key}]: HALTING LANE -- silently non-thinking data.",
                        f"  measured reasoning fraction : {fraction:.1%}",
                        f"  required minimum (COT_MIN_FRACTION): {COT_MIN_FRACTION:.0%}",
                        "  Below-threshold data is worse than no data -- this lane will "
                        "NOT be relaunched automatically.",
                        "=" * 72,
                    ]
                )
            )


def _advance_finished(runs: dict[str, _LaneRun], log_dir: Path) -> None:
    """Advance every cleanly exited lane to its next phase, or shut it down."""
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        if run.proc.poll() != 0:
            continue  # not a clean exit (still running, or handled by the restart policy)

        if run.current_phase == "deduction":
            # Anchored on `lane_env.REPO_ROOT` (not the driver's own
            # `runner.results_root()`, which would read this supervisor's own
            # environment) to reproduce the repo-root-anchored default the
            # lane subprocess actually resolved.
            run_dir = (
                _lane_env.REPO_ROOT / "notebooks" / "deduction" / "results" / "runs"
                / f"scaling_{run.lane.key}"
            )
            try:
                # Re-spooling here (cheap: the driver's own prune already left
                # only manifest.json) confirms the spool before this
                # supervisor destroys the box, rather than trusting an
                # already-exited process's earlier attempt. `SystemExit` is
                # caught explicitly since the driver's module-scope guard
                # raises it, and a failure here must not kill the supervisor.
                _deduction_driver().spool_to_s3(run_dir, run.lane.key)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 -- see comment above
                run.spool_error = f"{type(exc).__name__}: {exc}"
                logging.error(f"run_fleet[{key}]: spool sync failed: {run.spool_error}")

        run.phase_index += 1
        if run.current_phase is not None:
            _start_phase(run, log_dir)
            continue

        # Shut down only if a deduction phase ran this invocation: an
        # induction-only run leaves the instance up for a later
        # `--phase deduction` invocation.
        if "deduction" in run.phases:
            logging.info(f"run_fleet[{key}]: all phases complete; shutting down its instance.")
            cmd = _lane_env.lane_command(run.lane, "shutdown")
            env = _lane_env.lane_env(run.lane, "shutdown")
            subprocess.run(cmd, env=env, check=False)
        run.done = True


def _tick(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence, tick: int) -> None:
    """Run one monitor pass, ending with the state save.

    Saved at the END of every tick, so the most a supervisor-host failure can
    cost is the tick in progress.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state for every lane.
    log_dir : Path
        Directory containing lane logs and state.
    presence : _Presence
        Latest instance-presence state.
    tick : int
        1-based monitor-pass number.
    """
    time.sleep(MONITOR_INTERVAL_SECONDS)
    _monitor_tick(runs, log_dir, tick, presence)
    _apply_restart_policy(runs, log_dir, presence)
    _check_cot(runs)
    _advance_finished(runs, log_dir)
    save_fleet_state(runs, log_dir)


def _all_terminal(runs: dict[str, _LaneRun]) -> bool:
    """Check whether every lane has halted or fully finished its phase sequence."""
    return all(run.halted or run.done for run in runs.values())


def _run_fleet(
    lanes: dict[str, _lane_env.Lane],
    phase_sequence: tuple[str, ...],
    *,
    gate: bool,
    log_dir: Path,
    phase_name: str,
) -> None:
    """Launch and supervise every lane in `lanes` to completion or halt.

    Tier D, then tier A, staggered. Then, unless `gate` is False or no
    ``GATE_MODELS`` lane is selected, a blocking wait for every gate lane to
    report a healthy serve -- that wait runs full monitor ticks, so a gate
    lane's crash is still retried or halted promptly. Then tiers B and C, and a
    monitor loop until every lane is halted or done.

    Parameters
    ----------
    lanes : dict[str, _lane_env.Lane]
        Lanes to launch and supervise, keyed by lane key.
    phase_sequence : tuple[str, ...]
        Ordered phases each lane runs.
    gate : bool
        Whether to wait for gate lanes before launching tiers B and C.
    log_dir : Path
        Directory containing lane logs and supervisor state.
    phase_name : str
        Requested phase name for the run banner.
    """
    runs = {key: _LaneRun(lane=lane, phases=phase_sequence) for key, lane in lanes.items()}
    # After `runs` is built (every lane exists to restore into) and before
    # the first launch (so `_launch_batch` sees restored state already).
    resumed = load_fleet_state(runs, log_dir)
    logging.info(
        f"run_fleet: {resumed} of {len(runs)} lane(s) resumed from a previous supervisor; "
        f"the rest start clean."
    )

    tier_d = [k for k in lanes if lanes[k].tier == "D"]
    tier_a = [k for k in lanes if lanes[k].tier == "A"]
    tier_bc = [k for k in lanes if lanes[k].tier in ("B", "C")]

    _launch_batch(runs, tier_d, log_dir)
    _launch_batch(runs, tier_a, log_dir)

    presence = _Presence()
    tick = 0

    gate_keys = [k for k in GATE_MODELS if k in runs] if gate else []
    while gate_keys and not all(_lane_gate_passed(runs[k], log_dir) for k in gate_keys):
        tick += 1
        _tick(runs, log_dir, presence, tick)
        if all(runs[k].halted for k in gate_keys):
            logging.error(
                "run_fleet: FAMILY GATE FAILED -- every GATE_MODELS lane halted; NOT "
                "launching tiers B/C. Investigate FLEET_IMAGE before retrying."
            )
            # Halt, not done: these lanes were never launched, so without a
            # terminal state `_all_terminal` never returns True.
            for bc_key in tier_bc:
                runs[bc_key].halted = True
                runs[bc_key].halt_reason = (
                    "never launched: family gate failed (every GATE_MODELS lane halted)"
                )
            save_fleet_state(runs, log_dir)  # the `break` skips the loop's own save
            gate_keys = []  # stop waiting; skip the else-clause launch below
            break
    else:
        logging.info("run_fleet: family gate passed (or was skipped) -- launching tiers B and C.")
        _launch_batch(runs, tier_bc, log_dir)

    while not _all_terminal(runs):
        tick += 1
        _tick(runs, log_dir, presence, tick)

    halted = {key: run.halt_reason for key, run in runs.items() if run.halted}
    if halted:
        logging.error(f"run_fleet: fleet finished with {len(halted)} halted lane(s): {halted}")
    # Printed even when no lane halted: a spool failure does not halt a lane,
    # so this is the only place it would otherwise surface.
    spool_errors = {key: run.spool_error for key, run in runs.items() if run.spool_error}
    if spool_errors:
        logging.error(
            f"run_fleet: {len(spool_errors)} lane(s) had a post-deduction spool failure "
            f"(data is collected locally, NOT confirmed in S3): {spool_errors}"
        )
    if phase_name == "induction":
        print(
            "\nrun_fleet: induction-only run complete. Boxes are left RUNNING on purpose "
            "(the deduction phase may reuse them) -- run "
            "`scripts/fleet/fleet_teardown.py --terminate` when you are done with them."
        )
