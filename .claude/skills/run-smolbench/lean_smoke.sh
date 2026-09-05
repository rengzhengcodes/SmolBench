#!/usr/bin/env bash
# Smoke driver for the smolbench.deduction.lean harness (Lean 4 theorem-proving
# eval, folded into the main package from the old standalone lean/ project).
#
# Default run is credential-free and Lean-free: check the generation/analysis
# modules import without pulling in lean_interact, sync the .venv, then drive
# the `metadata` and `list` CLI subcommands against the tiny post-cutoff
# corpus fixture committed at tests/fixtures/lean_mini_postcutoff/ -- no
# download. `notebooks/deduction/run_study.py`'s `build_config` now refuses a
# pre-cutoff corpus (every roster checkpoint's cutoff postdates the old
# 2024-03-24 LeanDojo Benchmark 4 snapshot, so its theorems are not a valid
# held-out set), so this tier no longer bootstraps that retired Zenodo
# archive; see scripts/deduction/build_postcutoff_corpus.py for how a REAL
# post-cutoff corpus is built.
#
#   bash .claude/skills/run-smolbench/lean_smoke.sh            # Tier 0+1 (~seconds)
#   bash .claude/skills/run-smolbench/lean_smoke.sh --replay   # + one REPL ground-truth replay
#   bash .claude/skills/run-smolbench/lean_smoke.sh --e2e      # + FULL run-sweep: fake LLMs, REAL Lean
#
# --replay and --e2e additionally need elan on PATH, SMOLBENCH_MATHLIB_ROOT
# pointing at a mathlib4 checkout that has been BUILT with elan/lake, AND
# SMOLBENCH_LEAN_DATA pointing at a REAL corpus (the Tier-1 fixture above is
# JSON-shape-only -- its Mini.theoremA/B declarations do not exist in any real
# mathlib4 checkout and cannot replay against a live Lean session). The
# verifier drives leanprover-community/repl through the lean-interact package
# and reads that local checkout; there is no traced-corpus download from
# LeanDojo's S3 any more. All three tiers refuse to start without their
# required variable.
# The old cold/warm budgets were measured under the retired LeanDojo backend
# and have not been re-measured here.
#
# --e2e is the credential-free END-TO-END sweep check: it starts two local
# OpenAI-compatible stub LLMs (stub_llm.py — one returns the theorem's true
# ground-truth tail, one a bogus tactic), points the primeintellect and
# openrouter providers at them, and drives `run-sweep` on one theorem. Real
# Lean verification must yield success for the good stub and lean_error for
# the bad one; a second identical run must resume-skip both cells.
# Results/logs go to a mktemp dir — never the committed results tree.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."   # repo root

# uv-managed Python needs the system CA bundle for `uv sync`'s downloads.
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Tier 0: the generation/analysis side of smolbench.deduction.lean must import
# without needing lean_interact — only verify.py is allowed to need it. The
# assertion is on sys.modules, not on the import succeeding: lean_interact IS
# installed in this .venv, so a bare import would pass even if runner/cli had
# grown a hard dependency on the Lean backend.
.venv/bin/python -c "import smolbench.deduction.lean.runner, smolbench.deduction.lean.cli, sys; assert 'lean_interact' not in sys.modules, 'runner/cli pulled in lean_interact'" \
    || { echo "FAIL: smolbench.deduction.lean.{runner,cli} must import on .venv without lean_interact" >&2; exit 1; }
echo "PASS — Tier 0 (smolbench.deduction.lean imports cleanly without pulling in lean_interact)."

uv sync -q --all-extras

# Tier 1 demonstrates metadata/list against the tiny post-cutoff corpus
# fixture committed for exactly this purpose
# (tests/fixtures/lean_mini_postcutoff/, fictional Mini.theoremA/B
# declarations) -- no download, no credentials, no Lean toolchain touched.
# The override is scoped to each command below (`VAR=val cmd`, not `export`),
# so it never leaks into --replay/--e2e further down, which need a REAL
# corpus and must see any caller-supplied SMOLBENCH_LEAN_DATA untouched.
FIXTURE=tests/fixtures/lean_mini_postcutoff

metadata_out=$(SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" .venv/bin/python -m smolbench.deduction.lean.cli metadata)
echo "$metadata_out"
# Semantic check, not a substring of the dataset name: a real corpus built by
# build_postcutoff_corpus.py is named "SmolBench post-cutoff mathlib4
# (LeanDojo-v2 trace)", which does not contain "LeanDojo Benchmark 4" at all,
# so the assertion has to be on the postcutoff block itself.
SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" .venv/bin/python -c \
    "from smolbench.deduction.lean import corpus as c; assert c.is_postcutoff_corpus(), c.data_root()" \
    || { echo "FAIL: active corpus is not post-cutoff (see scripts/deduction/build_postcutoff_corpus.py)" >&2; exit 1; }

list_out=$(SMOLBENCH_LEAN_DATA="${SMOLBENCH_LEAN_DATA:-$FIXTURE}" .venv/bin/python -m smolbench.deduction.lean.cli list --kind random --split val --limit 5)
echo "$list_out"
grep -q "theorems with traced tactics in random/val" <<<"$list_out" || { echo "FAIL: unexpected list output" >&2; exit 1; }

echo "PASS — smolbench.deduction.lean Tier-1 smoke (metadata + list against a post-cutoff corpus)."

need_elan() {
    export PATH="$HOME/.elan/bin:$PATH"
    command -v elan >/dev/null || {
        echo "FAIL: elan not found. Install with:" >&2
        echo "  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none" >&2
        exit 1
    }
}

# The REPL backend runs inside a BUILT mathlib4 checkout named by
# SMOLBENCH_MATHLIB_ROOT. Refuse up front rather than starting a tier that
# cannot succeed: without it every group is reported as `exception`, slowly,
# after the session-open backoff has been spent on each one. Only "set and
# non-empty" is checked here — replbackend.mathlib_root does the real
# validation (directory exists, contains lean-toolchain) and its message is
# more specific than anything this script could produce. The `:-` is required:
# this script runs under `set -u`.
need_mathlib_root() {
    [ -n "${SMOLBENCH_MATHLIB_ROOT:-}" ] || {
        echo "FAIL: SMOLBENCH_MATHLIB_ROOT is not set. Lean verification drives" >&2
        echo "  leanprover-community/repl (via the lean-interact package) inside a" >&2
        echo "  mathlib4 checkout built with elan/lake. Point the variable at one:" >&2
        echo "    export SMOLBENCH_MATHLIB_ROOT=/path/to/mathlib4" >&2
        echo "  Or run the default (no-argument) Tier-0/1 smoke, which needs no Lean." >&2
        exit 1
    }
}

# --replay/--e2e need a REAL corpus, reachable by a live Lean session: the
# tiny fixture Tier 1 uses above is fictional (Mini.theoremA/B do not exist in
# any real mathlib4 checkout) and cannot replay. Refuse up front, for the same
# reason as need_mathlib_root: without one, every group would fail only after
# the session-open backoff has been spent on each one, rather than failing
# immediately and legibly. scripts/deduction/build_postcutoff_corpus.py builds
# the post-cutoff corpus this study's own driver (run_study.py's
# build_config) requires; --replay/--e2e themselves do not call that gate, so
# any real, Lean-elaborable corpus works here too.
need_real_corpus() {
    [ -n "${SMOLBENCH_LEAN_DATA:-}" ] || {
        echo "FAIL: SMOLBENCH_LEAN_DATA is not set. --replay/--e2e need a REAL corpus" >&2
        echo "  (the tiny Tier-1 fixture above is fictional and cannot replay). Build" >&2
        echo "  one with scripts/deduction/build_postcutoff_corpus.py and point the" >&2
        echo "  variable at its output, e.g.:" >&2
        echo "    export SMOLBENCH_LEAN_DATA=notebooks/deduction/data/leandojo_benchmark_4" >&2
        exit 1
    }
}

if [ "${1:-}" = "--replay" ]; then
    need_elan
    need_mathlib_root
    need_real_corpus
    .venv/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0
    echo "PASS — smolbench.deduction.lean replay smoke (REPL ground-truth replay succeeded)."
fi

if [ "${1:-}" = "--e2e" ]; then
    need_elan
    need_mathlib_root
    need_real_corpus
    SKILL=.claude/skills/run-smolbench
    WORK=$(mktemp -d)
    STUB_PID=""
    trap '[ -n "$STUB_PID" ] && kill "$STUB_PID" 2>/dev/null; rm -rf "$WORK"' EXIT

    # Stub servers pick their own ports and print them as one JSON line.
    .venv/bin/python "$SKILL/stub_llm.py" "$WORK/reqlog.jsonl" > "$WORK/ports.json" &
    STUB_PID=$!
    for _ in $(seq 50); do [ -s "$WORK/ports.json" ] && break; sleep 0.1; done
    [ -s "$WORK/ports.json" ] || { echo "FAIL: stub_llm.py never printed its ports" >&2; exit 1; }
    PI_PORT=$(.venv/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["pi"])' "$WORK/ports.json")
    OR_PORT=$(.venv/bin/python -c 'import json,sys; print(json.load(open(sys.argv[1]))["or"])' "$WORK/ports.json")

    # Lagrange.eval_nodal_at_node: 2 traced tactics, replays in ~7 s warm.
    # NOTE: this is a long-standing mathlib4 theorem, not a post-cutoff one --
    # a corpus built by build_postcutoff_corpus.py keeps only declarations
    # that provably postdate the roster's cutoff, so it will NOT contain this
    # theorem. SMOLBENCH_LEAN_DATA for --e2e must point at a corpus where it
    # is actually present (e.g. a pre-cutoff LeanDojo Benchmark 4 export, or
    # any other real trace that includes it); that is independent of, and in
    # tension with, this study's post-cutoff requirement for run_study.py
    # itself, which does not apply to this stub-LLM smoke path.
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
        .venv/bin/python -m smolbench.deduction.lean.cli run-sweep --config "$WORK/sweep.yaml"
    }
    run_sweep

    .venv/bin/python - "$WORK/results/runs/e2e_stub_smoke/all_rows.jsonl" <<'PY'
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
