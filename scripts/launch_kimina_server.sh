#!/usr/bin/env bash
# Launch kimina-lean-server on an H200 box for SmolBench.
#
# Reads .env from the kimina-lean-server clone; expects bootstrap_h200.sh to
# have been run first.

set -euo pipefail

ROOT="${ROOT:-/opt/dlami/nvme/sb}"
KIMINA_DIR="$ROOT/external/kimina-lean-server"

cd "$KIMINA_DIR"
source .venv/bin/activate
export PATH="$HOME/.elan/bin:$PATH"
mkdir -p logs

echo "[kimina] starting on port $(grep ^LEAN_SERVER_PORT .env | cut -d= -f2)"
nohup python -m server >> logs/server.log 2>&1 &
echo $! > "$ROOT/logs/kimina.pid"
disown
echo "[kimina] pid $(cat $ROOT/logs/kimina.pid); tail -f $KIMINA_DIR/logs/server.log"
