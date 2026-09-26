# Plan: Horn bench on the family-ladder roster (single context, no tools)

Goal. Run the fixed Horn setup (`smolbench/deduction/horn/README.md`) on the same 21 models
and serving path as the induction study, as plain chat completions: one prompt, one
thinking answer, no tools, no file reading.

## What stays identical to induction / the Lean B200 sweep
- Roster: the 21 checkpoints in `smolbench/evals/study_config.toml` (7 families x 3 rungs),
  same pinned revisions, tags and ladder order.
- Serving: vLLM via `providers/ec2.py` recipes (reasoning parsers, thinking toggles from
  `COT_ARGS`: `enable_thinking` / DeepSeek `thinking` / Ministral prompt template), one
  shared 131,072-token context for every model.
- Sampling: temperature 0.7, 3 replicates per prompt (pass@1 = mean of 3, pass@3 = any),
  paired by theory seed.
- Request: system = the Horn `SYSTEM` string; user = `prompt.md` verbatim.
- Results: JSONL rows with raw response, reasoning/answer split, finish_reason, usage;
  spooled to `s3://smolbench-results-414266451290/deduction_horn/<run>/` every few minutes.

## What changes
- Task: Horn theories instead of Lean theorems. Scorer: `smolbench.deduction.horn.checker`
  on the last contiguous block of `derive` lines after the thinking is stripped.
- Output cap: 32,768 tokens inside the 131k window (decided 2026-09-25). The Lean run left
  output uncapped and reasoning models spent hours on `length` failures. `finish_reason =
  length` scores as a failure and is reported separately.

## Design
The four arms of the fixed setup, token-matched within a rung: `lem`, and `pad`, `disc`,
`both` at about four times its tokens. A rung is its chain length m (m chain lemmas,
5 m open alternatives, depth-2 trees; `lem` is about 80 tokens per chain lemma). Thirty
theories (seeds 100-129) x 3 replicates x 4 arms = 360 requests per model at the model's
chain length.

Primary contrast: `both − pad` (usable derivations vs filler of equal length). Controls:
`both − disc` (not rule-shaped text or dead same-head candidates), `pad − lem` (length).
(`junk` was dropped 2026-09-26: level with lorem for Haiku, and as costly as `disc` for a
non-thinking model, so `disc` carries the rule-shaped control.) Per-model analysis: seed-paired contrasts with bootstrap CIs and the
exact sign-flip test; Holm across the 21 models as in
`notebooks/induction/analysis/significance_report.py`. Family ladders (effect vs scale) as
in the induction figures.

## Difficulty differs by model: a per-model chain length
The same theory is easy for a 397B model and out of reach for a 2B one, and a contrast
measured at floor or ceiling says nothing. The Haiku result shows the effect grows with the
chain length: −10 points at m = 12, −50 at m = 48, with the same library size and tokens.

1. A difficulty ladder rendered once for everyone: chain length m in {3, 6, 12, 24, 48, 96,
   192} (`roster/m<m>`, seeds 100-129). Library composition is fixed per chain level, so the
   arms stay matched within a rung and m scales chain, search space and tokens together
   (`lem` 0.4k to 15k tokens, the other arms 1k to 58k).
2. A two-stage run per model, with the level chosen from the control arm on disjoint seeds:
   - Stage 1, calibration (`scripts/deduction/horn/calibrate_m.py`): a smart search with
     10 theories per level (seeds 200-209): start at a prior taken from the closest
     calibrated relative (same family, nearest size), step up the ladder m in {1, 2, 3, 4,
     6, 8, 10, 12, 16, 20, 24, 32, 48, 64, 96, 192} while more than 8 of 10 pass and down
     while fewer than 7 pass; stop at 7-8 of 10 (2-3 failures), when bracketed, or at the
     ladder's end; pick the level nearest the 75% crossing of a logistic fit over the
     levels run. Typically 2-3 levels, 20-30 requests per model (decided 2026-09-26; the
     first seven models had run the full ladder with 30 theories per level and keep those
     picks). A model under the band at m = 1 is below floor and runs at m = 1 for the
     record.
   - Stage 2, the full benchmark: the four arms at the chosen level, seeds 100-199 x 3
     replicates (1,200 requests per model; raised from 30 theories on 2026-09-26).
   The selection uses `lem` only on seeds no contrast cell shares, so it cannot bias the
   contrast. The rule is fixed before the run.

Analysis reports `both − pad` at each model's matched level (primary; Holm across models)
and, as a check that the choice of level does not drive the result, a pooled model with
model x level x arm terms over every level a model ran. Models below floor are listed, not
silently dropped.

Size: about 21 models x (20-30 calibration + 1,200) requests, about 26,000. One p6-b200 block (23 h) held about 4,500
requests x 21 models at up to 58k-token prompts with uncapped output in the Lean run, so
this fits in one block with margin.

## Pilot (before any full launch)
Four models spanning the ladder (gemma-4-e2b, qwen3.5-27b, glm-4.7-flash, qwen3.5-122b-a10b):
stage 1 on all four, then stage 2 on the matched level. Check: answers parse (thinking
stripped, last derive block found), finish_reason distribution under the cap, the spread of
matched levels across the ladder. Full launch waits for an explicit go.

## Rungs to render
| rung | m | seeds | arms |
|---|---|---|---|
| `roster/m<m>` for m in 3, 6, 12, 24, 48, 96, 192 | as named | 100-129 | lem, pad, disc, both |
| `calib_m<m>` for the same m | as named | 200-229 | lem |

`M=<m> SEED0=100 NSEEDS=30 scripts/deduction/horn/render_rung.sh roster/m<m>`, and
`M=<m> SEED0=200 ARMS=lem ... render_rung.sh calib_m<m>`. The rungs used for the Haiku
result were token-fitted (5k / 25k) and are archived; nothing from them is reused.

## Bedrock
Bedrock (us-east-2) serves 7 roster models exactly: zai.glm-4.7-flash, zai.glm-4.7,
nvidia.nemotron-nano-3-30b, nvidia.nemotron-super-3-120b and the three
mistral.ministral-3-*-instruct checkpoints (instruct, no thinking; the vLLM roster uses the
Reasoning-2512 variants). `bedrock_sweep.py` runs a rung over the Converse API;
`reasoning_effort: high` switches thinking on for GLM-4.7 and Nemotron-3 (`low` yields no
reasoning content at all on these models, so it is not a thinking mode). Bedrock runs use a
131,072-token output cap (decided 2026-09-25; Bedrock accepts it on all four thinking
models) so that thinking is never cut. The other 14 models need the vLLM box.

## Driver
`scripts/deduction/horn/sweep.py`: one chat completion per cell (system.md + prompt.md),
`max_tokens` 32768, temperature 0.7, the roster model's thinking arguments, resumable JSONL
rows scored with the checker; `length` finish reasons score as failures. Tested against a
stub OpenAI-compatible server (`tests/deduction/test_horn_sweep.py`). Serving order and
box setup: `scripts/deduction/packed_box.py` (small models first, then 2/4/8-GPU).
