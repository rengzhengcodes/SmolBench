# Horn bench: the experimental setup

This package implements one fixed experiment. It measures whether adding *relevant*
information to a prover's context (statements that could be used to reason to the goal)
harms it more than adding the same amount of irrelevant text. Everything the code can
render, check or score is described here. Variants tried on the way to this setup are
retired; their code is on the git branch `horn-deduction-archive` and their results are
listed in `notebooks/deduction/HORN_BOTH_VS_PAD.md`.

## 1. The claim

A prover is given facts about one object and a library of Horn rules that proves a goal
about it. The library alone (`lem`) is enough. Adding a proof of every library rule
(`both`) makes the prover fail more often than adding the same number of tokens of lorem
filler (`pad`) or of the same proofs with their entry points removed (`disc`). The harm grows with the length of the proof the prover
must find (the chain length `m`).

## 2. The theory

`theory.generate(seed, m, height, n_extra, depths)` builds one theory. Every name is a
pseudo-word drawn from the seed, so nothing can be recalled from training.

| element | definition |
|---|---|
| constant | one object `c`. Every predicate is unary; every rule is over the variable `x`. |
| facts | `m + 1` predicates `F0 .. Fm`, all true of `c`. Each is a premise of one chain lemma; no fact is idle. |
| chain | `F0 ∧ F1 → C1`, `C1 ∧ F2 → C2`, ..., `C(m-1) ∧ Fm → Cm`. `Cm` is the goal. Its `m` steps are the shortest proof. |
| open alternatives | `n_extra` more lemmas. Each has a head that is a chain head (or an intermediate that an earlier alternative introduced) and a body that is derivable for `c`. One premise sits at most one level below the head, so no route skips a chain level: every route to the goal has at least `m` steps. An alternative is one rule, or a two-step detour through a fresh intermediate. |
| derivation trees | Every lemma `i` (chain or alternative) has a binary tree of depth `H_i >= 2`. The internal node `p` is the two-premise axiom `pred(p0) ∧ pred(p1) → pred(p)` over fresh intermediates; the `2^H_i` leaves are the lemma's body atoms, each used at least once. The axioms derive the lemma's head from its body in `2^H_i - 1` steps. The root axiom shares the lemma's head, so it is a second same-head candidate for that head. |
| master order | one shuffle per seed of every rule. An arm shows a subset of it, so a lemma has the same position in every arm. |

Every rule is unique by content (head and body set). The library is a DAG: a rule's
premises all have a lower level than its head (facts 0, chain head `i` at level `i`, a
detour's intermediate half a level below its head).

A rung is defined by its chain length `m` alone (`cli.build_theory`): the library holds
the `m` chain lemmas and exactly `5 m` open alternatives, and every tree has depth 2, so
the prompt size follows from `m`. Sizes (cl100k tokens, seed 100):

| m | lemmas | axioms | `lem` | `both` / `pad` / `disc` | rule lines in `both` |
|---|---|---|---|---|---|
| 3 | 18 | 54 | 379 | 1,034 | 72 |
| 6 | 36 | 108 | 616 | 1,935 | 144 |
| 12 | 72 | 216 | 1,091 | 3,714 | 288 |
| 24 | 144 | 432 | 2,070 | 7,323 | 576 |
| 48 | 288 | 864 | 3,987 | 14,537 | 1,152 |
| 96 | 576 | 1,728 | 7,750 | 28,911 | 2,304 |
| 192 | 1,152 | 3,456 | 15,377 | 57,537 | 4,608 |

So a rung fixes the composition of the library (six lemmas per chain level, three axioms
per lemma) and `m` scales the chain, the search space and the tokens together.

## 3. The four arms

`render.render(theory, arm)` produces one prompt per arm. `ARMS = (lem, pad, disc, both)`.
Only these four exist. A fifth arm, `junk` (rule-shaped lines over a vocabulary that
appears nowhere else), was run on Haiku and on Ministral-3-14b and retired on
2026-09-26: it sat level with lorem for Haiku and cost as much as `disc` for the
non-thinking Ministral, so `disc` carries the rule-shaped control alone.

| arm | library section | what the extra lines are |
|---|---|---|
| `lem` | the lemmas, in master order | nothing |
| `both` | the lemmas and every axiom, in master order | true rules on a derivation of the goal: a proof of every lemma (about four times `lem`'s tokens) |
| `pad` | `lem` with a lorem line in every axiom's slot | filler of the same token count per slot |
| `disc` | `both` with every tree's leaves renamed | the same trees, same-head root rules included, but the leaves are fresh predicates that are never facts, so no tree can be entered |

Matching. `pad` and `disc` have `both`'s line count, its token count within one token
per slot (rounding debt is carried from slot to slot), and every lemma at the token
offset it has in `both`. `disc` also has `both`'s rule count. The three larger arms
differ only in what the tree slots hold.

What each contrast isolates:

| contrast | what differs |
|---|---|
| `pad − lem` | prompt length (irrelevant filler) |
| `disc − pad` | rule-shaped text that offers a second same-head candidate at every lemma head, with preconditions that cannot be discharged |
| `both − disc` | the trees can be entered: every added line is usable |
| `both − pad` | the primary contrast: usable derivations vs filler of equal length |

## 4. The prompt

System message (`render.SYSTEM`): "You are a careful theorem prover. Answer with a proof in
exactly the requested format and nothing else."

User message, in this order: one line of instructions (the goal is always provable),
`## Facts` (the `m + 1` fact atoms `F(c)`, shuffled once per seed), `## Library` (the
arm's lines, one rule `a(x) ∧ b(x) → h(x)` or filler line per line, no ids), `## Goal`
(`Cm(c)`), `## Answer format`:

```
One step per line, nothing else:
derive <atom> from <atom>[, <atom>]
```

A step applies one library rule with `x` set to the constant; the atoms after `from` are
that rule's body atoms, each a fact or an atom derived on an earlier line; the last line
derives the goal. `examples/` holds a small rendered theory in every arm.

## 5. The checker

`checker.verify(theory, rendered, text, finish_reason)` scores an answer.

- Parsing: a line is a step if it matches `derive <head> from <atoms>` after optional
  numbering; a trailing `by ...` is ignored; other lines are ignored (a model may think
  before it answers); a bare predicate is read as `pred(c)`.
- A step is valid if a rule with exactly that head and body set is shown in the arm and
  every body atom is a fact or was derived earlier. Any valid derivation of the goal
  passes, not only the designed one; there is no step budget.
- Verdicts: `success`; `invalid_step` (the reason names the first bad step: an invented
  rule, an underived premise, an unknown constant); `incomplete` (valid steps, goal not
  derived); `given_up`; `no_answer`; `length` (the output cap was hit); `exception`
  (infrastructure, not scored).
- Route: `short` if only lemmas were applied, `long` if only tree rules, `mixed`
  otherwise, over the valid steps plus the failing step's rule. A `disc` rule counts as a
  tree rule (an attempt to enter a tree); a `junk` rule counts as nothing.

`checker.certify(theory, rendered)` runs on every arm before it is written. It checks
that rule content is unique; the goal is derivable; every library lemma lies on a path to
the goal and fires for `c`; every fact is a premise of a chain lemma; the lemma route
verifies in exactly `m` steps; in `both` the tree route (every chain lemma replaced by its
axioms) verifies as a `long` route; in `pad` and `disc` the tree route is invalid and the
added rules never fire and derive nothing new.

## 6. Rendering a rung

```
M=12 SEED0=100 NSEEDS=30 scripts/deduction/horn/render_rung.sh <out>
```

writes `<out>/s<seed>/theory.json` and `<out>/s<seed>/<arm>/{prompt.md,system.md,meta.json}`
for the four arms of 30 theories (`python -m smolbench.deduction.horn.cli render` does one
seed). `meta.json` holds what the checker needs (rule ids by line, extra rules, facts,
goal), the certificate, the lemma route and the tree depths. The chain length `m` is the
one parameter. The same seed at the same `m` gives the same theory; the same seed at
different `m` shares nothing beyond the recipe.

## 7. Running

Haiku (Claude Code): `scripts/deduction/horn/solve_arms.workflow.js` gives one Read-only
Haiku subagent per cell (arm x theory x sample); the agent reads the prompt file and
returns the proof. `collect_rung.py` writes the answers into the rung and scores them.
Cells whose agent used a search tool are listed by `grep_excluded.py`, and cells that
returned no proof (contamination by the parent chat) are refilled. See
`scripts/deduction/horn/README.md`.

Served models: `scripts/deduction/horn/sweep.py` sends each cell as one chat completion
(system message + prompt) with a 32,768-token output cap, temperature 0.7, the roster
model's thinking arguments, and no tools; the answer is the last block of `derive` lines
after the reasoning is stripped. `finish_reason = length` scores as a failure.

Design: 100 theories (seeds 100-199) x 3 samples per arm, paired by theory. Per model,
the chain length is chosen from `lem` alone on disjoint calibration seeds: `scripts/
deduction/horn/calibrate_m.py` starts at a prior (the pick of the closest calibrated
relative in the same family), runs 10 theories (seeds 200-209) at that level, steps up
the ladder m in {1, 2, 3, 4, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64, 96, 192} while more than
8 of 10 pass and down while fewer than 7 pass, and stops when 7 or 8 pass (2 to 3
failures in 10), when the target is bracketed, or at the ladder's end; the pick is the
level nearest the 75% crossing of a logistic fit over the levels run
(`calibration_pick.py`). The first seven models were calibrated on the full ladder with 30
theories per level (seeds 200-229) before this rule was set; their picks stand
(`notebooks/deduction/HORN_ROSTER_PLAN.md`). AWS Bedrock models run through
`bedrock_sweep.py` (Converse API; `reasoning_effort: high` switches thinking on for GLM-4.7
and Nemotron-3).

## 8. Analysis

Unit: the cell mean over samples, paired by theory seed across arms. Contrasts are
seed-paired differences in percentage points with a percentile bootstrap over seeds
(95%) and an exact two-sided sign-flip permutation p-value (`pilot_analysis.py`). The
primary contrast is `both − pad`; `both − disc` shows the harm is not rule-shaped text
or dead candidates; `pad − lem` is the length cost. `route_analysis.py`
reports, per arm, how many attempts used a tree rule and where failures occur.

## 9. Reference result (Haiku, seeds 100-109 x 3)

These rungs predate the ratio definition: their library was fitted to 5k tokens of
lemmas (about 400 at every `m`, so 32 alternatives per chain lemma at m = 12 and 6.8 at
m = 48) and their trees to 20k tokens (a depth-2 / depth-3 mix). The m = 48 rung is
therefore close to the current definition; the m = 12 rung had a much larger library.

| arm | m = 12 | m = 48 | m = 48 attempts using a tree rule |
|---|---|---|---|
| lem | 93.3% | 73.3% | 0/30 |
| pad | 96.7% | 53.3% | 0/30 |
| junk | 96.7% | 50.0% | 0/30 |
| disc | 96.7% | 53.3% | 1/30 |
| both | 86.7% | 3.3% | 11/30 |

At `m = 48`: `both − pad` = −50 [−70, −30], p = 0.008; `both − junk` = −46.7, p = 0.016;
`both − disc` = −50, p = 0.004; the controls sit within 4 points of each other. The
mechanism: usable derivations are entered and committed to (a valid candidate passes the
first lookup, so there is no signal to backtrack), while dead candidates are rejected
after one lookup. Failures assert a derived chain head as a fact or invent a one-premise
rule inside a tree. Details and history: `notebooks/deduction/HORN_BOTH_VS_PAD.md`.

## 10. Files

| file | role |
|---|---|
| `theory.py` | `Theory`, `Rule`, `Lemma`, `generate`; JSON round-trip |
| `render.py` | `ARMS`, `render`, `Rendered`, `Tokenizer`; lorem and disc slot fillers |
| `checker.py` | `verify`, `certify`, `designed_proof`, `closure`, `route_of` |
| `cli.py` | `render` (fits the budgets, certifies, writes a rung) and `check` |
| `score.py` | scores `answer.s<i>.md` files under a rung into `scores.jsonl` |
| `examples/` | one small theory rendered in every arm, with its designed proofs |
| `../../../scripts/deduction/horn/` | rung renderer, Haiku workflow, served-model driver, analysis |
| `../../../tests/deduction/test_horn_bench.py`, `test_horn_sweep.py` | invariants, matching, checker, certificate, driver |

Compatibility. `Theory.from_json` loads theories written before the setup was fixed when
they match it (one constant, no derivations below the facts); the retired partial-cut
rules they carry are dropped. The theories behind the reference result were generated by
the archived generator with token-fitted budgets and carry two extra given facts (in the
`m = 48` theories one of them is idle); the current generator takes no token budget, adds
no extra facts, and its theories differ from the archived ones for the same seed.
