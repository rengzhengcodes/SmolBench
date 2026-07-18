# Order.sequenceOfCofinals.monotone   (k=5, 6 tactics total)

file: `Mathlib/Order/Ideal.lean`  

**Ground-truth tail (from k):**
```lean
apply Cofinal.le_above
```

**True premises at k:** `Order.Cofinal.le_above`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✘ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=346, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (𝒟 _).le_above _
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=346, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact le_Cofinal_above _ _
```

**lean_error:** tail step 1/1 ('exact le_Cofinal_above _ _'): unknown identifier 'le_Cofinal_above'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=346, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Cofinal.le_above _ _
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.8s, verify 0.1s, in=346, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (𝒟 _).le_above _
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=538, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=538, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Cofinal.le_above _ _
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=538, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.5s, verify 0.3s, in=538, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=662, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=662, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Cofinal.le_above _ _
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=662, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=662, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.6s, verify 0.1s, in=686, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Cofinal.le_above _ _
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=686, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.9s, verify 0.1s, in=686, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Cofinal.le_above
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=686, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Cofinal.le_above _ _
```
