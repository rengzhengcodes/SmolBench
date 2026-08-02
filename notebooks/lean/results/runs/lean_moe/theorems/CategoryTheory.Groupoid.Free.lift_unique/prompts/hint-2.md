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

## Proof so far (9 tactics)
```lean
apply Quotient.lift_unique
apply Paths.lift_unique
fapply @Quiver.Symmetrify.lift_unique _ _ _ _ _ _ _ _ _
rw [← Functor.toPrefunctor_comp]
exact hΦ
rintro X Y f
simp only [← Functor.toPrefunctor_comp, Prefunctor.comp_map, Paths.of_map, inv_eq_inv]
change Φ.map (inv ((Quotient.functor redStep).toPrefunctor.map f.toPath)) =
  inv (Φ.map ((Quotient.functor redStep).toPrefunctor.map f.toPath))
have := Functor.map_inv Φ ((Quotient.functor redStep).toPrefunctor.map f.toPath)
```

## Theorem
`CategoryTheory.Groupoid.Free.lift_unique` in `Mathlib/CategoryTheory/Groupoid/FreeGroupoid.lean`

## Premises used in the next tactic
- `CategoryTheory.Groupoid.inv_eq_inv`

## Premise signatures
### `CategoryTheory.Groupoid.inv_eq_inv` (commanddeclaration)
```lean
@[simp]
theorem Groupoid.inv_eq_inv (f : X ⟶ Y) : Groupoid.inv f = CategoryTheory.inv f
```

## Premise full source (with proof)
### `CategoryTheory.Groupoid.inv_eq_inv` (commanddeclaration) at `Mathlib/CategoryTheory/Groupoid.lean`
```lean
@[simp]
theorem Groupoid.inv_eq_inv (f : X ⟶ Y) : Groupoid.inv f = CategoryTheory.inv f :=
  IsIso.eq_inv_of_hom_inv_id <| Groupoid.comp_inv f
```
