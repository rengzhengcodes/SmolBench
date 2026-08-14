#!/usr/bin/env bash
# Launcher for the gemma-4-12b DEDUCTION lane, resharded MID-FLIGHT 4 ways
# (2026-08-14, user-directed: complete by noon ET). The original unsharded
# driver was SIGKILLed at ~cell 510 and its outputs pre-split into the four
# shard run dirs via scripts/split_lean_run_into_shards.py; each shard's
# resume skips the pre-seeded cells. Shard 0 REATTACHES to the original live
# g7.12xlarge via the original state file (relaunch within 30 min of the
# kill or the idle watchdog reaps it); shards 1-3 provision fresh
# g7.12xlarge boxes, us-west-2 only (same type+region as the original box ->
# whole-lane hardware homogeneity; E2 quota-full, E1 pricier).
#
# RELAUNCH RULE: to relaunch a dead shard, re-run THIS script with the shard
# index as $1. The (LEAN_SHARD, run_name, state file) triple is derived here
# and only here, so a relaunch reattaches via the same state file and
# resumes from the shard's own all_rows.jsonl -- never a second box.
#
# Shards run --no-s3 (shard dirs are non-canonical). After all 4 print
# DEDUCTION LANE COMPLETE:
#   .venv/bin/python scripts/merge_lean_shards.py gemma-4-12b --n 4
#   cp .../runs/scaling_gemma-4-12b_shard0of4/manifest_prelude.json \
#      .../runs/scaling_gemma-4-12b/          # unsharded-phase provenance
#   then re-run the merge's spool step (or merge with --spool after the cp
#   by re-invoking; see merge_lean_shards.py) and only then delete
#   runs/scaling_gemma-4-12b_presplit (the pre-split backup).
set -euo pipefail
cd /workspace/SmolBench
set -a; source notebooks/ec2-operator.env; set +a

N=4
launch_one() {
    local i="$1"
    local state=".ec2_state_scaling_gemma-4-12b_ded${i}.json"
    if [[ "$i" == 0 ]]; then
        state=".ec2_state_scaling_gemma-4-12b.json"   # the original live box
    fi
    LEAN_MODEL=gemma-4-12b \
    LEAN_SHARD="${i}/${N}" \
    LEAN_STATE_FILE="$state" \
    EC2_INSTANCE_TYPES=g7.12xlarge \
    EC2_REGIONS=us-west-2 \
    nohup .venv/bin/python -u notebooks/deduction/run_study.py --teardown --no-s3 \
        > "notebooks/deduction/results/gemma12b_ded_shard${i}.log" 2>&1 &
    echo "shard ${i}/${N} pid $!"
}

if [[ $# -ge 1 ]]; then
    launch_one "$1"
else
    for i in $(seq 0 $((N - 1))); do launch_one "$i"; done
fi
