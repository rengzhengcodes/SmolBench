# Horn bench: does more relevant information hurt? (`both` vs `pad`)

Status (2026-09-25). The setup in R11 is the final experimental setup and the only one the
code can run: one constant, a chain of m lemmas, open alternatives, a derivation tree per
lemma, and the token-matched arms lem / pad / disc / both (junk was run in R11 and dropped on
2026-09-26; see the specification). The specification is
`smolbench/deduction/horn/README.md`. Every other arm and variant named below (ax, unf,
both:j, pad:j, bothm, padm, deep, dpad, lem25, multi-constant theories, step budgets) is
retired; its code is on the git branch `horn-deduction-archive` and its numbers are kept
here as history only.

Question. A prover is given the lemmas that prove a goal. Does adding the lemmas'
derivations (true, usable, and logically redundant given the lemmas) make it fail more
often than adding the same number of tokens of lorem-ipsum filler?

What the data can and cannot say. `both` adds relevant information as more candidates:
every tree's root rule shares its lemma's head, so `both` doubles the valid rules per chain
head (6.8 -> 13.7) and for the goal (6.4 -> 12.8) and multiplies distinct predicates 10x
(138 -> 1,376); `lem25` sits between on both counts (10.5; 603) and in accuracy. "More valid
choices" alone predicts the lem / lem25 / both ordering. `deep` (derivations below the given
facts: longer valid routes, no new candidate for any lemma head) was tried as a way to add
relevant information without new candidates and has no effect (R9): the backward search
stops at facts and never visits those rules. The controls that separate "valid content" from
"rule-shaped text" are `junk` (rule-shaped lines over a vocabulary that cannot reach the goal)
and `disc` (the same trees with leaves renamed, so every same-head candidate is kept but no
tree can be entered); both were run on Haiku in R11.
The Haiku numbers in R8 are exploratory (the design was chosen after five earlier designs),
matched under the cl100k tokenizer rather than Haiku's, and at m = 12 the exact sign-flip
test for both - pad gives p = 0.078 (st_h2), 0.062 (st_h4) and 0.5 (fresh seeds): suggestive.
R11 supplies the controls (junk, disc) and the chain length (m = 48) at which the effect is
large and significant: both - pad = -50 [-70, -30], p = 0.008, with junk and disc level with
lorem. The confirmatory roster run is still the test across models.

## Valid setup (single constant, every added line usable)

Theory. One object `c`. Facts about `c`; a chain of 12 lemmas from the facts to the goal;
plus open alternatives: extra lemmas whose heads lie on the chain and whose bodies are
derivable, so the goal has many valid routes. Every lemma has a binary derivation tree down
to two-body axioms. Names are pseudo-words; a proof step names a rule by its content
(`derive h(c) from a(c), b(c)`); any valid proof counts; the prompt says the goal is always
provable.

Arms, token-matched.
- `lem`: the lemmas only.
- `both`: the lemmas and every lemma's derivation tree.
- `pad`: the lemmas and lorem-ipsum lines in the tree rules' slots, matched to `both` in
  tokens and position.
- `ax`: the trees only (the long route is the only route).
- `lem25`: compact lemmas only, grown to the token count of `both` (same chain and facts as
  st_h2, ~2000 lemmas). Separates the derivation form from the rule count.

Solver. Haiku 4.5 as a Claude Code subagent that reads the prompt file in 2000-line chunks
and returns the proof; 10 seeds x 3 samples per arm; paired seed bootstrap for contrasts.
Cells whose solver used any tool other than Read are excluded (st_h2: 0/120, st_h4: 2/120).

### Results

| rung | trees | lem | pad | both | ax | both - pad, paired |
|---|---|---|---|---|---|---|
| st_h2 | depth 2 (29% depth 3); ax proof 40-60 steps | 5.0k, 28/30 = 93.3% | 25.0k, 28/30 = 93.3% | 25.0k, 19/30 = 63.3% | 20.2k, 6/30 = 20.0% | -30.0 [-53, -7] |
| st_h4 | depth 4; ax proof 180 steps | 2.0k, 30/30 = 100% | 29.4k, 28/28 = 100% | 29.4k, 22/30 = 73.3% | 27.7k, 0/24 = 0% | -26.7 [-50, -7] |
| lem25 control | none; 25.0k of compact lemmas, 2057 rules (same chain and facts as st_h2) | 25.0k, 23/29 = 79.3% | | | | vs st_h2 pad: -15.0 [-32, +2]; vs st_h2 both: +15.0 [-8, +40] |

1. Valid derivations hurt relative to lorem. With nothing false or off-target in the
   prompt, `both` loses 27-30 points to a token-matched lorem arm (bootstrap intervals
   exclude zero; sign-flip p = 0.078 and 0.062). Lorem itself shows no detectable cost at
   this n: pad - lem = 0.0 [-10, +10] (st_h2); both at ceiling in st_h4.
2. The long route fails when it is the only route: 20% at 40-60 steps, 0% at 180 steps.
   Failures are invented rules and undischarged premises.
3. The loss appears on lemma-level proofs. Classifying each written proof by its heads
   (any tree intermediate => "via tree"): 8 of 60 `both` attempts go via a tree (5 pass,
   too few to compare); 52 stay on lemma heads and 36 pass (69%), against 93-100% for the
   lemma-level proofs in `pad`. Route choice, a post-treatment variable, does not explain
   the loss.
4. What the transcripts show (descriptive; regenerated from the committed script, which
   counts a predicate only when written as an atom). `both` reasoning is about twice as
   long as `lem` or `pad` (st_h2: 24k chars on successes, 15k on failures; lem 10k, pad
   13k), lists 12-15 candidate rules for the goal against 7-8, and mentions 94-142 tree
   intermediates. Both extra counts are built in: every tree adds one same-head root rule
   per lemma, and the intermediates exist only in `both`, so these numbers say the model
   reads what is there, not that it is diverted. Reasoning length is also confounded with
   quoting. The failures were hand-classified: a chain head asserted as a fact ("I have
   fova(zal) in the facts!", 9 cases) or two rules fused into one invented one-premise rule
   (9 cases); `lem25` fails the same ways, so these kinds are generic, not specific to the
   derivation form.

5. Form vs count (`lem25`). The same number of rules as `both`, all compact lemmas, all
   valid: 79.3% (29 of 30 cells; one agent returned nothing). It sits between `pad` (93.3)
   and `both` (63.3): lem25 - pad = -15 [-32, +2], lem25 - both = +15 [-8, +40]. Both
   intervals include zero and the full effect, so the count/form split is undetermined.
   `lem25` matches `both` in rule count and tokens only: its alternatives give more
   same-head rules per chain head than `both`'s one root rule each, its library order
   differs, and it ran as a separate rung. Its failures are the same two kinds (3 invented
   rules, 3 undischarged premises) and its proofs are long (22.6 steps vs 15.9 for `lem`):
   2000 valid alternates already pull the model onto detours.

Reading. For Haiku, redundant valid derivations cost about 28 points against lorem of the
same length; the loss appears on lemma-level proofs, not on tree routes; and whether it is
the number of usable rules or their unfolded form is undetermined at 10 seeds.

### Cell accounting
Every launched cell is accounted for. st_h2: 120 launched, 120 proofs returned, 0 confused,
0 empty, 0 used a tool other than Read. st_h4: `lem`, `both`, `pad` 30/30 proofs each, 2
`pad` cells excluded for Bash use (both passed; pad is 28/28 without them); `ax` 24 proofs,
3 confused, 3 empty. lem25: 29 proofs, 1 empty. So no `both` or `pad` contrast has a
missing cell other than the two grep exclusions.

### Caveats that still apply
- Statistics: paired seed-level cell means with a percentile bootstrap over 10 seeds
  undercover at this n; `pilot_analysis.py` now reports an exact sign-flip permutation p
  next to it. About 15 contrasts appear in this document; none is pre-registered.
- Seeds 0-9 are shared by every rung, so st_h2 and st_h4 share chains, facts and goals. A
  confirmatory run needs fresh seeds (`SEED0` in `scripts/deduction/horn/render_rung.sh`).
- The solver reads through a tool in chunks; a single-context API call is the clean version.
- Layout is interleaved (tree rules scattered among lemmas in one master order), not
  grouped under each lemma as in a source file.
- One model, one length (25-29k). (The 60k/105k collapse was seen in the superseded
  multi-constant rungs, not in this setup.)

## R9. Derivations below the facts (`deep`) on Haiku: no effect
Rung `m12_25k_deep`, fresh seeds 100-109 x 3 samples, libraries identical to `m12_25k`.
Every given fact also has a derivation (depth-2 tree, then ~34-step unary chains to 60 deep
facts): longer valid routes exist under every premise, and no lemma head or the goal gains a
candidate. 1 `dpad` cell excluded for Bash use.

| arm | tokens | pass | mean proof length |
|---|---|---|---|
| lem | 5.3k | 28/30 = 93.3% | 19.4 |
| dpad (lorem in the fact-tree slots) | 25.1k | 22/27 = 81.5% | 19.8 |
| deep (fact trees) | 25.1k | 27/30 = 90.0% | 19.0 |

deep - dpad = +10.0 [0, +27], sign-flip p = 0.50; deep - lem = -3.3 [-20, +13].
Not one step in any arm applies a fact-tree rule: every proof is lemma steps only. The
reasoning in `deep` mentions about 10 of the ~2,000 fact-tree intermediates and is 8% longer
than in `dpad`. So a longer valid route beneath premises the model already holds is neither
taken nor costly. This fits the search the transcripts show: backward chaining from the goal
stops at a given fact, so rules whose heads are facts are never expanded. The `both` loss is
therefore not "longer chains feasible" as such; it needs the extra routes to sit on the path
the search actually walks, i.e. at lemma heads, where they are also extra candidates.
Paired `pad` / `both` on the same ten theories (rung `m12_25k`, 3 `pad` cells excluded for
Bash use): pad 26/27 = 96.3%, both 26/30 = 86.7%, mean proof length 18.8 vs 20.7; only 6 of
587 `both` steps are tree rules. both - pad = -10.0 [-23, 0], sign-flip p = 0.50.

All five arms on these theories: lem 93.3, pad 96.3, dpad 81.5, deep 90.0, both 86.7. Two
things follow. (1) The two lorem controls differ by 15 points (pad - dpad = +16.7 [-3, +40])
while their prompts differ only in 60 extra given facts and the slot positions, so the noise
floor at 10 theories x 3 samples is about +/-15 points. (2) The st_h2 effect (both - pad =
-30 on seeds 0-9) did not replicate at that size on fresh seeds (-10 on seeds 100-109). With
the exact test at p = 0.5 on the fresh seeds alone, the single-rung evidence is weak. Pooled
over the 20 theories of st_h2 and m12_25k (same recipe, seeds 0-9 and 100-109): both 75.0%
(45/60) vs pad 95.0% (54/57); both - pad = -20.0 [-35, -7], exact sign-flip p = 0.023;
pad - lem = 0 [-10, +10]. That is the current Haiku estimate: a 20-point cost of the lemma
derivations against lorem, significant at n = 20, with the effect size uncertain by a factor
of two. The st_h4 rung (depth 4, seeds 0-9) gives -26.7 [-47, -10], p = 0.062, on the same
seeds as st_h2 and is not an independent replication.

## R10. Does a longer required chain lower the pass rate? Only through search.
Required proof length m in {6, 12, 24, 48, 96}, lemma-only prompts, 10 fresh theories
(seeds 100-109) x 3 samples per level, every cell accounted for (contaminated and empty
cells refilled; 0 grep). Two variants: *pure chain*, the library is exactly the m chain
lemmas (prompts 0.3k-2.0k tokens, no search); *with alternatives*, the library is held at
5k tokens (~350-400 lemmas), so the chain must be found among open alternatives.

| m | pure chain | with alternatives (5k) | mean proof length, alt |
|---|---|---|---|
| 6 | 100% | 96.7% | 8.8 |
| 12 | 93.3% | 93.3% | 19.5 |
| 24 | 100% | 90.0% | 33.8 |
| 48 | 86.7% | 60.0% [43, 77] | 60.7 |
| 96 | 90.0% | 50.0% [33, 67] | 109.3 |

Executing a long chain is nearly free: with no search, Haiku writes 96 consecutive correct
steps 90% of the time, and the few failures are single invented rules. With a library to
search, the pass rate holds to m = 24, falls to 60% at m = 48 (proofs average 61 steps,
10 of 12 failures invented rules) and to 50.0% at m = 96 (proofs average 109.3 steps). So "a longer chain of lemmas"
lowers the pass rate through the search for the chain, not through its execution. For the
deep design this means a longer valid route is only costly if the model has to find it,
and R9 showed the model never looks for routes below facts it already holds.

## R11. The full ladder at m = 12 and m = 48: only usable derivations cost
Same ten theories (seeds 100-109) x 3 samples per arm, 25k tokens, one constant. Five arms
share every lemma position and token count: `lem` (5k), and in the tree slots `pad` (lorem),
`junk` (rule-shaped lines over a disjoint vocabulary, fire for nothing), `disc` (the trees
with leaves renamed: same-head root rules kept, no tree can be entered), `both` (the trees).
All 150 cells per chain length are in (30 per arm). These theories were generated before
the generator's extra-fact default was removed: each carries two given facts beyond the
m + 1 chain facts, identical across arms; at m = 48 one of them is used by no rule. The
final generator adds none. Tool audit (transcripts of the nine
workflows that solved this rung): 11 of 150 cells used a search tool besides Read (both 2,
disc 1, junk 2, pad 6); restricting to the 139 Read-only cells moves no arm by more than
3.3 points (pad 50.0, disc 51.7, junk 50.0, both 3.6, lem 73.3) and both - pad = -43 [-65,
-20]. One disc cell (seed 104, sample 0) is scored from its transcript: the agent wrote a
complete proof text and then looped on the structured-output call; the proof fails at step 1
(a derived head asserted as a fact).

| arm | m = 12 | m = 48 | m = 48 mean proof length | m = 48 attempts using a tree rule |
|---|---|---|---|---|
| lem | 93.3% | 73.3% | 59 | 0/30 |
| pad (lorem) | 96.7% | 53.3% | 69 | 0/30 |
| junk (rule-shaped irrelevant) | 96.7% | 50.0% | 61 | 0/30 |
| disc (dead same-head candidates) | 96.7% | 53.3% | 62 | 1/30 |
| both (usable derivations) | 86.7% | 3.3% | 87 | 11/30 |

Paired contrasts at m = 48 (seed-paired bootstrap CI, exact sign-flip p over 10 seeds):
both - pad = -50.0 [-70, -30], p = 0.008; both - junk = -46.7 [-70, -23], p = 0.016;
both - disc = -50.0 [-70, -30], p = 0.004; disc - pad = 0.0, p = 1.0; junk - pad = -3.3,
p = 1.0; pad - lem = -20.0 [-43, +7], p = 0.25. At m = 12 the same ordering holds with
both - pad = -10 [-23, 0], p = 0.5, and every control within 0 of lorem.

Reading.
1. Length costs something once the chain is long (pad - lem = -20 at m = 48), and it is
   the same whether the filler is lorem, rule-shaped junk, or dead derivations: the three
   controls are within 4 points of each other at both chain lengths.
2. Usable derivations cost 47-50 points more than any of the controls at m = 48. Every
   line in `both` is true and on a derivation of the goal; the only difference from `disc`
   is that its trees can be entered. The model enters them (11 of 30 attempts use a tree
   rule, against 1 of 30 in `disc`), commits, and fails: 16 of 29 failures assert a derived
   chain head as a fact on the first line (route "short", premise not derived), 10 fail
   inside a tree (invented one-premise rules or an underived tree premise), 3 elsewhere.
3. Dead candidates are rejected cheaply. `disc` shows the same second rule at every head,
   but its intermediates fail the first lookup, so the model returns to the chain. A valid
   candidate passes the lookup, so there is no signal to return. This is the mechanism the
   design notes predicted: validity removes the backtrack signal.
4. The effect scales with the search load: -10 at m = 12, -50 at m = 48, with the same
   library size and tokens. Longer required chains make the model expand more heads, and
   every expanded head is a place where the usable derivation is met.

This is the claim in its supported form: adding relevant information (statements that could
be used to reason to the goal, in the form of a proof of every library statement) harms the
prover more than the same tokens of lorem, of clearly irrelevant statements, or of identical-
looking statements that cannot be used; and the harm grows with the length of the chain the
prover must find.

## Assumptions behind the design
A1 Any valid proof scores; no step budget. (A budget turns search cost into failures on the
   long route; kept as a secondary condition, not used here.)
A2 Irrelevant text is skimmable, relevant text is not. This is what makes `pad` differ from
   `both`; no detectable lorem cost at n=10 (pad - lem = 0 [-10, +10]).
A3 Models use what they find first. Held: mixed routes and long searches in `both`.
A4 Derivations are interleaved with lemmas, as in retrieved context, not attached as in a file.

## Superseded runs (not to be cited)
Earlier rungs used 3-4 constants: the library held on-path lemmas for the goal's object and
for neighbour objects, and `both` unfolded all of them. They are superseded for three
reasons found in review: (1) the effect there is a decoy effect, since same-head rules per
chain head double from `lem` to `both` and ~90% of the added trees belong to alternatives
that never fire for the goal's object; (2) the cut-level arm `both:1` duplicates `both` for
depth-2 trees, so its "stated intermediates" contrast mixes cue with volume; (3) at 60k and
105k tokens, 27/90 and 30/90 solver cells grepped the prompt file instead of reading it, and
the Read-only cells fail in every arm. Their numbers, for the record only: pos1d (25k, 4
constants) lem 90 / pad 83 / both 52; pos1f cue arms both:1 76, pad:1 96, bothm 89, padm 80;
pos1e_cap (step budget) lem 83 / pad 25 / both 5; pos2d (60k) and pos_deep (105k) unusable.
The full earlier write-up is kept outside the repo.

## Harness
`smolbench/deduction/horn/` (theory, render, checker, cli, score) and
`scripts/deduction/horn/` (render_rung.sh, solve_arms.workflow.js with the Read-only
`horn-solver` agent, collect_rung.py, analysis scripts). See `scripts/deduction/horn/README.md`.
