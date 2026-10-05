# Horn bench: the experimental setup

This package implements one fixed experiment. It measures whether adding *relevant*
information to a prover's context (statements that could be used to reason to the goal)
harms it more than adding the same amount of irrelevant text. Everything the code can
render, check or score is described here.

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
arm's lines, one rule `a(x) ∧ b(x) → h(x)` or filler line per line, no ids), `## Goal`
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

Before `verify`, `extract.extract_answer(content)` removes inline reasoning blocks and
takes the last contiguous run of step lines. A non-step line ends the run, so a draft
written above the final proof is not scored. This is the rule the ICLR 2027 results were
scored with.

## 6. Rendering a rung

```
python -m smolbench.deduction.horn.cli render --seeds 100-199 --m 12 --out rungs/m12
```

writes `<out>/s<seed>/theory.json` and `<out>/s<seed>/<arm>/{prompt.md,system.md,meta.json}`
for the four arms of every seed, and certifies each arm before it is written. Seeds are a
comma list of numbers and `a-b` ranges. `meta.json` holds what the checker needs (rule
ids by line, facts, goal), the certificate, the designed proof and the tree depths. The
chain length `m` is the one parameter. Rendering is deterministic: the same seed at the
same `m` gives the same files, byte for byte, on any machine. The same seed at different
`m` shares nothing beyond the recipe.

## 7. Running

Served models: `scripts/deduction/horn/sweep.py` sends each cell (arm x seed x replicate)
as one chat completion to an OpenAI-compatible endpoint (vLLM), with the system prompt,
temperature 0.7, the roster model's thinking arguments, and no tools. The output cap is
`--max-tokens` (default 32,768; the ICLR runs used 131,072), cut per cell so that prompt
and output fit `--context-length` (131,072). The answer is extracted as in section 5, and `finish_reason = length` scores as a failure. Rows go to a JSONL file,
keyed by (model, rung, arm, seed, replicate); rerunning the same command resumes, and a
second sweep on the same file is refused. `bedrock_sweep.py` does the same over the AWS
Bedrock Converse API (`--extra-fields '{"reasoning_effort": "high"}'` switches thinking
on for GLM-4.7, DeepSeek-V3.1 and Nemotron-3).

Design: 100 theories (seeds 100-199) x 3 replicates per arm, paired by theory. Per model,
the chain length is chosen from `lem` alone on disjoint calibration seeds (200-209):
`scripts/deduction/horn/calibrate_m.py` starts at a prior (the pick of the closest
calibrated relative in the same family), steps up the ladder m in {1, 2, 3, 4, 6, 8, 10,
12, 16, 20, 24, 32, 48, 64, 96, 192} while more than 8 of 10 pass and down while fewer than
7 pass, and stops when 7 or 8 pass, when the target is bracketed by a level already run,
or at the ladder's end. The pick is the level nearest the target crossing of a logistic
fit over the levels run (`calibration_pick.py`; `--target` is 0.75 in `calibrate_m.py`
and 0.70 in `calibration_pick.py`). Two models ran this search: `deepseek-v4-flash` and
`qwen3.5-397b-a17b` (whose m was then set by hand). The other 14 ran a longer ladder
(up to 17 levels) on seeds 200-229, with up to 30 theories per level; the levels and
theory counts for each model are in the released calibration rows. The picks are
recorded in `iclr.json`, and the calibration rows are in the released results
(`horn/calibration/`).

## 8. Analysis

Unit: the per-seed pass rate (mean over replicates), paired by seed across arms
(`stats.py`). A pass rate is the mean over seeds. A contrast is the seed-paired
difference in percentage points with a 95% percentile bootstrap CI over seeds and a
two-sided sign-flip permutation p-value (exact up to 16 seeds, else 20,000 Monte Carlo
draws). The reported contrasts are relative to `both` (low density): `lem − both`,
`pad − both` and `disc − both`. `python -m smolbench.deduction.horn.repro report
<rows.jsonl>...` prints them for any rows files. The paper tables and figures come from
`notebooks/deduction/analysis/make_figures.py` (section 9).

## 9. Reproducing the ICLR 2027 results

### From the released results (no model runs)

The released results folder holds every prompt, model output and verdict behind the
paper's Horn table, and the calibration runs (`README.md` in the folder describes the
layout and fields). To regenerate the tables and figures:

```
python notebooks/deduction/analysis/make_figures.py --data <results-folder> --out results
```

This checks the folder against its `MANIFEST.json`, then writes the paper table
(`horn_table.tex`), the full table, the summary, the ladder figures, the proof-route
figures and the reasoning-length figure to `results/`. It takes about four minutes. The outputs match
the submitted ones byte for byte (PDFs up to their embedded creation date).

### Running the experiments again

`iclr.json` records the protocol of the submission's runs: seeds, replicates, sampling,
each model's chain length and serving settings (the pinned checkpoint revision
of every self-hosted model, the Bedrock model id and request fields otherwise), a SHA-256
digest of every served theory, and the published pass rates.
`repro.py` reads it.

1. Check the pipeline offline, with no model (about ten seconds):

   ```
   python scripts/deduction/horn/demo.py --out /tmp/horn_demo
   ```

   The demo renders a small rung, serves the designed proofs from a local
   OpenAI-compatible server, runs `sweep.py` and prints the report. Every cell passes.

2. List the models and their chain lengths:

   ```
   python -m smolbench.deduction.horn.repro models
   ```

3. Get a model's rung (seeds 100-199 at its `m`). The released results folder holds the
   served prompts (`horn/prompts/m<m>/`, a rung directory the sweep runs directly). To
   regenerate them instead, render from the seeds; the command checks the files against
   the recorded digests, and `OK` means they are byte-identical to the prompts the model
   was served:

   ```
   python -m smolbench.deduction.horn.repro render --model glm-4.7 --out rungs/m48
   ```

4. Print the commands that run the model with the protocol's settings. For a
   self-hosted model, the first command serves the pinned checkpoint with vLLM (the image
   digest is in `iclr.json`); for a Bedrock model, the sweep uses your AWS credentials:

   ```
   python -m smolbench.deduction.horn.repro command --model qwen3.5-27b --rung rungs/m64 --out rows.jsonl
   ```

5. Compare the rows with the published values:

   ```
   python -m smolbench.deduction.horn.repro report rows.jsonl
   ```

Sampling runs at temperature 0.7, so a rerun reproduces the numbers up to sampling noise
(the published CIs give the scale), not row for row. Serving numerics also differ across
GPU types and tensor-parallel layouts.

## 10. Files

| file | role |
|---|---|
| `theory.py` | `Theory`, `Rule`, `Lemma`, `generate`; JSON round-trip |
| `render.py` | `ARMS`, `render`, `Rendered`, `Tokenizer`; lorem and disc slot fillers |
| `checker.py` | `verify`, `certify`, `designed_proof`, `closure`, `route_of` |
| `extract.py` | `final_proof_block`, `extract_answer`, `verdict_fields`: the answer extraction |
| `stats.py` | `load_rows` (dedupe by cell), `pass_rate`, `contrast` |
| `cli.py` | `render` (certifies and writes a rung) and `check` |
| `repro.py`, `iclr.json` | the ICLR protocol record; `models`, `render`, `command`, `report`, `check-data` |
| `../../../scripts/deduction/horn/` | sweep drivers (`sweep.py`, `bedrock_sweep.py`), calibration, `demo.py` |
| `../../../notebooks/deduction/analysis/` | `make_figures.py` and the table, route and reasoning-length scripts |
| `../../../tests/deduction/test_horn_*.py` | generator, checker, certificate, drivers, extraction, reproduction, figures |

`Theory.from_json` ignores legacy `facts_by_const`, accepts retired setup fields only at
their current values and a single matching `constants` entry, and drops `sublemma`
partial-cut rules.
