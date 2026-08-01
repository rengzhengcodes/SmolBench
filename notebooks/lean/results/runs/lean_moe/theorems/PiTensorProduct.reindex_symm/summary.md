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

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 3.7s, in=513, out=595)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.6s, verify 0.8s, in=2907, out=1337)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [reindex]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=7282, out=1154)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.2s, in=6810, out=1299)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch
