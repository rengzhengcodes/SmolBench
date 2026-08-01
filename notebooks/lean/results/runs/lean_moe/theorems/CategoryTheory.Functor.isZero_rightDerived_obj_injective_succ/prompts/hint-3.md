## Current goal
```
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```

## Full tactic state
```
C : Type u
inst✝⁶ : Category.{v, u} C
D : Type u_1
inst✝⁵ : Category.{u_2, u_1} D
inst✝⁴ : Abelian C
inst✝³ : HasInjectiveResolutions C
inst✝² : Abelian D
F : C ⥤ D
inst✝¹ : Additive F
n : ℕ
X : C
inst✝ : Injective X
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```

## Proof so far (3 tactics)
```lean
refine IsZero.of_iso ?_ ((InjectiveResolution.self X).isoRightDerivedObj F (n + 1))
erw [← HomologicalComplex.exactAt_iff_isZero_homology]
exact ShortComplex.exact_of_isZero_X₂ _ (F.map_isZero (by apply isZero_zero))
```

## Theorem
`CategoryTheory.Functor.isZero_rightDerived_obj_injective_succ` in `Mathlib/CategoryTheory/Abelian/RightDerived.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.isZero_zero`

## Premise signatures
### `CategoryTheory.Limits.isZero_zero` (commanddeclaration)
```lean
theorem isZero_zero : IsZero (0 : C)
```

## Premise full source (with proof)
### `CategoryTheory.Limits.isZero_zero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroObjects.lean`
```lean
theorem isZero_zero : IsZero (0 : C) :=
  HasZeroObject.zero.choose_spec
```

## Transitive premise context (1-hop, 1/1 premises, ≈163 tokens)
### `CategoryTheory.Limits.IsZero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroObjects.lean`
```lean
/-- An object `X` in a category is a *zero object* if for every object `Y`
there is a unique morphism `to : X → Y` and a unique morphism `from : Y → X`.

This is a characteristic predicate for `has_zero_object`. -/
structure IsZero (X : C) : Prop where
  /-- there are unique morphisms to the object -/
  unique_to : ∀ Y, Nonempty (Unique (X ⟶ Y))
  /-- there are unique morphisms from the object -/
  unique_from : ∀ Y, Nonempty (Unique (Y ⟶ X))
```
