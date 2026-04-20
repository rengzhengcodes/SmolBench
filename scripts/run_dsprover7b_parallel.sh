#!/bin/bash
# Multi-replica DS-Prover-V2-7B run: 8 vLLM instances, one per GPU, 64 Dojo
# workers. LLM side scales ~8x vs single-GPU; Dojo scales with CPU. Net
# throughput limited by Dojo (CPU-bound) but we raise its ceiling too.
#
# Standalone, nohup-friendly.

set -u
cd ~/SmolBench
source ~/.elan/env
export HF_HOME=/opt/dlami/nvme/sb/hf_cache

LOG_DIR=/opt/dlami/nvme/sb
S3="s3://training-runs-us-east-2-414266451290/runs/dev-fisher/"
MAIN_LOG="$LOG_DIR/dsprover7b_parallel_main.log"
N_REPLICAS=8
BASE_PORT=8000
MODEL="deepseek-ai/DeepSeek-Prover-V2-7B"

ts() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(ts)] $*" | tee -a "$MAIN_LOG"; }

cleanup_vllm() {
    pkill -9 -f "vllm serve" 2>/dev/null || true
    pkill -9 -f "VLLM::" 2>/dev/null || true
    pkill -9 -f EngineCore 2>/dev/null || true
    pkill -9 -f "vllm.*worker" 2>/dev/null || true
    sleep 10
    for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 15
}

log "=== DS-Prover 7B PARALLEL RUN START ==="
log "replicas=${N_REPLICAS}  base_port=${BASE_PORT}"
cleanup_vllm
nvidia-smi --query-gpu=index,memory.free --format=csv,noheader | tee -a "$MAIN_LOG"

# Launch one vLLM per GPU
declare -a VLLM_PIDS
for i in $(seq 0 $((N_REPLICAS - 1))); do
    port=$((BASE_PORT + i))
    log "launching replica gpu=$i port=$port"
    CUDA_VISIBLE_DEVICES=$i nohup uv run vllm serve "$MODEL" \
        --port "$port" \
        --max-model-len 16384 \
        --gpu-memory-utilization 0.85 \
        --tensor-parallel-size 1 \
        > "$LOG_DIR/vllm_7b_gpu${i}.log" 2>&1 &
    VLLM_PIDS+=($!)
done

# Wait for each replica's port to be listening
for i in $(seq 0 $((N_REPLICAS - 1))); do
    port=$((BASE_PORT + i))
    waited=0
    while ! ss -tln 2>/dev/null | grep -q ":${port} "; do
        sleep 15
        waited=$((waited + 15))
        if [ "$waited" -gt 600 ]; then
            log "ABORT: replica on port $port didn't listen in 10 min"
            cleanup_vllm
            aws s3 cp "$LOG_DIR/vllm_7b_gpu${i}.log" "${S3}vllm_7b_gpu${i}.log" --only-show-errors || true
            exit 1
        fi
    done
    log "  replica gpu=$i port=$port ready after ${waited}s"
done

# Build the CSV endpoint list
URLS=""
for i in $(seq 0 $((N_REPLICAS - 1))); do
    port=$((BASE_PORT + i))
    URLS="${URLS}${URLS:+,}http://localhost:${port}/v1"
done
log "endpoint csv: $URLS"

# Run the pilot with round-robin across all endpoints and 64 Dojo workers
SB_MODEL="$MODEL" \
SB_LOG_NAME=pilot_dsprover7b.jsonl \
SB_PROMPT_TYPE=dsprover \
SB_MAX_TOKENS_OUT=2048 \
SB_BASE_URLS="$URLS" \
SB_MAX_WORKERS=64 \
    uv run python -m deduction.run_pilot > "$LOG_DIR/pilot_dsprover7b_parallel.log" 2>&1
RC=$?
log "run_pilot rc=$RC"
LINES=$(wc -l < ~/SmolBench/data/pilot_dsprover7b.jsonl 2>/dev/null || echo 0)
log "log lines=$LINES"

aws s3 cp ~/SmolBench/data/pilot_dsprover7b.jsonl "${S3}pilot_dsprover7b.jsonl" --only-show-errors || true
aws s3 cp "$LOG_DIR/pilot_dsprover7b_parallel.log" "${S3}pilot_dsprover7b_parallel.log" --only-show-errors || true
for i in $(seq 0 $((N_REPLICAS - 1))); do
    aws s3 cp "$LOG_DIR/vllm_7b_gpu${i}.log" "${S3}vllm_7b_gpu${i}.log" --only-show-errors || true
done

for pid in "${VLLM_PIDS[@]}"; do kill -9 "$pid" 2>/dev/null || true; done
cleanup_vllm
log "=== DS-Prover 7B PARALLEL RUN END ==="
aws s3 cp "$MAIN_LOG" "${S3}dsprover7b_parallel_main.log" --only-show-errors || true
