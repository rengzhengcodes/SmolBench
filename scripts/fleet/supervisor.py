"""The live 21-lane supervision loop: launch, monitor, restart, gate, spool.

This module owns everything that happens once an operator has committed to a
real launch: the pre-flight budget derivation, the staggered tier-D/tier-A
launch, the FAMILY GATE that holds tiers B/C behind `GATE_MODELS`, the
per-tick monitor table and its alerts, the application of the shared restart
policy, the CoT-ON assertion, the phase advance, the post-deduction S3 spool
and the box shutdown. `_run_fleet` is its one entry point.

It deliberately does NOT own three things:

- the roster and the per-lane environment -- ``scripts/fleet/lane_env.py``'s
  (`Lane`, ``LANES``, ``lane_env``, ``lane_command``), reached here through
  the module-level `_lane_env` binding;
- the restart VOCABULARY -- ``scripts/fleet/policy.py``'s
  (``classify_exit``, the relaunch caps, the backoff schedule and
  ``decide_relaunch``), reached through `_policy` and shared with
  ``scripts/fleet/run_shards.py`` so one spot reclaim gets one answer
  whichever supervisor is watching. What this module owns is only how that
  answer is SPENT: a tick-driven deadline, never a blocking sleep (see
  `_apply_restart_policy`);
- the command line -- ``scripts/fleet/run_fleet.py``'s, which is now nothing
  but argument parsing, the lane selection and the ``--dry-run`` plan.

Import-time cost is deliberately small: binding `_lane_env` and `_policy`,
and one ``smolbench.evals.results_store`` import for `reasoning_fraction`'s
address type. ``fleet_status.py`` and ``notebooks/deduction/run_study.py``
are loaded LAZILY, on first use, by `_fleet_status_module` and
`_deduction_driver` -- see those functions for why. No AWS SDK is imported at
module scope here or in ``lane_env.py``: ``results_store`` defers ``boto3``
into ``smolbench.evals._aws``, and every ``os.environ`` read it does happens
at call time, not import time, so loading it AFTER ``lane_env``'s
``load_dotenv`` cannot freeze a stale value.

It is loaded BY FILE PATH, never a bare ``import supervisor``:
``scripts/fleet`` has no ``__init__.py`` -- it is not a package -- so a bare
import name is absent from ``sys.path`` for a script launched from an
arbitrary working directory. See ``_config.load_fleet_module``, the loader
every fleet consumer now calls.
"""

from __future__ import annotations

import functools
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
from typing import Any, Callable, Optional, Sequence

from smolbench.evals.results_store import ReplicateAddress, resolve_store

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config():
    """Load ``scripts/fleet/_config.py`` by file path (see its docstring)."""
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        path = Path(__file__).resolve().parent / "_config.py"
        spec = importlib.util.spec_from_file_location(_CONFIG_MODULE_NAME, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[_CONFIG_MODULE_NAME] = module
        spec.loader.exec_module(module)
    return module


# Bootstrapped by hand, and only for `_config` itself: `load_fleet_module` is
# a function ON that module, so it cannot load it. Everything else below goes
# through the loader. Cached under the shared `_CONFIG_MODULE_NAME` key, so
# whichever fleet module happens to run first this process, there is one
# `_config` object -- see `_config.py`'s own module docstring.
_config = _load_fleet_config()

# The roster and the per-lane environment. Eager, at module scope: `LANES` is
# needed on the very first `_run_fleet` call, and loading it here also runs
# `lane_env.py`'s import-time roster `_drift_guard` before any subprocess is
# launched. Through `_config.load_fleet_module`, so `run_fleet.py` and this
# module hold the SAME module object -- one roster per process, and a
# `_drift_guard` that runs once rather than per consumer.
_lane_env = _config.load_fleet_module("lane_env")

# The restart vocabulary -- `classify_exit`, the relaunch caps, the reclaim
# backoff schedule and `decide_relaunch` -- used to be declared in the
# supervisor's own file while `run_shards.py` carried an unrelated set of its
# own, so the same spot reclaim got two different answers depending on which
# supervisor was watching. It now lives in `scripts/fleet/policy.py`, which
# both supervisors load through `_config.load_fleet_module` -- and therefore
# as ONE module object per process, not a copy each.
#
# Loaded eagerly, at module scope, not lazily like `_fleet_status_module`
# below: `policy.py` imports nothing but `re` and `dataclasses`, so it cannot
# fail, read the environment or pull in an AWS SDK, and `_apply_restart_policy`
# needs it on every supervision tick anyway.
_policy = _config.load_fleet_module("policy")


# ---------------------------------------------------------------------------
# Lane logs
# ---------------------------------------------------------------------------
# Anchored on `lane_env.REPO_ROOT` (itself ``__file__``-anchored) per repo
# convention, never cwd-relative, since the entry point may launch from any
# working directory. It sits inside an already-gitignored tree
# (`notebooks/*/results/`), and `*.log` is separately gitignored on top of
# that, so lane logs -- gigabytes of vLLM/CoT chatter over a study run -- never
# enter a commit either way.
LOG_DIR: Path = _lane_env.REPO_ROOT / "notebooks" / "induction" / "results" / "fleet_logs"

#: Byte budget `_tail_log` reads from the END of a lane's log file. Finding
#: 14-03: `_apply_restart_policy` calls `_tail_log` every tick for every lane
#: whose subprocess just exited, and a live lane's log can reach gigabytes
#: over a multi-hour vLLM serve, so reading the WHOLE file every tick does
#: not scale. 256 KiB is deliberately generous relative to the ~40 lines
#: callers ask for: UNDER-reading is not neutral here -- a
#: `_policy.RECLAIM_PATTERNS` match that falls outside the read window would
#: silently reclassify a reclaim as a crash, halting a lane that should have
#: been relaunched.
TAIL_MAX_BYTES = 262144


def _tail_log(log_dir: Path, key: str, n: int = 40, *, max_bytes: int = TAIL_MAX_BYTES) -> str:
    """Return the last `n` lines of lane `key`'s log file, or ``""`` if unreadable.

    Reads at most `max_bytes` (default `TAIL_MAX_BYTES`) from the END of the
    file (seek-from-end), never the whole file -- see `TAIL_MAX_BYTES`'s
    comment for why that budget is generous rather than tight.

    Notes
    -----
    When the file is bigger than `max_bytes`, the read does not start at byte
    0, so its first line is very likely PARTIAL (the seek landed mid-line);
    that line is dropped rather than returned, since a partial line could
    spuriously match or fail to match a pattern a caller checks lines
    against (`is_serve_healthy`, `_policy.RECLAIM_PATTERNS`).
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
        lines = lines[1:]  # drop the partial first line -- see docstring
    return "\n".join(lines[-n:])


# ---------------------------------------------------------------------------
# Serve-health line matching
# ---------------------------------------------------------------------------
# `ec2.serve_model` logs exactly `serve_model: '<model>' is up at
# http://<ip>:8000/v1` once the swapped-in checkpoint is confirmed healthy. The
# earlier in-flight line (`serve_model: requesting '<model>' ...`) must NOT
# match -- that line is what the family gate is waiting to stop seeing.
SERVE_HEALTHY_RE = re.compile(r"serve_model: '.+?' is up at http://\S+")


def is_serve_healthy(line: str) -> bool:
    """Check whether `line` (logging prefix allowed) is ec2.py's healthy-serve log line."""
    return SERVE_HEALTHY_RE.search(line) is not None


# ---------------------------------------------------------------------------
# CoT-ON assertion
# ---------------------------------------------------------------------------
# A DEAD toggle measures ~0-11% (bare integers everywhere); a
# working-but-variable soft protocol measures 78-100%. 0.5 cleanly
# separates the two regimes. (With only 9 intens marks, a 0.9 threshold
# trips on one or two direct answers from a capable model.)
COT_MIN_FRACTION = 0.5
#: A response longer than this counts as a reasoning chain carried in content
#: (the quiz contract asks for a single bare integer). See
#: ``reasoning_fraction``'s Notes.
COT_CONTENT_REASONING_MIN_CHARS = 200


def reasoning_fraction(
    store: Any,
    model: str,
    tag: str,
    seed: Optional[int] = None,
    infos: Optional[Sequence[str]] = None,
) -> Optional[float]:
    """Measure the fraction of a model's landed marks that carry reasoning evidence.

    Parameters
    ----------
    store : Any
        Duck-typed ``ResultsStore`` (``exists``/``load_marks``), injected so this
        is testable with a fake and no S3; production passes `build_results_store`.
    tag : str
        Analysis tag -- unused by the S3 backend, required by ``ReplicateAddress``.
    seed : int or None, optional
        ``None`` uses ``lane_env.run_study.BASE_SEED``, the FIRST replicate a
        lane collects.
    infos : Sequence[str] or None, optional
        Info arms to pool; ``None`` uses ``lane_env.run_study.INFO_TYPES`` (all
        four).

    Returns
    -------
    float or None
        ``None`` when no arm has landed yet for (`model`, `seed`); otherwise the
        fraction of pooled marks with a non-empty ``Mark.reasoning`` OR a
        ``Mark.response`` longer than ``COT_CONTENT_REASONING_MIN_CHARS``.

    Notes
    -----
    Response length counts because models on a SOFT thinking protocol
    (Ministral's [THINK] system prompt, EXAONE's ``enable_thinking``) wrap only
    some chains in think markup, leaving 40-60% of marks with the chain in plain
    ``response``. The quiz contract is "exactly one integer and nothing else",
    so a long response is a chain, while a dead toggle -- bare integers, an
    empty reasoning channel -- still fails.
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

    ``resolve_store`` picks S3 when ``SMOLBENCH_RESULTS_S3`` is set, local
    otherwise; kept out of :func:`reasoning_fraction` so that stays fake-able.
    """
    return resolve_store(_lane_env.run_study.EXPERIMENT.results_dir)


# ---------------------------------------------------------------------------
# Loop constants (exact names/values -- pinned by tests/tooling/test_run_fleet.py)
# ---------------------------------------------------------------------------
GATE_MODELS = ("gemma-4-e2b", "nemotron-3-nano-4b", "ministral-3-3b")
# The relaunch caps and the reclaim backoff schedule that used to sit beside
# `GATE_MODELS`, in the pre-split `run_fleet.py`, are now
# `_policy.MAX_CRASH_RELAUNCHES`, `_policy.MAX_RECLAIM_RELAUNCHES`
# and `_policy.reclaim_backoff_seconds` -- see `scripts/fleet/policy.py` for
# the values and for why a reclaim is no longer retried without limit. They
# are not re-exported here: a module-level alias is exactly the second
# spelling this move exists to remove.
LAUNCH_STAGGER_SECONDS = 30
MONITOR_INTERVAL_SECONDS = 60
DESCRIBE_EVERY_N_TICKS = 5


# ---------------------------------------------------------------------------
# Pre-flight (before any subprocess.Popen)
# ---------------------------------------------------------------------------
def preflight(lanes: Sequence[_lane_env.Lane]) -> dict[str, int]:
    """Warm every lane's tokenizer and derive its completion budget.

    Calls ``lane_env.run_study.completion_budget`` per lane BEFORE any
    subprocess or EC2 provisioning -- pure CPU plus HuggingFace downloads, on a
    machine not yet billing -- so a tokenizer-fetch failure or an under-budget
    verdict cannot surface between a live GPU box and its first request.

    Returns
    -------
    dict[str, int]
        Spec key -> completion-token budget, only when EVERY lane succeeded.

    Raises
    ------
    SystemExit
        If any lane failed, by exception or by ``completion_budget``'s own
        ``SystemExit`` for a budget below ``run_study.MIN_VIABLE_BUDGET``. Both
        kinds are COLLECTED across all lanes (hence ``except (Exception,
        SystemExit)``, since ``SystemExit`` is not an ``Exception``) and printed
        as one table.
    """
    run_study = _lane_env.run_study
    budgets: dict[str, int] = {}
    failures: list[tuple[str, str, str]] = []
    seeds = range(run_study.BASE_SEED, run_study.BASE_SEED + run_study.N_REPLICATES)
    for lane in lanes:
        try:
            budgets[lane.key] = run_study.completion_budget(lane.key, seeds)
        except (Exception, SystemExit) as exc:  # noqa: BLE001 -- collected, see docstring
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
    check for the run banner; it never raises, since it must not block a launch.

    Returns
    -------
    str or None
        For a multi-arch image, a PER-ARCHITECTURE digest (``manifests[0]``),
        which will NOT match the index digest in the ref. ``None``, always
        logged at INFO, when ``docker`` is missing, the inspect call fails, or
        the JSON has no digest field.
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
        # A multi-arch image returns a manifest LIST, not a single manifest with
        # a top-level "config"; fall back to the first platform entry.
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
# Nothing below this point runs at import time; it is reached only from
# `run_fleet.main()`'s live (non-`--dry-run`) path -- with the single
# exception of `_phase_sequence`, which the `--dry-run` plan also calls to
# name each lane's scheduled phases.


@functools.lru_cache(maxsize=1)
def _fleet_status_module():
    """Lazily load ``scripts/fleet/fleet_status.py`` by file path; cached.

    By path, like ``lane_env.py``'s `run_study` loader, to avoid colliding
    with the private module name ``tests/tooling/test_run_fleet.py`` loads
    ``fleet_status.py`` under.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("run_fleet_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@functools.lru_cache(maxsize=1)
def _deduction_driver():
    """Lazily load ``notebooks/deduction/run_study.py`` by file path; cached.

    Finding 14-11: this supervisor used to re-implement the S3 spool upload
    itself (`sync_deduction_spool`, now DELETED), without the driver's own
    ``head_object``/``ContentLength`` verification -- an unverified upload
    followed by a local delete can lose rows silently. Loading the driver and
    calling its OWN ``spool_to_s3`` instead means one verified implementation,
    not two that can drift.

    LAZY on purpose, never imported at module scope: that module pulls in
    ``smolbench.deduction.lean.runner`` (which pulls ``tiktoken``, unneeded by
    every OTHER path through this supervisor) and, at MODULE SCOPE, runs
    ``os.environ.setdefault`` work keyed on ``LEAN_MODEL`` plus a guard that
    raises ``SystemExit`` when ``EC2_EXPERIMENT_TAG`` is not exactly
    ``f"scaling-{LEAN_MODEL}"`` (see that file's module docstring). Neither
    variable is set in THIS process's environment (they are per-lane
    subprocess env, built by ``lane_env.lane_env`` and never written to
    `os.environ` here), so that guard's ``if _RAW_LEAN_MODEL:`` gate is false
    and the whole block -- setdefaults and guard alike -- is skipped on load,
    regardless of which lane's `_advance_finished` call triggers it first.
    Called only from `_advance_finished`.

    Registered in `sys.modules` under a distinct private name BEFORE
    ``exec_module``, exactly as the induction loader at the top of
    ``lane_env.py`` does (a ``@dataclass`` applied inside a module not yet in
    `sys.modules` raises ``AttributeError`` -- see that loader's comment).
    """
    path = _lane_env.REPO_ROOT / "notebooks" / "deduction" / "run_study.py"
    spec = importlib.util.spec_from_file_location("run_fleet_deduction_run_study_dep", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class _Presence:
    """Last describe sweep's lane set, plus whether any lane has EVER been seen.

    Distinguishes three states a `fleet_status.fleet_rows()` sweep can leave a
    lane's presence in: seen THIS sweep (`lanes` is the fresh set), seen
    BEFORE and now gone (`lanes` is an explicit empty ``set()`` -- the fleet
    really is empty), and never seen YET (`lanes` is ``None`` -- unknown).
    Collapsing the last two into "empty" is finding 14-02: a fleet that has
    not finished provisioning its first box looks IDENTICAL, via
    `fleet_rows`, to every region's ``describe_instances`` raising -- both
    return ``[]`` -- so reading an early empty sweep as "everything is gone"
    turned every lane's exit into an unlimited-retry reclaim before a single
    box had even been described successfully.

    Attributes
    ----------
    lanes : set or None
        Lane keys from the most recent sweep that did not raise; ``None``
        means no such sweep has landed yet (or every one so far has come back
        empty with nothing ever seen -- see `observe`).
    ever_seen : bool
        Whether any past sweep has returned a NON-EMPTY lane set.
    """

    lanes: Optional[set] = None
    ever_seen: bool = False

    def observe(self, swept: set) -> None:
        """Update presence from one sweep's raw lane set.

        Parameters
        ----------
        swept : set
            Lane keys ``fleet_status.fleet_rows()`` returned THIS sweep. Call
            only for a sweep that did NOT raise -- see `_monitor_tick`, which
            treats a raising sweep as a separate case (logged and skipped,
            `observe` never runs, `lanes` keeps its last value).

        Notes
        -----
        PURE: no I/O, no AWS, no monitor-loop dependency -- directly
        unit-testable against a bare ``set``. Semantics:

        * non-empty `swept` -> ``lanes = set(swept)``, ``ever_seen = True``.
        * empty `swept` and `ever_seen` -> ``lanes = set()``: a fleet that HAS
          been seen non-empty before and is now empty really is empty -- a
          lane exiting now IS a reclaim.
        * empty `swept` and NOT `ever_seen` -> `lanes` is left UNCHANGED
          (``None`` on the first such call). On a fleet's very first sweeps,
          "not yet provisioned" and "describe_instances failed everywhere"
          both present as an empty list from `fleet_rows`, with no way to
          tell them apart from here; treating either as "everything is gone"
          is exactly the defect this type exists to prevent.
        """
        if swept:
            self.lanes = set(swept)
            self.ever_seen = True
        elif self.ever_seen:
            self.lanes = set()
        # else: nothing has ever been seen and this sweep was also empty --
        # leave `lanes` as-is (unknown), per the docstring above.

    def present(self, key: str) -> bool:
        """Whether lane `key` should be treated as present right now.

        Keys off `ever_seen`, NOT merely ``lanes is None``: nothing has been
        CONFIRMED yet whenever ``ever_seen`` is ``False``, regardless of
        whatever placeholder `lanes` happens to hold, so that state is
        UNKNOWN and must default to present -- the same "unknown counts as
        present" rule the ``None`` case exists for (see `observe`'s
        docstring, third bullet). Only once `ever_seen` is ``True`` -- a real
        sweep has actually seen this fleet non-empty at least once -- does an
        empty `lanes` mean the fleet is genuinely gone, and only then is a
        lane's absence from `lanes` allowed to mean "not present".

        Returns
        -------
        bool
            ``True`` when `ever_seen` is ``False`` (preserves the historical
            first-tick behaviour, so an unchecked lane is never wrongly
            reclassified as reclaimed), or when `lanes` is ``None`` or `key`
            is in `lanes`; ``False`` otherwise.
        """
        if not self.ever_seen:
            return True
        return self.lanes is None or key in self.lanes


@dataclass
class _LaneRun:
    """Mutable per-lane runtime state, carried across monitor-loop ticks."""

    lane: _lane_env.Lane
    #: Ordered subprocess phases this invocation runs for this lane, e.g.
    #: ``("induction",)``, ``("deduction",)``, or ``("induction", "deduction")``.
    phases: tuple[str, ...]
    phase_index: int = 0
    proc: Optional[subprocess.Popen] = None
    #: Timestamp of the most recent (re)launch; reset by every relaunch.
    started_at: float = 0.0
    #: Timestamp of this lane's FIRST launch ONLY -- never reset by a
    #: relaunch. `_monitor_tick`'s 2x-budget alert keys on THIS, not
    #: `started_at`: an alert keyed on a value every relaunch resets could
    #: never fire for the one lane it exists to catch -- one being relaunched
    #: over and over (see `_start_phase`).
    lane_started_at: float = 0.0
    #: Crash relaunches so far this invocation; bounded by
    #: `_policy.MAX_CRASH_RELAUNCHES`. Passed to `_policy.decide_relaunch` as
    #: its ``attempt``, so it is incremented BEFORE the decision is asked for.
    crash_relaunches: int = 0
    #: Reclaim relaunches so far this invocation; bounded by
    #: `_policy.MAX_RECLAIM_RELAUNCHES` (see that constant's comment in
    #: ``scripts/fleet/policy.py`` for why a reclaim is no longer unlimited).
    #: Incremented before the decision, like `crash_relaunches`.
    reclaim_relaunches: int = 0
    #: `time.monotonic()` deadline for a pending backed-off reclaim relaunch;
    #: ``None`` means nothing is pending. Set by `_apply_restart_policy` on a
    #: reclaim verdict, cleared when that relaunch fires.
    pending_relaunch_at: Optional[float] = None
    cot_checked: bool = False
    #: Latches True once `_lane_gate_passed` has found the healthy-serve line
    #: for this lane; makes every later gate check an O(1) no-I/O return.
    gate_passed: bool = False
    #: Byte offset `_lane_gate_passed` has already scanned up to, so each
    #: call reads only newly appended bytes. Reset to 0 if the log file is
    #: ever found shorter than this (truncated/replaced).
    gate_scan_offset: int = 0
    halted: bool = False
    halt_reason: str = ""
    done: bool = False
    #: Non-empty when this lane's post-deduction S3 spool failed; surfaced in
    #: `_run_fleet`'s closing report. A spool failure does NOT halt the lane
    #: (its data is already collected; this is a reporting matter -- see
    #: `_advance_finished`).
    spool_error: str = ""

    @property
    def current_phase(self) -> Optional[str]:
        """The phase this lane runs now, or None once `phases` is exhausted."""
        if self.phase_index >= len(self.phases):
            return None
        return self.phases[self.phase_index]


def _phase_sequence(phase: str) -> tuple[str, ...]:
    """Map a ``--phase`` CLI value onto the ordered subprocess phases each lane runs.

    A lane's instance shuts down (`_advance_finished`) only once its LAST
    scheduled phase exits successfully AND that phase was ``"deduction"``, so an
    induction-only invocation never shuts its boxes down.

    Returns
    -------
    tuple[str, ...]
        ``("induction",)``, ``("deduction",)`` or ``("induction", "deduction")``.

    Raises
    ------
    ValueError
        For any other `phase`.
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
    # Append mode lets the family gate scan a lane's WHOLE log -- across a
    # relaunch or a later phase -- for the one-time healthy-serve line; a
    # truncating mode would lose it the moment the lane's phase changed.
    with open(log_path, "a") as log_file:
        run.proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, env=env)
    run.started_at = time.monotonic()
    if not run.lane_started_at:
        # FIRST launch only -- see `_LaneRun.lane_started_at`'s docstring for
        # why the 2x-budget alert must key on this instead of `started_at`.
        run.lane_started_at = run.started_at


def _launch_batch(runs: dict, keys: Sequence[str], log_dir: Path) -> None:
    """Launch each lane in `keys` at its current phase, ``LAUNCH_STAGGER_SECONDS`` apart."""
    for i, key in enumerate(keys):
        if i:
            time.sleep(LAUNCH_STAGGER_SECONDS)
        _start_phase(runs[key], log_dir)


def _lane_gate_passed(run: _LaneRun, log_dir: Path) -> bool:
    """Check whether `run`'s log has ever produced a healthy-serve line.

    STICKY and INCREMENTAL -- deliberately NOT a plain `_tail_log` bounded
    read (finding 14-03): the healthy-serve line (`is_serve_healthy`) is a
    ONE-TIME event near the start of a lane's log, which scrolls out of any
    fixed byte window under gigabytes of later vLLM/CoT chatter, so a bounded
    tail would silently stop finding it. Instead:

    * once found, `run.gate_passed` latches ``True`` and every later call for
      this lane is an O(1) return with no file I/O at all;
    * until then, only the bytes APPENDED since `run.gate_scan_offset` are
      read and scanned, so total work across many calls is O(log size), not
      O(calls x log size);
    * the offset only ever advances over WHOLE lines: if the newly read
      chunk does not end in a newline (a write may be mid-flight), the scan
      trims back to the last complete newline and advances the offset only
      that far -- so a healthy-serve line split across two reads is not
      half-consumed on the first call and then missed (already past the
      offset) on the second;
    * if the log file is found SHORTER than `gate_scan_offset` (truncated or
      replaced under the same name), the offset resets to 0 and the scan
      restarts from the beginning, rather than seeking past EOF and reading
      nothing forever.
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
        offset = 0  # file shrank -- rescan from the start, see docstring

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

    Parameters
    ----------
    tick : int
        1-based. The ``describe_instances`` sweep (read-only
        ``fleet_status.fleet_rows``) runs on tick 1 -- so the table has instance
        data immediately -- and every ``DESCRIBE_EVERY_N_TICKS``-th tick after.
    presence : _Presence
        Mutated in place. A sweep that RAISES is logged and skipped, leaving
        `presence` untouched -- the previous "could not check" behaviour. A
        sweep that RETURNS, even with an empty result, calls
        ``presence.observe`` and lets that type's own rules (see its
        docstring) decide whether an empty result means unknown or genuinely
        gone -- these are different cases: a failed sweep tells you nothing,
        while an empty but successful one is real information.
    """
    if tick == 1 or tick % DESCRIBE_EVERY_N_TICKS == 0:
        try:
            rows = _fleet_status_module().fleet_rows()
        except Exception as exc:  # noqa: BLE001 -- one bad sweep must not crash the monitor
            logging.warning(f"run_fleet: describe_instances sweep failed this tick: {exc}")
        else:
            presence.observe({row["lane"] for row in rows})

    print(f"\n=== fleet tick {tick} ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    for key in sorted(runs):
        run = runs[key]
        alive = run.proc is not None and run.proc.poll() is None
        status = "halted" if run.halted else ("done" if run.done else (run.current_phase or "?"))
        last_line = _tail_log(log_dir, key, n=1)
        print(f"{key:<28} status={status:<10} alive={str(alive):<5} last: {last_line[-120:]}")

        if run.proc is not None and not alive and not run.halted and not run.done:
            rc = run.proc.returncode
            if rc not in (0, None):
                print(f"ALERT [{key}]: process exited non-zero (rc={rc}).")

        if presence.lanes is not None and alive and key not in presence.lanes:
            print(f"ALERT [{key}]: subprocess is still running but its instance is "
                  "gone or shutting down.")

        if run.lane_started_at:
            # `lane_started_at`, NOT `started_at`: see `_LaneRun.lane_started_at`'s
            # docstring for why this alert must key on the lane's CUMULATIVE
            # age across relaunches, not the most recent launch's timestamp.
            age_hours = (time.monotonic() - run.lane_started_at) / 3600
            budget = 2 * run.lane.budget_hours
            if age_hours > budget:
                print(f"ALERT [{key}]: wall clock {age_hours:.1f}h exceeds 2x budget "
                      f"({budget}h).")


def _apply_restart_policy(runs: dict[str, _LaneRun], log_dir: Path, presence: _Presence) -> None:
    """Relaunch or halt every lane whose subprocess exited non-zero this tick.

    Applies `_policy.classify_exit`'s verdict through `_policy.decide_relaunch`,
    the ONE place either supervisor's relaunch cap is enforced (``run_shards.py``
    asks the same function about a dead shard): a CRASH gets
    `_policy.MAX_CRASH_RELAUNCHES` immediate relaunches then a halt; a RECLAIM
    gets `_policy.MAX_RECLAIM_RELAUNCHES` BACKED-OFF relaunches, on
    `_policy.reclaim_backoff_seconds`' schedule, then a halt too. Reclaims are
    not unlimited: an empty or failed describe sweep used to make every exit
    look like a reclaim, so an unbounded retry policy on that misclassification
    meant a lane could relaunch forever with no crash counting and no budget
    alert ever firing.

    This function owns only the TICK-DRIVEN half of that: it never sleeps,
    because it supervises 21 lanes from a single loop and blocking in one
    lane's backoff would stall the other twenty. A non-zero
    ``decision.delay_seconds`` becomes a `pending_relaunch_at` deadline
    re-checked on later ticks; a zero delay relaunches in line.
    (``run_shards.py``, which watches one model's shards and has nothing else
    pending, sleeps the same delay instead. The scheduling differs; the policy
    does not.)

    A lane whose previous reclaim verdict is still waiting out its backoff
    (`pending_relaunch_at` in the future) is left alone this tick: neither
    relaunched early nor re-classified against a log tail that has not
    changed.

    Parameters
    ----------
    runs : dict of str to _LaneRun
        Lane key -> live lane state; mutated in place (counters, ``halted``,
        ``halt_reason``, ``pending_relaunch_at``, and `proc` via
        `_start_phase`).
    log_dir : Path
        Directory holding ``<lane key>.log``, read for the verdict and passed
        to `_start_phase` for a relaunch.
    presence : _Presence
        The last ``describe_instances`` sweep, consulted per lane for
        `_policy.classify_exit`'s ``instance_present``.

    Raises
    ------
    ValueError
        Propagated from `_policy.decide_relaunch` if the verdict is neither
        ``"reclaim"`` nor ``"crash"`` -- which would mean the classifier and
        this caller had drifted apart, and is not something to paper over.
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

        tail = _tail_log(log_dir, key)
        verdict = _policy.classify_exit(tail, presence.present(key))
        # The counter is incremented FIRST, then handed to the policy: its
        # `attempt` is defined as the post-increment count, so `attempt == 1`
        # is the first relaunch and the cap is exceeded at MAX + 1.
        if verdict == "reclaim":
            run.reclaim_relaunches += 1
            attempt = run.reclaim_relaunches
        else:
            run.crash_relaunches += 1
            attempt = run.crash_relaunches
        decision = _policy.decide_relaunch(verdict, attempt=attempt, rc=rc)

        if decision.action == "halt":
            run.halted = True
            run.halt_reason = decision.reason
            logging.error(f"run_fleet[{key}]: HALTED -- {run.halt_reason}")
            continue

        logging.warning(f"run_fleet[{key}]: {decision.reason}")
        if decision.delay_seconds:
            # Record a deadline rather than sleeping -- see this function's
            # docstring on why the 21-lane loop must not block.
            run.pending_relaunch_at = now + decision.delay_seconds
        else:
            _start_phase(run, log_dir)


def _check_cot(runs: dict[str, _LaneRun], store_factory: Callable[[], Any] = build_results_store) -> None:
    """Run the CoT-ON assertion once per lane; halt any lane below `COT_MIN_FRACTION`."""
    for key, run in runs.items():
        if run.cot_checked or run.halted or run.done or run.current_phase != "induction":
            continue
        try:
            store = store_factory()
            # intens ONLY: this is a WIRING check -- "did the thinking toggle
            # reach the model" -- and intens is the short, well-formed arm where
            # every wired model reasons. An all-arms pool would halt lanes that
            # collapse on the ~30k-token extens listing or confabulate on noise,
            # which is the phenomenon the study measures, not a fault.
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

        finished_phase = run.current_phase
        if finished_phase == "deduction":
            # `run_dir` is built from `lane_env.REPO_ROOT` EXPLICITLY, not from
            # the driver's own `runner.results_root()`: that helper reads
            # `SMOLBENCH_LEAN_RESULTS` from whatever process calls it -- here,
            # THIS supervisor, whose environment is not the lane's.
            # `SMOLBENCH_LEAN_RESULTS` is not in `lane_env.PASSTHROUGH_ENV`, so
            # the lane subprocess resolved the repo-root-anchored default;
            # anchoring here on `lane_env.REPO_ROOT` reproduces exactly that,
            # while `results_root()` would instead follow a stray
            # supervisor-side export to a directory no lane ever wrote to.
            run_dir = (
                _lane_env.REPO_ROOT / "notebooks" / "deduction" / "results" / "runs"
                / f"scaling_{run.lane.key}"
            )
            try:
                # WHY spool again here, given the driver already spools before
                # it can exit 0 (`lane_env.lane_command` passes no `--no-s3`):
                # its own prune leaves only `manifest.json`, so this is normally
                # a cheap re-upload of one file -- but it is the LAST thing
                # between "the lane process exited 0" and this supervisor
                # shutting that instance down under `--phase deduction`/`both`.
                # Going through the driver's OWN verified implementation
                # (upload, head_object ContentLength check, only then prune)
                # confirms the spool before destroying the box, rather than
                # trusting an already-exited process's own earlier attempt.
                #
                # `SystemExit` explicitly, alongside `Exception`: the
                # deduction driver's module-scope guard raises `SystemExit`
                # (not caught by a bare `except Exception`), and a failure
                # loading or running it here must not kill this supervisor.
                _deduction_driver().spool_to_s3(run_dir, run.lane.key)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 -- see docstring above
                run.spool_error = f"{type(exc).__name__}: {exc}"
                logging.error(f"run_fleet[{key}]: spool sync failed: {run.spool_error}")

        run.phase_index += 1
        if run.current_phase is not None:
            _start_phase(run, log_dir)
            continue

        # No more scheduled phases. Shut down only if a deduction phase ran THIS
        # invocation: an induction-only run leaves the instance up on purpose
        # (see `run_fleet.py`'s module docstring, "Phases" bullet) for a later
        # `--phase deduction` invocation.
        if "deduction" in run.phases:
            logging.info(f"run_fleet[{key}]: all phases complete; shutting down its instance.")
            cmd = _lane_env.lane_command(run.lane, "shutdown")
            env = _lane_env.lane_env(run.lane, "shutdown")
            subprocess.run(cmd, env=env, check=False)
        run.done = True


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
    """
    runs = {key: _LaneRun(lane=lane, phases=phase_sequence) for key, lane in lanes.items()}

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
        time.sleep(MONITOR_INTERVAL_SECONDS)
        _monitor_tick(runs, log_dir, tick, presence)
        _apply_restart_policy(runs, log_dir, presence)
        _check_cot(runs)
        _advance_finished(runs, log_dir)
        if all(runs[k].halted for k in gate_keys):
            logging.error(
                "run_fleet: FAMILY GATE FAILED -- every GATE_MODELS lane halted; NOT "
                "launching tiers B/C. Investigate FLEET_IMAGE before retrying."
            )
            # Finding 14-03: these tier B/C lanes were never launched (proc is
            # still None), so without marking them HALTED here they sit
            # forever with halted=False, done=False -- `_all_terminal` never
            # returns True, both policy loops `continue` on `proc is None`,
            # and the supervisor spins with the tier-D boxes still up,
            # printing ticks forever and never reaching the closing report or
            # the teardown reminder below. HALT, not `done`: these lanes
            # produced no data and the operator must see them in the closing
            # summary, not have them silently disappear from it.
            for bc_key in tier_bc:
                runs[bc_key].halted = True
                runs[bc_key].halt_reason = (
                    "never launched: family gate failed (every GATE_MODELS lane halted)"
                )
            gate_keys = []  # stop waiting; skip the else-clause launch below
            break
    else:
        logging.info("run_fleet: family gate passed (or was skipped) -- launching tiers B and C.")
        _launch_batch(runs, tier_bc, log_dir)

    while not _all_terminal(runs):
        tick += 1
        time.sleep(MONITOR_INTERVAL_SECONDS)
        _monitor_tick(runs, log_dir, tick, presence)
        _apply_restart_policy(runs, log_dir, presence)
        _check_cot(runs)
        _advance_finished(runs, log_dir)

    halted = {key: run.halt_reason for key, run in runs.items() if run.halted}
    if halted:
        logging.error(f"run_fleet: fleet finished with {len(halted)} halted lane(s): {halted}")
    # Printed unconditionally -- even when no lane halted -- because a spool
    # failure (finding 14-11) does not halt a lane; it is the only place this
    # would otherwise surface.
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
