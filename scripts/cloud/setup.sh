#!/bin/bash
# Setup script for the SmolBench cloud environment. PASTE THIS FILE into the
# "Setup script" field of the environment dialog at claude.ai/code -- the
# dialog is the only place a setup script can live; this copy is the source
# of truth (see scripts/cloud/README.md).
#
# Runs once as root on Ubuntu 24.04 before Claude Code launches; the
# filesystem is then snapshotted and reused for about seven days, provided
# the script finishes in roughly five minutes. So it only provisions the VM
# and warms caches. The .venv itself is built per session by
# session_start.sh, against whichever branch that session cloned.
#
# Every step is best-effort: a non-zero exit fails session start, and a cold
# cache only costs the first `uv sync` a minute or two.

# SMOLBENCH_CLOUD_CACHE relocates the caches for a dry run off the VM.
CACHE_ROOT="${SMOLBENCH_CLOUD_CACHE:-/opt/smolbench-cache}"
export UV_CACHE_DIR="$CACHE_ROOT/uv"
export TIKTOKEN_CACHE_DIR="$CACHE_ROOT/tiktoken"
export UV_PYTHON_DOWNLOADS=never
mkdir -p "$UV_CACHE_DIR" "$TIKTOKEN_CACHE_DIR"

# requires-python is >=3.12,<3.13. Ubuntu 24.04 ships 3.12 as its system
# python; install it from apt if this image does not. uv's own interpreter
# download is a GitHub release asset of a repository the session does not
# have attached, which the GitHub proxy answers with a 403.
if ! uv python find 3.12 >/dev/null 2>&1; then
    (apt-get update && apt-get install -y python3.12 python3.12-venv) || true
fi

# Warm the wheel cache from the lockfile when the clone is already on disk.
# Where this script runs relative to the clone is not documented, so look
# rather than assume; without a clone the first session fills the cache.
warm_wheels() {
    local dir
    for dir in "$PWD" "${CLAUDE_PROJECT_DIR:-}" /home/user/SmolBench /workspace/SmolBench; do
        if [ -n "$dir" ] && [ -f "$dir/uv.lock" ] && grep -q '^name = "smolbench"' "$dir/pyproject.toml" 2>/dev/null; then
            # A throwaway environment outside the clone: only the cache is kept.
            (cd "$dir" && UV_PROJECT_ENVIRONMENT=/tmp/smolbench-warm-venv \
                uv sync --all-extras --frozen --no-install-project)
            rm -rf /tmp/smolbench-warm-venv
            return
        fi
    done
    echo "setup.sh: no SmolBench clone found; wheel cache left cold"
}

# Pre-fetch the tiktoken encodings the offline tests load. Their host
# (openaipublic.blob.core.windows.net) is outside the Trusted list, so this
# only succeeds under the Custom allowlist in the README; the tests skip
# cleanly when the encodings are absent.
warm_tiktoken() {
    uv run --no-project --with 'tiktoken>=0.13' python -c '
import tiktoken
for name in ("cl100k_base", "o200k_base"):
    tiktoken.get_encoding(name)
    print("cached tiktoken encoding", name)
'
}

# Exit status stays 0 whatever happens below, so say plainly when uv itself
# is missing: the README's check reads the cache sizes this leaves behind.
command -v uv >/dev/null || echo "setup.sh: uv is not on PATH ($PATH); caches left cold"

warm_wheels &
warm_tiktoken &
wait
du -sh "$CACHE_ROOT"/* 2>/dev/null

# Sessions may not run as root; leave the caches writable for any user.
chmod -R a+rwX "$CACHE_ROOT" || true
exit 0
