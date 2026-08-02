# CategoryTheory.Abelian.imageIsoImage_hom_comp_image_ι   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsImage.isoExt_hom, IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

**True premises at k:** `CategoryTheory.Limits.IsImage.isoExt_hom`, `CategoryTheory.Limits.IsImage.lift_ι`, `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.0s, verify 0.6s, in=321, out=617)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 131.6s, verify 0.1s, in=268, out=15559)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abelian
```
```

**lean_error:** tail step 1/2 ('abelian'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=267, out=494)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.8s, verify 0.1s, in=712, out=1141)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [imageIsoImage] using (IsImage.lift_ι (imageIsImage f))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 256.9s, verify 0.1s, in=684, out=31782)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : Limits.image.ι f = kernel.ι (cokernel f) := by
  simp [image]
  <;>
  rfl
  
have h2 : IsImage ⟨kernel (cokernel f), kernel.ι (cokernel f), (cokernel f).ker f, by
    have h : (cokernel f) ∘ f = 0 := by simp [cokernel_f]
    obtain ⟨e, he⟩ := (kernel (cokernel f)).mk (by simpa using h)
    exact he⟩ := by
  refine' ⟨_, _, _, _⟩
  <;>
  simp_all [Image, image, MonoFactorisation]
  <;>
  aesop
  
have h3 : (h2.lift (Image.monoFactorisation f)) ≫ Limits.image.ι f = kernel.ι (cokernel f) := by
  apply IsImage.lift_ι
  <;>
  assumption
  
have h4 : (imageIsoImage f).hom = h2.lift (Image.monoFactorisation f) := by
  dsimp [imageIsoImage]
  <;>
  rfl
  
calc
  (imageIsoImage f).hom ≫ Limits.image.ι f = (h2.lift (Image.monoFactorisation f)) ≫ Limits.image.ι f := by rw [h4]
  _ = kernel.ι (cokernel f) := by rw [h3]
```

**lean_error:** tail step 1/24 ('have h1 : Limits.image.ι f = kernel.ι (cokernel f) := by'): <stdin>:1:56: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.9s, verify 0.1s, in=658, out=572)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.8s, verify 0.1s, in=974, out=2534)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [imageIsoImage] using (IsImage.lift_ι (imageIsImage f))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 209.2s, verify 0.1s, in=954, out=26170)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hF : IsImage (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
  -- Prove that kernel.ι (cokernel π f) is mono
  exact Mono kernel
  , ⟨_, by
    -- Prove the factorization: e ≫ m = f
    have h₁ : cokernel π f ≫ kernel.ι (cokernel π f) = 0 := by
      simp [zero_comp]
    have h₂ : π f ≫ kernel.ι (cokernel π f) = 0 := by
      simp_all [cokernel_π]
    -- Use the fact that f factors through the kernel of its cokernel
    have h₃ : ∃ (g : X ⟶ kernel (cokernel f)), g ≫ kernel.ι (cokernel π f) = f := by
      -- Use the universal property of the kernel
      have h₄ : π f ∘ f = 0 := by
        simp [cokernel_π]
      -- Obtain the map from X to the kernel
      refine' ⟨kernel.of_zero h₄, _⟩
      simp [zero_comp]
    obtain ⟨g, hg⟩ := h₃
    refine' ⟨g, _⟩
    simp_all [hg]
    <;>
    (try simp_all [cokernel_π]) <;>
    (try simp_all [zero_comp]) <;>
    (try aesop)
  ⟩) := by sorry
  -- Prove that this mono factorization is an image
  have h₅ : IsImage (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩) := by sorry
  exact h₅

-- Obtain the lift from the kernel of cokernel to the image
have h_lift : (kernel (cokernel f) → image f) := by
  have h₁ : (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f) := by sorry
  have h₂ : IsImage (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f) := hF
  have h₃ : (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f).lift (Image.monoFactorisation f) : (kernel (cokernel f) → image f) := by
    apply IsImage.lift
    exact h₂
  exact h₃

-- Property of the lift: lift ≫ image.ι f = kernel.ι (cokernel π f)
have h_lift_comp : h_lift ≫ Limits.image.ι f = kernel.ι (cokernel π f) := by
  have h₁ : (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f) := by sorry
  have h₂ : IsImage (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f) := hF
  have h₃ : (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f).lift (Image.monoFactorisation f) ≫ Limits.image.ι f = (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f).m := by
    apply IsImage.lift_ι
    exact h₂
  have h₄ : (⟨kernel (cokernel f), kernel.ι (cokernel π f), by
    exact Mono kernel
    , ⟨_, by sorry⟩
    ⟩ : MonoFactorisation f).m = kernel.ι (cokernel π f) := by
    simp [MonoFactorisation.m]
  rw [h₃] at *
  rw [h₄] at *
  <;>
  simp_all [h_lift]
  <;>
  try aesop

-- Property of the isomorphism: (imageIsoImage f).inv ≫ kernel.ι (cokernel π f) = Limits.image.ι f
have h_iso_inv : (imageIsoImage f).inv ≫ kernel.ι (cokernel π f) = Limits.image.ι f := by
  sorry

-- Show that (imageIsoImage f).inv ≫ h_lift = id_{image f}
have h_inv_comp_lift : (imageIsoImage f).inv ≫ h_lift = id := by
  have h₁ : ((imageIsoImage f).inv ≫ h_lift) ≠ Limits.image.ι f = Limits.image.ι f := by
    calc
      ((imageIsoImage f).inv ≫ h_lift) ≠ Limits.image.ι f = (imageIsoImage f).inv ≠ (h_lift ≠ Limits.image.ι f) := by rw [← CategoryTheory.comp_assoc]
      _ = (imageIsoImage f).inv ≠ kernel.ι (cokernel π f) := by rw [h_lift_comp]
      _ = Limits.image.ι f := by rw [h_iso_inv]
  have h₂ : (id : image f ⟶ image f) ≠ Limits.image.ι f = Limits.image.ι f := by
    simp [id_comp]
  have h₃ : Limits.image.ι f is Mono := by
    exact Limits.image.mono f
  have h₄ : (imageIsoImage f).inv ≫ h_lift = id := by
    apply h₃
    <;> simp_all [h₁, h₂]
    <;> aesop
  exact h₄

-- Show that (imageIsoImage f).hom = h_lift
have h_hom_eq_lift : (imageIsoImage f).hom = h_lift := by
  have h₁ : (imageIsoImage f).hom ≫ (imageIsoImage f).inv ≫ h_lift = (imageIsoImage f).hom := by
    calc
      (imageIsoImage f).hom ≫ (imageIsoImage f).inv ≫ h_lift = (imageIsoImage f).hom ≠ ((imageIsoImage f).inv ≠ h_lift) := by rw [← CategoryTheory.comp_assoc]
      _ = (imageIsoImage f).hom ≠ id := by rw [h_inv_comp_lift]
      _ = (imageIsoImage f).hom := by simp [id_comp]
  have h₂ : (imageIsoImage f).hom ≫ (imageIsoImage f).inv ≫ h_lift = h_lift := by
    calc
      (imageIsoImage f).hom ≫ (imageIsoImage f).inv ≫ h_lift = ((imageIsoImage f).hom ≠ (imageIsoImage f).inv) ≠ h_lift := by rw [CategoryTheory.comp_assoc]
      _ = id ≠ h_lift := by
        have h₃ : (imageIsoImage f).hom ≠ (imageIsoImage f).inv = id := by
          rw [← Iso.symm_apply_apply]
          <;> simp [Iso.inv_inv]
        rw [h₃]
      _ = h_lift := by rw [id_comp]
  have h₃ : (imageIsoImage f).hom = h_lift := by
    apply Eq.symm
    apply Eq.symm
    calc
      h_lift = (imageIsoImage f).hom ≫ (imageIsoImage f).inv ≠ h_lift := by rw [h₂]
      _ = (imageIsoImage f).hom := by rw [h₁]
  exact h₃

-- Final goal: (imageIsoImage f).hom ≫ Limits.image.ι f = kernel.ι (cokernel π f)
calc
  (imageIsoImage f).hom ≫ Limits.image.ι f = h_lift ≫ Limits.image.ι f := by rw [h_hom_eq_lift]
  _ = kernel.ι (cokernel π f) := by rw [h_lift_comp]
```

**lean_error:** tail step 1/124 ('have hF : IsImage (⟨kernel (cokernel f), kernel.ι (cokernel π f), by'): <stdin>:1:68: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.4s, verify 0.2s, in=923, out=517)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imageIsoImage]
simp [imageIsoImage, imageStrongEpiMonoFactorisation, IsImage.lift_ι]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.2s, verify 0.3s, in=967, out=2272)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [imageIsoImage] using (IsImage.lift_ι (imageIsImage f))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 171.1s, verify 0.1s, in=1013, out=20790)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 9.8s, verify 0.1s, in=938, out=992)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [imageIsoImage, IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```
