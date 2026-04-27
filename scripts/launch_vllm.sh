#!/usr/bin/env bash
# Launch a vLLM server hosting Qwen/Qwen2.5-Math-1.5B-Instruct on
# http://localhost:8010 for the SmolBench deductive-track local pilot.
#
# Hardware target: NixOS workstation, single NVIDIA RTX PRO 2000 Blackwell
# (compute cap 12.0), 8 GB VRAM, CUDA 13 driver. NVIDIA driver libs live in
# /run/opengl-driver/lib on NixOS rather than ldconfig's standard paths, so
# we export LD_LIBRARY_PATH so torch can dlopen libcuda.so.1.
#
# The script is intentionally lightweight: foreground or `nohup` from a wrapper
# as the caller prefers. Logs always go to /tmp/vllm_server.log so the next
# session can `tail` them.

set -euo pipefail

PROJECT_ROOT="/home/fisherxue/SmolBench"
MODEL="Qwen/Qwen2.5-Math-1.5B-Instruct"
PORT=8010
MAX_MODEL_LEN=4096   # matches Qwen2.5-Math-1.5B-Instruct's max_position_embeddings
GPU_MEM_UTIL=0.85
LOG_FILE="/tmp/vllm_server.log"

# NixOS: expose the system NVIDIA driver libs (libcuda.so.1, libnvidia-ml.so.1)
# to the venv's torch wheel.
export LD_LIBRARY_PATH="/run/opengl-driver/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# NixOS: Triton's libcuda autodetect calls /sbin/ldconfig which doesn't work
# on NixOS (real ldconfig lives at /run/current-system/sw/bin/ldconfig, and
# the /sbin shim errors). Set TRITON_LIBCUDA_PATH explicitly so Triton skips
# the ldconfig probe and uses our driver libs directly.
export TRITON_LIBCUDA_PATH="/run/opengl-driver/lib"

cd "$PROJECT_ROOT"

# Run via uv so we land in the project's .venv (vllm lives in the [gpu] extra).
#
# Notes on flags for RTX PRO 2000 Blackwell (sm_120, very new):
#   --enforce-eager                disables torch.compile + CUDA graph capture.
#                                  V1 engine's memory-determination step crashes
#                                  on this GPU during Dynamo lowering otherwise
#                                  (vllm 0.19.1 + CUDA 13 + Blackwell).
#   --disable-custom-all-reduce    only relevant on multi-GPU; harmless here
#                                  but explicit for clarity.
exec uv run vllm serve "$MODEL" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_MEM_UTIL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --dtype auto \
    --enforce-eager \
    --disable-custom-all-reduce \
    --api-key EMPTY \
    >> "$LOG_FILE" 2>&1
