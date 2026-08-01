# CategoryTheory.oppositeShiftFunctorAdd'_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

**True premises at k:** `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`, `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | · |
| `hint:3` | · | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=365, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]
rfl
```

**lean_error:** tail step 1/2 ("erw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=330, out=55)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app, unop_op, op_inv]
simp only [← op_comp, ← Functor.map_comp]
congr 1
simp only [Functor.map_id, id_comp, comp_id]
```

**lean_error:** tail step 1/4 ("rw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app, unop_op, op_inv]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=354, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply_fun unop
simp [shiftFunctorAdd'_op]
```

**lean_error:** tail step 1/2 ('apply_fun unop'): unknown identifier 'unop'

### `hint:2` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.6s, verify 0.4s, in=828, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd]
rw [oppositeShiftFunctorAdd_hom_app]
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

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=771, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd, CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd]
exact CategoryTheory.oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 2/2 ('exact CategoryTheory.oppositeShiftFunctorAdd_hom_app'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=817, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
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

### `hint:3` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=1254, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
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

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1186, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, shiftFunctorAdd'_eq_shiftFunctorAdd]
exact oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 2/2 ('exact oppositeShiftFunctorAdd_hom_app'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=1243, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
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

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=1278, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd]
apply oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 2/2 ('apply oppositeShiftFunctorAdd_hom_app'): tactic 'apply' failed, failed to unify

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1270, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd]
exact CategoryTheory.oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 2/2 ('exact CategoryTheory.oppositeShiftFunctorAdd_hom_app'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 7.7s, verify 0.1s, in=1267, out=471)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
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
