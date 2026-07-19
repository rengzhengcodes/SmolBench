# Gate results — CoT-recipe round 1

Analysis run 2026-07-18 ~21:15Z by `scripts/lean_gate_mcnemar.py`, after the
sweep completed (exit 0, 2026-07-18 20:56Z), the purge of 52 infra-exception
rows (backup `all_rows.jsonl.bak-purge4-20260718T2059Z`), and one gap-fill
pass per PENDING_PURGE.md (now deleted; its content is summarized here).
Final data: 9,123 rows; 697 (theorem, k, rung) groups scored; 51 theorems
sanity-dropped (the known core-namespace DojoInitError set — symmetric
across arms, ~1pt power cost as pre-registered).

## VERDICT: **RED**

Per PREREGISTRATION.md (registered 2026-07-13, before the run): GREEN iff
cot-r128 beats bare-r128 AND base, one-sided exact McNemar at alpha 0.05
each, unit = pass@4 group.

| comparison | b | c | n pairs | effect (b−c)/n | 95% CI | p (one-sided) | verdict |
|---|---|---|---|---|---|---|---|
| **cot vs bare** (gate 1) | 66 | 75 | 689 | **−0.013** | [−0.047, +0.021] | 0.800 | not significant |
| **cot vs base** (gate 2) | 92 | 70 | 691 | +0.032 | [−0.004, +0.068] | 0.049 | significant |
| bare vs base (descriptive) | 109 | 79 | 693 | **+0.043** | [+0.005, +0.082] | 0.017 | significant |

Gate 1 fails ⇒ RED.

## Reading

- **The r128 recipe fix worked**: bare-r128 significantly beats base
  (+4.3pt pass@4, p = 0.017) — the original 17/77 null (r16 bare adapters
  degrading performance) is reversed by rank 128 + 2 epochs + cosine.
- **CoT targets added nothing on this configuration**: cot-r128 ≈ bare-r128
  (−1.3pt, p = 0.80). The cot-vs-base significance is therefore attributable
  to the shared training recipe, not the target format.
- **The effect lives entirely in stepk:1** (next-tactic prediction — the
  rung the SFT data directly targets): base 0.145 → bare 0.329 / cot 0.272.
  The hint:2 / hint:3 / noise:3 rungs are flat across arms (~0.46–0.50).
- **No CoT collapse**: cot-arm outputs did not degenerate to bare tactic
  tails (mean raw_response 229 chars vs bare 46; base 167 — note
  raw_response excludes server-parsed reasoning_content, so these understate
  full generation lengths for reasoning arms).
- pass@1: base 0.239, bare 0.301, cot 0.240 — bare also leads per-rollout.

## Pass@4 marginals

base 269/695 = 0.387 · bare 298/693 = 0.430 · cot 290/691 = 0.420
(missing groups per arm: 2 / 4 / 6 — exception-rule drops, pairwise.)

## Scoring notes

- Exceptions scored as MISSING per pre-registration: a group with ≥1 success
  is a pass regardless; a group with no success and ≥1 exception (or <4
  scored rollouts) is missing and drops its pairs only.
- The cot arm's 07-13 calibration cells (8 rollouts/group) are restricted to
  rollout_idx 0–3 so all arms score the same four seeds.
- Power context: this design had 0.88 power for a +8pt per-rollout effect,
  0.51 for +5pt (see PREREGISTRATION.md) — the CoT null rules out large
  effects only; a small CoT benefit (≤3pt) would likely have been missed.

## Pre-registered follow-up on RED

Qwen attention-only LoRA is the recipe's least-favorable configuration
(fused-expert ParamWrapper OOM forbids MLP/expert targeting), so this RED is
NOT decisive for the dense trio arms (llama-31-405b / nemotron-ultra-253b).
The approved plan's next step is the cheap dense fenced micro-smoke (a few
hundred fenced-style rows, tiny train + serve) before any abandon decision.
A secondary lead worth carrying: bare-r128's stepk:1 gain suggests expert
iteration on the WORKING bare recipe as an alternative round-2 axis.
