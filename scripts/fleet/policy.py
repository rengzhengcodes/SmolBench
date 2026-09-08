"""Share restart classification and relaunch limits between fleet supervisors.

Keep imports and import-time work minimal because both supervisors load this
module by path before AWS setup.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Excludes routine provisioning logs so crashes do not receive reclaim retries.
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

    Treat an absent instance or a reclaim marker as reclaim; otherwise crash,
    avoiding abandoned interruptions or money-burning crash retries.

    Parameters
    ----------
    log_tail : str
        Recent child-process log output.
    instance_present : bool
        Whether the lane's EC2 instance remains present.

    Returns
    -------
    str
        ``"reclaim"`` or ``"crash"``.
    """
    if not instance_present:
        return "reclaim"
    if any(pattern.search(log_tail) for pattern in RECLAIM_PATTERNS):
        return "reclaim"
    return "crash"


MAX_CRASH_RELAUNCHES = 2
# Bound reclaim retries: failed instance sweeps otherwise hide crashes; 12
# relaunches span about 4.15h against 9--14h tier budgets.
MAX_RECLAIM_RELAUNCHES = 12
RECLAIM_BACKOFF_BASE_SECONDS = 60
RECLAIM_BACKOFF_CAP_SECONDS = 1800


def reclaim_backoff_seconds(attempt: int) -> float:
    """Return the delay to wait before reclaim relaunch number `attempt` (1-based).

    Use 60, 120, 240, 480, 960, then 1800 seconds for persistent capacity
    shortages; the schedule must never decrease for a persistently dry pool.

    Parameters
    ----------
    attempt : int
        1-based reclaim relaunch number.

    Returns
    -------
    float
        Relaunch delay in seconds.

    Raises
    ------
    ValueError
        ``attempt`` below 1, which would invert the schedule.
    """
    if attempt < 1:
        raise ValueError(f"attempt must be >= 1 (1-based), got {attempt}")
    return float(
        min(RECLAIM_BACKOFF_CAP_SECONDS,
            RECLAIM_BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
    )


@dataclass(frozen=True)
class Decision:
    """What a supervisor should do about one non-zero exit.

    Frozen so logged reasons cannot diverge from actions; halts name exceeded caps.
    ``action`` is ``"relaunch"`` or ``"halt"``; ``delay_seconds`` is ``0.0``
    for halts or immediate crashes, and ``reason`` has no supervisor prefix.
    """

    action: str
    delay_seconds: float
    reason: str


def decide_relaunch(verdict: str, *, attempt: int, rc: int | None) -> Decision:
    """Decide whether to relaunch after a `verdict` exit, and after how long.

    Crash relaunches are immediate because waiting cannot fix them; only capacity
    reclaims back off. This is the one cap enforcement point: both supervisors
    pass their counters here, so a raised cap applies to both and neither carries a laxer rule.

    Parameters
    ----------
    verdict : str
        ``"reclaim"`` or ``"crash"``.
    attempt : int
        Post-increment relaunch count for this verdict.
    rc : int | None
        Child exit status for the reason; never compared because callers supply either ``Popen.poll()`` or inferred 0/1 without a waitable handle.

    Returns
    -------
    Decision
        Relaunch or halt decision.

    Raises
    ------
    ValueError
        Raised, never asserted because ``python -O`` strips assertions; accepting another verdict would apply the wrong cap to a real failure.
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

    Increment before deciding so caps use the post-increment count.

    Parameters
    ----------
    counters : Any
        Object with crash and reclaim relaunch counters.
    log_tail : str
        Recent child-process log output.
    instance_present : bool
        Whether the lane's EC2 instance remains present.
    rc : int | None
        Child-process exit status.

    Returns
    -------
    Decision
        Relaunch or halt decision.
    """
    verdict = classify_exit(log_tail, instance_present)
    name = "reclaim_relaunches" if verdict == "reclaim" else "crash_relaunches"
    attempt = getattr(counters, name) + 1
    setattr(counters, name, attempt)
    return decide_relaunch(verdict, attempt=attempt, rc=rc)
