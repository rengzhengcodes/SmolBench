# ExteriorAlgebra.liftAlternating_ι_mul   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✓ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 55.6s, verify 0.1s, in=691, out=2752)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr' 1
ext i
rw [LinearMap.mk₂_apply]
```

**lean_error:** tail step 1/3 ("congr' 1"): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 73.3s, verify 0.1s, in=691, out=3655)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext i
refl
```

**lean_error:** tail step 1/2 ('ext i'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 84.8s, verify 0.2s, in=691, out=4234)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
ext i
simp [LinearMap.mk₂_apply]
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 103.5s, verify 0.1s, in=691, out=5182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext i
simp [LinearMap.mk₂_apply]
```

**lean_error:** tail step 1/2 ('ext i'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.6s, verify 0.2s, in=691, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=691, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.2s, in=691, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.2s, in=691, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.8s, verify 0.2s, in=691, out=194)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.2s, verify 0.2s, in=691, out=213)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.6s, verify 0.2s, in=691, out=226)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.2s, verify 0.2s, in=691, out=293)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```
