# Reading the deduction snapshot: rules vs. one dataset's measured findings

> **Provenance.** The counts in this document were measured on the family-ladder
> re-collection as published under `analysis/2026-08-16`
> (`scripts/results/snapshot_analysis_data.py --dest analysis/2026-08-16`).
> They describe **that dataset**. A snapshot taken with a different
> `--spool-prefix`, or the same prefix re-collected at a later date, is a
> different set of rows and must be re-measured before any of the specific
> numbers below are trusted again. `scripts/results/audit_run_completeness.py`
> is the tool that re-measures them.
>
> This file is checked into git (dated, reviewable) rather than being
> re-emitted as literal prose inside `MANIFEST.json` on every snapshot run --
> the manifest only ever carries fields computed from the run that wrote it.

## Rules (hold for any snapshot of this study)

These describe the study's data model and are not specific to one
`--spool-prefix` or one date:

- **Sources are unmodified.** This is a snapshot of an append-only experiment
  log; no source object is ever changed or deleted by taking a snapshot.
- **`verified_rows.jsonl` is the analysis input.** `deduction/<model>/verified_rows.jsonl`
  is what analysis reads; `deduction/<model>/all_rows.jsonl` holds the
  pre-verification candidates and is not itself an analysis input.
- **`exception` is infrastructure, not a model failure.** An `exception`
  verdict means the attempt never reached the model at all. Exclude these
  rows from scoring -- never count them as a score of 0.
- **`replay_failed` is a verification-setup failure, not a model failure.**
  A `replay_failed` verdict means verification could not be set up at all --
  LeanDojo could not open the theorem, or the ground-truth prefix would not
  replay -- so no model was ever actually tested on that cell. Exclude these
  rows from scoring -- never count them as a score of 0.
- **`incomplete` is model-dependent and stays in the denominator.** Unlike
  `exception`/`replay_failed`, `incomplete` reflects the model actually being
  tested and not finishing -- it is a genuine failure and belongs in the
  denominator, not excluded.
- **The `*_SUPERSEDED-*` / `*_STALE-*` / `*_BROKEN-*` files are the repair
  audit trail.** They are copied on purpose; their names say they are not
  current data, and they should not be read as live rows.

## Measured findings (specific to the `analysis/2026-08-16` dataset)

These are counts observed on this one re-collection. Re-measure them for any
other snapshot before relying on them:

- **Take the earliest surviving (non-exception) row per cell.** In this
  dataset, 74 cells across 3 lanes hold more than one surviving attempt. The
  last-wins alternative (taking the most recent attempt instead of the
  earliest surviving one) inflates ministral-3-3b by 5.9 points, so the
  earliest-surviving rule matters here, not just as a tie-break formality.
- **The `replay_failed` cells are the same 232 cells in every lane.** Of
  those, 151 come from `DojoInit` failures and 81 from prefix-replay
  failures. Because they are identical across every lane, the measurable
  denominator in this dataset is 944 - 232 = 712 cells per lane. Scoring
  these 232 as 0 instead of excluding them deflates every marginal rate by up
  to 24.6%.
- **The `incomplete` split is 68/30/50 across the three lanes.** `incomplete`
  is model-dependent (see the rule above), and in this dataset the three
  lanes' incomplete counts are 68, 30, and 50 respectively.
