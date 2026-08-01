## Current goal
```
⊢ toRightDerivedZero' P F ≫
      HomologicalComplex.iCycles ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj P.cocomplex) 0 =
    F.map (P.ι.f 0)
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
inst✝¹ : Abelian D
X : C
P : InjectiveResolution X
F : C ⥤ D
inst✝ : Functor.Additive F
⊢ toRightDerivedZero' P F ≫
      HomologicalComplex.iCycles ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj P.cocomplex) 0 =
    F.map (P.ι.f 0)
```
