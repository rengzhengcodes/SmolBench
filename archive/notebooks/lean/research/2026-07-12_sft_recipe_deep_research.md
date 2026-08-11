# Deep-research report: Lean 4 SFT recipe to beat 17/77

*Generated 2026-07-12 by a deep-research workflow (6 search angles, 25 sources
fetched, 107 claims extracted, top 25 adversarially verified with 3-vote
panels: 24 confirmed 3–0, 1 refuted 0–3). Raw run output:
`lean_qwen4way_pilot` baseline context; workflow run `wf_1c296600-ec2`.*

## Question

What SFT training-recipe changes are best supported by published evidence for
fine-tuning large LLMs to prove Lean 4 theorems, to substantially raise
verified pass rate over the current best of 17/77 (qwen3-lean-leannav; base
15/77; McNemar insignificant)? Current recipe: QLoRA r=16 α=32, lr 1e-4,
1 epoch, seq-len 4096, assistant-only loss on ~56k bare tactic-tail targets
from LeanDojo Benchmark 4 novel_premises/train; eval = single-rollout pass@1
at temperature 0.7, LeanDojo replay verification.

## Executive summary

The dominant, best-supported defect in the current recipe is the **target
format**: bare ground-truth tactic tails with assistant-only loss trained away
the base model's long chain-of-thought (observed collapse from ~4–5k output
tokens to ~15). Every leading Lean 4 system (DeepSeek-Prover-V2, Kimina-Prover,
Goedel-Prover-V2, Leanabell-Prover, Lean-STaR) trains on reasoning traces that
interleave informal reasoning with Lean code. The second lever is closing the
loop (expert iteration on self-generated Lean-verified proofs + compiler-error
self-correction). Third: LoRA capacity (r=16 is the pessimal case for
code-like domains) and inference-time sampling budget (pass@N rises steeply
with N). Recipe quality dominates scale — an 8B model with the right recipe
beats a 671B one — so the null is recipe-driven, not a size problem.

## Verified findings

### 1. CoT-augmented targets beat bare tactic tails (HIGH — primary fix)
- Lean-STaR, matched 7B ablation on LeanDojo Benchmark 4 data: bare
  (state→tactic) SFT 29.5% vs CoT-augmented 32.8% pass@32 on miniF2F-test.
- DeepSeek-Prover-V2: CoT 82.4% vs non-CoT 73.8% pass@32 at 671B.
- Kimina-Prover synthesizes ~20k `<think>`-block SFT examples; Lean-STaR
  builds ~52.4k GPT-4 retrospective "thoughts" before each tactic **from
  LeanDojo Benchmark 4 — the same source as our 56k pairs, a drop-in path**.
- Sources: arxiv.org/html/2407.10040v1 (Lean-STaR),
  arxiv.org/html/2504.21801v2 (DeepSeek-Prover-V2),
  arxiv.org/html/2504.11354 (Kimina), arxiv.org/pdf/2508.03613 (Goedel-V2),
  arxiv.org/pdf/2504.06122 (Leanabell).

### 2. Expert iteration / rejection sampling (HIGH)
- Lean-STaR: two rounds (+32.2k, +19.3k Lean-verified trajectories) lift
  32.8% → 34.8–36.1% pass@32/64 at 7B.
- BFS-Prover: strategic per-round filtering (drop already-solvable problems,
  concentrate on hard cases). Standard backbone of every SOTA prover.
- Sources: arxiv.org/html/2407.10040v1, arxiv.org/pdf/2508.03613,
  arxiv.org/pdf/2502.03438 (BFS-Prover), arxiv.org/pdf/2505.10962 (MPS-Prover).

### 3. Compiler-feedback self-correction (HIGH)
- Goedel-Prover-V2: verifier-guided self-correction; 32B reaches 88.1%
  pass@32 standard / 90.4% in self-correction mode. Combining long CoT with
  error correction "requires special efforts on curating data".
- BFS-Prover: DPO on state-tactic pairs auto-annotated with compiler errors.
- Leanabell: RL with Lean 4 compiler outcome reward.
- Sources: arxiv.org/pdf/2508.03613, arxiv.org/pdf/2502.03438,
  arxiv.org/pdf/2504.06122.

### 4. Whole-proof / subgoal-decomposed targets are competitive-to-superior (HIGH)
- DeepSeek-Prover-V2 cold-start: decompose into subgoals (`have … sorry`),
  solve with a 7B prover, append assembled proof to the CoT.
- Apples-to-apples reference for OUR split: ReProver (stepwise, no CoT,
  retrieval-augmented) = 26.3% pass@1 on novel_premises via best-first search.
- Sources: arxiv.org/html/2504.21801v2, arxiv.org/pdf/2508.03613,
  ar5iv.labs.arxiv.org/html/2306.15626 (LeanDojo).

### 5. Recipe quality dominates model scale (HIGH — strategic)
- Goedel-Prover-V2-8B (84.6% pass@32 miniF2F) outperforms
  DeepSeek-Prover-V2-671B despite being ~80× smaller. SOTA provers are
  7B–72B. The 235B/405B/253B trio is not too small; the recipe is the issue.
- Sources: arxiv.org/abs/2508.03613, arxiv.org/html/2504.11354.

### 6. LoRA capacity: r=16 underperforms; code-like domains want r≈256 (HIGH, nuanced)
- Biderman et al. ("LoRA Learns Less and Forgets Less", TMLR 2024): LoRA
  substantially underperforms full FT on code/math; gap larger for code and
  widens with data; code needs r≈256, math often closes at r=64.
- Thinking Machines "LoRA Without Regret" (surfaced in verifier evidence,
  less firmly established): LoRA can match full FT when adapters cover ALL
  layers incl. MoE experts, LR ≈10× full-FT LR, and rank×capacity exceeds
  dataset information content.
- **Refuted claim (0–3)**: that LoRA capacity is the primary explanation of
  the 17/77 null. Verdict: contributing factor only; CoT collapse dominates.
- Source: arxiv.org/html/2405.09673v2.

### 7. pass@N is a large, cheap lever (HIGH — eval-side)
- Kimina-Prover 72B: 52.94% pass@1 → 80.74% pass@8192 on miniF2F-test.
- Literature reports pass@32–64 (often with tree search); our single-rollout
  pass@1 at temp 0.7 is the least favorable regime and not comparable.
- Sources: arxiv.org/html/2504.11354, arxiv.org/html/2407.10040v1.

### 8. Curation > raw volume for SFT data (HIGH)
- MPS-Prover: pruning ~40% of redundant training data loses nothing (and
  improves results). Goedel-V2: scaffolded synthesis of increasing-difficulty
  problems. Explains the flat synthetic arms: raw 24k Goedel/LeanNavigator
  rows without CoT format or difficulty scaffolding is not the mechanism that
  works in the literature.
- Sources: arxiv.org/pdf/2505.10962, arxiv.org/pdf/2508.03613.

### 9. Hyperparameters differ by regime (MEDIUM)
- Kimina distillation (full FT): lr 2e-5, cosine schedule, 3 epochs, packing.
- LoRA regime: ~10× the full-FT LR (so our 1e-4 LR is roughly right for LoRA;
  the deficient dimension is rank/coverage, not LR).
- Sources: arxiv.org/html/2504.11354, arxiv.org/html/2405.09673v2.

### 10. Premise retrieval & agent wrappers (MEDIUM — inference-time, complementary)
- ReProver concatenates retrieved premises with the tactic state (26.3%
  pass@1 novel_premises). Prover Agent (informal reasoner + prover + auxiliary
  lemmas) reaches 88.1% miniF2F at small scale.
- Sources: ar5iv.labs.arxiv.org/html/2306.15626, arxiv.org/pdf/2506.19923.

## Concrete recipe mapped to this repo

Ordered by expected impact per unit cost:

1. **Fix the target format (data change, biggest expected effect).** Rebuild
   the SFT JSONL so the assistant target is `<think>rationale</think> +
   tactic tail`, not the bare tail. Two implementation options:
   - *Lean-STaR path*: annotate the existing ~56k pairs with retrospective
     rationales — prompt a strong LLM with (state_before_k, ground-truth
     tail) to write the thought that would precede the tactic. ~20–50k
     annotated rows suffices per the literature (Kimina used ~20k).
   - *Lighter probe first*: verify the hypothesis cheaply by checking whether
     the collapse is format-driven — fine-tune on a subsample where targets
     are wrapped in the Qwen3 think format, and confirm output length no
     longer collapses.
2. **Raise LoRA capacity.** r=128–256 (α=2r), adapters on all linear layers
   including MoE expert projections (already targeting gate/up/down_proj —
   confirm expert coverage under peft's ParamWrapper). Keep lr ≈1e-4 (the
   ~10× rule), consider 2–3 epochs with cosine schedule.
3. **Expert iteration round.** Sample K proofs per train theorem from the
   best current model, verify by LeanDojo replay, keep verified (state,
   CoT+proof) trajectories, re-SFT (optionally staged via `--init-adapter`).
   Filter out already-easy theorems each round (BFS-Prover). If budget
   allows, add compiler-error self-correction pairs or DPO on
   compiler-annotated failures.
4. **Eval-side: report pass@N.** Raise `n_rollouts` (≥8, ideally 32 to match
   the literature) alongside pass@1; keep the seed. This mechanically raises
   verified successes and makes results comparable to published numbers.
5. **Curate before scaling.** Dedup/prune the 56k pool; if synthetic arms
   return, reformat them into the CoT target format and scaffold difficulty
   rather than raw-appending.

## Caveats

- Nearly all headline numbers (Kimina 52.9%, Goedel-V2 84.6%, DeepSeek-V2
  82.4%, BFS 72.95%, Prover Agent 88.1%) are **miniF2F-test** (olympiad
  style), NOT our Mathlib novel_premises split. Only ReProver (26.3% pass@1)
  and Lean-STaR's data source are directly transferable. Trust the
  *directions* (CoT > bare, iteration helps, rank helps, pass@N helps), not
  the absolute numbers.
- CoT effect size in the matched ablation is modest at 7B (+3.3pt); the big
  jumps come from combining CoT + expert iteration + self-correction + large
  pass@N. No single change is proven to produce a dramatic jump alone.
- The "LoRA Without Regret" all-layers/10×-LR prescription comes from a lab
  report, not peer review — promising but less established than Biderman.
- Fast-moving field (sources 2023–2026).

## Open questions

1. What CoT-augmented pass rate is achievable on the novel_premises split
   specifically? (Lean-STaR trains on this data but reports miniF2F.) A
   Lean-STaR-style annotation of our 56k pairs is the most direct experiment.
2. Does the LoRA-Without-Regret prescription hold for a 235B MoE with fused
   expert Parameters (peft ParamWrapper), or does routing change the calculus?
3. Is the CoT benefit mostly *preserving* the base model's reasoning (don't
   train it away) vs teaching new reasoning? If the former, think-format
   wrapping may recover most of the gain without full re-annotation.
4. What is the minimum expert-iteration + compiler-feedback loop that beats
   17/77 within a fixed QLoRA budget — and does DPO-on-errors beat pure
   rejection-sampling SFT for sample efficiency?

## Refuted claims (transparency)

- "The 17/77 null may be partly attributable to LoRA capacity limits rather
  than data/recipe alone" — killed 0–3: verifiers judged the bare-tactic /
  CoT-collapse mechanism dominant; capacity is secondary.
