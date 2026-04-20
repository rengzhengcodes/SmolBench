#!/bin/bash
# Re-run DS-Prover-V2-7B with the model-matched prompt (SB_PROMPT_TYPE=dsprover).
# Standalone so SSH drops don't care: nohup this and walk away.

set -u
cd ~/SmolBench
source ~/.elan/env
export HF_HOME=/opt/dlami/nvme/sb/hf_cache

LOG_DIR=/opt/dlami/nvme/sb
S3="s3://training-runs-us-east-2-414266451290/runs/dev-fisher/"
MAIN_LOG="$LOG_DIR/dsprover7b_v2_main.log"

ts() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(ts)] $*" | tee -a "$MAIN_LOG"; }

cleanup_vllm() {
    pkill -9 -f "vllm serve" 2>/dev/null || true
    pkill -9 -f "VLLM::" 2>/dev/null || true
    pkill -9 -f EngineCore 2>/dev/null || true
    pkill -9 -f "vllm.*worker" 2>/dev/null || true
    sleep 20
}

log "=== DS-Prover 7B v2 RUN START ==="
cleanup_vllm
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | tee -a "$MAIN_LOG"

nohup uv run vllm serve deepseek-ai/DeepSeek-Prover-V2-7B \
    --port 8000 --max-model-len 16384 \
    --gpu-memory-utilization 0.85 \
    --tensor-parallel-size 1 \
    > "$LOG_DIR/vllm_dsprover7b_v2.log" 2>&1 &
VLLM_PID=$!
log "vllm pid=$VLLM_PID"

# Wait for port
WAITED=0
while ! ss -tln 2>/dev/null | grep -q ":8000 "; do
    sleep 15
    WAITED=$((WAITED + 15))
    if [ "$WAITED" -gt 600 ]; then
        log "ABORT: vLLM didn't listen in 10 min"
        aws s3 cp "$LOG_DIR/vllm_dsprover7b_v2.log" "${S3}vllm_dsprover7b_v2.log" --only-show-errors || true
        exit 1
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        log "ABORT: vLLM process died before serving"
        aws s3 cp "$LOG_DIR/vllm_dsprover7b_v2.log" "${S3}vllm_dsprover7b_v2.log" --only-show-errors || true
        exit 1
    fi
done
log "vLLM ready after ${WAITED}s"

# Warmup
curl -s -f -m 60 -H "Content-Type: application/json" \
    -X POST http://localhost:8000/v1/chat/completions \
    -d '{"model":"deepseek-ai/DeepSeek-Prover-V2-7B","messages":[{"role":"user","content":"hi"}],"max_tokens":4}' \
    > /dev/null || log "warmup request failed (continuing)"

SB_MODEL=deepseek-ai/DeepSeek-Prover-V2-7B \
SB_LOG_NAME=pilot_dsprover7b.jsonl \
SB_PROMPT_TYPE=dsprover \
SB_MAX_TOKENS_OUT=2048 \
    uv run python -m deduction.run_pilot > "$LOG_DIR/pilot_dsprover7b_v2.log" 2>&1

RC=$?
log "run_pilot rc=$RC"
LINES=$(wc -l < ~/SmolBench/data/pilot_dsprover7b.jsonl 2>/dev/null || echo 0)
log "log lines=$LINES"

aws s3 cp ~/SmolBench/data/pilot_dsprover7b.jsonl "${S3}pilot_dsprover7b.jsonl" --only-show-errors || true
aws s3 cp "$LOG_DIR/pilot_dsprover7b_v2.log" "${S3}pilot_dsprover7b_v2.log" --only-show-errors || true
aws s3 cp "$LOG_DIR/vllm_dsprover7b_v2.log" "${S3}vllm_dsprover7b_v2.log" --only-show-errors || true

kill -9 "$VLLM_PID" 2>/dev/null || true
cleanup_vllm
log "=== DS-Prover 7B v2 RUN END ==="
aws s3 cp "$MAIN_LOG" "${S3}dsprover7b_v2_main.log" --only-show-errors || true
