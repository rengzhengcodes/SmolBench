#!/usr/bin/env bash
# Launcher for the ministral-3-14b DEDUCTION lane, sharded 3 ways by theorem
# stride (LEAN_SHARD=i/3) so the leg lands alongside the induction drain
# (2026-08-14; user-directed parallel launch). One g7.24xlarge (tp=4, same
# type/tp/image as the lane's induction fleet) per shard, us-west-2/us-east-1
# only -- us-east-2's G-spot quota is fully consumed by the induction fleet
# until ~15:30Z and hunting it invites the quota-race relaunch failure mode.
#
# RELAUNCH RULE: to relaunch a dead shard, re-run THIS script with the shard
# index as $1 (e.g. `bash scripts/launch_ministral14b_deduction_shards.sh 2`).
# The (LEAN_SHARD, run_name, state file) triple is derived here and only
# here, so a relaunch reattaches to the same box via the same state file and
# resumes via the shard's own all_rows.jsonl -- never a second box.
#
# Shards run --no-s3: their per-shard run_dirs are NON-canonical
# (scaling_ministral-3-14b_shard<i>of3) and must never be spooled to the
# canonical S3 prefix. scripts/merge_lean_shards.py merges them into
# runs/scaling_ministral-3-14b, asserts row uniqueness/totals, spools ONCE,
# then prunes the shard dirs.
set -euo pipefail
cd /workspace/SmolBench
set -a; source notebooks/ec2-operator.env; set +a

N=3
launch_one() {
    local i="$1"
    LEAN_MODEL=ministral-3-14b \
    LEAN_SHARD="${i}/${N}" \
    LEAN_STATE_FILE=".ec2_state_scaling_ministral-3-14b_ded${i}.json" \
    EC2_INSTANCE_TYPES=g7.24xlarge \
    EC2_REGIONS=us-west-2,us-east-1 \
    nohup .venv/bin/python -u notebooks/deduction/run_study.py --teardown --no-s3 \
        > "notebooks/deduction/results/ded14b_shard${i}.log" 2>&1 &
    echo "shard ${i}/${N} pid $!"
}

if [[ $# -ge 1 ]]; then
    launch_one "$1"
else
    for i in $(seq 0 $((N - 1))); do launch_one "$i"; done
fi
