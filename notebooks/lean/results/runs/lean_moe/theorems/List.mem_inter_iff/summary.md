# List.mem_inter_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases l₁ <;> simp [List.inter_def, mem_filter]
```

**True premises at k:** `List.inter_def`, `List.mem_filter`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | · |
| `hint:3` | ✓ | ✘ | · |
| `noise:3` | ✓ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=311, out=315)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using List.mem_inter
```

**lean_error:** tail step 1/1 ('simpa using List.mem_inter'): unknown constant 'List.mem_inter'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=248, out=944)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.mem_inter]
<;> tauto
```

**lean_error:** tail step 1/2 ('rw [List.mem_inter]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=241, out=447)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.mem_inter]
```

**lean_error:** tail step 1/1 ('simp [List.mem_inter]'): unknown constant 'List.mem_inter'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.8s, verify 0.7s, in=712, out=1522)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun a => a ∈ l₂) (as:=l₁))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.2s, in=642, out=574)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
<;> simp
```

**lean_error:** tail step 3/3 ('<;> simp'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.5s, verify 0.2s, in=620, out=385)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
```

**final state (truncated):**
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∧ decide (x ∈ l₂) = true ↔ x ∈ l₁ ∧ x ∈ l₂
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=1610, out=718)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun y => y ∈ l₂) (as:=l₁))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 20.6s, verify 0.1s, in=1550, out=2395)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.inter_def]
<;> simp [List.mem_filter]
<;> rfl
```

**lean_error:** tail step 2/3 ('<;> simp [List.mem_filter]'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.0s, verify 0.2s, in=1514, out=443)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
```

**final state (truncated):**
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∧ decide (x ∈ l₂) = true ↔ x ∈ l₁ ∧ x ∈ l₂
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=1515, out=1350)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun a => a ∈ l₂) (as:=l₁))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.2s, in=1690, out=926)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
<;> simp
```

**lean_error:** tail step 3/3 ('<;> simp'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 7.4s, verify 0.2s, in=1513, out=710)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.inter_def]
rw [List.mem_filter]
```

**final state (truncated):**
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∧ decide (x ∈ l₂) = true ↔ x ∈ l₁ ∧ x ∈ l₂
```
