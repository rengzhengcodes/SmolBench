# PiTensorProduct.reindex_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [reindex, domDomCongrLinearEquiv', LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk,
  LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, LinearEquiv.ofLinear_apply,
  Equiv.piCongrLeft'_symm]
```

**True premises at k:** `PiTensorProduct.reindex`, `MultilinearMap.domDomCongrLinearEquiv'`, `LinearEquiv.coe_symm_mk`, `LinearEquiv.coe_mk`, `LinearEquiv.ofLinear_symm_apply`, `Equiv.symm_symm_apply`, `LinearEquiv.ofLinear_apply`, `Equiv.piCongrLeft'_symm`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=467, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearEquiv.symm_apply_eq]
rw [reindex_symm]
```

**lean_error:** tail step 2/2 ('rw [reindex_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.7s, verify 0.3s, in=467, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearEquiv.symm_apply_eq]
rw [reindex_apply]
rw [reindex_apply]
congr with (_ | i)
rw [Equiv.symm_symm]
```

**lean_error:** tail step 2/5 ('rw [reindex_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.0s, verify 0.3s, in=467, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearEquiv.symm_apply_eq]
rw [reindex_apply]
rw [TensorProduct.reindex_comm]
rw [TensorProduct.reindex_not _ e.symm]
rw [TensorProduct.reindex_id]
```

**lean_error:** tail step 2/5 ('rw [reindex_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.3s, verify 0.3s, in=467, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearEquiv.symm_apply_eq]
rw [reindex_apply]
rw [TensorProduct.reindex_comm]
rw [reindex_apply]
rw [Equiv.coe_symm]
rw [Equiv.coe_coe]
```

**lean_error:** tail step 2/6 ('rw [reindex_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.2s, in=467, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=467, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=467, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.2s, in=467, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=2732, out=93)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply, 
  MultilinearMap.domDomCongrLinearEquiv'_symm_apply, 
  MultilinearMap.domDomCongrLinearEquiv'_apply, 
  LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, 
  Equiv.piCongrLeft'_symm, Equiv.symm_symm_apply]
```

**lean_error:** tail step 1/5 ('simp_rw [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply,'): <stdin>:1:78: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.3s, verify 0.1s, in=2732, out=111)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply, 
         MultilinearMap.domDomCongrLinearEquiv'_apply, 
         MultilinearMap.domDomCongrLinearEquiv'_symm_apply, 
         Equiv.piCongrLeft'_apply, Equiv.piCongrLeft'_symm_apply, 
         LinearEquiv.coe_mk, LinearEquiv.coe_symm_mk, 
         Equiv.symm_symm_apply, 
         lift.tprod]
```

**lean_error:** tail step 1/7 ('simp_rw [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply,'): <stdin>:1:78: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.4s, verify 0.1s, in=2732, out=113)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [reindex, LinearEquiv.ofLinear_apply, lift.tprod, domDomCongrLinearEquiv'_apply,
  MultilinearMap.coe_mk, Function.comp, piCongrLeft'_symm_apply, Equiv.apply_symm_apply]
simp_rw [reindex, LinearEquiv.ofLinear_symm_apply, lift.tprod, domDomCongrLinearEquiv'_symm_apply,
  MultilinearMap.coe_mk, Function.comp, piCongrLeft'_apply, Equiv.symm_apply_apply]
rfl
```

**lean_error:** tail step 1/5 ("simp_rw [reindex, LinearEquiv.ofLinear_apply, lift.tprod, domDomCongrLinearEquiv'_apply,"): <stdin>:1:88: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 5.0s, verify 0.1s, in=2732, out=189)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [LinearEquiv.coe_symm_mk, PiTensorProduct.reindex, LinearEquiv.ofLinear_symm_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply]
simp_rw [MultilinearMap.domDomCongrLinearEquiv'_apply, Equiv.piCongrLeft'_symm, LinearEquiv.ofLinear_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply]
simp_rw [LinearEquiv.coe_symm_mk, PiTensorProduct.reindex, LinearEquiv.ofLinear_symm_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply]
simp_rw [MultilinearMap.domDomCongrLinearEquiv'_apply, Equiv.piCongrLeft'_symm, LinearEquiv.ofLinear_apply, MultilinearMap.domDomCongrLinearEquiv'_apply]
rw [Equiv.symm_symm_apply]
```

**lean_error:** tail step 1/5 ("simp_rw [LinearEquiv.coe_symm_mk, PiTensorProduct.reindex, LinearEquiv.ofLinear_symm_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply]"): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.6s, verify 0.9s, in=2732, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [reindex, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=2732, out=58)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [reindex, LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.ofLinear_symm_apply,
  Equiv.symm_symm_apply, LinearEquiv.ofLinear_apply, Equiv.piCongrLeft'_symm]
```

**lean_error:** tail step 1/2 ('simp only [reindex, LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.ofLinear_symm_apply,'): <stdin>:1:97: unexpected end of input; expected ']'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.1s, in=2732, out=84)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.ofLinear_symm_apply,
  MultilinearMap.domDomCongrLinearEquiv'_symm_apply, LinearEquiv.ofLinear_apply,
  MultilinearMap.domDomCongrLinearEquiv'_apply, Equiv.piCongrLeft'_symm, Equiv.symm_symm_apply]
```

**lean_error:** tail step 1/3 ('simp_rw [LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.ofLinear_symm_apply,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 3.8s, verify 0.1s, in=2732, out=87)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [reindex, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, LinearEquiv.coe_mk,
  LinearEquiv.coe_symm_mk, MultilinearMap.domDomCongrLinearEquiv'_apply,
  MultilinearMap.domDomCongrLinearEquiv'_symm_apply, Equiv.piCongrLeft'_symm,
  Equiv.symm_symm_apply]
```

**lean_error:** tail step 1/4 ('simp [reindex, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, LinearEquiv.coe_mk,'): <stdin>:1:95: unexpected end of input; expected ']'
