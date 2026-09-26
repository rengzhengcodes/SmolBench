# Example prompts

The m = 6 rung of seed 7, rendered in the four arms: 6 chain lemmas, 30 open alternatives
(five per chain lemma), a depth-2 derivation tree per lemma. `render_examples.sh` regenerates
them; `theory.json` is the generated theory and `system.md` the system message every arm uses.

Goal: `gari(leb)`. Facts: 7 (m + 1), each a premise of a chain lemma.

| file | arm | lines | chars | what it contains |
|---|---|---|---|---|
| `lem.prompt.md` | lem | 56 | 1480 | the lemmas only: chain lemmas and open alternatives |
| `pad.prompt.md` | pad | 164 | 7024 | the lemmas, with a lorem line in every slot where `both` has a tree rule |
| `disc.prompt.md` | disc | 164 | 4103 | the lemmas, with the trees whose leaves are renamed, so no tree can be entered |
| `both.prompt.md` | both | 164 | 4083 | the lemmas and every lemma's derivation tree (axioms over fresh intermediates) |

`<arm>.proof.txt` is the 6-step lemma route the certificate verified for that arm.
`both.tree_proof.txt` is the 18-step tree route (every chain lemma replaced by its axioms),
valid in `both` only.

Answer format (the tail of every prompt): one step per line, `derive h(c) from a(c), b(c)`,
each step one library rule with `x` set to the constant, premises facts or earlier heads, the
last line derives the goal. The checker (`checker.verify`) matches steps by content, so rules
have no ids and any valid proof counts.

Rules are listed in one shuffled order per theory; `pad` and `disc` keep every lemma
at the position it has in `both`. Facts are listed first, then the library, then the goal.
Rungs at other chain lengths are rendered with `scripts/deduction/horn/render_rung.sh`; the
specification is `../README.md`.
