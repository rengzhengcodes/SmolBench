# ExteriorAlgebra.liftAlternating_one   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rw [foldl_one]
```

**True premises at k:** `CliffordAlgebra.foldl_one`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✘ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=469, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_zero, LinearMap.mk₂_apply]
simp [LinearMap.mk₂_apply, AlternatingMap.curryLeft_zero]
rfl
```

**lean_error:** tail step 1/3 ('simp only [CliffordAlgebra.foldl_zero, LinearMap.mk₂_apply]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=427, out=83)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_apply, CliffordAlgebra.ι, LinearMap.mk₂_apply, CliffordAlgebra.ι_apply_one, map_zero, zero_add, CliffordAlgebra.foldl_zero, LinearMap.zero_apply, AlternatingMap.curryLeft_apply, Pi.zero_apply, zero_smul]
simp only [AlternatingMap.map_zero, CliffordAlgebra.foldl_zero, LinearMap.zero_apply]
```

**lean_error:** tail step 1/2 ('simp only [CliffordAlgebra.foldl_apply, CliffordAlgebra.ι, LinearMap.mk₂_apply, CliffordAlgebra.ι_apply_one, map_zero, zero_add, CliffordAlgebra.foldl_zero, LinearMap.zero_apply, AlternatingMap.curryLeft_apply, Pi.zero_apply, zero_smul]'): invalid field notation, type is not of the f

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=458, out=65)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_zero, LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, Nat.succ, f] |
  simp only [AlternatingMap.curryLeft_apply, LinearMap.mk₂_apply, CliffordAlgebra.foldl_zero, f]
```

**lean_error:** tail step 1/2 ('simp only [CliffordAlgebra.foldl_zero, LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, Nat.succ, f] |'): <stdin>:1:105: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=722, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=669, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_one]
simp only [LinearMap.mk₂_apply, AlternatingMap.curryLeft_zero, LinearMap.zero_apply]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=711, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1227, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=1175, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_one]
simp only [LinearMap.mk₂_apply, AlternatingMap.curryLeft_zero, f.zero_apply, CliffordAlgebra.ι, one_smul]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=1216, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rfl
```

**lean_error:** tail step 1/1 ('exact rfl'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1252, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=1257, out=38)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_one]
simp only [LinearMap.mk₂_apply, AlternatingMap.curryLeft_zero, LinearMap.zero_apply, Pi.zero_apply]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1241, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rfl
```

**lean_error:** tail step 1/1 ('exact rfl'): type mismatch
