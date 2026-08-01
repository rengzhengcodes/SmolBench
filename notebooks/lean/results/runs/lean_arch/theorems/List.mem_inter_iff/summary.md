# List.mem_inter_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases l₁ <;> simp [List.inter_def, mem_filter]
```

**True premises at k:** `List.inter_def`, `List.mem_filter`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | · | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=258, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.inter]
rfl
```

**lean_error:** tail step 1/2 ('rw [List.inter]'): failed to rewrite using equation theorems for 'List.inter'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=230, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.inter, elem_iff_mem, and_comm]
```

**lean_error:** tail step 1/1 ('simp [List.inter, elem_iff_mem, and_comm]'): unknown identifier 'elem_iff_mem'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=247, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.inter]
```

**lean_error:** tail step 1/1 ('simp [List.inter]'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=626, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
exact Iff.rfl
```

**lean_error:** tail step 3/3 ('exact Iff.rfl'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=596, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
simp only [and_comm]
```

**lean_error:** tail step 3/3 ('simp only [and_comm]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=615, out=410)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def],
exact mem_filter,
```

**lean_error:** tail step 1/2 ('rw [inter_def],'): <stdin>:1:14: expected end of input

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.3s, in=1474, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
exact Iff.rfl
```

**lean_error:** tail step 3/3 ('exact Iff.rfl'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.4s, verify 0.2s, in=1449, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.inter_def]
simp only [List.mem_filter, and_comm]
```

**final state (truncated):**
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∧ decide (x ∈ l₂) = true ↔ x ∈ l₁ ∧ x ∈ l₂
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 12.3s, verify 0.2s, in=1463, out=757)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inter_def]
exact mem_filter
```

**lean_error:** tail step 2/2 ('exact mem_filter'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=1508, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
exact Iff.rfl
```

**lean_error:** tail step 3/3 ('exact Iff.rfl'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1577, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
simp only [and_comm]
```

**lean_error:** tail step 3/3 ('simp only [and_comm]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 7.6s, verify 0.2s, in=1497, out=452)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
```

**final state (truncated):**
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∧ decide (x ∈ l₂) = true ↔ x ∈ l₁ ∧ x ∈ l₂
```
