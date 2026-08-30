---
name: run-smolbench
description: Build, launch, and drive SmolBench — run the offline smolbench eval smoke driver, pytest suite, and induction demos, and run/smoke/test the smolbench.deduction.lean theorem-proving harness (notebooks/deduction experiment). Use when asked to run, start, test, smoke, or drive smolbench or the lean eval, or to verify a change works end-to-end.
---

# Run SmolBench

One package, two runnable surfaces, no GUI/server. **smolbench** (repo root):
an LLM-eval library — "running" it means driving the real quiz → provider →
evaluate → grade → YAML pipeline against a local OpenAI-compatible stub, zero
credentials. **smolbench.deduction.lean** (package `smolbench/deduction/lean/`, experiment
`notebooks/deduction/`): a Lean 4 theorem-proving eval whose VERIFICATION path
needs `lean_dojo`, elan, and a traced-repo cache; generation/analysis need
none of those. Both run on the same `.venv`. All paths below are relative
to the repo root; all commands were verified in a headless Linux container.

## Prerequisites

```bash
uv sync --all-extras   # single .venv (Python 3.12, pinned by .python-version), every extra
```

## Run (agent path)

```bash
# End-to-end smoke: generation -> provider dispatch -> stub round trip -> grading -> YAML IO.
# `timeout` is mandatory: the provider retries transient failures FOREVER (60s backoff).
timeout 120 .venv/bin/python .claude/skills/run-smolbench/driver.py   # PASS + exit 0

.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials

.venv/bin/python -m smolbench.induction.periodic              # quiz-generation demo
.venv/bin/python -m smolbench.induction.chromatic | tail -25  # prints ~120 prompt blocks

bash .claude/skills/run-smolbench/lean_smoke.sh           # lean Tier 0+1 (~seconds warm)
bash .claude/skills/run-smolbench/lean_smoke.sh --replay  # + one real Dojo replay (see below)
bash .claude/skills/run-smolbench/lean_smoke.sh --e2e     # + FULL run-sweep: fake LLMs, REAL Lean (~1 min warm)
```

## Direct invocation (drive internals without the driver)

Most PRs touch `smolbench/evals/` or `smolbench/induction/`; exercise them
directly from the repo root — no credentials, real production code path:

```python
# .venv/bin/python - <<'EOF' ... EOF
import os, string, sys, threading
sys.path.insert(0, ".")  # repo root: makes tests.conftest importable
from tests.conftest import StubServer, StubTokenizer, chat_completion
from smolbench.evals import provider
from smolbench.induction.periodic import (
    PeriodicConfig, Prompter, get_periodic_numeric_quiz, numeric_count_query_gen)

template = string.Template(
    "Rules:\n$positive_info\nHow many of positions 1..$seq_len include '$label'? Integer only.")
# `tokenizer` is keyword-only and has NO default: the noise arm pads to an
# exact token count, so a quiz cannot be built without one.
quiz, _, _ = get_periodic_numeric_quiz(
    PeriodicConfig(n=2, labels=["fizz", "buzz"], seed=7),
    Prompter(template, {}, numeric_count_query_gen),
    tokenizer=StubTokenizer())

server = StubServer()
threading.Thread(target=server.serve_forever, daemon=True).start()
os.environ |= {"INFERENCE_PROVIDER": "openrouter",
               "OPENROUTER_BASE_URL": server.base_url,
               "OPENROUTER_API_KEY": "dummy"}
server.default_response = chat_completion("2")
marks = provider.evaluate(quiz, "any-model", seed=7, max_parallel=1, show_progress=False)
print(f"{marks.correct} correct / {marks.incorrect} incorrect / {marks.invalid} invalid of {len(quiz)}")
server.shutdown()
# -> 1 correct / 1 incorrect / 0 invalid of 2
```

## Run: smolbench.deduction.lean (theorem-proving eval)

`lean_smoke.sh` handles the venv sync and a one-time 64 MB benchmark
bootstrap (Zenodo record 10929138 → `notebooks/deduction/data/leandojo_benchmark_4/`,
gitignored). Manual driving from the repo root with
`export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`:

```bash
# No Lean/Dojo needed:
.venv/bin/python -m smolbench.deduction.lean.cli metadata
.venv/bin/python -m smolbench.deduction.lean.cli list --kind random --split test --limit 5
.venv/bin/python -m smolbench.deduction.lean.cli analyze <run_dir>/all_rows.jsonl   # + report/show/compare
# prompt-stats also runs here but needs the replay_passing_*.jsonl sidecar
# that only `filter` (~70 min) produces.

# Verification path (needs elan + a traced-repo cache; not just an install):
.venv/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0   # needs elan; see Gotchas
.venv/bin/python -m smolbench.deduction.lean.cli run-sweep --config <sweep.yaml>
```

The canonical sweep driver is `notebooks/deduction/lean_eval.ipynb` (kernel:
`.venv`) — config dicts live in its cells; `run-sweep` is the headless
escape hatch for the same config schema.

**Credential-free END-TO-END sweep verification (fake LLM, REAL Lean):**
`lean_smoke.sh --e2e` is the committed harness — it starts two local
OpenAI-compatible stubs (`stub_llm.py` beside this file: one answers with
the theorem's ground-truth tail in a ```` ```lean ```` fence, one with a
bogus tactic), points the `primeintellect` + `openrouter` providers at them
via `*_BASE_URL`/`*_API_KEY` env, and drives `run-sweep` on
`Lagrange.eval_nodal_at_node` (2 tactics, ~7 s warm replay). It asserts:
sanity gate passes, real Lean returns `success` for the true tail and
`lean_error` for the bogus one, rows AND wire requests carry `seed`,
per-model provider dispatch holds, and an identical rerun resume-skips both
cells. Results/reqlog go to a mktemp dir via `SMOLBENCH_LEAN_RESULTS` —
keep stub runs out of the committed results tree if you adapt it. ~30 s
warm; like `--replay` it needs elan (first Dojo call pulls the ~2.4 GB
traced corpus from S3 to `~/.cache/lean_dojo/`, creds-free; cold ~2–4 min,
warm ~10 s).
Real-model `run-cell`/`run-sweep` need a provider key
(`PRIME_INTELLECT_API_KEY` or `OPENROUTER_API_KEY`), cost money, and are
user-opt-in only; `filter` (~70 min/split) produces the
`replay_passing_*.jsonl` sidecar that non-explicit sweep configs need —
none is checked in yet (`--e2e` sidesteps it with `theorems.source:
explicit`). Sweep results land under `notebooks/deduction/results/runs/`.

## Live AWS surfaces — do NOT run without explicit user opt-in

`scripts/smoke/bedrock_smoke.py`, `scripts/smoke/ec2_lifecycle_smoke.py <step>`, and the
`notebooks/{induction,deduction}/` notebooks provision/bill real AWS infra
(Bedrock, EC2 spot vLLM, SageMaker) and need `keys.env` credentials (never
print those files). Runbook: `scripts/README.md`'s "Live smoke runbook";
last live-verified 2026-07-02. Everything in this skill runs without them.

## Gotchas

- Always name the interpreter explicitly: `.venv/bin/python`, never a system
  python. `run-sweep`, `run-cell`, `replay`, and `filter` additionally need
  elan and a traced-repo cache (see below); every other subcommand needs
  neither.
- `uv sync` prunes packages not in the lockfile: it uninstalls the ad-hoc
  `aws-bedrock-token-generator` that `scripts/smoke/bedrock_smoke.py` needs
  (observed). Restore with `uv pip install aws-bedrock-token-generator`.
  Plain `uv run` / `uv run --no-sync` likewise strips extras — resync with
  `uv sync --all-extras`; use `uv run --no-project` for ephemeral scripts.
- The shared `ChatClient` retries 429/5xx/connection errors **forever**
  (60 s backoff) under openrouter — always wrap unattended runs in `timeout`.
  Lean sweeps are exempt: the runner passes `max_retries` (config key,
  default 4) so a wedged endpoint can't hang an open Dojo session.
- `StubServer.next_response` pops FIFO: queued-response↔question mapping is
  only deterministic with `max_parallel=1`; for parallel fan-out set a
  uniform `server.default_response` instead.
- Direct `provider.query()`/`complete()` needs explicit `context_length=`
  (default 0 fails any response that reports `usage.total_tokens`);
  `evaluate()` resolves it internally via a GET the stub answers with 100000.
- Repo rule: every request carries `seed` — never drop it to dodge an error.
  Lean sweeps derive per-replicate seeds as `config["seed"] + replicate_idx`.
- `notebooks/*/results*/` are huge generated trees (~80 M lines of YAML for
  the induction experiments; JSONL with full raw responses for lean) — never
  grep/glob them blindly.
- `GITHUB_ACCESS_TOKEN` is optional for `replay` (corpus comes from S3
  anonymously — verified); heavier LeanDojo use may still hit anonymous
  GitHub rate limits.
- elan is enough for Dojo: install with
  `curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none`
  (Dojo fetches its own pinned toolchain).

## Troubleshooting

- `Python ... is not the project interpreter` from the driver → you used a
  system python; rerun with `.venv/bin/python`.
- `cannot import tests.conftest` (driver exit 2) → run from a synced repo:
  `uv sync --all-extras` at the root.
- `ImportError: smolbench.deduction.lean.verify requires lean_dojo` → run
  `uv sync --all-extras`.
- `elan not found` from `lean_smoke.sh --replay` → install elan (line above)
  or run the default Tier-0/1 smoke instead.
