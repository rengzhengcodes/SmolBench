# PiTensorProduct.lift_comp_map   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

**True premises at k:** `LinearMap.compMultilinearMap_apply`, `LinearMap.coe_comp`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `PiTensorProduct.lift.tprod`, `MultilinearMap.compLinearMap_apply`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.5s, in=690, out=2932)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap, LinearMap.comp_apply, compLinearMap, TensorProduct.map_tprod]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.compMultilinearMap, LinearMap.comp_apply, compLinearMap, TensorProduct.map_tprod]'): unknown constant 'TensorProduct.map_tprod'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.3s, in=1750, out=1141)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=2527, out=1298)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp,
      PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod,
      MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/3 ('simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp,'): <stdin>:1:61: unexpected end of input; expected ']'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=2450, out=1398)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod,
      PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp [LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod,'): <stdin>:1:73: unexpected end of input; expected ']'
