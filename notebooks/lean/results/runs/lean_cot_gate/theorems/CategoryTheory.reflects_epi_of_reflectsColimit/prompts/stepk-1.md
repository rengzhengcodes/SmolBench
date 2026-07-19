## Current goal
```
⊢ Epi f
```

## Full tactic state
```
C : Type u₁
D : Type u₂
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
F : C ⥤ D
X Y : C
f : X ⟶ Y
inst✝¹ : ReflectsColimit (span f f) F
inst✝ : Epi (F.map f)
this : IsColimit (PushoutCocone.mk (F.map (𝟙 Y)) (F.map (𝟙 Y)) ⋯)
⊢ Epi f
```
