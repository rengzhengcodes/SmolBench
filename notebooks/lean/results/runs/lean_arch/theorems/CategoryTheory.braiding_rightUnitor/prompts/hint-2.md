## Current goal
```
⊢ (β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom
```

## Full tactic state
```
C : Type u₁
inst✝² : Category.{v₁, u₁} C
inst✝¹ : MonoidalCategory C
inst✝ : BraidedCategory C
X : C
⊢ (β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.braiding_rightUnitor` in `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`

## Premises used in the next tactic
- `CategoryTheory.MonoidalCategory.whiskerLeft_iff`
- `CategoryTheory.MonoidalCategory.whiskerLeft_comp`
- `CategoryTheory.braiding_rightUnitor_aux₂`

## Premise signatures
### `CategoryTheory.MonoidalCategory.whiskerLeft_iff` (commanddeclaration)
```lean
theorem whiskerLeft_iff {X Y : C} (f g : X ⟶ Y) : 𝟙_ C ◁ f = 𝟙_ C ◁ g ↔ f = g
```

### `CategoryTheory.MonoidalCategory.whiskerLeft_comp` (commanddeclaration)
```lean
@[reassoc, simp]
theorem whiskerLeft_comp (W : C) {X Y Z : C} (f : X ⟶ Y) (g : Y ⟶ Z) :
    W ◁ (f ≫ g) = W ◁ f ≫ W ◁ g
```

### `CategoryTheory.braiding_rightUnitor_aux₂` (commanddeclaration)
```lean
theorem braiding_rightUnitor_aux₂ (X : C) :
    (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom
```

## Premise full source (with proof)
### `CategoryTheory.MonoidalCategory.whiskerLeft_iff` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Category.lean`
```lean
theorem whiskerLeft_iff {X Y : C} (f g : X ⟶ Y) : 𝟙_ C ◁ f = 𝟙_ C ◁ g ↔ f = g := by simp
```

### `CategoryTheory.MonoidalCategory.whiskerLeft_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Category.lean`
```lean
@[reassoc, simp]
theorem whiskerLeft_comp (W : C) {X Y Z : C} (f : X ⟶ Y) (g : Y ⟶ Z) :
    W ◁ (f ≫ g) = W ◁ f ≫ W ◁ g := by
  simp only [← id_tensorHom, ← tensor_comp, comp_id]
```

### `CategoryTheory.braiding_rightUnitor_aux₂` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`
```lean
theorem braiding_rightUnitor_aux₂ (X : C) :
    (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom :=
  calc
    (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) =
      (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (α_ _ _ _).inv ≫ (α_ _ _ _).hom ≫ (𝟙_ C ◁ (ρ_ X).hom) :=
      by coherence
    _ = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (α_ _ _ _).inv ≫ ((β_ _ X).hom ▷ _) ≫
          ((β_ _ X).inv ▷ _) ≫ (α_ _ _ _).hom ≫ (𝟙_ C ◁ (ρ_ X).hom) :=
      by simp
    _ = (α_ _ _ _).inv ≫ (β_ _ _).hom ≫ (α_ _ _ _).inv ≫ ((β_ _ X).inv ▷ _) ≫ (α_ _ _ _).hom ≫
          (𝟙_ C ◁ (ρ_ X).hom) :=
      by (slice_lhs 1 3 => rw [← hexagon_reverse]); simp only [assoc]
    _ = (α_ _ _ _).inv ≫ (β_ _ _).hom ≫ (X ◁ (ρ_ _).hom) ≫ (β_ _ X).inv :=
      by rw [braiding_rightUnitor_aux₁]
    _ = (α_ _ _ _).inv ≫ ((ρ_ _).hom ▷ _) ≫ (β_ _ X).hom ≫ (β_ _ _).inv :=
      by (slice_lhs 2 3 => rw [← braiding_naturality_left]); simp only [assoc]
    _ = (α_ _ _ _).inv ≫ ((ρ_ _).hom ▷ _) := by rw [Iso.hom_inv_id, comp_id]
    _ = 𝟙_ C ◁ (λ_ X).hom := by rw [triangle_assoc_comp_right]
```
