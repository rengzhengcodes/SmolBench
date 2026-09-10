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
      run_all.py                  sequences power_analysis -> paired_analysis -> significance_report -> extens_vs_noise
  deduction/                   family-ladder Lean 4 deduction study
    run_study.py                the (generation-only) driver  <- ditto
    lean_eval.ipynb             the exploration notebook
    README.md                   ditto, plus the Lean data bootstrap
    sweep.yaml                  knobs shared by all 21 lanes; sha256-stamped into each run's manifest.json
    results/, data/             S3-mirrored; both archived out of the tree
    analysis/                   the numbers that got published
      rows_source.py              the one `--s3` / `--rows-dir` choice shared by the three scripts
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

**A re-run retires its predecessor rather than racing it.** The S3 key is an
append-only log; a forced re-collection goes through
`ResultsStore.regrade`/`supersede_all` (retire every surviving run
at the address, then write the replacement, whose `regraded_from` names the run
it replaced). `ARCHIVE.md` has the marker spellings.

`notebooks/deduction/analysis/rows_source.py` is where the three deduction
scripts resolve their rows: `--s3 [PREFIX]` fetches straight off S3 into a
scratch directory, `--rows-dir` reads a local tree, and `reject_superseded`
refuses retired artifacts. `notebooks/deduction/sweep.yaml` holds the knobs
shared by all 21 lanes.

## statistical_analyses.ipynb

The single notebook of this study's statistics. It imports the live analysis
modules; cells that need the full results store are gated behind `RUN_HEAVY`
and print a `skipped` line when it is off. Its heavy deduction cells fetch rows
through `rows_source` into scratch, never a tracked path; the archive-reading
cells stream the `archives/2026-08-25` evidence prefix off S3. It carries the
posterior DECIDED/EQUIVALENT/UNDECIDED classifier and re-derives the score-level
flip rate from the archived JSON, asserting equality with the stored numbers.
Outputs are committed cleared.
