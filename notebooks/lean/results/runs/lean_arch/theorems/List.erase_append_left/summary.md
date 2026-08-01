# List.erase_append_left   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact eraseP_append_left (beq_self_eq_true a) l₂ h
```

**True premises at k:** `List.eraseP_append_left`, `beq_self_eq_true`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | · |
| `hint:3` | ✘ | · | · |
| `noise:3` | ✓ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=305, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append_comm (fun x => a == x) l₁ l₂ h],
  exact eraseP_comm (fun x => a == x) l₁ l₂ h
```

**lean_error:** tail step 1/2 ('rw [eraseP_append_comm (fun x => a == x) l₁ l₂ h],'): <stdin>:1:49: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=279, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append, eraseP_eq_nil]
simp [*]
```

**lean_error:** tail step 1/2 ('rw [eraseP_append, eraseP_eq_nil]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=294, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply list.eraseP_append_left
exact h
```

**lean_error:** tail step 1/2 ('apply list.eraseP_append_left'): unknown identifier 'list.eraseP_append_left'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=738, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left (beq_self_eq_true a) l₂ h]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.3s, in=710, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left]
simp [beq_self_eq_true]
exact h
```

**lean_error:** tail step 3/3 ('exact h'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=727, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply eraseP_append_left
exact beq_self_eq_true a
```

**final state (truncated):**
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1612, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact List.eraseP_append_left (by rw [beq_self_eq_true a]; exact trivial) l₂ h
```

**lean_error:** tail step 1/1 ('exact List.eraseP_append_left (by rw [beq_self_eq_true a]; exact trivial) l₂ h'): no goals to be solved

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.8s, verify 0.2s, in=1586, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.eraseP_append_left]
simp [beq_self_eq_true]
```

**final state (truncated):**
```
case pa
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=1601, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply eraseP_append_left (beq_self_eq_true a)
```

**final state (truncated):**
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1636, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact List.eraseP_append_left (beq_self_eq_true a) l₂ h
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=1707, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.eraseP_append_left]
simp [beq_self_eq_true]
exact h
```

**lean_error:** tail step 3/3 ('exact h'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=1625, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply eraseP_append_left
exact beq_self_eq_true a
```

**final state (truncated):**
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```
