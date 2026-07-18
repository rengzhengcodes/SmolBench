# OmegaCompletePartialOrder.ContinuousHom.map_continuous'   (k=2, 3 tactics total)

file: `Mathlib/Order/OmegaCompletePartialOrder.lean`  

**Ground-truth tail (from k):**
```lean
apply const_continuous'
```

**True premises at k:** `OmegaCompletePartialOrder.const_continuous'`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✘ ✓ |
| `hint:3` | ✓ ✓ ✘ ✓ |
| `noise:3` | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=318, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact continuous'_const
```

**lean_error:** tail step 1/1 ("exact continuous'_const"): unknown identifier 'continuous'_const'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=318, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact continuous'_pure
```

**lean_error:** tail step 1/1 ("exact continuous'_pure"): unknown identifier 'continuous'_pure'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=318, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact continuous'.const _
```

**lean_error:** tail step 1/1 ("exact continuous'.const _"): unknown identifier 'continuous'.const'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=318, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact continuous'_pure.comp continuous'_id
```

**lean_error:** tail step 1/1 ("exact continuous'_pure.comp continuous'_id"): unknown identifier 'continuous'_pure.comp'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.7s, verify 0.1s, in=521, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply const_continuous'
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=521, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply const_continuous'
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=521, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact const_continuous' f
```

**lean_error:** tail step 1/1 ("exact const_continuous' f"): failed to synthesize instance

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=521, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact const_continuous' _
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1120, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact const_continuous' _
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=1120, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact const_continuous' _
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1120, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact const_continuous' f
```

**lean_error:** tail step 1/1 ("exact const_continuous' f"): failed to synthesize instance

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 70.9s, verify 0.1s, in=1120, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply const_continuous'
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.1s, in=1141, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply const_continuous'
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=1141, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' _
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1141, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' (pure ())
```

**lean_error:** tail step 1/1 ("exact const_continuous' (pure ())"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1141, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact const_continuous' (pure ())
```

**lean_error:** tail step 1/1 ("exact const_continuous' (pure ())"): typeclass instance problem is stuck, it is often due to metavariables
