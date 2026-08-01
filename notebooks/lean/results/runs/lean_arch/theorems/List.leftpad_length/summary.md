# List.leftpad_length   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp only [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```

**True premises at k:** `List.leftpad`, `List.length_append`, `List.length_replicate`, `Nat.sub_add_eq_max`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.2s, in=242, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction n generalizing l
case zero =>
  simp [leftpad, max]
case succ n ih =>
  cases l
  · simp [leftpad, max]
  · simp [leftpad, max]
    apply ih
```

**lean_error:** tail step 2/8 ('case zero =>'): <stdin>:1:12: unexpected end of input; expected '{'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.2s, in=216, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [leftpad]
simp [Nat.max_comm, Nat.max_eq_left_iff, Nat.max_eq_right_iff]
split <;> simp [*]
```

**lean_error:** tail step 2/3 ('simp [Nat.max_comm, Nat.max_eq_left_iff, Nat.max_eq_right_iff]'): unknown constant 'Nat.max_eq_left_iff'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=231, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil => simp [leftpad, max]
| cons hd tl ih => simp [leftpad, max, ih]
```

**lean_error:** tail step 1/3 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 8.2s, verify 0.3s, in=905, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.leftpad]
rw [List.length_append]
rw [List.length_replicate]
exact Nat.sub_add_eq_max n (length l)
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 7.8s, verify 1.3s, in=878, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.leftpad]
simp [List.length_append, List.length_replicate]
rw [Nat.sub_add_eq_max]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 2.5s, verify 0.7s, in=894, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 6.8s, verify 1.4s, in=2189, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.leftpad]
rw [List.length_append, List.length_replicate]
rw [Nat.sub_add_eq_max]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 4.5s, verify 3.3s, in=2175, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.leftpad]
simp [List.length_append, List.length_replicate]
rw [Nat.sub_add_eq_max]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.7s, verify 0.8s, in=2178, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 5.4s, in=2215, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [leftpad]
rw [length_append, length_replicate]
exact Nat.sub_add_eq_max n (length l)
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 4.0s, in=2335, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.leftpad]
simp [List.length_append, List.length_replicate]
rw [Nat.sub_add_eq_max]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.8s, in=2204, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [leftpad, length_append, length_replicate, Nat.sub_add_eq_max]
```
