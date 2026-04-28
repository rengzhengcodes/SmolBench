#!/usr/bin/env bash
# Launch vLLM serving Goedel-Prover-V2-32B on an H200 box for SmolBench.
#
# Defaults: TP=1 (32B fits comfortably on a single H200). Bump TP to 2 if
# you want more KV-cache headroom for high concurrency.
#
# Override via env: MODEL, TP, PORT, MAX_LEN, GPU_MEM_UTIL, ROOT.

set -euo pipefail

ROOT="${ROOT:-/opt/dlami/nvme/sb}"
MODEL="${MODEL:-Goedel-LM/Goedel-Prover-V2-32B}"
TP="${TP:-1}"
PORT="${PORT:-8010}"
MAX_LEN="${MAX_LEN:-32768}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"
SERVED_NAME="${SERVED_NAME:-goedel-prover-v2-32b}"

source "$ROOT/smolbench/.venv/bin/activate"
export HF_HOME="$ROOT/.cache/huggingface"
mkdir -p "$ROOT/logs"

echo "[vllm] launching $MODEL on port $PORT (TP=$TP, max_len=$MAX_LEN, util=$GPU_MEM_UTIL)" \
  | tee -a "$ROOT/logs/vllm.log"

nohup vllm serve "$MODEL" \
  --tensor-parallel-size "$TP" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --served-model-name "$SERVED_NAME" \
  --enable-prefix-caching \
  --trust-remote-code \
  >> "$ROOT/logs/vllm.log" 2>&1 &
echo $! > "$ROOT/logs/vllm.pid"
disown
echo "[vllm] pid $(cat $ROOT/logs/vllm.pid); tail -f $ROOT/logs/vllm.log"
