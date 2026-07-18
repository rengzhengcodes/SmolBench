# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✓ ✓ · |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.1s, in=417, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=417, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=417, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero, dif_neg h, comp_zero, zero_comp]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.6s, verify 0.2s, in=417, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero, if_neg h, zero_comp, comp_zero]
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=1037, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=1037, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1438, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=1438, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1462, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=1462, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch
