---
name: run-smolbench
description: Run and test SmolBench's offline evals and Lean theorem-proving harness.
---

# Run SmolBench

Use the repo `.venv`; ordinary tests and demos need no credentials. Lean
verification needs `lean-interact`, elan, and a built mathlib4 checkout at
`SMOLBENCH_MATHLIB_ROOT`; generation and analysis do not.

## Prerequisites

```bash
uv sync --all-extras
```

## Run

```bash
# `timeout` is required: provider retries transient failures forever (60s backoff).
timeout 120 .venv/bin/python .claude/skills/run-smolbench/driver.py
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m smolbench.induction.periodic

bash .claude/skills/run-smolbench/lean_smoke.sh
bash .claude/skills/run-smolbench/lean_smoke.sh --replay
bash .claude/skills/run-smolbench/lean_smoke.sh --e2e
```

## Lean commands

```bash
.venv/bin/python -m smolbench.deduction.lean.cli metadata
.venv/bin/python -m smolbench.deduction.lean.cli list --kind random --split test --limit 5
.venv/bin/python -m smolbench.deduction.lean.cli analyze <run_dir>/all_rows.jsonl

export SMOLBENCH_MATHLIB_ROOT=/path/to/mathlib4
.venv/bin/python -m smolbench.deduction.lean.cli replay -n 1 --seed 0
.venv/bin/python -m smolbench.deduction.lean.cli run-sweep --config <sweep.yaml>
```

`lean_smoke.sh` bootstraps the 64 MB Benchmark 4 download at
`notebooks/deduction/data/leandojo_benchmark_4/`. `filter` (~70 min/split)
produces required `replay_passing_*.jsonl` sidecars. The canonical sweep is
`notebooks/deduction/run_study.py`; results land in
`notebooks/deduction/results/runs/`.

`lean_smoke.sh --e2e` is credential-free: it uses local provider stubs and a
temporary Lean project, but needs elan. Real `run-cell`/`run-sweep` need
`PRIME_INTELLECT_API_KEY` or `OPENROUTER_API_KEY`, cost money, and require
explicit user opt-in.

For direct provider tests, `get_periodic_numeric_quiz` needs an explicit
`tokenizer` because its noise arm pads exact token counts. `StubServer` FIFO
responses are deterministic only with `max_parallel=1`; use
`server.default_response` for parallel fan-out. `provider.query()` and
`complete()` need `context_length=` (default 0 fails token-usage responses);
`evaluate()` resolves it with a stub GET of 100000.

## Live AWS

Do not run `scripts/smoke/bedrock_smoke.py`,
`scripts/smoke/ec2_lifecycle_smoke.py <step>`, `scripts/fleet/run_fleet.py`,
or the `notebooks/{induction,deduction}/run_study.py` lane drivers without
explicit opt-in: they provision billable infrastructure and need `keys.env`.
Never print credential files.

## Gotchas

- Always use `.venv/bin/python`, never system Python. Lean `run-sweep`,
  `run-cell`, `replay`, and `filter` additionally need elan and the built
  `SMOLBENCH_MATHLIB_ROOT` checkout.
- `uv sync` removes ad-hoc packages outside the lockfile, including
  `aws-bedrock-token-generator`; restore it with `uv pip install
  aws-bedrock-token-generator`. `uv run` and `uv run --no-sync` strip extras;
  use `uv run --no-project` for ephemeral scripts.
- `ChatClient` retries 429/5xx/connection failures forever, so unattended
  runs must use `timeout`. Lean sweeps use `max_retries` (default 4) so an
  endpoint cannot hold an open REPL forever.
- Keep `seed` on every request; Lean sweeps derive it as `config["seed"] +
  replicate_idx`.
- Do not glob `notebooks/*/results*/`: generated results are huge.
- `GITHUB_ACCESS_TOKEN` is unnecessary for REPL `replay`, but LeanDojo tracing
  and premise slicing can hit GitHub rate limits.
- elan alone is insufficient: build mathlib4 (`lake exe cache get && lake
  build`) because `lean-interact` runs its REPL under that checkout's
  `lean-toolchain`. Install elan with `curl -sSf
  https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
  -s -- -y --default-toolchain none` if needed.

## Troubleshooting

- `Python ... is not the project interpreter` or `cannot import
  tests.conftest` → run `uv sync --all-extras` and use `.venv/bin/python`.
- Missing `lean_interact` → run `uv sync --all-extras`.
- Missing `SMOLBENCH_MATHLIB_ROOT` → export a built elan/lake mathlib4
  checkout; the verifier records it as `lean_error`/`replay_failed` on cells
  and `exception` on sanity rows.
- `elan not found` → install elan or run default Tier-0/1 smoke.
