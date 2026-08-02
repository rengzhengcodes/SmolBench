# Int.neg_le_sub_left_of_le_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/Order.lean`  

**Ground-truth tail (from k):**
```lean
rwa [Int.add_comm] at h
```

**True premises at k:** `Int.add_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.4s, in=270, out=478)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [sub_eq_add_neg, add_comm] using h
```

**lean_error:** tail step 1/1 ('simpa [sub_eq_add_neg, add_comm] using h'): unknown identifier 'sub_eq_add_neg'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 20.0s, verify 0.1s, in=215, out=2268)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
linarith
```

**lean_error:** tail step 1/1 ('linarith'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=215, out=143)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=523, out=871)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.6s, verify 0.1s, in=475, out=5159)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  -a ≤ -c + b := h
  _ = b - c := by rw [add_comm] <;> rfl
```

**lean_error:** tail step 1/3 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=471, out=667)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=946, out=678)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [sub_eq_add_neg, add_comm] using h
```

**lean_error:** tail step 1/1 ('simpa [sub_eq_add_neg, add_comm] using h'): unknown identifier 'sub_eq_add_neg'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 28.7s, verify 0.1s, in=907, out=3476)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [sub_eq_add_neg, add_comm]
<;> exact h
```

**lean_error:** tail step 1/2 ('rw [sub_eq_add_neg, add_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 34.0s, verify 0.1s, in=908, out=3805)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=930, out=1734)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.5s, verify 0.1s, in=999, out=1960)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Int.neg_le_sub_left_of_le_add {a b c : ℤ} (h : c ≤ a + b) : -a ≤ b - c := by
  have h₁ : -a ≤ -c + b := by
    have h₂ : -a ≤ -c + b := by
      -- Use the given hypothesis to derive the desired inequality
      have h₃ : c ≤ a + b := h
      have h₄ : -a ≤ -c + b := by
        -- Use the property of integers to manipulate the inequality
        linarith
      exact h₄
    exact h₂
  
  have h₂ : -c + b = b - c := by
    rw [add_comm]
    <;> simp [sub_eq_add_neg]
    <;> ring_nf
    <;> simp_all [add_assoc]
    <;> linarith
  
  have h₃ : -a ≤ b - c := by
    rw [h₂] at h₁
    exact h₁
  
  exact h₃
```

**lean_error:** tail step 1/20 ('theorem Int.neg_le_sub_left_of_le_add {a b c : ℤ} (h : c ≤ a + b) : -a ≤ b - c := by'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=920, out=561)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm] at h
exact h
```
