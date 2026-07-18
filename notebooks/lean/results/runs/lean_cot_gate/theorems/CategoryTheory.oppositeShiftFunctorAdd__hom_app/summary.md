# CategoryTheory.oppositeShiftFunctorAdd'_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

**True premises at k:** `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`, `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | · ✘ · · |
| `hint:2` | ✓ · ✓ ✓ |
| `hint:3` | · ✓ ✘ · |
| `noise:3` | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.5s, verify 0.1s, in=338, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.6s, verify 0.2s, in=338, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.8s, verify 0.1s, in=338, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd']
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.9s, verify 0.1s, in=338, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftFunctorAdd']
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

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=801, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.8s, verify 0.1s, in=801, out=26)

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

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=801, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=801, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.4s, verify 0.1s, in=1222, out=26)

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

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=1222, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1222, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app, ←
  shiftFunctorAdd'_eq_shiftFunctorAdd]
```

**lean_error:** tail step 1/2 ("rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app, ←"): <stdin>:1:75: unexpected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.1s, verify 0.1s, in=1222, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd]
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=1254, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1254, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=1254, out=38)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, shiftFunctorAdd'_eq_shiftFunctorAdd,
  oppositeShiftFunctorAdd_hom_app]
```

**lean_error:** tail step 1/2 ("rw [shiftFunctorAdd'_eq_shiftFunctorAdd, shiftFunctorAdd'_eq_shiftFunctorAdd,"): <stdin>:1:77: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1254, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app, ←
  shiftFunctorAdd'_eq_shiftFunctorAdd]
```

**lean_error:** tail step 1/2 ("rw [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app, ←"): <stdin>:1:75: unexpected end of input
