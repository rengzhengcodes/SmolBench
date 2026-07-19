## Current goal
```
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
              ⋯).hom.app
        X ≫
      ((shiftFunctorZero C ℤ).inv.app X.unop).op =
    (shiftFunctorOpIso C 0 0 ⋯).hom.app X ≫ ((shiftFunctorZero C ℤ).inv.app X.unop).op
```

## Full tactic state
```
C : Type u_1
inst✝¹ : Category.{u_2, u_1} C
inst✝ : HasShift C ℤ
X : Cᵒᵖ
⊢ (pullbackShiftIso (OppositeShift C ℤ)
              (AddMonoidHom.mk' (fun n => -n) CategoryTheory.Pretriangulated.Opposite.OppositeShiftAux.proof_1) 0 0
              ⋯).hom.app
        X ≫
      ((shiftFunctorZero C ℤ).inv.app X.unop).op =
    (shiftFunctorOpIso C 0 0 ⋯).hom.app X ≫ ((shiftFunctorZero C ℤ).inv.app X.unop).op
```
