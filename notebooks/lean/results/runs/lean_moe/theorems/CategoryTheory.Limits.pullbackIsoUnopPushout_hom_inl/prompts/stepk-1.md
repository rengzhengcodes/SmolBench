## Current goal
```
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```

## Full tactic state
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
X Y Z : C
f : X ⟶ Z
g : Y ⟶ Z
inst✝¹ : HasPullback f g
inst✝ : HasPushout f.op g.op
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```
