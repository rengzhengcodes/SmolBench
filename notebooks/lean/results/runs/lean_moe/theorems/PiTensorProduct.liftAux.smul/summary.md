# PiTensorProduct.liftAux.smul   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
```

**True premises at k:** `smul_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `PiTensorProduct.liftAux`, `AddMonoidHom.map_add`, `smul_add`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.5s, verify 0.1s, in=547, out=1756)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [smul_add, map_add, ihz, ihy]
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 76.6s, verify 0.1s, in=508, out=8559)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem refine'_2 {ι : Type u_1} {ι₂ : Type u_2} {ι₃ : Type u_3} {R : Type u_4} [CommSemiring R] {R₁ : Type u_5} {R₂ : Type u_6} {s : ι → Type u_7} [∀ (i : ι), AddCommMonoid (s i)] [∀ (i : ι), Module R (s i)] {M : Type u_8} [AddCommMonoid M] [Module R M] {E : Type u_9] [AddCommMonoid E] [Module R E] {F : Type u_10] [AddCommMonoid F] (φ : MultilinearMap R s E) (r : R) (x z y : ⨂[R] (i : ι), s i) (ihz : (liftAux φ) (r • z) = r • (liftAux φ) z) (ihy : (liftAux φ) (r • y) = r • (liftAux φ) y) : (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y) := by
  have h_main : (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y) := by
    have h₁ : (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y) := by
      -- Use the property that liftAux φ is a linear map to commute scalar multiplication
      have h₂ : (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y) := by
        -- Apply the linearity of liftAux φ
        rw [show (liftAux φ) (r • (z + y)) = (liftAux φ) (r • (z + y)) by rfl]
        -- Use the fact that liftAux φ is a linear map to factor out the scalar
        <;>
        (try simp_all [smul_smul]) <;>
        (try
          {
            -- Use the linearity of liftAux φ to commute scalar multiplication
            apply LinearMap.map_smul
          }) <;>
        (try
          {
            -- If the above doesn't work, try to use the given hypotheses
            -- This is a fallback and might not be necessary
            simp_all [ihz, ihy]
          })
      exact h₂
    exact h₁
  
  exact h_main
```

**lean_error:** tail step 1/24 ("theorem refine'_2 {ι : Type u_1} {ι₂ : Type u_2} {ι₃ : Type u_3} {R : Type u_4} [CommSemiring R] {R₁ : Type u_5} {R₂ : Type u_6} {s : ι → Type u_7} [∀ (i : ι), AddCommMonoid (s i)] [∀ (i : ι), Module R (s i)] {M : Type u_8} [AddCommMonoid M] [Module R M] {E : Type u_9] [AddCommMonoi

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=491, out=631)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (liftAux φ) (r • (z + y)) = (liftAux φ) (r • z + r • y) := by rw [smul_add]
  _ = (liftAux φ) (r • z) + (liftAux φ) (r • y) := by rw [liftAux.add]
  _ = r • (liftAux φ) z + r • (liftAux φ) y := by rw [ihz, ihy]
  _ = r • ((liftAux φ) z + (liftAux φ) y) := by rw [smul_add]
  _ = r • (liftAux φ) (z + y) := by rw [← liftAux.add]
```

**lean_error:** tail step 1/6 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.3s, verify 0.1s, in=1707, out=1735)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, (liftAux φ).map_add, smul_add]
  rfl
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.2s, verify 0.1s, in=1704, out=6539)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : (liftAux φ) (r • (z + y)) = (liftAux φ) (r • z + r • y) := by
  rw [smul_add]
have h2 : (liftAux φ) (r • z + r • y) = (liftAux φ) (r • z) + (liftAux φ) (r • y) := by
  apply (liftAux φ).map_add
have h3 : (liftAux φ) (r • z) + (liftAux φ) (r • y) = r • (liftAux φ) z + r • (liftAux φ) y := by
  rw [ihz, ihy]
have h4 : r • (liftAux φ) z + r • (liftAux φ) y = r • ((liftAux φ) z + (liftAux φ) y) := by
  rw [smul_add]
have h5 : r • ((liftAux φ) z + (liftAux φ) y) = r • (liftAux φ) (z + y) := by
  have h5₁ : (liftAux φ) z + (liftAux φ) y = (liftAux φ) (z + y) := by
    apply (liftAux φ).map_add
  rw [h5₁]
calc
  (liftAux φ) (r • (z + y)) = (liftAux φ) (r • z + r • y) := h1
  _ = (liftAux φ) (r • z) + (liftAux φ) (r • y) := h2
  _ = r • (liftAux φ) z + r • (liftAux φ) y := h3
  _ = r • ((liftAux φ) z + (liftAux φ) y) := h4
  _ = r • (liftAux φ) (z + y) := h5
```

**lean_error:** tail step 1/18 ('have h1 : (liftAux φ) (r • (z + y)) = (liftAux φ) (r • z + r • y) := by'): <stdin>:1:71: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.0s, verify 0.2s, in=1649, out=642)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [smul_add, map_add, ihz, ihy, ← smul_add, map_add]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.1s, verify 0.2s, in=2798, out=1697)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [smul_add, AddMonoidHom.map_add, ihz, ihy]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 55.8s, verify 0.1s, in=2810, out=6265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  (liftAux φ) (r • (z + y)) = (liftAux φ) (r • z + r • y) := by rw [smul_add]
  _ = (liftAux φ) (r • z) + (liftAux φ) (r • y) := by apply AddMonoidHom.map_add
  _ = (r • (liftAux φ) z) + (r • (liftAux φ) y) := by rw [ihz, ihy]
  _ = r • ((liftAux φ) z + (liftAux φ) y) := by rw [← smul_add]
  _ = r • (liftAux φ) (z + y) := by
    have h : (liftAux φ) z + (liftAux φ) y = (liftAux φ) (z + y) := by apply AddMonoidHom.map_add
    rw [h]
```

**lean_error:** tail step 1/8 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.5s, verify 0.1s, in=2719, out=706)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy, ← smul_add, ← (liftAux φ).map_add]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.4s, verify 0.1s, in=2669, out=2943)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, map_add, ihz, ihy, map_add, smul_add]
  rfl
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 71.1s, verify 0.9s, in=2961, out=8012)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add]
rw [AddMonoidHom.map_add]
rw [ihz, ihy]
rw [← smul_add]
rw [← AddMonoidHom.map_add]
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 9.6s, verify 0.3s, in=2719, out=918)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [smul_add, (liftAux φ).map_add, ihz, ihy]
rw [← smul_add, (liftAux φ).map_add]
```
