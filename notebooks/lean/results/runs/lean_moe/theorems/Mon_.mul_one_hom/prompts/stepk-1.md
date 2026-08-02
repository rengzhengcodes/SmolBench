## Current goal
```
⊢ (f ⊗ M.one) ≫ M.mul = (ρ_ Z).hom ≫ f
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : MonoidalCategory C
M : Mon_ C
Z : C
f : Z ⟶ M.X
⊢ (f ⊗ M.one) ≫ M.mul = (ρ_ Z).hom ≫ f
```
