# Where the historical artifacts live

Result trees, evidence packages, data sidecars, analysis writeups, and
concluded probe scripts are not kept in this tree. They live in two places,
and docstrings across the repo that cite `notebooks/README.md` or
`notebooks/ARCHIVE.md` as provenance mean this file.

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

The tests that pin archived evidence stream it from S3 and never write a
local copy (archived data is read on AWS, not pulled down):

```bash
SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/<date> \
    .venv/bin/python -m pytest tests/deduction/test_s3_archive.py -q
```

## GitHub releases

The same archive zips are attached to GitHub releases created for the pull
requests that removed them (releases attach to tags, not PRs -- e.g.
`gh release view pr4-regenerable-artifacts`; `gh release list` shows every
archive tag, with sha256s in the release notes).

## What is regenerable, and what is not

| Kind | Regenerate with |
| --- | --- |
| Report `.txt` files (`*_REPORT.txt`) | the matching script under `notebooks/<study>/analysis/`, against an analysis snapshot (needs AWS credentials) |
| `replay_passing_*.jsonl` sidecars | `.venv/bin/python -m smolbench.deduction.lean.cli filter --kind <kind> --split <split>` (~70 min per split); restore under `data_root().parent` |
| LeanDojo corpus, pre-cutoff (archived) | re-download from Zenodo record 10929138 |
| LeanDojo corpus, post-cutoff (active) | `scripts/deduction/build_postcutoff_corpus.py`; see `notebooks/deduction/README.md`, "Data bootstrap" |
| `postcutoff_names_<target-date>.json` declaration lists | `scripts/deduction/postcutoff_names.py` (network + a GitHub token; not cheap -- see below) |
| Evidence trees (`results/**`, `EVIDENCE.json` manifests, raw generations, logs) | NOT regenerable -- live GPU measurements; the archive is the record |
| Analysis writeups, correction verdicts, probe scripts | NOT regenerable; their live conclusions are in the code they shaped (`smolbench.evals.providers.ec2.DETERMINISM_ARGS`, the streaming transport, `notebooks/statistical_analyses.ipynb`) |

Nothing regenerable is tracked under `notebooks/` or `scripts/`.

`notebooks/deduction/postcutoff_names_2026-06-03.json` (sha256
`ff541bbccc8a5fa5ccab7e0a3d3c6559d5917956b022cd192e3be2806754669e`, 1,582,143
bytes / 36,474 lines) regenerates with:

```bash
.venv/bin/python scripts/deduction/postcutoff_names.py \
    --old 97f12126beb5c05c4354bc7d8cb0dc3cce1da7e7 \
    --new 2ca39e62989124794bd8405bb2e60805f63d37bc \
    --target-date 2026-06-03 \
    --out notebooks/deduction/postcutoff_names_2026-06-03.json \
    --workdir <scratch dir> --github-token <token or $GITHUB_ACCESS_TOKEN>
```

This needs network access and a GitHub token: the script's only network calls
go through `fetch_pr_created_at`, which resolves each candidate declaration's
evidence date against the GitHub API. Regenerable, but not cheaply -- and the
result can drift if a PR's metadata changes, which is exactly why the sha256
above is recorded rather than assumed stable. It is expected to be attached to
a GitHub release the same way the S3 archives are (see "GitHub releases"
above); that has not happened yet for this file.
