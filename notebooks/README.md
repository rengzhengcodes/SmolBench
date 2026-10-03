# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Result trees, evidence
packages, data sidecars and writeups live on S3 and the release assets;
[`ARCHIVE.md`](ARCHIVE.md) says where. Each study's own README covers its
task design, run instructions and contracts.

```
notebooks/
  _power_common.py            shared power-analysis scaffolding
  notebook_stats.py           induction posterior-power and bootstrap estimators
  statistical_analyses.ipynb  the single notebook of this study's statistics
  induction/                  family-ladder induction study
    run_study.py                the driver           <- fleet launches this by path
    induction_eval.ipynb        the exploration notebook
    README.md                   task design, layout, the analysis chain
    results/                    S3-mirrored replicate YAMLs; not in the tree  <- S3 key anchor
    analysis/                   the numbers that got published
      run_all.py                  sequences power_analysis -> paired_analysis -> significance_report -> extens_vs_noise
  deduction/                   Horn benchmark
    horn_results.ipynb          the results notebook
    HORN_BOTH_VS_PAD.md         benchmark findings
    HORN_RELEVANCE_DESIGNS.md, HORN_ROSTER_PLAN.md
    analysis/                   Horn result and route analyses
      horn_reasoning_figure.py, horn_results.py, horn_routes.py
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

**The induction `run_study.py` is launched by literal path.**
`scripts/fleet/run_fleet.py` builds each lane's argv from
`notebooks/<study>/run_study.py` (in `scripts/fleet/lane_env.py`),
and `scripts/fleet/run_shards.py` matches running shards with
`pgrep -f notebooks/induction/run_study.py`. `notebooks/induction/keys.env`
must stay the induction driver's own sibling
(`load_dotenv(__file__.parent/"keys.env")`).

## Sibling imports inside a study

Induction analysis scripts import siblings by bare name. Anything loading them
alongside other modules (`tests/tooling/test_analysis_stats.py`,
`statistical_analyses.ipynb`) loads each one under a unique name.

**A re-run retires its predecessor rather than racing it.** The S3 key is an
append-only log; a forced re-collection goes through
`ResultsStore.regrade`/`supersede_all` (retire every surviving run
at the address, then write the replacement, whose `regraded_from` names the run
it replaced). `ARCHIVE.md` has the marker spellings.

## statistical_analyses.ipynb

The single notebook of this study's statistics. It imports the induction
analysis modules plus `notebooks/notebook_stats.py`; cells that need the full
results store are gated behind `RUN_HEAVY` and print a `skipped` line when it
is off. It includes the posterior DECIDED/EQUIVALENT/UNDECIDED classifier.
Outputs are committed cleared. Horn results are analysed in
`notebooks/deduction/horn_results.ipynb`.
