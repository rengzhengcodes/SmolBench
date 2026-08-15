#!/usr/bin/env bash
# Repair launcher for the deduction lanes that lost cells to infrastructure
# failure during the 2026-08-14 fleet run (user-directed re-run).
#
# WHAT WAS WRONG
# --------------
# 2,564 of the study's 19,824 cells (12.9%) carry candidate_proof: "",
# completion_tokens: 0 and a generation-time
#   RuntimeError: EC2 spot instance ... is shutting-down -- likely a spot
#   interruption (or the idle watchdog fired)
# The verifier faithfully copied them, so they surfaced only as an unusually
# high `exception` rate in verified_rows.jsonl. Loss per lane (cells with NO
# non-empty generation in ANY row):
#
#   nemotron-3-nano-4b   885/944  93.8%
#   gemma-4-31b          638/944  67.6%
#   ministral-3-3b       479/944  50.7%
#   deepseek-v3.1        415/944  44.0%
#   exaone-4.5-33b       141/944  14.9%
#   (qwen3.5-27b's 6 lost cells were already recovered by its own retry rows)
#
# A further 962 cells across the study are GENUINE empty output -- the model
# returned nothing with no error attached. Those carry verdict "unverified",
# are DATA not loss, and must not be regenerated.
#
# WHY THIS IS SAFE TO JUST RE-RUN
# -------------------------------
# Every lost cell carries verdict "exception", and runner._existing_keys()
# deliberately excludes exception rows from the skip set ("transient API
# errors ... should be retried on resume"). So a plain relaunch regenerates
# exactly the lost cells and nothing else -- no row surgery, no deletion, and
# genuine-empty cells stay untouched because "unverified" IS in the skip set.
#
# Resume needs the lane's all_rows.jsonl locally; the run dirs were pruned
# under the keep-run-data-in-S3 rule, so each lane's row file is restored from
# S3 first. Without that restore the driver would happily regenerate all 1,244
# rows at 4x the cost.
#
# Lanes run WITH the TCP-keepalive fix (27fd1c1a) and EC2_IDLE_TIMEOUT_MIN=90:
# "the idle watchdog fired" is the same failure family as the induction bug,
# and a 30-minute idle timeout is shorter than a legitimate long generation.
#
# RELAUNCH RULE: re-run this script with a lane key as $1 to relaunch just
# that lane (e.g. `bash scripts/relaunch_damaged_deduction.sh gemma-4-31b`).
# The (types, regions, state file) triple is derived here and only here, so a
# relaunch reattaches to the same box via the same state file and resumes from
# the same all_rows.jsonl -- never a second box for one lane.
set -euo pipefail
cd /workspace/SmolBench
set -a; source notebooks/ec2-operator.env; set +a
set -a; source notebooks/deduction/keys.env; set +a

BUCKET=smolbench-results-414266451290

# lane key | instance types | regions | REQUIRED GPU (silicon pin)
# Types match each rung's original EC2_DEPLOY_SPECS placement so the re-run
# lands on the SAME hardware class as the cells it is completing -- a
# different GPU would confound within-lane comparisons.
LANES=(
  # tp=1 lanes: every g6e size below carries exactly ONE L40S, so widening the
  # type list buys capacity without changing the accelerator (derive_tp reads
  # the landed box). ministral-3-3b exhausted g6e.4xlarge in all three regions
  # on the first attempt.
  "nemotron-3-nano-4b|g6e.4xlarge,g6e.2xlarge,g6e.8xlarge,g6e.16xlarge|us-east-2,us-west-2,us-east-1|L40S:1"
  "ministral-3-3b|g6e.4xlarge,g6e.2xlarge,g6e.8xlarge,g6e.16xlarge|us-east-2,us-west-2,us-east-1|L40S:1"
  "exaone-4.5-33b|g6e.12xlarge|us-east-2,us-west-2,us-east-1|L40S:4"
  "gemma-4-31b|g6e.12xlarge|us-east-2,us-west-2,us-east-1|L40S:4"
  "deepseek-v3.1|p5e.48xlarge|us-east-2,us-west-2|H200:8"
  # Only 6 cells, but a lane with ANY infra loss keeps the completeness audit
  # red, and a permanently-red gate is one nobody reads.
  "qwen3.5-27b|g6e.12xlarge|us-east-2,us-west-2,us-east-1|L40S:4"
)

launch_one() {
    local key="$1" types="$2" regions="$3" gpu="$4"
    local run_dir="notebooks/deduction/results/runs/scaling_${key}"
    mkdir -p "$run_dir"

    # Restore resume state. Without all_rows.jsonl the lane regenerates
    # everything; with it, only the exception rows are retried.
    if [[ ! -f "$run_dir/all_rows.jsonl" ]]; then
        aws s3 cp "s3://${BUCKET}/deduction/runs/scaling_${key}/all_rows.jsonl" \
                  "$run_dir/all_rows.jsonl" --quiet
    fi
    # Report DEAD CELLS, not exception rows. A key with both an exception row
    # and a later good row is already recovered and will be skipped on resume;
    # counting raw exception rows overstates the work (qwen3.5-27b: 231 rows,
    # 6 actually dead) and would misrepresent what this re-run is doing.
    local rows dead
    rows=$(wc -l < "$run_dir/all_rows.jsonl")
    dead=$(.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from audit_run_completeness import audit_lane
print(audit_lane(open('$run_dir/all_rows.jsonl').read())['infra'])
")
    echo "  ${key}: restored ${rows} rows, ${dead} dead cell(s) to regenerate"

    # EC2_EXPERIMENT_TAG MUST be set explicitly per lane. keys.env carries a
    # standalone-run default (EC2_EXPERIMENT_TAG=scaling-standalone) and
    # sourcing it above EXPORTS that value, after which the driver's
    # os.environ.setdefault correctly declines to override it -- so every lane
    # would share one tag. Boxes are discovered by tag when a state file is
    # absent (_recover_tagged_instance), so the second lane to start adopts the
    # first lane's box and serves ITS model on top: three lanes fought over one
    # g6e.12xlarge on the first attempt at this re-run (22:29Z 2026-08-14),
    # caught before any row was written.
    # EC2_MARKET is inherited (default "spot") so ONE lane can be bought
    # on-demand without touching the others. Used 2026-08-15 for
    # deepseek-v3.1: p5e.48xlarge spot was empty in every AZ all night, and
    # its 415 dead cells cannot be regenerated on other silicon without
    # contaminating the lane. Same instance type, same 8x H200, same tp --
    # only the till differs. The idle watchdog below is what keeps that
    # affordable: an abandoned on-demand p5e bills at full rate, where an
    # abandoned spot box is at least reclaimable.
    # Pin the SILICON, not the instance size: permits the harmless
    # g6e.4xlarge->g6e.2xlarge substitution (same single L40S, same tp; the
    # user accepted it 2026-08-14) while refusing a 4-GPU g6e.12xlarge, which
    # would change derived tp mid-lane. serve_model raises before the
    # container swap, so a mismatched box never writes a row.
    EC2_REQUIRE_GPU="$gpu" \
    EC2_EXPERIMENT_TAG="scaling-${key}" \
    LEAN_MODEL="$key" \
    LEAN_STATE_FILE=".ec2_state_scaling_${key}_repair.json" \
    EC2_INSTANCE_TYPES="$types" \
    EC2_REGIONS="$regions" \
    EC2_IDLE_TIMEOUT_MIN=90 \
    EC2_MAX_PARALLEL_REQUESTS=8 \
    EC2_MARKET="${EC2_MARKET:-spot}" \
    setsid nohup .venv/bin/python -u notebooks/deduction/run_study.py --teardown \
        >> "notebooks/deduction/results/repair_${key}.log" 2>&1 < /dev/null &
    echo "  ${key}: launched pid $!  (${types} @ ${regions}, pinned ${gpu})"
}

if [[ $# -ge 1 ]]; then
    for spec in "${LANES[@]}"; do
        IFS='|' read -r key types regions gpu <<< "$spec"
        [[ "$key" == "$1" ]] && launch_one "$key" "$types" "$regions" "$gpu" && exit 0
    done
    echo "unknown lane: $1" >&2; exit 1
fi

echo "relaunching ${#LANES[@]} damaged deduction lanes:"
for spec in "${LANES[@]}"; do
    IFS='|' read -r key types regions gpu <<< "$spec"
    launch_one "$key" "$types" "$regions" "$gpu"
    sleep 5   # stagger so five provision hunts do not race the same AZ
done
