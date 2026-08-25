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
Writeups in this directory (`FAMILY_LADDER_ANALYSIS_2026-08-16.md`,
`DOJOINIT_RECOVERY_2026-08-18.md`, `corrections_2026-08-21/*.json`) cite
these reports by file and line number; those citations refer to the archived
copies.

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
  `tests/test_evidence_manifest.py`, two sidecar-resolution tests from
  `tests/test_lean_corpus.py`, and `test_noise_rung_is_token_matched_to_its_hint_counterpart`
  from `tests/test_deduction_study.py`. The manifest *mechanism* tests remain.

### Where the archive lives, and how the gates run now

Both zips, the unpacked evidence tree, the data sidecars, and the LeanDojo
corpus (`leandojo_benchmark_4/`, 759 MB, previously an untracked local
download) are on S3 under
`s3://smolbench-results-414266451290/archives/2026-08-25/` (the zips at the
prefix root, the tree under `notebooks/deduction/`). The same two zips are
attached to PR #4 as release assets.

The seven tests moved out of the offline suite are re-homed in
`tests/test_s3_archive.py` against that prefix. They stream each object
into memory through `tests/conftest.py::S3Archive` and never write to a
local tree (user ruling 2026-08-25: archived data is accessed on AWS, not
pulled locally). They skip unless opted in:

```bash
SMOLBENCH_ARCHIVE_S3=s3://smolbench-results-414266451290/archives/2026-08-25 \
    .venv/bin/python -m pytest tests/test_s3_archive.py -q
```

Last live run 2026-08-25: 7 passed (all four `EVIDENCE.json` manifests
verify byte-for-byte over S3, including tarball members).

Nothing under `notebooks/` or `scripts/` is now regenerable-and-tracked.
