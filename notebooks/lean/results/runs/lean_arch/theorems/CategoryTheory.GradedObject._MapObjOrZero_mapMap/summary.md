# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=444, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero, φ.naturality_assoc]
simp only [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero, φ.naturality_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=414, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero _ h, ιMapObjOrZero_eq_zero _ h, zero_comp, comp_zero]
rfl
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero _ h, ιMapObjOrZero_eq_zero _ h, zero_comp, comp_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 9.8s, verify 0.2s, in=433, out=578)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero, comp_zero, zero_comp, ιMapObjOrZero_eq_zero]
```

**lean_error:** tail step 1/1 ('rw [ιMapObjOrZero_eq_zero, comp_zero, zero_comp, ιMapObjOrZero_eq_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1061, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('simp only [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1019, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero, mapMap, ← φ i, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero, mapMap, ← φ i, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1050, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1459, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1413, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero]'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1448, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1483, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('simp only [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1486, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero, mapMap, ← φ, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero _ _ _ h, zero_comp, comp_zero, mapMap, ← φ, comp_zero, zero_comp]'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1472, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch
