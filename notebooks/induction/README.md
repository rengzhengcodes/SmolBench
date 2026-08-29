# Induction: family-ladder scaling study

This is the INDUCTION side of the family-ladder scaling study (periodic and
chromatic quizzes). See `smolbench/induction/README.md` for the task design
and the shared experiment API these scripts drive, and `notebooks/README.md`
for what is anchored where across both studies.

```
induction/
  run_study.py            the driver          <- pinned here; see "Layout" below
  induction_eval.ipynb    the exploration notebook
  keys.env                the driver's own sibling (untracked)
  results/                S3-mirrored replicate YAMLs; archived out of the tree
  analysis/               the numbers that got published
  audits/                 concluded one-off probes
```

## Layout

`run_study.py`, `induction_eval.ipynb` and `keys.env` stay at this study
root because things outside this directory reach them by literal path:
`scripts/fleet/run_fleet.py` builds a lane's argv from
`notebooks/induction/run_study.py`, `scripts/fleet/run_shards.py` finds
running shards with `pgrep -f` on that same string,
`notebooks/deduction/run_study.py` loads this driver by file path for the
shared roster, and the driver itself does
`load_dotenv(__file__.parent / "keys.env")`.

`results/` stays directly beneath this directory because
`notebooks/induction/results` is what `results_store.experiment_name`
matches to derive the short S3 experiment prefix `induction`.

Everything else is free to be grouped, and is. The write-side S3 key comes
from the literal `notebook_dir="induction"` argument to
`InductionExperiment` (`run_study.py`), not from any script's `__file__`,
and nothing under `analysis/` or `audits/` writes to the store -- they are
read-only consumers of a synced-down local tree. Their depth affects only
where they READ from, so the ones that need `results/` anchor it explicitly
(`_power_common.results_dir(__file__, up=1)`, or `parents[1]`) rather than
assuming a sibling. `tests/tooling/test_power_common.py` pins that.

## Study driver

- `run_study.py` -- headless driver for the family-ladder scaling study.
  Defines the roster (`MODELS`, `COT_ARGS`) and sweep config.
  `notebooks/deduction/run_study.py` loads it by file path for both;
  `audits/check_currency.py` imports `MODELS` from it as the model ->
  local-tag map. The analysis scripts do
  NOT -- they take their own `MODELS` from `analysis/power_analysis.py`.
- `induction_eval.ipynb` -- the fleet-aware notebook for exploring and
  validating the study; framing cells document the as-served roster,
  config epochs, and the earliest-wins selection rule.

## analysis/ -- the published numbers

Each script puts its own directory on `sys.path` and imports its siblings
by bare name; `power_analysis.py` is the root of that chain and the only
one that resolves `results/`.

| File | What it's for |
| --- | --- |
| `power_analysis.py` | Power analysis for the family-ladder scaling study. Owns `MODELS`, `INFOS` and `RESULTS_DIR` for the whole `analysis/` chain. |
| `paired_analysis.py` | Paired re-analysis of the family-ladder induction study. |
| `significance_report.py` | Holm and Hochberg significance report over the primary contrast family. |
| `extens_vs_noise.py` | Focused test: extensional vs noise-padded intensional, per model. |
| `multiplicity_sim.py` | Monte Carlo study of TEST and CORRECTION choice for this study. Standalone -- imports nothing from its siblings. |

## audits/ -- concluded one-off probes

These answered a specific question once and are kept for the record;
read each one's module docstring for its inputs before re-running.

| File | What it answered |
| --- | --- |
| `check_currency.py` | Re-gates the local induction tree on CONTENT, under the earliest-wins ruling. Takes an S3 key listing as `argv[1]`. |
| `verify_survivorship.py` | Shows the empty-response profile of ministral-3-14b's re-collected seeds vs the rest. |
| `response_audit.py` | Response-level audit of the induction results tree. `verify_survivorship.py` imports its `TagIgnoringLoader`. |

## results/

S3-mirrored and not in this tree; see `notebooks/ARCHIVE.md`.
