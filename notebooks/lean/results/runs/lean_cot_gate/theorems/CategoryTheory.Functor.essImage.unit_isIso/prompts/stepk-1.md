## Current goal
```
⊢ IsIso ((getIso h).inv ≫ (ofRightAdjoint i).unit.app (i.obj (witness h)) ≫ (leftAdjoint i ⋙ i).map (getIso h).hom)
```

## Full tactic state
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
i : D ⥤ C
inst✝ : Reflective i
A : C
h : A ∈ essImage i
this :
  (ofRightAdjoint i).unit.app A =
    (getIso h).inv ≫ (ofRightAdjoint i).unit.app (i.obj (witness h)) ≫ (leftAdjoint i ⋙ i).map (getIso h).hom
⊢ IsIso ((getIso h).inv ≫ (ofRightAdjoint i).unit.app (i.obj (witness h)) ≫ (leftAdjoint i ⋙ i).map (getIso h).hom)
```
