# ExteriorAlgebra.liftAlternating_one   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rw [foldl_one]
```

**True premises at k:** `CliffordAlgebra.foldl_one`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=437, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.2s, verify 0.2s, in=437, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.6s, verify 0.5s, in=437, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.4s, verify 0.4s, in=437, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.2s, in=690, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.2s, in=690, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.2s, in=690, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.2s, verify 0.3s, in=690, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.4s, verify 0.2s, in=1199, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.6s, verify 0.2s, in=1199, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 4.8s, verify 0.2s, in=1199, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [liftAlternating]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 5.1s, verify 0.2s, in=1199, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [liftAlternating, foldl_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.3s, in=1223, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.4s, verify 0.2s, in=1223, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [liftAlternating, foldl_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.8s, verify 0.3s, in=1223, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.1s, verify 0.2s, in=1223, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```
