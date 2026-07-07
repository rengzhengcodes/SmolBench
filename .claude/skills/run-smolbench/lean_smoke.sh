#!/usr/bin/env bash
# Smoke driver for the smolbench.lean harness (LeanDojo theorem-proving eval,
# folded into the main package from the old standalone lean/ project).
#
# Default run is credential-free and Lean-free: check the generation/analysis
# modules import on the MAIN 3.14 venv, sync the dedicated 3.12 verification
# venv (.venv-lean; lean-dojo pins Python <3.13), bootstrap the LeanDojo
# Benchmark 4 JSON from Zenodo (64 MB, one-time), then drive the `metadata`
# and `list` CLI subcommands against real benchmark data.
#
#   bash .claude/skills/run-smolbench/lean_smoke.sh            # Tier 0+1 (~seconds after bootstrap)
#   bash .claude/skills/run-smolbench/lean_smoke.sh --replay   # + one Dojo ground-truth replay
#
# --replay additionally needs elan on PATH and, on first use, pulls the
# ~2.4 GB traced corpus from LeanDojo's S3 cache into ~/.cache/lean_dojo/
# (creds-free; verified working WITHOUT GITHUB_ACCESS_TOKEN for this path).
# Budget ~5 min cold / ~3 min warm.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # repo root

# uv-managed Python needs the system CA bundle (see notebooks/lean/README.md).
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Tier 0: the generation/analysis side of smolbench.lean must import on the
# main venv (3.14, no lean_dojo) — only verify.py is allowed to need 3.12.
.venv/bin/python -c "import smolbench.lean.runner, smolbench.lean.cli" \
    || { echo "FAIL: smolbench.lean.{runner,cli} must import on the main .venv" >&2; exit 1; }
echo "PASS — Tier 0 (smolbench.lean imports cleanly on the main 3.14 venv)."

# Dedicated 3.12 venv for the verification path. UV_PROJECT_ENVIRONMENT keeps
# the root .venv untouched; the environment marker on lean-dojo makes this
# same sync command valid for both interpreters.
UV_PROJECT_ENVIRONMENT=.venv-lean uv sync -q --python 3.12 --extra lean --extra notebook --extra dev

DATA=notebooks/lean/data/leandojo_benchmark_4
if [ ! -f "$DATA/metadata.json" ]; then
    echo "Bootstrapping LeanDojo Benchmark 4 (64 MB) from Zenodo record 10929138..."
    mkdir -p notebooks/lean/data
    curl -sSL -o notebooks/lean/data/leandojo_benchmark_4.tar.gz \
        "https://zenodo.org/api/records/10929138/files/leandojo_benchmark_4.tar.gz/content"
    tar xzf notebooks/lean/data/leandojo_benchmark_4.tar.gz -C notebooks/lean/data
    rm notebooks/lean/data/leandojo_benchmark_4.tar.gz
fi

metadata_out=$(.venv-lean/bin/python -m smolbench.lean.cli metadata)
echo "$metadata_out"
grep -q "LeanDojo Benchmark 4" <<<"$metadata_out" || { echo "FAIL: unexpected metadata" >&2; exit 1; }

list_out=$(.venv-lean/bin/python -m smolbench.lean.cli list --kind random --split test --limit 5)
echo "$list_out"
grep -q "theorems with traced tactics in random/test" <<<"$list_out" || { echo "FAIL: unexpected list output" >&2; exit 1; }

echo "PASS — smolbench.lean Tier-1 smoke (metadata + list against real benchmark data)."

if [ "${1:-}" = "--replay" ]; then
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found. Install with:" >&2
        echo "  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none" >&2
        exit 1
    }
    .venv-lean/bin/python -m smolbench.lean.cli replay -n 1 --seed 0
    echo "PASS — smolbench.lean replay smoke (Dojo ground-truth replay succeeded)."
fi
