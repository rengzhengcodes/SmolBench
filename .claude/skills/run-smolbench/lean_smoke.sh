#!/usr/bin/env bash
# Smoke driver for the smolbench.deduction.lean harness (LeanDojo theorem-proving eval,
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
#   bash .claude/skills/run-smolbench/lean_smoke.sh --e2e      # + FULL run-sweep: fake LLMs, REAL Lean
#
# --replay and --e2e additionally need elan on PATH and, on first use, pull
# the ~2.4 GB traced corpus from LeanDojo's S3 cache into ~/.cache/lean_dojo/
# (creds-free; verified working WITHOUT GITHUB_ACCESS_TOKEN for this path).
# Budget ~5 min cold / ~3 min warm (--replay); ~1 min warm (--e2e).
#
# --e2e is the credential-free END-TO-END sweep check: it starts two local
# OpenAI-compatible stub LLMs (stub_llm.py — one returns the theorem's true
# ground-truth tail, one a bogus tactic), points the primeintellect and
# openrouter providers at them, and drives `run-sweep` on one warm-cached
# theorem. Real Dojo verification must yield success for the good stub and
# lean_error for the bad one; a second identical run must resume-skip both
# cells. Results/logs go to a mktemp dir — never the committed results tree.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # repo root

# uv-managed Python needs the system CA bundle (see notebooks/deduction/README.md).
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Tier 0: the generation/analysis side of smolbench.deduction.lean must import on the
# main venv (3.14, no lean_dojo) — only verify.py is allowed to need 3.12.
.venv/bin/python -c "import smolbench.deduction.lean.runner, smolbench.deduction.lean.cli" \
    || { echo "FAIL: smolbench.deduction.lean.{runner,cli} must import on the main .venv" >&2; exit 1; }
echo "PASS — Tier 0 (smolbench.deduction.lean imports cleanly on the main 3.14 venv)."

# Dedicated 3.12 venv for the verification path. UV_PROJECT_ENVIRONMENT keeps
# the root .venv untouched; the environment marker on lean-dojo makes this
# same sync command valid for both interpreters.
UV_PROJECT_ENVIRONMENT=.venv-lean uv sync -q --python 3.12 --extra lean --extra notebook --extra dev

DATA=notebooks/deduction/data/leandojo_benchmark_4
if [ ! -f "$DATA/metadata.json" ]; then
    echo "Bootstrapping LeanDojo Benchmark 4 (64 MB) from Zenodo record 10929138..."
    mkdir -p notebooks/deduction/data
    curl -sSL -o notebooks/deduction/data/leandojo_benchmark_4.tar.gz \
        "https://zenodo.org/api/records/10929138/files/leandojo_benchmark_4.tar.gz/content"
    tar xzf notebooks/deduction/data/leandojo_benchmark_4.tar.gz -C notebooks/deduction/data
    rm notebooks/deduction/data/leandojo_benchmark_4.tar.gz
fi

metadata_out=$(.venv-lean/bin/python -m smolbench.deduction.lean.cli metadata)
echo "$metadata_out"
grep -q "LeanDojo Benchmark 4" <<<"$metadata_out" || { echo "FAIL: unexpected metadata" >&2; exit 1; }

list_out=$(.venv-lean/bin/python -m smolbench.deduction.lean.cli list --kind random --split test --limit 5)
echo "$list_out"
grep -q "theorems with traced tactics in random/test" <<<"$list_out" || { echo "FAIL: unexpected list output" >&2; exit 1; }

echo "PASS — smolbench.deduction.lean Tier-1 smoke (metadata + list against real benchmark data)."

need_elan() {
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found. Install with:" >&2
        echo "  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none" >&2
        exit 1
    }
}

if [ "${1:-}" = "--replay" ]; then
    need_elan
    .venv-lean/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0
    echo "PASS — smolbench.deduction.lean replay smoke (Dojo ground-truth replay succeeded)."
fi

if [ "${1:-}" = "--e2e" ]; then
    need_elan
    SKILL=.claude/skills/run-smolbench
    WORK=$(mktemp -d)
    STUB_PID=""
    trap '[ -n "$STUB_PID" ] && kill "$STUB_PID" 2>/dev/null; rm -rf "$WORK"' EXIT

    # Stub servers pick their own ports and print them as one JSON line.
    .venv-lean/bin/python "$SKILL/stub_llm.py" "$WORK/reqlog.jsonl" > "$WORK/ports.json" &
    STUB_PID=$!
    for _ in $(seq 50); do [ -s "$WORK/ports.json" ] && break; sleep 0.1; done
    [ -s "$WORK/ports.json" ] || { echo "FAIL: stub_llm.py never printed its ports" >&2; exit 1; }
    PI_PORT=$(.venv-lean/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["pi"])' "$WORK/ports.json")
    OR_PORT=$(.venv-lean/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["or"])' "$WORK/ports.json")

    # Lagrange.eval_nodal_at_node: 2 traced tactics, replays in ~7 s warm.
    cat > "$WORK/sweep.yaml" <<'YAML'
run_name: e2e_stub_smoke
seed: 4242
n_replicates: 1
temperature: 0.7
max_tokens: 512
request_timeout: 30
max_retries: 2
dojo_timeout: 300
concurrent_gen: false
skip_trivial: false
theorem_workers: 1
models:
  - provider: primeintellect     # stub A -> the true ground-truth tail
    model: stub-good-model
    display_name: stub-good
  - provider: openrouter         # stub B -> a bogus tactic
    model: stub-bad-model
    display_name: stub-bad
theorems:
  source: explicit
  kind: random
  split: val
  full_names:
    - Lagrange.eval_nodal_at_node
k:
  strategy: last
rungs:
  - "stepk:1"
YAML

    run_sweep() {
        SMOLBENCH_LEAN_RESULTS="$WORK/results" \
        PRIME_INTELLECT_BASE_URL="http://127.0.0.1:$PI_PORT/v1" PRIME_INTELLECT_API_KEY=dummy \
        OPENROUTER_BASE_URL="http://127.0.0.1:$OR_PORT/v1" OPENROUTER_API_KEY=dummy \
        .venv-lean/bin/python -m smolbench.deduction.lean.cli run-sweep --config "$WORK/sweep.yaml"
    }
    run_sweep

    .venv-lean/bin/python - "$WORK/results/runs/e2e_stub_smoke/all_rows.jsonl" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
sanity = [r for r in rows if r.get("kind") == "sanity"]
cells = {r["model"]: r for r in rows if r.get("kind") == "cell"}
assert sanity and all(r["verdict"] == "success" for r in sanity), sanity
assert cells["stub-good"]["verdict"] == "success", cells["stub-good"]
assert cells["stub-bad"]["verdict"] == "lean_error", cells["stub-bad"]
assert "nonexistent_lemma_xyz42" in (cells["stub-bad"]["lean_error"] or ""), cells["stub-bad"]
assert all(r["seed"] == 4242 for r in cells.values()), "seed not threaded into rows"
reqs = [json.loads(l) for l in open(sys.argv[1].replace("results/runs/e2e_stub_smoke/all_rows.jsonl", "reqlog.jsonl"))]
gens = [r for r in reqs if r["path"].endswith("/chat/completions")]
assert {r["body"]["model"] for r in gens} == {"stub-good-model", "stub-bad-model"}, "per-model dispatch broken"
assert all(r["body"].get("seed") == 4242 for r in gens), "requests missing seed"
print("assertions OK: sanity=success, stub-good=success, stub-bad=lean_error, "
      "seed=4242 in rows AND wire requests, per-model provider dispatch")
PY

    resume_out=$(run_sweep)
    grep -q "(2 skipped)" <<<"$resume_out" \
        || { echo "FAIL: resume rerun did not skip both cells:" >&2; echo "$resume_out" >&2; exit 1; }
    echo "PASS — smolbench.deduction.lean END-TO-END stub sweep (fake LLMs, real Lean: good=success, bad=lean_error, resume skips)."
fi
