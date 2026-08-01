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

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.3s, in=467, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearEquiv.symm_apply_eq]
rw [reindex_symm]
rw [reindex_self]
```

**lean_error:** tail step 2/3 ('rw [reindex_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=438, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← reindex_symm, LinearEquiv.symm_symm]
rfl
```

**lean_error:** tail step 1/2 ('rw [← reindex_symm, LinearEquiv.symm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 43.0s, verify 0.2s, in=456, out=2670)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=2732, out=93)

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

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=2690, out=50)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [LinearEquiv.symm_symm]
simp only [reindex, LinearEquiv.ofLinear_symm_apply, domDomCongrLinearEquiv'_symm_apply,
  Equiv.symm_symm_apply]
rfl
```

**lean_error:** tail step 1/4 ('simp_rw [LinearEquiv.symm_symm]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.2s, in=2721, out=100)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.6s, in=6990, out=67)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearEquiv.coe_symm_mk]
rw [LinearEquiv.coe_mk]
rw [LinearEquiv.ofLinear_symm_apply]
rw [Equiv.symm_symm_apply]
rw [LinearEquiv.ofLinear_apply]
rw [Equiv.piCongrLeft'_symm]
```

**lean_error:** tail step 3/6 ('rw [LinearEquiv.ofLinear_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=6954, out=74)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearEquiv.ofLinear_symm_apply, ← LinearEquiv.ofLinear_apply]
simp only [PiTensorProduct.reindex, LinearEquiv.coe_mk, LinearEquiv.coe_symm_mk, domDomCongrLinearEquiv'_symm_apply, domDomCongrLinearEquiv'_apply, lift_tprod]
rfl
```

**lean_error:** tail step 1/3 ('rw [← LinearEquiv.ofLinear_symm_apply, ← LinearEquiv.ofLinear_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 2.6s, verify 0.4s, in=6979, out=79)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, PiTensorProduct.reindex, MultilinearMap.domDomCongrLinearEquiv'_symm_apply, Equiv.piCongrLeft'_symm]
```

**final state (truncated):**
```
case h
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.7s, in=7031, out=120)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [reindex, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply]
simp_rw [MultilinearMap.domDomCongrLinearEquiv'_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply]
simp_rw [Equiv.piCongrLeft'_apply, Equiv.piCongrLeft'_symm_apply]
simp_rw [Equiv.symm_symm_apply]
simp_rw [LinearEquiv.coe_mk, LinearEquiv.coe_symm_mk]
simp_rw [Equiv.piCongrLeft'_symm]
```

**lean_error:** tail step 3/6 ("simp_rw [Equiv.piCongrLeft'_apply, Equiv.piCongrLeft'_symm_apply]"): simp made no progress

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=7479, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [LinearEquiv.ofLinear_symm_apply, domDomCongrLinearEquiv'_symm_apply, Equiv.symm_symm_apply]
rfl
```

**lean_error:** tail step 1/2 ("simp_rw [LinearEquiv.ofLinear_symm_apply, domDomCongrLinearEquiv'_symm_apply, Equiv.symm_symm_apply]"): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=7020, out=288)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply, MultilinearMap.domDomCongrLinearEquiv'_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply, Equiv.piCongrLeft'_symm, Equiv.coe_piCongrLeft', Equiv.coe_piCongrLeft'_symm, Equiv.apply_symm_apply, LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk, LinearEquiv.toLinearMap_coe, LinearEquiv.symm_toLinearMap, LinearEquiv.toLinearMap_symm, LinearEquiv.trans_apply, LinearEquiv.symm_trans, LinearEquiv.self_trans_symm, LinearEquiv.refl_symm, LinearEquiv.refl_apply, LinearEquiv.self_trans_refl, LinearEquiv.trans_refl, LinearEquiv.trans_symm, LinearEquiv.symm_trans_apply, LinearEquiv.trans_assoc, LinearEquiv.symm_symm, LinearEquiv.ofLinear_toLinearMap, LinearEquiv.ofLinear_symm_toLinearMap, LinearEquiv.toLinearMap_ofLinear, LinearEquiv.symm_toLinearMap_ofLinear, LinearEquiv.apply_symm_apply, LinearEquiv.symm_apply_apply, LinearEquiv.coe_ofLinear, LinearEquiv.coe_ofLinear_symm]
```

**lean_error:** tail step 1/1 ("simp only [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply, MultilinearMap.domDomCongrLinearEquiv'_apply, MultilinearMap.domDomCongrLinearEquiv'_symm_apply, Equiv.piCongrLeft'_symm, Equiv.coe_piCongrLeft', Equiv.coe_piCongrLeft'_symm, Equiv.apply_symm_apply, Line
