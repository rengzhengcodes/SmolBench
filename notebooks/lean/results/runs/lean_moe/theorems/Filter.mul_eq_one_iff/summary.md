# Filter.mul_eq_one_iff   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
rw [pure_mul_pure, h, pure_one]
```

**True premises at k:** `Filter.pure_mul_pure`, `Filter.pure_one`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=326, out=1173)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using h
```

**lean_error:** tail step 1/1 ('simpa using h'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 69.5s, verify 0.1s, in=272, out=7906)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=267, out=534)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← pure_mul, h, pure_one]
```

**lean_error:** tail step 1/1 ('rw [← pure_mul, h, pure_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.8s, verify 0.1s, in=865, out=404)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [pure_mul_pure, pure_one, h]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 28.5s, verify 0.3s, in=820, out=3190)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure]
rw [h]
rw [Filter.pure_one]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.0s, verify 0.1s, in=784, out=236)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure, h, Filter.pure_one]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.3s, verify 0.1s, in=2705, out=531)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [pure_mul_pure, h]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 32.9s, verify 0.3s, in=2728, out=3694)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure]
rw [h]
rw [Filter.pure_one]
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.5s, verify 0.1s, in=2686, out=364)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=2531, out=683)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [pure_mul_pure, h] using (pure_one (α:=α))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 23.8s, verify 0.3s, in=2998, out=2646)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure]
rw [h]
rw [Filter.pure_one]
rfl
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.6s, verify 0.1s, in=2638, out=383)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure, h, Filter.pure_one]
```
