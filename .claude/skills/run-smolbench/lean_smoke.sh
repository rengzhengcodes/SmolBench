#!/usr/bin/env bash
# Smoke driver for the lean/ leaneval harness (LeanDojo theorem-proving eval).
#
# Default run is credential-free and Lean-free: sync the lean/.venv, bootstrap
# the LeanDojo Benchmark 4 JSON from Zenodo (64 MB, one-time), then drive the
# `metadata` and `list` CLI subcommands against real benchmark data.
#
#   bash .claude/skills/run-smolbench/lean_smoke.sh            # Tier 1 (~seconds after bootstrap)
#   bash .claude/skills/run-smolbench/lean_smoke.sh --replay   # + one Dojo ground-truth replay
#
# --replay additionally needs elan on PATH and, on first use, pulls the
# ~2.4 GB traced corpus from LeanDojo's S3 cache into ~/.cache/lean_dojo/
# (creds-free; verified working WITHOUT GITHUB_ACCESS_TOKEN for this path).
# Budget ~5 min cold / ~3 min warm.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../../lean"

# uv-managed Python needs the system CA bundle (see lean/README.md).
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

uv sync -q

DATA=data/leandojo_benchmark_4
if [ ! -f "$DATA/metadata.json" ]; then
    echo "Bootstrapping LeanDojo Benchmark 4 (64 MB) from Zenodo record 10929138..."
    mkdir -p data
    curl -sSL -o data/leandojo_benchmark_4.tar.gz \
        "https://zenodo.org/api/records/10929138/files/leandojo_benchmark_4.tar.gz/content"
    tar xzf data/leandojo_benchmark_4.tar.gz -C data
    rm data/leandojo_benchmark_4.tar.gz
fi

metadata_out=$(uv run python -m leaneval.cli metadata)
echo "$metadata_out"
grep -q "LeanDojo Benchmark 4" <<<"$metadata_out" || { echo "FAIL: unexpected metadata" >&2; exit 1; }

list_out=$(uv run python -m leaneval.cli list --kind random --split test --limit 5)
echo "$list_out"
grep -q "theorems with traced tactics in random/test" <<<"$list_out" || { echo "FAIL: unexpected list output" >&2; exit 1; }

echo "PASS — leaneval Tier-1 smoke (metadata + list against real benchmark data)."

if [ "${1:-}" = "--replay" ]; then
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found. Install with:" >&2
        echo "  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none" >&2
        exit 1
    }
    uv run python -m leaneval.cli replay -n 1 --seed 0
    echo "PASS — leaneval replay smoke (Dojo ground-truth replay succeeded)."
fi
