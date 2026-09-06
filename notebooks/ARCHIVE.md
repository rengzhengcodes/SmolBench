# Where the historical artifacts live

Result trees, evidence packages, data sidecars, analysis writeups, and
concluded probe scripts are not kept in this tree. They live in two places,
and docstrings across the repo that cite `notebooks/README.md` or
`notebooks/ARCHIVE.md` as provenance mean this file.

## S3

Everything is under `s3://smolbench-results-414266451290/` (`us-west-2`):

| Prefix | What |
| --- | --- |
| `<study>/<model>/seed=<seed>/<info>--<run_ts>.yaml` | the live append-only experiment log (`smolbench.evals.results_store`); reads are earliest-wins over runs not retired by a sibling `.superseded` marker (see below) |
| `deduction_postcutoff/runs/scaling_<spec-key>/` | the re-collection's per-lane deduction spools (`all_rows.jsonl`, `verified_rows.jsonl`); the prefix `rows_source.spool_prefix()` -- and every reader in the tree -- defaults to |
| `deduction_postcutoff/runs/dojoinit_recovery_2026-08-18/<lane>/recovered_rows.jsonl` | the DojoInit recovery rows for the post-recovery sensitivity pool; read by `scripts/results/audit_lean_pinning.py` (layer 5, `RECOVERY_RUN`/`fetch_recovery`), `notebooks/deduction/analysis/error_bars.py --recovery-dir`, and `statistical_analyses.ipynb`'s Section 5, which fetches these rows through `rows_source.resolve_rows_dir` and computes the post-recovery sensitivity pool from them; the same tree also sits inside the `archives/2026-08-25/` unpacked evidence below |
| `deduction/runs/scaling_<spec-key>/` | the PUBLISHED PRE-CUTOFF study's per-lane spools; `rows_source.spool_prefix()` and `runner.spool_prefix()` both REFUSE to resolve this prefix unless `LEAN_ALLOW_LEGACY_PREFIX=1` is set, so a reader has to opt in on purpose before landing here |
| `analysis/<date>/` | frozen analysis snapshots (`scripts/results/snapshot_analysis_data.py`); nothing requires one anymore -- the deduction report scripts take a `--s3 [PREFIX]` (via `rows_source.resolve_rows_dir`) and fetch rows straight off the live spool into scratch instead |
| `archives/<date>/` | dated archives of what left the tree: zips at the prefix root, plus the unpacked evidence tree, data sidecars, LeanDojo corpus (`notebooks/deduction/`), record files (`notebooks/`), and concluded scripts/tests (`scripts/`, `tests/`) |
| `archives/2026-08-30/notebooks/induction/audits/` | the three concluded induction audit probes (`check_currency.py`, `verify_survivorship.py`, `response_audit.py`); also `pr4_induction_audits_2026-08-30.zip` on the PR #4 release |

Paths inside an archive are the flat layout of the tree on the day it was
taken; they are never rewritten to match today's grouped layout.

A run in the live log is retired, never edited or deleted in place. On S3,
`S3ResultsStore.supersede` writes a sibling marker key beside the run it
retires -- the same key with its `.yaml` swapped for `.superseded`
(`S3_SUPERSEDED_SUFFIX`) -- whose body is a JSON object
`{"superseded_at": ..., "reason": ...}`; `list_runs`, `load_marks` and
`sync_down` all skip any run_ts carrying such a marker and then apply
earliest-wins (the lexicographically-least, hence chronologically-earliest,
surviving `run_ts`) over what is left. The local replicate trees mirror this
with a rename instead of a sibling key: `LocalResultsStore.supersede` renames
a retired `rep_<seed>.yaml` to `rep_<seed>.SUPERSEDED-<run_ts>.yaml`
(`LOCAL_SUPERSEDED_INFIX`), and every local reader already ignores a name in
that shape: `list_seeds` skips it because its seed portion fails the `int()`
parse, while `load_marks`/`exists` never even look at it, since both address
a replicate by the literal `rep_<seed>.yaml` path built from the seed number,
which a renamed file no longer matches. `scripts/results/regrade.py`
retires a run the same way: it goes through `ResultsStore.regrade`, which
supersedes every surviving run at an address first and only then appends the
replacement, and that replacement's `regraded_from` field names the `run_ts`
of the run it replaced -- the old refusal-to-regrade path is gone, on both
backends.

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
archive tag). The `pr4-regenerable-artifacts` release has 5 assets, but its
release notes carry sha256s for only 2 of them; the other 3 were posted only
in PR #4's issue comments. The evidence tree these zips hold is marked NOT
regenerable in "What is regenerable, and what is not" below, so its integrity
hash -- the only way to tell a good copy from a corrupted one -- needs a
durable home in the tree itself, not only in a release body or a PR comment
thread. This file is that home, for all five assets on the release:

| Asset | Date | Size (bytes) | sha256 | Contents |
| --- | --- | --- | --- | --- |
| `pr4_regenerable_artifacts_2026-08-25.zip` | 2026-08-25 | 133314 | `1642cd34fc9466fc72bdc1cfe38b3cac6b946f0d549134310a9303ff5f33afae` | the four `*_REPORT.txt` files (`notebooks/induction/{EXTENS_VS_NOISE,SIGNIFICANCE}_REPORT.txt`, `notebooks/deduction/{ERROR_BARS,HINT_VS_NOISE}_REPORT.txt`) plus `scripts/arch/{page_data.json,model_architectures.html}` |
| `pr4_evidence_and_data_2026-08-25.zip` | 2026-08-25 | 7340725 | `8d93a25afbf12c81b9846308034b122028ac3db047c9b4053942f42555b0e24a` | `notebooks/deduction/results/**` (52 files) and `notebooks/deduction/data/*` (4 files), plus the 7 removed pinning tests as `tests/archived_tests_2026-08-25.py` |
| `pr4_notebook_records_2026-08-25.zip` | 2026-08-25 | 339362 | `e05eff9840c167cdad0387190768ae1bc4c1d4b1432cf0ff0370236c9bbaf889` | the 19 non-code record files under `notebooks/` (dated analysis/plan writeups, the `corrections_2026-08-21/` verdict and re-gate JSONs, five induction audit/multiplicity docs) |
| `pr4_scripts_2026-08-25.zip` | 2026-08-25 | 151482 | `c75e6e013e49cd583e465914006e9bbb2713e2aa64f76924792db03e469fd677` | 17 files under `scripts/` (concluded determinism/delivery probes, the 2026-08-14/16 incident launchers, `recover_dojoinit_std`, and the three statistical scripts `posterior_power` / `flip_probe` / `flip_free_bound`) plus the 4 test modules that only loaded them |
| `pr4_induction_audits_2026-08-30.zip` | 2026-08-30 | 5558 | `f5a3079c34656862ccff7c08a5548a6aa76863f1bda93a4d2b67005f4655eccf` | the three concluded induction audit probes `notebooks/induction/audits/{check_currency,response_audit,verify_survivorship}.py` -- same zip named in the S3 table above |

All five are mirrored in S3 next to the unpacked archive: the first four
under `archives/2026-08-25/`, the induction-audits zip under
`archives/2026-08-30/` (see the S3 table above).

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
