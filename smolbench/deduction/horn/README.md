# Horn-rule deduction

This package implements one fixed experiment. It measures whether adding *relevant*
information to a prover's context (statements that could be used to reason to the goal)
harms it more than adding the same amount of irrelevant text. Everything the code can
render, check or score is described here.

## 1. The claim

A prover is given facts about one object and a library of Horn rules that proves a goal
about it. The library alone (`lem`) is enough. Adding a proof of every library rule
(`both`) makes the prover fail more often than adding the same number of tokens of lorem
filler (`pad`) or of the same proofs with their entry points removed (`disc`). The harm
grows with the length of the proof the prover must find (the chain length `m`).

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

A rung with chain length `m` has the `m` chain lemmas, exactly `5 m` open alternatives,
and trees of depth 2. Thus, `m` determines the library size and prompt size. Sizes
(cl100k tokens, seed 100):

| m | lemmas | axioms | `lem` | `both` / `pad` / `disc` | rule lines in `both` |
|---|---|---|---|---|---|
| 3 | 18 | 54 | 379 | 1,034 | 72 |
| 6 | 36 | 108 | 616 | 1,935 | 144 |
| 12 | 72 | 216 | 1,091 | 3,714 | 288 |
| 24 | 144 | 432 | 2,070 | 7,323 | 576 |
| 48 | 288 | 864 | 3,987 | 14,537 | 1,152 |
| 96 | 576 | 1,728 | 7,750 | 28,911 | 2,304 |
| 192 | 1,152 | 3,456 | 15,377 | 57,537 | 4,608 |

## 3. The four arms

`render.render(theory, arm)` produces one prompt per arm. `ARMS = (lem, pad, disc, both)`.
Only these four exist.

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
arm's lines, one rule `a(x) ∧ b(x) → h(x)` or filler line per line), `## Goal`
(`Cm(c)`), `## Answer format`:

```
One step per line, nothing else:
derive <atom> from <atom>[, <atom>]
```

A step applies one library rule with `x` set to the constant; the atoms after `from` are
that rule's body atoms, each a fact or an atom derived on an earlier line; the last line
derives the goal.

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
  tree rule (an attempt to enter a tree).

Before `verify`, `extract.extract_answer(content, scoring)` removes inline reasoning and
takes the final block of step lines. There are two scoring modes:

- `iclr`: the block is the last contiguous run of step lines, so a prose line between two
  steps drops every step above it. The ICLR 2027 submission's Horn table was scored this
  way. Rows with no `scoring` field were scored this way.
- `default`: prose lines between steps are skipped. A code fence, a reasoning close tag
  (`</think>`, `[/THINK]`), a horizontal rule (`--` or longer) or a markdown heading
  still ends the block, so a draft above it is not scored.

`checker.certify(theory, rendered)` checks that rule content is unique; the goal is
derivable; every library lemma lies on a path to the goal and fires for `c`; every fact is
a premise of a chain lemma; the lemma route verifies in exactly `m` steps; in `both` the
tree route verifies as a `long` route; and in `pad` and `disc` the tree route is invalid.

## 6. Design

The released study has 100 theories (seeds 100-199) and 3 replicates per arm, paired by
theory. Each model's chain length is chosen from `lem` on disjoint calibration seeds.
The picks are recorded in `iclr.json`, and the calibration rows are in the released
results under `horn/calibration/`.

## 7. Analysis

The unit is the per-seed pass rate (mean over replicates), paired by seed across arms.
A pass rate is the mean over seeds. A contrast is the seed-paired difference in
percentage points with a 95% percentile bootstrap CI over seeds and a two-sided sign-flip
permutation p-value (exact up to 16 seeds, else 20,000 Monte Carlo draws). The reported
contrasts are relative to `both` (low density): `lem − both`, `pad − both` and
`disc − both`. `python -m smolbench.deduction.horn.repro report <rows.jsonl>...` prints
them for any rows files. The paper tables and figures come from
`notebooks/deduction/analysis/make_figures.py`.

## 8. Reproducing the released results

Fetch the results, check their manifest, and rebuild the tables and figures:

```
python -m smolbench.deduction.horn.repro fetch --out <results-folder>
python -m smolbench.deduction.horn.repro check-data <results-folder>
python notebooks/deduction/analysis/make_figures.py --data <results-folder> --out results
```

The analysis writes the paper table, the full table, the summary, ladder figures,
proof-route figures and the reasoning-length figure to `results/iclr/` (scored as
submitted) and `results/default/` (the default extractor). It takes about four minutes.
The outputs match the submitted ones byte for byte, apart from embedded PDF creation
dates.

## 9. Files

| file | role |
|---|---|
| `theory.py` | `Theory`, `Rule`, `Lemma`, `generate`; JSON round-trip |
| `render.py` | `ARMS`, `render`, `Rendered`, `Tokenizer`; lorem and disc slot fillers |
| `checker.py` | `verify`, `certify`, `designed_proof`, `closure`, `route_of` |
| `extract.py` | Scoring modes: `final_proof_block`, `extract_answer`, `verdict_fields` |
| `stats.py` | `load_rows` (dedupe by cell), `pass_rate`, `contrast` |
| `repro.py`, `iclr.json` | Protocol record; `fetch`, `check-data`, `models`, `report` |
| `../../../notebooks/deduction/analysis/` | `make_figures.py` and the table, route and reasoning-length scripts |
| `../../../tests/deduction/test_horn_*.py` | Theory, checker, scoring, reproduction, tables and figures |

`Theory.from_json` ignores legacy `facts_by_const`, accepts retired setup fields only at
their current values and a single matching `constants` entry, and drops `sublemma`
partial-cut rules.
