# Induction: family-ladder scaling study

The INDUCTION side of the family-ladder scaling study (periodic quizzes).
`smolbench/induction/README.md` has the task design and the shared experiment
API these scripts drive; `notebooks/README.md` has the path anchors that hold
across both studies.

```
induction/
  run_study.py            the driver          <- launched by literal path
  induction_eval.ipynb    the exploration notebook
  keys.env                the driver's own sibling (untracked)
  results/                S3-mirrored replicate YAMLs; not in the tree
  analysis/               the numbers that got published
```

## Layout

`run_study.py`, `induction_eval.ipynb` and `keys.env` stay at this study root,
and `results/` stays directly beneath it, for the two reasons
`notebooks/README.md` gives. `keys.env` carries the driver's AWS credentials
plus any `EC2_*` / `INDUCTION_*` overrides (catalogued in `run_study.py`'s
module docstring); it is untracked with no committed example, because
credential-shaped files never enter the tree.

Everything else is free to be grouped, and is: nothing under `analysis/` writes
to the store, so a script's depth affects only where it reads from.

## Study driver

- `run_study.py` -- headless driver for the study; derives the roster
  (`MODELS`, `COT_ARGS`) from `smolbench/evals/study_config.toml` and owns
  the sweep config. The analysis scripts do NOT use `run_study.py` -- they
  take their own `MODELS` from `analysis/study_design.py`.
- `induction_eval.ipynb` -- the notebook for exploring and
  validating the study; framing cells document the as-served roster, config
  epochs, and the earliest-wins selection rule.

## analysis/ -- the published numbers

Each chained script inserts a `__file__`-anchored directory on `sys.path` --
its own, or `notebooks/` for the ones importing `_power_common` -- and imports
its siblings by bare name; `study_design.py` roots that chain (table below).
All read marks through `Marks.load`, never scraped; a lane with no replicates
(or, for `power_analysis.py`, no pilot replicate) exits with a `sync_down()`
hint, and an incomplete lane is compared on its common seeds under a depth
warning.

`run_all.py` prints a banner before each script so a long combined log says
whose numbers are whose, and keeps `multiplicity_sim` behind `--with-sim`
because its Monte Carlo takes longer than the rest of the chain combined.

| File | What it's for |
| --- | --- |
| `study_design.py` | The study design as read from `smolbench/evals/study_config.toml` (roster, `[study]` parameters), the contrast tiers and correction thresholds derived from it, and the CMH/McNemar/GCMH kernels. Owns `MODELS`, `INFOS` and `RESULTS_DIR` for the whole `analysis/` chain. |
| `power_analysis.py` | Sizing scans and the power report for the family-ladder scaling study. |
| `paired_analysis.py` | Paired re-analysis of the family-ladder induction study. |
| `significance_report.py` | Holm and Hochberg significance report over the primary contrast family. |
| `extens_vs_noise.py` | Focused test: extensional vs noise-padded intensional, per model. |
| `multiplicity_sim.py` | Monte Carlo study of TEST and CORRECTION choice for this study. Imports its design constants from `_power_common` and `study_design`; reads the tree only for PART 2's measured design effect and writes its checkpoint into it as `multiplicity_sim_results.json`. |
| `run_all.py` | The one driver over the chain above: runs the four report scripts in process, in order, plus `multiplicity_sim.py` behind `--with-sim`. |
