> Design notes written 2026-09-25 while the setup was still open. The setup has since been
> fixed to the five-arm ladder (`smolbench/deduction/horn/README.md`); the arms discussed
> here that are not among the five (deep, lem25, the S1-S5 proposals) are not implemented.

# Relevant-information setups that should degrade more than padding

Design report from an Opus 5.5 planning agent, 2026-09-25, on the Horn bench (see HORN_BOTH_VS_PAD.md for the results it builds on).

## Horn bench: "relevant information" setups that should hurt more than lorem or junk

I proposed five setups, ranked. The first to build is S1, derived-premise siblings. Before any new code, run the `junk` and `disc` arms that are already built on the existing `m12_25k` rung. How to read every setup below depends on that run.

### Constraints from the code and data that shape the designs
- **Rule syntax.** All predicates are unary and every rule uses the single variable `x`. `checker.verify` rejects any step whose premises are about a different constant than its head ("premise ... is about d, head is about c"). So cross-object bridges need a new binary-atom rule kind, with changes to the checker and the renderer. This is the costliest item on the list.
- **Where harm lands.** Only 8 of 60 `both` attempts entered a tree, but the loss showed up on lemma-level proofs. Zero of 88 `deep` proofs touched a fact-tree rule. So the cost comes from what the backward search meets at chain heads and the goal: extra same-head candidates, what it takes to check them, and the lines that mention chain words. Material inside trees or below the given facts only matters if the model is pulled into it.
- **Controls match no candidates.** `pad` and `junk` add zero same-head candidates. `junk` also shares no vocabulary with the theory. Any treatment that adds candidates at chain heads is therefore confounded with candidate count. That is acceptable under your definition (more usable rules is relevance), but a reviewer will want a control ladder.
- **Lorem is not length-matched in characters.** In the examples, `pad` has 18,480 characters where `both` has 10,646 and `junk` has 10,639, all at matched cl100k tokens. Under Haiku's own tokenizer, `pad` is probably the longer prompt. That makes `pad` a conservative control, but `junk` is the character-matched one. Any "relevant beats irrelevant" claim should be made against `junk`.
- **A new mechanism to exploit: validity removes the backtrack signal.** A dead candidate (`disc`-style) is eventually abandoned and the model returns to the short chain. A valid long candidate can always be completed, so the model commits to it and writes a longer proof. That is exactly the regime where R10 shows the pass rate falling (60% at m = 48 and 50% at m = 96 with a library to search). Every setup below exploits this.
- **Do not change task difficulty.** No added route may shorten the minimal proof: the route length through the new material must be at least the level gap it covers, or the task gets easier. `certify` should assert that `min_steps` is unchanged.

### Proposed control ladder (shared by all setups)
All controls use the same slots, the same line count and matched cl100k tokens (`pad`'s existing per-slot, debt-carrying scheme). Build them once:
- **`pad`**: lorem.
- **`junk`**: rule-shaped lines over a disjoint vocabulary.
- **`fwd`** (new, about 40 lines): lines like `minu(x) ∧ desu(x) → kopa(x)`, where `kopa` is used nowhere. The rule fires for `c`, so it looks "true and applicable", but its head is not an ancestor of the goal. That makes it irrelevant by definition while sharing the proof's vocabulary. It answers the "vocabulary overlap" objection. `certify` needs a kind-specific exception, because today it flags any extra rule that fires.
- **`hjunk`** (new, about 25 lines in `render.py`): the head is a chain head, the body is fresh names used nowhere else. It matches the same-head candidate count but is dead within one lookup.
- **`disc` / `hdisc`**: same-head candidates that are dead only after a deep search. This is a diagnostic, not a "clearly irrelevant" control.

### Worked-example base theory
Constant `leb`; the chain is the `lem.proof.txt` route in `examples/`:
```
dudi ∧ pebad → rarep;  rarep ∧ gapor → minu;  minu ∧ desu → lige;
lige ∧ ruma → gari;    gari ∧ buzef → loku;   loku ∧ pari → dume (goal)
```
`sedu` and `kova` are also facts of `leb` (both appear in the example facts). `zite` is a new fact the S3 example adds for both constants.

---

### S1 (run first). Derived-premise siblings (`sib`)

**1. What is added.** Each chain head `C_i` gets K siblings (K = 2–4) of the form `C_{i-1}(x) ∧ q(x) → C_i(x)`. Each sibling is a near-duplicate of the chain lemma: it shares the correct premise and swaps the fact for `q`. `q` is not a fact. It is derivable from facts through a chain of L binary rules (L = 6–12). Some of those chain steps get one valid internal alternative, so reaching `q` takes a search, not just a walk. No facts are added. Every added rule gets a random slot in the master order.
- `spad`: lorem in every sibling and q-chain slot.
- `sjunk`: junk in the same slots.
- `shjunk`: the siblings are kept, and the q-chain slots hold junk, so `q` is never derivable.
- `sdisc`: the siblings and q-chains are kept, but the bottom leaves are renamed, so `q` is never derivable.

Tokens are fitted by searching over L (like `_fit_fact_chain`). Line counts and lemma positions are identical across arms.

**Example (siblings at `minu` and `loku`):**
```
rarep(x) ∧ kelo(x) → minu(x)       # sibling of rarep ∧ gapor → minu
gapor(x) ∧ sedu(x) → fumi(x)
fumi(x) ∧ ruma(x) → tavo(x)
fumi(x) ∧ desu(x) → tavo(x)        # internal open alternative
tavo(x) ∧ kova(x) → kelo(x)
gari(x) ∧ vesab(x) → loku(x)       # sibling of gari ∧ buzef → loku
...q-chain for vesab (L steps from facts)
```

**2. Why every line is relevant.** `C_{i-1}(leb)` is derivable, `q(leb)` is derivable through its chain, and `C_i` lies on the chain to the goal. So each sibling instance, and each q-chain rule, appears in the valid proof "chain up to `C_{i-1}` + q-chain + sibling + chain from `C_i` to the goal". The internal alternatives are ancestors of `q`, which is an ancestor of `C_i`. The route has length (i−1) + L + 1 + (m−i), which is more than m, so the minimal proof is unchanged.

**3. Mechanism.** The search meets the siblings at every head it expands (unlike `deep`). Because a sibling shares `C_{i-1}` with the true lemma, it looks like the lemma, and `q` looks like a fact name. This targets the most common failure seen so far: asserting a derived atom as a fact ("premise not derived", 9 of 18 hand-classified failures). If the model does check `q`, the check succeeds after an L-step search, so it commits to a longer proof with no backtrack signal (see the mechanism above).

**4. Confound and answer.**
- Objection: "It's candidate count or near-duplicate surface, not relevance." Answer: `shjunk` and `sdisc` have identical sibling lines with the same surface and candidate count; only the derivability of `q` differs.
- Objection: "It's chain vocabulary." Answer: `fwd`.

The primary claim is `sib` vs `spad` and `sjunk`. `sib` vs `sdisc` is diagnostic.

**5. Code: not renderable today, about 110–130 lines.**
- `theory.py`, about 50 lines: new params `n_sib` and `sib_len`; new rule kinds `sib` and `sibch`, kept out of `lemmas()` like `fact_tree_keys`; built after the alternatives loop and before `order` is shuffled.
- `render.py`, about 30 lines: arms added to `_ARM_RE` and to the present/padded sets in `arm_keys`; the `sdisc` leaf-rename is a variant of `_disc_rule`.
- `checker.certify`, about 15 lines: every `q` is derivable (or, for `sdisc`, not derivable), and `min_steps` is unchanged.
- `cli.py` fit, about 20 lines.

**6. Prediction and pilot.**
- Predicted effect: `sib` − `spad` = −20 to −35 at m = 12, 25k.
- Signature: failure reasons will name a sibling precondition, e.g. "premise not derived: kelo(leb)". The checker already logs this, and `used_kinds` will show `sib`.
- Pilot: fresh seeds (130–139), m = 12, 25k, arms {`spad`, `sjunk`, `sib`}, 10 theories × 3 samples = 90 cells.
- Go/no-go: if `sib` − `spad` ≤ −20, extend to 20 theories and add `sdisc` and `fwd`. Twenty theories × 2 samples is better than 10 × 3, because the variance is mostly between theories.

**Why first.** It is the cheapest new generator code. It aims at the documented failure mode at the exact place the backward search walks. It has a clean contrast where only derivability changes. It reuses the existing `pad`/`junk` machinery unchanged.

---

### S2. Bridged objects: making former decoys relevant (`bridge` vs `nobridge`)

**1. What is added.** Start from the existing multi-constant generator (`n_constants` > 1, blocked alternatives, and the "full" decoy that holds every fact). Add:
- a binary fact `nabo(leb, d)` for each decoy `d`;
- for each chain head `H` that is targeted by blocked alternatives, one bridge rule `nabo(x, y) ∧ H(y) → H(x)`.

The facts, including the link facts, are identical in every arm, so the arms differ only in rules.
- `bridge`: the lemmas, blocked alternatives and bridges.
- `nobridge`: the blocked alternatives are kept, and the bridge slots hold lorem. This is the old, criticised decoy design at matched tokens.
- `bpad`: lorem in both the alternative and bridge slots.
- `bjunk`: junk in both.

**Example:**
```
Facts: nabo(leb, dak); dak: dudi pebad gapor desu vonu zite ...; leb: (no vonu)
lige(x) ∧ sopa(x) → gari(x)          # dead for leb, fires for dak
desu(x) ∧ vonu(x) → sopa(x)
nabo(x, y) ∧ gari(y) → gari(x)       # bridge
Proof: ...lige(dak); derive sopa(dak) from desu(dak), vonu(dak);
derive gari(dak) from lige(dak), sopa(dak);
derive gari(leb) from nabo(leb, dak), gari(dak); derive loku(leb) ...
```

**2. Relevance, stated precisely.** A rule is relevant if and only if some ground instance of it appears in a valid derivation of `goal(c)`. `certify` should compute the ground closure and the ground ancestor set of `goal(c)`, then require at least one such instance for every shown rule and every fact added for `d`. The bridge carries `gari(dak)` into `gari(leb)`, so dak's blocked alternatives are ancestors of the goal. The bridged route is longer than the chain, so the minimal proof is unchanged.

**3. Mechanism.**
- At `gari(leb)` the search meets rules that fail for `leb` but work for `dak`, plus the bridge. This forces the model to carry constants.
- New error types become available: wrong constant, wrong bridge direction, and asserting `gari(dak)` without deriving it.
- Rather than abandoning dead rules (as in the old design), the model can complete a long, other-object subproof.
- The old decoy version gave −30 to −60, so there is headroom.

**4. Confound and answer.**
- Objection: "Binary atoms and the new syntax make it harder." Answer: `nabo` facts and a bridge-shaped line appear in every arm, including `lem`. For example, give `lem` one bridge on a head where the bridged route is valid but pointless, or make one chain step a bridge in all arms.
- `bridge` vs `nobridge` is the cleanest test of relevance per se: the same alternative lines flip from decoy to relevant because of about m short lines.
- The primary claim is still against `bpad` and `bjunk`.

**5. Code: about 250 lines.**
- `theory.py`, about 60 lines: bridges, link facts, and ensuring every blocked rule fires for some linked decoy.
- `render.py`, about 25 lines: binary atoms in the facts section and rule text.
- `checker.py`, about 100 lines: a binary-atom regex, variable binding for the bridge kind, allowing mixed constants only in bridge steps, and the ground-relevance certificate.
- Tests.

**6. Prediction and pilot.**
- Predicted effect: `bridge` − `bpad` = −25 to −45. The sign of `bridge` − `nobridge` is genuinely uncertain.
- Pilot: 10 × 3 × {`bpad`, `nobridge`, `bridge`} = 90 cells.

**Decoy traps here.** A link in the wrong direction (`nabo(dak, leb)`), a missing link fact, or a blocked rule whose decoy has no link: each of these makes the rules decoys again.

---

### S3. Long parallel routes with their own library (`par`), your lead (a)

**1. What is added.** K parallel chains, each of length L. They attach at the goal and at a few chain heads through a top rule `P_L ∧ F → T`. `P_1` is built from facts. Each `P_j` gets 0–2 valid internal open alternatives, so entering a route means searching a small library, which is the R10 m = 48 regime.
- Constraint: L + (m − level(T)) + 1 ≥ m, so the minimal proof stays m.
- At 20k tokens, about 10 routes of L = 24–48 fit.
- Controls: `ppad` and `pjunk` in the same slots; `pdisc` has the bottom entries renamed (dead long routes, same top candidates); `lemK` has one compact direct open alternative per attach point, matching the same-head count.

**Example (route into the goal):**
```
kova(x) ∧ zite(x) → tabu(x)
tabu(x) ∧ sedu(x) → sefo(x)
sefo(x) ∧ desu(x) → niral(x)
tabu(x) ∧ ruma(x) → niral(x)     # internal alternative
niral(x) ∧ gapor(x) → voke(x)
... (L steps)
bimo(x) ∧ pari(x) → dume(x)      # new candidate for the goal
```

**2. Relevance.** Every route rule's instance at `leb` lies on the valid proof "route + top rule + chain from T to the goal".

**3. Mechanism.** The top rule is a candidate at a head the search expands. Haiku does not minimise proofs (alt-library proofs average 19.5 steps at m = 12), so it plausibly enters a route. Once inside, completion is always possible, so there is no backtrack signal, and it faces an m = 48-style search.

**4. Confound and answer.** "It's candidate count": `lemK`. "It's dead structure": `pdisc`.
- This setup is weaker per token than S1. With about 8 candidates at the goal, the chance of entering a route per attempt is modest. The effect needs many attach points.

**5. Code: about 110 lines.** Generator about 60 (a generalisation of the existing two-step `mid` detour), render about 20, cli fit about 20, certify about 10.

**6. Prediction and pilot.**
- Predicted effect: −10 to −25 at m = 12, and larger on an m = 24 base.
- Pilot: 90 cells, as for S1.
- Gate it on the m = 48 both/pad test that is already running. If derivations hurt more when the chain is long, raise S3's priority.

---

### S4. Spine unfoldings (`spine`): lemma derivations as long hidden-precondition chains

**1. What is added.** Same slots and matching as `both`/`pad`/`junk`/`disc`, but each lemma's derivation tree is a caterpillar (a long single spine) rather than a full binary tree. The root becomes the one-premise rule `t_L → h`.

**Example (lemma `rarep ∧ gapor → minu` kept, plus):**
```
rarep(x) ∧ gapor(x) → sulo(x)
sulo(x) ∧ rarep(x) → pemi(x)
pemi(x) ∧ gapor(x) → daki(x)
daki(x) → minu(x)                 # one-premise same-head root
```

**2. Relevance.** Identical to `both`: each spine rule derives an ancestor of `h` from the lemma's body.

**3. Mechanism.** It keeps `both`'s one same-head root per lemma, but the root's precondition is L − 1 steps deep. The root is also one-premise, and a library full of valid one-premise rules at heads legitimises one-premise steps. That should feed the invented-rule failure (two rules fused into an invented one-premise rule) as well as the undischarged-premise failure.

**4. Confound and answer.** "Different tree shape, not relevance." The contrast `spine` vs `both` at equal tokens isolates root-precondition depth; `disc` built on spines gives the dead version. The claim against `pad`/`junk` is as before.

**5. Code: about 60–80 lines.** `_build_tree` needs a shape option, and `leaves_under`/`cut` must handle leaves at varying depth (`leaves_under` assumes `len(p) == height`). After that, all existing arms work.

**6. Prediction and pilot.** −15 to −30. Pilot: 10 × 3 × {`pad`, `both`, `spine`}, where the `both` cells re-measure the known effect as a calibration.

---

### S5. Bushy trees (`bushy both`): ranked last

**1. What is added.** `both`, plus 1–2 valid alternative axioms at each internal tree node, with bodies drawn from derivable nodes lower in the same tree. Matched to `pad` as usual.

**2. Relevance.** Each alternative derives a tree node, which is an ancestor of the lemma head.

**3. Mechanism.** Entering a tree becomes a search.

**Why last.** Only 8 of 60 `both` attempts entered a tree. Material inside trees is rarely met, and this adds no new candidates at chain heads. I expect roughly `both`'s −20, with little extra.

**5. Code:** about 50 lines in `_build_tree` and `cut`.

---

### Step 0 (zero code, do first): `junk` and `disc` on the existing `m12_25k` rung
10 theories × 3 samples × 2 arms = 60 cells. This tells us whether dead same-head candidates (`disc`) cost as much as valid ones (`both`), and whether rule shape (`junk`) costs anything relative to `pad`. If `disc` is at or below `both`, the S1–S4 claims must rest on `pad`/`junk`/`fwd`, not on "validity per se".

### Setups that look relevant but are decoys (or inert) under the definition
- **Forward-fireable dead ends** (`fwd`): true, and they fire for `c`, but their heads are not ancestors of the goal, so they are irrelevant. This is the most seductive false positive.
- **Other-object rules with no usable bridge**: the old multi-constant design, S2 with a missing or reversed link, or blocked rules for an unlinked decoy.
- **`disc`, `sdisc`, `pdisc`, `hjunk`**: same-head candidates that are never derivable, so decoys by construction. They are useful as controls only.
- **Siblings whose `q` is not derivable** (S1 without its q-chain): decoys.
- **`deep`**: relevant by the definition but inert. It is never visited, so it is not a decoy, just unreachable by the model's search.
- **Any added route that shortens the minimal proof**: relevant, but it makes the task easier, so it is not a fair treatment. `certify` should reject it.

### Three biggest risks
1. **Dead controls may hurt as much as valid material.** `disc`, `sdisc` or `nobridge` may cost as much as, or more than, the valid versions: an undischargeable premise invites the same "assert it as a fact" error. The claim would then reduce to "same-head candidates cost", not "relevance costs". Mitigation: pre-register the primary contrasts against `pad` and `junk` (plus `fwd` for vocabulary) and report `disc`-type contrasts as diagnostics.
2. **Power and heterogeneity.** The noise floor is about ±15 points at 10 × 3 (`pad` − `dpad` was +16.7 with near-identical prompts), and `both` − `pad` ranged from −30 to −10 across theory sets. Use fresh seeds, 20+ theories × 2 samples, a pre-registered go/no-go, and Holm correction across the new contrasts.
3. **Matching and format artifacts.** cl100k matching does not match Haiku's tokenizer or character counts (lorem has about 74% more characters than rule lines). S2 introduces binary syntax and cross-constant steps. The Read-chunked solver is sensitive to line count, so keep line counts identical across arms. Mitigations: use `junk` as the character-matched primary control, put bridge syntax in every arm including `lem`, assert identical line counts and lemma offsets in `certify`, and later confirm with single-context API calls.

### Critical files
All under `/tmp/claude-1000/-home-fisherxue-SmolBench-stack3/5bb1813f-c09f-47cd-81ba-0a438c80d47f/scratchpad/horn_branch/`:
- `smolbench/deduction/horn/theory.py`: generator (siblings, parallel routes, bridges, spine shape)
- `smolbench/deduction/horn/render.py`: `_ARM_RE`, `arm_keys`, `_junk_rule`/`_disc_rule`, new `fwd`/`hjunk` controls
- `smolbench/deduction/horn/checker.py`: `verify` (binary atoms, bridge steps), `certify` (ground relevance, unchanged minimal proof, inertness of the controls)
- `smolbench/deduction/horn/cli.py`: token fitting (`_fit_fact_chain` pattern for L and K)
- `notebooks/deduction/HORN_ROSTER_PLAN.md`: arms and roster to extend