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
