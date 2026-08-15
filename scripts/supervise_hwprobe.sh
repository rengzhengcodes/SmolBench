#!/usr/bin/env bash
# Retry the g6e.4xlarge-vs-g6e.2xlarge equivalence probe until capacity appears.
#
# WHY
# ---
# Both probe invocations on 2026-08-14 died before sending a single prompt:
# g6e.4xlarge had no spot capacity in any of the 13 AZs across us-west-2,
# us-east-1 and us-east-2. That is a capacity block, not a design failure, so
# the answer is to keep asking rather than to redesign the test.
#
# The instance type is NOT widened on retry, and must never be. g6e.4xlarge is
# the A-side of the comparison -- the size the affected cells were originally
# generated on. Substituting another type to get a box would answer a question
# nobody asked.
#
# The two models run SEQUENTIALLY, not in parallel: they want the same scarce
# capacity, so racing them halves each one's chance of landing and doubles the
# peak spend. Each probe takes three boxes of its own anyway (A1/A2 on one
# 4xlarge, B1 on a 2xlarge).
#
# USAGE
#     scripts/supervise_hwprobe.sh [attempts] [sleep_seconds]
set -uo pipefail
cd /workspace/SmolBench

ATTEMPTS="${1:-72}"          # 72 x 600s = 12h of hunting
SLEEP_S="${2:-600}"
MODELS=(nemotron-3-nano-4b ministral-3-3b)

set -a
source notebooks/deduction/keys.env
source notebooks/ec2-operator.env
set +a
# keys.env exports EC2_EXPERIMENT_TAG; the probe sets its own per-model tag, but
# clear the inherited one so nothing can adopt a live study lane's box.
unset EC2_EXPERIMENT_TAG

for model in "${MODELS[@]}"; do
    log="notebooks/deduction/results/hwprobe_${model}.log"
    report="notebooks/deduction/results/hwprobe_${model}.json"
    if [ -f "$report" ]; then
        echo "$(date -u +%H:%M:%S) hwprobe[$model]: report already exists; skipping"
        continue
    fi
    for attempt in $(seq 1 "$ATTEMPTS"); do
        echo "$(date -u +%H:%M:%S) hwprobe[$model]: attempt $attempt/$ATTEMPTS"
        .venv/bin/python -u scripts/hardware_equivalence_probe.py --model "$model" \
            >> "$log" 2>&1
        rc=$?
        if [ "$rc" -eq 0 ]; then
            echo "$(date -u +%H:%M:%S) hwprobe[$model]: DONE -> $report"
            break
        fi
        # Only capacity is worth retrying. Anything else is a real failure and
        # silently re-running it 72 times would just bury the traceback.
        if ! tail -c 4000 "$log" | grep -q "No spot capacity"; then
            echo "$(date -u +%H:%M:%S) hwprobe[$model]: FAILED rc=$rc (not capacity) -- see $log"
            break
        fi
        echo "$(date -u +%H:%M:%S) hwprobe[$model]: no g6e.4xlarge capacity; retrying in ${SLEEP_S}s"
        sleep "$SLEEP_S"
    done
done
echo "$(date -u +%H:%M:%S) hwprobe supervisor: exiting"
