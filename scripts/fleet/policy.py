"""The ONE restart vocabulary both fleet supervisors read.

``run_fleet.py`` (21 one-model-per-box lanes) and ``run_shards.py`` (one
shard group of a direct ``run_study.py`` run) both watch a child process die
and must answer the same question: spot reclaim (likely to succeed later) or
real crash (won't)? That answer, and the cap/backoff on acting on it, lives
here once, so the two supervisors can differ in HOW they spend the answer
without risking a POLICY difference: ``run_fleet`` is tick-driven (21 lanes
in one loop, so it records a `pending_relaunch_at` deadline rather than
blocking) and ``run_shards`` is sleep-driven (nothing else to do, so it
sleeps `decision.delay_seconds` in line).

This module imports only ``re``/``dataclasses`` -- no ``_config``, boto3 or
``smolbench`` -- and does no import-time work beyond compiling
`RECLAIM_PATTERNS`. Required, not incidental: it is loaded by file path from
both supervisors, at module scope in ``run_fleet``'s case before anything
else is set up, so it must stay free of anything that could fail, read the
environment, or need AWS credentials.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Verdict: reclaim or crash
# ---------------------------------------------------------------------------
# Excludes the bare provisioning line (`ec2._launch_fresh`'s "trying <type>
# in <az> ..."): it logs on every attempt, including successful ones, so
# matching it would misclassify a provisioning-time crash as a reclaim --
# and a reclaim gets far more relaunches than a crash. Only failure wording
# counts: capacity/quota errors, and the "endpoint unreachable" message
# ec2.py raises after its connection-failure cap trips (the reclaim/IP-drift
# symptom).
RECLAIM_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"InsufficientInstanceCapacity",
        r"spot quota exhausted",
        r"MaxSpotInstanceCountExceeded",
        r"SpotMaxPriceTooLow",
        r"spot capacity",
        r"capacity-not-available",
        r"spot interruption",
        r"endpoint unreachable",
    )
)


def classify_exit(log_tail: str, instance_present: bool) -> str:
    """Classify a lane's non-zero exit as a spot reclaim or a real crash.

    ``"reclaim"`` when `instance_present` is false or `log_tail` matches
    `RECLAIM_PATTERNS`; ``"crash"`` otherwise, including an empty tail with
    the instance still present. A backwards verdict either abandons a lane on
    a routine interruption or burns money relaunching one that will always
    fail the same way.

    Parameters
    ----------
    log_tail : str
        Recent child-process log output.
    instance_present : bool
        Whether the lane's EC2 instance remains present.

    Returns
    -------
    str
        The ``"reclaim"`` or ``"crash"`` verdict.
    """
    if not instance_present:
        return "reclaim"
    if any(pattern.search(log_tail) for pattern in RECLAIM_PATTERNS):
        return "reclaim"
    return "crash"


# ---------------------------------------------------------------------------
# Caps and backoff schedule
# ---------------------------------------------------------------------------
MAX_CRASH_RELAUNCHES = 2
# Bounded, not unlimited: a failed `describe_instances` sweep (see
# `supervisor._Presence`) makes every exit look like a reclaim, so an
# unbounded budget would let a lane relaunch for the fleet's whole lifetime
# with no crash counting. 12 relaunches span ~4.15h of backoff against a
# 9-14h tier budget (`lane_env.TIER_BUDGET_HOURS`).
MAX_RECLAIM_RELAUNCHES = 12
RECLAIM_BACKOFF_BASE_SECONDS = 60
RECLAIM_BACKOFF_CAP_SECONDS = 1800


def reclaim_backoff_seconds(attempt: int) -> float:
    """Return the delay to wait before reclaim relaunch number `attempt` (1-based).

    ``min(RECLAIM_BACKOFF_CAP_SECONDS, RECLAIM_BACKOFF_BASE_SECONDS * 2 **
    (attempt - 1))``: 60, 120, 240, 480, 960, then 1800 from the sixth attempt
    on. Monotonically non-decreasing, so a lane fighting a persistently dry
    capacity pool never waits less than it did last time.

    Parameters
    ----------
    attempt : int
        1-based reclaim relaunch number.

    Returns
    -------
    float
        Delay in seconds before the relaunch.

    Raises
    ------
    ValueError
        below 1: a 0-based or negative `attempt` would give a shorter delay than
        the base (``2 ** -1`` is 0.5), inverting the schedule.
    """
    if attempt < 1:
        raise ValueError(f"attempt must be >= 1 (1-based), got {attempt}")
    return float(
        min(RECLAIM_BACKOFF_CAP_SECONDS,
            RECLAIM_BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
    )


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Decision:
    """What a supervisor should do about one non-zero exit.

    Frozen: both supervisors hold a decision across a few statements (log it,
    then record a deadline or sleep and relaunch), and an accidental mutation
    between those steps would make the action taken and the reason logged
    stop describing each other.

    `action` is ``"relaunch"`` or ``"halt"``. `delay_seconds` is ``0.0`` for
    a halt or an immediate crash relaunch. `reason` is the operator-facing
    sentence to log, with no supervisor-specific prefix (``run_fleet``
    prepends ``"run_fleet[<lane>]: "``, ``run_shards`` prepends ``"shard
    <i>: "``); on a halt it names the exceeded constant, so the log line is
    self-explaining without the reader knowing the cap by heart.
    """

    action: str
    delay_seconds: float
    reason: str


def decide_relaunch(verdict: str, *, attempt: int, rc: int | None) -> Decision:
    """Decide whether to relaunch after a `verdict` exit, and after how long.

    The ONE place either supervisor's relaunch cap is enforced: both call it
    with their own per-lane/per-shard counter, so a cap raised here applies
    to both, and neither can quietly carry a second, laxer rule.

    A crash relaunches immediately (``delay_seconds == 0.0``) rather than
    backing off: it isn't a capacity shortage, so waiting buys nothing, and
    the tight `MAX_CRASH_RELAUNCHES` cap bounds the loop instead. Backoff
    exists only for the reclaim path, where the thing being waited on (spot
    capacity, a quota window) actually frees up on its own.

    Raises `ValueError`, never an assert (stripped under ``python -O``), for
    a `verdict` outside ``"reclaim"``/``"crash"``: silently treating an
    unrecognised verdict as one of the two would apply the wrong cap to a
    real failure.

    Parameters
    ----------
    attempt : int
        the POST-increment count of relaunches of this verdict's kind
        for this lane/shard (the caller bumps its counter first, then asks), so
        the cap is exceeded once `attempt` exceeds the relevant maximum.
    rc : int | None
        the child's exit status, interpolated into `Decision.reason` for the
        operator. never compared against: callers differ in what they can
        supply (`subprocess.Popen.poll()`, or an inferred 0/1 for an adopted
        process with no waitable handle).
    """
    if verdict == "reclaim":
        if attempt > MAX_RECLAIM_RELAUNCHES:
            return Decision(
                action="halt",
                delay_seconds=0.0,
                reason=(
                    f"reclaimed {attempt} time(s) (last rc={rc}); exceeded "
                    f"MAX_RECLAIM_RELAUNCHES={MAX_RECLAIM_RELAUNCHES}"
                ),
            )
        delay = reclaim_backoff_seconds(attempt)
        return Decision(
            action="relaunch",
            delay_seconds=delay,
            reason=(
                f"exited rc={rc}, classified RECLAIM -- relaunch "
                f"{attempt}/{MAX_RECLAIM_RELAUNCHES} in {delay:.0f}s."
            ),
        )
    if verdict == "crash":
        if attempt > MAX_CRASH_RELAUNCHES:
            return Decision(
                action="halt",
                delay_seconds=0.0,
                reason=(
                    f"crashed {attempt} time(s) (last rc={rc}); exceeded "
                    f"MAX_CRASH_RELAUNCHES={MAX_CRASH_RELAUNCHES}"
                ),
            )
        return Decision(
            action="relaunch",
            delay_seconds=0.0,
            reason=(
                f"exited rc={rc}, classified CRASH -- relaunch "
                f"{attempt}/{MAX_CRASH_RELAUNCHES}."
            ),
        )
    raise ValueError(
        f"unknown verdict {verdict!r}: classify_exit returns only "
        "'reclaim' or 'crash'"
    )


def count_and_decide(
    counters: Any, log_tail: str, instance_present: bool, rc: int | None
) -> Decision:
    """Classify a dead child's exit, bump the matching counter, and decide.

    The sequence both supervisors share; only the scheduling of
    `Decision.delay_seconds` differs between them. `counters` is any object
    with `crash_relaunches`/`reclaim_relaunches` attributes (a
    `supervisor._LaneRun` or a `shards.Shard`); incremented first, since
    `decide_relaunch`'s `attempt` is the post-increment count.

    Parameters
    ----------
    counters : Any
        Object holding crash and reclaim relaunch counters.
    log_tail : str
        Recent child-process log output.
    instance_present : bool
        Whether the lane's EC2 instance remains present.
    rc : int | None
        Child-process exit status.

    Returns
    -------
    Decision
        Relaunch or halt decision for the exit.
    """
    verdict = classify_exit(log_tail, instance_present)
    name = "reclaim_relaunches" if verdict == "reclaim" else "crash_relaunches"
    attempt = getattr(counters, name) + 1
    setattr(counters, name, attempt)
    return decide_relaunch(verdict, attempt=attempt, rc=rc)
