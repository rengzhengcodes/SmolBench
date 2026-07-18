## Current goal
```
⊢ 𝟙 (Functor.rightDerivedToHomotopyCategory F ⋙ HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n) =
    𝟙 (Functor.rightDerived F n)
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
F : C ⥤ D
inst✝ : Functor.Additive F
n : ℕ
⊢ 𝟙 (Functor.rightDerivedToHomotopyCategory F ⋙ HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n) =
    𝟙 (Functor.rightDerived F n)
```
