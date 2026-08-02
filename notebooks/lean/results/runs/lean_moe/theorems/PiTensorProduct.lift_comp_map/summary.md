# PiTensorProduct.lift_comp_map   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  map_tprod, lift.tprod, MultilinearMap.compLinearMap_apply]
```

**True premises at k:** `LinearMap.compMultilinearMap_apply`, `LinearMap.coe_comp`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `PiTensorProduct.lift.tprod`, `MultilinearMap.compLinearMap_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.5s, in=690, out=2932)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap, LinearMap.comp_apply, compLinearMap, TensorProduct.map_tprod]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.compMultilinearMap, LinearMap.comp_apply, compLinearMap, TensorProduct.map_tprod]'): unknown constant 'TensorProduct.map_tprod'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.9s, verify 0.1s, in=654, out=9404)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) ((tprod R) x✝) := by rw [LinearMap.compMultilinearMap_apply]
  _ = lift h (map f ((tprod R) x✝)) := by simp [LinearMap.comp_apply]
  _ = lift h ((tprod R) (fun i => f i (x✝ i))) := by rw [TensorProduct.map_tensorProd]
  _ = h (fun i => f i (x✝ i)) := by rw [LinearMap.lift_tensorProd]
  _ = (compLinearMap h f) x✝ := by rw [MultilinearMap.compLinearMap_apply]
  _ = (lift (compLinearMap h f)) ((tprod R) x✝) := by rw [← LinearMap.lift_tensorProd]
  _ = (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ := by rw [LinearMap.compMultilinearMap_apply]
```

**lean_error:** tail step 1/8 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=628, out=557)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.3s, in=1750, out=1141)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 50.8s, verify 0.1s, in=1750, out=5824)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.apply_comp, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.compMultilinearMap_apply, LinearMap.apply_comp, PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=1675, out=532)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=2527, out=1298)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp,
      PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod,
      MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/3 ('simp [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp,'): <stdin>:1:61: unexpected end of input; expected ']'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 99.6s, verify 0.1s, in=2542, out=11805)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) (tprod R x✝) := by apply LinearMap.compMultilinearMap_apply, have h₂ : (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ = lift (compLinearMap h f) (tprod R x✝) := by apply LinearMap.compMultilinearMap_apply, have h₃ : (lift h ∘ₗ map f) (tprod R x✝) = h (fun i => f i (x✝ i)) := by calc (lift h ∘ₗ map f) (tprod R x✝) = lift h (map f (tprod R x✝)) := by ext x; simp [Function.comp_apply] _ = lift h (tprod R (fun i ↦ f i (x✝ i))) := by rw [PiTensorProduct.map_tprod] _ = h (fun i ↦ f i (x✝ i)) := by rw [PiTensorProduct.lift.tprod] _ = h (fun i => f i (x✝ i)) := by rfl, have h₄ : lift (compLinearMap h f) (tprod R x✝) = h (fun i => f i (x✝ i)) := by calc lift (compLinearMap h f) (tprod R x✝) = (compLinearMap h f) x✝ := by rw [PiTensorProduct.lift.tprod] _ = h (fun i => f i (x✝ i)) := by rw [MultilinearMap.compLinearMap_apply], calc (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) (tprod R x✝) := by rw [h₁] _ = h (fun i => f i (x✝ i)) := by rw [h₃] _ = lift (compLinearMap h f) (tprod R x✝) := by rw [h₄] <;> rfl _ = (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ := by rw [h₂] <;> rfl
```

**lean_error:** tail step 1/1 ('have h₁ : (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) (tprod R x✝) := by apply LinearMap.compMultilinearMap_apply, have h₂ : (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ = lift (compLinearMap h f) (tprod R x✝) := by appl

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=2447, out=536)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,
  PiTensorProduct.map_tprod, PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp only [LinearMap.compMultilinearMap_apply, LinearMap.coe_comp, Function.comp_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=2450, out=1398)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod,
      PiTensorProduct.lift.tprod, MultilinearMap.compLinearMap_apply]
```

**lean_error:** tail step 1/2 ('simp [LinearMap.coe_comp, Function.comp_apply, PiTensorProduct.map_tprod,'): <stdin>:1:73: unexpected end of input; expected ']'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.7s, verify 0.1s, in=2664, out=9526)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) ((tprod R) x✝) := by
  rw [LinearMap.compMultilinearMap_apply]
have h₂ : (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ = (lift (compLinearMap h f)) ((tprod R) x✝) := by
  rw [LinearMap.compMultilinearMap_apply]
have h₃ : (lift h ∘ₗ map f) ((tprod R) x✝) = h (fun i ↦ f i (x✝ i)) := by
  calc
    (lift h ∘ₗ map f) ((tprod R) x✝) = lift h (map f ((tprod R) x✝)) := by rw [LinearMap.comp_apply]
    _ = lift h (tprod R (fun i ↦ f i (x✝ i))) := by rw [PiTensorProduct.map_tprod]
    _ = h (fun i ↦ f i (x✝ i)) := by rw [PiTensorProduct.lift.tprod]
have h₄ : (lift (compLinearMap h f)) ((tprod R) x✝) = h (fun i ↦ f i (x✝ i)) := by
  calc
    (lift (compLinearMap h f)) ((tprod R) x✝) = lift (compLinearMap h f) (tprod R x✝) := by rfl
    _ = (compLinearMap h f) x✝ := by rw [PiTensorProduct.lift.tprod]
    _ = h (fun i => f i (x✝ i)) := by rw [MultilinearMap.compLinearMap_apply]
calc
  (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) ((tprod R) x✝) := h₁
  _ = h (fun i ↦ f i (x✝ i)) := h₃
  _ = (lift (compLinearMap h f)) ((tprod R) x✝) := by rw [h₄]
  _ = (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝ := by
    rw [h₂]
    <;>
    simp_all [LinearMap.compMultilinearMap_apply]
    <;>
    try ring_nf
    <;>
    try simp_all [PiTensorProduct.map_tprod]
    <;>
    try aesop
```

**lean_error:** tail step 1/28 ('have h₁ : (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ = (lift h ∘ₗ map f) ((tprod R) x✝) := by'): <stdin>:1:70: expected token

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=2453, out=459)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod,
  PiTensorProduct.map_tprod, MultilinearMap.compLinearMap_apply]
 rfl
```

**lean_error:** tail step 1/3 ('simp only [LinearMap.compMultilinearMap_apply, PiTensorProduct.lift.tprod,'): <stdin>:1:74: unexpected end of input; expected ']'
