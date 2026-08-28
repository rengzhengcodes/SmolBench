# Induction: family-ladder scaling study

This is the INDUCTION side of the family-ladder scaling study (periodic and
chromatic quizzes). Files stay flat in this directory on purpose:
`results_dir(__file__)` anchors `results/` as this directory's sibling, and
this study's S3 experiment keys derive from `notebooks/<study>/results` --
so `<study>` has to stay `induction`, not some deeper subpath. See
`smolbench/induction/README.md` for the task design and the shared
experiment API these scripts drive.

## Study driver

- `run_study.py` -- headless driver for the family-ladder scaling study:
  the roster (`MODELS`, `COT_ARGS`) and sweep config every other file in
  this directory (and `notebooks/deduction/run_study.py`) imports from.
- `induction_eval.ipynb` -- the fleet-aware notebook for exploring and
  validating the study; framing cells document the as-served roster,
  config epochs, and the earliest-wins selection rule.

## Analysis / report scripts

- `power_analysis.py` -- power analysis for the family-ladder scaling
  study.
- `paired_analysis.py` -- paired re-analysis of the family-ladder
  induction study.
- `significance_report.py` -- Holm and Hochberg significance report over
  the primary contrast family.
- `extens_vs_noise.py` -- focused test: extensional vs noise-padded
  intensional, per model.

## One-off audit probes

- `check_currency.py` -- re-gates the local induction tree on CONTENT,
  under the earliest-wins ruling.
- `compare_selection_rules.py` -- isolates the earliest-vs-newest
  selection rule's effect on induction conclusions.
- `build_selected_tree.py` -- builds an earliest-selected induction tree,
  per the 2026-08-16 user ruling.
- `verify_survivorship.py` -- shows the empty-response profile of
  ministral-3-14b's re-collected seeds vs the rest.
- `multiplicity_sim.py` -- Monte Carlo study of TEST and CORRECTION
  choice for the induction study.
- `response_audit.py` -- response-level audit of the induction results
  tree.

## results/

S3-mirrored; the local tree has been archived -- see `notebooks/README.md`
for what was removed, its S3 location, and how to regenerate or restore it.
