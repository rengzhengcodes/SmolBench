# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Result trees are S3-backed
and not tracked here. Each study's own README covers its task design, run
instructions and contracts.

```
notebooks/
  _power_common.py            scaffolding shared by both power analyses
  statistical_analyses.ipynb  the single notebook of this study's statistics
  induction/                  family-ladder induction study
    run_study.py                the driver           <- fleet launches this by path
    induction_eval.ipynb        the exploration notebook
    README.md                   task design, layout, the analysis chain
    results/                    S3-mirrored replicate YAMLs; not in the tree  <- S3 key anchor
    analysis/                   the numbers that got published
                                (induction_results.py: the accuracy table)
  deduction/                   Horn-rule deduction benchmark
    analysis/                   tables and figures from the released results
                                (make_figures.py; see smolbench/deduction/horn/README.md)
```

## What may not move

Neither rule below raises when broken; a bad move shows up as wrong data.

**`notebooks/<study>/results` is an S3 key.** `results_store.experiment_name`
mints the short S3 experiment prefix only from a repo-relative path of
exactly three components shaped `notebooks/<study>/results`; anything else
takes the full-path fallback and a different prefix. Script depth is free:
the write side takes `<study>` from the literal `notebook_dir="induction"`
passed to `InductionExperiment`, never from a `__file__`, and readers anchor
through `_power_common.results_dir(__file__, up=N)` (`up=1` under
`analysis/`, pinned by `tests/tooling/test_analysis_stats.py`).

**`notebooks/induction/run_study.py` is launched by literal path.**
`scripts/fleet/run_fleet.py` builds each lane's argv from
`notebooks/<study>/run_study.py` (in `scripts/fleet/lane_env.py`), and
`scripts/fleet/run_shards.py` matches running shards with
`pgrep -f notebooks/induction/run_study.py`. `notebooks/induction/keys.env`
must stay the induction driver's own sibling
(`load_dotenv(__file__.parent/"keys.env")`).

## Sibling imports inside a study

Analysis scripts put `notebooks/` (for `_power_common`) and/or their own
directory on `sys.path` and import siblings by bare module name. Both legs
ship a `power_analysis.py`, so whichever imported first would own
`sys.modules["power_analysis"]` for the rest of a session: anything loading
both legs in one process (`tests/tooling/test_analysis_stats.py`,
`statistical_analyses.ipynb`) loads each module under a unique name and binds
the bare names only for the duration of each exec.
