# CategoryTheory.oppositeShiftFunctorAdd'_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

**True premises at k:** `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`, `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=395, out=858)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 120.5s, verify 0.1s, in=356, out=13833)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd', HasShift.shift_add, opp_eq_iff, opp_map, opp_id]
```

**lean_error:** tail step 1/1 ("simp [shiftFunctorAdd', HasShift.shift_add, opp_eq_iff, opp_map, opp_id]"): unknown constant 'CategoryTheory.HasShift.shift_add'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.5s, verify 0.1s, in=350, out=395)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [OppositeShift, shiftFunctorAdd']
```

**final state (truncated):**
```
C : Type u_1
inst✝² : Category.{u_3, u_1} C
A : Type u_2
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
X : OppositeShift C A
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.3s, in=843, out=759)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 1/1 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using oppositeShiftFunctorAdd_hom_app"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 99.9s, verify 0.1s, in=844, out=11482)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
      (shiftFunctorAdd (OppositeShift C A) a b).hom.app X := by rfl
  _ = ((shiftFunctorAdd C a b).inv.app X.unop).op := by
    rw [oppositeShiftFunctorAdd_hom_app]
  _ = ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op := by rfl
```

**lean_error:** tail step 1/6 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=831, out=879)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd a b, shiftFunctorAdd'_eq_shiftFunctorAdd a b]
exact oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 1/2 ("rw [shiftFunctorAdd'_eq_shiftFunctorAdd a b, shiftFunctorAdd'_eq_shiftFunctorAdd a b]"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=1283, out=1416)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using
  (oppositeShiftFunctorAdd_hom_app (X:=X) (a:=a) (b:=b))
```

**lean_error:** tail step 1/2 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using"): <stdin>:1:49: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.6s, verify 0.3s, in=1307, out=4850)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd]
apply oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 2/2 ('apply oppositeShiftFunctorAdd_hom_app'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.2s, in=1273, out=562)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd (OppositeShift C A) a b, shiftFunctorAdd'_eq_shiftFunctorAdd C a b]
apply oppositeShiftFunctorAdd_hom_app
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.2s, in=1257, out=1167)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using
  (oppositeShiftFunctorAdd_hom_app (C:=C) (A:=A) (a:=a) (b:=b) (X:=X))
```

**lean_error:** tail step 1/2 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using"): <stdin>:1:49: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 48.5s, verify 0.1s, in=1378, out=5520)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (shiftFunctorAdd' (OppositeShift C A) a b (a + b) rfl) = shiftFunctorAdd (OppositeShift C A) a b := by
  rw [shiftFunctorAdd'_eq_shiftFunctorAdd]
have h₂ : (shiftFunctorAdd' C a b (a + b) rfl) = shiftFunctorAdd C a b := by
  rw [shiftFunctorAdd'_eq_shiftFunctorAdd]
rw [h₁]
rw [h₂]
exact oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 1/7 ("have h₁ : (shiftFunctorAdd' (OppositeShift C A) a b (a + b) rfl) = shiftFunctorAdd (OppositeShift C A) a b := by"): <stdin>:1:112: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=1288, out=521)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd (OppositeShift C A) a b,
    shiftFunctorAdd'_eq_shiftFunctorAdd C a b]
apply oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 1/3 ("rw [shiftFunctorAdd'_eq_shiftFunctorAdd (OppositeShift C A) a b,"): <stdin>:1:64: unexpected end of input; expected ']'
