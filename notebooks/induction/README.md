# Induction: family-ladder scaling study

This is the INDUCTION side of the family-ladder scaling study (periodic
quizzes). See `smolbench/induction/README.md` for the task design
and the shared experiment API these scripts drive, and `notebooks/README.md`
for what is anchored where across both studies.

```
induction/
  run_study.py            the driver          <- pinned here; see "Layout" below
  induction_eval.ipynb    the exploration notebook
  keys.env                the driver's own sibling (untracked)
  results/                S3-mirrored replicate YAMLs; archived out of the tree
  analysis/               the numbers that got published
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

`keys.env` carries the driver's AWS credentials plus any `EC2_*` /
`INDUCTION_*` overrides (catalogued in `run_study.py`'s module docstring;
`EC2_*` is read at `ec2` import time -- see "keys.env first, then import" in
`smolbench/induction/README.md`). Untracked by design, with no committed
example: credential-shaped files never enter the tree.

Everything else is free to be grouped, and is. The write-side S3 key comes
from the literal `notebook_dir="induction"` argument to
`InductionExperiment` (`run_study.py`), not from any script's `__file__`,
and nothing under `analysis/` writes to the store -- they are
read-only consumers of a synced-down local tree. Their depth affects only
where they READ from, so the ones that need `results/` anchor it explicitly
(`_power_common.results_dir(__file__, up=1)`) rather than
assuming a sibling. `tests/tooling/test_analysis_stats.py`
(`test_shared_scaffolding_wiring`) pins that.

## Study driver

- `run_study.py` -- headless driver for the family-ladder scaling study.
  Defines the roster (`MODELS`, `COT_ARGS`) and sweep config.
  `notebooks/deduction/run_study.py` loads it by file path. The analysis
  scripts do NOT -- they take their own `MODELS` from `analysis/power_analysis.py`.
- `induction_eval.ipynb` -- the fleet-aware notebook for exploring and
  validating the study; framing cells document the as-served roster,
  config epochs, and the earliest-wins selection rule.

## analysis/ -- the published numbers

Each of the four chained scripts inserts a `__file__`-anchored directory on
`sys.path` -- its own (`extens_vs_noise.py`, `significance_report.py`,
`paired_analysis.py`) or `notebooks/` (`power_analysis.py`, which imports
`_power_common` from there) -- and imports its siblings by bare name;
`power_analysis.py` is the root of that chain and the only one that resolves
`results/`. `multiplicity_sim.py` is standalone and inserts nothing. All four
read marks through ``Marks.load`` (never scraped), so they run under the
project venv; `power_analysis.py` warns when the checkout it reads is not the
one the installed package's `sync_down()` writes.

| File | What it's for |
| --- | --- |
| `power_analysis.py` | Power analysis for the family-ladder scaling study. Owns `MODELS`, `INFOS` and `RESULTS_DIR` for the whole `analysis/` chain. |
| `paired_analysis.py` | Paired re-analysis of the family-ladder induction study. |
| `significance_report.py` | Holm and Hochberg significance report over the primary contrast family. |
| `extens_vs_noise.py` | Focused test: extensional vs noise-padded intensional, per model. |
| `multiplicity_sim.py` | Monte Carlo study of TEST and CORRECTION choice for this study. Standalone -- imports nothing from its siblings. |

## audits/ -- archived

The three concluded one-off probes (`check_currency.py`, `verify_survivorship.py`,
`response_audit.py`) left the tree on 2026-08-30; see `notebooks/ARCHIVE.md`.

## results/

S3-mirrored and not in this tree; see `notebooks/ARCHIVE.md`.
