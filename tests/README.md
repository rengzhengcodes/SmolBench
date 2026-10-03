# tests/

## Running

```
uv sync --all-extras          # the suite imports the notebook extra (dotenv, scipy, statsmodels)
.venv/bin/python -m pytest tests/ -q
```

A bare `pytest` from the repo root also works: `pyproject.toml` sets
`pythonpath = ["."]` so `tests._paths` and `conftest` import cleanly
without a `tests/__init__.py`.

## Grouping

Tests are grouped by subsystem under test:

- `analysis/` -- the induction analysis chain (report rendering, statistics,
  run_all driver) over synthetic result trees from `_trees.py`.
- `evals/` -- harness infrastructure and providers (EC2, AWS, OpenAI-compat,
  results store, marks I/O, tokenization/parsing).
- `induction/` -- the induction benchmark (periodic quizzes,
  golden fixtures).
- `deduction/` -- the Horn-rule benchmark (generator, checker, scoring
  modes, sweep drivers, reproduction CLI, tables and figures).

## Path conventions

- `tests/conftest.py` and `tests/fixtures/` stay at the `tests/` root:
  pytest resolves `conftest.py` by directory ancestry, so its fixtures reach
  every group.
- Import repo anchors from `tests/_paths.py` instead of hand-counting
  `parents[N]`; see that file for why.

## No `__init__.py` in subdirectories

Test module basenames must stay globally unique across all subdirectories
(pytest's rootdir-relative test IDs assume this when there's no package
marker). Do not add `__init__.py` or `conftest.py` inside `analysis/`,
`evals/`, `induction/` or `deduction/`.
