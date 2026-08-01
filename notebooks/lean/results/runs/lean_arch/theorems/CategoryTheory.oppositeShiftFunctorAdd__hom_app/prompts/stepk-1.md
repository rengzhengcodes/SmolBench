## Current goal
```
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_3, u_1} C
A : Type u_2
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
X : OppositeShift C A
a b : A
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```
