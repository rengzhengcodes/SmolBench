# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✘ ✘ |
| `hint:2` | ✘ ✘ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=444, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero, φ.naturality_assoc]
simp only [ιMapObjOrZero_eq_zero h]
```

**lean_error:** tail step 1/2 ('rw [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero, φ.naturality_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.7s, verify 0.5s, in=444, out=41)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero _ _ _ _ h]
rw [zero_comp]
rw [comp_zero]
rw [ιMapObjOrZero_eq_zero _ _ _ _ h]
```

**lean_error:** tail step 3/4 ('rw [comp_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.2s, verify 0.2s, in=444, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_neg _ _ h]
rw [ιMapObjOrZero_neg _ _ h]
rw [zero_comp]
rw [comp_zero]
rw [zero_comp]
rw [comp_zero]
```

**lean_error:** tail step 1/6 ('rw [ιMapObjOrZero_neg _ _ h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.4s, verify 0.2s, in=444, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ιMapObjOrZero_eq_zero _ _ h, zero_comp, comp_zero, zero_comp] 
simp only [ιMapObjOrZero_eq_zero _ _ h] 
simp only [zero_comp]
```

**lean_error:** tail step 1/3 ('rw [ιMapObjOrZero_eq_zero _ _ h, zero_comp, comp_zero, zero_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **incomplete**  (gen 0.7s, verify 0.1s, in=444, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **incomplete**  (gen 0.8s, verify 0.2s, in=444, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=444, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, zero_comp, comp_zero]'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=444, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]
```

**lean_error:** tail step 1/1 ('simp only [ιMapObjOrZero_eq_zero h, comp_zero, zero_comp]'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=1061, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h]
simp only [comp_zero, zero_comp]
```

**lean_error:** tail step 1/2 ('simp only [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1061, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero h]
simp only [zero_comp, comp_zero]
```

**lean_error:** tail step 1/2 ('simp only [ιMapObjOrZero_eq_zero h]'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 1.3s, verify 0.2s, in=1061, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h]
simp only [zero_comp, comp_zero]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=1061, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```
