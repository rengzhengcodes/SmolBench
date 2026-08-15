#!/usr/bin/env bash
# ONE command to restart every outstanding run after a session exit.
#
# WHY THIS EXISTS
# ---------------
# Every driver in this study runs on the LOCAL host and is killed when the
# Claude session exits -- `setsid nohup` does not save it (the harness reaps
# the tree), and there is no systemd/at/cron on this box to hand work to.
# Harness cron is session-scoped too. So work PAUSES at session exit; nothing
# is lost, because resume is content-based on both legs:
#
#   induction  -- a seed's four arm files are written to S3 only when the seed
#                 COMPLETES, and has_outstanding() re-derives what is missing.
#   deduction  -- runner._existing_keys() skips cells that already have a
#                 non-exception row, so relaunching regenerates only the dead
#                 ones.
#
# Boxes outlive the drivers. If a box from the previous session is still up,
# provision_spot_instance() REATTACHES to it via the lane's state file (kept in
# the repo root) instead of launching a second one -- so resuming within the
# 90-minute idle-watchdog window skips a fresh model load. After that window
# the boxes reap themselves and this script simply provisions new ones.
#
# Idempotent: safe to run when some lanes are already going -- a lane whose
# driver is alive is skipped rather than duplicated. Duplicate drivers for one
# lane are the hazard this guards against, because two drivers sharing a state
# file will fight over one box.
set -uo pipefail
cd /workspace/SmolBench

INDUCTION_SEEDS="2,3,4,5,6,7,8"   # shard indices of seeds 19, 24-29 at --count 11
DAMAGED_LANES=(nemotron-3-nano-4b ministral-3-3b exaone-4.5-33b qwen3.5-27b gemma-4-31b deepseek-v3.1)

lane_alive() {  # $1 = LEAN_MODEL value; cmdlines are identical across lanes
    local p
    for p in $(pgrep -f "deduction/run_study.py" 2>/dev/null); do
        tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | grep -qx "LEAN_MODEL=$1" && return 0
    done
    return 1
}

echo "== induction: ministral-3-14b seeds 19,24-29"
if pgrep -f "run_shards.py --model ministral-3-14b" >/dev/null; then
    echo "   already running; left alone"
else
    set -a; source notebooks/induction/keys.env; source notebooks/ec2-operator.env; set +a
    # g7.24xlarge = 4x RTX PRO 4500; pin it so a widened hunt cannot
    # quietly move these seeds onto different silicon.
    #
    # --request-timeout 5400. Do NOT lower this. It was cut to 2100 (35 min) at
    # 02:35Z on 2026-08-15, reasoning from a MEAN e2e latency of 17-26 min --
    # and that mean is the wrong statistic. Measured per-stream throughput is
    # 46.1 tok/s, so a generation that runs to the 88,396-token budget cap takes
    # 32.0 MINUTES, and cap-hitting requests are the MAJORITY of this workload
    # (finished_reason=length was 114 of 173 completions). A 35-minute timeout
    # left three minutes of margin on the modal case; 28 requests timed out in
    # one wave at exactly relaunch+35min. Size this against the CAP, never the
    # mean: 88396 / 46 tok/s + contention headroom.
    EC2_REQUIRE_GPU="RTX PRO 4500:4" \
    EC2_MAX_PARALLEL_REQUESTS=4 EC2_IDLE_TIMEOUT_MIN=90 \
    setsid nohup .venv/bin/python -u scripts/run_shards.py \
        --model ministral-3-14b --count 11 --only-shards "$INDUCTION_SEEDS" \
        --types g7.24xlarge --regions us-east-2,us-west-2,us-east-1 \
        --request-timeout 5400 \
        >> notebooks/induction/results/fleet_logs/shards_ministral_repair.log 2>&1 < /dev/null &
    echo "   relaunched (pid $!)"
fi

echo "== deduction: damaged lanes"
for key in "${DAMAGED_LANES[@]}"; do
    if lane_alive "$key"; then
        echo "   $key: already running; left alone"
        continue
    fi
    # Supervised, because the two big-box lanes are capacity-starved and a
    # bare launch just dies in ~2 minutes with nothing watching.
    setsid nohup bash scripts/supervise_deduction_lane.sh "$key" 40 300 \
        >> "notebooks/deduction/results/supervise_${key}.log" 2>&1 < /dev/null &
    echo "   $key: supervisor relaunched (pid $!)"
    sleep 3
done

echo
echo "== verify what came up (give it ~2 min), then gate on content:"
echo "   .venv/bin/python scripts/audit_run_completeness.py --induction   # must exit 0"
