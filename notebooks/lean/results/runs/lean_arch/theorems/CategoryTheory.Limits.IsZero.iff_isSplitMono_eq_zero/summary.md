# CategoryTheory.Limits.IsZero.iff_isSplitMono_eq_zero   (k=6, 7 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
simp only [h, zero_comp]
```

**True premises at k:** `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=292, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h]
exact zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=265, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=281, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=589, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, CategoryTheory.Limits.zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=555, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, CategoryTheory.Limits.zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=578, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=855, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, CategoryTheory.Limits.zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=817, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=844, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
exact zero_comp f
```

**lean_error:** tail step 1/2 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=879, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, CategoryTheory.Limits.zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, CategoryTheory.Limits.zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=878, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.4s, in=868, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
exact zero_comp
```

**lean_error:** tail step 1/2 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct
