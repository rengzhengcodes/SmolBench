## Current goal
```
⊢ (ρ_ (M.X ⊗ N.X)).hom =
    (M.X ⊗ N.X) ◁ (λ_ (𝟙_ C)).inv ≫ tensor_μ C (M.X, N.X) (𝟙_ C, 𝟙_ C) ≫ ((ρ_ M.X).hom ⊗ (ρ_ N.X).hom)
```

## Full tactic state
```
C : Type u₁
inst✝² : Category.{v₁, u₁} C
inst✝¹ : MonoidalCategory C
inst✝ : BraidedCategory C
M N : Mon_ C
⊢ (ρ_ (M.X ⊗ N.X)).hom =
    (M.X ⊗ N.X) ◁ (λ_ (𝟙_ C)).inv ≫ tensor_μ C (M.X, N.X) (𝟙_ C, 𝟙_ C) ≫ ((ρ_ M.X).hom ⊗ (ρ_ N.X).hom)
```

## Proof so far (4 tactics)
```lean
simp only [MonoidalCategory.whiskerLeft_comp_assoc]
slice_lhs 2 3 => rw [tensor_μ_natural_right]
slice_lhs 3 4 => rw [← tensor_comp, mul_one M, mul_one N]
symm
```

## Theorem
`Mon_.Mon_tensor_mul_one` in `Mathlib/CategoryTheory/Monoidal/Mon_.lean`

## Premises used in the next tactic
- `CategoryTheory.tensor_right_unitality`

## Premise signatures
### `CategoryTheory.tensor_right_unitality` (commanddeclaration)
```lean
@[reassoc]
theorem tensor_right_unitality (X₁ X₂ : C) :
    (ρ_ (X₁ ⊗ X₂)).hom =
      ((X₁ ⊗ X₂) ◁ (λ_ (𝟙_ C)).inv) ≫
        tensor_μ C (X₁, X₂) (𝟙_ C, 𝟙_ C) ≫ ((ρ_ X₁).hom ⊗ (ρ_ X₂).hom)
```

## Premise full source (with proof)
### `CategoryTheory.tensor_right_unitality` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`
```lean
@[reassoc]
theorem tensor_right_unitality (X₁ X₂ : C) :
    (ρ_ (X₁ ⊗ X₂)).hom =
      ((X₁ ⊗ X₂) ◁ (λ_ (𝟙_ C)).inv) ≫
        tensor_μ C (X₁, X₂) (𝟙_ C, 𝟙_ C) ≫ ((ρ_ X₁).hom ⊗ (ρ_ X₂).hom) := by
  dsimp only [tensor_μ]
  have :
    ((X₁ ⊗ X₂) ◁ (λ_ (𝟙_ C)).inv) ≫
        (α_ X₁ X₂ (𝟙_ C ⊗ 𝟙_ C)).hom ≫ (X₁ ◁ (α_ X₂ (𝟙_ C) (𝟙_ C)).inv) =
      (α_ X₁ X₂ (𝟙_ C)).hom ≫ (X₁ ◁ (ρ_ X₂).inv ▷ 𝟙_ C) :=
    by coherence
  slice_rhs 1 3 => rw [this]
  clear this
  slice_rhs 2 3 => rw [← MonoidalCategory.whiskerLeft_comp, ← comp_whiskerRight,
    rightUnitor_inv_braiding]
  simp [tensorHom_id, id_tensorHom, tensorHom_def]
```

## Transitive premise context (1-hop, 4/4 premises, ≈412 tokens)
### `CategoryTheory.MonoidalCategory.comp_whiskerRight` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Category.lean`
```lean
@[reassoc, simp]
theorem comp_whiskerRight {W X Y : C} (f : W ⟶ X) (g : X ⟶ Y) (Z : C) :
    (f ≫ g) ▷ Z = f ▷ Z ≫ g ▷ Z := by
  simp only [← tensorHom_id, ← tensor_comp, id_comp]
```

### `CategoryTheory.rightUnitor_inv_braiding` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`
```lean
@[reassoc]
theorem rightUnitor_inv_braiding (X : C) : (ρ_ X).inv ≫ (β_ X (𝟙_ C)).hom = (λ_ X).inv := by
  apply (cancel_mono (λ_ X).hom).1
  simp only [assoc, braiding_leftUnitor, Iso.inv_hom_id]
```

### `CategoryTheory.MonoidalCategory.tensorHom_id` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Category.lean`
```lean
@[simp]
theorem tensorHom_id {X₁ X₂ : C} (f : X₁ ⟶ X₂) (Y : C) :
    f ⊗ 𝟙 Y = f ▷ Y := by
  simp [tensorHom_def]
```

### `CategoryTheory.MonoidalCategory.id_tensorHom` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Category.lean`
```lean
@[simp]
theorem id_tensorHom (X : C) {Y₁ Y₂ : C} (f : Y₁ ⟶ Y₂) :
    𝟙 X ⊗ f = X ◁ f := by
  simp [tensorHom_def]
```
