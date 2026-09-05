# notebooks/

One directory per study, each holding that study's driver, its exploration
notebook, and its analysis code grouped by job. Artifacts that are not in
this tree -- result trees, evidence packages, data sidecars, writeups --
live on S3 and the release assets; **[`ARCHIVE.md`](ARCHIVE.md)** says
where.

This repo lands as a five-slice PR stack. This commit is slice 2
(induction only), so several paths below don't exist yet; each forward
reference is marked with the slice that adds it: `scripts/fleet/*`
(`run_fleet.py`, `run_shards.py`) -- slice 4; anything under
`deduction/` / `smolbench/deduction/` / `tests/deduction/` -- slice 5;
`statistical_analyses.ipynb` / `tests/tooling/test_analysis_stats.py` /
`scripts/results/snapshot_analysis_data.py` -- slice 3.

```
notebooks/
  _power_common.py            scaffolding shared by both power analyses (deduction's lands in slice 5)
  statistical_analyses.ipynb  the single notebook of this study's statistics (slice 3)
  induction/                  family-ladder induction study
    run_study.py                the driver           <- fleet launches this by path
    induction_eval.ipynb        the exploration notebook
    results/                    S3-mirrored replicate YAMLs; not in the tree  <- S3 key anchor
    analysis/                   the numbers that got published
  deduction/                   family-ladder Lean 4 deduction study (slice 5)
    run_study.py                the (generation-only) driver  <- ditto
    lean_eval.ipynb             the exploration notebook
    results/, data/             S3-mirrored; both archived out of the tree
    analysis/                   the numbers that got published
```

Each study has its own README covering its task design, run instructions,
and contracts: [`induction/README.md`](induction/README.md),
[`deduction/README.md`](deduction/README.md) (slice 5).

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
`analysis/`. `tests/tooling/test_analysis_stats.py` (slice 3) will pin both
call sites (`test_shared_scaffolding_wiring`).

**2. Both `run_study.py` files are launched by literal path.**
`scripts/fleet/run_fleet.py` (slice 4) will build each lane's argv from
`notebooks/<study>/run_study.py`, `scripts/fleet/run_shards.py` (slice 4)
will match running shards with `pgrep -f notebooks/induction/run_study.py`,
and `notebooks/deduction/run_study.py` (slice 5) will load the induction
driver by file path for the shared roster once it lands.
`notebooks/induction/keys.env` must stay the induction driver's own sibling
(`load_dotenv(__file__.parent/"keys.env")`). So the induction driver, and
that env file, stay at their study root now; the deduction driver will be
bound by the same constraint once slice 5 lands.

## Sibling imports inside a study

Each analysis script puts `notebooks/` (for `_power_common`) and/or its own
directory on `sys.path` and imports its siblings by bare module name (`from power_analysis import ...`). Only one leg
(`induction/`) exists at this commit. Once `deduction/` lands (slice 5),
both legs will ship a file called `power_analysis.py`, so whichever
imported first would otherwise own `sys.modules["power_analysis"]` for the
rest of a session. Anything loading more than one leg in a single process
-- `tests/tooling/test_analysis_stats.py` (slice 3), `statistical_analyses.ipynb`
(slice 3) -- will therefore need to load each module under a unique name and
bind the bare names only for the duration of each exec.

## Lands in later slices

### statistical_analyses.ipynb (slice 3)

The single notebook of this study's analyses, once it lands. It will
import the live modules above (sizing, paired, significance, error-bar and
hint-vs-noise sections, gated behind `RUN_HEAVY` since they need the
results store), port the posterior DECIDED/EQUIVALENT/UNDECIDED classifier,
and re-render its §8 score-level flip rate and §9 free flip bound from
archived JSON streamed off S3, asserting equality with the stored numbers.
It will never write archived data to a local path. Outputs will be
committed cleared.
