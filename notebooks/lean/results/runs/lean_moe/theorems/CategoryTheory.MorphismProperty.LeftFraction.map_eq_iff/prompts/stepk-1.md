## Current goal
```
⊢ Localization.Hom.mk φ = Localization.Hom.mk ψ
```

## Full tactic state
```
case mpr.e_f
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
W : MorphismProperty C
inst✝¹ : Functor.IsLocalization L W
inst✝ : HasLeftCalculusOfFractions W
X Y : C
φ ψ : LeftFraction W X Y
h : LeftFractionRel φ ψ
⊢ Localization.Hom.mk φ = Localization.Hom.mk ψ
```
