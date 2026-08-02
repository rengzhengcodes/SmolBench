## Current goal
```
⊢ Adhesive C
```

## Full tactic state
```
J : Type v'
inst✝⁸ : Category.{u', v'} J
C : Type u
inst✝⁷ : Category.{v, u} C
W X Y Z : C
f : W ⟶ X
g : W ⟶ Y
h : X ⟶ Z
i : Y ⟶ Z
D : Type u''
inst✝⁶ : Category.{v'', u''} D
F : C ⥤ D
inst✝⁵ : Adhesive D
inst✝⁴ : HasPullbacks C
inst✝³ : HasPushouts C
inst✝² : PreservesLimitsOfShape WalkingCospan F
inst✝¹ : PreservesColimitsOfShape WalkingSpan F
inst✝ : ReflectsIsomorphisms F
this✝ : ReflectsLimitsOfShape WalkingCospan F
this : ReflectsColimitsOfShape WalkingSpan F
⊢ Adhesive C
```
