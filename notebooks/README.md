# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Result trees
(`notebooks/<study>/results/`) are gitignored; the induction tree mirrors the
S3 results store. Each study's own README covers its task design, run
instructions and contracts.

```
notebooks/
  _power_common.py            shared analysis constants and multiplicity corrections
  notebook_stats.py           posterior-power and bootstrap estimators for the stats notebook
  statistical_analyses.ipynb  every statistic the induction study reports
  induction/                  family-ladder induction study
    run_study.py                the driver           <- fleet launches this by path
    induction_eval.ipynb        offline infrastructure check: prompts, padding, budgets
    README.md                   task design, layout, the analysis chain
    results/                    S3-mirrored replicate YAMLs; gitignored  <- S3 key anchor
    analysis/                   the study's statistical reports and accuracy table
      study_design.py             roster, contrast tiers and test kernels the reports share
      run_all.py                  runs power_analysis -> paired_analysis ->
                                  significance_report -> extens_vs_noise
                                  (multiplicity_sim with --with-sim)
      induction_results.py        the accuracy table, from a fetched or local results folder
  deduction/                  Horn-rule deduction benchmark
    analysis/                   tables and figures from the released results
                                (make_figures.py; see smolbench/deduction/horn/README.md)
```

## What may not move

Neither rule below raises when broken; a bad move shows up as wrong data.

**`notebooks/<study>/results` is an S3 key.** `results_store.experiment_name`
mints the short S3 experiment prefix only from a repo-relative path of
exactly three components shaped `notebooks/<study>/results`; anything else
takes the full-path fallback and a different prefix. Scripts may sit at any
depth: the write side takes `<study>` from the literal `notebook_dir="induction"`
passed to `InductionExperiment`, never from a `__file__`, and readers anchor
through `study_design.RESULTS_DIR`, built from `repo_root()` and the literal
study name.

**`notebooks/induction/run_study.py` is loaded and launched by literal path.**
`scripts/fleet/lane_env.py` (imported by `scripts/fleet/run_fleet.py`) loads
it as a module and builds each lane's argv from that path.
`scripts/fleet/run_shards.py` launches it as `DRIVER` and matches running
shards with `pgrep -f notebooks/induction/run_study.py`.
`scripts/results/audit_run_completeness.py` also loads it by path.
`notebooks/induction/keys.env` must stay the driver's sibling: the driver
loads it from its own directory.

## Sibling imports inside a study

Analysis scripts put `notebooks/` (for `_power_common`), the repo root, or
their own directory on `sys.path` and import siblings by bare module name.

## Tests

`tests/analysis/` covers the induction analysis chain and `run_all.py`.
`tests/tooling/test_analysis_stats.py` covers the analysis scripts' statistical
contracts, `tests/tooling/test_stats_notebook_posterior.py` the notebook's
posterior bootstrap, and `tests/tooling/test_notebook_docs.py` checks that every
file this README names exists.
