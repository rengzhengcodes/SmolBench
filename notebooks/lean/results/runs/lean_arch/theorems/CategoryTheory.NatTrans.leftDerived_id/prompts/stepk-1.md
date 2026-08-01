## Current goal
```
⊢ 𝟙 (Functor.leftDerivedToHomotopyCategory F ⋙ HomotopyCategory.homologyFunctor D (ComplexShape.down ℕ) n) =
    𝟙 (Functor.leftDerived F n)
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasProjectiveResolutions C
inst✝¹ : Abelian D
F : C ⥤ D
inst✝ : Functor.Additive F
n : ℕ
⊢ 𝟙 (Functor.leftDerivedToHomotopyCategory F ⋙ HomotopyCategory.homologyFunctor D (ComplexShape.down ℕ) n) =
    𝟙 (Functor.leftDerived F n)
```
