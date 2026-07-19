# CategoryTheory.oppositeShiftFunctorAdd'_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

**True premises at k:** `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`, `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | · ✘ · · | · · · · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.8s, verify 0.3s, in=365, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
dsimp [shiftFunctorAdd']
rw [unop_op]
```

**lean_error:** tail step 2/2 ('rw [unop_op]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=365, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [shiftFunctorAdd'_hom_app]
erw [shiftFunctorAdd'_inv_app]
dsimp
rfl
```

**lean_error:** tail step 1/4 ("erw [shiftFunctorAdd'_hom_app]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=365, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]
simp only [OppositeShift.shift_unop]
```

**lean_error:** tail step 1/2 ("erw [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=365, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]
erw [← unop_op X.unop]
rfl
```

**lean_error:** tail step 1/3 ("simp only [shiftFunctorAdd'_hom_app, shiftFunctorAdd'_inv_app]"): unknown identifier 'shiftFunctorAdd'_hom_app'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=365, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd'_op]
```

**lean_error:** tail step 1/1 ("simp [shiftFunctorAdd'_op]"): unknown identifier 'shiftFunctorAdd'_op'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=365, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (shiftFunctorAdd'_op _ _ _ _ _).hom.app X
```

**lean_error:** tail step 1/1 ("exact (shiftFunctorAdd'_op _ _ _ _ _).hom.app X"): unknown identifier 'shiftFunctorAdd'_op'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 3.4s, verify 0.2s, in=365, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op_def
```

**lean_error:** tail step 1/1 ("exact ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op_def"): invalid field 'op_def', the environment does not contain 'Quiver.Hom.op_def'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=365, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_hom_app, Iso.app_inv, Iso.app_hom, shiftFunctorAdd'_inv_app, unop_op]
```

**lean_error:** tail step 1/1 ("simp only [shiftFunctorAdd'_hom_app, Iso.app_inv, Iso.app_hom, shiftFunctorAdd'_inv_app, unop_op]"): unknown identifier 'shiftFunctorAdd'_hom_app'

### `hint:2` · llama-31-405b-base · rollout 1 → **incomplete**  (gen 1.1s, verify 0.2s, in=828, out=25)

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

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.3s, verify 0.2s, in=828, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.6s, verify 0.2s, in=828, out=25)

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

### `hint:2` · llama-31-405b-base · rollout 2 → **incomplete**  (gen 1.8s, verify 0.2s, in=828, out=25)

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

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **incomplete**  (gen 1.5s, verify 0.1s, in=828, out=22)

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

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **incomplete**  (gen 1.4s, verify 1.5s, in=828, out=22)

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

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **incomplete**  (gen 3.1s, verify 0.1s, in=828, out=22)

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

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **incomplete**  (gen 3.3s, verify 0.1s, in=828, out=22)

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
