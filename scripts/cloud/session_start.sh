#!/bin/bash
# SessionStart hook for Claude Code cloud sessions (.claude/settings.json).
#
# Builds the project's single .venv (Python 3.12, every extra) in the fresh
# clone a cloud session starts from. A no-op anywhere else: the session VM
# sets CLAUDE_CODE_REMOTE=true and nothing local does, so a dev box keeps the
# .venv it already has.
#
# Runs on every startup and resume, so it stays idempotent and cheap: with
# the wheel cache the environment's setup script warmed (setup.sh), a repeat
# `uv sync` is a few seconds. Always exits 0 -- a failed sync must not block
# the session; the failure is printed for Claude to read and repair.

if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
    exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

# Same cache paths as setup.sh, so the snapshot's wheels and tiktoken
# encodings are found whichever user the session runs as. The environment's
# own variables win when set.
export UV_CACHE_DIR="${UV_CACHE_DIR:-/opt/smolbench-cache/uv}"
export TIKTOKEN_CACHE_DIR="${TIKTOKEN_CACHE_DIR:-/opt/smolbench-cache/tiktoken}"
# uv's interpreter download is a GitHub release asset the session's GitHub
# proxy rejects; fail at once with "no interpreter found" instead.
export UV_PYTHON_DOWNLOADS="${UV_PYTHON_DOWNLOADS:-never}"

# --frozen: install exactly uv.lock, never re-resolve or rewrite it.
# --quiet: hook output lands in the session context; keep it to two lines.
# --all-extras: the test suite imports the notebook extra (tests/README.md).
if uv sync --all-extras --frozen --quiet; then
    echo "smolbench cloud session: .venv ready ($(.venv/bin/python --version 2>&1), $(uv --version 2>&1))"
    echo "run the suite with: .venv/bin/python -m pytest tests/ -q"
else
    echo "smolbench cloud session: 'uv sync --all-extras --frozen' FAILED; .venv is missing or partial." >&2
    echo "see scripts/cloud/README.md (Troubleshooting) before running tests." >&2
fi
exit 0
