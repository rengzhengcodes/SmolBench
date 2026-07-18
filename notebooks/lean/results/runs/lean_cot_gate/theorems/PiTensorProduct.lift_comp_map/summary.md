# PiTensorProduct.lift_comp_map   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

**True premises at k:** `LinearMap.compMultilinearMap_apply`, `LinearMap.coe_comp`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `PiTensorProduct.lift.tprod`, `MultilinearMap.compLinearMap_apply`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✓ ✘ X |
| `hint:2` | ✘ ✘ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✘ |
| `noise:3` | ✘ ✓ ✓ X |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=608, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [lift_apply, compLinearMap_apply]
```

**lean_error:** tail step 1/1 ('simp [lift_apply, compLinearMap_apply]'): unknown identifier 'lift_apply'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.9s, verify 0.1s, in=608, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [lift_tprod, map_tprod]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=608, out=58)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_compMultilinearMap,
  lift_tprod_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod_apply,
  compLinearMap_apply, compMultilinearMap_apply]
```

**lean_error:** tail step 1/3 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_compMultilinearMap,'): <stdin>:1:80: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 80.4s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance-state check failed: ClientError: An error occurred (RequestExpired) when calling the DescribeInstances operation: Request has expired.). If the instance is running, your public IP probably changed and the

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=1613, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [lift.tprod, compMultilinearMap_apply, compLinearMap_apply, coe_comp, Function.comp_apply,
  map_tprod]
```

**lean_error:** tail step 1/2 ('simp [lift.tprod, compMultilinearMap_apply, compLinearMap_apply, coe_comp, Function.comp_apply,'): <stdin>:1:95: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=1613, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 70.4s, verify 0.1s, in=1613, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 70.6s, verify 0.1s, in=1613, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Function.comp_apply, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=2358, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=2358, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [compLinearMap_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.0s, verify 0.1s, in=2358, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Function.comp, LinearMap.compMultilinearMap_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=2358, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=2384, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 70.3s, verify 0.1s, in=2384, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 70.7s, verify 0.1s, in=2384, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [compLinearMap_apply, LinearMap.compMultilinearMap_apply, map_tprod, lift.tprod]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 80.3s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance-state check failed: ClientError: An error occurred (RequestExpired) when calling the DescribeInstances operation: Request has expired.). If the instance is running, your public IP probably changed and the
