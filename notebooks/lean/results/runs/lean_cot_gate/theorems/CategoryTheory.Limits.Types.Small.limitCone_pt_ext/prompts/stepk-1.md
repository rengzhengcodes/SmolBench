## Current goal
```
⊢ x = y
```

## Full tactic state
```
J : Type v
inst✝¹ : Category.{w, v} J
F : J ⥤ Type u
inst✝ : Small.{u, max u v} ↑(Functor.sections F)
x y : (limitCone F).pt
w : (equivShrink ↑(Functor.sections F)).symm x = (equivShrink ↑(Functor.sections F)).symm y
⊢ x = y
```
