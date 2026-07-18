# Pre-registered improvement gate — CoT-recipe round 1

Registered 2026-07-13 ~07:55Z, BEFORE the 3-arm gate run started; user-approved
"full power" design. Calibration source: this run dir's first 40-theorem ×
8-rollout cot-arm pass (cells merge into the gate via the resumable run_dir).

## Design

- Theorems: 300, seeded (1776) sample of novel_premises/val; rungs stepk:1,
  hint:2, hint:3, noise:3; n_rollouts = 4 (per-rollout seed = 1776 + idx).
- Arms: `qwen3-235b-a22b` (served base), `qwen3-lean-bare-r128` (control:
  bare tactic-tail targets, r=128 α=256, 2 ep cosine),
  `qwen3-lean-cot-r128` (treatment: identical schedule/rank, CoT targets on
  the SAME (full_name, k) rows). `qwen3-lean-real` (r16) is EXCLUDED from the
  gate: not part of the criterion, saves ~25% of spend.
- Unit: (theorem, k, rung) group; group outcome = pass@4 (any rollout
  verified by LeanDojo replay).

## Decision rule

GREEN iff BOTH hold (McNemar exact test on discordant group pairs, one-sided
alpha = 0.05 each, conjunction — no multiplicity correction needed for a
conjunctive success criterion):

1. cot-r128 > bare-r128 (attributes the win to target FORMAT, not rank), and
2. cot-r128 > base.

Report effect size (b - c) / n_groups with a 95% CI for both comparisons,
not just p-values.

- Exceptions (generation/verification infrastructure timeouts, verdict
  `exception`) are MISSING data: the group is dropped from any pairwise
  comparison involving it, not scored as failure. (Verification-timeout
  pathology is goal-shape-driven — e.g. `CategoryTheory.Limits.Types.
  isLimit_iff`, 1/40 calibration theorems — and cannot be pre-excluded for
  unseen theorems, so it is handled at scoring time.)
- Sanity-gate failures (ground-truth replay fails; 5/40 in calibration,
  arm-independent by construction) drop the theorem entirely, as always.

## Power (empirical calibration, 2000-sim Monte Carlo)

Calibration (cot arm, 94 groups >= 8 rollouts): marginal per-rollout rate
0.132; frac_solvable 0.309 (stepk:1 0.19); mean per-rollout p among solvable
0.435, wide dispersion (0.12–0.88, fitted beta concentration ~2.8).

At 300 theorems × 4 rungs, pass@4, alpha 0.05: power = 0.88 for a +0.08
per-rollout treatment bump, 0.51 for +0.05, 0.22 for +0.03. A null therefore
rules out (at ~88% sensitivity) only effects >= ~8pt per-rollout; smaller
real effects may be missed — noted in advance, accepted by the user
("Full power" option, ~$1000).

RED-gate follow-up (from the approved plan): a red gate is NOT decisive for
the dense trio arms (Qwen attention-only is the recipe's least-favorable
configuration) — run the cheap dense fenced micro-smoke before any abandon
decision.

## Secondary (descriptive, no gating)

- Output-length distribution per arm (CoT-collapse check: base ~5k tok,
  old bare-SFT ~15 tok; calibration cot arm ~320 tok, trunc = 0).
- pass@1 alongside pass@4; per-rung breakdown; expert-iteration harvest
  feasibility from cot-arm successes (rationale extraction rate).
