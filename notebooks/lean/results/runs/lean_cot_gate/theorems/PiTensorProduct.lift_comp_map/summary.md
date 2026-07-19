# PiTensorProduct.lift_comp_map   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

**True premises at k:** `LinearMap.compMultilinearMap_apply`, `LinearMap.coe_comp`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `PiTensorProduct.lift.tprod`, `MultilinearMap.compLinearMap_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ X ✓ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✘ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ |
| `hint:3` | · ✓ ✘ ✓ | ✓ ✓ ✓ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✓ ✘ ✘ ✘ | ✘ ✓ ✓ X ✓ | ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 134.5s, verify 0.2s, in=608, out=5198)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_tprod, lift_tprod, lift_tprod]
```

**lean_error:** tail step 1/1 ('rw [map_tprod, lift_tprod, lift_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 166.8s, verify 0.1s, in=608, out=6393)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 214.8s, verify 0.8s, in=608, out=8432)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.compMultilinearMap_apply, LinearMap.compMultilinearMap_apply]
rw [LinearMap.coe_comp, Function.comp_apply]
rw [map_tprod]
rw [lift_tprod]
rw [compLinearMap_apply]
rw [lift_tprod]
```

**lean_error:** tail step 4/6 ('rw [lift_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 215.6s, verify 0.4s, in=608, out=8408)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.compMultilinearMap_apply, LinearMap.compMultilinearMap_apply]
rw [map_tprod]
rw [lift_apply_tprod]
rw [compLinearMap_apply]
rw [map_tprod]
rw [lift_apply_tprod]
```

**lean_error:** tail step 2/6 ('rw [map_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.2s, verify 0.1s, in=608, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.6s, verify 0.2s, in=608, out=140)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [lift_map]
```

**lean_error:** tail step 1/1 ('rw [lift_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.3s, verify 0.1s, in=608, out=151)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.5s, verify 0.1s, in=608, out=196)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [comp_tprod_apply]
```

**lean_error:** tail step 1/1 ('simp only [comp_tprod_apply]'): unknown identifier 'comp_tprod_apply'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.2s, verify 0.1s, in=608, out=324)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, lift_apply, compLinearMap]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.compMultilinearMap_apply, lift_apply, compLinearMap]'): unknown identifier 'lift_apply'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 59.9s, verify 0.1s, in=1613, out=2440)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 105.5s, verify 0.1s, in=1613, out=4156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 136.5s, verify 0.1s, in=1613, out=5269)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 173.4s, verify 0.4s, in=1613, out=6655)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply]
rw [map_tprod, lift.tprod]
rw [lift.tprod]
rw [MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 2/4 ('rw [map_tprod, lift.tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.2s, verify 0.1s, in=1613, out=356)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.8s, verify 0.1s, in=1613, out=383)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.0s, verify 0.1s, in=1613, out=389)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.4s, verify 0.1s, in=1613, out=440)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 141.0s, verify 0.2s, in=2358, out=1801)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**final state (truncated):**
```
case H.H
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝¹¹ : CommSemiring R
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 173.2s, verify 0.1s, in=2358, out=3127)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 178.9s, verify 0.2s, in=2358, out=4423)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod, compLinearMap_apply]
```

**lean_error:** tail step 1/1 ('rw [compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod, compLinearMap_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 214.7s, verify 0.1s, in=2358, out=4798)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.5s, verify 0.1s, in=2358, out=316)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.6s, verify 0.1s, in=2358, out=382)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 16.3s, verify 0.1s, in=2358, out=394)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 22.2s, verify 0.1s, in=2358, out=492)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp_rw [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:85: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 88.2s, verify 0.1s, in=2384, out=3507)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 91.0s, verify 0.1s, in=2384, out=3613)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [compMultilinearMap_apply, LinearMap.coe_comp, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/1 ('simp [compMultilinearMap_apply, LinearMap.coe_comp, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]'): unknown identifier 'compMultilinearMap_apply'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 91.2s, verify 0.1s, in=2384, out=3622)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod, compLinearMap_apply]
```

**lean_error:** tail step 1/1 ('simp [compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod, compLinearMap_apply]'): unknown identifier 'compMultilinearMap_apply'

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 101.6s, verify 0.2s, in=2384, out=4011)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [compMultilinearMap_apply, compMultilinearMap_apply]
rw [LinearMap.coe_comp, Function.comp_apply, map_tprod, lift.tprod]
rw [lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/3 ('rw [compMultilinearMap_apply, compMultilinearMap_apply]'): tactic 'rewrite' failed, equality or iff proof expected

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

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 4.1s, verify 0.1s, in=2384, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Function.comp, LinearMap.compMultilinearMap_apply]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.7s, verify 0.1s, in=2384, out=375)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.4s, verify 0.1s, in=2384, out=401)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod,
  lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, map_tprod,'): <stdin>:1:98: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.1s, verify 0.1s, in=2384, out=426)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 13.6s, verify 0.1s, in=2384, out=445)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```
