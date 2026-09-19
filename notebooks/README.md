# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Result trees, evidence
packages, data sidecars and writeups live on S3 and the release assets;
[`ARCHIVE.md`](ARCHIVE.md) says where. Each study's own README covers its
task design, run instructions and contracts.

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
  deduction/                   family-ladder Lean 4 deduction study
    run_study.py                the (generation-only) driver  <- ditto
    lean_eval.ipynb             the exploration notebook
    README.md                   ditto, plus the Lean data bootstrap
    results/, data/             S3-mirrored; both archived out of the tree
    analysis/                   the numbers that got published
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

**Both `run_study.py` files are launched by literal path.**
`scripts/fleet/run_fleet.py` builds each lane's argv from
`notebooks/<study>/run_study.py` (in `scripts/fleet/lane_env.py`),
`scripts/fleet/run_shards.py` matches
running shards with `pgrep -f notebooks/induction/run_study.py`, and
`notebooks/deduction/run_study.py` loads the induction driver by file path
for the shared roster. `notebooks/induction/keys.env` must stay the induction
driver's own sibling (`load_dotenv(__file__.parent/"keys.env")`).

## Sibling imports inside a study

Analysis scripts put `notebooks/` (for `_power_common`) and/or their own
directory on `sys.path` and import siblings by bare module name. Both legs
ship a `power_analysis.py`, so whichever imported first would own
`sys.modules["power_analysis"]` for the rest of a session: anything loading
both legs in one process (`tests/tooling/test_analysis_stats.py`,
`statistical_analyses.ipynb`) loads each module under a unique name and binds
the bare names only for the duration of each exec.
