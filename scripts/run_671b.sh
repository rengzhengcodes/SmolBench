#!/bin/bash
# DeepSeek-Prover-V2-671B pilot. TP=8 + MoE expert parallel + NCCL env tuning.
# Native fp8 weights (~671 GB) vs 640 GB aggregate VRAM make this tight;
# --enable-expert-parallel shards experts across GPUs so per-GPU footprint
# matches the 37B active params rather than the 671B total.
#
# Standalone so SSH drops don't kill it: nohup this and walk away.

set -u
cd ~/SmolBench
source ~/.elan/env
export HF_HOME=/opt/dlami/nvme/sb/hf_cache

# NCCL + vLLM multiprocessing env that unsticks TP on 8x H100 DLAMIs.
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export NCCL_P2P_LEVEL=NVL
export NCCL_IB_DISABLE=1
export NCCL_SHM_DISABLE=0
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT

LOG_DIR=/opt/dlami/nvme/sb
S3="s3://training-runs-us-east-2-414266451290/runs/dev-fisher/"
MAIN_LOG="$LOG_DIR/dsprover671b_main.log"

ts() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(ts)] $*" | tee -a "$MAIN_LOG"; }

cleanup_vllm() {
    pkill -9 -f "vllm serve" 2>/dev/null || true
    pkill -9 -f "VLLM::" 2>/dev/null || true
    pkill -9 -f EngineCore 2>/dev/null || true
    pkill -9 -f "vllm.*worker" 2>/dev/null || true
    sleep 30  # big model needs more time for driver to reclaim VRAM
}

log "=== DS-Prover 671B RUN START ==="
log "VLLM_WORKER_MULTIPROC_METHOD=$VLLM_WORKER_MULTIPROC_METHOD"
log "NCCL_P2P_LEVEL=$NCCL_P2P_LEVEL NCCL_IB_DISABLE=$NCCL_IB_DISABLE"
cleanup_vllm
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | tee -a "$MAIN_LOG"

nohup uv run vllm serve deepseek-ai/DeepSeek-Prover-V2-671B \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.92 \
    --tensor-parallel-size 8 \
    --enable-expert-parallel \
    --trust-remote-code \
    > "$LOG_DIR/vllm_dsprover671b_v2.log" 2>&1 &
VLLM_PID=$!
log "vllm pid=$VLLM_PID"

# 671B download was pre-fetched, so model load dominates (~10-20 min for TP=8)
WAITED=0
TIMEOUT=2400  # 40 min cap
while ! ss -tln 2>/dev/null | grep -q ":8000 "; do
    sleep 20
    WAITED=$((WAITED + 20))
    if [ "$WAITED" -gt "$TIMEOUT" ]; then
        log "ABORT: vLLM didn't listen within ${TIMEOUT}s"
        aws s3 cp "$LOG_DIR/vllm_dsprover671b_v2.log" "${S3}vllm_dsprover671b_v2.log" --only-show-errors || true
        cleanup_vllm
        aws s3 cp "$MAIN_LOG" "${S3}dsprover671b_main.log" --only-show-errors || true
        exit 1
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        log "ABORT: vLLM process died before serving"
        aws s3 cp "$LOG_DIR/vllm_dsprover671b_v2.log" "${S3}vllm_dsprover671b_v2.log" --only-show-errors || true
        cleanup_vllm
        aws s3 cp "$MAIN_LOG" "${S3}dsprover671b_main.log" --only-show-errors || true
        exit 1
    fi
    if [ $((WAITED % 120)) -eq 0 ]; then
        log "  still waiting after ${WAITED}s ..."
    fi
done
log "vLLM ready after ${WAITED}s"

# Warmup
curl -s -f -m 120 -H "Content-Type: application/json" \
    -X POST http://localhost:8000/v1/chat/completions \
    -d '{"model":"deepseek-ai/DeepSeek-Prover-V2-671B","messages":[{"role":"user","content":"hi"}],"max_tokens":4}' \
    > /dev/null || log "warmup request failed (continuing)"

SB_MODEL=deepseek-ai/DeepSeek-Prover-V2-671B \
SB_LOG_NAME=pilot_dsprover671b.jsonl \
SB_PROMPT_TYPE=dsprover \
SB_MAX_TOKENS_OUT=2048 \
SB_BUDGET_TOKENS=3500 \
SB_MAX_WORKERS=8 \
    uv run python -m deduction.run_pilot > "$LOG_DIR/pilot_dsprover671b.log" 2>&1

RC=$?
log "run_pilot rc=$RC"
LINES=$(wc -l < ~/SmolBench/data/pilot_dsprover671b.jsonl 2>/dev/null || echo 0)
log "log lines=$LINES"

aws s3 cp ~/SmolBench/data/pilot_dsprover671b.jsonl "${S3}pilot_dsprover671b.jsonl" --only-show-errors || true
aws s3 cp "$LOG_DIR/pilot_dsprover671b.log" "${S3}pilot_dsprover671b.log" --only-show-errors || true
aws s3 cp "$LOG_DIR/vllm_dsprover671b_v2.log" "${S3}vllm_dsprover671b_v2.log" --only-show-errors || true

kill -9 "$VLLM_PID" 2>/dev/null || true
cleanup_vllm
log "=== DS-Prover 671B RUN END ==="
aws s3 cp "$MAIN_LOG" "${S3}dsprover671b_main.log" --only-show-errors || true
