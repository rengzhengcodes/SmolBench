# CategoryTheory.shiftComm_symm   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact NatTrans.congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

**True premises at k:** `CategoryTheory.NatTrans.congr_app`, `congr_arg`, `CategoryTheory.Iso.hom`, `CategoryTheory.shiftFunctorComm_symm`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | · | · |
| `hint:2` | ✘ | · | · | · |
| `hint:3` | ✘ | · | · | · |
| `noise:3` | ✘ | · | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 65.3s, verify 0.1s, in=270, out=3031)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 70.3s, verify 0.1s, in=270, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 8.9s, verify 0.1s, in=270, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `stepk:1` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 10.6s, verify 0.1s, in=270, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 91.4s, verify 0.1s, in=793, out=4384)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm C i j]
rfl
```

**lean_error:** tail step 1/2 ('rw [shiftFunctorComm_symm C i j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 17.1s, verify 0.1s, in=793, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 9.0s, verify 0.1s, in=793, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 10.7s, verify 0.3s, in=793, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 133.6s, verify 0.1s, in=2638, out=6940)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm i j]
```

**lean_error:** tail step 1/1 ('rw [shiftFunctorComm_symm i j]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 17.5s, verify 0.1s, in=2638, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [shiftFunctorComm_eq, shiftFunctorAdd'_eq_shiftFunctorAdd, shiftFunctorAdd]
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 9.1s, verify 0.2s, in=2638, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `hint:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 10.4s, verify 0.1s, in=2638, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 113.5s, verify 0.1s, in=2668, out=5672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact congr_app (shiftFunctorComm_symm i j) X
```

**lean_error:** tail step 1/1 ('exact congr_app (shiftFunctorComm_symm i j) X'): type mismatch

### `noise:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 17.2s, verify 0.1s, in=2668, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `noise:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 8.8s, verify 0.1s, in=2668, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 10.3s, verify 0.1s, in=2668, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```
