## Current goal
```
⊢ prodComparison L (F.obj A) B ≫ prod.map (h.counit.app A) (𝟙 (L.obj B)) ≫ prod.snd =
    L.map (prod.map (F.map (𝟙 A)) (h.unit.app B) ≫ prod.snd) ≫ h.counit.app (L.obj B)
```

## Full tactic state
```
case w.h.h₂
C : Type u
inst✝⁶ : Category.{v, u} C
D : Type u'
inst✝⁵ : Category.{v, u'} D
inst✝⁴ : HasFiniteProducts C
inst✝³ : HasFiniteProducts D
F : C ⥤ D
L : D ⥤ C
inst✝² : CartesianClosed C
inst✝¹ : CartesianClosed D
inst✝ : PreservesLimitsOfShape (Discrete WalkingPair) F
h : L ⊣ F
A : C
B : D
⊢ prodComparison L (F.obj A) B ≫ prod.map (h.counit.app A) (𝟙 (L.obj B)) ≫ prod.snd =
    L.map (prod.map (F.map (𝟙 A)) (h.unit.app B) ≫ prod.snd) ≫ h.counit.app (L.obj B)
```
