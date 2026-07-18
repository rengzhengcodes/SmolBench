## Current goal
```
⊢ η_ X Xᘁ ⊗≫ f ▷ Xᘁ ⊗≫ ⊗𝟙 ▷ Xᘁ ⊗≫ g ▷ Xᘁ ⊗≫ 𝟙 (Z ⊗ Xᘁ) = η_ X Xᘁ ≫ f ▷ Xᘁ ≫ g ▷ Xᘁ
```

## Full tactic state
```
C : Type u₁
inst✝⁴ : Category.{v₁, u₁} C
inst✝³ : MonoidalCategory C
X Y Z : C
inst✝² : HasRightDual X
inst✝¹ : HasRightDual Y
inst✝ : HasRightDual Z
f : X ⟶ Y
g : Y ⟶ Z
⊢ η_ X Xᘁ ⊗≫ f ▷ Xᘁ ⊗≫ ⊗𝟙 ▷ Xᘁ ⊗≫ g ▷ Xᘁ ⊗≫ 𝟙 (Z ⊗ Xᘁ) = η_ X Xᘁ ≫ f ▷ Xᘁ ≫ g ▷ Xᘁ
```
