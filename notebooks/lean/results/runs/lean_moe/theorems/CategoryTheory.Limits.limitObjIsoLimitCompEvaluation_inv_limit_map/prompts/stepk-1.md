## Current goal
```
⊢ (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f =
    limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u'
inst✝³ : Category.{v', u'} D
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
inst✝ : HasLimitsOfShape J C
i j : K
F : J ⥤ K ⥤ C
f : i ⟶ j
⊢ (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f =
    limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv
```
