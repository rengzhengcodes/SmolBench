#!/usr/bin/env bash
# Master launcher: brings up kimina + vLLM + s3-sync + spot-handler, then
# runs the (target × K × B × seed) grid. Designed for spot-instance use:
# all child processes are managed via pidfiles so the spot-handler can
# graceful-drain on the 2-minute interruption notice.
#
# Required env (from caller):
#   RUN_NAME           short tag, e.g. "kimina72b_pilot1"
#   MODEL_KIND         "kimina72b" or "goedel32b" — selects vLLM script
#   MODEL_SERVED_NAME  string vLLM advertises (must match runner --model arg)
#   POOL               replay-pool path (default: $ROOT/data/replay_pool.jsonl)
#   KS                 e.g. "0,1,2,3" (default)
#   BS                 e.g. "0,1,2,3,4" (default)
#   K_SEEDS            decoding seeds per cell (default 4)
#   TARGET_LIMIT       cap on targets (default empty)
#   WORKERS            cells in flight (default 4)
#   MAX_TOKENS         per-completion (default 4096)
#   MAX_PROMPT_CHARS   skip cells over this (default 100000)
#   S3_BUCKET          default s3://smolbench-deductive
#   ROOT               install root (default /opt/dlami/nvme/sb)
#
# Pidfiles + logs live under $ROOT/logs/. JSONL output under
# $ROOT/runs/$RUN_NAME/cells.jsonl. S3 mirror at
# s3://smolbench-deductive/runs/<hostname>/$RUN_NAME/.
#
# To stop everything cleanly:
#   bash scripts/stop_run.sh

set -euo pipefail
trap 'echo "[launch_run] FAILED at line $LINENO" >&2' ERR

ROOT="${ROOT:-/opt/dlami/nvme/sb}"
S3_BUCKET="${S3_BUCKET:-s3://smolbench-deductive}"
RUN_NAME="${RUN_NAME:?RUN_NAME required}"
MODEL_KIND="${MODEL_KIND:?MODEL_KIND required (kimina72b|goedel32b)}"
MODEL_SERVED_NAME="${MODEL_SERVED_NAME:-}"
POOL="${POOL:-$ROOT/data/replay_pool.jsonl}"
KS="${KS:-0,1,2,3}"
BS="${BS:-0,1,2,3,4}"
K_SEEDS="${K_SEEDS:-4}"
TARGET_LIMIT="${TARGET_LIMIT:-}"
WORKERS="${WORKERS:-4}"
MAX_TOKENS="${MAX_TOKENS:-4096}"
MAX_PROMPT_CHARS="${MAX_PROMPT_CHARS:-100000}"
SYNC_INTERVAL="${SYNC_INTERVAL:-60}"

case "$MODEL_KIND" in
  kimina72b)
    VLLM_SCRIPT="$ROOT/smolbench/scripts/launch_vllm_kimina72b.sh"
    : "${MODEL_SERVED_NAME:=kimina-prover-72b}"
    ;;
  goedel32b)
    VLLM_SCRIPT="$ROOT/smolbench/scripts/launch_vllm_goedel32b.sh"
    : "${MODEL_SERVED_NAME:=goedel-prover-v2-32b}"
    ;;
  *) echo "Unknown MODEL_KIND=$MODEL_KIND"; exit 2 ;;
esac

HOSTNAME_TAG="$(hostname)"
RUN_DIR="$ROOT/runs/$RUN_NAME"
S3_DST="$S3_BUCKET/runs/$HOSTNAME_TAG/$RUN_NAME/"
mkdir -p "$RUN_DIR" "$ROOT/logs"

log() { echo "[launch_run $(date -u +%H:%M:%S)] $*"; }

# ---------- 1. kimina ----------
if ! curl -sf "http://127.0.0.1:9000/" >/dev/null 2>&1; then
  log "starting kimina-lean-server"
  bash "$ROOT/smolbench/scripts/launch_kimina_server.sh"
  log "waiting for kimina to come up (max 60s)"
  for i in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:9000/" >/dev/null 2>&1; then
      log "kimina up after ${i}s"
      break
    fi
    sleep 1
    if [[ $i -eq 60 ]]; then log "kimina did not come up in 60s"; exit 3; fi
  done
else
  log "kimina already up"
fi

# ---------- 2. vLLM ----------
if ! curl -sf "http://127.0.0.1:8010/v1/models" >/dev/null 2>&1; then
  log "starting vLLM via $VLLM_SCRIPT"
  bash "$VLLM_SCRIPT"
  log "waiting for vLLM to come up (max 600s — model load is slow)"
  for i in $(seq 1 600); do
    if curl -sf "http://127.0.0.1:8010/v1/models" >/dev/null 2>&1; then
      log "vLLM up after ${i}s"
      break
    fi
    sleep 1
    if [[ $i -eq 600 ]]; then log "vLLM did not come up in 10min"; exit 4; fi
  done
else
  log "vLLM already up"
fi

# ---------- 3. s3_sync ----------
SYNC_PID="$ROOT/logs/s3_sync.pid"
if [[ ! -f "$SYNC_PID" ]] || ! kill -0 "$(cat "$SYNC_PID")" 2>/dev/null; then
  log "starting s3-sync daemon -> $S3_DST"
  source "$ROOT/smolbench/.venv/bin/activate"
  nohup python -m deduction.s3_sync \
    --src "$RUN_DIR" \
    --dst "$S3_DST" \
    --interval "$SYNC_INTERVAL" \
    --metrics-interval 30 \
    >> "$ROOT/logs/s3_sync.log" 2>&1 &
  echo $! > "$SYNC_PID"
  disown
  deactivate
  log "s3_sync pid=$(cat "$SYNC_PID")"
fi

# ---------- 4. spot_handler ----------
SPOT_PID="$ROOT/logs/spot_handler.pid"
if [[ ! -f "$SPOT_PID" ]] || ! kill -0 "$(cat "$SPOT_PID")" 2>/dev/null; then
  log "starting spot interruption watchdog"
  source "$ROOT/smolbench/.venv/bin/activate"
  nohup python -m deduction.spot_handler \
    --runner-pidfile "$ROOT/logs/runner.pid" \
    --sync-pidfile  "$SYNC_PID" \
    --src "$RUN_DIR" \
    --dst "$S3_DST" \
    --event-log "$RUN_DIR/spot_events.jsonl" \
    >> "$ROOT/logs/spot_handler.log" 2>&1 &
  echo $! > "$SPOT_PID"
  disown
  deactivate
  log "spot_handler pid=$(cat "$SPOT_PID")"
fi

# ---------- 5. runner (foreground, with pidfile) ----------
RUNNER_PID="$ROOT/logs/runner.pid"
echo $$ > "$RUNNER_PID"
trap 'rm -f "$RUNNER_PID"' EXIT

log "launching runner: RUN=$RUN_NAME MODEL=$MODEL_SERVED_NAME"
log "  KS=$KS BS=$BS K_SEEDS=$K_SEEDS WORKERS=$WORKERS"
log "  POOL=$POOL TARGET_LIMIT=${TARGET_LIMIT:-<all>}"
log "  OUT=$RUN_DIR/cells.jsonl"
log "  S3=$S3_DST"

cd "$ROOT/smolbench"
source .venv/bin/activate

EXTRA_ARGS=()
[[ -n "$TARGET_LIMIT" ]] && EXTRA_ARGS+=(--target-limit "$TARGET_LIMIT")

# Re-exec the runner so its PID becomes the script's PID (lets spot_handler
# SIGTERM the actual python).
exec python -m deduction.runner \
  --pool "$POOL" \
  --out "$RUN_DIR/cells.jsonl" \
  --ks "$KS" --bs "$BS" --k-seeds "$K_SEEDS" \
  --workers "$WORKERS" \
  --model "$MODEL_SERVED_NAME" \
  --vllm-url "http://127.0.0.1:8010/v1" \
  --server-url "http://127.0.0.1:9000" \
  --max-tokens "$MAX_TOKENS" \
  --max-prompt-chars "$MAX_PROMPT_CHARS" \
  "${EXTRA_ARGS[@]}"
