# Where the historical artifacts live

Result trees, evidence packages, data sidecars, analysis writeups and
concluded probe scripts are not kept in this tree. Docstrings that cite
`notebooks/README.md` or `notebooks/ARCHIVE.md` as provenance mean this file.

## S3

Everything is under `s3://smolbench-results-414266451290/` (`us-west-2`):

| Prefix | What |
| --- | --- |
| `<study>/<model>/seed=<seed>/<info>--<run_ts>.yaml` | the live append-only experiment log (`smolbench.evals.results_store`); reads are earliest-wins |
| `deduction/runs/scaling_<spec-key>/` | per-lane deduction spools (`all_rows.jsonl`, `verified_rows.jsonl`) |
| `analysis/<date>/` | frozen analysis snapshots the report scripts render from (`scripts/results/snapshot_analysis_data.py`) |
| `archives/<date>/` | dated archives of what left the tree: zips at the prefix root, plus the unpacked evidence tree, data sidecars, LeanDojo corpus (`notebooks/deduction/`), record files (`notebooks/`), and concluded scripts/tests (`scripts/`, `tests/`) |
| `archives/2026-08-30/notebooks/induction/audits/` | the three concluded induction audit probes (`check_currency.py`, `verify_survivorship.py`, `response_audit.py`); also `pr4_induction_audits_2026-08-30.zip` on the PR #4 release |

Paths inside an archive are the flat layout of the tree on the day it was
taken; they are never rewritten to match today's grouped layout.

Tests that pin archived evidence stream it from S3, never a local copy:

```bash
SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/<date> \
    .venv/bin/python -m pytest tests/deduction/test_s3_archive.py -q
```

## GitHub releases

The same zips are attached to releases created for the pull requests that
removed them. Releases attach to tags, not PRs: `gh release list` shows every
archive tag, with sha256s in the release notes.

## What is regenerable, and what is not

| Kind | Regenerate with |
| --- | --- |
| Report `.txt` files (`*_REPORT.txt`) | the matching script under `notebooks/<study>/analysis/`, against an analysis snapshot (needs AWS credentials) |
| `replay_passing_*.jsonl` sidecars | `.venv/bin/python -m smolbench.deduction.lean.cli filter --kind <kind> --split <split>` (~70 min per split); restore under `data_root().parent` |
| LeanDojo corpus | re-download from Zenodo; see `notebooks/deduction/README.md`, "Data bootstrap" |
| Evidence trees (`results/**`, `EVIDENCE.json` manifests, raw generations, logs) | NOT regenerable -- live GPU measurements; the archive is the record |
| Analysis writeups, correction verdicts, probe scripts | NOT regenerable; their live conclusions are in the code they shaped (`smolbench.evals.providers.ec2.DETERMINISM_ARGS`, the streaming transport, `notebooks/statistical_analyses.ipynb`) |

Nothing regenerable is tracked under `notebooks/` or `scripts/`.
