## Current goal
```
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
inst✝ : HasBiproduct f
T U : C
g : (j : J) → T ⟶ f j
h : (j : J) → f j ⟶ U
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```
