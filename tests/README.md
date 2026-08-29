# tests/

## Running

Both interpreters must stay green (the repo ships two venvs because
`lean_dojo` only installs on Python 3.12):

```
.venv/bin/python -m pytest tests/ -q
.venv-lean/bin/python -m pytest tests/ -q
```

A bare `pytest` from the repo root also works: `pyproject.toml` sets
`pythonpath = ["."]` so `tests._paths` and `conftest` import cleanly
without a `tests/__init__.py`.

## Grouping

Tests are grouped by subsystem under test:

- `evals/` -- harness infrastructure and providers (EC2, AWS, OpenAI-compat,
  results store, marks I/O, tokenization/parsing).
- `induction/` -- the induction benchmark (periodic/chromatic quizzes,
  golden fixtures, figures).
- `deduction/` -- the Lean 4 benchmark and its pipeline scripts (corpus,
  context, prompt, runner, sft, decontam, verify, S3 archive).
- `tooling/` -- cross-study fleet/evidence/bucket/arch analysis contracts
  (run_fleet, run_shards, power_common, kv_budget, evidence_manifest,
  analysis_stats, provision_results_bucket).

## Path conventions

- `tests/conftest.py` and `tests/fixtures/` (including `fixtures/lean_mini`)
  stay at the `tests/` root -- they are shared across every group, and
  pytest resolves `conftest.py` by directory ancestry.
- Import repo anchors from `tests/_paths.py` instead of hand-counting
  `parents[N]`; see that file for why.

## No `__init__.py` in subdirectories

Test module basenames must stay globally unique across all subdirectories
(pytest's rootdir-relative test IDs assume this when there's no package
marker). Do not add `__init__.py` or `conftest.py` inside `evals/`,
`induction/`, `deduction/`, or `tooling/`.
