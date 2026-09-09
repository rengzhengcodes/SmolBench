# tests/

## Running

```
uv sync --all-extras          # the suite imports the notebook extra (dotenv, scipy, statsmodels, matplotlib)
.venv/bin/python -m pytest tests/ -q
```

`pyproject.toml` sets `pythonpath = ["."]`, so a root `pytest` works without
`tests/__init__.py`.

## Grouping

Tests are grouped by subsystem:

- `evals/` -- harness infrastructure and providers.
- `induction/` -- periodic quizzes, fixtures, and figures.
- `deduction/` -- Lean 4 pipeline scripts.
- `tooling/` -- cross-study fleet, evidence, bucket, and analysis contracts.

## Path conventions

- Keep `tests/conftest.py` and `tests/fixtures/` at the root: pytest resolves
  `conftest.py` by ancestry, so fixtures reach every group.
- Import repo anchors from `tests/_paths.py`, not `parents[N]`.

## No `__init__.py` in subdirectories

Test module basenames must stay globally unique because pytest uses
rootdir-relative IDs without package markers. Do not add `__init__.py` or
`conftest.py` inside `evals/`, `induction/`, `deduction/`, or `tooling/`.
