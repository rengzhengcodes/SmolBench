# PiTensorProduct.lift_comp_map   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

**True premises at k:** `LinearMap.compMultilinearMap_apply`, `LinearMap.coe_comp`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `PiTensorProduct.lift.tprod`, `MultilinearMap.compLinearMap_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.7s, in=633, out=65)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.compMultilinearMap_apply]
rw [LinearMap.compMultilinearMap_apply]
rw [lift_apply]
rw [lift_apply]
rw [compLinearMap_apply]
rw [(map f).apply]
rw [Function.comp_apply]
rw [Function.comp_apply]
rw [Function.comp_apply]
congr
```

**lean_error:** tail step 3/10 ('rw [lift_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=601, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, lift_apply, map_apply, compLinearMap_apply, tprod_apply]
congr
funext i
simp only [Function.comp_apply, map_apply]
```

**lean_error:** tail step 1/4 ('simp only [LinearMap.compMultilinearMap_apply, lift_apply, map_apply, compLinearMap_apply, tprod_apply]'): unknown identifier 'lift_apply'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.8s, in=622, out=409)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply MultilinearMap.ext
simp [LinearMap.compMultilinearMap_apply, MultilinearMap.lift_apply, MultilinearMap.map_apply, LinearMap.comp_apply]
```

**lean_error:** tail step 1/2 ('apply MultilinearMap.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.7s, verify 0.2s, in=1630, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1586, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, PiTensorProduct.map_tprod, MultilinearMap.compLinearMap_apply]
rfl
```

**lean_error:** tail step 1/2 ('simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, PiTensorProduct.map_tprod, MultilinearMap.compLinearMap_apply]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1619, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.0s, verify 0.5s, in=2367, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply]
simp_rw [PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=2321, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply, PiTensorProduct.map_tprod, LinearMap.coe_comp, Function.comp_apply]
```

**lean_error:** tail step 1/1 ('simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply, PiTensorProduct.map_tprod, LinearMap.coe_comp, Function.comp_apply]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2356, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.5s, verify 0.4s, in=2398, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply]
simp_rw [PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2441, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, PiTensorProduct.map_tprod, MultilinearMap.compLinearMap_apply]
rfl
```

**lean_error:** tail step 1/2 ('simp_rw [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod, PiTensorProduct.map_tprod, MultilinearMap.compLinearMap_apply]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2387, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'
