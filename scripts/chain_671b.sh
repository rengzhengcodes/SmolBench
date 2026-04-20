#!/bin/bash
# Waits for the DS-Prover-7B re-run to finish, then launches run_671b.sh.
# Meta-wrapper so I can `nohup` one process and the remaining pipeline runs
# itself.
set -u
LOG=/opt/dlami/nvme/sb/chain_671b.log
echo "=== chain started at $(date -u) ===" | tee -a "$LOG"

# Only poll if the DS-Prover 7B script is actually running; otherwise fall
# straight through.
if pgrep -f "run_dsprover7b.sh" > /dev/null; then
    echo "waiting on run_dsprover7b.sh ..." | tee -a "$LOG"
    while pgrep -f "run_dsprover7b.sh" > /dev/null; do sleep 120; done
fi

echo "=== dsprover7b no longer running; starting 671B at $(date -u) ===" | tee -a "$LOG"
bash ~/SmolBench/scripts/run_671b.sh
echo "=== chain done at $(date -u) ===" | tee -a "$LOG"
