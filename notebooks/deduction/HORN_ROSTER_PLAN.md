# Plan: Horn bench on the family-ladder roster (single-context, no tools)

Goal. Run the valid Horn setup (one constant, every added line usable) on the same 21
models and serving path as the induction study, as plain chat completions: one prompt,
one thinking answer, no tools, no file reading.

## What stays identical to induction / the Lean B200 sweep
- Roster: the 21 checkpoints in `smolbench/evals/study_config.toml` (7 families x 3 rungs),
  same pinned revisions, tags and ladder order.
- Serving: vLLM via `providers/ec2.py` recipes (reasoning parsers, thinking toggles from
  `COT_ARGS`: `enable_thinking` / DeepSeek `thinking` / Ministral prompt template), one
  shared 131,072-token context for every model.
- Sampling: temperature 0.7, 3 replicates per prompt (pass@1 = mean of 3, pass@3 = any),
  paired by theory seed.
- Request: system = the Horn `SYSTEM` string; user = `prompt.md` verbatim. No "read the
  file" text, no chunking, no tool schema.
- Results: JSONL rows with raw response, reasoning/answer split, finish_reason, usage;
  spooled to `s3://smolbench-results-414266451290/deduction_horn/<run>/` every few minutes.

## What changes
- Task: Horn theories instead of Lean theorems. Scorer: `smolbench.deduction.horn.checker`
  on the last contiguous block of `derive` lines after the thinking is stripped.
- Output cap: the Lean run left output uncapped and reasoning models spent hours on
  `length` failures (nemotron 55-70% of cells). Proposal: `max_tokens` 32,768 inside the
  131k window; `finish_reason=length` scores as failure and is reported separately.
  (Decision needed.)

## Design
Theories: `n_constants=1`, `m=12`, `open_frac=1`, height 2 (the st_h2 recipe), fresh seeds
(`SEED0=100`). Every lemma fully unfolded.

Treatment (decided 2026-09-25): derivations below the facts. Review showed that `both`
adds relevant information as more candidates: every tree's root rule shares its lemma's
head, so `both` doubles the valid rules per chain head (st_h2: 6.8 -> 13.7) and for the
goal (6.4 -> 12.8), and multiplies distinct predicates 10x (138 -> 1,376). "More valid
choices" alone predicts the lem / lem25 / both ordering (93 / 79 / 63). The `deep` arm adds
relevant information without that: every given fact stays given and also gets a derivation
(a depth-2 tree whose leaves continue as unary chains of about 34 steps down to new deep
facts, 60 of them). No lemma head or the goal gains a candidate; the only change is that
longer valid routes exist below the premises. Its control `dpad` puts lorem in the same slots.

Arms (token-matched within a length level):
| arm | content |
|---|---|
| lem | lemmas only (5k) |
| deep | lemmas + derivation trees below the given facts (primary treatment) |
| dpad | lemmas + lorem in the fact-tree slots, matched to deep (primary control) |
| pad | lemmas + lorem in the lemma-tree slots, matched to both |
| both | lemmas + every lemma's derivation tree (+1 same-head candidate per lemma) |
| junk | lemmas + rule-shaped lines over a disjoint vocabulary in the lemma-tree slots (rule-shaped irrelevant text) |
| disc | lemmas + the lemma trees with leaves renamed so no tree can be entered; same-head roots kept |
| lem25 | compact lemmas only, grown to both's token count (more usable rules, compact form) |

Primary contrast: deep - dpad (longer valid routes below the facts, no new candidates).
Secondary, the same-head family: both - pad (derivations of the lemmas), disc - junk
(candidates with undischargeable preconditions), junk - pad (rule-shaped text), lem25 - pad
(compact usable rules), pad - lem and dpad - lem (length).

Length levels: 25k (the level where the Haiku result is clean) and 50k. Same theories at
both levels (the 50k rung adds unfolding depth, so lem and the chain are shared).

Size: see "Difficulty differs by model" for the per-model request count (90 calibration
+ 720 contrast, or 270 with the primary arms only). 21 models x 810 = 17,010 requests
(7,560 primary only). The Lean sweep was 4,500 per model.

Per-model analysis: the primary contrast at the matched level, paired by theory; Holm across the 21
models as in `notebooks/induction/analysis/significance_report.py`. Secondary: lem25 - pad
(count) and both - lem25 (form); pad - lem (filler cost); the 50k level; family ladders
(effect vs scale) as in the induction figures.

## Calibration first (before any full launch)
Pilot 3 models spanning the ladder (gemma-4-e2b, qwen3.5-27b, deepseek-v4-flash), 10
theories x 1 replicate x 4 arms at 25k. Check: lem between 60% and 95% (else adjust m or
the chain), answers parse (thinking stripped, last derive block found), finish_reason
distribution under the cap. Full launch waits for an explicit go.

## Implementation (small, on the horn-deduction branch)
1. `scripts/deduction/horn/sweep.py`: reads a rendered rung dir, builds (system, user)
   per cell, calls the served endpoint through `smolbench.evals.provider` with the model's
   `COT_ARGS`, writes one JSONL row per cell with a resume key (model, seed, arm, replicate),
   scores with `checker.verify`, spools to S3. Reuses `packed_box.py` for serving order
   (small models first, 1-GPU x8 packed, then 2/4/8-GPU).
2. `render_rung.sh` with `SEED0=100`, two levels: `(5000, 20000)` and `(5000, 45000)`,
   arms `lem both pad`; `lem25` rendered as its own rung with `--lemma-tokens` set to the
   `both` token count of each level.
3. Extraction: strip `<think>...</think>` and `[THINK]...[/THINK]` (the Ministral gotcha
   from the Lean run), then take the last run of lines matching the step regex.
4. Analysis: `pilot_analysis.py`-style paired bootstrap per model, plus a roster table and
   ladder plot; `transcript_search.py` is not applicable (no tool transcripts); reasoning
   length comes from usage.

## Compute
Per model at 25k/50k prompts: prefill dominates for small models, decode for reasoning
models under the cap. One p6-b200 block (23 h) held ~4,500 requests x 21 models at up to
58k-token prompts with uncapped output, so 15k-19k requests with a 32k cap fits in one
block with margin; alternatively the induction-style per-lane spot fleet. Keep boxes alive
until results are downloaded; stop-only backstop.

## Decisions (2026-09-25)
Output cap 32,768 tokens. 30 theories. No ax arm. Length levels decided after the pilot.

## Difficulty differs by model: a per-model matched level
The same theory is easy for a 397B model and out of reach for a 2B one, and a contrast
measured at floor or ceiling says nothing. Two things handle this.

1. A difficulty ladder rendered once for everyone: chain length m in {6, 12, 24} at 25k
   tokens (`roster/m6_25k`, `m12_25k`, `m24_25k`), plus m=12 at 50k for the length
   question. Longer chains mean longer minimal proofs (6, 12, 24 steps) and more places to
   slip; the library size and the token budget stay fixed, so the arms stay matched within
   a level. Each level has its own compact-lemma control (`m*_lem25`, `m12_lem50`).

2. A two-stage run per model, with the level chosen from the control arm only:
   - Stage 1, calibration: `lem` on all three levels, 30 theories x 1 replicate
     (90 requests, ~5k-token prompts, cheap). Pick the level whose `lem` pass rate is
     closest to 80%, preferring the harder level on ties; if no level reaches 40%, the
     model is reported as below floor (format or chain failure, from the verdicts) and
     excluded from the primary contrast; if the easiest level is at 100%, it is used and
     flagged as near ceiling.
   - Stage 2, the contrast: `lem`, `deep`, `dpad` (primary) and `pad`, `both`, `junk`,
     `disc`, `lem25` (secondary) at the chosen level,
     30 theories x 3 replicates (720 requests per model; 270 for the primary arms).
   The selection uses `lem` only, never `both` or `pad`, so it cannot bias the contrast.
   The rule is fixed before the run.

Analysis then reports both - pad at each model's matched level (primary; Holm across
models), and, as a check that the choice of level does not drive the result, a pooled
model with model x level x arm terms over every level a model ran. Models below floor
are listed, not silently dropped.

Pilot: stage 1 on the four pilot models tells us the spread of matched levels across the
ladder and whether m=24 is needed at all.

## Rendered rungs (seeds 100-129, one constant, height 2)
Note (2026-09-25): these rungs carry 2 idle given facts per theory (the generator's old
default), identical across arms. The default is now 0 (`--n-unused-facts`); re-render the
roster rungs with `NUF=0` before the roster run so every given fact is on a derivation of the
goal. Adding arms to the existing rungs needs `NUF=2`.
| rung | m | lem | both = pad | control |
|---|---|---|---|---|
Arms rendered in every `m*_25k`/`m12_50k` rung: lem, both, pad, junk, disc. The deep
treatment is `m12_25k_deep` (lem, deep, dpad; same libraries as `m12_25k` via
`--match-library`, fact trees fitted to 20k tokens with `--fact-height 2 --fact-tokens`).
| m6_25k | 6 | 5k | 25k | m6_lem25 (25k of compact lemmas) |
| m12_25k | 12 | 5k | 25k | m12_lem25 |
| m24_25k | 24 | 5k | 25k | m24_lem25 |
| m12_50k | 12 | 5k | 50k | m12_lem50 (50k of compact lemmas) |

## Driver
`scripts/deduction/horn/sweep.py`: one chat completion per cell (system.md + prompt.md),
`max_tokens` 32768, temperature 0.7, the roster model's thinking arguments, resumable
JSONL rows scored with the checker; `length` finish reasons score as failures. Tested
against a stub OpenAI-compatible server (`tests/deduction/test_horn_sweep.py`).
