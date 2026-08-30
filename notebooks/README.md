# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Artifacts that are not in
this tree -- result trees, evidence packages, data sidecars, writeups --
live on S3 and the release assets; **[`ARCHIVE.md`](ARCHIVE.md)** says
where.

```
notebooks/
  _power_common.py            scaffolding shared by both power analyses
  statistical_analyses.ipynb  the single notebook of this study's statistics
  induction/                  family-ladder induction study
    run_study.py                the driver           <- fleet launches this by path
    induction_eval.ipynb        the exploration notebook
    results/                    S3-mirrored replicate YAMLs  <- S3 key anchor
    analysis/                   the numbers that got published
  deduction/                   family-ladder Lean 4 deduction study
    run_study.py                the (generation-only) driver  <- ditto
    lean_eval.ipynb             the exploration notebook
    results/, data/             S3-mirrored; both archived out of the tree
    analysis/                   the numbers that got published
```

Each study has its own README covering its task design, run instructions,
and contracts: [`induction/README.md`](induction/README.md),
[`deduction/README.md`](deduction/README.md).

## What is anchored where, and what may not move

Two path facts are load-bearing, and both are quiet when broken -- neither
raises, so a bad move shows up as wrong data rather than a traceback.

**1. `notebooks/<study>/results` is an S3 key.**
`results_store.experiment_name` maps a results directory onto an S3
experiment prefix only when its repo-relative path is EXACTLY three
components shaped `notebooks/<study>/results`; anything else takes a
documented full-path fallback and mints a *different* prefix. So the
directory names `induction`/`deduction` and the position of `results/`
directly beneath them are fixed. What is NOT fixed is how deep the scripts
sit: the write side takes its `<study>` segment from the literal
`notebook_dir="induction"` passed to `InductionExperiment`, never from any
script's `__file__`.

Read-side consumers reach `results/` through
`_power_common.results_dir(__file__, up=N)`, where `up` counts the levels
between a script and its study root -- `up=1` for everything under
`analysis/`. `tests/tooling/test_power_common.py` pins both call sites.

**2. Both `run_study.py` files are launched by literal path.**
`scripts/fleet/run_fleet.py` builds each lane's argv from
`notebooks/<study>/run_study.py`, `scripts/fleet/run_shards.py` matches
running shards with `pgrep -f notebooks/induction/run_study.py`, and
`notebooks/deduction/run_study.py` loads the induction driver by file path
for the shared roster. `notebooks/induction/keys.env` must stay the
induction driver's own sibling (`load_dotenv(__file__.parent/"keys.env")`).
So both drivers, and that env file, stay at their study root.

## Sibling imports inside a study

Each analysis script puts its OWN directory on `sys.path` and imports its
siblings by bare module name (`from power_analysis import ...`). Both legs
ship a file called `power_analysis.py`, so whichever imported first would
otherwise own `sys.modules["power_analysis"]` for the rest of a session.
Anything loading more than one leg in a single process -- `tests/tooling/
test_analysis_stats.py`, `statistical_analyses.ipynb` -- therefore loads
each module under a unique name and binds the bare names only for the
duration of each exec.

## statistical_analyses.ipynb

The single notebook of this study's analyses. It imports the live modules
above (sizing, paired, significance, error-bar and hint-vs-noise sections,
gated behind `RUN_HEAVY` since they need the results store), ports the
posterior DECIDED/EQUIVALENT/UNDECIDED classifier, and re-renders the
§6.2 flip rate and §6.3 free bound from archived JSON streamed off S3,
asserting equality with the stored numbers. It never writes archived data
to a local path. Outputs are committed cleared.
