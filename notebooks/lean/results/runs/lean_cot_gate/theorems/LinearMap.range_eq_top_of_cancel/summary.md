# LinearMap.range_eq_top_of_cancel   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Quotient.lean`  

**Ground-truth tail (from k):**
```lean
exact ker_zero
```

**True premises at k:** `LinearMap.ker_zero`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 9.4s, verify 0.1s, in=454, out=355)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ker_zero
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 52.1s, verify 0.1s, in=454, out=2248)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ker_zero
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 73.7s, verify 0.3s, in=454, out=3303)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 87.6s, verify 0.3s, in=454, out=4022)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.4s, verify 0.1s, in=454, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ker_zero
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=454, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=454, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.5s, verify 0.1s, in=454, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 8.9s, verify 0.1s, in=713, out=330)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 13.7s, verify 0.1s, in=713, out=499)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply ker_zero
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 20.3s, verify 0.1s, in=713, out=803)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ker_zero
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 85.2s, verify 0.4s, in=713, out=3902)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply eq_top_iff.2
intro x
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.3s, verify 0.1s, in=713, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ker_zero
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.6s, verify 0.1s, in=713, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ker_zero
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=713, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Submodule.ker_eq_top_iff]
```

**lean_error:** tail step 1/1 ('simp [Submodule.ker_eq_top_iff]'): unknown constant 'Submodule.ker_eq_top_iff'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=713, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```
