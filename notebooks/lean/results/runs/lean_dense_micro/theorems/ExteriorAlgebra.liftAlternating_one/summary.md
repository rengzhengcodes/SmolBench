# ExteriorAlgebra.liftAlternating_one   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rw [foldl_one]
```

**True premises at k:** `CliffordAlgebra.foldl_one`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=469, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_zero]
simp only [LinearMap.mk₂_apply]
simp only [AlternatingMap.curryLeft_zero]
rfl
```

**lean_error:** tail step 1/4 ('simp only [CliffordAlgebra.foldl_zero]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=469, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [CliffordAlgebra.foldl_zero]
simp only [LinearMap.mk₂_apply]
simp only [AlternatingMap.curryLeft_zero]
simp only [Fin.natSub_zero]
```

**lean_error:** tail step 1/4 ('simp only [CliffordAlgebra.foldl_zero]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama-31-405b-base · rollout 1 → **success**  (gen 1.6s, verify 0.6s, in=469, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
simp [LinearMap.mk₂, LinearMap.mk₂'']
simp [AlternatingMap.curryLeft_zero]
simp [LinearMap.mk₂_apply]
simp [Fin.natSub_zero]
```

### `stepk:1` · llama-31-405b-base · rollout 2 → **success**  (gen 13.2s, verify 0.3s, in=469, out=561)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
simp [LinearMap.mk₂, AlternatingMap.curryLeft]
simp [Fin.natSub]
simp [Fin.succAbove]
simp [Fin.succAbove_ne]
simp [Fin.succAbove_lt]
simp [Fin.castSucc]
simp [Fin.succAbove_castSucc]
simp [Fin.castSucc_fin_succ]
simp [Fin.succAbove_comp]
simp [Fin.succAbove_comp']
simp [Fin.succAbove_comm]
simp [Fin.succAbove_assoc]
simp [Fin.succAbove_left_comm]
simp [Fin.succAbove_right_comm]
simp [Fin.succAbove_castLT]
simp [Fin.castLT_fin_succ]
rw [Fin.succAbove_fin_succ]
simp [Fin.castSucc_castLT]
simp [Fin.castLT_castSucc]
simp [Fin.castSucc_castLT_assoc]
simp [Fin.castLT_castSucc_assoc]
simp [Fin.castSucc_castLT_left_comm]
simp [Fin.castLT_castSucc_left_comm]
simp [Fin.castSucc_castLT_right_comm]
simp [Fin.castLT_castSucc_right_comm]
simp [Fin.castSucc_injective]
simp [Fin.castLT_injective]
simp [Fin.castSucc_surjective]
simp [Fin.castLT_surjective]
simp [Fin.castSucc_bijective]
simp [Fin.castLT_bijective]
simp [Fin.succAbove_injective]
simp [Fin.succAbove_surjective]
simp [Fin.succAbove_bijective]
rw [Fin.succAbove_comp]
rw [Fin.succAbove_comp']
rw [Fin.succAbove_comm]
rw [Fin.succAbove_assoc]
rw [Fin.succAbove_left_comm]
rw [Fin.succAbove_right_comm]
rw [Fin.succAbove_castLT]
rw [Fin.castLT_fin_succ]
rw [Fin.succAbove_fin_succ]
rw [Fin.castSucc_castLT]
rw [Fin.castLT_castSucc]
rw [Fin.castSucc_castLT_assoc]
rw [Fin.castLT_castSucc_assoc]
rw [Fin.castSucc_castLT_left_comm]
rw [Fin.castLT_castSucc_left_comm]
rw [Fin.castSucc_castLT_right_comm]
rw [Fin.castLT_castSucc_right_comm]
rw [Fin.castSucc_injective]
rw [Fin.castLT_injective]
rw [Fin.castSucc_surjective]
rw [Fin.castLT_surjective]
rw [Fin.castSucc_bijective]
rw [Fin.castLT_bijective]
rw [Fin.succAbove_injective]
rw [Fin.succAbove_surjective]
rw [Fin.succAbove_bijective]
exact AlternatingMap.curryLeft_zero
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.2s, in=469, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (f 0).map_zero
```

**lean_error:** tail step 1/1 ('exact (f 0).map_zero'): failed to synthesize instance

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=469, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (foldl_zero _ _ _).trans rfl
```

**lean_error:** tail step 1/1 ('exact (foldl_zero _ _ _).trans rfl'): unknown identifier 'foldl_zero'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=469, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact AlternatingMap.curryLeft_zero _ _
```

**lean_error:** tail step 1/1 ('exact AlternatingMap.curryLeft_zero _ _'): function expected at

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=469, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [foldl, Nat.succ_ne_zero, LinearMap.mk₂_apply, zero_smul, add_zero, curryLeft_apply,
  Fin.cases_zero]
```

**lean_error:** tail step 1/2 ('simp only [foldl, Nat.succ_ne_zero, LinearMap.mk₂_apply, zero_smul, add_zero, curryLeft_apply,'): <stdin>:1:94: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 0.7s, verify 0.1s, in=722, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=722, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=722, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=722, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=722, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [foldl_one]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=722, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CliffordAlgebra.foldl_one _ _ _
```

**lean_error:** tail step 1/1 ('exact CliffordAlgebra.foldl_one _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=722, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CliffordAlgebra.foldl_one _ _ _
```

**lean_error:** tail step 1/1 ('exact CliffordAlgebra.foldl_one _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=722, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CliffordAlgebra.foldl_one _ _ _
```

**lean_error:** tail step 1/1 ('exact CliffordAlgebra.foldl_one _ _ _'): typeclass instance problem is stuck, it is often due to metavariables
