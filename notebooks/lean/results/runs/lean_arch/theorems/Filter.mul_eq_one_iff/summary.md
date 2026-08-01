# Filter.mul_eq_one_iff   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
rw [pure_mul_pure, h, pure_one]
```

**True premises at k:** `Filter.pure_mul_pure`, `Filter.pure_one`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=284, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h, pure_mul]
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=262, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← h]
simp [pure]
```

**lean_error:** tail step 1/2 ('rw [← h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 43.4s, verify 0.1s, in=273, out=2668)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=778, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=758, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=767, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=2586, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=2574, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← pure_one, ← pure_mul_pure, h]
```

**lean_error:** tail step 1/1 ('rw [← pure_one, ← pure_mul_pure, h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=2575, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=2611, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2800, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, pure_one, h]
```

**lean_error:** tail step 1/1 ('rw [pure_mul_pure, pure_one, h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=2600, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```
