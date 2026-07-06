---
name: run-smolbench
description: Build, launch, and drive SmolBench — run the offline smolbench eval smoke driver, pytest suite, and induction demos, and run/smoke/test the lean/ leaneval theorem-proving harness. Use when asked to run, start, test, smoke, or drive smolbench or leaneval, or to verify a change works end-to-end.
---

# Run SmolBench

Two runnable units, no GUI/server. **smolbench** (repo root): a Python 3.14
LLM-eval library — "running" it means driving the real quiz → provider →
evaluate → grade → YAML pipeline against a local OpenAI-compatible stub,
zero credentials. **leaneval** (`lean/`): a Lean 4 theorem-proving eval CLI
with its own Python 3.12 env. All paths below are relative to the repo root;
all commands were verified in a headless Linux container.

## Prerequisites

```bash
uv sync --all-extras        # root .venv (Python 3.14) — smolbench + dev + notebook extras
cd lean && uv sync && cd -  # lean/.venv (Python 3.12) — separate, incompatible env
```

## Run (agent path)

```bash
# End-to-end smoke: generation -> provider dispatch -> stub round trip -> grading -> YAML IO.
# `timeout` is mandatory: the provider retries transient failures FOREVER (60s backoff).
timeout 120 .venv/bin/python .claude/skills/run-smolbench/driver.py   # PASS + exit 0

.venv/bin/python -m pytest tests/ -q          # 52 tests, offline, ~7s

.venv/bin/python -m smolbench.induction.periodic              # quiz-generation demo
.venv/bin/python -m smolbench.induction.chromatic | tail -25  # prints ~120 prompt blocks

bash .claude/skills/run-smolbench/lean_smoke.sh           # leaneval Tier 1 (~seconds warm)
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

## Run: leaneval (`lean/`)

`lean_smoke.sh` handles env sync and a one-time 64 MB benchmark bootstrap
(Zenodo record 10929138 → `lean/data/leandojo_benchmark_4/`, gitignored).
Manual driving, from `lean/` with `export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt`:

```bash
uv run python -m leaneval.cli metadata
uv run python -m leaneval.cli list --kind random --split test --limit 5
uv run python -m leaneval.cli replay -n 1 --seed 0   # needs elan; see Gotchas
```

Verified tiers in this container: `metadata`/`list` (credential-free, no
Lean) and `replay`/Dojo (needs elan on PATH; first call pulls the ~2.4 GB
traced corpus from S3 to `~/.cache/lean_dojo/` — creds-free, ~1 min; cold
replay ~2–4 min, warm ~10 s). NOT verified here: `run-cell`/`run-sweep`
(need a provider key — `PRIME_INTELLECT_API_KEY` or `ANTHROPIC_API_KEY` —
and cost money) and `filter` (~70 min/split). `lean/figures/*.py` need sweep
results under `lean/results/runs/` which are gitignored and absent.

## Live AWS surfaces — do NOT run without explicit user opt-in

`scripts/bedrock_smoke.py`, `scripts/ec2_lifecycle_smoke.py <step>`, and the
`notebooks/{periodic,chromatic}/` notebooks provision/bill real AWS infra
(Bedrock, EC2 spot vLLM, SageMaker) and need `keys.env` credentials (never
print those files). Runbook: `REFACTOR.md` §2.8 "Live-verification runbook";
last live-verified 2026-07-02. Everything in this skill runs without them.

## Gotchas

- System `python3` is 3.12; smolbench requires ≥3.14 → always
  `.venv/bin/python`. Meanwhile `lean/` requires ≥3.11,<3.13 → the two venvs
  are mutually incompatible; never point one unit at the other's venv.
- `uv sync` prunes packages not in the lockfile: it uninstalls the ad-hoc
  `aws-bedrock-token-generator` that `scripts/bedrock_smoke.py` needs
  (observed). Restore with `uv pip install aws-bedrock-token-generator`.
  Plain `uv run` / `uv run --no-sync` likewise strips extras — resync with
  `uv sync --all-extras`; use `uv run --no-project` for ephemeral scripts.
- The shared `ChatClient` retries 429/5xx/connection errors **forever**
  (60 s backoff) under openrouter — always wrap unattended runs in `timeout`.
- `StubServer.next_response` pops FIFO: queued-response↔question mapping is
  only deterministic with `max_parallel=1`; for parallel fan-out set a
  uniform `server.default_response` instead.
- Direct `provider.query()` needs explicit `context_length=` (default 0
  fails any response that reports `usage.total_tokens`); `evaluate()`
  resolves it internally via a GET the stub answers with 100000.
- Repo rule: every request carries `seed` — never drop it to dodge an error.
- `notebooks/*/results*/` are huge generated YAML trees (~80 M lines) —
  never grep/glob them blindly.
- leaneval's README says `GITHUB_ACCESS_TOKEN` is required — `replay`
  verified working **without** it here (corpus comes from S3 anonymously);
  heavier LeanDojo use may still hit anonymous GitHub rate limits.
- elan is enough for Dojo: install with
  `curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none`
  (Dojo fetches its own pinned toolchain; `lean/lean-toolchain` is not used
  by the harness).

## Troubleshooting

- `RuntimeError: Python 3.12.x is too old` from the driver → you used system
  `python3`; rerun with `.venv/bin/python`.
- `cannot import tests.conftest` (driver exit 2) → run from a synced repo:
  `uv sync --all-extras` at the root.
- `elan not found` from `lean_smoke.sh --replay` → install elan (line above)
  or run the default Tier-1 smoke instead.
