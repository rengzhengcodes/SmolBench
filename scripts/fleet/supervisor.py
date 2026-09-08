"""Supervise fleet launch, monitoring, restart, gating, spooling, and shutdown.

Persisted state preserves relaunch budgets across supervisor replacement.
Fleet modules load by path because ``scripts/fleet`` is not a package.
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
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional, Sequence

from smolbench.evals.results_store import ReplicateAddress, resolve_store

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config() -> ModuleType:
    # _config provides its own loader; scripts/fleet is not a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Eager loading validates the roster before any subprocess launch.
_lane_env = _config.load_fleet_module("lane_env")

# Share restart decisions with run_shards.
_policy = _config.load_fleet_module("policy")


# Anchor logs at the repo root because entry points may use any cwd.
LOG_DIR: Path = _lane_env.REPO_ROOT / "notebooks" / "induction" / "results" / "fleet_logs"

#: Read enough tail data to retain reclaim patterns.
TAIL_MAX_BYTES = 262144


def _tail_log(log_dir: Path, key: str, n: int = 40, *, max_bytes: int = TAIL_MAX_BYTES) -> str:
    """Return trailing lane-log lines, or ``""`` if unreadable.

    Parameters
    ----------
    log_dir : Path
        Lane-log directory.
    key : str
        Log lane key.
    n : int, optional
        Trailing line count.
    max_bytes : int, optional
        Tail byte limit.

    Returns
    -------
    str
        Trailing lines or ``""``.
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


# Match ec2's ready line, not its earlier in-flight line.
SERVE_HEALTHY_RE = re.compile(r"serve_model: '.+?' is up at http://\S+")


def is_serve_healthy(line: str) -> bool:
    """Check whether `line` (logging prefix allowed) is ec2.py's healthy-serve log line."""
    return SERVE_HEALTHY_RE.search(line) is not None


# 0.5 separates failed 0–11% toggles from working 78–100% protocols.
COT_MIN_FRACTION = 0.5
#: Longer responses carry reasoning because quiz answers are bare integers.
COT_CONTENT_REASONING_MIN_CHARS = 200


def reasoning_fraction(
    store: Any,
    model: str,
    tag: str,
    seed: Optional[int] = None,
    infos: Optional[Sequence[str]] = None,
) -> Optional[float]:
    """Measure landed marks with reasoning evidence.

    Long responses cover protocols that put chains outside reasoning markup.

    Parameters
    ----------
    store : Any
        Landed-mark store.
    model : str
        Model key.
    tag : str
        Experiment tag.
    seed : Optional[int], optional
        Replicate seed.
    infos : Optional[Sequence[str]], optional
        Information arms.

    Returns
    -------
    Optional[float]
        Reasoning fraction, or None if no marks landed.
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
    """Build the production results store; kept separate for test fakes."""
    return resolve_store(_lane_env.run_study.EXPERIMENT.results_dir)


GATE_MODELS = ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b")
LAUNCH_STAGGER_SECONDS = 30
MONITOR_INTERVAL_SECONDS = 60
DESCRIBE_EVERY_N_TICKS = 5


def preflight(lanes: Sequence[_lane_env.Lane]) -> dict[str, int]:
    """Warm tokenizers and derive completion budgets before provisioning.

    Parameters
    ----------
    lanes : Sequence[_lane_env.Lane]
        Lanes to check.

    Returns
    -------
    dict[str, int]
        Budgets by lane key.

    Raises
    ------
    SystemExit
        Any failed lane.
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
    """Return the image digest for the banner without blocking launch."""
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
        # A multi-arch manifest exposes architecture digests here.
        entries = manifest.get("manifests") or []
        if entries:
            digest = entries[0].get("digest")
    if not digest:
        logging.info("fleet_image_digest: manifest JSON had no recognisable digest field.")
        return None
    return digest


# Only _phase_sequence is import-safe for the dry-run plan.


def _deduction_driver() -> ModuleType:
    """Load deduction lazily because its setup requires lane environment."""
    return _config.load_module_by_path(
        "run_fleet_deduction_run_study_dep",
        _lane_env.REPO_ROOT / "notebooks" / "deduction" / "run_study.py",
    )


@dataclass
class _Presence:
    """Describe sweep state that distinguishes unknown from confirmed empty."""

    lanes: Optional[set] = None
    ever_seen: bool = False

    def observe(self, swept: set) -> None:
        """Update presence from a successful sweep."""
        if swept:
            self.lanes = set(swept)
            self.ever_seen = True
        elif self.ever_seen:
            self.lanes = set()
        # Empty before any sighting remains unknown.

    def present(self, key: str) -> bool:
        """Return presence, treating unsighted fleets as unknown and present.

        Parameters
        ----------
        key : str
            Lane key.

        Returns
        -------
        bool
            Presence result.
        """
        if not self.ever_seen:
            return True
        return key in self.lanes


@dataclass
class _LaneRun:
    """Per-lane runtime state."""

    lane: _lane_env.Lane
    #: Ordered phases for this invocation.
    phases: tuple[str, ...]
    phase_index: int = 0
    proc: Optional[subprocess.Popen] = None
    #: First launch only, preserving the cumulative budget alert.
    lane_started_at: float = 0.0
    #: Crash relaunch count for policy caps.
    crash_relaunches: int = 0
    #: Reclaim relaunch count for policy caps.
    reclaim_relaunches: int = 0
    #: Pending relaunch deadline; None when absent.
    pending_relaunch_at: Optional[float] = None
    cot_checked: bool = False
    #: Latched healthy-serve result avoids later I/O.
    gate_passed: bool = False
    #: Scanned byte offset; reset after log replacement.
    gate_scan_offset: int = 0
    halted: bool = False
    halt_reason: str = ""
    done: bool = False
    #: Post-deduction spool failure; report without halting collected data.
    spool_error: str = ""

    @property
    def current_phase(self) -> Optional[str]:
        """The phase this lane runs now, or None once `phases` is exhausted."""
        if self.phase_index >= len(self.phases):
            return None
        return self.phases[self.phase_index]


# Rewrite one state file each tick to preserve relaunch budgets after replacement.
FLEET_STATE_FILENAME = "fleet_state.json"

#: Shared persisted fields prevent save/load drift.
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

#: Monotonic fields persisted as epoch timestamps for cross-process resume.
_STATE_CLOCK_FIELDS = ("lane_started_at_epoch", "pending_relaunch_at_epoch")


def fleet_state_path(log_dir: Path) -> Path:
    """Return the state path beside its lane logs.

    Parameters
    ----------
    log_dir : Path
        Lane-log directory.

    Returns
    -------
    Path
        State-file path.
    """
    return log_dir / FLEET_STATE_FILENAME


def _monotonic_to_epoch(
    value: Optional[float], *, monotonic_now: float, epoch_now: float
) -> Optional[float]:
    """Convert monotonic time to epoch time for cross-process persistence.

    Parameters
    ----------
    value : Optional[float]
        Monotonic timestamp.
    monotonic_now : float
        Reference monotonic timestamp.
    epoch_now : float
        Reference epoch timestamp.

    Returns
    -------
    Optional[float]
        Equivalent epoch timestamp, or None.
    """
    if value is None:
        return None
    return epoch_now - (monotonic_now - value)


def _epoch_to_monotonic(
    value: Optional[float], *, monotonic_now: float, epoch_now: float
) -> Optional[float]:
    """Convert persisted epoch time to this process's monotonic frame.

    Parameters
    ----------
    value : Optional[float]
        Persisted epoch timestamp.
    monotonic_now : float
        Reference monotonic timestamp.
    epoch_now : float
        Reference epoch timestamp.

    Returns
    -------
    Optional[float]
        Equivalent monotonic timestamp, or None.
    """
    if value is None:
        return None
    return monotonic_now - (epoch_now - value)


def save_fleet_state(runs: dict[str, _LaneRun], log_dir: Path) -> None:
    """Atomically save resumable lane state.

    Processes and static lane fields are rebuilt rather than persisted.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state by lane key.
    log_dir : Path
        State-file directory.
    """
    # One reference pair keeps every saved lane consistent.
    monotonic_now = time.monotonic()
    epoch_now = time.time()

    lanes: dict[str, dict[str, Any]] = {}
    for key, run in runs.items():
        entry: dict[str, Any] = {name: getattr(run, name) for name in _STATE_PLAIN_FIELDS}
        # Unset timestamps become JSON null.
        entry["lane_started_at_epoch"] = _monotonic_to_epoch(
            run.lane_started_at if run.lane_started_at else None,
            monotonic_now=monotonic_now,
            epoch_now=epoch_now,
        )
        entry["pending_relaunch_at_epoch"] = _monotonic_to_epoch(
            run.pending_relaunch_at, monotonic_now=monotonic_now, epoch_now=epoch_now
        )
        lanes[key] = entry

    document = {"lanes": lanes}

    log_dir.mkdir(parents=True, exist_ok=True)
    path = fleet_state_path(log_dir)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as state_file:
        json.dump(document, state_file, indent=2, sort_keys=True)
        state_file.write("\n")
    os.replace(tmp, path)


def load_fleet_state(runs: dict[str, _LaneRun], log_dir: Path) -> int:
    """Restore persisted lane state in place.

    Processes relaunch; the driver skips already-landed work.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state to restore.
    log_dir : Path
        State-file directory.

    Returns
    -------
    int
        Resumed lane count; zero when absent.

    Raises
    ------
    ValueError
        Unreadable, invalid, or malformed state file; name it for deletion.
    """
    path = fleet_state_path(log_dir)
    if not path.exists():
        logging.info(
            f"run_fleet: no supervisor state file at {path}; treating this as a first run "
            "(every lane starts with a clean phase index and relaunch budget)."
        )
        return 0

    # Name the file and remedy for stalled fleets.
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
        # Include the file and remedy, not only JSON's position.
        raise ValueError(
            f"run_fleet: the supervisor state file {path} is not valid JSON: {exc}. {remedy}"
        ) from exc

    # Do not require phase-count agreement across different invocations.
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
            # Reject partial restores; counters must remain consistent.
            raise ValueError(
                f"run_fleet: lane {key!r} in the supervisor state file {path} is missing "
                f"{', '.join(missing)}. {remedy}"
            )

        run = runs[key]
        for name in _STATE_PLAIN_FIELDS:
            setattr(run, name, entry[name])
        # Preserve distinct unset sentinels to avoid immediate mass relaunch.
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
    """Map a CLI phase to ordered subprocess phases.

    Only a completed deduction phase shuts down its instance.

    Parameters
    ----------
    phase : str
        CLI phase.

    Returns
    -------
    tuple[str, ...]
        Ordered phases.
    """
    if phase == "induction":
        return ("induction",)
    if phase == "deduction":
        return ("deduction",)
    if phase == "both":
        return ("induction", "deduction")
    raise ValueError(f"run_fleet: unknown --phase {phase!r}; expected induction/deduction/both")


def _start_phase(run: "_LaneRun", log_dir: Path) -> None:
    """Launch the current phase and append to its lane log."""
    phase = run.current_phase
    if phase is None or phase == "shutdown":
        raise RuntimeError(f"_start_phase: lane {run.lane.key} has no runnable current phase")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run.lane.key}.log"
    cmd = _lane_env.lane_command(run.lane, phase)
    env = _lane_env.lane_env(run.lane, phase)
    logging.info(f"run_fleet[{run.lane.key}]: launching phase={phase!r}: {' '.join(cmd)}")
    # Append preserves the gate's one-time healthy line across relaunches.
    with open(log_path, "a") as log_file:
        run.proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)
    started_at = time.monotonic()
    if not run.lane_started_at:
        run.lane_started_at = started_at  # first launch only


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launch lanes at their current phase with the configured stagger."""
    for i, key in enumerate(keys):
        if i:
            time.sleep(LAUNCH_STAGGER_SECONDS)
        _start_phase(runs[key], log_dir)


def _lane_gate_passed(run: _LaneRun, log_dir: Path) -> bool:
    """Return whether a lane log has produced the healthy-serve line.

    Scan incrementally and latch success so the one-time line cannot scroll out.

    Parameters
    ----------
    run : _LaneRun
        Lane runtime state.
    log_dir : Path
        Lane-log directory.

    Returns
    -------
    bool
        Healthy-line result.
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
            # Keep partial lines for the next scan.
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
    """Refresh presence, print lane status, and emit alerts.

    Failed describe sweeps leave presence unchanged; successful empty sweeps do not.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state by lane.
    log_dir : Path
        Lane-log directory.
    tick : int
        One-based monitor-pass number.
    presence : _Presence
        Presence state.
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
        # A larger tail avoids blank output after a mid-line seek.
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
            # Use first-launch age, not the latest relaunch.
            age_hours = (time.monotonic() - run.lane_started_at) / 3600
            budget = 2 * run.lane.budget_hours
            if age_hours > budget:
                print(f"ALERT [{key}]: wall clock {age_hours:.1f}h exceeds 2x budget "
                      f"({budget}h).")


def _apply_restart_policy(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence) -> None:
    """Apply restart policy to non-zero exits without blocking other lanes.

    Backoff becomes a later deadline so one lane cannot stall the fleet.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state by lane.
    log_dir : Path
        Lane-log directory.
    presence : _Presence
        Instance-presence state.
    """
    now = time.monotonic()
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue

        if run.pending_relaunch_at is not None:
            if now < run.pending_relaunch_at:
                continue  # Still backing off.
            run.pending_relaunch_at = None
            _start_phase(run, log_dir)
            continue

        rc = run.proc.poll()
        if rc is None or rc == 0:
            continue  # Running or clean; advance handles the latter.

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
    """Check CoT once per lane and halt below the minimum fraction."""
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
            # Intens checks toggle wiring, not performance on extens listings.
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
    """Advance clean exits or shut down completed deduction lanes."""
    for key, run in runs.items():
        if run.halted or run.done or run.proc is None:
            continue
        if run.proc.poll() != 0:
            continue  # not a clean exit (still running, or handled by the restart policy)

        if run.current_phase == "deduction":
            # Match the lane subprocess's repo-root result path.
            run_dir = (
                _lane_env.REPO_ROOT / "notebooks" / "deduction" / "results" / "runs"
                / f"scaling_{run.lane.key}"
            )
            try:
                # Confirm spool before teardown; SystemExit must not kill supervision.
                _deduction_driver().spool_to_s3(run_dir, run.lane.key)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 -- see comment above
                run.spool_error = f"{type(exc).__name__}: {exc}"
                logging.error(f"run_fleet[{key}]: spool sync failed: {run.spool_error}")

        run.phase_index += 1
        if run.current_phase is not None:
            _start_phase(run, log_dir)
            continue

        # Induction-only runs retain boxes for later deduction.
        if "deduction" in run.phases:
            logging.info(f"run_fleet[{key}]: all phases complete; shutting down its instance.")
            cmd = _lane_env.lane_command(run.lane, "shutdown")
            env = _lane_env.lane_env(run.lane, "shutdown")
            subprocess.run(cmd, env=env, check=False)
        run.done = True


def _tick(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence, tick: int) -> None:
    """Run a monitor pass and save state last.

    A host failure loses at most the current tick.

    Parameters
    ----------
    runs : dict[str, _LaneRun]
        Runtime state by lane.
    log_dir : Path
        Logs and state directory.
    presence : _Presence
        Presence state.
    tick : int
        One-based monitor-pass number.
    """
    time.sleep(MONITOR_INTERVAL_SECONDS)
    _monitor_tick(runs, log_dir, tick, presence)
    _apply_restart_policy(runs, log_dir, presence)
    _check_cot(runs)
    _advance_finished(runs, log_dir)
    save_fleet_state(runs, log_dir)


def _all_terminal(runs: dict[str, _LaneRun]) -> bool:
    """Return whether every lane halted or completed."""
    return all(run.halted or run.done for run in runs.values())


def _run_fleet(
    lanes: dict[str, _lane_env.Lane],
    phase_sequence: tuple[str, ...],
    *,
    gate: bool,
    log_dir: Path,
    phase_name: str,
) -> None:
    """Launch and supervise lanes to completion or halt.

    Gate tiers D/A before B/C so unhealthy image families limit provisioning.

    Parameters
    ----------
    lanes : dict[str, _lane_env.Lane]
        Lanes by key.
    phase_sequence : tuple[str, ...]
        Ordered lane phases.
    gate : bool
        Gate B/C on healthy D/A lanes.
    log_dir : Path
        Logs and state directory.
    phase_name : str
        Requested phase name.
    """
    runs = {key: _LaneRun(lane=lane, phases=phase_sequence) for key, lane in lanes.items()}
    # Restore after all lanes exist and before any launch.
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
            # Mark unlaunched lanes terminal so the monitor can finish.
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
    # Spool failure does not halt a lane, so report it separately.
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
