#!/usr/bin/env bash
# Gracefully stop a SmolBench run on this box. Sends SIGTERM to runner +
# s3_sync + spot_handler (so s3_sync flushes once before exit). vLLM and
# kimina are left running by default — pass STOP_SERVERS=1 to also stop
# them.
set -euo pipefail
ROOT="${ROOT:-/opt/dlami/nvme/sb}"
STOP_SERVERS="${STOP_SERVERS:-0}"

term() {
  local label="$1" pidfile="$2"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "[stop] SIGTERM $label pid=$pid"
      kill -TERM "$pid" || true
    else
      echo "[stop] $label pid=$pid not running"
    fi
  fi
}
term runner       "$ROOT/logs/runner.pid"
term s3_sync      "$ROOT/logs/s3_sync.pid"
term spot_handler "$ROOT/logs/spot_handler.pid"

if [[ "$STOP_SERVERS" == "1" ]]; then
  term vllm   "$ROOT/logs/vllm.pid"
  term kimina "$ROOT/logs/kimina.pid"
fi
echo "[stop] sent. tail logs to confirm exit."
