#!/usr/bin/env bash
# Launch vLLM serving Kimina-Prover-72B on an H200 box for SmolBench.
#
# Defaults assume an 8×H200 box. Tensor-parallel-size of 2 leaves
# headroom and gives good throughput for batched inference; raise to 4 or 8
# if you want more KV-cache room.
#
# Override via env: MODEL, TP, PORT, MAX_LEN, GPU_MEM_UTIL, ROOT.
#
# Logs to $ROOT/logs/vllm.log. PID written to $ROOT/logs/vllm.pid.

set -euo pipefail

ROOT="${ROOT:-/opt/dlami/nvme/sb}"
MODEL="${MODEL:-AI-MO/Kimina-Prover-72B}"
# TP=4 is the safe default: Kimina-72B FP16 is ~144GB, which doesn't fit at
# TP=2 on 80GB H100s (36GB room per GPU after weights at TP=4 vs ~8GB at TP=2).
# H200 (144GB) can handle TP=2 — set TP=2 explicitly there if you want to
# free GPUs for other work.
TP="${TP:-4}"
PORT="${PORT:-8010}"
MAX_LEN="${MAX_LEN:-32768}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"
SERVED_NAME="${SERVED_NAME:-kimina-prover-72b}"

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
