"""The ONE restart vocabulary both fleet supervisors read.

``scripts/fleet/run_fleet.py`` (21 one-model-per-box lanes) and
``scripts/fleet/run_shards.py`` (one shard group of a direct
``notebooks/induction/run_study.py`` run) both watch a child process die and
have to answer the same question: was that a spot reclaim, which will very
likely succeed on a later attempt, or a real crash, which will not? They used
to answer it with two unrelated vocabularies -- ``run_fleet`` with the eight
`RECLAIM_PATTERNS` below, a cap of `MAX_RECLAIM_RELAUNCHES` and exponential
backoff; ``run_shards`` with a single ``"No spot capacity for any"`` substring,
a consecutive-fast-crash counter and an UNBOUNDED flat 300s retry. The same
reclaim therefore got two different answers depending on which supervisor
happened to be watching. Everything either of them needs to answer it now
lives here, once.

The two supervisors still SPEND the answer differently, and that difference is
deliberate rather than an inconsistency:

- ``run_fleet`` is TICK-driven. It supervises 21 lanes from one loop, so it
  must never block in one lane's backoff; it records
  ``_LaneRun.pending_relaunch_at = now + decision.delay_seconds`` and
  re-checks that deadline on later ticks.
- ``run_shards`` is SLEEP-driven. It supervises a handful of shards of a
  single model and has no other work pending, so it simply sleeps
  ``decision.delay_seconds`` in line before relaunching.

Both get the delay, the cap and the verdict from the same functions, so the
scheduling difference cannot become a POLICY difference.

Notes
-----
This module imports nothing but ``re`` and ``dataclasses`` -- no ``_config``,
no ``boto3``, no ``smolbench`` package -- and does no work at import beyond
compiling `RECLAIM_PATTERNS`. That is a requirement, not an accident: it is
loaded by file path from both supervisors (and, in ``run_fleet``'s case, at
module scope, before anything else is set up), so it must be free of side
effects and of any import that could fail, read the environment or need AWS
credentials.

It is loaded BY FILE PATH, never a bare ``import policy``: ``scripts/fleet``
has no ``__init__.py`` -- it is not a package -- so a bare import name is
absent from ``sys.path`` for a script launched from an arbitrary working
directory. See ``_config.load_fleet_module``, the one loader both consumers
call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Verdict: reclaim or crash
# ---------------------------------------------------------------------------
# Deliberately EXCLUDES the bare provisioning line (`provision_spot_instance:
# trying <type> in <az> ...`, logged by `ec2._launch_fresh` on EVERY attempt):
# it appears in successful launches too, so matching it would misclassify a
# provisioning-time CRASH -- which also logs "trying ..." before failing -- as a
# reclaim, and a reclaim gets far more relaunches than a crash. Only failure
# wording counts: capacity/quota errors, and the "endpoint unreachable" message
# ec2.py raises after its connection-failure cap trips (the spot-reclaim/IP-drift
# symptom).
#
# The `spot capacity` pattern is also what covers `providers/ec2.py`'s
# "No spot capacity for any (instance type, region) combination:" -- the line
# `run_shards.py` used to match with a private `CAPACITY_MARKER` substring of
# its own.
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

    Parameters
    ----------
    log_tail : str
        The lane's last ~40 log lines at the moment the exit was observed.
    instance_present : bool
        Whether its ``scaling-<key>`` instance was in the last sweep.

    Returns
    -------
    str
        ``"reclaim"`` when the instance is absent or `log_tail` matches
        `RECLAIM_PATTERNS`; ``"crash"`` otherwise, INCLUDING an empty tail with
        the instance still present.

    Notes
    -----
    A backwards verdict either abandons a lane on a routine interruption or
    burns money relaunching one that will always fail the same way.
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
# A RECLAIM verdict used to get unlimited relaunches, on the theory that a spot
# reclaim is never the lane's fault. But an empty or failed
# `describe_instances` sweep (see `supervisor._Presence`) made EVERY exit look
# like a reclaim, so "unlimited" meant a lane could relaunch forever with no
# crash counting and no budget alert ever firing (`supervisor._monitor_tick`'s
# 2x-budget check keys on `lane_started_at`, which a relaunch never resets, but
# nothing stopped the relaunches themselves). Bounding it, with backoff so a
# lane genuinely fighting spot capacity is not hammered every tick:
#   delay before relaunch n = min(RECLAIM_BACKOFF_CAP_SECONDS,
#                                  RECLAIM_BACKOFF_BASE_SECONDS * 2 ** (n - 1))
#   = 60, 120, 240, 480, 960, then 1800s thereafter.
# MAX_RECLAIM_RELAUNCHES=12 relaunches therefore span about 4h of backoff
# (60+120+240+480+960+1800*7 ~= 4.15h) against a 9-14h tier budget
# (`lane_env.TIER_BUDGET_HOURS`), so a lane fighting genuine capacity pressure
# still gets most of its budget, while the pathological misclassification above
# stops at 12 relaunches instead of running for the fleet's whole lifetime.
# `run_shards.py` now reads this same schedule for its own capacity-shaped
# retries, so a shard hunting a dry pool is bounded exactly like a lane is.
MAX_RECLAIM_RELAUNCHES = 12
RECLAIM_BACKOFF_BASE_SECONDS = 60
RECLAIM_BACKOFF_CAP_SECONDS = 1800


def reclaim_backoff_seconds(attempt: int) -> float:
    """Return the delay to wait before reclaim relaunch number `attempt`.

    Parameters
    ----------
    attempt : int
        1-BASED relaunch number: ``1`` is the delay before the first relaunch
        after a reclaim verdict, ``2`` before the second, and so on. Must be
        ``>= 1``.

    Returns
    -------
    float
        ``min(RECLAIM_BACKOFF_CAP_SECONDS, RECLAIM_BACKOFF_BASE_SECONDS * 2 **
        (attempt - 1))`` -- that is 60, 120, 240, 480, 960, then 1800 for every
        attempt from the sixth on. The sequence is monotonically
        non-decreasing: it NEVER shrinks, so a lane fighting a persistently dry
        capacity pool always waits at least as long as it did last time.

    Raises
    ------
    ValueError
        If `attempt` is less than 1. A 0-based or negative `attempt` would
        silently produce a SHORTER delay than the base (``2 ** -1`` is 0.5),
        inverting the whole point of the schedule, so it is refused rather
        than accepted.

    Examples
    --------
    >>> [reclaim_backoff_seconds(n) for n in (1, 2, 5, 6, 99)]
    [60.0, 120.0, 960.0, 1800.0, 1800.0]
    """
    if attempt < 1:
        raise ValueError(f"attempt must be >= 1 (1-based), got {attempt}")
    # Capped BEFORE the exponent can grow large: `2 ** (attempt - 1)` is an
    # exact Python int at any attempt, so there is no overflow to guard, but
    # `min` keeps the result inside the documented ceiling regardless.
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

    Frozen because both supervisors hold a decision across a few statements
    (log it, then either record a deadline or sleep and relaunch); an
    accidental mutation between those steps would mean the action taken and
    the reason logged no longer describe each other.

    Attributes
    ----------
    action : str
        ``"relaunch"`` or ``"halt"``.
    delay_seconds : float
        How long to wait before relaunching. Always ``0.0`` when `action` is
        ``"halt"`` (nothing is going to be relaunched), and ``0.0`` for a crash
        relaunch, which is immediate.
    reason : str
        The operator-facing sentence to log, WITHOUT any supervisor-specific
        prefix -- ``run_fleet`` prepends ``"run_fleet[<lane>]: "`` and
        ``run_shards`` prepends ``"shard <i>: "``. On a halt it names the
        constant that was exceeded, so a log line is self-explaining without
        the reader having to know the cap by heart.
    """

    action: str
    delay_seconds: float
    reason: str


def decide_relaunch(verdict: str, *, attempt: int, rc) -> Decision:
    """Decide whether to relaunch after a `verdict` exit, and after how long.

    This is the ONE place either supervisor's relaunch cap is enforced. Both
    call it with their own per-lane / per-shard counter, so a cap raised here
    is raised for both and neither can quietly carry a second, laxer rule.

    Parameters
    ----------
    verdict : str
        `classify_exit`'s answer: ``"reclaim"`` or ``"crash"``.
    attempt : int
        The POST-increment count of relaunches of THIS verdict's kind for this
        lane/shard: the caller increments its own counter first, then asks. So
        ``attempt == 1`` on the first reclaim, and the cap is exceeded when
        `attempt` is strictly greater than the relevant maximum -- which is
        what makes ``MAX_RECLAIM_RELAUNCHES`` relaunches actually happen before
        the halt.
    rc : object
        The child's exit status, interpolated into `Decision.reason` for the
        operator. Deliberately untyped and never compared against: callers
        differ in what they can supply (``subprocess.Popen.poll()`` for a live
        handle, an INFERRED 0/1 for an adopted process with no waitable
        handle), and this function only reports it.

    Returns
    -------
    Decision
        ``action="relaunch"`` with `delay_seconds` from
        `reclaim_backoff_seconds` for a reclaim inside its cap, ``0.0`` for a
        crash inside its cap, or ``action="halt"`` once the cap is exceeded.

    Raises
    ------
    ValueError
        If `verdict` is neither ``"reclaim"`` nor ``"crash"``. Raised, never
        asserted: an ``assert`` is stripped entirely under ``python -O``, and
        an unrecognised verdict silently treated as one of the two would apply
        the wrong cap to a real failure.

    Notes
    -----
    A crash relaunches IMMEDIATELY (``delay_seconds == 0.0``) rather than
    backing off. That is deliberate, and is the behaviour both supervisors
    already had: a crash is not a capacity shortage, so waiting buys nothing
    -- the same code will fail the same way in 60s -- and the tight
    `MAX_CRASH_RELAUNCHES` cap is what bounds the loop instead. Backoff exists
    only for the reclaim path, where the thing being waited on (spot capacity,
    a quota window) really does free up on its own.

    Examples
    --------
    >>> decide_relaunch("crash", attempt=1, rc=1).action
    'relaunch'
    >>> decide_relaunch("reclaim", attempt=1, rc=1).delay_seconds
    60.0
    >>> decide_relaunch("crash", attempt=MAX_CRASH_RELAUNCHES + 1, rc=1).action
    'halt'
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
