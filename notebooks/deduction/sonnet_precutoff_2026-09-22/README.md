# Sonnet 5 on the pre-cutoff pilot corpus (2026-09-22)

Harness test of the redesigned ladder, not a result: the corpus is Mathlib 2024-03-24, inside Sonnet 5's training data. 100 cells (last step of replay-passing theorems with <= 5 tactics, seed 0), 29 rungs, one sample per cell. Solver: `claude-sonnet-5`, extended thinking at effort `high`, closed book (the agent read only its `prompt.md`; transcripts audited). Scorer: LeanDojo on the traced checkout, `lean/scripts/verify_examples.py`. Three cells are degenerate (a `classical`-wrapped tactic closes the goal before the recorded final step) and score `replay_failed` on every rung; n = 97 below.

## Pass rate per rung (of 100)

| rung | pass | rung | pass | rung | pass |
|---|---|---|---|---|---|
| stepk-2 | 61 | sig-0 | 79 | proof-0 | 81 |
| hint-0 | 80 | sig-1 | 79 | proof-1 | 84 |
| hint-1 | 82 | sig-2 | 81 | proof-2 | 77 |
| hint-2 | 82 | sig-3 | 86 | proof-3 | 82 |
| hint-3 | 86 | sig-4 | 80 | proof-4 | 81 |
| hint-4 | 85 | signoise-1 | 79 | proofnoise-0 | 80 |
| noise-1 | 81 | signoise-2 | 84 | proofnoise-1 | 81 |
| noise-2 | 78 | signoise-3 | 77 | proofnoise-2 | 81 |
| noise-3 | 79 | signoise-4 | 82 | proofnoise-3 | 78 |
| noise-4 | 78 |  |  | proofnoise-4 | 84 |

## Paired differences over cells, percentage points, 95% bootstrap

| question | comparison | diff |
|---|---|---|
| MPI effect | hint-1 vs stepk-2 | +21.6 [+10.3, +33.0] |
| MPI effect, unflagged | sig-0 vs stepk-2 | +18.6 [+8.2, +29.9] |
| flagging | sig-0 vs hint-1 | -3.1 [-10.3, +4.1] |
| hops vs blank length | sig-1 vs signoise-1 | +0.0 [-6.2, +6.2] |
| hops vs blank length | sig-2 vs signoise-2 | -3.1 [-10.3, +3.1] |
| hops vs blank length | sig-3 vs signoise-3 | +9.3 [+2.1, +17.5] |
| hops vs blank length | sig-4 vs signoise-4 | -2.1 [-9.3, +4.1] |
| hops vs sig-0 | sig-1 vs sig-0 | +0.0 [-8.2, +8.2] |
| hops vs sig-0 | sig-2 vs sig-0 | +2.1 [-4.1, +8.2] |
| hops vs sig-0 | sig-3 vs sig-0 | +7.2 [+1.0, +14.4] |
| hops vs sig-0 | sig-4 vs sig-0 | +1.0 [-6.2, +9.3] |
| density | proof-0 vs sig-0 | +2.1 [-6.2, +10.3] |
| density | proof-1 vs sig-1 | +5.2 [-2.1, +12.4] |
| density | proof-2 vs sig-2 | -4.1 [-11.3, +3.1] |
| density | proof-3 vs sig-3 | -4.1 [-10.3, +2.1] |
| density | proof-4 vs sig-4 | +1.0 [-5.2, +7.2] |
| density vs blank length | proof-0 vs proofnoise-0 | +1.0 [-7.2, +9.3] |
| density vs blank length | proof-1 vs proofnoise-1 | +3.1 [-3.1, +10.3] |
| density vs blank length | proof-2 vs proofnoise-2 | -4.1 [-10.3, +2.1] |
| density vs blank length | proof-3 vs proofnoise-3 | +4.1 [-3.1, +11.3] |
| density vs blank length | proof-4 vs proofnoise-4 | -3.1 [-11.3, +5.2] |
| legacy flagged ladder | hint-1 vs noise-1 | +1.0 [-7.2, +9.3] |
| legacy flagged ladder | hint-2 vs noise-2 | +4.1 [-3.1, +11.3] |
| legacy flagged ladder | hint-3 vs noise-3 | +7.2 [+3.1, +12.4] |
| legacy flagged ladder | hint-4 vs noise-4 | +7.2 [+2.1, +13.4] |

## Reading

- The MPI effect is the only robust one and survives unflagging: +19 to +22 points.
- Burying the lemmas unmarked costs about 3 points, inside the noise at n = 97.
- No hop level, up to 140k tokens of true context (`proof-4`), moves pass rate against its length control. The two intervals that exclude zero (`sig-3` vs `signoise-3`, `hint-4` vs `noise-4`) have no neighbour agreeing with them across 20 comparisons.
- Proofs are no better or worse than signatures at any depth.
- Failures are elaboration errors (argument roles, rewrite shape, invalid projections), not missing lemmas: 132 of 180 failing answers name an MPI lemma, the same rate as passing answers.
- Exact matches to the ground-truth tactic: 9/97 at None, 19 to 27 at every other rung. Recall and competence cannot be separated on this corpus; that is what the post-cutoff corpus is for.

`verdicts.jsonl` holds one row per (cell, rung). The prompts, answers and full Lean errors are in the gitignored `examples/` tree, regenerable with `scripts/deduction/render_examples.py` and the solve workflow.
