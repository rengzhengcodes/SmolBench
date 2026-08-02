## Current goal
```
⊢ Φ.map (inv ((Quotient.functor redStep).map (Quiver.Hom.toPath f))) =
    inv (Φ.map ((Quotient.functor redStep).map (Quiver.Hom.toPath f)))
```

## Full tactic state
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
hΦ : of V ⋙q Φ.toPrefunctor = φ
X Y : Quiver.Symmetrify V
f : X ⟶ Y
this :
  Φ.map (CategoryTheory.inv ((Quotient.functor redStep).map (Quiver.Hom.toPath f))) =
    CategoryTheory.inv (Φ.map ((Quotient.functor redStep).map (Quiver.Hom.toPath f)))
⊢ Φ.map (inv ((Quotient.functor redStep).map (Quiver.Hom.toPath f))) =
    inv (Φ.map ((Quotient.functor redStep).map (Quiver.Hom.toPath f)))
```
