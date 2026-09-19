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
  results/                S3-mirrored replicate YAMLs; archived out of the tree
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
  the sweep config. `notebooks/deduction/run_study.py`
  loads it by file path for the shared roster; the analysis scripts do NOT --
  they take their own `MODELS` from `analysis/power_analysis.py`.
- `induction_eval.ipynb` -- the notebook for exploring and
  validating the study; framing cells document the as-served roster, config
  epochs, and the earliest-wins selection rule.

## analysis/ -- the published numbers

Each chained script inserts a `__file__`-anchored directory on `sys.path` --
its own, or `notebooks/` for the ones importing `_power_common` -- and imports
its siblings by bare name. `power_analysis.py` roots that chain and owns
`RESULTS_DIR` for it; it warns when the checkout it reads is not the one the
installed package's `sync_down()` writes. All read marks through
`Marks.load`, never scraped.

`run_all.py` prints a banner before each script so a long combined log says
whose numbers are whose, and keeps `multiplicity_sim` behind `--with-sim`
because its Monte Carlo takes longer than the rest of the chain combined.

| File | What it's for |
| --- | --- |
| `power_analysis.py` | Power analysis for the family-ladder scaling study. Owns `MODELS`, `INFOS` and `RESULTS_DIR` for the whole `analysis/` chain. |
| `paired_analysis.py` | Paired re-analysis of the family-ladder induction study. |
| `significance_report.py` | Holm and Hochberg significance report over the primary contrast family. |
| `extens_vs_noise.py` | Focused test: extensional vs noise-padded intensional, per model. |
| `multiplicity_sim.py` | Monte Carlo study of TEST and CORRECTION choice for this study. Imports its design constants from `_power_common` and `power_analysis`; reads no results tree. |
| `run_all.py` | The one driver over the chain above: runs the four report scripts in process, in order, plus `multiplicity_sim.py` behind `--with-sim`. |

## audits/ and results/ -- archived

The three concluded audit scripts are not in this tree:

- `check_currency.py`: checked that every local `results/` file matched the
  earliest-timestamped S3 object for its (model, seed, arm) by content size,
  i.e. that the local tree was current under earliest-wins.
- `verify_survivorship.py`: compared the empty-response rate of
  ministral-3-14b's seven re-collected seeds against the other 23, per arm,
  to size the exclusion-bias caveat left by a delivery fault.
- `response_audit.py`: tallied raw responses per condition (empty, scored
  correct, correct answer present anywhere, longest) to tell a genuinely
  low-accuracy lane from a broken one.

They left it on 2026-08-30 and live on S3 under
`archives/2026-08-30/notebooks/induction/audits/` (and in the PR #4 release
zip). `results/` is likewise S3-mirrored rather than tracked. The exact
locations are listed in `notebooks/ARCHIVE.md`.
