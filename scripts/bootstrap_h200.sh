#!/usr/bin/env bash
# Bootstrap a fresh H200 spot instance for the SmolBench deductive run.
#
# Idempotent: re-running picks up where the last attempt left off (each
# heavy step checks for a sentinel file before redoing work). Safe to run
# after a spot-restart.
#
# Lays everything out under /opt/dlami/nvme/sb/ so the tiny root volume
# isn't touched.
#
# Usage on a fresh box:
#   curl -sL https://raw.githubusercontent.com/<repo>/.../bootstrap_h200.sh | bash
# OR scp this file over and:
#   bash bootstrap_h200.sh
#
# Required env (set before running, or this script will set sensible defaults):
#   SMOL_BRANCH       git branch to check out (default: deduction-rewrite)
#   SMOL_REPO         git URL for SmolBench (default: empty -> rsync'd in by operator)
#   S3_CACHE          s3://bucket/path/ holding pre-staged tarballs
#                     (default: s3://smolbench-deductive/cache)
#   ROOT              install root (default: /opt/dlami/nvme/sb)

set -euo pipefail
trap 'echo "[bootstrap] FAILED at line $LINENO" >&2' ERR

ROOT="${ROOT:-/opt/dlami/nvme/sb}"
S3_CACHE="${S3_CACHE:-s3://smolbench-deductive/cache}"
SMOL_BRANCH="${SMOL_BRANCH:-deduction-rewrite}"
SMOL_REPO="${SMOL_REPO:-}"
LEAN_TOOLCHAIN="leanprover/lean4:v4.10.0-rc1"
MATHLIB_SHA="29dcec074de168ac2bf835a77ef68bbe069194c5"

mkdir -p "$ROOT" "$ROOT/external" "$ROOT/data" "$ROOT/logs" "$ROOT/runs" "$ROOT/sentinels"
cd "$ROOT"

log() { echo "[bootstrap $(date -u +%H:%M:%S)] $*"; }
done_marker() { touch "$ROOT/sentinels/$1.done"; }
already_done() { [[ -f "$ROOT/sentinels/$1.done" ]]; }

# ---------- 1. apt deps ----------
if ! already_done apt; then
  log "installing apt deps"
  sudo apt-get update -qq
  sudo apt-get install -y -qq build-essential curl git unzip jq pigz \
    pkg-config libssl-dev ca-certificates
  done_marker apt
fi

# ---------- 2. elan + lean toolchain ----------
if ! already_done elan; then
  log "installing elan"
  if [[ ! -x "$HOME/.elan/bin/elan" ]]; then
    curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
      | sh -s -- -y --default-toolchain "$LEAN_TOOLCHAIN"
  fi
  export PATH="$HOME/.elan/bin:$PATH"
  elan toolchain install "$LEAN_TOOLCHAIN"
  elan default "$LEAN_TOOLCHAIN"
  done_marker elan
fi
export PATH="$HOME/.elan/bin:$PATH"

# ---------- 3. uv (already on DLAMI but pin behavior) ----------
command -v uv >/dev/null || { log "uv not found"; exit 1; }

# ---------- 4. SmolBench source ----------
if [[ ! -d "$ROOT/smolbench" ]]; then
  log "cloning SmolBench branch=$SMOL_BRANCH"
  if [[ -n "$SMOL_REPO" ]]; then
    git clone --branch "$SMOL_BRANCH" --single-branch "$SMOL_REPO" "$ROOT/smolbench"
  else
    log "SMOL_REPO not set — operator must rsync source to $ROOT/smolbench"
    log "  e.g.: rsync -av --exclude=data --exclude=external ~/SmolBench/ ubuntu@<box>:$ROOT/smolbench/"
  fi
fi

# ---------- 5. SmolBench python venv (vllm + deduction deps) ----------
if [[ ! -d "$ROOT/smolbench/.venv" ]] && [[ -d "$ROOT/smolbench" ]]; then
  log "creating smolbench venv"
  cd "$ROOT/smolbench"
  uv venv --python 3.12 .venv
  source .venv/bin/activate
  # Install smolbench + vllm. vllm is heavy (~6GB of wheels) — be patient.
  uv pip install -e ".[gpu]"
  uv pip install huggingface_hub
  deactivate
  cd "$ROOT"
fi

# ---------- 6. REPL (Lean) ----------
if ! already_done repl; then
  log "fetching REPL from S3 + building"
  rm -rf "$ROOT/external/repl"
  aws s3 cp "$S3_CACHE/repl.tar.gz" - | gunzip | tar -x -C "$ROOT/external/"
  # The S3 tarball was packed from a NixOS box and may carry a .lake/build
  # whose binary's ELF interpreter points at /nix/store/.../ld-linux. Force
  # a clean Ubuntu rebuild so the resulting binary is loadable here.
  rm -rf "$ROOT/external/repl/.lake/build"
  cd "$ROOT/external/repl"
  lake build
  test -x .lake/build/bin/repl || { log "REPL binary missing after build"; exit 1; }
  # Sanity-check the binary actually runs (catches NixOS-linker leftovers).
  if ! "$ROOT/external/repl/.lake/build/bin/repl" --help >/dev/null 2>&1; then
    log "REPL binary built but won't execute; checking ldd:"
    ldd "$ROOT/external/repl/.lake/build/bin/repl" | head -10 || true
    exit 1
  fi
  cd "$ROOT"
  done_marker repl
fi

# ---------- 7. kimina-lean-server (clone + patch + venv + prisma) ----------
if ! already_done kimina; then
  log "installing kimina-lean-server"
  cd "$ROOT/external"
  if [[ ! -d kimina-lean-server ]]; then
    git clone --depth 1 https://github.com/project-numina/kimina-lean-server.git
  fi
  cd kimina-lean-server
  # Apply the no-mathlib-collapse patch. Detect by looking for the patched
  # comment marker; skip the apply if already present.
  aws s3 cp "$S3_CACHE/kimina-no-mathlib-collapse.patch" /tmp/kimina.patch
  if grep -q "defeats our truncated-imports defense" server/split.py 2>/dev/null; then
    log "kimina-no-mathlib-collapse patch already applied"
  else
    log "applying kimina-no-mathlib-collapse patch"
    git apply /tmp/kimina.patch || { log "patch failed"; exit 1; }
  fi
  # Python deps
  if [[ ! -d .venv ]]; then
    uv venv --python 3.12 .venv
  fi
  source .venv/bin/activate
  uv pip install -r requirements.txt
  uv pip install .
  # Prisma generate. On Ubuntu, prisma's pip install fetches engine binaries
  # — no nix-shell needed.
  PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1 \
    LEAN_SERVER_DATABASE_URL='postgresql://dummy:dummy@localhost:5432/dummy' \
    prisma generate --schema prisma/schema.prisma
  deactivate
  cd "$ROOT"
  done_marker kimina
fi

# ---------- 8. LeanDojo benchmark + Mathlib build cache ----------
if ! already_done benchmark; then
  log "fetching leandojo_benchmark_4 from S3"
  aws s3 cp "$S3_CACHE/leandojo_benchmark_4.tar.gz" - | tar -xz -C "$ROOT/data/"
  done_marker benchmark
fi

if ! already_done cache; then
  log "fetching lean_dojo_cache from S3 (~3GB compressed)"
  aws s3 cp "$S3_CACHE/lean_dojo_cache.tar.gz" - | gunzip | tar -x -C "$ROOT/data/"
  # The original lean_dojo_cache.tar.gz on S3 is missing the per-package
  # build/lib oleans for aesop/batteries/proofwidgets/Qq/importGraph.
  # Apply the small fixup tarball.
  log "applying dep_oleans_fixup (~67MB)"
  aws s3 cp "$S3_CACHE/dep_oleans_fixup.tar.gz" - \
    | tar -xz -C "$ROOT/data/lean_dojo_cache/leanprover-community-mathlib4-${MATHLIB_SHA}/mathlib4/"
  done_marker cache
fi

if ! already_done pool; then
  aws s3 cp "$S3_CACHE/replay_pool.jsonl" "$ROOT/data/replay_pool.jsonl"
  done_marker pool
fi

# ---------- 8b. data/mathlib4 symlink ----------
# corpus.py reads source ranges via MATHLIB_DIR = data/mathlib4. The cache
# tarball contains the same source under lean_dojo_cache/.../mathlib4 — point
# data/mathlib4 at it so we don't need to ship the source tree twice.
if [[ ! -e "$ROOT/data/mathlib4" ]]; then
  ln -snf "$ROOT/data/lean_dojo_cache/leanprover-community-mathlib4-${MATHLIB_SHA}/mathlib4" \
    "$ROOT/data/mathlib4"
fi

# ---------- 9. kimina .env ----------
KIMINA_PROJECT_DIR="$ROOT/data/lean_dojo_cache/leanprover-community-mathlib4-${MATHLIB_SHA}/mathlib4"
ENV_FILE="$ROOT/external/kimina-lean-server/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  log "writing kimina .env"
  cat > "$ENV_FILE" <<EOF
LEAN_SERVER_HOST=127.0.0.1
LEAN_SERVER_PORT=9000
LEAN_SERVER_LOG_LEVEL=INFO
LEAN_SERVER_ENVIRONMENT=dev
LEAN_SERVER_LEAN_VERSION=v4.10.0-rc1
LEAN_SERVER_MAX_REPLS=4
LEAN_SERVER_MAX_REPL_USES=-1
LEAN_SERVER_MAX_REPL_MEM=24G
LEAN_SERVER_MAX_WAIT=180
LEAN_SERVER_INIT_REPLS={}
LEAN_SERVER_REPL_PATH=$ROOT/external/repl/.lake/build/bin/repl
LEAN_SERVER_PROJECT_DIR=$KIMINA_PROJECT_DIR
EOF
fi

# ---------- 10. data symlink so smolbench code finds artifacts ----------
if [[ -d "$ROOT/smolbench" ]]; then
  if [[ -e "$ROOT/smolbench/data" && ! -L "$ROOT/smolbench/data" ]]; then
    log "WARN: $ROOT/smolbench/data exists and is not a symlink; leaving alone"
  elif [[ ! -e "$ROOT/smolbench/data" ]]; then
    ln -s "$ROOT/data" "$ROOT/smolbench/data"
  fi
  if [[ -e "$ROOT/smolbench/external" && ! -L "$ROOT/smolbench/external" ]]; then
    log "WARN: $ROOT/smolbench/external exists and is not a symlink; leaving alone"
  elif [[ ! -e "$ROOT/smolbench/external" ]]; then
    ln -s "$ROOT/external" "$ROOT/smolbench/external"
  fi
fi

# ---------- 11. Hugging Face cache on NVMe ----------
mkdir -p "$ROOT/.cache/huggingface"
grep -q HF_HOME "$HOME/.bashrc" 2>/dev/null || \
  echo "export HF_HOME=$ROOT/.cache/huggingface" >> "$HOME/.bashrc"
export HF_HOME="$ROOT/.cache/huggingface"

log "DONE. Root: $ROOT"
log "Next: launch kimina + vLLM with the per-model script, then run smoke test."
