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

Deliberately NOT archived: `notebooks/deduction/results/**` (measured evidence
pinned by `EVIDENCE.json` manifests, which `tests/test_evidence_manifest.py`
enforces) and `notebooks/deduction/data/*` (harness inputs loaded by
`smolbench.deduction.lean`, pinned by `tests/test_lean_corpus.py`).
