# tests/

## Running

```
uv sync --extra dev
.venv/bin/python -m pytest -q
```

The tests run offline and need no credentials.

## Grouping

- `deduction/` covers Horn theories, checking and scoring, result reproduction, and
  analysis tables and figures.
- `induction/` covers protocol reproduction and the induction results table.
