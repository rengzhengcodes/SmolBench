# Archived regenerable artifacts (2026-08-25)

On 2026-08-25 a security review of every tracked file under `notebooks/` and
`scripts/` (150 files, archive members and notebook cell outputs included)
found no API keys, tokens, private keys, or personal data. Following that
review, the regenerable artifacts below were removed from the tree, zipped,
and attached to PR #4 as the release asset
`pr4-regenerable-artifacts/pr4_regenerable_artifacts_2026-08-25.zip`
(sha256 `1642cd34fc9466fc72bdc1cfe38b3cac6b946f0d549134310a9303ff5f33afae`).

| Removed file | Regenerate with |
|---|---|
| `notebooks/induction/EXTENS_VS_NOISE_REPORT.txt` | `.venv/bin/python notebooks/induction/extens_vs_noise.py` |
| `notebooks/induction/SIGNIFICANCE_REPORT.txt` | `.venv/bin/python notebooks/induction/significance_report.py` |
| `notebooks/deduction/ERROR_BARS_REPORT.txt` | `.venv/bin/python notebooks/deduction/error_bars.py` |
| `notebooks/deduction/HINT_VS_NOISE_REPORT.txt` | `.venv/bin/python notebooks/deduction/hint_vs_noise.py` |
| `scripts/arch/page_data.json`, `scripts/arch/model_architectures.html` | `.venv/bin/python scripts/arch/build_page.py` |

The four reports render from the 2026-08-16 S3 analysis snapshot
(`scripts/snapshot_analysis_data.py`; needs AWS credentials). The 2026-08-21
audit round reproduced `EXTENS_VS_NOISE_REPORT.txt` byte-identically.
The writeups that cite these reports by file and line number
(`FAMILY_LADDER_ANALYSIS_2026-08-16.md`, `DOJOINIT_RECOVERY_2026-08-18.md`,
`corrections_2026-08-21/*.json`) were themselves archived later the same day
(third archive, below); every citation between them resolves inside the
archive.

The arch atlas outputs rebuild from the tracked inputs (`arch_configs_raw.json`,
`arch_facts.json`, `annotations*.json`, `page_template.html`) with no network,
but note that `build_page_data.py` embeds the *current* `EC2_DEPLOY_SPECS`; the
archived copy records the fleet's as-served (pre-determinism-bundle) serving
arguments, so a fresh build differs in the per-model `vllm_args` block.

## Second archive: evidence tree, data sidecars, and their tests

Also on 2026-08-25, under the user's "all candidates" ruling, the following
were removed from the tree and attached to the same PR #4 release as
`pr4_evidence_and_data_2026-08-25.zip`
(sha256 `8d93a25afbf12c81b9846308034b122028ac3db047c9b4053942f42555b0e24a`):

- `notebooks/deduction/results/**` (52 tracked files): the determinism-
  certification packages (tp=4 / tp=8 / MoE-tp=8 hinges, regime-mean draw,
  DojoInit recovery, 2026-08-23 validation probe), their `EVIDENCE.json`
  manifests, raw generations, logs, and the five preserved scratch tarballs.
  These are live GPU measurements: they are NOT regenerable; the archive is
  the record.
- `notebooks/deduction/data/*` (4 files): `replay_passing_novel_premises_{val,test}.jsonl`
  (regenerate with `python -m smolbench.deduction.lean.cli filter`, ~70 min per
  split, needs `.venv-lean`) and `lean3_align.json.gz` + manifest (the Mathlib
  `#align` map asset). `smolbench.deduction.lean` resolves both off
  `data_root().parent`; restore them there before running the deduction study.
- Seven tests that pinned those files (`tests/archived_tests_2026-08-25.py`
  inside the zip): the four tracked-manifest tests and `tracked` fixture from
  `tests/tooling/test_evidence_manifest.py`, two sidecar-resolution tests from
  `tests/deduction/test_lean_corpus.py`, and `test_noise_rung_is_token_matched_to_its_hint_counterpart`
  from `tests/deduction/test_deduction_study.py`. The manifest *mechanism* tests remain.

### Where the archive lives, and how the gates run now

Both zips, the unpacked evidence tree, the data sidecars, and the LeanDojo
corpus (`leandojo_benchmark_4/`, 759 MB, previously an untracked local
download) are on S3 under
`s3://smolbench-results-414266451290/archives/2026-08-25/` (the zips at the
prefix root, the tree under `notebooks/deduction/`). The same two zips are
attached to PR #4 as release assets.

The seven tests moved out of the offline suite are re-homed in
`tests/deduction/test_s3_archive.py` against that prefix. They stream each object
into memory through `tests/conftest.py::S3Archive` and never write to a
local tree (user ruling 2026-08-25: archived data is accessed on AWS, not
pulled locally). They skip unless opted in:

```bash
SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/2026-08-25 \
    .venv/bin/python -m pytest tests/deduction/test_s3_archive.py -q
```

Last live run 2026-08-25: 7 passed (all four `EVIDENCE.json` manifests
verify byte-for-byte over S3, including tarball members).

## Third archive: analysis writeups, audit records, and correction verdicts

Also on 2026-08-25, the 19 non-code record files under `notebooks/` left the
tree for `pr4_notebook_records_2026-08-25.zip`
(sha256 `e05eff9840c167cdad0387190768ae1bc4c1d4b1432cf0ff0370236c9bbaf889`;
on the PR #4 release and at the S3 prefix root, with each file also stored
individually under `notebooks/` at the prefix):

- `notebooks/CONTAMINATION_INVENTORY_2026-08-15.md`, `DEDUCTION_COVERAGE_DIAGNOSIS_2026-08-16.md`,
  `DETERMINISM_PLAN_2026-08-16.md`, `DOJOINIT_RECOVERY_2026-08-18.md`,
  `FAMILY_LADDER_ANALYSIS_2026-08-16.md` (the study's final analysis
  writeup; its published form is the "Corrected Ladders" artifact from
  `3bcc1519`), `PASS_AT_1_REVIEW_PLAN_2026-08-16.md`;
- `notebooks/corrections_2026-08-21/*.json` (8 files): the 2026-08-21
  adversarial-verification rounds, the applied-edits log, S3 re-gates, token-
  matching re-verification, the gemma-4-e2b probe verdict, and two EC2
  provisioning stubs. Every accepted correction in them was applied at
  `3bcc1519`; nothing in them is pending;
- `notebooks/induction/CONFOUND_AUDIT_2026-08-13.md`, `MULTIPLICITY_CMH_VARIANTS.md`,
  `MULTIPLICITY_PLAN.md`, `PAIRED_ANALYSIS_RESULTS.md`, `POWER_ANALYSIS_2026-08-14.md`.

Before archiving, each finding those records establish that the driver
notebooks did not yet state was written into the notebooks themselves
(`induction_eval.ipynb`: as-designed-vs-as-served roster note, the noise-arm
collapse census, the 2026-08-18 config epoch, the earliest-wins selection
rule and the Holm 119/210 headline, the prospective-only status of
`power_analysis.py`; `lean_eval.ipynb`: the config epoch, the 944-cell lane
and 111-unmeasurable-cell denominator, and that `error_bars.py` -- not
`power_analysis.py` -- produces the published 14/21). Docstrings across
`smolbench/`, `scripts/`, `notebooks/*/*.py` and `tests/` still cite these
records by name as provenance; those citations point here.

Security: the 19 files were scanned before archiving -- no keys, tokens,
emails, or personal data; only terminated EC2 instance IDs, four ephemeral
public IPs, and the account ID already present in this README.

## Fourth archive: concluded probes, incident launchers, and the statistics they carried

Also on 2026-08-25, 17 files under `scripts/` and the 4 test modules that
only loaded them left the tree for `pr4_scripts_2026-08-25.zip`
(sha256 `c75e6e013e49cd583e465914006e9bbb2713e2aa64f76924792db03e469fd677`;
on the PR #4 release and at the S3 prefix root, each file also stored
individually under `scripts/` and `tests/` at the prefix):

- Concluded determinism / delivery probes: `hinge_probe.py`, `tp4_hinge_probe.py`,
  `tp8_hinge_probe.py`, `moe_tp8_probe.py`, `hardware_equivalence_probe.py`,
  `delivery_probe.py`, `streaming_ab_probe.py`, `keepalive_ab_probe.py`,
  `tp8_hinge_summary.py`. Their findings are the determinism bundle that is
  now `smolbench.evals.ec2.DETERMINISM_ARGS` (the default config) and the
  streaming transport; their reports are in the evidence archive above.
- 2026-08-14/16 incident-response launchers: `launch_gemma12b_deduction_shards.sh`,
  `relaunch_damaged_deduction.sh`, `resume_all_runs.sh`,
  `supervise_deduction_lane.sh`; and the 2026-08-18 `recover_dojoinit_std.py`
  recovery (all 21 lanes done; its report is in the evidence archive).
- The three statistical scripts: `posterior_power.py`, `flip_probe.py`,
  `flip_free_bound.py`. Their statistics now live in
  **`notebooks/statistical_analyses.ipynb`**, the single notebook of this
  study's analyses: it imports the live analysis modules
  (`notebooks/{induction,deduction}/*.py`, `_power_common.py`) for the
  sizing, paired, significance, error-bar and hint-vs-noise sections (gated
  behind `RUN_HEAVY`, since they need the results store), ports the
  posterior DECIDED/EQUIVALENT/UNDECIDED classifier (§7, with an ungated
  self-test), and re-renders the §6.2 flip rate (0.0950, CP95 [0.058, 0.144])
  and §6.3 free bound (3/74) from the archived JSON streamed off S3 (§8-9),
  asserting equality with the stored numbers. The notebook never writes
  archived data to a local path; the only local materialisation is the
  gated `aws s3 sync` of the analysis snapshot that `error_bars.build_pool`
  needs as a directory. Outputs are committed cleared.
- Tests archived with them: `tests/test_delivery_probe.py`,
  `test_determinism_probes.py`, `test_flip_probe.py`, `test_recover_dojoinit.py`
  (116 tests; the offline suite is 1104 passed / 7 skipped after the move).

Kept in `scripts/` (live tooling): the `arch/` atlas pipeline, `run_fleet.py`,
`fleet_status.py`, `fleet_teardown.py`, `run_shards.py`, `merge_lean_shards.py`,
`split_lean_run_into_shards.py`, `lean_verify_rows.py`, `audit_run_completeness.py`,
`regrade.py`, `snapshot_analysis_data.py`, `provision_results_bucket.py`,
`evidence_manifest.py`, `bedrock_smoke.py`, `ec2_lifecycle_smoke.py`.
`smolbench/evals/ec2.py`'s provenance notes that named `hinge_probe.py` now
point here. Security: all 21 files scanned -- no secrets or PII (cloud IDs
only).

Nothing under `notebooks/` or `scripts/` is now regenerable-and-tracked.
