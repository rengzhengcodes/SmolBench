#!/usr/bin/env bash
# Smoke driver for the Lean benchmark. The default is credential-free and
# Lean-free: import generation/analysis, sync the environment, then run
# metadata/list against the committed post-cutoff fixture. It does not
# download a corpus. ``--replay`` additionally drives one theorem through a
# configured real Lean checkout. ``--e2e`` runs two stub LLMs through a full
# sweep against the post-cutoff fixture and its local Lean project.
#
# The old 2024-03-24 corpus is invalid for the roster because every model
# cutoff postdates it; build a real post-cutoff corpus with
# scripts/deduction/build_postcutoff_corpus.py.
#
#   bash .claude/skills/run-smolbench/lean_smoke.sh
#   bash .claude/skills/run-smolbench/lean_smoke.sh --replay
#   bash .claude/skills/run-smolbench/lean_smoke.sh --e2e
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
elif [ "${1:-}" = "--e2e" ]; then
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found; install it before --e2e" >&2
        exit 1
    }
    SKILL=.claude/skills/run-smolbench
    WORK=$(mktemp -d)
    STUB_PID=""
    trap '[ -n "$STUB_PID" ] && kill "$STUB_PID" 2>/dev/null; rm -rf "$WORK"' EXIT

    # The committed corpus fixture is intentionally source-free; materialize
    # its theorem in a temporary Lean project so this tier exercises real Lean.
    mkdir -p "$WORK/lean_project/Mini" "$WORK/corpus/random"
    cp tests/fixtures/lean_repl_project/{lakefile.toml,lean-toolchain} "$WORK/lean_project/"
    cp "$FIXTURE/metadata.json" "$WORK/corpus/metadata.json"
    cat > "$WORK/lean_project/Mini/A.lean" <<'LEAN'
axiom P Q R : Nat → Prop
@[simp] axiom q_iff_r (n : Nat) : Q n = R n

namespace Mini
axiom premiseA {n : Nat} (h : P n) (m : Nat) : R n
def premiseB (n : Nat) : Nat := n
end Mini

theorem theoremA {n : Nat} (hn : n > 0) : P n → Q n := by
  intro h
  simp
  exact Mini.premiseA h (Mini.premiseB n)
LEAN
    .venv/bin/python - "$FIXTURE/random/val.json" "$WORK/corpus/random/val.json" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
row = next(row for row in rows if row["full_name"] == "Mini.theoremA")
row["start"] = [9, 1]
open(sys.argv[2], "w").write(json.dumps([row]))
PY

    .venv/bin/python "$SKILL/stub_llm.py" "$WORK/reqlog.jsonl" > "$WORK/ports.json" &
    STUB_PID=$!
    for _ in $(seq 50); do [ -s "$WORK/ports.json" ] && break; sleep 0.1; done
    [ -s "$WORK/ports.json" ] || {
        echo "FAIL: stub_llm.py never printed its ports" >&2
        exit 1
    }
    PI_PORT=$(.venv/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["pi"])' "$WORK/ports.json")
    OR_PORT=$(.venv/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["or"])' "$WORK/ports.json")

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
  - provider: ec2
    model: stub-good-model
    display_name: stub-good
  - provider: ec2
    model: stub-bad-model
    display_name: stub-bad
theorems:
  source: explicit
  kind: random
  split: val
  full_names:
    - Mini.theoremA
k:
  strategy: last
rungs:
  - "stepk:1"
YAML

    run_sweep() {
        SMOLBENCH_LEAN_DATA="$WORK/corpus" \
        SMOLBENCH_MATHLIB_ROOT="$WORK/lean_project" \
        SMOLBENCH_LEAN_RESULTS="$WORK/results" \
        EC2_INFERENCE_BASE_URL="http://127.0.0.1:$PI_PORT/v1" EC2_VLLM_API_KEY=dummy \
        .venv/bin/python -m smolbench.deduction.lean.cli run-sweep --config "$WORK/sweep.yaml"
    }
    run_sweep

    .venv/bin/python - "$WORK/results/runs/e2e_stub_smoke/all_rows.jsonl" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])]
sanity = [row for row in rows if row.get("kind") == "sanity"]
cells = {row["model"]: row for row in rows if row.get("kind") == "cell"}
assert sanity and all(row["verdict"] == "success" for row in sanity), sanity
assert cells["stub-good"]["verdict"] == "success", cells["stub-good"]
assert cells["stub-bad"]["verdict"] == "lean_error", cells["stub-bad"]
assert "nonexistent_lemma_xyz42" in (cells["stub-bad"]["lean_error"] or "")
assert all(row["seed"] == 4242 for row in cells.values())
reqs = [json.loads(line) for line in open(sys.argv[1].replace(
    "results/runs/e2e_stub_smoke/all_rows.jsonl", "reqlog.jsonl"))]
gens = [row for row in reqs if row["path"].endswith("/chat/completions")]
assert {row["body"]["model"] for row in gens} == {"stub-good-model", "stub-bad-model"}
assert all(row["body"].get("seed") == 4242 for row in gens)
PY

    resume_out=$(run_sweep)
    grep -q "(2 skipped)" <<<"$resume_out" || {
        echo "FAIL: resume rerun did not skip both cells:" >&2
        echo "$resume_out" >&2
        exit 1
    }
    echo "PASS — end-to-end stub sweep (post-cutoff fixture, real Lean, resume skips)."
elif [ -n "${1:-}" ]; then
    echo "unknown argument: $1" >&2
    exit 2
fi
