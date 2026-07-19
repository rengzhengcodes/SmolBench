# Lean portion of SmolBench — change summary

A README-style summary of everything added to or changed in the Lean 4 part of
SmolBench since the original eval harness landed (`546fcdd`, 2026-06-03),
through the CoT-recipe gate run of 2026-07-13/14. The companion
[README.md](README.md) is the *runbook* (how to run each stage); this document
is the *inventory and narrative* (what exists, why it was built, what was
learned). File references are repo-relative.

## Timeline at a glance

| Date | Milestone |
| --- | --- |
| 2026-06-03 | Original harness: progressive-context Lean 4 theorem proving eval (`smolbench/deduction/lean/`) |
| 2026-07-06/07 | Refactor into package modules; run-smolbench skill; SFT groundwork (`sft.py`, first trainer) |
| 2026-07-09/11 | Training infrastructure: spot trainer boxes, staged QLoRA, capacity blocks; Qwen3-235B 4-way LoRA cohort trained + pilot-evaled — **synthetic-pretraining signal: null** |
| 2026-07-12 | Root-cause research (SFT-recipe deep research + failure taxonomy); CoT-recipe round-1 infra; 8k CoT annotation on DeepSeek V3.2; anti-Lean3 repair mix-in (L3R); 500 handcrafted reasoning chains |
| 2026-07-12/13 | Both 8k smoke arms (bare-r128 / cot-r128) trained on 8×H200; r128 LoRA serving fix |
| 2026-07-13/14 | Pre-registered 3-arm improvement gate (300 theorems, pass@4, McNemar) — run in flight |

## 1. The eval harness (`smolbench/deduction/lean/`)

The June harness evaluated single models on step-k / hint / noise context
rungs against traced mathlib4 theorems (LeanDojo verification). Changes since:

- **Package refactor** (`5f3d483`, `e52cff7`): inlined logic split into
  `runner.py` (generation + Dojo verification loop), `prompt.py`, `context.py`,
  `corpus.py`, `premises.py`, `cli.py`, `verify.py`, `figures.py`. Behavior
  pinned by the offline test suite as it moved.
- **`sft.py`**: builds SFT rows from traced proofs (tactic-tail targets keyed
  by `(full_name, k)`), shared by every dataset builder below.
- **`decontam.py`**: content-level decontamination (K1–K4 keys: canonicalizes
  metavariable / autoname / universe counters so alpha-equivalent states
  collide) with a `HoldoutIndex` used by every training-data builder — nothing
  that matches an eval-holdout state at K1–K4 may enter a training set.
- **`lean3.py`**: 6-kind Lean 3 relic *detector* (`find_relics`) and 5-transform
  inverse *corrupter* (`corrupt_tail`) with a structurally-enforced
  shared-vocabulary invariant; powers the L3R repair dataset (§4) and the `l3`
  column in run analysis. Backed by a 130,752-pair `#align` map asset
  (`notebooks/lean/data/lean3_align.json.gz`, built by
  `scripts/build_lean3_align_map.py`).
- **Multi-rollout eval**: `--n-rollouts` with per-rollout seeds; every rollout
  is Dojo-verified at sweep time. Analysis (`cmd_analyze` in
  `scripts/lean_ec2_sweep.py`) reports pass@N plus a truncation metric that
  fires on unclosed `<think>` in content or reasoning-only replies.
  `extract_tactic_block` strips a leading closed think block; unclosed → empty.

## 2. Training infrastructure (`scripts/`)

- **`lean_lora_sft.py`** — QLoRA trainer (4-bit NF4 base, LoRA adapters).
  Grown across the cohort runs: staged training via `--init-adapter` (stage-2
  anneal on real data on top of a synthetic stage-1), `--extra-dataset`
  (aux rows ride on top of `--max-examples`, resume-safe), configurable
  `--lr-scheduler-type/--warmup-ratio`, and the trl `loss_type="nll"` fix
  (trl ≥1.7's `chunked_nll` default crashes on device-mapped quantized models;
  version-guarded via a dataclass-fields probe).
- **`lean_train_ec2.py`** — spot GPU box provisioner for training, S3
  checkpoint round-tripping, `OPTIONAL_DATASETS` threading, and the **capacity
  block** subcommands (`cb-search` / `cb-purchase` / `cb-status`, plus
  `provision --capacity-reservation`) for interruption-free multi-day windows.
  Purchases are deliberately user-gated with a no-retry client.
- **`lean_qwen_4way.sh`** — cohort orchestrator (real-only / goedel ×2 stages /
  leannav ×2 stages) with S3-head completion checks so re-runs skip finished
  stages, and a self-halt after the final stage.
- **`lean_cot_recipe.sh`** — round-1 CoT recipe orchestrator: paired
  `bare8k-r128` / `cot8k-r128` smoke stages, `FULL=1` trio stages, `L3R` env
  to mix in the repair dataset (`-l3r` stage-name infix keeps S3 checkpoints
  from cross-resuming), `DRYRUN=1` resolution mode.
- **`build_lean_sft.py` / `build_lean_synth_sft.py`** — real (novel-premises
  stepk-1, decontaminated) and synthetic-pretrain (Goedel-V2, LeanNavigator,
  24k each) dataset builders, seeded subsamples + manifest sidecars.
- **`nemo_convert_data.py`** + `data/sft/nemo/` — NeMo-format export for the
  (fallback) Nemotron-Ultra NeMo pipeline.
- **`requirements-train.txt`** — pinned training stack (lesson: unpinned trl
  drifted between boxes and broke SFTTrainer nondeterministically).

## 3. Serving & eval at scale

- **`scripts/lean_ec2_sweep.py`** — the serve-swap eval driver: provisions one
  vLLM spot box (BF16 Qwen3-235B at TP=8, `--enable-lora`), swaps
  base/adapter arms in place, runs the harness against each arm, records
  every cell to `all_rows.jsonl` (append-only, resume-safe). Added phases:
  `cot-gate` (the pre-registered gate), `expert-iter` (pass@8 harvest on the
  train split, `source=with_proof` only), `--cot-smoke` arm table,
  `--limit/--n-rollouts/--theorem-workers/--no-teardown`.
- **r128 LoRA serving fix**: BF16 235B at TP=8 leaves ~30 MiB/GPU free after
  weight load; vLLM's rank-128 LoRA buffer (128 MiB) OOMs in
  `_create_lora_modules` (r16's 16 MiB just fit, which is why earlier pilots
  worked). Fix: `--fully-sharded-loras` (shards buffers across TP ranks),
  applied automatically when `lora_rank >= 64`. Not a vLLM version issue
  (reproduced on v0.23.0 and v0.25.0).
- **`smolbench/evals/ec2.py`** hardening along the way: user-data payloads
  extracted to byte-exact asset files (16 KB user-data budget with a canary
  test), idle watchdog on every box, and scoped-credential tolerance
  (`_ensure_bucket` accepts HEAD→403 on our own account-suffixed bucket;
  `ensure_instance_profile` returns early on IAM AccessDenied) so a
  restricted operator key can drive everything up to `RunInstances`.
- **`scripts/harvest_expert_iter.py`** — converts expert-iteration sweep rows
  into new SFT items for a future round.

## 4. Datasets (`notebooks/lean/data/`)

JSONLs are gitignored where large; manifests + QC sidecars are committed.

| Dataset | Contents | Provenance |
| --- | --- | --- |
| `sft/novel_premises_train_stepk1[_decontam]` | real tactic-tail SFT from traced proofs | `build_lean_sft.py`, decontam-gated |
| `sft/synth_goedel_v2_24k`, `sft/synth_leannavigator_24k` | synthetic-pretrain stage-1 corpora | `build_lean_synth_sft.py` |
| `sft/cot_stepk1_think_8k` + `sft/cot_stepk1_bare_8k` | **7,305 paired rows**: CoT-annotated targets and byte-identical bare-tail control siblings (same `(full_name,k)` keys) | `annotate_lean_cot.py` (§5) |
| `sft/lean3_repair_stepk1_1k6` | 1,600 corrupted→repair + 160 identity rows | `build_lean3_repair_sft.py`; detector-anchored errors |
| `handcrafted/unrelated_500` | 500 trace/tactic-disjoint handwritten instances + think-style SFT rows | audited by 13 independent reviewers; `verify_handcrafted_lean.py` |
| `lean3_align.json.gz` | 130,752 Lean3→Lean4 `#align` pairs | `build_lean3_align_map.py`, byte-reproducible |

## 5. CoT annotation pipeline (`scripts/annotate_lean_cot.py`)

Bedrock Converse via boto3 (the smolbench `aws` eval provider cannot reach
this path), temperature 0, prompt-template hash recorded in the manifest as
the reproducibility anchor (Converse has no seed parameter). Append-only
output keyed by `(full_name, k)` makes it resume-safe; the bare-control
sibling is emitted from the final file's keys so pairing survives QC drops.

- **Annotator selection** was adversarial: DeepSeek-R1 was rejected after two
  independent reviews (fluent rationales that confabulate lemma statements
  and inequality directions — the worst possible training signal);
  **DeepSeek V3.2** won head-to-head and is the default.
- **Confabulation containment**: three rounds of prompt hardening
  (copy hypotheses verbatim, never assert lemma statements from memory,
  term-mode abstention) plus a mechanical hedging QC gate (`_HEDGING_RE`)
  and size/markup/restatement gates. At 8k scale: 8.6% drops
  (hedging 529 / too-long 111 / restatement 45 / markup 2), then a
  post-filter removed 8 rows whose rationale cited an eval-holdout name
  absent from the proof tail. Final faithfulness sample: 1 major / 20.
- Cost: ~$10–15 for the full 8k pass.

## 6. Research findings (`notebooks/lean/research/`)

- **The null that started it** (Qwen3-235B 4-way pilot, 2026-07-11): all LoRA
  arms beat base, but synthetic pretraining added nothing over real-only
  (McNemar p > 0.5 everywhere) and the best arm reached only 17/77.
- **`2026-07-12_sft_recipe_deep_research.md`**: diagnosis — bare tactic-tail
  targets *trained away* the base model's chain-of-thought (outputs collapsed
  ~5k → ~15 tokens). Evidence-ranked fixes: CoT targets > expert iteration +
  compiler feedback > LoRA rank ≥128 > pass@N eval > curation.
- **`2026-07-12_failure_taxonomy.md`** (self-verifying report): base-model
  failures ≈50% compilation-class (Lean 3 syntax leakage) + ~40% misapplied
  tactics; SFT-arm failures shift to hallucinated Mathlib names and bare-`simp`
  single-step myopia — both are exactly what reasoning-before-answer
  suppresses, independently confirming the CoT fix. Also motivated L3R.
- **Power analyses**: `scripts/lean_gate_power.py`. Key caveat: pass@8
  *saturates* at realistic solve rates, making McNemar power worse than
  pass@1 — gate sizing must be calibrated from empirical rollout rates, not
  defaults. The empirical calibration (frac_solvable ≈ 0.31, mean p|solvable
  ≈ 0.44) sized the gate at pass@4 × 300 theorems: 88% power at +8 pt
  per-rollout delta.

## 7. Experiments run

1. **Trio pilot** (`results/runs/lean_trio_pilot/`): llama-31-405b /
   nemotron-ultra-253b / qwen3-235b-a22b, base vs r16 real-only LoRA. All
   LoRAs help (405B 3.7×); absolute rates low.
2. **Qwen 4-way** (`results/runs/lean_qwen4way_pilot/`): real-only vs
   goedel-staged vs leannav-staged. Synthetic signal null (§6) → Nemotron/405B
   full-trio training deliberately **not** committed pending a better recipe.
3. **8k smoke arms** (2026-07-12/13, p5e 8×H200, ~$500): `bare8k-r128`
   (loss 2.28→0.57) and `cot8k-r128` (1.02→0.48), 914 steps each, adapters in
   S3. Calibration confirmed the CoT format trains in (~320-token outputs,
   zero truncation — no more 15-token collapse).
4. **Pre-registered improvement gate** (`results/runs/lean_cot_gate/`,
   design in `PREREGISTRATION.md`): 300 seeded validation theorems ×
   4 rungs × 4 rollouts × 3 arms (base / bare-r128 / cot-r128); unit =
   (theorem, k, rung) group; outcome pass@4; GREEN iff cot > bare AND
   cot > base, one-sided exact McNemar α=0.05 each; exceptions = missing.
   **RESULT (2026-07-18): RED** — see `results/runs/lean_cot_gate/RESULTS.md`.
   cot-r128 did not beat bare-r128 (−1.3pt pass@4, p=0.80); its edge over
   base (+3.2pt, p=0.049) is attributable to the shared r128 recipe, since
   bare-r128 ALSO significantly beats base (+4.3pt, p=0.017) — reversing the
   original r16 null. The gain concentrates in the stepk:1 rung
   (0.145 → 0.329/0.272); hint/noise rungs are flat. No CoT output collapse.
   Per the pre-registered follow-up, RED on Qwen attention-only is not
   decisive for the dense trio arms: next step is the dense fenced
   micro-smoke; expert iteration on the working bare-r128 recipe is the
   secondary round-2 axis.

## 8. Results-integrity rules learned the hard way

- The sweep's resume logic **replays recorded exception rows**. Infra-caused
  exceptions (Dojo cache eviction "Unexpected EOF", dead inference endpoint,
  transient `BlockingIOError`) must be purged from `all_rows.jsonl` before
  relaunch or the affected cells are lost to the analysis forever. Genuine
  `DojoTacticTimeoutError` rows stay (pre-registered as missing data).
- The traced-mathlib `std` package build gets evicted from the LeanDojo cache
  by an unidentified process; a missing build makes *every* Dojo init fail.
  A rebuild guard (`lake build`, ~1 min) runs alongside any long sweep.
- Seeds are never dropped to dodge provider errors (repo policy: seeded,
  reproducible evals); generated state/results live inside the repo, anchored
  via `__file__`.

## 9. Test coverage

Everything above is pinned by the offline suite — from 183 tests before the
lean training work to **489+ tests** across both venvs (`.venv` 3.14 and
`.venv-lean` 3.12) at the time of writing: dataset builders, decontam keys,
Lean3 detector/corrupter invariants, annotator QC gates, sweep arm tables,
trainer argument plumbing, EC2 payload byte-budgets, and provisioning
credential-fallback paths.
