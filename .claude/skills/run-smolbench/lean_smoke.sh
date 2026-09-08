#!/usr/bin/env bash
# Credential-free import and fixture smoke for the Lean benchmark. ``--replay``
# additionally drives one theorem through a configured real Lean checkout.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

.venv/bin/python -c "import smolbench.deduction.lean.runner, smolbench.deduction.lean.cli, sys; assert 'lean_interact' not in sys.modules" \
    || { echo "FAIL: runner/cli imported lean_interact" >&2; exit 1; }
echo "PASS — Tier 0 imports."

uv sync -q --all-extras
FIXTURE=tests/fixtures/lean_mini_postcutoff
SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" \
    .venv/bin/python -m smolbench.deduction.lean.cli metadata
list_out=$(SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" \
    .venv/bin/python -m smolbench.deduction.lean.cli list --kind random --split val --limit 5)
grep -q "theorems with traced tactics in random/val" <<<"$list_out"
echo "PASS — Tier 1 fixture metadata and listing."

need_mathlib_root() {
    [ -n "${SMOLBENCH_MATHLIB_ROOT:-}" ] || {
        echo "FAIL: SMOLBENCH_MATHLIB_ROOT is not set" >&2; exit 1;
    }
}

if [ "${1:-}" = "--replay" ]; then
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || { echo "FAIL: elan not found" >&2; exit 1; }
    need_mathlib_root
    [ -n "${SMOLBENCH_LEAN_DATA:-}" ] || {
        echo "FAIL: SMOLBENCH_LEAN_DATA is not set" >&2; exit 1;
    }
    .venv/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0
    echo "PASS — real Lean replay."
elif [ -n "${1:-}" ]; then
    echo "unknown argument: $1" >&2
    exit 2
fi
