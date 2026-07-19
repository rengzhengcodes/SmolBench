## Current goal
```
⊢ biprod.desc f g ≫ h = biprod.desc (f ≫ h) (g ≫ h)
```

## Full tactic state
```
case e_a
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : HasZeroMorphisms C
inst✝ : HasBinaryBiproducts C
X Y Z : C
f g : X ⟶ Y
h : Y ⟶ Z
⊢ biprod.desc f g ≫ h = biprod.desc (f ≫ h) (g ≫ h)
```
