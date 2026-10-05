# notebooks/

The analysis scripts use released result folders:

```
notebooks/
  deduction/
    analysis/                 Horn tables and figures, built by make_figures.py
  induction/
    analysis/
      induction_results.py    Induction results table
```

The analysis scripts import sibling modules by bare name and add the required directory
to `sys.path` themselves.
