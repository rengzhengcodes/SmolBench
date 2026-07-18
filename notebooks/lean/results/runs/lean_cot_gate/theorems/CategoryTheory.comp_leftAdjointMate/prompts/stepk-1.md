## Current goal
```
⊢ η_ (ᘁX) X ⊗≫ ᘁX ◁ f ⊗≫ ᘁX ◁ ⊗𝟙 ⊗≫ ᘁX ◁ g = η_ (ᘁX) X ≫ ᘁX ◁ f ≫ ᘁX ◁ g
```

## Full tactic state
```
C : Type u₁
inst✝⁴ : Category.{v₁, u₁} C
inst✝³ : MonoidalCategory C
X Y Z : C
inst✝² : HasLeftDual X
inst✝¹ : HasLeftDual Y
inst✝ : HasLeftDual Z
f : X ⟶ Y
g : Y ⟶ Z
⊢ η_ (ᘁX) X ⊗≫ ᘁX ◁ f ⊗≫ ᘁX ◁ ⊗𝟙 ⊗≫ ᘁX ◁ g = η_ (ᘁX) X ≫ ᘁX ◁ f ≫ ᘁX ◁ g
```
