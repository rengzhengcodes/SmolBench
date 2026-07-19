# CategoryTheory.Limits.pullbackIsoUnopPushout_hom_inl   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Limits/Opposites.lean`  

**Ground-truth tail (from k):**
```lean
rw [← pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]
```

**True premises at k:** `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst`, `CategoryTheory.Iso.hom_inv_id_assoc`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ · | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ · ✓ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 145.5s, verify 0.1s, in=311, out=5278)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_hom]
apply pullback.fst_unique
simp
rw [← comp_assoc]
simp
rw [← comp_assoc]
simp
```

**lean_error:** tail step 1/7 ('simp [pullbackIsoUnopPushout_hom]'): unknown identifier 'pullbackIsoUnopPushout_hom'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 189.8s, verify 0.1s, in=311, out=7137)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 222.2s, verify 0.1s, in=311, out=8629)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw (pullbackIsoUnopPushout f g).hom_comp_inl_unop
```

**lean_error:** tail step 1/1 ('rw (pullbackIsoUnopPushout f g).hom_comp_inl_unop'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 248.7s, verify 0.2s, in=311, out=9795)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pullback.hom_ext
dsimp [pullback_iso_unop_pushout]
rw ← pushout.condition_unop
simp only [category.id_comp, comp_assoc]
apply (pullback_property f g _ _ _).1
exact ⟨pullback.fst, pullback.snd, by simp⟩
```

**lean_error:** tail step 1/6 ('apply pullback.hom_ext'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.7s, verify 0.1s, in=311, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout]
```

**final state (truncated):**
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=311, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=311, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.1s, in=311, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout]
```

**final state (truncated):**
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.2s, verify 0.1s, in=311, out=131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_hom_inl_unop]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_hom_inl_unop]'): unknown identifier 'pullbackIsoUnopPushout_hom_inl_unop'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=311, out=140)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_hom]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_hom]'): unknown identifier 'pullbackIsoUnopPushout_hom'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.1s, verify 0.1s, in=311, out=222)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_hom_inl]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_hom_inl]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.9s, verify 0.1s, in=311, out=246)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_hom_comp_unop_inl]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_hom_comp_unop_inl]'): unknown identifier 'pullbackIsoUnopPushout_hom_comp_unop_inl'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 82.6s, verify 0.1s, in=763, out=3039)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw pullbackIsoUnopPushout_inv_fst
simp [CategoryTheory.Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 100.5s, verify 0.2s, in=763, out=3656)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pullbackIsoUnopPushout_inv_fst]
simp [comp_assoc, CategoryTheory.Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw [pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 126.7s, verify 0.1s, in=763, out=4591)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw pullbackIsoUnopPushout_inv_fst
rw comp_assoc
rw Iso.hom_inv_id_assoc
```

**lean_error:** tail step 1/3 ('rw pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 186.9s, verify 0.1s, in=763, out=7012)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw pullbackIsoUnopPushout_inv_fst
rw ← Category.assoc
erw (pullbackIsoUnopPushout f g).hom_inv_id
simp
```

**lean_error:** tail step 1/4 ('rw pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=763, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.0s, verify 0.1s, in=763, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout]
```

**final state (truncated):**
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.3s, verify 0.1s, in=763, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← cancel_epi (pullbackIsoUnopPushout f g).inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.5s, verify 0.1s, in=763, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g).hom]
```

**lean_error:** tail step 1/1 ('simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g).hom]'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.6s, verify 0.1s, in=763, out=344)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.2s, verify 0.1s, in=763, out=364)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g).symm, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp only [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g).symm, pullbackIsoUnopPushout_inv_fst]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.3s, verify 0.2s, in=763, out=364)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
erw [← CategoryTheory.Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('erw [← CategoryTheory.Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 14.4s, verify 0.2s, in=763, out=490)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g), pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g), pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 164.4s, verify 0.2s, in=1382, out=2588)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pullbackIsoUnopPushout_inv_fst]
simp [CategoryTheory.Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw [pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 166.5s, verify 0.2s, in=1382, out=3524)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/1 ('rw [pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 169.7s, verify 0.1s, in=1382, out=3201)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw pullbackIsoUnopPushout_inv_fst
simp [assoc, iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 205.1s, verify 0.2s, in=1382, out=4117)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pullbackIsoUnopPushout_inv_fst]
simp [Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw [pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1382, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.1s, in=1382, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_inv_fst]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.7s, verify 0.1s, in=1382, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_inv_fst, ← Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_inv_fst, ← Iso.hom_inv_id_assoc]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=1382, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]
```

**lean_error:** tail step 1/1 ('simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 14.6s, verify 0.1s, in=1382, out=358)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
trans CategoryTheory.Iso.hom_inv_id_assoc.trans
  (CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst f g).symm.op
```

**lean_error:** tail step 1/2 ('trans CategoryTheory.Iso.hom_inv_id_assoc.trans'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.3s, verify 0.2s, in=1382, out=390)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/1 ('rwa [Iso.hom_inv_id_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 17.3s, verify 0.1s, in=1382, out=388)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← CategoryTheory.Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp [← CategoryTheory.Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 18.2s, verify 0.1s, in=1382, out=400)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_inv_fst, hom_inv_id_assoc]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_inv_fst, hom_inv_id_assoc]'): unknown identifier 'hom_inv_id_assoc'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 69.7s, verify 0.2s, in=1409, out=2592)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←pullbackIsoUnopPushout_inv_fst f g]
simp [category.assoc, iso.hom_inv_id_assoc]
```

**lean_error:** tail step 2/2 ('simp [category.assoc, iso.hom_inv_id_assoc]'): unknown identifier 'iso.hom_inv_id_assoc'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 94.4s, verify 0.2s, in=1409, out=3447)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pullbackIsoUnopPushout_inv_fst f g]
simp [iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/2 ('rw [pullbackIsoUnopPushout_inv_fst f g]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 146.3s, verify 0.1s, in=1409, out=5308)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw pullbackIsoUnopPushout_inv_fst
apply Iso.hom_inv_id_assoc
```

**lean_error:** tail step 1/2 ('rw pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 232.2s, verify 0.1s, in=1409, out=9080)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw ←pullbackIsoUnopPushout_inv_fst
apply CategoryTheory.Iso.hom_inv_id_assoc
```

**lean_error:** tail step 1/2 ('rw ←pullbackIsoUnopPushout_inv_fst'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1409, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1409, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.8s, verify 0.1s, in=1409, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout]
```

**final state (truncated):**
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.2s, in=1409, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]
```

**lean_error:** tail step 1/1 ('simp [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=1409, out=201)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('rw [← Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, pattern is a metavariable

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.4s, verify 0.1s, in=1409, out=307)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.5s, verify 0.1s, in=1409, out=311)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.4s, verify 0.1s, in=1409, out=418)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('simp only [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): simp made no progress
