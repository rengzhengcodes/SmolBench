#!/usr/bin/env bash
# Start a packed_box.py run on the box, detached, with this study's paths.
#
#   bash scripts/deduction/packed_box_run.sh calib   # 10 cells x 3 rungs, one model per size group
#   bash scripts/deduction/packed_box_run.sh full    # set A, the whole roster
#
# Calibration and the full run write to different S3 prefixes and results
# directories, so neither can resume from or overwrite the other.
set -euo pipefail
MODE=${1:?usage: packed_box_run.sh calib|full}
W=${W:-/opt/dlami/nvme/sb}
REPO=$W/repo
PREFIX_ROOT=deduction_postcutoff/b200_2026-09-24
export PATH=$REPO/.venv/bin:$HOME/.elan/bin:$HOME/.local/bin:$PATH
# Reuse the built REPL: lean-interact's default setup serializes parallel Lean sessions.
export SMOLBENCH_REPL_LOCAL_PATH=/opt/dlami/nvme/sb/repo/.venv/lib/python3.12/site-packages/lean_interact/cache/leanprover-community/repl/repl_v4.34.0-rc2_lean-toolchain-v4.34.0-rc2

case "$MODE" in
    calib)
        PREFIX=$PREFIX_ROOT/calib
        SWEEP=$REPO/notebooks/deduction/sweep_b200_calib.yaml
        WORK=$W/calib
        MODELS="--models deepseek-v4-flash,qwen3.5-122b-a10b,qwen3.5-27b,nemotron-3-nano-30b-a3b,gemma-4-e2b,ministral-3-8b"
        ;;
    full)
        PREFIX=$PREFIX_ROOT/setA_v2
        SWEEP=$REPO/notebooks/deduction/sweep_b200.yaml
        WORK=$W/full
        # MODELS=a,b runs only those plan entries (a second box taking part of
        # the roster); the default is the whole roster.
        MODELS=${MODELS:+--models "$MODELS"}
        ;;
    *) echo "unknown mode $MODE" >&2; exit 2 ;;
esac

mkdir -p "$WORK"
# Weights are shared across modes; each mode keeps its own results and logs.
ln -sfn "$W/hf-cache" "$WORK/hf-cache"
cd "$REPO"
nohup .venv/bin/python scripts/deduction/packed_box.py \
    --spool-prefix "$PREFIX" \
    --sweep "$SWEEP" \
    --lean-data "$W/corpus_T2026-06-03/leandojo_benchmark_4" \
    --mathlib-root "$W/mathlib4" \
    --work "$WORK" $MODELS ${LIVE_LOGS:+--live-logs "$LIVE_LOGS"} ${PLAN:+--plan "$PLAN"} ${PASSES:+--passes "$PASSES"} \
    > "$WORK/packed_box.stdout" 2>&1 &
echo "started $MODE: pid $! work=$WORK s3=s3://smolbench-results-414266451290/$PREFIX"
