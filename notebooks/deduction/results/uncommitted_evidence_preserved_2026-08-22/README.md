# Uncommitted run evidence — preserved 2026-08-22 by the adversarial-verification session

These tarballs are byte-copies of the PRODUCING session's ephemeral scratchpad
(/tmp/claude-1001/-workspace-SmolBench/e02d645d-a971-4770-ad99-4f84f96cc96e/scratchpad/),
taken because the determinism-bundle writeups cite artifacts that exist ONLY there
(preregistered_framing.md, pool_analyze.py, by_process.py, keys_before_box3.json,
keys_full.json, the true 200-cell all_rows_leg2_full_raw.jsonl.gz, drift_gate_pre.json,
env.sh, server_config_box3_vs_box4_diff.json, backup_pre_r6/, teardown scripts,
spot_price_actual.txt, run logs, ...) and /tmp is subject to cleanup.

- r4-tp4hinge  -> tp=4 hinge package  (commit 4d5dee14)
- r5-regime    -> regime-mean leg-2 extension n=311  (commit f9a3e5db)
- r6-regime    -> regime-mean full draw n=399  (commit cbc3c862)
- r6-tp8       -> tp=8 dense hinge  (commit 6f411981)
- r7-moe-tp8   -> MoE-at-tp8 package  (commit e3068d21)

NOTE: preservation of content only. The anti-HARKing value of preregistered_framing.md's
"fixed before grading" timestamp cannot be restored retroactively — its mtime lived in a
mutable temp dir. This directory was force-added and committed on 2026-08-23 (user-approved).
