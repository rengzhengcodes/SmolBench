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

## Filler (hint:2 → hint:3 token-match, ≈101 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet
