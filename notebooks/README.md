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
    run_study.py                 the driver           <- fleet launches this by path
    induction_eval.ipynb         the exploration notebook
    results/                     S3-mirrored replicate YAMLs; not in the tree  <- S3 key anchor
    analysis/                    the numbers that got published
      run_all.py                   sequences power_analysis -> paired_analysis -> significance_report -> extens_vs_noise
  deduction/                  family-ladder Lean 4 deduction study
    run_study.py                 the (generation-only) driver  <- ditto
    lean_eval.ipynb              the exploration notebook
    sweep.yaml                   knobs shared by all 21 lanes; sha256-stamped into each run's manifest.json
    results/, data/              S3-mirrored; both archived out of the tree
    analysis/                    the numbers that got published
      rows_source.py               the one `--s3` / `--rows-dir` choice shared by all three scripts here
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
`analysis/`. `tests/tooling/test_analysis_stats.py` pins both call sites
(`test_shared_scaffolding_wiring`).

**2. Both `run_study.py` files are launched by literal path.**
`scripts/fleet/lane_env.py` builds each lane's argv from
`notebooks/<study>/run_study.py` (one literal path per study, in
`lane_command`), `scripts/fleet/run_shards.py` matches running shards with
`pgrep -f notebooks/induction/run_study.py`, and
`notebooks/deduction/run_study.py` loads the induction driver by file path
(`importlib.util.spec_from_file_location`) for the shared roster.
`notebooks/induction/keys.env` must stay the induction driver's own sibling
(`load_dotenv(__file__.parent/"keys.env")`). So the induction driver, and
that env file, stay at their study root.

**3. A re-run retires its predecessor rather than racing it.**
The S3 key from fact 1 is an append-only log, so writing to it never
overwrites in place. Both a forced re-collection and
`scripts/results/regrade.py` go through `ResultsStore.regrade`/`supersede_all`:
every surviving run at an address is retired first (a sibling marker key on
S3, a renamed file locally), and only then is the replacement written; a
regrade's replacement additionally carries `regraded_from`, naming the
`run_ts` of the run it replaced. See **[`ARCHIVE.md`](ARCHIVE.md)** for the
exact marker spellings and key shapes.

## Sibling imports inside a study

Each analysis script puts `notebooks/` (for `_power_common`) and/or its own
directory on `sys.path` and imports its siblings by bare module name (`from
power_analysis import ...`). Both legs ship a file called `power_analysis.py`,
so whichever imported first would otherwise own
`sys.modules["power_analysis"]` for the rest of a session -- the same
collision applies to `error_bars`/`hint_vs_noise` (deduction) needing to
coexist with `paired_analysis`/`significance_report`/`extens_vs_noise`
(induction). Anything loading more than one leg in a single process --
`tests/tooling/test_analysis_stats.py`, `statistical_analyses.ipynb` -- loads
each module under a unique name, lets it bind the bare names it needs while it
execs, and unbinds every bare name afterward so the next module's own bare
imports resolve to itself rather than to whichever leg happened to load first.

`notebooks/deduction/analysis/rows_source.py` is the one place the deduction
scripts (`power_analysis.py`, `error_bars.py`, `hint_vs_noise.py`) resolve
where their rows come from: `--s3 [PREFIX]` (default the re-collection's
spool, `spool_prefix()`) or `--rows-dir` a local tree, and which spooled
artifacts are retired and must be refused (`reject_superseded`). None of the
three needs a locally-mirrored snapshot first -- `resolve_rows_dir` fetches
straight off S3 into a scratch directory when `--s3` is given.
`notebooks/deduction/sweep.yaml` holds the knobs shared by all 21 lanes, read
through `notebooks/deduction/run_study.py`'s `build_config`.

## statistical_analyses.ipynb

The single notebook of this study's statistics. It imports the live analysis
modules above (sizing, paired, significance, error-bar and hint-vs-noise
sections), with the cells that need the full results store gated behind
`RUN_HEAVY` -- with `RUN_HEAVY = False` they print a `skipped` line and read
nothing. Its heavy deduction cells fetch results-store rows the same way the
standalone scripts do, through `rows_source` (`--s3`/`resolve_rows_dir`),
landing them in scratch rather than a tracked path: §5's gated cell fetches
both the 21 lanes' `verified_rows.jsonl` and the DojoInit recovery run's
`recovered_rows.jsonl` this way and COMPUTES the post-recovery sensitivity
pool from them (`error_bars.main` with `--recovery-dir`). Separately, and
ungated, its provenance cell and §5, §8 and §9 read the `archives/2026-08-25`
evidence prefix directly off S3 (a `sha256`/`size`/`json` reader over
`smolbench.evals._aws.fresh_client`) and never write archived data to a local
path; §5's ungated cell streams the recovery run's own `report.json` out of
that archive as a pointer to the same run, not a substitute for the computed
pool. It also carries the posterior DECIDED/EQUIVALENT/UNDECIDED classifier
(§7) and re-renders the §8 score-level flip rate and §9 free flip bound from
that same archived JSON, asserting equality with the stored numbers. Outputs
are committed cleared.
