# Example prompts

One theory (seed 7, one constant, chain length m=6, depth-2 derivation trees, small token
budgets so the files stay readable), rendered in every arm. `render_examples.sh` regenerates
them; `theory.json` is the generated theory and `system.md` the system message every arm uses.

Goal: `dume(leb)`. Facts: 35 (of which 28 are deep facts, used only by `deep`); every given fact is a premise of some rule.
Library: 6 chain lemmas + 92 open alternatives.

| file | arm | lines | chars | what it contains |
|---|---|---|---|---|
| `lem.prompt.md` | lem | 145 | 3349 | the lemmas only (chain lemmas + open alternatives) |
| `pad.prompt.md` | pad | 436 | 18395 | the lemmas + lorem lines in the slots where `both` has tree rules |
| `both.prompt.md` | both | 436 | 10522 | the lemmas + every lemma's derivation tree (axioms over fresh intermediates) |
| `junk.prompt.md` | junk | 436 | 10511 | the lemmas + rule-shaped lines over a disjoint vocabulary in the tree slots (clearly irrelevant) |
| `disc.prompt.md` | disc | 436 | 10523 | the lemmas + the trees with their leaves renamed, so no tree can be entered |
| `deep.prompt.md` | deep | 446 | 9295 | the lemmas + derivation trees below the given facts (deep facts are also given) |
| `dpad.prompt.md` | dpad | 446 | 15278 | the lemmas + lorem in the fact-tree slots |
| `ax.prompt.md` | ax | 339 | 8119 | the trees only (the long route is the only route) |

`<arm>.proof.txt` is the designed proof the certificate verified for that arm: the 6-step
lemma route everywhere except `ax`, where it is the full tree route.

Answer format (the tail of every prompt): one step per line, `derive h(c) from a(c), b(c)`,
each step one library rule with `x` set to the constant, premises facts or earlier heads, the
last line derives the goal. The checker (`checker.verify`) matches steps by content, so rules
have no ids and any valid proof counts.

Rules are listed in one shuffled order per theory; `pad`, `junk`, `disc` and `dpad` keep every
lemma at the position it has in `both` / `deep`. Facts are listed first, then the library,
then the goal. Full-size rungs (25k tokens, m = 6/12/24, 30 theories) are rendered with
`scripts/deduction/horn/render_rung.sh`.
