#!/usr/bin/env bash
# Smoke driver for the Lean benchmark. The default is credential-free and
# Lean-free: import generation/analysis, sync the environment, then run
# metadata/list against the committed post-cutoff fixture. It does not
# download a corpus. ``--replay`` additionally drives one theorem through a
# configured real Lean checkout.
#
# The old 2024-03-24 corpus is invalid for the roster because every model
# cutoff postdates it; build a real post-cutoff corpus with
# scripts/deduction/build_postcutoff_corpus.py.
#
#   bash .claude/skills/run-smolbench/lean_smoke.sh
#   bash .claude/skills/run-smolbench/lean_smoke.sh --replay
#
# Replay needs elan, a BUILT mathlib4 checkout in SMOLBENCH_MATHLIB_ROOT, and
# a REAL corpus in SMOLBENCH_LEAN_DATA. The fixture's Mini.theoremA/B are
# fictional and cannot replay. The verifier drives leanprover-community/repl
# through lean-interact against the local checkout; it downloads no corpus.
# Retired-backend cold/warm budgets have not been re-measured.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
# uv-managed Python needs the system CA bundle if sync must download packages.
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Assert on sys.modules because lean_interact is installed: a bare successful
# import would not prove runner/cli kept the backend optional.
.venv/bin/python -c "import smolbench.deduction.lean.runner, smolbench.deduction.lean.cli, sys; assert 'lean_interact' not in sys.modules, 'runner/cli pulled in lean_interact'" \
    || { echo "FAIL: runner/cli must import without lean_interact" >&2; exit 1; }
echo "PASS — Tier 0 imports."

uv sync -q --all-extras
# Scope the fixture fallback to each command so a caller's real corpus remains
# visible to replay below.
FIXTURE=tests/fixtures/lean_mini_postcutoff
metadata_out=$(SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" \
    .venv/bin/python -m smolbench.deduction.lean.cli metadata)
echo "$metadata_out"
# Check the semantic postcutoff block, not a dataset-name substring: real
# builder output does not contain "LeanDojo Benchmark 4" in its name.
SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" .venv/bin/python -c \
    "from smolbench.deduction.lean import corpus as c; assert c.is_postcutoff_corpus(), c.data_root()" \
    || { echo "FAIL: active corpus is not post-cutoff (see scripts/deduction/build_postcutoff_corpus.py)" >&2; exit 1; }
list_out=$(SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" \
    .venv/bin/python -m smolbench.deduction.lean.cli list --kind random --split val --limit 5)
echo "$list_out"
grep -q "theorems with traced tactics in random/val" <<<"$list_out" \
    || { echo "FAIL: unexpected list output" >&2; exit 1; }
echo "PASS — Tier 1 fixture metadata and listing."

# Refuse before opening a session: without a built checkout every group spends
# its session-open backoff and then becomes an infrastructure exception.
# replbackend performs the detailed directory/lean-toolchain validation; this
# guard only checks set-and-nonempty, with ``:-`` required under set -u.
need_mathlib_root() {
    [ -n "${SMOLBENCH_MATHLIB_ROOT:-}" ] || {
        echo "FAIL: SMOLBENCH_MATHLIB_ROOT is not set; point it at a mathlib4 checkout built with elan/lake" >&2
        exit 1
    }
}

if [ "${1:-}" = "--replay" ]; then
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found; install it before replay" >&2
        exit 1
    }
    need_mathlib_root
    # The Tier-1 fixture is JSON-shape-only. Fail immediately rather than
    # spending session-open backoff on declarations absent from mathlib.
    [ -n "${SMOLBENCH_LEAN_DATA:-}" ] || {
        echo "FAIL: SMOLBENCH_LEAN_DATA is not set; replay needs a real corpus" >&2
        exit 1
    }
    .venv/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0
    echo "PASS — real Lean replay."
elif [ -n "${1:-}" ]; then
    echo "unknown argument: $1" >&2
    exit 2
fi
