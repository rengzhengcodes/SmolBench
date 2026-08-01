## Current goal
```
⊢ f = e.inv.app X ≫ (e.hom.app X ≫ f ≫ e.inv.app Y) ≫ e.hom.app Y
```

## Full tactic state
```
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_4, u_1} C
inst✝² : Category.{u_3, u_2} D
L : C ⥤ D
W : MorphismProperty C
inst✝¹ : Functor.IsLocalization L W
inst✝ : MorphismProperty.HasLeftCalculusOfFractions W
X Y : C
f : L.obj X ⟶ L.obj Y
E : MorphismProperty.LeftFraction.Localization W ≌ D := uniq (MorphismProperty.LeftFraction.Localization.Q W) L W
e : MorphismProperty.LeftFraction.Localization.Q W ⋙ E.functor ≅ L :=
  compUniqFunctor (MorphismProperty.LeftFraction.Localization.Q W) L W
⊢ f = e.inv.app X ≫ (e.hom.app X ≫ f ≫ e.inv.app Y) ≫ e.hom.app Y
```
