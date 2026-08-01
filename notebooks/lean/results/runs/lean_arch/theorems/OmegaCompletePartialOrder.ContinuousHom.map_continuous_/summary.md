# OmegaCompletePartialOrder.ContinuousHom.map_continuous'   (k=2, 3 tactics total)

file: `Mathlib/Order/OmegaCompletePartialOrder.lean`  

**Ground-truth tail (from k):**
```lean
apply const_continuous'
```

**True premises at k:** `OmegaCompletePartialOrder.const_continuous'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=352, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact continuous_bind_pure_comp hg (continuous'_const f)
```

**lean_error:** tail step 1/1 ("exact continuous_bind_pure_comp hg (continuous'_const f)"): unknown identifier 'continuous_bind_pure_comp'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=322, out=41)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [continuous', ← continuous'_coerce]
exact continuous'_const
rw [Function.comp]
exact continuous'_pure.comp continuous'_id
rw [continuous'_coerce]
exact continuous'_const
```

**lean_error:** tail step 1/6 ("rw [continuous', ← continuous'_coerce]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=341, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply continuous'_pure
exact continuous'_const
```

**lean_error:** tail step 1/2 ("apply continuous'_pure"): unknown identifier 'continuous'_pure'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=555, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply const_continuous' (pure ∘ f)
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=526, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact const_continuous' (f ⊥)
```

**lean_error:** tail step 1/1 ("exact const_continuous' (f ⊥)"): failed to synthesize instance

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=544, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply const_continuous'
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1148, out=5)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply const_continuous'
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=1117, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact const_continuous' (f ∘ default)
```

**lean_error:** tail step 1/1 ("exact const_continuous' (f ∘ default)"): stuck at solving universe constraint

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1137, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply const_continuous'
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1172, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' f
```

**lean_error:** tail step 1/1 ("exact const_continuous' f"): failed to synthesize instance

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=1210, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' f
```

**lean_error:** tail step 1/1 ("exact const_continuous' f"): failed to synthesize instance

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1161, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply const_continuous'
```
