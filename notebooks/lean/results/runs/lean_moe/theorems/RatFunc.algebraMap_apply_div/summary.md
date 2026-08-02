# RatFunc.algebraMap_apply_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
convert coe_div (algebraMap F[X] (RatFunc F) p) (algebraMap F[X] (RatFunc F) q) <;>
  rw [← mk_one, coe_def, coeAlgHom, mk_eq_div, liftAlgHom_apply_div, map_one, div_one,
    Algebra.ofId_apply]
```

**True premises at k:** `RatFunc.coe_div`, `algebraMap`, `RatFunc`, `algebraMap`, `RatFunc`, `RatFunc.mk_one`, `RatFunc.coe_def`, `RatFunc.coeAlgHom`, `RatFunc.mk_eq_div`, `RatFunc.liftAlgHom_apply_div`, `map_one`, `div_one`, `Algebra.ofId_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 11.0s, verify 0.2s, in=406, out=2137)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [div_eq_mul_inv]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p * ((ofPowerSeries ℤ F) ↑q)⁻¹
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 126.4s, verify 0.1s, in=351, out=14354)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
      (FractionField.map (algebraMap F[X] (LaurentSeries F))) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) := by
    apply algebraMap_fractionField
  _ = (FractionField.map (algebraMap F[X] (LaurentSeries F))) ((algebraMap F[X] (RatFunc F)) p) / (FractionField.map (algebraMap F[X] (LaurentSeries F))) ((algebraMap F[X] (RatFunc F)) q) := by
    rw [FractionField.map_div]
  _ = (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q := by
    have h2 : (FractionField.map (algebraMap F[X] (LaurentSeries F))) ((algebraMap F[X] (RatFunc F)) p) = (algebraMap F[X] (LaurentSeries F)) p := by
      have h2₁ : (FractionField.map (algebraMap F[X] (LaurentSeries F))) ∘ (algebraMap F[X] (RatFunc F)) = algebraMap F[X] (LaurentSeries F)) := by
        apply FractionField.map_algebraMap
      have h2₂ : ((FractionField.map (algebraMap F[X] (LaurentSeries F))) ∘ (algebraMap F[X] (RatFunc F))) p = (algebraMap F[X] (LaurentSeries F)) p := by
        rw [h2₁]
      simpa [Function.comp_apply] using h2₂
    have h3 : (FractionField.map (algebraMap F[X] (LaurentSeries F))) ((algebraMap F[X] (RatFunc F)) q) = (algebraMap F[X] (LaurentSeries F)) q := by
      have h3₁ : (FractionField.map (algebraMap F[X] (LaurentSeries F))) ∘ (algebraMap F[X] (RatFunc F)) = algebraMap F[X] (LaurentSeries F)) := by
        apply FractionField.map_algebraMap
      have h3₂ : ((FractionField.map (algebraMap F[X] (LaurentSeries F))) ∘ (algebraMap F[X] (RatFunc F))) q = (algebraMap F[X] (LaurentSeries F)) q := by
        rw [h3₁]
      simpa [Function.comp_apply] using h3₂
    rw [h2, h3]
```

**lean_error:** tail step 1/20 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=360, out=478)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_div]
```

**lean_error:** tail step 1/1 ('rw [map_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=2368, out=960)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using
    (RatFunc.coe_div (f := (algebraMap F[X] (RatFunc F)) p)
                     (g := (algebraMap F[X] (RatFunc F)) q))
```

**lean_error:** tail step 1/3 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 244.6s, verify 0.2s, in=2356, out=29153)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_trans : (algebraMap (RatFunc F) (LaurentSeries F)) ∘ (algebraMap F[X] (RatFunc F)) = algebraMap F[X] (LaurentSeries F) := by sorry
have h_ring : RingHom (algebraMap (RatFunc F) (LaurentSeries F)) := by exact inferInstance
have h₁ : (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p) / (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) q) := by
  apply RingHom.map_div
  <;> exact h_ring
have h₂ : (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p) = (algebraMap F[X] (LaurentSeries F)) p := by
  have h₃ : (algebraMap (RatFunc F) (LaurentSeries F)) ∘ (algebraMap F[X] (RatFunc F)) = algebraMap F[X] (LaurentSeries F) := h_trans
  have h₄ : ((algebraMap (RatFunc F) (LaurentSeries F)) ∘ (algebraMap F[X] (RatFunc F))) p = (algebraMap F[X] (LaurentSeries F)) p := by rw [h₃]
  simpa [Function.comp_apply] using h₄
have h₃ : (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) q) = (algebraMap F[X] (LaurentSeries F)) q := by
  have h₄ : (algebraMap (RatFunc F) (LaurentSeries F)) ∘ (algebraMap F[X] (RatFunc F)) = algebraMap F[X] (LaurentSeries F) := h_trans
  have h₅ : ((algebraMap (RatFunc F) (LaurentSeries F)) ∘ (algebraMap F[X] (RatFunc F))) q = (algebraMap F[X] (LaurentSeries F)) q := by rw [h₄]
  simpa [Function.comp_apply] using h₅
calc
  (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
      (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p) / (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) q) := by rw [h₁]
  _ = (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q := by rw [h₂, h₃]
```

**lean_error:** tail step 2/18 ('have h_ring : RingHom (algebraMap (RatFunc F) (LaurentSeries F)) := by exact inferInstance'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 1.1s, in=2397, out=564)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.coe_def, RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, Algebra.ofId_apply]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.coe_def, RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, Algebra.ofId_apply]'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.4s, verify 0.1s, in=5160, out=3817)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [RatFunc.coe_def, RatFunc.coeAlgHom, Algebra.ofId_apply] using
    (RatFunc.coe_div (f := (algebraMap F[X] (RatFunc F) p))
                     (g := (algebraMap F[X] (RatFunc F) q)))
```

**lean_error:** tail step 1/3 ('simpa [RatFunc.coe_def, RatFunc.coeAlgHom, Algebra.ofId_apply] using'): <stdin>:1:68: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 203.6s, verify 0.1s, in=5224, out=23834)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : (algebraMap (RatFunc F) (LaurentSeries F)) = (liftHom (Algebra.ofId F[X] (LaurentSeries F)) _ _ : RatFunc F → LaurentSeries F) := by
  rw [show (algebraMap (RatFunc F) (LaurentSeries F)) = (coeffAlgHom F : RatFunc F → LaurentSeries F) by rfl]
  rw [show (coeffAlgHom F : RatFunc F → LaurentSeries F) = liftAlgHom (Algebra.ofId F[X] (LaurentSeries F)) _ _ by rfl]
calc
  (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q)
    = (liftAlgHom (Algebra.ofId F[X] (LaurentSeries F)) _ _ : RatFunc F → LaurentSeries F) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) := by rw [h]
    _ = (Algebra.ofId F[X] (LaurentSeries F)) p / (Algebra.ofId F[X] (LaurentSeries F)) q := by
      apply RatFunc.liftHom_apply_div
    _ = (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q := by
      have h₁ : (Algebra.ofId F[X] (LaurentSeries F)) p = (algebraMap F[X] (LaurentSeries F)) p := by rw [Algebra.ofId_apply]
      have h₂ : (Algebra.ofId F[X] (LaurentSeries F)) q = (algebraMap F[X] (LaurentSeries F)) q := by rw [Algebra.ofId_apply]
      rw [h₁, h₂]
```

**lean_error:** tail step 1/12 ('have h : (algebraMap (RatFunc F) (LaurentSeries F)) = (liftHom (Algebra.ofId F[X] (LaurentSeries F)) _ _ : RatFunc F → LaurentSeries F) := by'): <stdin>:1:141: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 9.9s, verify 0.1s, in=5242, out=1003)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [RatFunc.coe_def, RatFunc.liftAlgHom_apply_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=4868, out=965)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using
  (RatFunc.coe_div (f := (algebraMap F[X] (RatFunc F) p))
    (g := (algebraMap F[X] (RatFunc F) q)))
```

**lean_error:** tail step 1/3 ('simpa using'): <stdin>:1:11: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.6s, verify 0.1s, in=5623, out=13442)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem RatFunc.algebraMap_apply_div {K F : Type u} [Field F] (p q : F[X]) :
    (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q := by
  have h1 : (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) = ((algebraMap F[X] (RatFunc F)) p : LaurentSeries F) / ((algebraMap F[X] (RatFunc F)) q : LaurentSeries F) := by
    rw [RatFunc.coe_div]
    <;>
    simp_all [algebraMap]
    <;>
    norm_cast
  
  have h2 : ((algebraMap F[X] (RatFunc F)) p : LaurentSeries F) = algebraMap F[X] (LaurentSeries F) p := by
    have h3 : (algebraMap F[X] (RatFunc F) p : LaurentSeries F) = (coeffAlgHom : RatFunc F → LaurentSeries F) (algebraMap F[X] (RatFunc F) p) := by
      simp [RatFunc.coe_def]
      <;>
      norm_cast
    rw [h3]
    have h4 : (coeffAlgHom : RatFunc F → LaurentSeries F) (algebraMap F[X] (RatFunc F) p) = algebraMap F[X] (LaurentSeries F) p := by
      apply algebraMap_map
    rw [h4]
  
  have h3 : ((algebraMap F[X] (RatFunc F)) q : LaurentSeries F) = algebraMap F[X] (LaurentSeries F) q := by
    have h4 : (algebraMap F[X] (RatFunc F) q : Laurent Series F) = (coeffAlgHom : RatFunc F → LaurentSeries F) (algebraMap F[X] (RatFunc F) q) := by
      simp [RatFunc.coe_def]
      <;>
      norm_cast
    rw [h4]
    have h5 : (coeffAlgHom : RatFunc F → LaurentSeries F) (algebraMap F[X] (RatFunc F) q) = algebraMap F[X] (LaurentSeries F) q := by
      apply algebraMap_map
    rw [h5]
  
  calc
    (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) = ((algebraMap F[X] (RatFunc F)) p : LaurentSeries F) / ((algebraMap F[X] (RatFunc F)) q : LaurentSeries F) := h1
    _ = (algebraMap F[X] (LaurentSeries F) p) / (algebraMap F[X] (LaurentSeries F) q) := by rw [h2, h3]
    _ = (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q := by simp [algebraMap]
```

**lean_error:** tail step 1/31 ('theorem RatFunc.algebraMap_apply_div {K F : Type u} [Field F] (p q : F[X]) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 10.4s, verify 0.1s, in=5180, out=1061)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [RatFunc.coe_div, RatFunc.coe_def]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```
