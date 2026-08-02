# List.leftpad_length   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp only [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```

**True premises at k:** `List.leftpad`, `List.length_append`, `List.length_replicate`, `Nat.sub_add_eq_max`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 2.8s, in=280, out=1496)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold leftpad
by_cases h : n ≤ length l
· have h0 : n - length l = 0 := Nat.sub_eq_zero_of_le h
  simp [h0, h, Nat.max_eq_right h]
· have hlt : length l < n := Nat.lt_of_not_ge h
  have hle : length l ≤ n := Nat.le_of_lt hlt
  simp [List.length_append, List.length_replicate, Nat.sub_add_cancel hle,
        Nat.max_eq_left hle]
```

**lean_error:** tail step 3/8 ('· have h0 : n - length l = 0 := Nat.sub_eq_zero_of_le h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 11.8s, verify 0.2s, in=224, out=1307)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
by_cases h : length l < n
· -- case length l < n
  have h₁ : leftpad n a l = replicate (n - length l) a ++ l := by
    simp [leftpad, h]
  rw [h₁]
  simp [length_replicate, length_append]
  <;> ring_nf at *
  <;> omega
· -- case ¬ (length l < n)
  have h₁ : leftpad n a l = l := by
    simp [leftpad, h]
  rw [h₁]
  <;> simp [max_eq_right, le_of_not_lt]
```

**lean_error:** tail step 2/13 ('· -- case length l < n'): <stdin>:1:22: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 1.0s, in=227, out=842)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction n generalizing l with
| zero => simp [leftpad, max]
| succ n ih =>
    cases l with
    | nil => simp [leftpad, max]
    | cons x xs => simp [leftpad, max, ih]
```

**lean_error:** tail step 1/6 ('induction n generalizing l with'): <stdin>:1:31: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.8s, verify 0.6s, in=958, out=431)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [List.leftpad, List.length_replicate, Nat.sub_add_eq_max]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 10.4s, verify 0.1s, in=905, out=1153)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.9s, in=911, out=582)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [List.leftpad, List.length_append, List.length_replicate, Nat.sub_add_eq_max]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.6s, verify 0.1s, in=2268, out=893)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [List.leftpad, Nat.sub_add_eq_max]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 5.0s, verify 0.3s, in=2240, out=504)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.leftpad]
rw [List.length_append]
rw [List.length_replicate]
rw [Nat.sub_add_eq_max]
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.6s, verify 0.6s, in=2243, out=449)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [leftpad, Nat.sub_add_eq_max]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.4s, verify 0.3s, in=2151, out=837)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [List.leftpad, Nat.sub_add_eq_max]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 14.9s, verify 0.3s, in=2460, out=1668)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [leftpad]
rw [length_append]
rw [length_replicate]
rw [Nat.sub_add_eq_max]
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.7s, in=2237, out=474)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [List.leftpad, List.length_append, List.length_replicate, Nat.sub_add_eq_max]
```
