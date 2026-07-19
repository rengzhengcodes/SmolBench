# CategoryTheory.Pretriangulated.shiftFunctorZero_op_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Triangulated/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✘ ✓ ✘ | · ✓ · ✘ | ✘ ✓ · · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 70.3s, verify 0.1s, in=448, out=3218)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
refl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 76.4s, verify 0.1s, in=448, out=3468)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iso.cancel_right (shiftFunctorZero.inv.app X.unop).op
rfl
```

**lean_error:** tail step 1/2 ('apply iso.cancel_right (shiftFunctorZero.inv.app X.unop).op'): unknown identifier 'iso.cancel_right'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 76.5s, verify 0.9s, in=448, out=3494)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 93.5s, verify 0.1s, in=448, out=4273)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iso_comp_right_inj.mp,
rfl
```

**lean_error:** tail step 1/2 ('apply iso_comp_right_inj.mp,'): <stdin>:1:27: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.3s, verify 0.2s, in=448, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_1
inst✝¹ : Category.{u_2, u_1} C
inst✝ : HasShift C ℤ
X : Cᵒᵖ
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.5s, verify 1.6s, in=448, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.2s, verify 1.2s, in=448, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorOpIso]
```

**final state (truncated):**
```
C : Type u_1
inst✝¹ : Category.{u_2, u_1} C
inst✝ : HasShift C ℤ
X : Cᵒᵖ
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.3s, verify 0.1s, in=448, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Category.id_comp, shiftFunctorOpIso_app_hom, pullbackShiftIso_hom_app]
```

**lean_error:** tail step 1/1 ('simp only [Category.id_comp, shiftFunctorOpIso_app_hom, pullbackShiftIso_hom_app]'): unknown identifier 'shiftFunctorOpIso_app_hom'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.3s, in=448, out=220)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iso.hom_inv_id
```

**lean_error:** tail step 1/1 ('apply Iso.hom_inv_id'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.0s, verify 1.0s, in=448, out=229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 7.2s, verify 0.2s, in=448, out=278)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_1
inst✝¹ : Category.{u_2, u_1} C
inst✝ : HasShift C ℤ
X : Cᵒᵖ
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 8.5s, verify 0.2s, in=448, out=337)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C : Type u_1
inst✝¹ : Category.{u_2, u_1} C
inst✝ : HasShift C ℤ
X : Cᵒᵖ
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
...
```
