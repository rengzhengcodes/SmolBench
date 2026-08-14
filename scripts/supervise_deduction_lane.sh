#!/usr/bin/env bash
# Retry babysitter for ONE deduction repair lane whose instance type is
# capacity-starved.
#
# WHY: a capacity-exhausted hunt exits in ~2 minutes, and the driver stays
# dead. Two lanes of the 2026-08-14 repair could not place:
#   * gemma-4-31b  -- g6e.12xlarge; us-east-2's g-family Spot quota (768 vCPU)
#     is fully consumed by our OWN 7 induction shards (672) plus two g6e.12xl
#     lanes (96), so it frees only as the induction fleet drains.
#   * deepseek-v3.1 -- p5e.48xlarge exists in just 4 AZs (us-east-2 a/b/c,
#     us-west-2c) and all were dry.
#
# Substituting a different GPU would confound the lane it is repairing: these
# runs complete cells generated on the original accelerator. So we wait for
# the right hardware rather than take what is available.
#
# Retries until the lane reports completion, with a hard attempt cap so a
# permanently-unavailable type cannot spin forever unnoticed.
set -uo pipefail
cd /workspace/SmolBench

KEY="${1:?usage: supervise_deduction_lane.sh <lane-key> [max_attempts] [sleep_s]}"
MAX_ATTEMPTS="${2:-40}"
SLEEP_S="${3:-300}"
LOG="notebooks/deduction/results/repair_${KEY}.log"

# The launcher backgrounds the driver under `setsid`, so it is a detached
# grandchild -- `wait` cannot see it and `$!` would name the launcher, which
# exits immediately. Identify the live run by reading LEAN_MODEL out of each
# candidate process's environment: matching on the cmdline is useless here
# because every lane runs the byte-identical command
# `.venv/bin/python -u notebooks/deduction/run_study.py --teardown`.
lane_pid() {
    local p
    for p in $(pgrep -f "deduction/run_study.py" 2>/dev/null); do
        if tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | grep -qx "LEAN_MODEL=$KEY"; then
            echo "$p"; return 0
        fi
    done
    return 1
}

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "$(date -u +%H:%M:%S) supervise[$KEY]: attempt ${attempt}/${MAX_ATTEMPTS}" >> "$LOG"
    bash scripts/relaunch_damaged_deduction.sh "$KEY" >> "$LOG" 2>&1
    sleep 20                       # let the driver start and claim its env
    while lane_pid >/dev/null; do  # block for the lifetime of the real run
        sleep 60
    done
    # The driver prints this line only after runner.sweep returns and the run
    # is spooled; anything else means it died (capacity, crash, reclaim).
    if tail -40 "$LOG" | grep -q "DEDUCTION LANE COMPLETE"; then
        echo "$(date -u +%H:%M:%S) supervise[$KEY]: COMPLETE" >> "$LOG"
        exit 0
    fi
    if tail -5 "$LOG" | grep -qi "Widen EC2_INSTANCE_TYPES"; then
        echo "$(date -u +%H:%M:%S) supervise[$KEY]: no capacity; retrying in ${SLEEP_S}s" >> "$LOG"
    else
        echo "$(date -u +%H:%M:%S) supervise[$KEY]: died (see log); retrying in ${SLEEP_S}s" >> "$LOG"
    fi
    sleep "$SLEEP_S"
done
echo "$(date -u +%H:%M:%S) supervise[$KEY]: GAVE UP after ${MAX_ATTEMPTS} attempts" >> "$LOG"
exit 1
