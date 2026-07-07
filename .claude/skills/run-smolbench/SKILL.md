---
name: run-smolbench
description: Build, launch, and drive SmolBench — run the offline smolbench eval smoke driver, pytest suite, and induction demos, and run/smoke/test the smolbench.lean theorem-proving harness (notebooks/lean experiment). Use when asked to run, start, test, smoke, or drive smolbench or the lean eval, or to verify a change works end-to-end.
---

# Run SmolBench

One package, two runnable surfaces, no GUI/server. **smolbench** (repo root):
an LLM-eval library — "running" it means driving the real quiz → provider →
evaluate → grade → YAML pipeline against a local OpenAI-compatible stub, zero
credentials. **smolbench.lean** (package `smolbench/lean/`, experiment
`notebooks/lean/`): a Lean 4 theorem-proving eval whose VERIFICATION path
(lean_dojo) needs a dedicated Python 3.12 venv — generation/analysis run on
the main venv. All paths below are relative to the repo root; all commands
were verified in a headless Linux container.

## Prerequisites

```bash
uv sync --all-extras   # root .venv (Python 3.14) — the lean-dojo marker skips it here

# Dedicated 3.12 venv for the Lean verification path (lean-dojo pins <3.13):
UV_PROJECT_ENVIRONMENT=.venv-lean uv sync --python 3.12 --extra lean --extra notebook --extra dev
```

## Run (agent path)

```bash
# End-to-end smoke: generation -> provider dispatch -> stub round trip -> grading -> YAML IO.
# `timeout` is mandatory: the provider retries transient failures FOREVER (60s backoff).
timeout 120 .venv/bin/python .claude/skills/run-smolbench/driver.py   # PASS + exit 0

.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials
.venv-lean/bin/python -m pytest tests/ -q     # same suite on 3.12 (verify-guard import-OK branch)

.venv/bin/python -m smolbench.induction.periodic              # quiz-generation demo
.venv/bin/python -m smolbench.induction.chromatic | tail -25  # prints ~120 prompt blocks

bash .claude/skills/run-smolbench/lean_smoke.sh           # lean Tier 0+1 (~seconds warm)
bash .claude/skills/run-smolbench/lean_smoke.sh --replay  # + one real Dojo replay (see below)
```

## Direct invocation (drive internals without the driver)

Most PRs touch `smolbench/evals/` or `smolbench/induction/`; exercise them
directly from the repo root — no credentials, real production code path:

```python
# .venv/bin/python - <<'EOF' ... EOF
import os, string, sys, threading
sys.path.insert(0, ".")  # repo root: makes tests.conftest importable
from tests.conftest import StubServer, chat_completion
from smolbench.evals import provider
from smolbench.induction.periodic import (
    PeriodicConfig, Prompter, get_periodic_numeric_quiz, numeric_count_query_gen)

template = string.Template(
    "Rules:\n$positive_info\nHow many of positions 1..$seq_len include '$label'? Integer only.")
quiz, _, _ = get_periodic_numeric_quiz(
    PeriodicConfig(n=2, labels=["fizz", "buzz"], seed=7),
    Prompter(template, {}, numeric_count_query_gen))

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

## Run: smolbench.lean (theorem-proving eval)

`lean_smoke.sh` handles both venv syncs and a one-time 64 MB benchmark
bootstrap (Zenodo record 10929138 → `notebooks/lean/data/leandojo_benchmark_4/`,
gitignored). Manual driving from the repo root with
`export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`:

```bash
# Anywhere (main .venv works — no Lean/Dojo needed):
.venv/bin/python -m smolbench.lean.cli metadata
.venv/bin/python -m smolbench.lean.cli list --kind random --split test --limit 5
.venv/bin/python -m smolbench.lean.cli analyze <run_dir>/all_rows.jsonl   # + report/show/compare
# prompt-stats also runs here but needs the replay_passing_*.jsonl sidecar
# that only `filter` (~70 min, .venv-lean) produces.

# Verification path (needs .venv-lean; importing smolbench.lean.verify on 3.14
# raises an actionable ImportError):
.venv-lean/bin/python -m smolbench.lean.cli replay -n 1 --seed 0   # needs elan; see Gotchas
.venv-lean/bin/python -m smolbench.lean.cli run-sweep --config <sweep.yaml>
```

The canonical sweep driver is `notebooks/lean/lean_eval.ipynb` (kernel:
`.venv-lean`) — config dicts live in its cells; `run-sweep` is the headless
escape hatch for the same config schema. Verified tiers in this container:
`metadata`/`list` (credential-free, no Lean) and `replay`/Dojo
(needs elan on PATH; first call pulls the ~2.4 GB traced corpus from S3 to
`~/.cache/lean_dojo/` — creds-free, ~1 min; cold replay ~2–4 min, warm ~10 s).
NOT verified here: `run-cell`/`run-sweep` (need a provider key —
`PRIME_INTELLECT_API_KEY` or `OPENROUTER_API_KEY` — and cost money) and
`filter` (~70 min/split). Figure scripts live in `notebooks/lean/figures/`
and read results under `notebooks/lean/results/runs/` (committed once
sweeps are run; currently empty — scripts warn and skip missing runs).
Sweep configs need the `replay_passing_*.jsonl` sidecar that only `filter`
produces; none is checked in yet.

## Live AWS surfaces — do NOT run without explicit user opt-in

`scripts/bedrock_smoke.py`, `scripts/ec2_lifecycle_smoke.py <step>`, and the
`notebooks/{periodic,chromatic}/` notebooks provision/bill real AWS infra
(Bedrock, EC2 spot vLLM, SageMaker) and need `keys.env` credentials (never
print those files). Runbook: `REFACTOR.md` §2.8 "Live-verification runbook";
last live-verified 2026-07-02. Everything in this skill runs without them.

## Gotchas

- System `python3` is 3.12 and the root `.venv` is 3.14 → always name the
  interpreter explicitly: `.venv/bin/python` for everything except the Lean
  verification path, which needs `.venv-lean/bin/python` (lean-dojo pins
  Python <3.13; the `lean` extra's environment marker skips it on 3.14).
  `run-sweep`, `run-cell`, `replay`, and `filter` need `.venv-lean`; every
  other subcommand runs on either venv.
- `uv sync` prunes packages not in the lockfile: it uninstalls the ad-hoc
  `aws-bedrock-token-generator` that `scripts/bedrock_smoke.py` needs
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
  Lean sweeps derive per-rollout seeds as `config["seed"] + rollout_idx`.
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

- `RuntimeError: Python 3.12.x is too old` from the driver → you used system
  `python3`; rerun with `.venv/bin/python`.
- `cannot import tests.conftest` (driver exit 2) → run from a synced repo:
  `uv sync --all-extras` at the root.
- `ImportError: smolbench.lean.verify requires lean_dojo` → you ran a
  Dojo-touching subcommand on the 3.14 venv; rerun with
  `.venv-lean/bin/python` (build it with the UV_PROJECT_ENVIRONMENT one-liner
  under Prerequisites).
- `elan not found` from `lean_smoke.sh --replay` → install elan (line above)
  or run the default Tier-0/1 smoke instead.
