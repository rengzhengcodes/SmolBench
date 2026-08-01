# List.erase_append_left   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact eraseP_append_left (beq_self_eq_true a) l₂ h
```

**True premises at k:** `List.eraseP_append_left`, `beq_self_eq_true`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | · ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=305, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append_comm]
rw [eraseP_comm]
```

**lean_error:** tail step 1/2 ('rw [eraseP_append_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.6s, in=305, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append_comm]
rw [eraseP_pred_comm]
exact eraseP_append_comm_of_mem h
```

**lean_error:** tail step 1/3 ('rw [eraseP_append_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.8s, verify 4.0s, in=305, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append_comm]
rw [eraseP_eq_cons_of_mem _ _ h]
rw [eraseP_cons]
rw [cond]
rw [eraseP_eq_nil]
rw [append_nil]
```

**lean_error:** tail step 1/6 ('rw [eraseP_append_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 5.8s, verify 1.9s, in=305, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eraseP_append_comm]
rw [eraseP_eq_filter]
rw [filter_append]
rw [eraseP_eq_filter] at h 
rw [filter_eq_nil_iff] at h
rw [←h]
rw [append_nil]
```

**lean_error:** tail step 1/7 ('rw [eraseP_append_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **incomplete**  (gen 0.7s, verify 0.2s, in=738, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left]
exact beq_self_eq_true _
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

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=738, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left (beq_self_eq_true a)]
  exact h
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=738, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left (beq_self_eq_true a) l₂ h]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=738, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eraseP_append_left (beq_self_eq_true a) l₂ h]
```
