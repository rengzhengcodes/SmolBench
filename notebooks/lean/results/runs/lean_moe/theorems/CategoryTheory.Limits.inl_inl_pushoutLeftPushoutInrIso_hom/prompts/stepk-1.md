## Current goal
```
⊢ pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u₂
inst✝³ : Category.{v₂, u₂} D
W X Y Z : C
f : X ⟶ Y
g : X ⟶ Z
g' : Z ⟶ W
inst✝² : HasPushout f g
inst✝¹ : HasPushout pushout.inr g'
inst✝ : HasPushout f (g ≫ g')
⊢ pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl
```
