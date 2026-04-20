#!/bin/bash
# Overnight deduction pilot: three models sequentially on the same 73x9xk=10 spec.
# Each model gets its own (target, condition) pool run, logged to a distinct
# JSONL file; each log is mirrored to S3 on completion. Run under nohup so
# SSH drops don't kill it.
#
# Usage (on EC2):
#   nohup bash ~/SmolBench/scripts/overnight.sh > /opt/dlami/nvme/sb/overnight.log 2>&1 &
#   disown

set -u  # fail on unset vars
# Do NOT set -e — we want to continue to the next model if one fails.

cd ~/SmolBench
source ~/.elan/env
export HF_HOME=/opt/dlami/nvme/sb/hf_cache

LOG_DIR=/opt/dlami/nvme/sb
S3_DEST="s3://training-runs-us-east-2-414266451290/runs/dev-fisher/"
MAIN_LOG="$LOG_DIR/overnight_main.log"

ts() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(ts)] $*" | tee -a "$MAIN_LOG"; }

cleanup_vllm() {
    # `kill -9` on the vllm launcher doesn't reliably reap EngineCore subprocesses;
    # they survive and hold VRAM, which blocks the next vllm launch with an OOM-ish
    # "free memory less than desired utilization" error. Nuke anything vllm-flavored
    # and give the driver a beat to reclaim the memory.
    pkill -9 -f "vllm serve" 2>/dev/null || true
    pkill -9 -f "VLLM::" 2>/dev/null || true
    pkill -9 -f "EngineCore" 2>/dev/null || true
    pkill -9 -f "vllm.*worker" 2>/dev/null || true
    sleep 20
    # Best-effort assertion: log VRAM state so a stuck GPU is visible in the log.
    nvidia-smi --query-gpu=index,memory.free --format=csv,noheader 2>&1 | tee -a "$MAIN_LOG"
}

log "=== OVERNIGHT RUN START ==="
log "--- pre-run cleanup ---"
cleanup_vllm

run_one() {
    local label="$1"     # short tag for filenames
    local model="$2"     # full HF model id
    local tp="$3"        # tensor parallel size
    local mml="$4"       # max_model_len
    local extra="$5"     # extra vllm args (e.g. --quantization fp8)
    local log_name="$6"  # output JSONL name under data/

    local vllm_log="$LOG_DIR/vllm_${label}.log"
    local pilot_log="$LOG_DIR/pilot_${label}.log"

    log "--- [${label}] BEGIN — model=${model} tp=${tp} mml=${mml} ---"

    # Launch vLLM
    # shellcheck disable=SC2086
    uv run vllm serve "$model" \
        --port 8000 \
        --max-model-len "$mml" \
        --gpu-memory-utilization 0.90 \
        --tensor-parallel-size "$tp" \
        $extra \
        > "$vllm_log" 2>&1 &
    local vllm_pid=$!
    log "  [${label}] vllm pid=${vllm_pid}"

    # Wait for port 8000 with timeout (30 min covers 671B download + load)
    local waited=0
    local timeout=1800
    while ! ss -tln 2>/dev/null | grep -q ":8000 "; do
        sleep 15
        waited=$((waited + 15))
        if [ "$waited" -gt "$timeout" ]; then
            log "  [${label}] ABORT — vLLM didn't listen within ${timeout}s; see ${vllm_log}"
            aws s3 cp "$vllm_log" "${S3_DEST}vllm_${label}.log" --only-show-errors || true
            kill -9 "$vllm_pid" 2>/dev/null || true
            cleanup_vllm
            return 1
        fi
        if ! kill -0 "$vllm_pid" 2>/dev/null; then
            log "  [${label}] ABORT — vllm process died before serving; see ${vllm_log}"
            aws s3 cp "$vllm_log" "${S3_DEST}vllm_${label}.log" --only-show-errors || true
            cleanup_vllm
            return 1
        fi
    done
    log "  [${label}] vLLM ready after ${waited}s"

    # Brief model health check (first call warms up the server)
    local tries=0
    while ! curl -s -f -m 30 -H "Content-Type: application/json" \
        -X POST http://localhost:8000/v1/chat/completions \
        -d "{\"model\":\"${model}\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":4}" \
        > /dev/null 2>&1; do
        tries=$((tries + 1))
        if [ "$tries" -gt 10 ]; then
            log "  [${label}] ABORT — server not answering after warmup"
            kill -9 "$vllm_pid" 2>/dev/null || true
            cleanup_vllm
            return 1
        fi
        sleep 10
    done
    log "  [${label}] server responding"

    # Run pilot — env vars override run_pilot.py defaults
    SB_MODEL="$model" SB_LOG_NAME="$log_name" \
        uv run python -m deduction.run_pilot > "$pilot_log" 2>&1
    local rc=$?
    log "  [${label}] run_pilot rc=${rc} — log $(wc -l < "${HOME}/SmolBench/data/${log_name}" 2>/dev/null || echo '?') lines"

    # Sync both the trial log and this stage's log to S3
    aws s3 cp "${HOME}/SmolBench/data/${log_name}" "${S3_DEST}${log_name}" --only-show-errors || true
    aws s3 cp "$pilot_log" "${S3_DEST}pilot_${label}.log" --only-show-errors || true
    aws s3 cp "$vllm_log" "${S3_DEST}vllm_${label}.log" --only-show-errors || true

    # Tear down vLLM and give VRAM time to free before the next model
    kill -9 "$vllm_pid" 2>/dev/null || true
    cleanup_vllm
    log "--- [${label}] END ---"
}

# ---- Stage 1: DeepSeek-Prover-V2-7B (Lean-4 finetuned, fits on 1 H100) ----
run_one "dsprover7b" \
    "deepseek-ai/DeepSeek-Prover-V2-7B" \
    1 16384 "" \
    "pilot_dsprover7b.jsonl"

# ---- Stage 2: Qwen 2.5 72B Instruct (general-purpose, TP=4) ----
run_one "qwen72b" \
    "Qwen/Qwen2.5-72B-Instruct" \
    4 16384 "" \
    "pilot_qwen72b.jsonl"

# ---- Stage 3: DeepSeek-Prover-V2-671B (Lean-4 finetuned, TP=8, native fp8) ----
# Shorter max_model_len to leave room for KV cache — 640 GB VRAM is tight
# against 650+ GB of fp8 weights. If this still OOMs, the stage is skipped.
run_one "dsprover671b" \
    "deepseek-ai/DeepSeek-Prover-V2-671B" \
    8 8192 "--quantization fp8" \
    "pilot_dsprover671b.jsonl"

# Final sync of the orchestrator log
aws s3 cp "$MAIN_LOG" "${S3_DEST}overnight_main.log" --only-show-errors || true

log "=== OVERNIGHT RUN END ==="
